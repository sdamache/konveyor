import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from azure.mgmt.botservice import AzureBotService

class SlackChannelService:
    def __init__(self):
        # Get the absolute path to the .env file
        env_path = "/Users/neeharikavemulapati/Documents/Projects/konveyor/.env"
        
        # Verify .env file exists
        if not os.path.exists(env_path):
            raise FileNotFoundError(f".env file not found at: {env_path}")
            
        # Load environment variables from root .env
        load_dotenv(dotenv_path=env_path)
        print(f"Loading .env from: {env_path}")
        
        # Get environment variables with detailed logging
        credentials = {
            'AZURE_TENANT_ID': os.getenv('AZURE_TENANT_ID'),
            'AZURE_CLIENT_ID': os.getenv('AZURE_CLIENT_ID'),
            'AZURE_CLIENT_SECRET': os.getenv('AZURE_CLIENT_SECRET')
        }
        
        # Check each credential individually and log status
        missing_credentials = []
        for key, value in credentials.items():
            if not value:
                missing_credentials.append(key)
                print(f"⚠ Missing {key}")
            else:
                # Show first 3 and last 3 characters of the value for verification
                masked_value = f"{value[:3]}...{value[-3:]}"
                print(f"✓ Found {key} = {masked_value}")
                
        if missing_credentials:
            error_msg = (
                f"Missing required Azure credentials: {', '.join(missing_credentials)}\n"
                f"Looking for .env file at: {env_path}\n"
                f"Working directory: {os.getcwd()}"
            )
            raise ValueError(error_msg)
            
        self.credential = ClientSecretCredential(
            tenant_id=credentials['AZURE_TENANT_ID'].strip(),
            client_id=credentials['AZURE_CLIENT_ID'].strip(),
            client_secret=credentials['AZURE_CLIENT_SECRET'].strip()
        )
        
        self.subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        if not self.subscription_id:
            raise ValueError("AZURE_SUBSCRIPTION_ID is missing from environment variables")
            
        print("✓ Successfully initialized Azure credentials")
        self.bot_client = AzureBotService(
            self.credential, 
            self.subscription_id
        )

    def configure_channel(self):
        """Configure Slack channel in Azure Bot Service"""
        slack_channel = {
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
        
        try:
            response = self.bot_client.channels.create(
                resource_group_name="konveyor-rg",
                resource_name="konveyor-bot",
                channel_name="SlackChannel",
                parameters=slack_channel
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
                resource_group_name="konveyor-rg",
                resource_name="konveyor-bot",
                channel_name="SlackChannel"
            )
            return channel.properties.get("isEnabled", False)
        except Exception:
            return False

if __name__ == "__main__":
    service = SlackChannelService()
    service.configure_channel()