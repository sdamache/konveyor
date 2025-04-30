"""
Azure OpenAI client factory for Konveyor.

This module provides a factory for creating Azure OpenAI clients based on the
specified client type and configuration.
"""

import logging
import os
from typing import Optional, Dict, Any

from konveyor.core.azure_utils.openai_interface import OpenAIClientInterface
from konveyor.core.azure_utils.openai_client import UnifiedAzureOpenAIClient
from konveyor.core.azure_adapters.openai.client import (
    AzureOpenAIClient as CustomAzureOpenAIClient,
)

logger = logging.getLogger(__name__)


class OpenAIClientFactory:
    """
    Factory for creating Azure OpenAI clients.

    This class provides methods for creating Azure OpenAI clients based on the
    specified client type and configuration. It supports both the unified client
    and the custom client.
    """

    _clients = {}

    @classmethod
    def get_client(
        cls, client_type: str = "unified", config: Optional[Dict[str, Any]] = None
    ) -> OpenAIClientInterface:
        """
        Get an Azure OpenAI client.

        Args:
            client_type: Type of client to get ('unified', 'custom', 'sdk')
            config: Configuration for the client

        Returns:
            An Azure OpenAI client implementing the OpenAIClientInterface

        Raises:
            ValueError: If the client type is not supported
        """
        # Check if we already have an instance of this client type
        if client_type in cls._clients:
            return cls._clients[client_type]

        # Get configuration
        api_key = config.get("api_key") if config else None
        endpoint = config.get("endpoint") if config else None
        api_version = config.get("api_version") if config else None
        chat_deployment = config.get("chat_deployment") if config else None
        embedding_deployment = config.get("embedding_deployment") if config else None

        # Fall back to environment variables if not provided
        if not api_key:
            api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        if not endpoint:
            endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        if not api_version:
            api_version = os.environ.get(
                "AZURE_OPENAI_API_VERSION", "2024-12-01-preview"
            )
        if not chat_deployment:
            chat_deployment = os.environ.get(
                "AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-deployment"
            )
        if not embedding_deployment:
            embedding_deployment = os.environ.get(
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "embeddings"
            )

        # Create a new client instance
        if client_type == "unified":
            logger.debug("Creating unified Azure OpenAI client")
            client = UnifiedAzureOpenAIClient(
                api_key=api_key,
                endpoint=endpoint,
                api_version=api_version,
                chat_deployment=chat_deployment,
                embedding_deployment=embedding_deployment,
                use_sdk=True,
            )
        elif client_type == "custom":
            logger.debug("Creating custom Azure OpenAI client")
            client = CustomAzureOpenAIClient(
                api_key=api_key,
                endpoint=endpoint,
                gpt_api_version=api_version,
                embeddings_api_version=api_version,
                gpt_deployment=chat_deployment,
                embeddings_deployment=embedding_deployment,
            )
        elif client_type == "sdk":
            logger.debug("Creating SDK-based Azure OpenAI client")
            client = UnifiedAzureOpenAIClient(
                api_key=api_key,
                endpoint=endpoint,
                api_version=api_version,
                chat_deployment=chat_deployment,
                embedding_deployment=embedding_deployment,
                use_sdk=True,
            )
        else:
            logger.error(f"Unsupported client type: {client_type}")
            raise ValueError(f"Unsupported client type: {client_type}")

        # Cache the client instance
        cls._clients[client_type] = client

        return client

    @classmethod
    def register_client(cls, client_type: str, client: OpenAIClientInterface) -> None:
        """
        Register a custom client.

        Args:
            client_type: Type of client to register
            client: The client instance

        Raises:
            ValueError: If the client does not implement OpenAIClientInterface
        """
        if not isinstance(client, OpenAIClientInterface):
            raise ValueError("Client must implement OpenAIClientInterface")

        logger.debug(f"Registering custom client for {client_type}")
        cls._clients[client_type] = client
