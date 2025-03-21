import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from openai import AzureOpenAI
from azure.search.documents import SearchClient

class AzureConfig:
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.key_vault_url = os.getenv('AZURE_KEY_VAULT_URL')
        
    def get_openai_client(self):
        return AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version="2023-12-01-preview",
            azure_ad_token_provider=self.credential
        )
    
    def get_search_client(self):
        return SearchClient(
            endpoint=os.getenv("AZURE_COGNITIVE_SEARCH_ENDPOINT"),
            index_name="konveyor-index",
            credential=self.credential
        )
    
    def get_secret_client(self):
        return SecretClient(
            vault_url=self.key_vault_url,
            credential=self.credential
        )

# TODO: Add error handling and retries
# TODO: Add logging
# TODO: Add connection pooling
# TODO: Add caching layer for tokens
# TODO: Add rate limiting
