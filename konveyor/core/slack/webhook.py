"""
Slack Webhook Handler for Konveyor.

This module provides functionality for handling Slack webhook events,
including verification, event processing, and response generation.
"""

import json
import logging
import traceback
from typing import Dict, Any, Optional, Callable

from konveyor.core.slack.client import SlackService

logger = logging.getLogger(__name__)


class SlackWebhookHandler:
    """
    Handler for Slack webhook events.

    This class provides methods for verifying and processing Slack webhook events,
    and generating appropriate responses.
    """

    def __init__(self, slack_service: Optional[SlackService] = None):
        """
        Initialize the webhook handler.

        Args:
            slack_service: Optional SlackService instance (creates a new one if not provided)
        """
        self.slack_service = slack_service or SlackService()
        self.processed_events = set()
        logger.info("Initialized SlackWebhookHandler")

    def verify_request(
        self, request_body: bytes, signature: str, timestamp: str
    ) -> bool:
        """
        Verify that a request is from Slack.

        Args:
            request_body: The raw request body
            signature: The X-Slack-Signature header
            timestamp: The X-Slack-Request-Timestamp header

        Returns:
            True if the request is valid, False otherwise
        """
        return self.slack_service.verify_request(request_body, signature, timestamp)

    def process_event(
        self, payload: Dict[str, Any], process_message_func: Callable
    ) -> Optional[Dict[str, Any]]:
        """
        Process a Slack event.

        Args:
            payload: The parsed JSON payload from Slack
            process_message_func: Function to process messages

        Returns:
            Optional response data
        """
        event_type = payload.get("type")
        logger.debug(f"Processing Slack event: {event_type}")

        # Handle URL verification
        if event_type == "url_verification":
            challenge = payload.get("challenge")
            logger.info("Handling URL verification challenge")
            return {"challenge": challenge}

        # Handle events
        if event_type == "event_callback":
            event = payload.get("event", {})
            event_subtype = event.get("type")

            # Get the event ID and timestamp for deduplication
            event_id = payload.get("event_id", "")
            event_ts = event.get("ts", "")
            event_client_msg_id = event.get("client_msg_id", "")
            event_user = event.get("user", "")

            # Create a composite ID for more reliable deduplication
            import hashlib

            # Only hash the first 100 chars of text to avoid excessive logging
            event_text = event.get("text", "")
            text_preview = event_text[:100] + ("..." if len(event_text) > 100 else "")
            text_hash = (
                hashlib.md5(event_text.encode()).hexdigest()[:8] if event_text else ""
            )
            composite_id = (
                f"{event_id}:{event_ts}:{event_client_msg_id}:{event_user}:{text_hash}"
            )

            # Check if we've already processed this event
            if composite_id and composite_id in self.processed_events:
                logger.debug(f"Skipping duplicate event with ID: {event_id}")
                return None

            # Add this event to the processed set
            if composite_id:
                self.processed_events.add(composite_id)
                # Keep the set from growing too large
                if len(self.processed_events) > 1000:
                    self.processed_events = set(list(self.processed_events)[-1000:])
                    logger.debug(
                        f"Trimmed processed events to {len(self.processed_events)} items"
                    )

            # Process message events
            if event_subtype == "message":
                # Skip messages from our own bot to avoid infinite loops
                if event.get("bot_id") and event.get("app_id") == payload.get(
                    "api_app_id"
                ):
                    logger.debug("Skipping message from our own bot")
                    return None

                # Skip message subtypes like message_changed, message_deleted, etc.
                if event.get("subtype") and event.get("subtype") not in ["bot_message"]:
                    logger.debug(
                        f"Skipping message with subtype: {event.get('subtype')}"
                    )
                    return None

                channel = event.get("channel", "")
                user = event.get("user", "")
                channel_type = event.get("channel_type", "")
                thread_ts = event.get("thread_ts", None)

                logger.info(
                    f"Processing message from user {user} in {channel_type} {channel}"
                )
                logger.debug(f"Message text preview: {text_preview}")

                try:
                    # Process the message through the provided function
                    result = process_message_func(event_text, user, channel, thread_ts)
                    return result
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    logger.error(traceback.format_exc())
                    return {"error": str(e), "error_type": type(e).__name__}

        return None

    def send_response(
        self,
        response_text: str,
        user: str = None,
        channel: str = None,
        blocks: Optional[Dict[str, Any]] = None,
        thread_ts: Optional[str] = None,
        channel_type: str = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Send a response to Slack.

        Args:
            response_text: The text to send
            user: The user ID to send to (for direct messages)
            channel: The channel ID to send to (for channel messages)
            blocks: Optional blocks for rich formatting
            thread_ts: Optional thread timestamp to reply in a thread
            channel_type: The type of channel (e.g., 'im' for direct messages)

        Returns:
            The Slack API response, or None if there was an error
        """
        try:
            # For direct messages (im), use the send_direct_message method
            if channel_type == "im" and user:
                logger.info(f"Sending direct message response to user {user}")
                return self.slack_service.send_direct_message(
                    user, response_text, blocks, thread_ts
                )
            elif channel:
                # For channel messages, use the send_message method
                logger.info(f"Sending response to channel {channel}")
                return self.slack_service.send_message(
                    channel, response_text, blocks, thread_ts
                )
            else:
                logger.error("Cannot send response: no user or channel provided")
                return None
        except Exception as e:
            logger.error(f"Error sending response: {str(e)}")
            logger.error(traceback.format_exc())
            return None
