from dataclasses import dataclass
from typing import Dict, Any
import os

@dataclass
class BotSettings:
    name: str
    description: str
    max_response_length: int
    default_welcome_message: str
    error_message: str
    resource_group: str
    bot_name: str

class BotSettingsService:
    def __init__(self):
        self.settings = BotSettings(
            name="Konveyor Bot",
            description="AI assistant for documentation and code understanding",
            max_response_length=4000,
            default_welcome_message="Hello! I'm Konveyor Bot. I can help you find information in documentation and understand code.",
            error_message="I'm sorry, I encountered an error. Please try again or contact support.",
            resource_group="konveyor-rg",
            bot_name="konveyor-bot"
        )
    
    def get_settings(self) -> BotSettings:
        return self.settings
    
    def get_channel_config(self) -> Dict[str, Any]:
        """Get Azure Bot Service channel configuration"""
        return {
            "location": "global",
            "properties": {
                "channelName": "SlackChannel",
                "properties": {
                    "isEnabled": True,
                    "clientId": os.getenv('SLACK_CLIENT_ID'),
                    "clientSecret": os.getenv('SLACK_CLIENT_SECRET'),
                    "verificationToken": os.getenv('SLACK_SIGNING_SECRET')
                }
            }
        }