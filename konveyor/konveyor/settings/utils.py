import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

def get_secret(secret_name):
    """
    Get a secret from Azure Key Vault or environment variable.
    Falls back to environment variable if Key Vault is not configured.
    """
    key_vault_url = os.environ.get('AZURE_KEY_VAULT_URL')
    
    if key_vault_url:
        try:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=key_vault_url, credential=credential)
            return client.get_secret(secret_name).value
        except Exception as e:
            # Log the error but don't expose details
            print(f"Error accessing Key Vault: {type(e).__name__}")
    
    # Fall back to environment variable
    return os.environ.get(secret_name)
