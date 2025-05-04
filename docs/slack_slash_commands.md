# Slack Slash Commands

This document provides information about the available slash commands in the Konveyor Slack bot.

## Available Commands

### `/help`
Shows a list of available commands and their descriptions.

**Usage:**
```
/help
```

### `/status`
Checks the system status, including the bot's connection to various services.

**Usage:**
```
/status
```

### `/info`
Provides information about Konveyor, including version and capabilities.

**Usage:**
```
/info
```

### `/code`
Shows examples of how to format code in Slack messages.

**Usage:**
```
/code
```

### `/profile`
Displays your user profile information, including interaction history.

**Usage:**
```
/profile
```

### `/preferences`
Views and sets your user preferences.

**Usage:**
```
# View current preferences
/preferences

# Set code language preference
/preferences set code_language [language]

# Set response format preference
/preferences set response_format [concise|detailed|technical]
```

**Examples:**
```
/preferences set code_language python
/preferences set response_format detailed
```

## Command Endpoint

All slash commands are routed to the `/api/bot/slack/commands/` endpoint in the Konveyor API.

## Adding New Commands

To add a new slash command:

1. Register the command in the Slack API dashboard:
   - Go to api.slack.com/apps
   - Select your app
   - Go to "Slash Commands"
   - Click "Create New Command"
   - Set the Request URL to your API endpoint: `https://your-domain.com/api/bot/slack/commands/`

2. Implement the command handler in the code:
   ```python
   # In slash_commands.py
   def handle_new_command(command_text, user_id, channel_id, response_url):
       # Command implementation
       return {
           "response_type": "ephemeral",  # or "in_channel" for public responses
           "text": "Command response"
       }

   # Register the command
   register_command("new_command", handle_new_command, "Description of the new command")
   ```

## User Preferences

The following user preferences can be set using the `/preferences` command:

### Code Language Preference
Sets your preferred programming language for code examples.

**Available options:** Any programming language (e.g., python, javascript, java, etc.)

### Response Format Preference
Sets your preferred level of detail in responses.

**Available options:**
- `concise`: Brief, to-the-point responses
- `detailed`: More comprehensive responses with explanations
- `technical`: Technical responses with in-depth information
