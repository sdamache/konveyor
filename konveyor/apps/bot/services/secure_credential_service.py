from azure.keyvault.secrets import SecretClient
from azure.identity import ClientSecretCredential
import os
from dotenv import load_dotenv

class SecureCredentialService:
    """Service for securely managing bot credentials using Azure Key Vault"""
    
    def __init__(self):
        load_dotenv()
        
        # Initialize Azure credentials
        self.credential = ClientSecretCredential(
            tenant_id=os.getenv('AZURE_TENANT_ID'),
            client_id=os.getenv('AZURE_CLIENT_ID'),
            client_secret=os.getenv('AZURE_CLIENT_SECRET')
        )
        
        # Initialize Key Vault client
        self.key_vault_url = os.getenv('AZURE_KEY_VAULT_URL')
        self.secret_client = SecretClient(
            vault_url=self.key_vault_url,
            credential=self.credential
        )

    def store_bot_credentials(self):
        """Store bot credentials in Azure Key Vault"""
        try:
            # Store Slack credentials
            self._set_secret('slack-client-id', os.getenv('SLACK_CLIENT_ID'))
            self._set_secret('slack-client-secret', os.getenv('SLACK_CLIENT_SECRET'))
            self._set_secret('slack-signing-secret', os.getenv('SLACK_SIGNING_SECRET'))
            self._set_secret('slack-bot-token', os.getenv('SLACK_BOT_TOKEN'))
            
            print("✓ Successfully stored bot credentials in Key Vault")
            return True
        except Exception as e:
            print(f"⚠ Error storing bot credentials: {str(e)}")
            return False

    def get_bot_credentials(self):
        """Retrieve bot credentials from Azure Key Vault"""
        try:
            return {
                'SLACK_CLIENT_ID': self._get_secret('slack-client-id'),
                'SLACK_CLIENT_SECRET': self._get_secret('slack-client-secret'),
                'SLACK_SIGNING_SECRET': self._get_secret('slack-signing-secret'),
                'SLACK_BOT_TOKEN': self._get_secret('slack-bot-token')
            }
        except Exception as e:
            print(f"⚠ Error retrieving bot credentials: {str(e)}")
            return None

    def _set_secret(self, name, value):
        """Helper method to set a secret in Key Vault"""
        if not value:
            raise ValueError(f"Cannot store empty value for {name}")
        self.secret_client.set_secret(name, value)

    def _get_secret(self, name):
        """Helper method to get a secret from Key Vault"""
        secret = self.secret_client.get_secret(name)
        return secret.value