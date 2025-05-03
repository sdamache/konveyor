"""Mixins for Azure services providing common functionality."""

import logging
import os
from typing import Any, Optional  # noqa: F401

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from openai import AzureOpenAI

from konveyor.core.azure_adapters.openai.client import AzureOpenAIClient

logger = logging.getLogger(__name__)


class ServiceLoggingMixin:
    """Mixin providing standardized logging methods for services."""

    def log_init(self, service_name: str) -> None:
        """Log service initialization."""
        logger.info(f"Initializing {service_name}...")

    def log_azure_credentials(
        self, service: str, endpoint: str | None, key: str | None
    ) -> None:
        """Log Azure service credentials status."""
        logger.info(f"{service} Endpoint: {endpoint if endpoint else 'Not set'}")
        logger.info(f"{service} Key: {'Set' if key else 'Not set'}")

    def log_success(self, message: str) -> None:
        """Log a success message."""
        logger.info(message)

    def log_error(self, message: str, error: Exception | None = None) -> None:
        """Log an error message with optional exception."""
        if error:
            logger.error(f"{message}: {str(error)}")
        else:
            logger.error(message)


class AzureClientMixin:
    """Mixin providing Azure client initialization methods."""

    def initialize_openai_client(
        self,
        endpoint: str,
        api_key: str,
        api_version: str = "2024-12-01-preview",
        embedding_deployment: str = "embeddings",
        gpt_deployment: str = "gpt-deployment",
    ) -> tuple:
        """Initialize Azure OpenAI clients."""
        try:
            # Extract base endpoint if it includes deployment
            base_endpoint = (
                endpoint.split("/deployments/")[0]
                if "/deployments/" in endpoint
                else endpoint
            )

            # Initialize custom Azure OpenAI client
            azure_openai_client = AzureOpenAIClient(
                api_key=api_key,
                endpoint=base_endpoint,
                gpt_deployment=gpt_deployment,
                embeddings_deployment=embedding_deployment,
            )
            logger.info("Successfully initialized AzureOpenAIClient")

            # Initialize standard Azure OpenAI client
            openai_client = AzureOpenAI(
                azure_endpoint=base_endpoint, api_key=api_key, api_version=api_version
            )
            logger.info(
                f"Successfully initialized Azure OpenAI client with API version {api_version}"  # noqa: E501
            )

            return azure_openai_client, openai_client

        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI services: {str(e)}")
            raise

    def initialize_search_client(
        self, endpoint: str, api_key: str, index_name: str
    ) -> tuple:
        """Initialize Azure Search clients."""
        try:
            credential = AzureKeyCredential(api_key)

            # Initialize index client
            index_client = SearchIndexClient(endpoint=endpoint, credential=credential)

            # Initialize search client
            search_client = SearchClient(
                endpoint=endpoint, index_name=index_name, credential=credential
            )

            return index_client, search_client

        except Exception as e:
            logger.error(f"Failed to initialize Azure Search clients: {str(e)}")
            raise

    def initialize_document_intelligence_client(
        self, endpoint: str, api_key: str
    ) -> DocumentIntelligenceClient:
        """Initialize Azure Document Intelligence client."""
        try:
            credential = AzureKeyCredential(api_key)
            return DocumentIntelligenceClient(endpoint=endpoint, credential=credential)
        except Exception as e:
            logger.error(f"Failed to initialize Document Intelligence client: {str(e)}")
            raise


class AzureServiceConfig:
    """Configuration manager for Azure services."""

    def __init__(self, service_name: str):
        """Initialize configuration for an Azure service."""
        self.service_name = service_name
        self.endpoint = os.getenv(f"AZURE_{service_name}_ENDPOINT")
        self.key = os.getenv(f"AZURE_{service_name}_API_KEY")
        self.validate()

    def validate(self) -> None:
        """Validate required configuration is present."""
        if not self.endpoint or not self.key:
            error_msg = f"AZURE_{self.service_name}_ENDPOINT and AZURE_{self.service_name}_API_KEY must be configured"  # noqa: E501
            logger.error(error_msg)
            raise ValueError(error_msg)
