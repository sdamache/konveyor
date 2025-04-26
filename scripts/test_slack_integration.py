#!/usr/bin/env python
"""
Test script for Slack integration.

This script tests the Slack integration by sending a test message to a channel.
"""

import os
import sys
import django
import ssl
import certifi
from pathlib import Path

# Fix SSL certificate issues on macOS
ssl._create_default_https_context = ssl._create_unverified_context

# Add the project root to the Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'konveyor.settings.development')
django.setup()

from konveyor.apps.bot.services.slack_service import SlackService

def test_slack_service():
    """Test the Slack service by sending a test message."""
    # Create a Slack service instance
    slack = SlackService()

    # Check if the Slack token is set
    if not slack.token:
        print("Error: SLACK_BOT_TOKEN environment variable is not set.")
        return False

    # Get the user email from the environment or command line
    user_email = os.environ.get('SLACK_TEST_USER_EMAIL', '')

    if not user_email:
        print("No user email specified in SLACK_TEST_USER_EMAIL.")
        print("Checking for command-line argument...")

        # Check if a user email was provided as a command-line argument
        if len(sys.argv) > 1:
            user_email = sys.argv[1]
            print(f"Using user email from command-line argument: {user_email}")
        else:
            print("No user email provided. Will try to send a message to the bot's own DM.")
            print("This is useful for testing if the bot can receive and process messages.")

            # Get the bot's own user ID
            try:
                auth_test = slack.client.auth_test()
                if auth_test["ok"]:
                    bot_user_id = auth_test["user_id"]
                    print(f"Bot user ID: {bot_user_id}")

                    # Open a DM channel with the bot itself (this won't actually work for sending,
                    # but it's a good test of the API connection)
                    conversations_open = slack.client.conversations_open(users=[bot_user_id])
                    if conversations_open["ok"]:
                        channel_id = conversations_open["channel"]["id"]
                        print(f"Created DM channel with bot: {channel_id}")

                        # Send a test message
                        print(f"Sending test message to bot's DM channel: {channel_id}")
                        response = slack.send_message(
                            channel=channel_id,
                            text="Hello from Konveyor! This is a test message from the Slack integration."
                        )
                        return response is not None
            except Exception as e:
                print(f"Error testing bot connection: {str(e)}")
                return False

            return False

    # Look up the user by email
    print(f"Looking up user by email: {user_email}")
    try:
        user = slack.get_user_by_email(user_email)
        if not user:
            print(f"Could not find user with email: {user_email}")
            print("Please make sure the email address is correct and belongs to a user in your Slack workspace.")
            print("If you're using a placeholder email like 'your-email@example.com', replace it with a real email.")
            return False
    except Exception as e:
        print(f"Error looking up user by email: {str(e)}")
        print("Please make sure you have the 'users:read.email' scope enabled in your Slack app.")
        print("You may need to reinstall your app to the workspace after adding this scope.")
        return False

    user_id = user["id"]
    print(f"Found user: {user.get('name')} with ID: {user_id}")

    # Open a DM channel with the user
    try:
        print(f"Opening DM channel with user: {user_id}")
        conversations_open = slack.client.conversations_open(users=[user_id])
        if not conversations_open["ok"]:
            print(f"Failed to open DM channel: {conversations_open.get('error', 'Unknown error')}")
            return False

        channel_id = conversations_open["channel"]["id"]
        print(f"Created DM channel: {channel_id}")

        # Send a test message
        print(f"Sending test message to user's DM channel: {channel_id}")
        response = slack.send_message(
            channel=channel_id,
            text="Hello from Konveyor! This is a test message from the Slack integration."
        )
    except Exception as e:
        print(f"Error sending direct message: {str(e)}")
        return False

    # Check the response
    if response:
        print("Message sent successfully!")
        print(f"Response: {response}")
        return True
    else:
        print("Failed to send message.")
        return False

if __name__ == "__main__":
    print("Testing Slack integration...")
    success = test_slack_service()
    if success:
        print("Slack integration test passed!")
    else:
        print("Slack integration test failed.")
        sys.exit(1)
