"""
Slack Client for Konveyor.

This module provides functionality for interacting with Slack using the Slack SDK.
It handles sending messages, looking up users, and other Slack-related operations.
"""

import hashlib
import hmac
import logging
import random
import ssl
import time
from collections.abc import Callable
from typing import Any, TypeVar

# Removed: import certifi
from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Fix SSL certificate issues on macOS
ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger(__name__)

# Define a generic type for function return values
T = TypeVar("T")


def retry_on_slack_error(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 8.0,
    backoff_factor: float = 2.0,
):
    """
    Decorator to retry a function on Slack API errors with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Factor to increase delay with each retry

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T | None]) -> Callable[..., T | None]:
        def wrapper(*args, **kwargs) -> T | None:
            delay = initial_delay
            last_exception = None

            for retry in range(max_retries + 1):  # +1 for the initial attempt
                try:
                    if retry > 0:
                        logger.info(
                            f"Retry attempt {retry}/{max_retries} for {func.__name__}"
                        )
                    return func(*args, **kwargs)
                except SlackApiError as e:
                    last_exception = e
                    status_code = getattr(e.response, "status_code", None)

                    # Don't retry on client errors (4xx) except for 429 (rate limit)
                    if status_code and 400 <= status_code < 500 and status_code != 429:
                        logger.error(f"Non-retryable Slack API error: {str(e)}")
                        break

                    # For rate limiting (429), use the Retry-After header if available
                    if status_code == 429:
                        retry_after = getattr(e.response.headers, "Retry-After", None)
                        if retry_after:
                            delay = float(retry_after)
                            logger.warning(
                                f"Rate limited by Slack. Waiting {delay}s as specified by Retry-After header"  # noqa: E501
                            )

                    if retry < max_retries:
                        # Add jitter to avoid thundering herd problem
                        jitter = random.uniform(0, 0.1 * delay)
                        sleep_time = min(delay + jitter, max_delay)
                        logger.warning(
                            f"Slack API error: {str(e)}. Retrying in {sleep_time:.2f}s..."  # noqa: E501
                        )
                        time.sleep(sleep_time)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}: {str(e)}"  # noqa: E501
                        )
                except Exception as e:
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                    last_exception = e
                    break

            # If we got here, all retries failed
            if last_exception:
                logger.error(
                    f"All attempts failed for {func.__name__}: {str(last_exception)}"
                )
            return None

        return wrapper

    return decorator


class SlackService:
    """
    Service for interacting with Slack.

    This service provides methods for sending messages to channels and users,
    looking up user information, and verifying Slack requests.
    """

    def __init__(self, token: str | None = None):
        """
        Initialize the Slack service.

        Args:
            token: Optional Slack bot token (defaults to settings.SLACK_BOT_TOKEN)
        """
        self.token = token or getattr(settings, "SLACK_BOT_TOKEN", None)
        if not self.token:
            logger.warning(
                "No Slack token provided. Slack service will not function properly."
            )
            self.client = None
        else:
            self.client = WebClient(token=self.token)
            logger.info("Initialized Slack client with token")

    @retry_on_slack_error(max_retries=3)
    def send_message(
        self,
        channel: str,
        text: str,
        blocks: list[dict[str, Any]] | None = None,
        thread_ts: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Send a message to a Slack channel.

        Args:
            channel: The channel ID to send the message to
            text: The text of the message
            blocks: Optional blocks for rich formatting
            thread_ts: Optional thread timestamp to reply in a thread

        Returns:
            The Slack API response, or None if there was an error
        """
        if not self.client:
            logger.error("Cannot send message: Slack client not initialized")
            return None

        # Log at appropriate levels
        text_preview = text[:50] + ("..." if len(text) > 50 else "")
        logger.info(f"Sending message to channel {channel}")
        logger.debug(f"Message preview: {text_preview}")

        # Only log blocks at debug level
        if blocks:
            logger.debug("Using blocks for rich formatting")

        if thread_ts:
            logger.debug(f"Sending as reply in thread: {thread_ts}")

        kwargs = {"channel": channel, "text": text}

        if blocks:
            kwargs["blocks"] = blocks

        if thread_ts:
            kwargs["thread_ts"] = thread_ts

        try:
            response = self.client.chat_postMessage(**kwargs)
            logger.info(f"Message sent successfully to {channel}")
            return response
        except Exception as e:
            logger.error(f"Error sending message to Slack: {str(e)}")
            return None

    @retry_on_slack_error(max_retries=3)
    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
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

        logger.info(f"Looking up user by email: {email}")
        response = self.client.users_lookupByEmail(email=email)
        logger.info(f"Found user: {response.get('user', {}).get('name')}")
        return response.get("user")

    @retry_on_slack_error(max_retries=3)
    def send_direct_message(
        self,
        user_id: str,
        text: str,
        blocks: list[dict[str, Any]] | None = None,
        thread_ts: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Send a direct message to a user.

        Args:
            user_id: The Slack user ID
            text: The text of the message
            blocks: Optional blocks for rich formatting
            thread_ts: Optional thread timestamp to reply in a thread

        Returns:
            The Slack API response, or None if there was an error
        """
        if not self.client:
            logger.error("Cannot send direct message: Slack client not initialized")
            return None

        # Open a DM channel with the user
        logger.debug(f"Opening DM channel with user: {user_id}")
        try:
            conversations_open = self.client.conversations_open(users=[user_id])
            if not conversations_open["ok"]:
                logger.error(
                    f"Failed to open DM channel: {conversations_open.get('error', 'Unknown error')}"  # noqa: E501
                )
                return None

            # Get the channel ID
            channel_id = conversations_open["channel"]["id"]
            logger.debug(f"Created/retrieved DM channel: {channel_id}")

            # Send the message to the channel
            return self.send_message(channel_id, text, blocks, thread_ts)
        except Exception as e:
            logger.error(f"Error opening DM channel with user {user_id}: {str(e)}")
            return None

    def send_direct_message_by_email(
        self,
        email: str,
        text: str,
        blocks: list[dict[str, Any]] | None = None,
        thread_ts: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Send a direct message to a user by email.

        Args:
            email: The email address of the user
            text: The text of the message
            blocks: Optional blocks for rich formatting
            thread_ts: Optional thread timestamp to reply in a thread

        Returns:
            The Slack API response, or None if there was an error
        """
        user = self.get_user_by_email(email)
        if not user:
            logger.error(f"Could not find user with email: {email}")
            return None

        return self.send_direct_message(user.get("id"), text, blocks, thread_ts)

    @retry_on_slack_error(max_retries=3)
    def get_bot_user_id(self) -> str | None:
        """
        Get the bot's own user ID.

        Returns:
            The bot user ID, or None if there was an error
        """
        if not self.client:
            logger.error("Cannot get bot user ID: Slack client not initialized")
            return None

        auth_test = self.client.auth_test()
        if auth_test["ok"]:
            return auth_test["user_id"]
        else:
            logger.error(f"Auth test failed: {auth_test.get('error', 'Unknown error')}")
            return None

    @retry_on_slack_error(max_retries=3)
    def get_conversation_history(
        self, channel: str, limit: int = 10, thread_ts: str | None = None
    ) -> list[dict[str, Any]] | None:
        """
        Get the conversation history for a channel or thread.

        Args:
            channel: The channel ID
            limit: Maximum number of messages to return (default: 10)
            thread_ts: Optional thread timestamp to get replies from a thread

        Returns:
            List of messages, or None if there was an error
        """
        if not self.client:
            logger.error(
                "Cannot get conversation history: Slack client not initialized"
            )
            return None

        logger.info(f"Getting conversation history for channel {channel}")

        kwargs = {"channel": channel, "limit": limit}

        if thread_ts:
            logger.info(f"Getting thread replies for thread: {thread_ts}")
            kwargs["ts"] = thread_ts

        try:
            if thread_ts:
                # For thread replies, use conversations_replies
                response = self.client.conversations_replies(**kwargs)
            else:
                # For channel history, use conversations_history
                response = self.client.conversations_history(**kwargs)

            if not response["ok"]:
                logger.error(
                    f"Failed to get conversation history: {response.get('error', 'Unknown error')}"  # noqa: E501
                )
                return None

            messages = response.get("messages", [])
            logger.info(
                f"Retrieved {len(messages)} messages from {'thread' if thread_ts else 'channel'} {channel}"  # noqa: E501
            )
            return messages

        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return None

    @staticmethod
    def verify_request(
        request_body: bytes,
        signature: str,
        timestamp: str,
        signing_secret: str | None = None,
    ) -> bool:
        """
        Verify that a request is from Slack.

        Args:
            request_body: The raw request body
            signature: The X-Slack-Signature header
            timestamp: The X-Slack-Request-Timestamp header
            signing_secret: Optional signing secret (defaults to settings.SLACK_SIGNING_SECRET)  # noqa: E501

        Returns:
            True if the request is valid, False otherwise
        """
        # Get the signing secret from settings if not provided
        signing_secret = signing_secret or getattr(
            settings, "SLACK_SIGNING_SECRET", None
        )
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
        my_signature = f"v0={hmac.new(signing_secret.encode(), base_string.encode(), hashlib.sha256).hexdigest()}"  # noqa: E501

        # Compare the signatures
        result = hmac.compare_digest(my_signature, signature)
        if not result:
            logger.warning("Slack request signature verification failed")
        return result
