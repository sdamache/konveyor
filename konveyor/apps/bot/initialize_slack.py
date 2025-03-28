from services.slack_channel_service import SlackChannelService
import os
from dotenv import load_dotenv

def check_env_file():
    """Check if .env file exists and is readable"""
    env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
    if os.path.exists(env_path):
        print(f"✓ Found .env file at: {env_path}")
        with open(env_path, 'r') as f:
            content = f.read()
            if 'AZURE_TENANT_ID' in content:
                print("✓ .env file contains Azure credentials")
            else:
                print("⚠ .env file does not contain Azure credentials")
    else:
        print(f"⚠ No .env file found at: {env_path}")

def main():
    print("Starting Slack channel configuration...")
    check_env_file()
    try:
        service = SlackChannelService()
        service.configure_channel()
    except ValueError as e:
        print(f"Configuration failed: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()