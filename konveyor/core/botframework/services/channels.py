from azure.mgmt.botservice import AzureBotService
from konveyor.core.azure_utils.service import AzureService


class SlackChannelService(AzureService):
    def __init__(self):
        super().__init__(
            service_name="SlackChannelService",
            required_config=[
                "AZURE_SUBSCRIPTION_ID",
                "AZURE_RESOURCE_GROUP",
                "AZURE_BOT_SERVICE_NAME",
                "SLACK_CLIENT_ID",
                "SLACK_CLIENT_SECRET",
                "SLACK_SIGNING_SECRET",
            ],
        )
        # Get credential and subscription ID from core utilities
        azure_credential = self.client_manager.get_credential()
        subscription_id = self.config.get_setting("AZURE_SUBSCRIPTION_ID")

        # Initialize the Bot Service client
        self.bot_client = AzureBotService(azure_credential, subscription_id)
        self.log_init("AzureBotService client initialized.")
        # Removed manual .env loading, credential checks, and client initialization

    def configure_channel(self):
        """Configure Slack channel in Azure Bot Service"""
        slack_channel = {
            "location": "global",
            "properties": {
                "channelName": "SlackChannel",
                "properties": {
                    "isEnabled": True,
                    "clientId": self.config.get_setting("SLACK_CLIENT_ID"),
                    "clientSecret": self.config.get_setting("SLACK_CLIENT_SECRET"),
                    "verificationToken": self.config.get_setting(
                        "SLACK_SIGNING_SECRET"
                    ),
                },
            },
        }

        try:
            response = self.bot_client.channels.create(
                resource_group_name=self.config.get_setting("AZURE_RESOURCE_GROUP"),
                resource_name=self.config.get_setting("AZURE_BOT_SERVICE_NAME"),
                channel_name="SlackChannel",
                parameters=slack_channel,
            )
            print("Successfully configured Slack channel")
            return response
        except Exception as e:
            print(f"Error configuring Slack channel: {str(e)}")
            raise

    def verify_channel(self):
        """Verify Slack channel configuration"""
        try:
            channel = self.bot_client.channels.get(
                resource_group_name=self.config.get_setting("AZURE_RESOURCE_GROUP"),
                resource_name=self.config.get_setting("AZURE_BOT_SERVICE_NAME"),
                channel_name="SlackChannel",
            )
            return channel.properties.get("isEnabled", False)
        except Exception:
            return False


if __name__ == "__main__":
    service = SlackChannelService()
    service.configure_channel()
