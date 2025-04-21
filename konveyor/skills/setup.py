"""
Setup for Semantic Kernel framework.

Initializes the Semantic Kernel SDK and configures Azure OpenAI integration.
"""

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from konveyor.core.azure_utils.config import AzureConfig
from konveyor.core.azure_utils.clients import AzureClientManager
from semantic_kernel.memory import VolatileMemoryStore


def create_kernel() -> Kernel:
    """
    Create and configure the Semantic Kernel with Azure OpenAI chat and memory services.
    All configuration and secret logic is handled via konveyor/core utilities.
    Returns:
        Kernel: Configured Semantic Kernel instance.
    """
    config = AzureConfig()
    config.validate_required_config('OPENAI')

    endpoint = config.get_endpoint('OPENAI')
    key_or_secret_name = config.get_key('OPENAI')
    # Attempt to fetch API key from Key Vault; fallback to environment value if unavailable
    try:
        kv_client = AzureClientManager(config).get_key_vault_client()
        secret = kv_client.get_secret(key_or_secret_name)
        api_key = secret.value
    except Exception:
        api_key = key_or_secret_name
    deployment = config.get_setting('AZURE_OPENAI_CHAT_DEPLOYMENT') or 'gpt-35-turbo'
    api_version = config.get_setting('AZURE_OPENAI_API_VERSION') or '2024-12-01-preview'

    # Construct AzureChatCompletion with all required arguments
    chat_service = AzureChatCompletion(
        endpoint=endpoint,
        api_key=api_key,
        deployment_name=deployment,
        api_version=api_version,
        service_id='chat'
    )

    kernel = Kernel()
    kernel.add_service(chat_service)

    # Register volatile memory store
    volatile_memory = VolatileMemoryStore()
    volatile_memory.service_id = 'volatile'
    kernel.add_service(volatile_memory)
    return kernel
