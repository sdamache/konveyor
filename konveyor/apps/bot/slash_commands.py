"""
Slash command handlers for the Slack bot.

This module contains handlers for Slack slash commands.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Callable
from django.conf import settings

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
    command_registry[command_name] = {
        "handler": handler,
        "description": description
    }
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

def handle_help_command(command_text: str, user_id: str, channel_id: str, response_url: str) -> Dict[str, Any]:
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
            "text": {
                "type": "plain_text",
                "text": "Available Commands",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Here are the commands you can use with this bot:"
            }
        }
    ]

    # Add each command to the blocks
    for command in commands:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*/{command['name']}*: {command['description']}"
            }
        })

    return {
        "response_type": "ephemeral",  # Only visible to the user who triggered it
        "text": "Available Commands",
        "blocks": blocks
    }

def handle_status_command(command_text: str, user_id: str, channel_id: str, response_url: str) -> Dict[str, Any]:
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
            "text": {
                "type": "plain_text",
                "text": "System Status",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "✅ *Bot Service*: Online"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "✅ *Conversation Service*: Online"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "✅ *AI Service*: Online"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Environment: {getattr(settings, 'ENVIRONMENT', 'development')}"
                }
            ]
        }
    ]

    return {
        "response_type": "ephemeral",  # Only visible to the user who triggered it
        "text": "System Status",
        "blocks": blocks
    }

def handle_info_command(command_text: str, user_id: str, channel_id: str, response_url: str) -> Dict[str, Any]:
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
            "text": {
                "type": "plain_text",
                "text": "About Konveyor",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Konveyor is an intelligent onboarding solution for software engineers. It helps new team members get up to speed quickly by providing context-aware answers about your codebase and development processes."
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Key Features:*\n• Contextual code understanding\n• RAG-powered knowledge retrieval\n• Conversation memory\n• Multi-channel support"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "For more information, visit our documentation or contact the development team."
            }
        }
    ]

    return {
        "response_type": "ephemeral",  # Only visible to the user who triggered it
        "text": "About Konveyor",
        "blocks": blocks
    }

def handle_code_command(command_text: str, user_id: str, channel_id: str, response_url: str) -> Dict[str, Any]:
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
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Here are examples of how to format code in messages:"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Inline Code:*\n`const example = 'inline code';`"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Code Block:*\n```\nfunction example() {\n  return 'Hello, world!';\n}\n```"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Syntax Highlighted Code:*\n```python\ndef example():\n    return \"Hello, world!\"\n```"
            }
        }
    ]

    return {
        "response_type": "ephemeral",  # Only visible to the user who triggered it
        "text": "Code Formatting Examples",
        "blocks": blocks
    }

# Register commands
register_command("help", handle_help_command, "Show available commands")
register_command("status", handle_status_command, "Check system status")
register_command("info", handle_info_command, "Get information about Konveyor")
register_command("code", handle_code_command, "Show code formatting examples")
