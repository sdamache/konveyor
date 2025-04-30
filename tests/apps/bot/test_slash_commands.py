"""
Tests for Slack slash commands.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from django.http import JsonResponse
from django.test import RequestFactory
from django.utils import timezone

from konveyor.apps.bot.slash_commands import (get_all_commands,
                                              get_command_handler,
                                              handle_code_command,
                                              handle_help_command,
                                              handle_info_command,
                                              handle_preferences_command,
                                              handle_profile_command,
                                              handle_status_command,
                                              register_command)
from konveyor.apps.bot.views import slack_slash_command


def test_register_and_get_command():
    """Test registering and retrieving commands."""

    # Mock handler function
    def mock_handler(text, user_id, channel_id, response_url):
        return {"text": "Mock response"}

    # Register a test command
    register_command("test", mock_handler, "Test command")

    # Get the command handler
    command_info = get_command_handler("test")

    # Verify the command was registered correctly
    assert command_info is not None
    assert command_info["handler"] == mock_handler
    assert command_info["description"] == "Test command"

    # Get all commands
    commands = get_all_commands()

    # Verify the test command is in the list
    test_command = next((cmd for cmd in commands if cmd["name"] == "test"), None)
    assert test_command is not None
    assert test_command["description"] == "Test command"


def test_help_command():
    """Test the help command handler."""
    response = handle_help_command(
        "", "test_user", "test_channel", "http://example.com"
    )

    # Verify the response structure
    assert "response_type" in response
    assert response["response_type"] == "ephemeral"
    assert "text" in response
    assert "blocks" in response

    # Verify the blocks contain command information
    blocks = response["blocks"]
    assert len(blocks) > 2  # Header, intro, and at least one command

    # Verify the header
    assert blocks[0]["type"] == "header"
    assert "Available Commands" in blocks[0]["text"]["text"]


def test_status_command():
    """Test the status command handler."""
    response = handle_status_command(
        "", "test_user", "test_channel", "http://example.com"
    )

    # Verify the response structure
    assert "response_type" in response
    assert response["response_type"] == "ephemeral"
    assert "text" in response
    assert "blocks" in response

    # Verify the blocks contain status information
    blocks = response["blocks"]
    assert len(blocks) >= 4  # Header and at least 3 status items

    # Verify the header
    assert blocks[0]["type"] == "header"
    assert "System Status" in blocks[0]["text"]["text"]

    # Verify status items
    status_text = blocks[1]["text"]["text"]
    assert "Bot Service" in status_text


def test_info_command():
    """Test the info command handler."""
    response = handle_info_command(
        "", "test_user", "test_channel", "http://example.com"
    )

    # Verify the response structure
    assert "response_type" in response
    assert response["response_type"] == "ephemeral"
    assert "text" in response
    assert "blocks" in response

    # Verify the blocks contain info
    blocks = response["blocks"]
    assert len(blocks) >= 3  # Header and at least 2 info sections

    # Verify the header
    assert blocks[0]["type"] == "header"
    assert "About Konveyor" in blocks[0]["text"]["text"]


def test_code_command():
    """Test the code command handler."""
    response = handle_code_command(
        "", "test_user", "test_channel", "http://example.com"
    )

    # Verify the response structure
    assert "response_type" in response
    assert response["response_type"] == "ephemeral"
    assert "text" in response
    assert "blocks" in response

    # Verify the blocks contain code examples
    blocks = response["blocks"]
    assert len(blocks) >= 4  # Header and at least 3 code examples

    # Verify the header
    assert blocks[0]["type"] == "header"
    assert "Code Formatting" in blocks[0]["text"]["text"]

    # Check blocks structure

    # Verify we have section blocks with code examples
    section_blocks = [block for block in blocks if block["type"] == "section"]
    assert len(section_blocks) >= 4  # Header, intro, and at least 2 code examples

    # Verify we have at least one context block with language information
    context_blocks = [block for block in blocks if block["type"] == "context"]
    assert len(context_blocks) >= 1


@pytest.mark.django_db
def test_preferences_command():
    """Test the preferences command handler."""
    # Mock the SlackUserProfileService
    with patch(
        "konveyor.apps.bot.slash_commands.slack_user_profile_service"
    ) as mock_service:
        # Create a mock profile
        mock_profile = MagicMock()
        mock_profile.code_language_preference = "python"
        mock_profile.response_format_preference = "concise"
        mock_service.get_or_create_profile.return_value = mock_profile

        # Test with no arguments (show current preferences)
        response = handle_preferences_command(
            "", "test_user", "test_channel", "http://example.com"
        )

        # Verify the response structure
        assert "response_type" in response
        assert response["response_type"] == "ephemeral"
        assert "text" in response
        assert "blocks" in response

        # Verify the blocks contain preferences
        blocks = response["blocks"]
        assert len(blocks) >= 3  # Header, intro, and preferences

        # Verify the header
        assert blocks[0]["type"] == "header"
        assert "Your Preferences" in blocks[0]["text"]["text"]

        # Test setting a preference
        mock_service.update_preference.return_value = mock_profile
        response = handle_preferences_command(
            "set code_language javascript",
            "test_user",
            "test_channel",
            "http://example.com",
        )

        # Verify the response
        assert "response_type" in response
        assert response["response_type"] == "ephemeral"
        assert "text" in response
        assert "code_language" in response["text"]
        assert "javascript" in response["text"]

        # Verify the service was called correctly
        mock_service.update_preference.assert_called_once_with(
            "test_user", "code_language", "javascript"
        )


@pytest.mark.django_db
def test_profile_command():
    """Test the profile command handler."""
    # Mock the SlackUserProfileService
    with patch(
        "konveyor.apps.bot.slash_commands.slack_user_profile_service"
    ) as mock_service:
        # Create a mock profile
        mock_profile = MagicMock()
        mock_profile.slack_id = "test_user"
        mock_profile.slack_name = "Test User"
        mock_profile.slack_real_name = "Test Real Name"
        mock_profile.slack_display_name = "Test Display Name"
        mock_profile.slack_email = "test@example.com"
        mock_profile.interaction_count = 42
        mock_profile.last_interaction = timezone.now()
        mock_service.get_or_create_profile.return_value = mock_profile

        # Test the profile command
        response = handle_profile_command(
            "", "test_user", "test_channel", "http://example.com"
        )

        # Verify the response structure
        assert "response_type" in response
        assert response["response_type"] == "ephemeral"
        assert "text" in response
        assert "blocks" in response

        # Verify the blocks contain profile information
        blocks = response["blocks"]
        assert len(blocks) >= 4  # Header and at least 3 sections

        # Verify the header
        assert blocks[0]["type"] == "header"
        assert "Your Profile" in blocks[0]["text"]["text"]

        # Verify the service was called correctly
        mock_service.get_or_create_profile.assert_called_once_with("test_user")


@pytest.mark.django_db
def test_slash_command_endpoint():
    """Test the slash command endpoint."""
    # Create a request factory
    factory = RequestFactory()

    # Mock the SlackService
    with patch("konveyor.apps.bot.views.slack_service") as mock_slack_service, patch(
        "konveyor.apps.bot.views.get_command_handler"
    ) as mock_get_command_handler:

        # Set up the mocks
        mock_slack_service.verify_request.return_value = True

        # Mock a command handler
        mock_handler = MagicMock(
            return_value={"response_type": "ephemeral", "text": "Test response"}
        )

        # Set up the command handler mock
        mock_get_command_handler.return_value = {
            "handler": mock_handler,
            "description": "Test command",
        }

        # Create a POST request with form data
        post_data = {
            "command": "/test",
            "text": "test argument",
            "user_id": "test_user",
            "channel_id": "test_channel",
            "response_url": "http://example.com",
        }
        post_request = factory.post(
            "/api/bot/slack/commands/",
            data=post_data,
            content_type="application/x-www-form-urlencoded",
        )

        # Mock the request.POST dictionary
        post_request.POST = post_data

        # Call the slash command endpoint
        response = slack_slash_command(post_request)

        # Verify the response
        assert response is not None
        assert isinstance(response, JsonResponse)

        # Verify the command handler was called with the correct arguments
        mock_handler.assert_called_once_with(
            "test argument", "test_user", "test_channel", "http://example.com"
        )


@pytest.mark.django_db
def test_slash_command_unknown_command():
    """Test the slash command endpoint with an unknown command."""
    # Create a request factory
    factory = RequestFactory()

    # Mock the SlackService
    with patch("konveyor.apps.bot.views.slack_service") as mock_slack_service, patch(
        "konveyor.apps.bot.views.get_command_handler"
    ) as mock_get_command_handler:

        # Set up the mocks
        mock_slack_service.verify_request.return_value = True

        # Set up the command handler mock to return None (unknown command)
        mock_get_command_handler.return_value = None

        # Create a POST request with form data
        post_data = {
            "command": "/unknown",
            "text": "",
            "user_id": "test_user",
            "channel_id": "test_channel",
            "response_url": "http://example.com",
        }
        post_request = factory.post(
            "/api/bot/slack/commands/",
            data=post_data,
            content_type="application/x-www-form-urlencoded",
        )

        # Mock the request.POST dictionary
        post_request.POST = post_data

        # Call the slash command endpoint
        response = slack_slash_command(post_request)

        # Verify the response
        assert response is not None
        assert isinstance(response, JsonResponse)

        # Parse the response JSON
        response_data = json.loads(response.content)

        # Verify the response contains an error message
        assert "response_type" in response_data
        assert response_data["response_type"] == "ephemeral"
        assert "text" in response_data
        assert "Sorry, I don't know the command" in response_data["text"]
        assert "/help" in response_data["text"]
