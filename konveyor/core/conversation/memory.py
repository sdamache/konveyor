"""
In-memory conversation storage for Konveyor.

This module provides an in-memory implementation of the ConversationInterface.
It's designed for development, testing, and scenarios where persistence is not required.
"""

import json  # noqa: F401
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from konveyor.core.conversation.interface import ConversationInterface

logger = logging.getLogger(__name__)


class InMemoryConversationManager(ConversationInterface):
    """
    In-memory implementation of the ConversationInterface.

    This class provides a simple in-memory storage for conversations and messages.
    It's useful for development, testing, and scenarios where persistence is not required.  # noqa: E501

    All data is stored in memory and will be lost when the application restarts.
    """

    def __init__(self):
        """Initialize the in-memory conversation manager."""
        self.conversations = {}  # conversation_id -> conversation
        self.messages = {}  # conversation_id -> list of messages
        logger.info("Initialized InMemoryConversationManager")

    async def create_conversation(
        self, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new conversation.

        Args:
            user_id: Optional user identifier
            metadata: Optional metadata for the conversation

        Returns:
            Dictionary containing conversation details
        """
        conversation_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        conversation = {
            "id": conversation_id,
            "user_id": user_id,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {},
        }

        self.conversations[conversation_id] = conversation
        self.messages[conversation_id] = []

        logger.debug(f"Created conversation: {conversation_id}")
        return conversation

    async def add_message(
        self,
        conversation_id: str,
        content: str,
        message_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add a message to a conversation.

        Args:
            conversation_id: Identifier for the conversation
            content: Message content
            message_type: Type of message (user, assistant, system, etc.)
            metadata: Optional metadata for the message

        Returns:
            Dictionary containing message details
        """
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation not found: {conversation_id}")
            raise ValueError(f"Conversation not found: {conversation_id}")

        message_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        message = {
            "id": message_id,
            "conversation_id": conversation_id,
            "type": message_type,
            "content": content,
            "metadata": metadata or {},
            "created_at": now,
        }

        self.messages[conversation_id].append(message)

        # Update conversation's updated_at timestamp
        self.conversations[conversation_id]["updated_at"] = now

        logger.debug(f"Added message to conversation {conversation_id}: {message_id}")
        return message

    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        skip: int = 0,
        include_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: Identifier for the conversation
            limit: Maximum number of messages to retrieve
            skip: Number of messages to skip
            include_metadata: Whether to include message metadata

        Returns:
            List of message dictionaries
        """
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation not found: {conversation_id}")
            return []

        messages = self.messages.get(conversation_id, [])

        # Sort by created_at (newest first)
        sorted_messages = sorted(messages, key=lambda m: m["created_at"], reverse=True)

        # Apply skip and limit
        result = sorted_messages[skip : skip + limit]

        # Remove metadata if not requested
        if not include_metadata:
            for message in result:
                message.pop("metadata", None)

        logger.debug(
            f"Retrieved {len(result)} messages for conversation {conversation_id}"
        )
        return result

    async def get_conversation_context(
        self,
        conversation_id: str,
        format: str = "string",
        max_messages: Optional[int] = None,
    ) -> Union[str, List[Dict[str, Any]]]:
        """
        Get the conversation context in the specified format.

        Args:
            conversation_id: Identifier for the conversation
            format: Format of the context ('string', 'dict', etc.)
            max_messages: Maximum number of messages to include in the context

        Returns:
            Conversation context in the specified format
        """
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation not found: {conversation_id}")
            return "" if format == "string" else []

        messages = self.messages.get(conversation_id, [])

        # Sort by created_at (oldest first)
        sorted_messages = sorted(messages, key=lambda m: m["created_at"])

        # Apply max_messages limit if specified
        if max_messages is not None:
            sorted_messages = sorted_messages[-max_messages:]

        if format == "string":
            # Format as a string
            context = ""
            for message in sorted_messages:
                role = message["type"].capitalize()
                content = message["content"]
                context += f"{role}: {content}\n"
            return context.strip()

        elif format == "dict":
            # Return as a list of dictionaries
            return sorted_messages

        elif format == "openai":
            # Format for OpenAI API
            openai_messages = []
            for message in sorted_messages:
                role = message["type"]
                # Map message types to OpenAI roles
                if role == "user":
                    openai_role = "user"
                elif role == "assistant":
                    openai_role = "assistant"
                elif role == "system":
                    openai_role = "system"
                else:
                    # Default to user for unknown roles
                    openai_role = "user"

                openai_messages.append(
                    {"role": openai_role, "content": message["content"]}
                )
            return openai_messages

        else:
            logger.warning(f"Unsupported format: {format}")
            return "" if format == "string" else []

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: Identifier for the conversation

        Returns:
            True if the conversation was deleted, False otherwise
        """
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation not found: {conversation_id}")
            return False

        # Remove the conversation and its messages
        self.conversations.pop(conversation_id, None)
        self.messages.pop(conversation_id, None)

        logger.debug(f"Deleted conversation: {conversation_id}")
        return True

    async def update_conversation_metadata(
        self, conversation_id: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update the metadata for a conversation.

        Args:
            conversation_id: Identifier for the conversation
            metadata: New metadata for the conversation

        Returns:
            Updated conversation dictionary
        """
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation not found: {conversation_id}")
            raise ValueError(f"Conversation not found: {conversation_id}")

        # Update the metadata
        current_metadata = self.conversations[conversation_id].get("metadata", {})
        current_metadata.update(metadata)
        self.conversations[conversation_id]["metadata"] = current_metadata

        # Update the updated_at timestamp
        self.conversations[conversation_id]["updated_at"] = datetime.now().isoformat()

        logger.debug(f"Updated metadata for conversation: {conversation_id}")
        return self.conversations[conversation_id]

    async def get_user_conversations(
        self, user_id: str, limit: int = 10, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get conversations for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of conversations to retrieve
            skip: Number of conversations to skip

        Returns:
            List of conversation dictionaries
        """
        # Filter conversations by user_id
        user_conversations = [
            conv
            for conv in self.conversations.values()
            if conv.get("user_id") == user_id
        ]

        # Sort by updated_at (newest first)
        sorted_conversations = sorted(
            user_conversations, key=lambda c: c["updated_at"], reverse=True
        )

        # Apply skip and limit
        result = sorted_conversations[skip : skip + limit]

        logger.debug(f"Retrieved {len(result)} conversations for user {user_id}")
        return result
