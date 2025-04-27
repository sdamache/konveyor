# Bot Framework Integration

This module contains the integration with Microsoft Bot Framework for the Konveyor project.

## Structure

- `app.py`: Bot Framework app setup and message handler
- `bot.py`: Bot Framework bot implementation
- `services/`: Services for Bot Framework integration
  - `settings.py`: Service for managing bot settings
  - `credentials.py`: Service for securely managing bot credentials
  - `channels.py`: Service for configuring Slack channel in Bot Service
- `scripts/`: Scripts for setting up Bot Framework
  - `setup_credentials.py`: Script for setting up secure credential storage
  - `setup_slack.py`: Script for initializing Slack channel
- `templates/`: Templates for Bot Framework deployment
  - `bot-template.json`: Azure ARM template for Bot Service deployment

## Usage

This module is used when integrating with Microsoft Bot Framework. For direct Slack integration, see the `konveyor.core.slack` module.
