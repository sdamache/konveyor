"""
Semantic Kernel Factory for Konveyor.

This module provides functions for creating and configuring Semantic Kernel instances
with Azure OpenAI integration. It handles all the configuration, validation, and
service registration needed for the kernel to function properly.
"""

import logging
import os
from typing import Any, Dict, Optional  # noqa: F401

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_text_embedding import (
    AzureTextEmbedding,
)
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore

from konveyor.core.azure_utils.clients import AzureClientManager
from konveyor.core.azure_utils.config import AzureConfig

logger = logging.getLogger(__name__)


def create_kernel(use_embeddings: bool = False, validate: bool = True) -> Kernel:
    """
    Create and configure the Semantic Kernel with Azure OpenAI chat and memory services.
    All configuration and secret logic is handled via konveyor/core utilities.

    Args:
        use_embeddings: Whether to add embedding service to the kernel
        validate: Whether to validate the required configuration

    Returns:
        Kernel: Configured Semantic Kernel instance.
    """
    config = AzureConfig()

    # Validate configuration if requested
    if validate:
        try:
            config.validate_required_config("OPENAI")
        except Exception as e:
            logger.warning(f"Failed to validate OpenAI configuration: {str(e)}")
            logger.warning(
                "Continuing without validation - this may cause issues if Azure OpenAI services are required"  # noqa: E501
            )

    # Get Azure OpenAI configuration
    endpoint = config.get_endpoint("OPENAI")
    key_or_secret_name = config.get_key("OPENAI")

    # Attempt to fetch API key from Key Vault; fallback to environment value if unavailable  # noqa: E501
    try:
        kv_client = AzureClientManager(config).get_key_vault_client()
        secret = kv_client.get_secret(key_or_secret_name)
        api_key = secret.value
        logger.info("Successfully retrieved OpenAI API key from Key Vault")
    except Exception as e:
        logger.warning(
            f"Failed to retrieve key from Key Vault, using environment variable: {str(e)}"  # noqa: E501
        )
        api_key = key_or_secret_name

    # Get deployment names and API version
    chat_deployment = (
        config.get_setting("AZURE_OPENAI_CHAT_DEPLOYMENT") or "gpt-35-turbo"
    )
    embedding_deployment = (
        config.get_setting("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        or "text-embedding-ada-002"
    )
    api_version = config.get_setting("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview"

    # Create kernel
    kernel = Kernel()

    # Add chat service
    try:
        chat_service = AzureChatCompletion(
            endpoint=endpoint,
            api_key=api_key,
            deployment_name=chat_deployment,
            api_version=api_version,
            service_id="chat",
        )
        kernel.add_service(chat_service)
        logger.debug(
            f"Added Azure OpenAI chat service with deployment: {chat_deployment}"
        )
    except Exception as e:
        logger.error(f"Failed to add chat service: {str(e)}")
        raise

    # Add embedding service if requested
    if use_embeddings:
        try:
            embedding_service = AzureTextEmbedding(
                endpoint=endpoint,
                api_key=api_key,
                deployment_name=embedding_deployment,
                api_version=api_version,
                service_id="embeddings",
            )
            kernel.add_service(embedding_service)
            logger.debug(
                f"Added Azure OpenAI embedding service with deployment: {embedding_deployment}"  # noqa: E501
            )
        except Exception as e:
            logger.warning(f"Failed to add embedding service: {str(e)}")

    # Register volatile memory store
    try:
        volatile_memory = VolatileMemoryStore()
        volatile_memory.service_id = "volatile"
        kernel.add_service(volatile_memory)
        logger.debug("Added volatile memory store")
    except Exception as e:
        logger.warning(f"Failed to add memory store: {str(e)}")

    return kernel


def get_kernel_settings() -> dict[str, Any]:
    """
    Get the current Semantic Kernel settings from environment variables.
    Useful for diagnostics and testing.

    Returns:
        Dict[str, Any]: Dictionary of kernel settings
    """
    config = AzureConfig()

    return {
        "endpoint": config.get_endpoint("OPENAI"),
        "chat_deployment": config.get_setting("AZURE_OPENAI_CHAT_DEPLOYMENT")
        or "gpt-35-turbo",
        "embedding_deployment": config.get_setting("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        or "text-embedding-ada-002",
        "api_version": config.get_setting("AZURE_OPENAI_API_VERSION")
        or "2024-12-01-preview",
        "has_key_vault": bool(os.environ.get("AZURE_KEY_VAULT_NAME")),
    }
