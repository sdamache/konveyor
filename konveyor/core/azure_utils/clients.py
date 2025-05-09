"""Azure client initialization and management.

This module provides a centralized manager for initializing and configuring Azure service clients.  # noqa: E501
It handles client creation, configuration, and error handling for all Azure services used in the application.  # noqa: E501

The following clients are supported:
- Azure Cognitive Search
- Azure OpenAI
- Azure Document Intelligence
- Azure Blob Storage
- Azure Key Vault

Example:
    ```python
    # Initialize client manager
    manager = AzureClientManager()

    # Get search clients
    index_client, search_client = manager.get_search_clients('my-index')

    # Get OpenAI client
    openai_client = manager.get_openai_client()
    ```
"""

import logging
import os  # noqa: F401
from typing import Any, Optional, Tuple  # noqa: F401

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential, TokenCredential  # noqa: F401
from azure.identity import (  # noqa: E501, F401
    AzureCliCredential,
    DefaultAzureCredential,
)
from azure.keyvault.secrets import SecretClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.storage.blob import BlobServiceClient
from openai import AzureOpenAI

from konveyor.core.azure_utils.config import AzureConfig
from konveyor.core.azure_utils.retry import azure_retry
from konveyor.core.conversation.storage import AzureStorageManager

logger = logging.getLogger(__name__)


class AzureClientManager:
    """Manages Azure client initialization and configuration.

    This class provides methods to initialize and configure various Azure service clients.  # noqa: E501
    It uses AzureConfig for configuration management and applies retry logic to client operations.  # noqa: E501

    Each get_* method initializes a specific Azure service client with proper configuration  # noqa: E501
    and error handling. All methods use the azure_retry decorator for resilience.

    Attributes:
        config (AzureConfig): Configuration instance for Azure services
    """

    def __init__(self, config: AzureConfig | None = None):
        """Initialize with optional config."""
        self.config = config or AzureConfig()

    @azure_retry()
    def get_search_clients(
        self, index_name: str
    ) -> tuple[SearchIndexClient, SearchClient]:
        """Initialize and return Azure Cognitive Search clients.

        Creates both an index client for managing search indexes and a search client
        for performing searches on a specific index.

        Args:
            index_name (str): Name of the search index to connect to

        Returns:
            Tuple[SearchIndexClient, SearchClient]: A tuple containing:
                - SearchIndexClient for managing indexes
                - SearchClient for performing searches

        Raises:
            ValueError: If required configuration is missing
            Exception: If client initialization fails

        Required Environment Variables:
            AZURE_SEARCH_ENDPOINT: Search service endpoint
            AZURE_SEARCH_API_KEY: Search service API key
        """
        config = self.config
        try:
            # Initialize search clients
            search_endpoint = config.get_endpoint("SEARCH")
            search_key = config.get_key("SEARCH")

            if not all([search_endpoint, search_key, index_name]):
                raise ValueError("Missing required search configuration")

            # Create search credential
            search_credential = AzureKeyCredential(search_key)

            # Initialize clients
            index_client = SearchIndexClient(
                endpoint=search_endpoint, credential=search_credential
            )

            search_client = SearchClient(
                endpoint=search_endpoint,
                credential=search_credential,
                index_name=index_name,
            )

            return index_client, search_client

        except Exception as e:
            logger.error(f"Failed to initialize search clients: {str(e)}")
            raise

    @azure_retry()
    def get_openai_client(self) -> AzureOpenAI:
        """Initialize and return Azure OpenAI client.

        Creates an OpenAI client configured for Azure OpenAI Services.

        Returns:
            AzureOpenAI: Configured OpenAI client

        Raises:
            ValueError: If required configuration is missing
            Exception: If client initialization fails

        Required Environment Variables:
            AZURE_OPENAI_ENDPOINT: OpenAI service endpoint
            AZURE_OPENAI_API_KEY: OpenAI service API key

        Optional Environment Variables:
            AZURE_OPENAI_API_VERSION: API version (default: 2024-12-01-preview)
        """
        config = self.config
        try:
            endpoint = config.get_endpoint("OPENAI")
            api_key = config.get_key("OPENAI")
            api_version = config.get_setting("AZURE_OPENAI_API_VERSION")

            if not all([endpoint, api_key]):
                raise ValueError("Missing required OpenAI configuration")

            # Create client without deployment (will be specified per operation)
            client = AzureOpenAI(
                azure_endpoint=endpoint, api_key=api_key, api_version=api_version
            )

            return client

        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise

    @azure_retry()
    def get_document_intelligence_client(self) -> DocumentIntelligenceClient:
        """Initialize and return Azure Document Intelligence client.

        Creates a client for processing documents using Azure Document Intelligence.

        Returns:
            DocumentIntelligenceClient: Configured Document Intelligence client

        Raises:
            ValueError: If required configuration is missing
            Exception: If client initialization fails

        Required Environment Variables:
            AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: Document Intelligence endpoint
            AZURE_DOCUMENT_INTELLIGENCE_API_KEY: Document Intelligence API key
        """
        config = self.config
        try:
            endpoint = config.get_endpoint("DOCUMENT_INTELLIGENCE")
            key = config.get_key("DOCUMENT_INTELLIGENCE")

            if not all([endpoint, key]):
                raise ValueError("Missing required Document Intelligence configuration")

            credential = AzureKeyCredential(key)
            client = DocumentIntelligenceClient(endpoint, credential)

            return client

        except Exception as e:
            logger.error(f"Failed to initialize Document Intelligence client: {str(e)}")
            raise

    @azure_retry()
    def get_blob_client(self) -> BlobServiceClient:
        """Initialize and return Azure Blob Storage client.

        Creates a client for interacting with Azure Blob Storage.

        Returns:
            BlobServiceClient: Configured Blob Storage client

        Raises:
            ValueError: If required configuration is missing
            Exception: If client initialization fails

        Required Environment Variables:
            One of the following combinations:
            1. AZURE_STORAGE_CONNECTION_STRING
            2. Both AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY
        """
        config = self.config
        try:
            conn_str = config.get_storage_connection_string()

            if not conn_str:
                raise ValueError("Missing required storage configuration")

            client = BlobServiceClient.from_connection_string(conn_str)

            return client

        except Exception as e:
            logger.error(f"Failed to initialize Blob Storage client: {str(e)}")
            raise

    @azure_retry()
    def get_key_vault_client(self) -> SecretClient:
        """Initialize and return Azure Key Vault client.

        Creates a client for accessing secrets in Azure Key Vault.
        Uses token-based authentication via DefaultAzureCredential.

        Returns:
            SecretClient: Configured Key Vault client

        Raises:
            ValueError: If required configuration is missing
            Exception: If client initialization fails

        Required Environment Variables:
            AZURE_KEY_VAULT_URL: Key Vault URL

        Note:
            This client requires proper Azure AD authentication.
            It will attempt to use DefaultAzureCredential for authentication.
        """
        config = self.config
        vault_url = config.get_key_vault_url()
        credential = config.get_credential()
        if not all([vault_url, credential]):
            raise ValueError("Missing required Key Vault configuration")
        try:
            return SecretClient(vault_url=vault_url, credential=credential)
        except Exception as e:
            logger.error(f"Failed to initialize Key Vault client: {e}")
            raise

    @azure_retry()
    def get_storage_manager(self) -> "AzureStorageManager":
        """Initialize and return Azure Storage Manager.

        Creates a manager for handling both Cosmos DB and Redis storage.

        Returns:
            AzureStorageManager: Configured storage manager

        Raises:
            ValueError: If required configuration is missing
            Exception: If client initialization fails

        Required Environment Variables:
            AZURE_COSMOS_CONNECTION_STRING: Cosmos DB connection string
            AZURE_REDIS_CONNECTION_STRING: Redis connection string
        """
        config = self.config
        try:
            cosmos_conn_str = config.get_cosmos_connection_string()
            redis_conn_str = config.get_redis_connection_string()

            if not all([cosmos_conn_str, redis_conn_str]):
                raise ValueError("Missing required storage configuration")

            manager = AzureStorageManager(
                cosmos_connection_str=cosmos_conn_str,
                redis_connection_str=redis_conn_str,
            )

            return manager

        except Exception as e:
            logger.error(f"Failed to initialize Storage Manager: {str(e)}")
            raise
