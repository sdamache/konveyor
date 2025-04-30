"""
Views for the bot app.

This module contains views for handling Slack webhook events and other bot-related
HTTP endpoints.

This updated version uses the new core components for conversation management,
message formatting, and response generation.
"""

import asyncio
import datetime
import hashlib
import json
import logging
import ssl
import traceback
from typing import Any, Dict, Optional

# Removed: import certifi
# Removed: from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from konveyor.apps.bot.services.slack_service import SlackService
from konveyor.core.agent import AgentOrchestratorSkill, SkillRegistry
from konveyor.core.chat import ChatSkill
from konveyor.core.conversation.factory import ConversationManagerFactory
from konveyor.core.formatters.factory import FormatterFactory
from konveyor.core.kernel import create_kernel

# Fix SSL certificate issues on macOS
ssl._create_default_https_context = ssl._create_unverified_context

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
orchestrator.register_skill(
    chat_skill,
    "ChatSkill",
    "Handles general chat interactions and questions",
    ["chat", "question", "answer", "help"],
)

# Initialize the formatter
slack_formatter = FormatterFactory.get_formatter("slack")

# Initialize the conversation manager
conversation_manager = None


async def init_conversation_manager():
    """Initialize the conversation manager."""
    global conversation_manager
    try:
        conversation_manager = await ConversationManagerFactory.create_manager("memory")
        logger.info("Initialized conversation manager")
    except Exception as e:
        logger.error(f"Failed to initialize conversation manager: {str(e)}")
        logger.error(traceback.format_exc())


# Initialize the conversation manager
try:
    asyncio.run(init_conversation_manager())
except Exception as e:
    logger.error(f"Failed to initialize conversation manager: {str(e)}")
    logger.error(traceback.format_exc())


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
    logger.info(
        f"ROOT HANDLER: Received request to root URL with method {request.method}"
    )
    logger.info(f"ROOT HANDLER: Headers: {request.headers}")
    logger.info(f"ROOT HANDLER: Path: {request.path}")
    logger.info(f"ROOT HANDLER: GET params: {request.GET}")

    # If it's a POST request, it might be a Slack verification
    if request.method == "POST":
        try:
            body_str = request.body.decode("utf-8")
            logger.info(f"ROOT HANDLER: Request body: {body_str[:500]}...")

            # Try to parse as JSON
            payload = json.loads(body_str)
            logger.info(f"ROOT HANDLER: Parsed JSON payload: {payload}")

            # If it's a URL verification challenge, respond with the challenge
            if payload.get("type") == "url_verification":
                challenge = payload.get("challenge")
                logger.info(
                    f"ROOT HANDLER: Detected URL verification challenge: {challenge}"
                )
                return JsonResponse({"challenge": challenge})

            # If it's an event callback, log it
            if payload.get("type") == "event_callback":
                event = payload.get("event", {})
                logger.info(f"ROOT HANDLER: Received event callback: {event}")
                logger.info(f"ROOT HANDLER: Event type: {event.get('type')}")
                logger.info(f"ROOT HANDLER: Event user: {event.get('user')}")
                logger.info(f"ROOT HANDLER: Event text: {event.get('text')}")

        except Exception as e:
            logger.error(f"ROOT HANDLER: Error processing request: {str(e)}")
            logger.error(traceback.format_exc())

    # For other requests, return a simple response
    return HttpResponse(
        "Konveyor Slack Bot is running. Please use the /api/bot/slack/events/ endpoint for Slack events."
    )


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
    logger.debug(f"Received Slack webhook request to {request.path}")

    # Verify the request is from Slack
    slack_signature = request.headers.get("X-Slack-Signature", "")
    slack_timestamp = request.headers.get("X-Slack-Request-Timestamp", "")

    # Skip verification for URL verification challenges (initial setup)
    is_verification = False
    try:
        body_str = request.body.decode("utf-8")
        body_preview = body_str[:100] + ("..." if len(body_str) > 100 else "")
        logger.debug(f"Request body preview: {body_preview}")

        if '"type":"url_verification"' in body_str or '"challenge":' in body_str:
            is_verification = True
            logger.info("Detected URL verification challenge")
    except Exception as e:
        logger.error(f"Error decoding request body: {str(e)}")
        logger.error(traceback.format_exc())

    # Skip verification if headers are missing (for testing purposes)
    if not slack_signature or not slack_timestamp:
        logger.warning("Missing Slack verification headers, skipping verification")
        is_verification = True

    if not is_verification and not slack_service.verify_request(
        request.body, slack_signature, slack_timestamp
    ):
        logger.warning("Failed to verify Slack request")
        return HttpResponse(status=403)

    # Parse the request
    try:
        payload = json.loads(request.body)
        event_type = payload.get("type")
        logger.info(f"Received Slack event: {event_type}")
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON payload")
        logger.error(traceback.format_exc())
        return HttpResponse(status=400)

    # Handle URL verification
    if event_type == "url_verification":
        challenge = payload.get("challenge")
        logger.info("Handling URL verification challenge")
        return JsonResponse({"challenge": challenge})

    # Handle events
    if event_type == "event_callback":
        event = payload.get("event", {})
        event_subtype = event.get("type")

        # Initialize processed_events set if it doesn't exist
        if not hasattr(slack_webhook, "processed_events"):
            slack_webhook.processed_events = set()
            logger.debug("Initialized processed_events set")

        # Get the event ID and timestamp for deduplication
        event_id = payload.get("event_id", "")
        event_ts = event.get("ts", "")
        event_client_msg_id = event.get("client_msg_id", "")
        event_text = event.get("text", "")
        event_user = event.get("user", "")

        # Create a composite ID for more reliable deduplication
        text_hash = (
            hashlib.md5(event_text.encode()).hexdigest()[:8] if event_text else ""
        )
        composite_id = (
            f"{event_id}:{event_ts}:{event_client_msg_id}:{event_user}:{text_hash}"
        )

        # Check if we've already processed this event
        if composite_id and composite_id in slack_webhook.processed_events:
            logger.debug(f"Skipping duplicate event with ID: {event_id}")
            return HttpResponse(status=200)

        # Add this event to the processed set
        if composite_id:
            slack_webhook.processed_events.add(composite_id)
            # Keep the set from growing too large
            if len(slack_webhook.processed_events) > 1000:
                slack_webhook.processed_events = set(
                    list(slack_webhook.processed_events)[-1000:]
                )
                logger.debug(
                    f"Trimmed processed events to {len(slack_webhook.processed_events)} items"
                )

        # Process message events
        if event_subtype == "message":
            # Skip messages from our own bot to avoid infinite loops
            if event.get("bot_id") and event.get("app_id") == payload.get("api_app_id"):
                logger.debug("Skipping message from our own bot")
                return HttpResponse(status=200)

            # Skip message subtypes like message_changed, message_deleted, etc.
            if event.get("subtype") and event.get("subtype") not in ["bot_message"]:
                logger.debug(f"Skipping message with subtype: {event.get('subtype')}")
                return HttpResponse(status=200)

            text = event.get("text", "")
            channel = event.get("channel", "")
            user = event.get("user", "")
            channel_type = event.get("channel_type", "")

            # Log message details at appropriate levels
            logger.info(
                f"Processing message from user {user} in {channel_type} {channel}"
            )
            text_preview = text[:50] + ("..." if len(text) > 50 else "")
            logger.debug(f"Message text preview: {text_preview}")

            try:
                # Process the message through the orchestrator
                logger.debug(
                    f"Calling process_message with user: {user}, channel: {channel}"
                )
                result = process_message(text, user, channel)

                # Get the response text
                response_text = result.get(
                    "response", "Sorry, I could not process your request."
                )
                skill_name = result.get("skill_name", "")
                conversation_id = result.get("conversation_id", "")

                # Format the response with blocks
                blocks = None
                try:
                    if slack_formatter:
                        logger.debug("Formatting response with Slack formatter")
                        formatted_response = slack_formatter.format_message(
                            response_text, include_blocks=True
                        )
                        response_text = formatted_response.get("text", response_text)
                        blocks = formatted_response.get("blocks")
                    elif skill_name == "ChatSkill":
                        logger.debug("Formatting response with ChatSkill")
                        formatted_response = chat_skill.format_for_slack(response_text)
                        response_text = formatted_response.get("text", response_text)
                        blocks = formatted_response.get("blocks")
                except Exception as e:
                    logger.error(f"Error formatting response with blocks: {str(e)}")
                    logger.error(traceback.format_exc())

                # Send the response based on channel type
                try:
                    if channel_type == "im":
                        logger.info(f"Sending direct message response to user {user}")
                        response = slack_service.send_direct_message(
                            user, response_text, blocks
                        )
                    else:
                        logger.info(f"Sending response to channel {channel}")
                        response = slack_service.send_message(
                            channel, response_text, blocks
                        )

                    logger.debug(
                        f"Message sent successfully to {channel_type} {channel}"
                    )
                except Exception as e:
                    logger.error(f"Error sending message: {str(e)}")
                    logger.error(traceback.format_exc())

            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                logger.error(traceback.format_exc())

                # Send error message
                error_message = f"Sorry, I encountered an error: {str(e)}"

                # Format error message with blocks
                error_blocks = None
                try:
                    if slack_formatter:
                        formatted_error = slack_formatter.format_error(error_message)
                        error_message = formatted_error.get("text", error_message)
                        error_blocks = formatted_error.get("blocks")
                    else:
                        error_blocks = [
                            {
                                "type": "header",
                                "text": {"type": "plain_text", "text": "Error"},
                            },
                            {
                                "type": "section",
                                "text": {"type": "mrkdwn", "text": error_message},
                            },
                        ]
                except Exception as format_error:
                    logger.error(f"Error formatting error message: {str(format_error)}")

                try:
                    if channel_type == "im":
                        slack_service.send_direct_message(
                            user, error_message, error_blocks
                        )
                    else:
                        slack_service.send_message(channel, error_message, error_blocks)
                except Exception as send_error:
                    logger.error(f"Error sending error message: {str(send_error)}")

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
    text_preview = text[:50] + ("..." if len(text) > 50 else "")
    logger.debug(f"Processing message from user {user_id} in channel {channel_id}")
    logger.debug(f"Message preview: {text_preview}")

    # Create context with user and channel information
    context = {
        "user_id": user_id,
        "channel_id": channel_id,
        "platform": "slack",
        "timestamp": datetime.datetime.now().isoformat(),
    }

    # Get or create a conversation for this user
    conversation_id = None
    if conversation_manager:
        try:
            # Use asyncio to run the async method in a synchronous context
            async def get_or_create_conversation():
                # Try to find an existing conversation for this user
                user_conversations = await conversation_manager.get_user_conversations(
                    user_id, limit=1
                )
                if user_conversations:
                    return user_conversations[0]["id"]
                else:
                    # Create a new conversation
                    conversation = await conversation_manager.create_conversation(
                        user_id
                    )
                    return conversation["id"]

            # Run the async function
            conversation_id = asyncio.run(get_or_create_conversation())
            logger.debug(f"Using conversation ID: {conversation_id}")

            # Add the conversation ID to the context
            context["conversation_id"] = conversation_id
        except Exception as e:
            logger.error(f"Error getting or creating conversation: {str(e)}")
            logger.error(traceback.format_exc())

    # Process the request through the orchestrator
    try:
        logger.info(f"Sending request to orchestrator for user {user_id}")

        result = orchestrator.process_request_sync(text, context)

        # Log success at appropriate level
        skill_name = result.get("skill_name", "unknown")
        function_name = result.get("function_name", "unknown")
        success = result.get("success", False)

        if success:
            logger.info(
                f"Request processed successfully by {skill_name}.{function_name}"
            )
        else:
            logger.warning(
                f"Request processing completed with success=False by {skill_name}.{function_name}"
            )

        # Add the conversation ID to the result
        if conversation_id:
            result["conversation_id"] = conversation_id

        return result
    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)

        # Log structured error information
        logger.error(f"Error in orchestrator: {error_type}: {error_message}")
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
            user_message += (
                " Please try again or contact support if the issue persists."
            )

        return {
            "response": user_message,
            "error": error_message,
            "error_type": error_type,
            "success": False,
            "conversation_id": conversation_id,
        }
