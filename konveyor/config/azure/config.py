"""Azure configuration management.

This module provides a centralized configuration management system for Azure services.
It handles credential initialization, environment variable loading, and configuration validation.

Required Environment Variables:
    None - All environment variables are optional and services will validate their required variables

Optional Environment Variables:
    AZURE_KEY_VAULT_URL: URL for Azure Key Vault
    AZURE_SEARCH_ENDPOINT: Azure Cognitive Search endpoint
    AZURE_SEARCH_API_KEY: Azure Cognitive Search API key
    AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint
    AZURE_OPENAI_API_KEY: Azure OpenAI API key
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: Azure Document Intelligence endpoint
    AZURE_DOCUMENT_INTELLIGENCE_API_KEY: Azure Document Intelligence API key
    AZURE_STORAGE_ACCOUNT_URL: Azure Storage account URL
    AZURE_STORAGE_ACCOUNT_NAME: Azure Storage account name
    AZURE_STORAGE_ACCOUNT_KEY: Azure Storage account key
    AZURE_STORAGE_CONNECTION_STRING: Azure Storage connection string

Example:
    ```python
    # Get configuration
    config = AzureConfig()
    
    # Get service endpoint
    search_endpoint = config.get_endpoint('SEARCH')
    
    # Validate configuration
    config.validate_required_config('SEARCH')
    ```
"""

import os
import logging
from typing import Optional, Dict, Any
from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.core.credentials import AzureKeyCredential, TokenCredential
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

class AzureConfig:
    """Unified Azure configuration management.
    
    This class implements the Singleton pattern to ensure only one configuration instance exists.
    It handles loading configuration from environment variables and provides methods to access
    service-specific configuration.
    
    The class will attempt to initialize Azure credentials in the following order:
    1. DefaultAzureCredential
    2. AzureCliCredential
    3. Key-based authentication
    
    Attributes:
        credential (TokenCredential): Azure credential for authentication
        key_vault_url (str): URL for Azure Key Vault
        endpoints (dict): Dictionary of service endpoints
        keys (dict): Dictionary of service API keys
        storage_account_name (str): Azure Storage account name
        storage_account_key (str): Azure Storage account key
        storage_connection_string (str): Azure Storage connection string
    """
    
    _instance = None  # Singleton instance
    
    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self):
        """Initialize configuration if not already done."""
        if not hasattr(self, 'initialized'):
            self._initialize_credentials()
            self._load_configuration()
            self.initialized = True
            
    def _initialize_credentials(self):
        """Initialize Azure credentials."""
        try:
            # First try DefaultAzureCredential
            self.credential = DefaultAzureCredential()
        except Exception:
            try:
                # Fallback to CLI credential
                self.credential = AzureCliCredential()
            except Exception:
                # Final fallback to key-based auth
                self.credential = None
                logger.warning("Failed to initialize Azure credentials, falling back to key-based auth")
                
    def _load_configuration(self):
        """Load configuration from environment."""
        # Core configuration
        self.key_vault_url = os.getenv('AZURE_KEY_VAULT_URL')
        
        # Service endpoints
        self.endpoints = {
            'SEARCH': os.getenv('AZURE_SEARCH_ENDPOINT'),
            'OPENAI': os.getenv('AZURE_OPENAI_ENDPOINT'),
            'DOCUMENT_INTELLIGENCE': os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'),
            'STORAGE': os.getenv('AZURE_STORAGE_ACCOUNT_URL')
        }
        
        # Service keys
        self.keys = {
            'SEARCH': os.getenv('AZURE_SEARCH_API_KEY'),
            'OPENAI': os.getenv('AZURE_OPENAI_API_KEY'),
            'DOCUMENT_INTELLIGENCE': os.getenv('AZURE_DOCUMENT_INTELLIGENCE_API_KEY')
        }
        
        # Storage specific config
        self.storage_account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
        self.storage_account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
        self.storage_connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        
    def get_credential(self) -> Optional[TokenCredential]:
        """Get Azure credential for token-based authentication.
        
        Returns:
            Optional[TokenCredential]: Azure credential if available, None if using key-based auth
        """
        return self.credential
        
    def get_endpoint(self, service: str) -> Optional[str]:
        """Get endpoint URL for a specific Azure service.
        
        Args:
            service (str): Service identifier (SEARCH, OPENAI, DOCUMENT_INTELLIGENCE, STORAGE)
            
        Returns:
            Optional[str]: Service endpoint URL if configured, None otherwise
        """
        return self.endpoints.get(service)
        
    def get_key(self, service: str) -> Optional[str]:
        """Get API key for a specific Azure service.
        
        Args:
            service (str): Service identifier (SEARCH, OPENAI, DOCUMENT_INTELLIGENCE)
            
        Returns:
            Optional[str]: Service API key if configured, None otherwise
        """
        return self.keys.get(service)
        
    def get_key_vault_url(self) -> Optional[str]:
        """Get Azure Key Vault URL.
        
        Returns:
            Optional[str]: Key Vault URL if configured, None otherwise
            
        Environment Variables:
            AZURE_KEY_VAULT_URL: Key Vault URL
        """
        return self.key_vault_url
        
    def get_storage_connection_string(self) -> Optional[str]:
        """Get Azure Storage connection string.
        
        This method will first check for a complete connection string in environment variables.
        If not found, it will attempt to build one using the account name and key.
        
        Returns:
            Optional[str]: Storage connection string if available configuration exists,
            None otherwise

        Environment Variables:
            AZURE_STORAGE_CONNECTION_STRING: Complete connection string
            AZURE_STORAGE_ACCOUNT_NAME: Storage account name (used with key)
            AZURE_STORAGE_ACCOUNT_KEY: Storage account key (used with name)
        """
        if self.storage_connection_string:
            return self.storage_connection_string
            
        # Build connection string if we have account name and key
        if self.storage_account_name and self.storage_account_key:
            return (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={self.storage_account_name};"
                f"AccountKey={self.storage_account_key};"
                "EndpointSuffix=core.windows.net"
            )
            
        return None
        
    def validate_required_config(self, service: str) -> None:
        """Validate that all required configuration exists for a service.
        
        Args:
            service (str): Service identifier to validate (SEARCH, OPENAI, 
                          DOCUMENT_INTELLIGENCE, STORAGE)
                          
        Raises:
            ImproperlyConfigured: If any required configuration is missing
            
        Required Configuration by Service:
            SEARCH: AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY
            OPENAI: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY
            DOCUMENT_INTELLIGENCE: AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
                                  AZURE_DOCUMENT_INTELLIGENCE_API_KEY
            STORAGE: Either AZURE_STORAGE_CONNECTION_STRING or
                     both AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY
        """
        if service == 'SEARCH':
            if not all([self.get_endpoint('SEARCH'), self.get_key('SEARCH')]):
                raise ImproperlyConfigured("Missing required Azure Search configuration")
        elif service == 'OPENAI':
            if not all([self.get_endpoint('OPENAI'), self.get_key('OPENAI')]):
                raise ImproperlyConfigured("Missing required Azure OpenAI configuration")
        elif service == 'DOCUMENT_INTELLIGENCE':
            if not all([self.get_endpoint('DOCUMENT_INTELLIGENCE'), 
                       self.get_key('DOCUMENT_INTELLIGENCE')]):
                raise ImproperlyConfigured("Missing required Azure Document Intelligence configuration")
        elif service == 'STORAGE':
            if not self.get_storage_connection_string():
                raise ImproperlyConfigured("Missing required Azure Storage configuration")
