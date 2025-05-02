import logging
import os
from typing import Any  # Any type
from typing import Dict  # Dictionary type
from typing import List  # List type
from typing import Optional  # Optional type (equivalent to Union[Type, None])
from typing import Set  # Set type
from typing import Tuple  # Tuple type
from typing import Union  # Union of types

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Set up logging
logger = logging.getLogger(__name__)


class AzureOpenAIClient:
    """Client for interacting with Azure OpenAI API.

    This client provides utilities for generating embeddings and chat completions
    using Azure OpenAI services, with proper API version handling for different models.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        embeddings_api_version: Optional[str] = None,
        gpt_api_version: Optional[str] = None,
        gpt_deployment: Optional[str] = None,
        embeddings_deployment: Optional[str] = None,
    ):
        """Initialize the Azure OpenAI client.

        Args:
            api_key: Azure OpenAI API key
            endpoint: Azure OpenAI endpoint URL
            embeddings_api_version: API version for embeddings (defaults to 2023-05-15)
            gpt_api_version: API version for GPT models (defaults to 2024-12-01-preview)
            gpt_deployment: GPT model deployment name
            embeddings_deployment: Embeddings model deployment name
        """
        # Load configuration from environment variables if not provided
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.getenv(
            "AZURE_OPENAI_ENDPOINT", "https://eastus.api.cognitive.microsoft.com/"
        )
        self.embeddings_api_version = embeddings_api_version or os.getenv(
            "AZURE_OPENAI_EMBEDDING_API_VERSION", "2023-05-15"
        )
        self.gpt_api_version = gpt_api_version or os.getenv(
            "AZURE_OPENAI_API_VERSION", "2024-12-01-preview"
        )
        self.gpt_deployment = gpt_deployment or os.getenv(
            "AZURE_OPENAI_GPT_DEPLOYMENT", "gpt-deployment"
        )
        self.embeddings_deployment = embeddings_deployment or os.getenv(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "embeddings"
        )

        # Remove trailing slash from endpoint if present
        if self.endpoint.endswith("/"):
            self.endpoint = self.endpoint[:-1]

        # Validate configuration
        if not self.api_key:
            logger.error("Azure OpenAI API key is not configured")
            raise ValueError("Azure OpenAI API key is required")

        if not self.endpoint:
            logger.error("Azure OpenAI endpoint is not configured")
            raise ValueError("Azure OpenAI endpoint is required")

        logger.info(f"Azure OpenAI client initialized with endpoint: {self.endpoint}")
        logger.info(f"Embeddings API version: {self.embeddings_api_version}")
        logger.info(f"GPT API version: {self.gpt_api_version}")
        logger.info(f"GPT deployment: {self.gpt_deployment}")
        logger.info(f"Embeddings deployment: {self.embeddings_deployment}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for the given text.

        Args:
            text: The text to generate an embedding for

        Returns:
            A list of floats representing the embedding vector

        Raises:
            Exception: If embedding generation fails
        """
        try:
            # Truncate text if too long (OpenAI has token limits)
            truncated_text = text[:8000]  # Adjust limit based on your needs
            if len(truncated_text) < len(text):
                logger.info(
                    f"Truncated text from {len(text)} to {len(truncated_text)} chars"
                )

            # Construct the URL for embeddings deployment
            embeddings_url = f"{self.endpoint}/openai/deployments/{self.embeddings_deployment}/embeddings?api-version={self.embeddings_api_version}"

            # Prepare the request payload for embeddings
            payload = {"input": truncated_text}

            # Set up headers with API key
            headers = {"Content-Type": "application/json", "api-key": self.api_key}

            # Make the REST API call
            logger.info(
                f"Generating embedding for text of length {len(truncated_text)}"
            )
            response = requests.post(embeddings_url, headers=headers, json=payload)

            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                embedding = result["data"][0]["embedding"]
                logger.info(
                    f"Successfully generated embedding with {len(embedding)} dimensions"
                )
                return embedding
            else:
                error_msg = f"Embedding Error: {response.status_code} - {response.text}"
                logger.error(error_msg)

                # Additional diagnostic info
                if response.status_code == 404:
                    logger.error(
                        "404 error indicates the resource was not found. Check:"
                    )
                    logger.error("1. OpenAI endpoint URL is correct")
                    logger.error(
                        "2. API key is valid and has access to the embeddings model"
                    )
                    logger.error("3. The deployment name is correct")
                    logger.error("4. The model is deployed to your OpenAI resource")
                    logger.error(
                        f"Current deployment name: {self.embeddings_deployment}"
                    )

                raise Exception(error_msg)

        except Exception as e:
            error_msg = f"Error generating embedding: {str(e)}"
            logger.error(error_msg)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def generate_completion(
        self, messages: List[Dict[str, str]], max_tokens: int = 1000
    ) -> str:
        """Generate a chat completion response.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate

        Returns:
            The generated text response

        Raises:
            Exception: If completion generation fails
        """
        try:
            # Construct the URL for GPT deployment
            gpt_url = f"{self.endpoint}/openai/deployments/{self.gpt_deployment}/chat/completions?api-version={self.gpt_api_version}"

            logger.info(f"Using API version {self.gpt_api_version} for GPT completion")

            # Prepare the request payload
            payload = {"messages": messages, "max_tokens": max_tokens}

            # Set up headers with API key
            headers = {"Content-Type": "application/json", "api-key": self.api_key}

            # Make the REST API call
            logger.info(f"Generating completion with {len(messages)} messages")
            response = requests.post(gpt_url, headers=headers, json=payload)

            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                logger.info(
                    f"Successfully generated completion of length {len(content)}"
                )
                return content
            else:
                error_msg = (
                    f"Completion Error: {response.status_code} - {response.text}"
                )
                logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            error_msg = f"Error generating completion: {str(e)}"
            logger.error(error_msg)
            raise


# Example usage
if __name__ == "__main__":
    # Set up basic logging for testing
    logging.basicConfig(level=logging.INFO)

    # Create client
    client = AzureOpenAIClient()

    # Test embedding generation
    try:
        embedding = client.generate_embedding("This is a test for embeddings")
        print(f"Embedding generated successfully with {len(embedding)} dimensions")
        print(f"First few values: {embedding[:5]}")
    except Exception as e:
        print(f"Embedding generation failed: {str(e)}")

    # Test completion generation
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, who are you?"},
        ]
        completion = client.generate_completion(messages)
        print(f"Completion generated successfully:\n{completion}")
    except Exception as e:
        print(f"Completion generation failed: {str(e)}")
