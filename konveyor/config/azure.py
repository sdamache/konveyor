import os
from typing import Optional
import logging
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

# Core Azure dependencies
try:
    from azure.identity import DefaultAzureCredential, AzureCliCredential
    from azure.core.credentials import AzureKeyCredential
    HAS_CORE = True
except ImportError:
    HAS_CORE = False
    logger.warning("Azure Core packages not installed. Run: pip install azure-identity azure-core")

# Document Intelligence
try:
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    HAS_DOC_INTELLIGENCE = True
except ImportError:
    HAS_DOC_INTELLIGENCE = False
    logger.warning("Azure Document Intelligence not installed. Run: pip install azure-ai-documentintelligence")

# Storage
try:
    from azure.storage.blob import BlobServiceClient
    HAS_STORAGE = True
except ImportError:
    HAS_STORAGE = False
    logger.warning("Azure Storage not installed. Run: pip install azure-storage-blob")

# Search
try:
    from azure.search.documents import SearchClient
    HAS_SEARCH = True
except ImportError:
    HAS_SEARCH = False
    logger.warning("Azure Search not installed. Run: pip install azure-search-documents")

# Key Vault
try:
    from azure.keyvault.secrets import SecretClient
    HAS_KEYVAULT = True
except ImportError:
    HAS_KEYVAULT = False
    SecretClient = None  # Add this line to define SecretClient for type hints
    logger.warning("Azure Key Vault not installed. Run: pip install azure-keyvault-secrets")

# OpenAI
try:
    from openai import AzureOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("Azure OpenAI not installed. Run: pip install openai")

class AzureConfig:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            if not HAS_CORE:
                raise ImproperlyConfigured("Azure Core packages are required but not installed.")
            try:
                # First try DefaultAzureCredential
                self.credential = DefaultAzureCredential()
            except Exception:
                try:
                    # Fallback to CLI credential
                    self.credential = AzureCliCredential()
                except Exception:
                    # Final fallback to key credential if environment variable is set
                    key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
                    if key:
                        self.credential = AzureKeyCredential(key)
                    else:
                        raise ImproperlyConfigured(
                            "No valid Azure credentials found. Please configure either "
                            "DefaultAzureCredential, AzureCliCredential, or set "
                            "AZURE_DOCUMENT_INTELLIGENCE_API_KEY environment variable."
                        )
            self.key_vault_url = os.getenv('AZURE_KEY_VAULT_URL')
            self.initialized = True

    def get_openai_client(self) -> AzureOpenAI:
        return AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview"),
            azure_ad_token_provider=self.credential
        )
    
    def get_search_client(self) -> Optional[SearchClient]:
        if not HAS_SEARCH:
            logger.warning("Azure Search package not installed. Install with: pip install azure-search-documents")
            return None
        try:
            return SearchClient(
                endpoint=os.getenv("AZURE_COGNITIVE_SEARCH_ENDPOINT"),
                index_name=os.getenv("AZURE_SEARCH_INDEX_NAME", "konveyor-documents"),
                credential=self.credential
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Search client: {str(e)}")
            return None
    
    def get_storage_client(self) -> Optional[BlobServiceClient]:
        if not HAS_STORAGE:
            logger.warning("Azure Storage package not installed. Install with: pip install azure-storage-blob")
            return None
        try:
            return BlobServiceClient(
                account_url=os.getenv("AZURE_STORAGE_ACCOUNT_URL"),
                credential=self.credential
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Storage client: {str(e)}")
            return None
    
    def get_secret_client(self) -> Optional['SecretClient']:  # Update type hint with quotes
        if not HAS_KEYVAULT:
            return None
        if not self.key_vault_url:
            return None
        try:
            return SecretClient(
                vault_url=self.key_vault_url,
                credential=self.credential
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Key Vault client: {str(e)}")
            return None

    @property
    def openai(self) -> AzureOpenAI:
        return self.get_openai_client()
    
    @property
    def search(self) -> Optional[SearchClient]:
        return self.get_search_client()
    
    @property
    def storage(self) -> Optional[BlobServiceClient]:
        return self.get_storage_client()

# TODO: Add error handling and retries
# TODO: Add logging
# TODO: Add connection pooling
# TODO: Add caching layer for tokens
# TODO: Add rate limiting
