# Slack Direct Integration for Konveyor

This document provides instructions for setting up and testing the direct Slack integration for Konveyor.

## Overview

The Slack integration allows users to interact with the Konveyor agent through Slack. It uses the Slack SDK to communicate with Slack and the Agent Orchestration Layer to process messages.

## Setup

### 1. Create a Slack App

1. Go to the [Slack API website](https://api.slack.com/apps) and sign in
2. Click "Create New App" and select "From scratch"
3. Enter a name for your app (e.g., "Konveyor") and select a workspace
4. Under "OAuth & Permissions", add the following Bot Token Scopes:
   - `chat:write`
   - `im:history`
   - `im:read`
   - `im:write`
   - `channels:history`
   - `channels:read`
   - `groups:history`
   - `groups:read`
   - `users:read`
   - `users:read.email`
5. Install the app to your workspace
6. Copy the Bot User OAuth Token from the "OAuth & Permissions" page
7. Under "Basic Information", copy the Signing Secret

### 2. Configure Environment Variables

Add the following environment variables to your `.env` file:

```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_TEST_CHANNEL=channel-id-for-testing
NGROK_URL=https://your-ngrok-url.ngrok-free.app
```

### 3. Install Dependencies

Make sure you have the Slack SDK installed:

```bash
pip install slack_sdk
```

### 4. Configure Slack Events

1. Start your Django development server:

```bash
python manage.py runserver
```

2. Make your server publicly accessible using a tool like ngrok:

```bash
ngrok http 8000
```

After starting ngrok, copy the HTTPS URL and set it as the `NGROK_URL` environment variable:

```bash
export NGROK_URL=https://your-ngrok-url.ngrok-free.app
```

3. Copy the HTTPS URL provided by ngrok (e.g., `https://abc123.ngrok.io`)

4. In your Slack app settings, go to "Event Subscriptions" and enable events
5. Set the Request URL to `https://your-ngrok-url/api/bot/slack/events/`
6. Subscribe to the following bot events:
   - `message.channels`
   - `message.groups`
   - `message.im`
   - `message.mpim`
7. Save your changes

## Testing

### 1. Test Sending Direct Messages

You can test sending direct messages to Slack users using the provided test script:

```bash
# Test with an environment variable
export SLACK_TEST_USER_EMAIL=user@example.com
python scripts/test_slack_integration.py

# Or provide the email as a command-line argument
python scripts/test_slack_integration.py user@example.com
```

This script will:
1. Look up the user by email
2. Open a direct message channel with the user
3. Send a test message to the user

If you don't provide an email, the script will try to test the API connection by retrieving the bot's own user ID.

### 2. Test Receiving Messages

1. Make sure your Django server is running and publicly accessible
2. Send a message in a channel where your bot is present or send a direct message to your bot
3. Check the Django server logs to see if the message was received and processed
4. The bot should respond to your message

## Troubleshooting

### Common Issues

1. **Bot doesn't respond to messages**:
   - Check that your bot is invited to the channel
   - Verify that the Event Subscriptions are properly configured
   - Check the Django server logs for errors

2. **Authentication errors**:
   - Verify that the `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` are correct
   - Make sure the bot has the necessary OAuth scopes

3. **Request URL verification fails**:
   - Make sure your server is publicly accessible
   - Check that the URL is correct and includes the `/api/bot/slack/events/` path
   - Verify that your server is responding to the verification request

### Debugging

To enable more detailed logging, add the following to your `.env` file:

```
DJANGO_LOG_LEVEL=DEBUG
```

## Architecture

The Slack integration consists of the following components:

1. **SlackService**: Handles communication with the Slack API
2. **Webhook Endpoint**: Receives events from Slack
3. **Agent Orchestration Layer**: Processes messages and generates responses

```
┌─────────────┐     ┌─────────────────┐
│             │     │                 │
│    Slack    │◄────┤ Django Backend  │
│             │     │                 │
└─────────────┘     └─────────────────┘
                            ▲
                            │
                   ┌─────────────────┐
                   │                 │
                   │ Agent           │
                   │ Orchestration   │
                   │ Layer           │
                   │                 │
                   └─────────────────┘
```

## Files

- `konveyor/apps/bot/services/slack_service.py`: Slack service for sending messages and verifying requests
- `konveyor/apps/bot/views.py`: Webhook endpoint for receiving Slack events
- `konveyor/apps/bot/urls.py`: URL configuration for the bot app
- `scripts/test_slack_integration.py`: Test script for sending messages to Slack

## References

- [Slack API Documentation](https://api.slack.com/docs)
- [Slack Python SDK](https://slack.dev/python-slack-sdk/)
- [Django Documentation](https://docs.djangoproject.com/)
- [ngrok Documentation](https://ngrok.com/docs)
