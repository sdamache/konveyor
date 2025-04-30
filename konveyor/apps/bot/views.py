"""
Views for the bot app.

This module contains views for handling Slack webhook events and other bot-related
HTTP endpoints.

This updated version uses the new core components for conversation management,
message formatting, and response generation.
"""

import datetime
import json
import logging
import ssl
import traceback
from typing import Any, Dict, Optional

import certifi
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# Fix SSL certificate issues on macOS
ssl._create_default_https_context = ssl._create_unverified_context

from konveyor.apps.bot.services.slack_service import SlackService
from konveyor.apps.bot.services.slack_user_profile_service import \
    SlackUserProfileService
from konveyor.apps.bot.slash_commands import get_command_handler
from konveyor.core.agent import AgentOrchestratorSkill, SkillRegistry
from konveyor.core.chat import ChatSkill
from konveyor.core.conversation.factory import ConversationManagerFactory
from konveyor.core.conversation.feedback.factory import create_feedback_service
from konveyor.core.formatters.factory import FormatterFactory
from konveyor.core.kernel import create_kernel

# Import the feedback service directly from the core module
# This replaces the previous import from konveyor.apps.bot.services.feedback_service

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the Slack service
slack_service = SlackService()

# Initialize the Slack user profile service
slack_user_profile_service = SlackUserProfileService(slack_service=slack_service)

# Initialize the feedback service
feedback_service = create_feedback_service()

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
import asyncio

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
        import hashlib

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

        # Process reaction events
        if event_subtype == "reaction_added" or event_subtype == "reaction_removed":
            logger.info(f"Processing {event_subtype} event")

            # Extract reaction details
            reaction = event.get("reaction", "")
            user_id = event.get("user", "")
            item = event.get("item", {})

            logger.info(
                f"Reaction: {reaction}, User: {user_id}, Item type: {item.get('type', '')}"
            )

            # Process the reaction using the feedback service
            if item.get("type") == "message":
                try:
                    feedback = feedback_service.process_reaction_event(event)
                    if feedback:
                        logger.info(
                            f"Recorded feedback: {feedback.get('feedback_type')} from user {user_id}"
                        )
                    else:
                        logger.debug(f"No feedback recorded for reaction: {reaction}")
                except Exception as e:
                    logger.error(f"Error processing reaction: {str(e)}")
                    logger.error(traceback.format_exc())

            return HttpResponse(status=200)

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
            thread_ts = event.get(
                "thread_ts", None
            )  # Extract thread_ts for threaded messages

            # Log message details at appropriate levels
            thread_info = f" in thread {thread_ts}" if thread_ts else ""
            logger.info(
                f"Processing message from user {user} in {channel_type} {channel}{thread_info}"
            )
            text_preview = text[:50] + ("..." if len(text) > 50 else "")
            logger.debug(f"Message text preview: {text_preview}")

            try:
                # Process the message through the orchestrator
                logger.debug(
                    f"Calling process_message with user: {user}, channel: {channel}, thread_ts: {thread_ts}"
                )
                result = process_message(text, user, channel, thread_ts)

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
                    # Get thread_ts from the result or use the original thread_ts
                    result_thread_ts = result.get("thread_ts", thread_ts)
                    thread_info = (
                        f" in thread {result_thread_ts}" if result_thread_ts else ""
                    )

                    if channel_type == "im":
                        logger.info(
                            f"Sending direct message response to user {user}{thread_info}"
                        )
                        response = slack_service.send_direct_message(
                            user, response_text, blocks, thread_ts=result_thread_ts
                        )
                    else:
                        logger.info(
                            f"Sending response to channel {channel}{thread_info}"
                        )
                        response = slack_service.send_message(
                            channel, response_text, blocks, thread_ts=result_thread_ts
                        )

                    # Check if the Slack API response indicates an error
                    if not response.get("ok", False):
                        error_code = response.get("error", "unknown_error")
                        logger.error(
                            f"Slack API error: {error_code} when sending message to {channel_type} {channel}{thread_info}"
                        )

                        # Handle specific Slack API errors
                        if error_code == "channel_not_found":
                            logger.error(f"Channel {channel} not found")
                        elif error_code == "not_in_channel":
                            logger.error(f"Bot is not in channel {channel}")
                        elif error_code == "invalid_auth":
                            logger.error("Invalid authentication token")
                        elif error_code == "rate_limited":
                            retry_after = response.get("retry_after", 60)
                            logger.error(
                                f"Rate limited by Slack API. Retry after {retry_after} seconds"
                            )

                        # Don't raise an exception here, just log the error
                    else:
                        logger.debug(
                            f"Message sent successfully to {channel_type} {channel}{thread_info}"
                        )

                        # Store message content for potential feedback
                        try:
                            # Get the message timestamp from the response
                            message_ts = response.get("ts")
                            if message_ts:
                                # Update the feedback service with message content
                                feedback_service.update_message_content(
                                    message_id=message_ts,  # Changed from message_ts to message_id
                                    channel_id=channel,
                                    question=text,
                                    answer=response_text,
                                    skill_used=skill_name,
                                    function_used=result.get("function_name"),
                                    conversation_id=conversation_id,
                                )
                                logger.debug(
                                    f"Stored message content for feedback: {message_ts}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Error storing message content for feedback: {str(e)}"
                            )
                            logger.error(traceback.format_exc())
                except Exception as e:
                    error_type = type(e).__name__
                    error_message = str(e)
                    logger.error(
                        f"Error sending message: {error_type}: {error_message}"
                    )
                    logger.error(
                        f"Error details - Type: {error_type}, Message: {error_message}, User: {user}, Channel: {channel}"
                    )
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
                    thread_info = f" in thread {thread_ts}" if thread_ts else ""
                    if channel_type == "im":
                        logger.info(
                            f"Sending error message to user {user}{thread_info}"
                        )
                        response = slack_service.send_direct_message(
                            user, error_message, error_blocks, thread_ts=thread_ts
                        )
                    else:
                        logger.info(
                            f"Sending error message to channel {channel}{thread_info}"
                        )
                        response = slack_service.send_message(
                            channel, error_message, error_blocks, thread_ts=thread_ts
                        )

                    # Check if the Slack API response indicates an error
                    if not response.get("ok", False):
                        error_code = response.get("error", "unknown_error")
                        logger.error(
                            f"Slack API error when sending error message: {error_code}"
                        )
                    else:
                        logger.debug(
                            f"Error message sent successfully to {channel_type} {channel}{thread_info}"
                        )
                except Exception as send_error:
                    error_type = type(send_error).__name__
                    error_message = str(send_error)
                    logger.error(
                        f"Error sending error message: {error_type}: {error_message}"
                    )
                    logger.error(
                        f"Error details - Type: {error_type}, Message: {error_message}, User: {user}, Channel: {channel}"
                    )

                    # As a last resort, try to send a very simple message without blocks
                    try:
                        simple_message = "I encountered an error and couldn't process your request. Please try again later."
                        if channel_type == "im":
                            slack_service.send_direct_message(
                                user, simple_message, None, thread_ts=thread_ts
                            )
                        else:
                            slack_service.send_message(
                                channel, simple_message, None, thread_ts=thread_ts
                            )
                    except Exception:
                        # If even this fails, just log it and give up
                        logger.error("Failed to send simple error message as fallback")

    return HttpResponse(status=200)


@csrf_exempt
@require_POST
def slack_slash_command(request):
    """
    Handle Slack slash commands.

    This view receives slash commands from Slack, verifies them, and processes
    them using the appropriate command handler.

    Args:
        request: The HTTP request

    Returns:
        HTTP response
    """
    logger.debug(f"Received Slack slash command request to {request.path}")

    # Verify the request is from Slack
    slack_signature = request.headers.get("X-Slack-Signature", "")
    slack_timestamp = request.headers.get("X-Slack-Request-Timestamp", "")

    # Skip verification if headers are missing (for testing purposes)
    if not slack_signature or not slack_timestamp:
        logger.warning("Missing Slack verification headers, skipping verification")
    elif not slack_service.verify_request(
        request.body, slack_signature, slack_timestamp
    ):
        logger.warning("Failed to verify Slack slash command request")
        return HttpResponse(status=403)

    # Parse the request
    try:
        # Slack sends slash commands as form data
        command = request.POST.get("command", "").strip("/")
        text = request.POST.get("text", "")
        user_id = request.POST.get("user_id", "")
        channel_id = request.POST.get("channel_id", "")
        response_url = request.POST.get("response_url", "")

        logger.info(
            f"Received slash command: /{command} {text} from user {user_id} in channel {channel_id}"
        )

        # Get the command handler
        command_info = get_command_handler(command)
        if not command_info:
            logger.warning(f"Unknown slash command: /{command}")
            return JsonResponse(
                {
                    "response_type": "ephemeral",
                    "text": f"Sorry, I don't know the command `/{command}`. Try `/help` to see available commands.",
                }
            )

        # Execute the command handler
        handler = command_info["handler"]
        response = handler(text, user_id, channel_id, response_url)

        logger.info(f"Slash command /{command} processed successfully")
        return JsonResponse(response)

    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)
        logger.error(f"Error processing slash command: {error_type}: {error_message}")
        logger.error(traceback.format_exc())

        # Return an error message
        return JsonResponse(
            {
                "response_type": "ephemeral",
                "text": f"Sorry, I encountered an error processing your command: {error_message}",
            }
        )


def process_message(
    text: str, user_id: str, channel_id: str, thread_ts: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a message using the Agent Orchestration Layer.

    Args:
        text: The message text
        user_id: The Slack user ID
        channel_id: The Slack channel ID
        thread_ts: Optional thread timestamp for threaded messages

    Returns:
        The processed result
    """
    text_preview = text[:50] + ("..." if len(text) > 50 else "")
    thread_info = f" in thread {thread_ts}" if thread_ts else ""
    logger.debug(
        f"Processing message from user {user_id} in channel {channel_id}{thread_info}"
    )
    logger.debug(f"Message preview: {text_preview}")

    # Get or create user profile
    try:
        user_profile = slack_user_profile_service.get_or_create_profile(user_id)
        logger.debug(f"Retrieved user profile for {user_id}: {user_profile.slack_name}")
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        logger.error(traceback.format_exc())
        user_profile = None

    # Create context with user and channel information
    context = {
        "user_id": user_id,
        "channel_id": channel_id,
        "platform": "slack",
        "timestamp": datetime.datetime.now().isoformat(),
        "thread_ts": thread_ts,
    }

    # Add user profile information to context if available
    if user_profile:
        context["user_profile"] = {
            "name": user_profile.slack_real_name or user_profile.slack_name,
            "email": user_profile.slack_email,
            "code_language_preference": user_profile.code_language_preference,
            "response_format_preference": user_profile.get_preferred_response_format(),
            "interaction_count": user_profile.interaction_count,
        }

    # Get or create a conversation for this user
    conversation_id = None
    if conversation_manager:
        try:
            # Use asyncio to run the async method in a synchronous context
            import asyncio

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

            # Add the user's message to the conversation history
            async def add_user_message():
                await conversation_manager.add_message(
                    conversation_id=conversation_id,
                    content=text,
                    message_type="user",
                    metadata={
                        "channel_id": channel_id,
                        "thread_ts": thread_ts,
                        "platform": "slack",
                    },
                )
                logger.debug(f"Added user message to conversation {conversation_id}")

                # Retrieve conversation context
                conversation_context = (
                    await conversation_manager.get_conversation_context(
                        conversation_id=conversation_id,
                        format="openai",
                        max_messages=10,  # Limit to last 10 messages for context
                    )
                )
                logger.debug(
                    f"Retrieved conversation context with {len(conversation_context)} messages"
                )

                return conversation_context

            # Run the async function
            conversation_context = asyncio.run(add_user_message())

            # Add conversation context to the context
            context["conversation_history"] = conversation_context
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

        # Add the conversation ID and thread_ts to the result
        if conversation_id:
            result["conversation_id"] = conversation_id

            # Store the assistant's response in the conversation history
            response_text = result.get("response", "")
            if response_text and conversation_manager:
                try:
                    # Use asyncio to run the async method in a synchronous context
                    async def add_assistant_message():
                        await conversation_manager.add_message(
                            conversation_id=conversation_id,
                            content=response_text,
                            message_type="assistant",
                            metadata={
                                "skill_name": result.get("skill_name", "unknown"),
                                "function_name": result.get("function_name", "unknown"),
                                "thread_ts": thread_ts,
                                "platform": "slack",
                            },
                        )
                        logger.debug(
                            f"Added assistant response to conversation {conversation_id}"
                        )

                    # Run the async function
                    asyncio.run(add_assistant_message())
                except Exception as e:
                    logger.error(
                        f"Error adding assistant message to conversation: {str(e)}"
                    )
                    logger.error(traceback.format_exc())

        # Add thread_ts to the result if available
        if thread_ts:
            result["thread_ts"] = thread_ts

        return result
    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)

        # Log structured error information
        logger.error(f"Error in orchestrator: {error_type}: {error_message}")
        logger.error(traceback.format_exc())

        # Create a user-friendly error message
        user_message = "I encountered an error while processing your request."

        # Map common error types to user-friendly messages
        error_messages = {
            "ValueError": f" {error_message}",
            "KeyError": " I couldn't find some required information.",
            "TimeoutError": " The operation timed out. Please try again later.",
            "ConnectionError": " I'm having trouble connecting to a required service. Please try again later.",
            "AuthenticationError": " There was an authentication issue. Please contact support.",
            "PermissionError": " I don't have permission to access the requested resource.",
            "ResourceNotFoundError": " The requested resource could not be found.",
            "RateLimitError": " We've hit a rate limit. Please try again in a few minutes.",
            "InvalidRequestError": " The request was invalid. Please check your input and try again.",
            "ServiceUnavailableError": " A required service is currently unavailable. Please try again later.",
        }

        # Add the specific error message if available, otherwise use a generic message
        user_message += error_messages.get(
            error_type, " Please try again or contact support if the issue persists."
        )

        # Log the error with additional context
        logger.error(
            f"Error details - Type: {error_type}, Message: {error_message}, User: {user_id}, Channel: {channel_id}"
        )

        result = {
            "response": user_message,
            "error": error_message,
            "error_type": error_type,
            "success": False,
            "conversation_id": conversation_id,
        }

        # Add thread_ts to the result if available
        if thread_ts:
            result["thread_ts"] = thread_ts

        # Store the error message in the conversation history
        if conversation_id and conversation_manager:
            try:
                # Use asyncio to run the async method in a synchronous context
                async def add_error_message():
                    await conversation_manager.add_message(
                        conversation_id=conversation_id,
                        content=user_message,
                        message_type="assistant",
                        metadata={
                            "error": True,
                            "error_type": error_type,
                            "error_message": error_message,
                            "thread_ts": thread_ts,
                            "platform": "slack",
                        },
                    )
                    logger.debug(
                        f"Added error message to conversation {conversation_id}"
                    )

                # Run the async function
                asyncio.run(add_error_message())
            except Exception as e:
                logger.error(f"Error adding error message to conversation: {str(e)}")
                logger.error(traceback.format_exc())

        return result
