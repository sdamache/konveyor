"""
Slack Service for Konveyor.

This service provides functionality for interacting with Slack using the Slack SDK.
It handles sending messages, looking up users, and other Slack-related operations.
"""

import logging
import hmac
import hashlib
import time
import ssl
import certifi
from typing import Dict, Any, Optional, List
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from django.conf import settings

# Fix SSL certificate issues on macOS
ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger(__name__)

class SlackService:
    """
    Service for interacting with Slack.

    This service provides methods for sending messages to channels and users,
    looking up user information, and verifying Slack requests.
    """

    def __init__(self, token: Optional[str] = None):
        """
        Initialize the Slack service.

        Args:
            token: Optional Slack bot token (defaults to settings.SLACK_BOT_TOKEN)
        """
        self.token = token or getattr(settings, 'SLACK_BOT_TOKEN', None)
        if not self.token:
            logger.warning("No Slack token provided. Slack service will not function properly.")
            self.client = None
        else:
            self.client = WebClient(token=self.token)
            logger.info("Initialized Slack client with token")

    def send_message(self, channel: str, text: str, blocks: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """
        Send a message to a Slack channel.

        Args:
            channel: The channel ID to send the message to
            text: The text of the message
            blocks: Optional blocks for rich formatting

        Returns:
            The Slack API response, or None if there was an error
        """
        if not self.client:
            logger.error("Cannot send message: Slack client not initialized")
            return None

        try:
            logger.info(f"Sending message to channel {channel}: {text[:50]}...")

            kwargs = {
                "channel": channel,
                "text": text
            }

            if blocks:
                kwargs["blocks"] = blocks

            response = self.client.chat_postMessage(**kwargs)
            logger.info(f"Message sent successfully to {channel}")
            return response
        except SlackApiError as e:
            logger.error(f"Error sending message to Slack: {str(e)}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get a Slack user by email address.

        Args:
            email: The email address of the user

        Returns:
            The user information, or None if not found
        """
        if not self.client:
            logger.error("Cannot get user: Slack client not initialized")
            return None

        try:
            logger.info(f"Looking up user by email: {email}")
            response = self.client.users_lookupByEmail(email=email)
            logger.info(f"Found user: {response.get('user', {}).get('name')}")
            return response.get('user')
        except SlackApiError as e:
            logger.error(f"Error looking up Slack user: {str(e)}")
            return None

    def send_direct_message(self, user_id: str, text: str, blocks: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """
        Send a direct message to a user.

        Args:
            user_id: The Slack user ID
            text: The text of the message
            blocks: Optional blocks for rich formatting

        Returns:
            The Slack API response, or None if there was an error
        """
        if not self.client:
            logger.error("Cannot send direct message: Slack client not initialized")
            return None

        try:
            # Open a DM channel with the user
            logger.info(f"Opening DM channel with user: {user_id}")
            conversations_open = self.client.conversations_open(users=[user_id])
            if not conversations_open["ok"]:
                logger.error(f"Failed to open DM channel: {conversations_open.get('error', 'Unknown error')}")
                return None

            # Get the channel ID
            channel_id = conversations_open["channel"]["id"]
            logger.info(f"Created/retrieved DM channel: {channel_id}")

            # Send the message to the channel
            return self.send_message(channel_id, text, blocks)
        except SlackApiError as e:
            logger.error(f"Error sending direct message: {str(e)}")
            return None

    def send_direct_message_by_email(self, email: str, text: str, blocks: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """
        Send a direct message to a user by email.

        Args:
            email: The email address of the user
            text: The text of the message
            blocks: Optional blocks for rich formatting

        Returns:
            The Slack API response, or None if there was an error
        """
        user = self.get_user_by_email(email)
        if not user:
            logger.error(f"Could not find user with email: {email}")
            return None

        return self.send_direct_message(user.get('id'), text, blocks)

    def get_bot_user_id(self) -> Optional[str]:
        """
        Get the bot's own user ID.

        Returns:
            The bot user ID, or None if there was an error
        """
        if not self.client:
            logger.error("Cannot get bot user ID: Slack client not initialized")
            return None

        try:
            auth_test = self.client.auth_test()
            if auth_test["ok"]:
                return auth_test["user_id"]
            else:
                logger.error(f"Auth test failed: {auth_test.get('error', 'Unknown error')}")
                return None
        except SlackApiError as e:
            logger.error(f"Error getting bot user ID: {str(e)}")
            return None

    @staticmethod
    def verify_request(request_body: bytes, signature: str, timestamp: str, signing_secret: Optional[str] = None) -> bool:
        """
        Verify that a request is from Slack.

        Args:
            request_body: The raw request body
            signature: The X-Slack-Signature header
            timestamp: The X-Slack-Request-Timestamp header
            signing_secret: Optional signing secret (defaults to settings.SLACK_SIGNING_SECRET)

        Returns:
            True if the request is valid, False otherwise
        """
        # Get the signing secret from settings if not provided
        signing_secret = signing_secret or getattr(settings, 'SLACK_SIGNING_SECRET', None)
        if not signing_secret:
            logger.error("No Slack signing secret available for request verification")
            return False

        # Check if the timestamp is too old (prevent replay attacks)
        if abs(time.time() - int(timestamp)) > 60 * 5:
            logger.warning(f"Slack request timestamp too old: {timestamp}")
            return False

        # Create a base string using the timestamp and request body
        base_string = f"v0:{timestamp}:{request_body.decode('utf-8')}"

        # Create a signature using the Slack signing secret
        my_signature = f"v0={hmac.new(signing_secret.encode(), base_string.encode(), hashlib.sha256).hexdigest()}"

        # Compare the signatures
        result = hmac.compare_digest(my_signature, signature)
        if not result:
            logger.warning("Slack request signature verification failed")
        return result
