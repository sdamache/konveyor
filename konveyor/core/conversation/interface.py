"""
Conversation management interface for Konveyor.

This module defines the interface for conversation management, providing a common
contract for different implementations (in-memory, persistent storage, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union


class ConversationInterface(ABC):
    """
    Interface for conversation management.

    This interface defines the contract for managing conversations, including
    creating conversations, adding messages, and retrieving conversation history.
    Implementations can use different storage mechanisms (in-memory, MongoDB, etc.)
    while providing a consistent API.
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: Identifier for the conversation

        Returns:
            True if the conversation was deleted, False otherwise
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass
