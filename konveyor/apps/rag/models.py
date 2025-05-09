"""
Models for the RAG Django app using Azure storage.
"""

from datetime import datetime  # noqa: F401

from django.conf import settings

from konveyor.core.conversation.storage import AzureStorageManager


class ConversationManager:
    """Manager for conversation operations using Azure storage."""

    def __init__(self):
        self.storage = AzureStorageManager(
            cosmos_connection_str=settings.AZURE_COSMOS_CONNECTION_STRING,
            redis_connection_str=settings.AZURE_REDIS_CONNECTION_STRING,
        )

    async def create_conversation(self, user_id: str | None = None) -> dict:
        """Create a new conversation."""
        return await self.storage.create_conversation(user_id)

    async def add_message(
        self,
        conversation_id: str,
        content: str,
        message_type: str = "user",
        metadata: dict | None = None,
    ) -> dict:
        """Add a message to a conversation."""
        return await self.storage.add_message(
            conversation_id=conversation_id,
            message_type=message_type,
            content=content,
            metadata=metadata,
        )

    async def get_conversation_messages(
        self, conversation_id: str, limit: int = 50
    ) -> list[dict]:
        """Get messages for a conversation."""
        return await self.storage.get_conversation_messages(
            conversation_id=conversation_id, limit=limit
        )


# Constants for message types
MESSAGE_TYPE_USER = "user"
MESSAGE_TYPE_ASSISTANT = "assistant"
MESSAGE_TYPES = [MESSAGE_TYPE_USER, MESSAGE_TYPE_ASSISTANT]
