"""
Slash command handlers for the Slack bot.

This module contains handlers for Slack slash commands.
"""

# Removed: import json
import logging
from typing import Any, Callable, Dict, List, Optional

from django.conf import settings

from konveyor.apps.bot.services.slack_user_profile_service import (
    SlackUserProfileService,
)

# Configure logging
logger = logging.getLogger(__name__)

# Command registry
command_registry = {}


def register_command(command_name: str, handler: Callable, description: str):
    """
    Register a slash command handler.

    Args:
        command_name: The name of the command (without the slash)
        handler: The function to handle the command
        description: A description of what the command does
    """
    command_registry[command_name] = {"handler": handler, "description": description}
    logger.info(f"Registered slash command: /{command_name}")


def get_command_handler(command_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a command handler by name.

    Args:
        command_name: The name of the command (without the slash)

    Returns:
        The command handler or None if not found
    """
    return command_registry.get(command_name)


def get_all_commands() -> List[Dict[str, str]]:
    """
    Get all registered commands.

    Returns:
        A list of command information dictionaries
    """
    return [
        {"name": name, "description": info["description"]}
        for name, info in command_registry.items()
    ]


# Command handlers


def handle_help_command(
    command_text: str, user_id: str, channel_id: str, response_url: str
) -> Dict[str, Any]:
    """
    Handle the /help command.

    Args:
        command_text: The text after the command
        user_id: The Slack user ID
        channel_id: The Slack channel ID
        response_url: The URL to send the response to

    Returns:
        The response to send back to Slack
    """
    commands = get_all_commands()

    # Create blocks for the response
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Available Commands", "emoji": True},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Here are the commands you can use with this bot:",
            },
        },
    ]

    # Add each command to the blocks
    for command in commands:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*/{command['name']}*: {command['description']}",
                },
            }
        )

    return {
        "response_type": "ephemeral",  # Only visible to the user who triggered it
        "text": "Available Commands",
        "blocks": blocks,
    }


def handle_status_command(
    command_text: str, user_id: str, channel_id: str, response_url: str
) -> Dict[str, Any]:
    """
    Handle the /status command.

    Args:
        command_text: The text after the command
        user_id: The Slack user ID
        channel_id: The Slack channel ID
        response_url: The URL to send the response to

    Returns:
        The response to send back to Slack
    """
    # Create blocks for the response
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "System Status", "emoji": True},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "✅ *Bot Service*: Online"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "✅ *Conversation Service*: Online"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "✅ *AI Service*: Online"},
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Environment: {getattr(settings, 'ENVIRONMENT', 'development')}",
                }
            ],
        },
    ]

    return {
        "response_type": "ephemeral",  # Only visible to the user who triggered it
        "text": "System Status",
        "blocks": blocks,
    }


def handle_info_command(
    command_text: str, user_id: str, channel_id: str, response_url: str
) -> Dict[str, Any]:
    """
    Handle the /info command.

    Args:
        command_text: The text after the command
        user_id: The Slack user ID
        channel_id: The Slack channel ID
        response_url: The URL to send the response to

    Returns:
        The response to send back to Slack
    """
    # Create blocks for the response
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "About Konveyor", "emoji": True},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Konveyor is an intelligent onboarding solution for software engineers. It helps new team members get up to speed quickly by providing context-aware answers about your codebase and development processes.",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Key Features:*\n• Contextual code understanding\n• RAG-powered knowledge retrieval\n• Conversation memory\n• Multi-channel support",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "For more information, visit our documentation or contact the development team.",
            },
        },
    ]

    return {
        "response_type": "ephemeral",  # Only visible to the user who triggered it
        "text": "About Konveyor",
        "blocks": blocks,
    }


def handle_code_command(
    command_text: str, user_id: str, channel_id: str, response_url: str
) -> Dict[str, Any]:
    """
    Handle the /code command for code formatting examples.

    Args:
        command_text: The text after the command
        user_id: The Slack user ID
        channel_id: The Slack channel ID
        response_url: The URL to send the response to

    Returns:
        The response to send back to Slack
    """
    # Create blocks for the response
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Code Formatting Examples",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Here are examples of how to format code in messages:",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Inline Code:*\n`const example = 'inline code';`",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Basic Code Block:*\n```\nfunction example() {\n  return 'Hello, world!';\n}\n```",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": '*Python Syntax Highlighting:*\n```python\ndef example():\n    return "Hello, world!"\n```',
            },
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "*Language:* Python"}],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*JavaScript Syntax Highlighting:*\n```javascript\nconst getData = async () => {\n  try {\n    const response = await fetch('/api/data');\n    return await response.json();\n  } catch (error) {\n    console.error('Error fetching data:', error);\n  }\n};\n```",
            },
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "*Language:* JavaScript"}],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Supported Languages:*\nPython, JavaScript, TypeScript, Java, C#, C++, Go, Ruby, Rust, PHP, HTML, CSS, SQL, Shell/Bash, JSON, XML, YAML, and more.",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*How to Use:*\nWrap your code in triple backticks and specify the language:\n\\```python\nyour code here\n\\```",
            },
        },
    ]

    return {
        "response_type": "ephemeral",  # Only visible to the user who triggered it
        "text": "Code Formatting Examples",
        "blocks": blocks,
    }


# Initialize the service
slack_user_profile_service = SlackUserProfileService()


def handle_preferences_command(
    command_text: str, user_id: str, channel_id: str, response_url: str
) -> Dict[str, Any]:
    """
    Handle the /preferences command for viewing and setting user preferences.

    Args:
        command_text: The text after the command
        user_id: The Slack user ID
        channel_id: The Slack channel ID
        response_url: The URL to send the response to

    Returns:
        The response to send back to Slack
    """
    # Get the user profile
    profile = slack_user_profile_service.get_or_create_profile(user_id)

    # Parse the command text
    parts = command_text.strip().split()

    # If no arguments, show current preferences
    if not parts or len(parts) < 2:
        # Create blocks for the response
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Your Preferences",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Here are your current preferences:",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Code Language:* {profile.code_language_preference or 'Not set'}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Response Format:* {profile.response_format_preference or 'concise'}",
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "To set a preference, use:\n`/preferences set code_language python`\n`/preferences set response_format [concise|detailed|technical]`",
                },
            },
        ]

        return {
            "response_type": "ephemeral",  # Only visible to the user who triggered it
            "text": "Your Preferences",
            "blocks": blocks,
        }

    # Handle setting preferences
    action = parts[0].lower()
    if action == "set":
        if len(parts) < 3:
            return {
                "response_type": "ephemeral",
                "text": "Please specify both the preference name and value. Example: `/preferences set code_language python`",
            }

        preference_name = parts[1].lower()
        preference_value = parts[2].lower()

        # Validate preference name
        if preference_name not in ["code_language", "response_format"]:
            return {
                "response_type": "ephemeral",
                "text": f"Unknown preference: {preference_name}. Available preferences: code_language, response_format",
            }

        # Validate response_format value
        if preference_name == "response_format" and preference_value not in [
            "concise",
            "detailed",
            "technical",
        ]:
            return {
                "response_type": "ephemeral",
                "text": f"Invalid value for response_format: {preference_value}. Available options: concise, detailed, technical",
            }

        # Update the preference
        updated_profile = slack_user_profile_service.update_preference(
            user_id, preference_name, preference_value
        )

        if updated_profile:
            return {
                "response_type": "ephemeral",
                "text": f"Your {preference_name} preference has been set to {preference_value}.",
            }
        else:
            return {
                "response_type": "ephemeral",
                "text": "There was an error updating your preference. Please try again.",
            }

    # Handle unknown action
    return {
        "response_type": "ephemeral",
        "text": f"Unknown action: {action}. Available actions: set",
    }


def handle_profile_command(
    command_text: str, user_id: str, channel_id: str, response_url: str
) -> Dict[str, Any]:
    """
    Handle the /profile command for viewing user profile information.

    Args:
        command_text: The text after the command
        user_id: The Slack user ID
        channel_id: The Slack channel ID
        response_url: The URL to send the response to

    Returns:
        The response to send back to Slack
    """
    # Get the user profile
    profile = slack_user_profile_service.get_or_create_profile(user_id)

    # Create blocks for the response
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Your Profile", "emoji": True},
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Name:* {profile.slack_real_name or profile.slack_name}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Display Name:* {profile.slack_display_name or 'Not set'}",
                },
            ],
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Email:* {profile.slack_email or 'Not available'}",
                },
                {"type": "mrkdwn", "text": f"*Slack ID:* {profile.slack_id}"},
            ],
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Interactions:* {profile.interaction_count}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Last Interaction:* {profile.last_interaction.strftime('%Y-%m-%d %H:%M:%S') if profile.last_interaction else 'Never'}",
                },
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "To update your profile information, use `/preferences` to set your preferences.",
            },
        },
    ]

    return {
        "response_type": "ephemeral",  # Only visible to the user who triggered it
        "text": "Your Profile",
        "blocks": blocks,
    }


# Register commands
register_command("help", handle_help_command, "Show available commands")
register_command("status", handle_status_command, "Check system status")
register_command("info", handle_info_command, "Get information about Konveyor")
register_command("code", handle_code_command, "Show code formatting examples")
register_command(
    "preferences", handle_preferences_command, "View and set your preferences"
)
register_command("profile", handle_profile_command, "View your profile information")
