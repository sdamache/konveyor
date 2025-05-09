"""
Azure OpenAI client interface for Konveyor.

This module defines the interface for interacting with Azure OpenAI services,
providing a common contract for different implementations.

This interface is designed to be compatible with both:
1. The AzureOpenAI client from the OpenAI SDK (used in konveyor/core/azure_utils/clients.py)  # noqa: E501
2. The custom AzureOpenAIClient implementation (in konveyor/core/azure_adapters/openai/client.py)  # noqa: E501
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union  # noqa: F401, F401, F401


class OpenAIClientInterface(ABC):
    """
    Interface for Azure OpenAI client.

    This interface defines the contract for interacting with Azure OpenAI services,
    including generating completions and embeddings. It's designed to be compatible
    with existing implementations in the codebase.

    Implementations:
    - AzureOpenAI from OpenAI SDK (via AzureClientManager.get_openai_client)
    - AzureOpenAIClient in konveyor/core/azure_adapters/openai/client.py
    """

    @abstractmethod
    def generate_completion(
        self, messages: list[dict[str, str]], max_tokens: int = 1000
    ) -> str:
        """
        Generate a chat completion response.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate

        Returns:
            The generated text response
        """

    @abstractmethod
    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate an embedding for the given text.

        Args:
            text: The text to generate an embedding for

        Returns:
            A list of floats representing the embedding vector
        """
