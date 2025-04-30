from konveyor.core.azure_utils.service import AzureService


class SecureCredentialService(AzureService):
    """Service for securely managing bot credentials using Azure Key Vault"""

    def __init__(self):
        super().__init__(
            service_name="SecureCredentialService",
            required_config=[
                "AZURE_KEY_VAULT_URL",
                "SLACK_CLIENT_ID",
                "SLACK_CLIENT_SECRET",
                "SLACK_SIGNING_SECRET",
                "SLACK_BOT_TOKEN",
            ],
        )
        # Get the secret client from the centralized manager
        self.secret_client = self.client_manager.get_secret_client()
        # Removed manual load_dotenv, credential, and client initialization

    def store_bot_credentials(self):
        """Store bot credentials in Azure Key Vault"""
        try:
            # Store Slack credentials
            # Fetch credentials from central config to store them
            self._set_secret(
                "slack-client-id", self.config.get_setting("SLACK_CLIENT_ID")
            )
            self._set_secret(
                "slack-client-secret", self.config.get_setting("SLACK_CLIENT_SECRET")
            )
            self._set_secret(
                "slack-signing-secret", self.config.get_setting("SLACK_SIGNING_SECRET")
            )
            self._set_secret(
                "slack-bot-token", self.config.get_setting("SLACK_BOT_TOKEN")
            )

            print("✓ Successfully stored bot credentials in Key Vault")
            return True
        except Exception as e:
            print(f"⚠ Error storing bot credentials: {str(e)}")
            return False

    def get_bot_credentials(self):
        """Retrieve bot credentials from Azure Key Vault"""
        try:
            return {
                "SLACK_CLIENT_ID": self._get_secret("slack-client-id"),
                "SLACK_CLIENT_SECRET": self._get_secret("slack-client-secret"),
                "SLACK_SIGNING_SECRET": self._get_secret("slack-signing-secret"),
                "SLACK_BOT_TOKEN": self._get_secret("slack-bot-token"),
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
