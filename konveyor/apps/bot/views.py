"""
Views for the bot app.

This module contains views for handling Slack webhook events and other bot-related
HTTP endpoints.
"""

import json
import logging
import traceback
import ssl
import certifi
import datetime
from typing import Dict, Any, Optional
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

# Fix SSL certificate issues on macOS
ssl._create_default_https_context = ssl._create_unverified_context

from konveyor.skills.setup import create_kernel
from konveyor.skills.agent_orchestrator import AgentOrchestratorSkill, SkillRegistry
from konveyor.skills.ChatSkill import ChatSkill
from .services.slack_service import SlackService

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the Slack service
slack_service = SlackService()

# Initialize the Agent Orchestration components
kernel = create_kernel(validate=False)
registry = SkillRegistry()
orchestrator = AgentOrchestratorSkill(kernel, registry)
kernel.add_plugin(orchestrator, plugin_name="orchestrator")

# Register the ChatSkill with the same kernel instance
chat_skill = ChatSkill(kernel=kernel)
orchestrator.register_skill(chat_skill, "ChatSkill",
                          "Handles general chat interactions and questions",
                          ["chat", "question", "answer", "help"])

@csrf_exempt
def root_handler(request):
    """
    Handle requests to the root URL.

    This is a catch-all handler for the root URL to handle Slack's verification requests.

    Args:
        request: The HTTP request

    Returns:
        HTTP response
    """
    logger.info(f"ROOT HANDLER: Received request to root URL with method {request.method}")
    logger.info(f"ROOT HANDLER: Headers: {request.headers}")
    logger.info(f"ROOT HANDLER: Path: {request.path}")
    logger.info(f"ROOT HANDLER: GET params: {request.GET}")

    # If it's a POST request, it might be a Slack verification
    if request.method == 'POST':
        try:
            body_str = request.body.decode('utf-8')
            logger.info(f"ROOT HANDLER: Request body: {body_str[:500]}...")

            # Try to parse as JSON
            payload = json.loads(body_str)
            logger.info(f"ROOT HANDLER: Parsed JSON payload: {payload}")

            # If it's a URL verification challenge, respond with the challenge
            if payload.get('type') == 'url_verification':
                challenge = payload.get('challenge')
                logger.info(f"ROOT HANDLER: Detected URL verification challenge: {challenge}")
                return JsonResponse({'challenge': challenge})

            # If it's an event callback, log it
            if payload.get('type') == 'event_callback':
                event = payload.get('event', {})
                logger.info(f"ROOT HANDLER: Received event callback: {event}")
                logger.info(f"ROOT HANDLER: Event type: {event.get('type')}")
                logger.info(f"ROOT HANDLER: Event user: {event.get('user')}")
                logger.info(f"ROOT HANDLER: Event text: {event.get('text')}")

        except Exception as e:
            logger.error(f"ROOT HANDLER: Error processing request: {str(e)}")
            logger.error(traceback.format_exc())

    # For other requests, return a simple response
    return HttpResponse("Konveyor Slack Bot is running. Please use the /api/bot/slack/events/ endpoint for Slack events.")

@csrf_exempt
@require_POST
def slack_webhook(request):
    """
    Handle incoming Slack events.

    This view receives webhook events from Slack, verifies them, and processes
    them using the Agent Orchestration Layer.

    Args:
        request: The HTTP request

    Returns:
        HTTP response
    """
    logger.info(f"SLACK WEBHOOK: Received request to {request.path} with method {request.method}")
    logger.info(f"SLACK WEBHOOK: Headers: {request.headers}")
    logger.info(f"SLACK WEBHOOK: Path: {request.path}")
    logger.info(f"SLACK WEBHOOK: GET params: {request.GET}")

    # Verify the request is from Slack
    slack_signature = request.headers.get('X-Slack-Signature', '')
    slack_timestamp = request.headers.get('X-Slack-Request-Timestamp', '')

    logger.info(f"SLACK WEBHOOK: Slack signature: {slack_signature}")
    logger.info(f"SLACK WEBHOOK: Slack timestamp: {slack_timestamp}")

    # Skip verification for URL verification challenges (initial setup)
    is_verification = False
    try:
        body_str = request.body.decode('utf-8')
        logger.info(f"SLACK WEBHOOK: Request body: {body_str[:500]}...")
        if '"type":"url_verification"' in body_str or '"challenge":' in body_str:
            is_verification = True
            logger.info("SLACK WEBHOOK: Detected URL verification challenge")
    except Exception as e:
        logger.error(f"SLACK WEBHOOK: Error decoding request body: {str(e)}")
        logger.error(traceback.format_exc())

    # Skip verification if headers are missing (for testing purposes)
    if not slack_signature or not slack_timestamp:
        logger.warning("SLACK WEBHOOK: Missing Slack verification headers, skipping verification")
        is_verification = True

    if not is_verification and not slack_service.verify_request(request.body, slack_signature, slack_timestamp):
        logger.warning("SLACK WEBHOOK: Failed to verify Slack request")
        return HttpResponse(status=403)

    # Parse the request
    try:
        payload = json.loads(request.body)
        logger.info(f"SLACK WEBHOOK: Received Slack event: {payload.get('type')}")
        logger.info(f"SLACK WEBHOOK: Full payload: {payload}")
    except json.JSONDecodeError:
        logger.error("SLACK WEBHOOK: Failed to parse JSON payload")
        logger.error(traceback.format_exc())
        return HttpResponse(status=400)

    # Handle URL verification
    if payload.get('type') == 'url_verification':
        challenge = payload.get('challenge')
        logger.info(f"SLACK WEBHOOK: Handling URL verification challenge: {challenge}")
        logger.info(f"SLACK WEBHOOK: Full verification payload: {payload}")
        return JsonResponse({'challenge': challenge})

    # Handle events
    if payload.get('type') == 'event_callback':
        event = payload.get('event', {})
        logger.info(f"SLACK WEBHOOK: Received event callback: {event}")
        logger.info(f"SLACK WEBHOOK: Event type: {event.get('type')}")
        logger.info(f"SLACK WEBHOOK: Event user: {event.get('user')}")
        logger.info(f"SLACK WEBHOOK: Event text: {event.get('text')}")
        logger.info(f"SLACK WEBHOOK: Event channel: {event.get('channel')}")
        logger.info(f"SLACK WEBHOOK: Event channel type: {event.get('channel_type')}")
        logger.info(f"SLACK WEBHOOK: Event timestamp: {event.get('ts')}")
        logger.info(f"SLACK WEBHOOK: Event client_msg_id: {event.get('client_msg_id')}")
        logger.info(f"SLACK WEBHOOK: Event team: {event.get('team')}")
        logger.info(f"SLACK WEBHOOK: Event bot_id: {event.get('bot_id')}")
        logger.info(f"SLACK WEBHOOK: Event app_id: {event.get('app_id')}")
        logger.info(f"SLACK WEBHOOK: Payload api_app_id: {payload.get('api_app_id')}")

        # Get the event ID and timestamp for deduplication
        event_id = payload.get('event_id', '')
        event_ts = event.get('ts', '')
        event_client_msg_id = event.get('client_msg_id', '')
        event_text = event.get('text', '')
        event_user = event.get('user', '')

        # Create a composite ID for more reliable deduplication
        # Include user ID and a hash of the text to ensure unique messages are processed
        import hashlib
        text_hash = hashlib.md5(event_text.encode()).hexdigest()[:8] if event_text else ''
        composite_id = f"{event_id}:{event_ts}:{event_client_msg_id}:{event_user}:{text_hash}"

        # Log the deduplication details
        logger.info(f"SLACK WEBHOOK: Event deduplication details - ID: {event_id}, TS: {event_ts}, Client Msg ID: {event_client_msg_id}, User: {event_user}, Text Hash: {text_hash}")
        logger.info(f"SLACK WEBHOOK: Composite ID: {composite_id}")

        # Use a simple in-memory cache for deduplication
        # This is a class variable to persist across requests
        if not hasattr(slack_webhook, 'processed_events'):
            slack_webhook.processed_events = set()
            logger.info("SLACK WEBHOOK: Initialized processed_events set")

        # For debugging, log the current set of processed events
        logger.info(f"SLACK WEBHOOK: Current processed events count: {len(slack_webhook.processed_events)}")

        # Check if we've already processed this event
        if composite_id and composite_id in slack_webhook.processed_events:
            logger.info(f"SLACK WEBHOOK: Skipping duplicate event with composite ID: {composite_id}")
            return HttpResponse(status=200)

        # Add this event to the processed set
        if composite_id:
            slack_webhook.processed_events.add(composite_id)
            logger.info(f"SLACK WEBHOOK: Added event with composite ID: {composite_id} to processed events")
            # Keep the set from growing too large
            if len(slack_webhook.processed_events) > 1000:
                slack_webhook.processed_events = set(list(slack_webhook.processed_events)[-1000:])
                logger.info(f"SLACK WEBHOOK: Trimmed processed events to {len(slack_webhook.processed_events)} items")

        # Process all message events, including those from real users
        if event.get('type') == 'message':
            # Log the full event details for debugging
            logger.info(f"SLACK WEBHOOK: Received message event with full details: {event}")

            # Skip messages from our own bot to avoid infinite loops
            if event.get('bot_id') and event.get('app_id') == payload.get('api_app_id'):
                logger.info(f"SLACK WEBHOOK: Skipping message from our own bot (bot_id: {event.get('bot_id')}, app_id: {event.get('app_id')}, api_app_id: {payload.get('api_app_id')})")
                return HttpResponse(status=200)

            # Skip message subtypes like message_changed, message_deleted, etc.
            if event.get('subtype') and event.get('subtype') not in ['bot_message']:
                logger.info(f"SLACK WEBHOOK: Skipping message with subtype: {event.get('subtype')}")
                return HttpResponse(status=200)

            text = event.get('text', '')
            channel = event.get('channel', '')
            user = event.get('user', '')
            channel_type = event.get('channel_type', '')

            # Log detailed information about the message
            logger.info(f"SLACK WEBHOOK: Processing message event with full details: {event}")
            logger.info(f"SLACK WEBHOOK: Message from user {user} in channel {channel} with text: {text}")
            logger.info(f"SLACK WEBHOOK: Channel type: {channel_type}")
            logger.info(f"SLACK WEBHOOK: Processing message from user {user} in {channel_type} {channel}: {text}")

            try:
                # Process the message through the orchestrator
                logger.info(f"SLACK WEBHOOK: Calling process_message with text: {text}, user: {user}, channel: {channel}")
                result = process_message(text, user, channel)
                logger.info(f"SLACK WEBHOOK: process_message result: {result}")

                # Get the response text
                response_text = result.get('response', 'Sorry, I could not process your request.')
                logger.info(f"SLACK WEBHOOK: Response text: {response_text}")

                # Check if we should format the response with blocks
                skill_name = result.get('skill_name', '')
                logger.info(f"SLACK WEBHOOK: Skill name: {skill_name}")

                if skill_name == 'ChatSkill':
                    # Try to format the response with blocks using the ChatSkill
                    try:
                        logger.info(f"SLACK WEBHOOK: Formatting response with ChatSkill")
                        formatted_response = chat_skill.format_for_slack(response_text)
                        logger.info(f"SLACK WEBHOOK: Formatted response: {formatted_response}")
                        response_text = formatted_response.get('text', response_text)
                        blocks = formatted_response.get('blocks')
                        logger.info(f"SLACK WEBHOOK: Formatted response text: {response_text}")
                        logger.info(f"SLACK WEBHOOK: Formatted blocks: {blocks}")
                    except Exception as e:
                        logger.error(f"SLACK WEBHOOK: Error formatting response with blocks: {str(e)}")
                        logger.error(traceback.format_exc())
                        blocks = None
                else:
                    logger.info(f"SLACK WEBHOOK: Not using blocks for non-ChatSkill response")
                    blocks = None

                # For direct messages (im), use the send_direct_message method
                if channel_type == 'im':
                    logger.info(f"SLACK WEBHOOK: Sending direct message response to user {user}")
                    logger.info(f"SLACK WEBHOOK: Response text: {response_text}")
                    logger.info(f"SLACK WEBHOOK: Blocks: {blocks}")
                    try:
                        response = slack_service.send_direct_message(user, response_text, blocks)
                        logger.info(f"SLACK WEBHOOK: Slack API response: {response}")
                    except Exception as e:
                        logger.error(f"SLACK WEBHOOK: Error sending direct message: {str(e)}")
                        logger.error(traceback.format_exc())
                else:
                    # For channel messages, use the send_message method
                    logger.info(f"SLACK WEBHOOK: Sending response to channel {channel}")
                    logger.info(f"SLACK WEBHOOK: Response text: {response_text}")
                    logger.info(f"SLACK WEBHOOK: Blocks: {blocks}")
                    try:
                        response = slack_service.send_message(channel, response_text, blocks)
                        logger.info(f"SLACK WEBHOOK: Slack API response: {response}")
                    except Exception as e:
                        logger.error(f"SLACK WEBHOOK: Error sending channel message: {str(e)}")
                        logger.error(traceback.format_exc())

                logger.info(f"SLACK WEBHOOK: Sent response to {channel_type} {channel}")
            except Exception as e:
                logger.error(f"SLACK WEBHOOK: Error processing message: {str(e)}")
                logger.error(traceback.format_exc())

                error_message = f"Sorry, I encountered an error: {str(e)}"
                logger.info(f"SLACK WEBHOOK: Error message: {error_message}")

                # Create error blocks
                error_blocks = [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "Error"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": error_message
                        }
                    }
                ]
                logger.info(f"SLACK WEBHOOK: Error blocks: {error_blocks}")

                # Send error message to the appropriate channel type
                try:
                    if channel_type == 'im':
                        logger.info(f"SLACK WEBHOOK: Sending error message to user {user}")
                        response = slack_service.send_direct_message(user, error_message, error_blocks)
                        logger.info(f"SLACK WEBHOOK: Slack API response: {response}")
                    else:
                        logger.info(f"SLACK WEBHOOK: Sending error message to channel {channel}")
                        response = slack_service.send_message(channel, error_message, error_blocks)
                        logger.info(f"SLACK WEBHOOK: Slack API response: {response}")
                except Exception as send_error:
                    logger.error(f"SLACK WEBHOOK: Error sending error message: {str(send_error)}")
                    logger.error(traceback.format_exc())

    return HttpResponse(status=200)

def process_message(text: str, user_id: str, channel_id: str) -> Dict[str, Any]:
    """
    Process a message using the Agent Orchestration Layer.

    Args:
        text: The message text
        user_id: The Slack user ID
        channel_id: The Slack channel ID

    Returns:
        The processed result
    """
    logger.info(f"PROCESS_MESSAGE: Processing message: '{text}' from user {user_id} in channel {channel_id}")

    # Create context with user and channel information
    context = {
        "user_id": user_id,
        "channel_id": channel_id,
        "platform": "slack",
        "timestamp": datetime.datetime.now().isoformat()
    }

    logger.info(f"PROCESS_MESSAGE: Created context: {context}")

    # Process the request through the orchestrator
    try:
        logger.info(f"PROCESS_MESSAGE: Sending request to orchestrator",
                   extra={
                       "user_id": user_id,
                       "channel_id": channel_id,
                       "text_length": len(text),
                       "text_preview": text[:50] + ("..." if len(text) > 50 else "")
                   })

        logger.info(f"PROCESS_MESSAGE: Calling orchestrator.process_request_sync with text: {text}")
        result = orchestrator.process_request_sync(text, context)
        logger.info(f"PROCESS_MESSAGE: Orchestrator result: {result}")

        logger.info(f"PROCESS_MESSAGE: Orchestrator processed request successfully",
                   extra={
                       "user_id": user_id,
                       "channel_id": channel_id,
                       "skill_name": result.get("skill_name", "unknown"),
                       "function_name": result.get("function_name", "unknown"),
                       "success": result.get("success", False)
                   })

        return result
    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)

        # Log structured error information
        logger.error(f"PROCESS_MESSAGE: Error in orchestrator.process_request_sync: {error_message}",
                    extra={
                        "user_id": user_id,
                        "channel_id": channel_id,
                        "error_type": error_type,
                        "error_message": error_message,
                        "text_preview": text[:50] + ("..." if len(text) > 50 else "")
                    })

        # Log the full traceback
        logger.error(f"PROCESS_MESSAGE: Full traceback:")
        logger.error(traceback.format_exc())

        # Create a user-friendly error message
        user_message = "I encountered an error while processing your request."
        if error_type == "ValueError":
            user_message += f" {error_message}"
        elif error_type == "KeyError":
            user_message += " I couldn't find some required information."
        elif error_type == "TimeoutError":
            user_message += " The operation timed out. Please try again later."
        else:
            user_message += " Please try again or contact support if the issue persists."

        logger.info(f"PROCESS_MESSAGE: Returning error response: {user_message}")

        return {
            "response": user_message,
            "error": error_message,
            "error_type": error_type,
            "success": False
        }
