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

### `/konveyor-docs`
Searches documentation using the Documentation Navigator skill.

**Usage:**
```
/konveyor-docs [query]
```

**Examples:**
```
/konveyor-docs how to deploy to production
/konveyor-docs authentication system
/konveyor-docs environment setup
```

### `/konveyor-code`
Analyzes and explains code snippets using the Code Understanding skill.

**Usage:**
```
/konveyor-code [language]
```
After running this command, you'll be prompted to share a code snippet.

**Examples:**
```
/konveyor-code python
/konveyor-code javascript
/konveyor-code java
```

### `/konveyor-analyze`
Analyzes your knowledge gaps using the Knowledge Gap Analyzer skill.

**Usage:**
```
/konveyor-analyze [topic]
```

**Examples:**
```
/konveyor-analyze microservices
/konveyor-analyze authentication
/konveyor-analyze deployment process
```

### `/konveyor-feedback`
Provides feedback on the bot's responses to help improve its performance.

**Usage:**
```
/konveyor-feedback [message_id] [rating] [comment]
```

**Examples:**
```
/konveyor-feedback 1234567890 positive "Very helpful explanation!"
/konveyor-feedback 1234567890 negative "The explanation was too technical."
```

### `/code`
Shows examples of how to format code in Slack messages.

**Usage:**
```
/code
```

### `/profile`
Displays your user profile information, including interaction history and knowledge areas.

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

# Set knowledge tracking preference
/preferences set knowledge_tracking [enabled|disabled]
```

**Examples:**
```
/preferences set code_language python
/preferences set response_format detailed
/preferences set knowledge_tracking enabled
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
