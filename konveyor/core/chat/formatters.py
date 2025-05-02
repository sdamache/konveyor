"""
Chat Message Formatters for Konveyor.

This module provides utilities for formatting chat messages,
including conversation history formatting and message structuring.
"""

import logging
from typing import Any, Dict, List, Optional  # noqa: F401

logger = logging.getLogger(__name__)


def format_conversation_history(messages: List[Dict[str, Any]]) -> str:
    """
    Format a list of messages into a conversation history string.

    Args:
        messages: List of message dictionaries with 'role' and 'content' keys

    Returns:
        Formatted conversation history string
    """
    history = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        if role == "user":
            history.append(f"User: {content}")
        elif role == "assistant":
            history.append(f"Assistant: {content}")
        elif role == "system":
            # Optionally include system messages
            history.append(f"System: {content}")

    return "\n".join(history)


def parse_conversation_history(history: str) -> List[Dict[str, Any]]:
    """
    Parse a conversation history string into a list of message dictionaries.

    Args:
        history: Conversation history string

    Returns:
        List of message dictionaries with 'role' and 'content' keys
    """
    if not history:
        return []

    messages = []
    lines = history.split("\n")
    current_role = None
    current_content = []

    for line in lines:
        if line.startswith("User: "):
            # Save the previous message if there is one
            if current_role:
                messages.append(
                    {"role": current_role, "content": "\n".join(current_content)}
                )

            # Start a new user message
            current_role = "user"
            current_content = [line[6:]]  # Remove "User: " prefix
        elif line.startswith("Assistant: "):
            # Save the previous message if there is one
            if current_role:
                messages.append(
                    {"role": current_role, "content": "\n".join(current_content)}
                )

            # Start a new assistant message
            current_role = "assistant"
            current_content = [line[11:]]  # Remove "Assistant: " prefix
        elif line.startswith("System: "):
            # Save the previous message if there is one
            if current_role:
                messages.append(
                    {"role": current_role, "content": "\n".join(current_content)}
                )

            # Start a new system message
            current_role = "system"
            current_content = [line[8:]]  # Remove "System: " prefix
        else:
            # Continue the current message
            current_content.append(line)

    # Add the last message
    if current_role:
        messages.append({"role": current_role, "content": "\n".join(current_content)})

    return messages


def create_chat_context(
    user_id: str, channel_id: str, history: str = ""
) -> Dict[str, Any]:
    """
    Create a context dictionary for a chat interaction.

    Args:
        user_id: The user ID
        channel_id: The channel ID
        history: Optional conversation history

    Returns:
        Context dictionary
    """
    import datetime

    return {
        "user_id": user_id,
        "channel_id": channel_id,
        "platform": "slack",
        "timestamp": datetime.datetime.now().isoformat(),
        "history": history,
    }
