import os


def get_secret(secret_name, default=None):
    """
    Get a secret from environment variables.
    This is a placeholder for future Azure Key Vault integration.

    Args:
        secret_name: The name of the secret
        default: Default value if the secret is not found

    Returns:
        The secret value or default
    """
    return os.environ.get(secret_name, default)


# TODO: Add Azure Key Vault integration when needed
# Example implementation for future reference:
"""
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

def get_secret_from_key_vault(secret_name, default=None):
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
    return os.environ.get(secret_name, default)
"""
