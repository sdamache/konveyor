"""
Unified Azure OpenAI client for Konveyor.

This module provides a unified client for Azure OpenAI services that implements
the OpenAIClientInterface. It adapts the existing AzureOpenAI client from the
OpenAI SDK and the custom AzureOpenAIClient implementation.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

from openai import AzureOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from konveyor.core.azure_adapters.openai.client import (
    AzureOpenAIClient as CustomAzureOpenAIClient,
)
from konveyor.core.azure_utils.openai_interface import OpenAIClientInterface

logger = logging.getLogger(__name__)


class UnifiedAzureOpenAIClient(OpenAIClientInterface):
    """
    Unified client for Azure OpenAI services.

    This class implements the OpenAIClientInterface and adapts the existing
    AzureOpenAI client from the OpenAI SDK and the custom AzureOpenAIClient
    implementation. It provides a consistent interface for generating completions
    and embeddings.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
        chat_deployment: Optional[str] = None,
        embedding_deployment: Optional[str] = None,
        use_sdk: bool = True,
    ):
        """
        Initialize the unified Azure OpenAI client.

        Args:
            api_key: Azure OpenAI API key
            endpoint: Azure OpenAI endpoint URL
            api_version: API version
            chat_deployment: Chat model deployment name
            embedding_deployment: Embedding model deployment name
            use_sdk: Whether to use the OpenAI SDK client (True) or the custom client (False)
        """
        # Load configuration from environment variables if not provided
        self.api_key = api_key or os.environ.get("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.api_version = api_version or os.environ.get(
            "AZURE_OPENAI_API_VERSION", "2024-12-01-preview"
        )
        self.chat_deployment = chat_deployment or os.environ.get(
            "AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-deployment"
        )
        self.embedding_deployment = embedding_deployment or os.environ.get(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "embeddings"
        )

        # Validate configuration
        if not self.api_key:
            logger.error("Azure OpenAI API key is not configured")
            raise ValueError("Azure OpenAI API key is required")

        if not self.endpoint:
            logger.error("Azure OpenAI endpoint is not configured")
            raise ValueError("Azure OpenAI endpoint is required")

        # Initialize the appropriate client
        self.use_sdk = use_sdk

        if use_sdk:
            logger.info("Using OpenAI SDK client")
            self.sdk_client = AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version=self.api_version,
            )
        else:
            logger.info("Using custom Azure OpenAI client")
            self.custom_client = CustomAzureOpenAIClient(
                api_key=self.api_key,
                endpoint=self.endpoint,
                gpt_api_version=self.api_version,
                embeddings_api_version=self.api_version,
                gpt_deployment=self.chat_deployment,
                embeddings_deployment=self.embedding_deployment,
            )

    def generate_completion(
        self, messages: List[Dict[str, str]], max_tokens: int = 1000
    ) -> str:
        """
        Generate a chat completion response.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate

        Returns:
            The generated text response
        """
        try:
            if self.use_sdk:
                # Use the OpenAI SDK client
                response = self.sdk_client.chat.completions.create(
                    model=self.chat_deployment, messages=messages, max_tokens=max_tokens
                )
                return response.choices[0].message.content
            else:
                # Use the custom client
                return self.custom_client.generate_completion(messages, max_tokens)
        except Exception as e:
            logger.error(f"Error generating completion: {str(e)}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text.

        Args:
            text: The text to generate an embedding for

        Returns:
            A list of floats representing the embedding vector
        """
        try:
            if self.use_sdk:
                # Use the OpenAI SDK client
                response = self.sdk_client.embeddings.create(
                    model=self.embedding_deployment, input=text
                )
                return response.data[0].embedding
            else:
                # Use the custom client
                return self.custom_client.generate_embedding(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def generate_completion_with_retry(
        self, messages: List[Dict[str, str]], max_tokens: int = 1000
    ) -> str:
        """
        Generate a chat completion response with automatic retries.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate

        Returns:
            The generated text response
        """
        return self.generate_completion(messages, max_tokens)
