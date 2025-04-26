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

# Register the ChatSkill
chat_skill = ChatSkill()
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
    logger.info(f"Received request to root URL with method {request.method}")

    # If it's a POST request, it might be a Slack verification
    if request.method == 'POST':
        try:
            body_str = request.body.decode('utf-8')
            logger.info(f"Root handler request body: {body_str[:100]}...")

            # Try to parse as JSON
            payload = json.loads(body_str)

            # If it's a URL verification challenge, respond with the challenge
            if payload.get('type') == 'url_verification':
                logger.info("Root handler: Detected URL verification challenge")
                return JsonResponse({'challenge': payload.get('challenge')})

        except Exception as e:
            logger.error(f"Root handler error: {str(e)}")

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
    logger.info(f"Received request to {request.path} with method {request.method}")
    logger.info(f"Headers: {request.headers}")

    # Verify the request is from Slack
    slack_signature = request.headers.get('X-Slack-Signature', '')
    slack_timestamp = request.headers.get('X-Slack-Request-Timestamp', '')

    # Skip verification for URL verification challenges (initial setup)
    is_verification = False
    try:
        body_str = request.body.decode('utf-8')
        logger.info(f"Request body: {body_str[:100]}...")
        if '"type":"url_verification"' in body_str or '"challenge":' in body_str:
            is_verification = True
            logger.info("Detected URL verification challenge")
    except Exception as e:
        logger.error(f"Error decoding request body: {str(e)}")

    if not is_verification and not slack_service.verify_request(request.body, slack_signature, slack_timestamp):
        logger.warning("Failed to verify Slack request")
        return HttpResponse(status=403)

    # Parse the request
    try:
        payload = json.loads(request.body)
        logger.info(f"Received Slack event: {payload.get('type')}")
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON payload")
        return HttpResponse(status=400)

    # Handle URL verification
    if payload.get('type') == 'url_verification':
        logger.info("Handling URL verification challenge")
        return JsonResponse({'challenge': payload.get('challenge')})

    # Handle events
    if payload.get('type') == 'event_callback':
        event = payload.get('event', {})

        # Only process message events that aren't from a bot
        if event.get('type') == 'message' and not event.get('bot_id'):
            text = event.get('text', '')
            channel = event.get('channel', '')
            user = event.get('user', '')
            channel_type = event.get('channel_type', '')

            logger.info(f"Processing message from user {user} in {channel_type} {channel}: {text}")

            try:
                # Process the message through the orchestrator
                result = process_message(text, user, channel)

                # Send the response back to Slack
                response_text = result.get('response', 'Sorry, I could not process your request.')

                # For direct messages (im), use the send_direct_message method
                if channel_type == 'im':
                    logger.info(f"Sending direct message response to user {user}")
                    slack_service.send_direct_message(user, response_text)
                else:
                    # For channel messages, use the send_message method
                    logger.info(f"Sending response to channel {channel}")
                    slack_service.send_message(channel, response_text)

                logger.info(f"Sent response to {channel_type} {channel}")
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                logger.error(traceback.format_exc())

                error_message = f"Sorry, I encountered an error: {str(e)}"

                # Send error message to the appropriate channel type
                if channel_type == 'im':
                    slack_service.send_direct_message(user, error_message)
                else:
                    slack_service.send_message(channel, error_message)

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
    # Create context with user and channel information
    context = {
        "user_id": user_id,
        "channel_id": channel_id,
        "platform": "slack"
    }

    # Process the request through the orchestrator
    try:
        result = orchestrator.process_request_sync(text, context)
        logger.info(f"Orchestrator processed request successfully")
        return result
    except Exception as e:
        logger.error(f"Error in orchestrator.process_request_sync: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "response": f"I encountered an error while processing your request: {str(e)}",
            "error": str(e)
        }
