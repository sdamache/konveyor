"""Base service class for Azure services.

This module provides a base class for all Azure services in the application.
It includes common functionality for configuration, client management, and logging.

Example:
    ```python
    class SearchService(AzureService):
        def __init__(self):
            super().__init__('SEARCH')
            self.index_client, self.search_client = self.client_manager.get_search_clients('my-index')
            
        def search(self, query: str):
            try:
                results = self.search_client.search(query)
                self.log_success(f"Found {len(results)} results")
                return results
            except Exception as e:
                self.log_error("Search failed", e)
                raise
    ```
"""

import logging
from typing import Optional, Any
from konveyor.core.azure_utils.config import AzureConfig
from konveyor.core.azure_utils.clients import AzureClientManager

logger = logging.getLogger(__name__)

class AzureService:
    """Base class for Azure services with logging and client management.
    
    This class provides common functionality for Azure services including:
    - Configuration management via AzureConfig
    - Client initialization via AzureClientManager
    - Standardized logging methods
    - Configuration validation
    
    All Azure services should inherit from this class to ensure consistent
    behavior and proper initialization.
    
    Attributes:
        service_name (str): Name of the service for logging and config
        config (AzureConfig): Azure configuration instance
        client_manager (AzureClientManager): Client manager instance
    """
    
    def __init__(self, service_name: str):
        """Initialize service with name and clients.
        
        Args:
            service_name (str): Service identifier (e.g., 'SEARCH', 'OPENAI')
            
        Raises:
            ImproperlyConfigured: If service configuration validation fails
        """
        self.service_name = service_name
        self.config = AzureConfig()
        self.client_manager = AzureClientManager(self.config)
        self._validate_config()
        
    def _validate_config(self) -> None:
        """Validate service configuration."""
        self.config.validate_required_config(self.service_name)
        
    def log_init(self, component: str) -> None:
        """Log initialization of a component.
        
        Args:
            component (str): Name of the component being initialized
            
        Example:
            ```python
            self.log_init("SearchService")
            ```
        """
        logger.info(f"Initializing {component}")
        
    def log_success(self, message: str) -> None:
        """Log a success message.
        
        Args:
            message (str): Success message to log
            
        Example:
            ```python
            self.log_success("Successfully processed document")
            ```
        """
        logger.info(f"{self.service_name}: {message}")

    def log_info(self, message: str) -> None:
        """
        Log an informational message for the service.

        This method provides a standardized way to log informational events and status updates
        for Azure services. All subclasses should use this method for non-error, non-warning
        messages that are relevant for debugging, configuration, or operational transparency.

        Args:
            message (str): Informational message to log
        
        Example:
            ```python
            self.log_info("Search index initialized successfully.")
            ```
        """
        logger.info(f"{self.service_name}: {message}")
        
    def log_error(self, message: str, error: Optional[Exception] = None, exc_info: Optional[Exception] = None) -> None:
        """
        Log an error message with optional exception and exc_info for stack trace.
        Args:
            message (str): Error message to log
            error (Optional[Exception]): Exception object if available
            exc_info (Optional[Exception]): Exception for stack trace (passed to logger)
        """
        if error:
            logger.error(f"{self.service_name}: {message} - {str(error)}", exc_info=exc_info)
        else:
            logger.error(f"{self.service_name}: {message}", exc_info=exc_info)

    def log_warning(self, message: str, exc_info: Optional[Exception] = None) -> None:
        """Log a warning message.
        
        Args:
            message (str): Warning message to log
            
        Example:
            ```python
            self.log_warning("Resource usage above 80%")
            ```
        """
        if exc_info:
            logger.warning(f"{self.service_name}: {message} - {str(exc_info)}", exc_info=exc_info)
        else:
            logger.warning(f"{self.service_name}: {message}")
        
    def log_debug(self, message: str, exc_info: Optional[Exception] = None) -> None:
        """Log a debug message.
        
        Args:
            message (str): Debug message to log
            
        Example:
            ```python
            self.log_debug("Processing item 1 of 10")
            ```
        """
        if exc_info:
            logger.debug(f"{self.service_name}: {message} - {str(exc_info)}", exc_info=exc_info)
        else:
            logger.debug(f"{self.service_name}: {message}")
        
    def log_azure_credentials(self, service: str, endpoint: str, key: str) -> None:
        """Log Azure credential information safely.
        
        Logs the endpoint and a masked version of the key for debugging purposes.
        
        Args:
            service (str): Service name (e.g., 'Search', 'OpenAI')
            endpoint (str): Service endpoint URL
            key (str): Service API key (will be masked in logs)
            
        Example:
            ```python
            self.log_azure_credentials('Search', endpoint, api_key)
            # Logs: Search credentials configured - Endpoint: https://..., Key: abcd...wxyz
            ```
        """
        if endpoint and key:
            key_preview = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "****"
            self.log_success(f"{service} credentials configured - Endpoint: {endpoint}, Key: {key_preview}")
        else:
            self.log_warning(f"{service} credentials missing")
