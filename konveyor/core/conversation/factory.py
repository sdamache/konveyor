"""
Conversation manager factory for Konveyor.

This module provides a factory for creating conversation managers based on the
specified storage type and configuration.
"""

import logging
import os
from typing import Any, Dict, Optional

from konveyor.core.conversation.interface import ConversationInterface
from konveyor.core.conversation.memory import InMemoryConversationManager
from konveyor.core.conversation.storage import AzureStorageManager

logger = logging.getLogger(__name__)


class ConversationManagerFactory:
    """
    Factory for creating conversation managers.

    This class provides methods for creating conversation managers based on the
    specified storage type and configuration. It supports both in-memory and
    persistent storage options.
    """

    @staticmethod
    async def create_manager(
        storage_type: str = "memory", config: Optional[Dict[str, Any]] = None
    ) -> ConversationInterface:
        """
        Create a conversation manager.

        Args:
            storage_type: Type of storage to use ('memory', 'azure')
            config: Configuration for the storage

        Returns:
            A conversation manager implementing the ConversationInterface

        Raises:
            ValueError: If the storage type is not supported
        """
        if storage_type == "memory":
            logger.info("Creating in-memory conversation manager")
            return InMemoryConversationManager()

        elif storage_type == "azure":
            logger.info("Creating Azure conversation manager")

            # Get configuration
            cosmos_conn_str = config.get("cosmos_connection_string") if config else None
            redis_conn_str = config.get("redis_connection_string") if config else None

            # Fall back to environment variables if not provided
            if not cosmos_conn_str:
                cosmos_conn_str = os.environ.get("AZURE_COSMOS_CONNECTION_STRING")
            if not redis_conn_str:
                redis_conn_str = os.environ.get("AZURE_REDIS_CONNECTION_STRING")

            # Validate configuration
            if not cosmos_conn_str or not redis_conn_str:
                logger.warning(
                    "Missing Azure storage configuration, falling back to in-memory storage"  # noqa: E501
                )
                return InMemoryConversationManager()

            # Create Azure storage manager
            manager = AzureStorageManager(
                cosmos_connection_str=cosmos_conn_str,
                redis_connection_str=redis_conn_str,
            )

            # Initialize the manager
            await manager.initialize()

            return manager

        else:
            logger.error(f"Unsupported storage type: {storage_type}")
            raise ValueError(f"Unsupported storage type: {storage_type}")

    @staticmethod
    def get_default_storage_type() -> str:
        """
        Get the default storage type based on environment configuration.

        Returns:
            The default storage type ('memory' or 'azure')
        """
        # Check if Azure storage is configured
        cosmos_conn_str = os.environ.get("AZURE_COSMOS_CONNECTION_STRING")
        redis_conn_str = os.environ.get("AZURE_REDIS_CONNECTION_STRING")

        if cosmos_conn_str and redis_conn_str:
            return "azure"
        else:
            return "memory"
