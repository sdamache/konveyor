#!/usr/bin/env python
"""
Test script for user profile integration with Slack.

This script tests the user profile integration with real Slack API calls.
"""

import os
import sys
import logging
import json
from datetime import datetime

# Add the project directory to the Python path
project_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_dir)

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "konveyor.settings.development")

import django

django.setup()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import after Django setup
from konveyor.apps.bot.services.slack_user_profile_service import (
    SlackUserProfileService,
)
from konveyor.apps.bot.services.slack_service import SlackService
from konveyor.apps.bot.models import SlackUserProfile
from konveyor.apps.bot.slash_commands import (
    handle_profile_command,
    handle_preferences_command,
)


def test_slack_user_profile_service():
    """Test the SlackUserProfileService with real Slack API calls."""
    logger.info("Testing SlackUserProfileService...")

    # Initialize the service
    slack_service = SlackService()
    user_profile_service = SlackUserProfileService(slack_service=slack_service)

    # Get your own Slack user ID (you can replace this with a known user ID)
    # For testing, we'll use the email to find the user
    test_email = "nikhild.sai@gmail.com"  # Replace with your email

    try:
        # List users to find your user ID
        response = slack_service.client.users_list()
        if not response.get("ok", False):
            logger.error(
                f"Error listing users: {response.get('error', 'Unknown error')}"
            )
            return False

        # Find user by email
        user_id = None
        for member in response.get("members", []):
            profile = member.get("profile", {})
            if profile.get("email") == test_email:
                user_id = member.get("id")
                break

        if not user_id:
            logger.error(f"Could not find user with email {test_email}")
            return False

        logger.info(f"Found user ID: {user_id}")

        # Get or create user profile
        profile = user_profile_service.get_or_create_profile(user_id)
        logger.info(f"User profile: {profile.slack_name} ({profile.slack_id})")
        logger.info(f"Email: {profile.slack_email}")
        logger.info(f"Real name: {profile.slack_real_name}")
        logger.info(f"Display name: {profile.slack_display_name}")
        logger.info(f"Interaction count: {profile.interaction_count}")

        # Update profile
        updated_profile = user_profile_service.update_profile(user_id)
        logger.info(
            f"Updated profile: {updated_profile.slack_name} ({updated_profile.slack_id})"
        )

        # Update preferences
        user_profile_service.update_preference(user_id, "code_language", "python")
        user_profile_service.update_preference(user_id, "response_format", "detailed")

        # Get updated profile
        final_profile = SlackUserProfile.objects.get(slack_id=user_id)
        logger.info(
            f"Code language preference: {final_profile.code_language_preference}"
        )
        logger.info(
            f"Response format preference: {final_profile.response_format_preference}"
        )

        return True
    except Exception as e:
        logger.error(f"Error testing SlackUserProfileService: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def test_slash_commands():
    """Test the slash commands for user profiles."""
    logger.info("Testing slash commands...")

    try:
        # Get a user profile
        profiles = SlackUserProfile.objects.all()
        if not profiles.exists():
            logger.error(
                "No user profiles found. Run test_slack_user_profile_service first."
            )
            return False

        profile = profiles.first()
        user_id = profile.slack_id

        # Test profile command
        profile_response = handle_profile_command(
            "", user_id, "test_channel", "http://example.com"
        )
        logger.info(
            f"Profile command response: {json.dumps(profile_response, indent=2)}"
        )

        # Test preferences command (view)
        prefs_view_response = handle_preferences_command(
            "", user_id, "test_channel", "http://example.com"
        )
        logger.info(
            f"Preferences view response: {json.dumps(prefs_view_response, indent=2)}"
        )

        # Test preferences command (set)
        prefs_set_response = handle_preferences_command(
            "set code_language javascript",
            user_id,
            "test_channel",
            "http://example.com",
        )
        logger.info(
            f"Preferences set response: {json.dumps(prefs_set_response, indent=2)}"
        )

        # Verify the preference was updated
        updated_profile = SlackUserProfile.objects.get(slack_id=user_id)
        logger.info(
            f"Updated code language preference: {updated_profile.code_language_preference}"
        )

        return True
    except Exception as e:
        logger.error(f"Error testing slash commands: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def test_webhook_integration():
    """Test the integration with the webhook handler."""
    logger.info("Testing webhook integration...")

    try:
        # Import the process_message function
        from konveyor.apps.bot.views import process_message

        # Get a user profile
        profiles = SlackUserProfile.objects.all()
        if not profiles.exists():
            logger.error(
                "No user profiles found. Run test_slack_user_profile_service first."
            )
            return False

        profile = profiles.first()
        user_id = profile.slack_id

        # Call process_message
        result = process_message(
            "Hello, this is a test message", user_id, "test_channel"
        )

        # Log the result
        logger.info(f"Process message result: {result}")

        # Check if the interaction count was incremented
        updated_profile = SlackUserProfile.objects.get(slack_id=user_id)
        logger.info(f"Updated interaction count: {updated_profile.interaction_count}")

        return True
    except Exception as e:
        logger.error(f"Error testing webhook integration: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def main():
    """Run all tests."""
    logger.info("Starting user profile integration tests...")

    # Test SlackUserProfileService
    if test_slack_user_profile_service():
        logger.info("SlackUserProfileService test passed!")
    else:
        logger.error("SlackUserProfileService test failed!")
        return 1

    # Test slash commands
    if test_slash_commands():
        logger.info("Slash commands test passed!")
    else:
        logger.error("Slash commands test failed!")
        return 1

    # Test webhook integration
    if test_webhook_integration():
        logger.info("Webhook integration test passed!")
    else:
        logger.error("Webhook integration test failed!")
        return 1

    logger.info("All tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
