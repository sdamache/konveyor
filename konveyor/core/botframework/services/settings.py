from dataclasses import dataclass
from typing import Any

from konveyor.core.azure_utils.service import AzureService


@dataclass
class BotSettings:
    name: str
    description: str
    max_response_length: int
    default_welcome_message: str
    error_message: str
    resource_group: str
    bot_name: str


class BotSettingsService(AzureService):
    def __init__(self):
        super().__init__(
            service_name="BotSettingsService",
            required_config=[
                "SLACK_CLIENT_ID",
                "SLACK_CLIENT_SECRET",
                "SLACK_SIGNING_SECRET",
                "AZURE_RESOURCE_GROUP",  # Assuming this will be needed, based on other services  # noqa: E501
                "AZURE_BOT_SERVICE_NAME",  # Assuming this will be needed
            ],
        )
        self.settings = BotSettings(
            name="Konveyor Bot",
            description="AI assistant for documentation and code understanding",
            max_response_length=4000,
            default_welcome_message="Hello! I'm Konveyor Bot. I can help you find information in documentation and understand code.",  # noqa: E501
            error_message="I'm sorry, I encountered an error. Please try again or contact support.",  # noqa: E501
            resource_group=self.config.get_setting(
                "AZURE_RESOURCE_GROUP", default="konveyor-rg"
            ),  # Use config, provide default
            bot_name=self.config.get_setting(
                "AZURE_BOT_SERVICE_NAME", default="konveyor-bot"
            ),  # Use config, provide default
        )

    def get_settings(self) -> BotSettings:
        return self.settings

    def get_channel_config(self) -> dict[str, Any]:
        """Get Azure Bot Service channel configuration"""
        return {
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
