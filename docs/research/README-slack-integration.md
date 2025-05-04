# Slack Integration with Django and Bot Framework

This document provides information about how the Slack integration works with our Django backend using Microsoft Bot Framework.

## Latest Bot Framework SDK Information

The Microsoft Bot Framework SDK for Python is currently at version 4.16.1 (as of July 2024). The SDK provides a comprehensive framework for building conversational AI experiences, including integration with Slack and other channels.

Key features of the latest Bot Framework SDK:
- Support for multiple channels including Slack, Microsoft Teams, and more
- Rich conversation management capabilities
- Integration with Azure OpenAI and other AI services
- Adaptive dialogs for complex conversation flows
- State management for maintaining conversation context

## Overview

The Konveyor project integrates with Slack using Microsoft Bot Framework, which provides a standardized way to build bots that can communicate across multiple channels, including Slack. The integration consists of several components:

1. **Bot Framework Adapter**: Handles the communication between Slack and our Django application
2. **KonveyorBot**: Implements the bot logic and handles messages
3. **Agent Orchestration Layer**: Routes messages to the appropriate skills
4. **Django Integration**: Exposes endpoints for the Bot Framework to communicate with our application

## Integration Approaches

There are two main approaches to integrating Slack with a Django backend:

### 1. Using Bot Framework (Current Implementation)

This approach uses Microsoft Bot Framework as an intermediary between Slack and our Django backend. The Bot Framework handles the communication with Slack and provides a standardized way to build bots that can communicate across multiple channels.

```
┌─────────────┐     ┌───────────────┐     ┌─────────────────┐
│             │     │               │     │                 │
│    Slack    │◄────┤ Bot Framework │◄────┤ Django Backend  │
│             │     │               │     │                 │
└─────────────┘     └───────────────┘     └─────────────────┘
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

**Advantages:**
- Standardized approach that works across multiple channels
- Handles authentication and message formatting
- Provides rich conversation management capabilities
- Integrates with Azure services

**Disadvantages:**
- More complex setup
- Requires Azure Bot Service configuration
- Additional dependencies

### 2. Direct Slack SDK Integration (Alternative Approach)

An alternative approach is to use the Slack SDK directly in the Django application, bypassing the Bot Framework entirely.

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

**Advantages:**
- Simpler setup
- Direct integration without intermediaries
- Fewer dependencies
- More control over the integration

**Disadvantages:**
- Limited to Slack only
- Requires manual handling of authentication and message formatting
- No standardized approach for other channels

For our implementation, we've chosen the Bot Framework approach to maintain consistency with other channels and leverage the rich capabilities of the Bot Framework.

## Bot Framework Components

### 1. Bot Framework Adapter

The Bot Framework Adapter handles the communication between Slack and our Django application. It's responsible for:

- Receiving messages from Slack
- Sending messages to Slack
- Handling authentication and authorization

```python
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings

# Create the adapter with the appropriate settings
adapter = BotFrameworkAdapter(
    BotFrameworkAdapterSettings(
        app_id=os.environ.get("MICROSOFT_APP_ID"),
        app_password=os.environ.get("MICROSOFT_APP_PASSWORD")
    )
)
```

### 2. KonveyorBot

The KonveyorBot class (`konveyor/apps/bot/bot.py`) implements the bot logic and handles messages. It:

- Initializes the Semantic Kernel and Agent Orchestration Layer
- Processes incoming messages
- Manages conversation state
- Sends responses back to users

```python
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ActivityTypes, Activity

class KonveyorBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        # Process the message using the Agent Orchestration Layer
        result = await self.orchestrator.process_request(turn_context.activity.text)

        # Send the response back to the user
        await turn_context.send_activity(result["response"])
```

### 3. Agent Orchestration Layer

The Agent Orchestration Layer (`konveyor/skills/agent_orchestrator/`) routes messages to the appropriate skills. It:

- Determines which skill should handle a message
- Invokes the appropriate skill function
- Formats the response for the user

```python
class AgentOrchestratorSkill:
    async def process_request(self, request, context=None):
        # Find the appropriate skill for this request
        skill_name = self.registry.find_skill_for_request(request)

        # Invoke the skill function
        result = await self._invoke_skill_function(skill_name, request)

        # Return the response
        return result
```

## Django Integration

### 1. Webhook Endpoint

The Django application exposes a webhook endpoint that receives messages from Slack via Bot Framework:

```python
@csrf_exempt
@require_POST
def bot_webhook(request):
    """Handle incoming bot messages."""
    if request.content_type != "application/json":
        return HttpResponse(status=415)

    # Parse the incoming activity
    body = json.loads(request.body)
    activity = Activity.deserialize(body)

    # Get the auth header
    auth_header = request.headers.get("Authorization", "")

    # Process the activity
    response = await adapter.process_activity(activity, auth_header, bot.on_turn)

    if response:
        return JsonResponse(response.body, status=response.status)
    return JsonResponse({})
```

### 2. URL Configuration

The webhook endpoint is registered in the URL configuration:

```python
# konveyor/urls.py
urlpatterns = [
    # ... other URLs
    path('api/bot/', include('konveyor.apps.bot.urls')),
]

# konveyor/apps/bot/urls.py
urlpatterns = [
    path('', views.bot_webhook, name='bot_webhook'),
]
```

## Setting Up Slack Integration

To set up the Slack integration, you need to:

1. Create a Slack app in the [Slack API portal](https://api.slack.com/apps)
2. Configure the Bot Framework channel in Azure
3. Connect your Django application to the Bot Framework

### 1. Create a Slack App

1. Go to [Slack API portal](https://api.slack.com/apps) and sign in
2. Click "Create New App" and select "From scratch"
3. Enter a name for your app and select a workspace
4. Under "OAuth & Permissions", add the following Bot Token Scopes:
   - `chat:write`
   - `im:history`
   - `im:read`
   - `im:write`
   - `channels:history`
   - `channels:read`
   - `groups:history`
   - `groups:read`
   - `mpim:history`
   - `mpim:read`
5. Add a Redirect URL: `https://slack.botframework.com` (or the regional equivalent)
6. Under "Event Subscriptions", enable events and set the Request URL to:
   `https://slack.botframework.com/api/Events/{bot-name}` (replace `{bot-name}` with your bot's name)
7. Subscribe to the following bot events:
   - `message.channels`
   - `message.groups`
   - `message.im`
   - `message.mpim`
   - `member_joined_channel`
   - `member_left_channel`
8. Under "Interactivity & Shortcuts", enable interactivity and set the Request URL to:
   `https://slack.botframework.com/api/Actions`
9. Install the app to your workspace

### 2. Configure Bot Framework in Azure

1. Go to the [Azure portal](https://portal.azure.com/)
2. Open your Bot resource
3. Go to "Channels" and select "Slack"
4. Enter the following information from your Slack app:
   - Client ID
   - Client Secret
   - Verification Token
   - Signing Secret
5. Click "Save"

### 3. Connect Django to Bot Framework

1. Add the following environment variables to your Django application:
   - `MICROSOFT_APP_ID`: The App ID from your Bot Framework registration
   - `MICROSOFT_APP_PASSWORD`: The App Password from your Bot Framework registration
2. Install the required packages:
   ```
   pip install botbuilder-core botbuilder-schema botframework-connector
   ```
3. Implement the webhook endpoint as shown above
4. Deploy your Django application

## Testing the Integration

To test the Slack integration:

1. Add your bot to a Slack channel
2. Send a message mentioning your bot (e.g., `@YourBot hello`)
3. The bot should respond based on the Agent Orchestration Layer logic

## Troubleshooting

If you encounter issues with the Slack integration:

1. Check the logs in your Django application for errors
2. Verify that the Bot Framework channel is properly configured in Azure
3. Ensure that your Slack app has the correct permissions and event subscriptions
4. Check that the environment variables are correctly set in your Django application

## Alternative Implementation: Direct Slack SDK Integration

If you prefer a simpler approach without using Bot Framework, you can integrate directly with Slack using the Slack SDK. Here's how to implement this alternative approach:

### 1. Create a Slack App

1. Go to the [Slack API website](https://api.slack.com/) and sign in
2. Click "Create New App" and select "From scratch"
3. Enter a name for your app and select a workspace
4. Under "OAuth & Permissions", add the following Bot Token Scopes:
   - `chat:write`
   - `im:history`
   - `im:read`
   - `im:write`
   - `users:read`
   - `users:read.email`
5. Install the app to your workspace
6. Copy the OAuth Access Token from the "OAuth & Permissions" page

### 2. Install the Slack SDK

```bash
pip install slack_sdk
```

### 3. Implement the Slack Integration in Django

```python
from slack_sdk import WebClient
from django.contrib.auth.models import User
from django.conf import settings

# Initialize the Slack client
client = WebClient(token=settings.SLACK_OAUTH_TOKEN)

def send_message_to_channel(channel_id, message):
    """Send a message to a Slack channel."""
    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=message
        )
        return response
    except Exception as e:
        print(f"Error sending message to Slack: {str(e)}")
        return None

def get_slack_user_id(user_email):
    """Get a Slack user ID from their email address."""
    try:
        response = client.users_lookupByEmail(email=user_email)
        return response.get('user').get('id')
    except Exception as e:
        print(f"Error looking up Slack user: {str(e)}")
        return None

def send_direct_message(user_email, message):
    """Send a direct message to a user by email."""
    slack_user_id = get_slack_user_id(user_email)
    if slack_user_id:
        return send_message_to_channel(f"@{slack_user_id}", message)
    return None
```

### 4. Add Settings to Django

Add the Slack OAuth token to your Django settings:

```python
# settings.py
SLACK_OAUTH_TOKEN = 'xoxb-your-token-here'
```

### 5. Use the Slack Integration in Your Views

```python
from django.http import JsonResponse
from .slack_utils import send_message_to_channel, send_direct_message

def notify_user(request, user_id):
    """Notify a user about something."""
    user = User.objects.get(id=user_id)
    message = f"Hello {user.first_name}, you have a new notification!"

    # Send a direct message to the user
    response = send_direct_message(user.email, message)

    if response:
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=500)
```

This approach is simpler than using Bot Framework but is limited to Slack only. If you need to support multiple channels, the Bot Framework approach is recommended.

## References

- [Bot Framework Documentation](https://learn.microsoft.com/en-us/azure/bot-service/)
- [Connect a Bot Framework bot to Slack](https://learn.microsoft.com/en-us/azure/bot-service/bot-service-channel-connect-slack)
- [Bot Builder Python SDK](https://github.com/Microsoft/botbuilder-python)
- [Slack API Documentation](https://api.slack.com/docs)
- [Slack Python SDK](https://slack.dev/python-slack-sdk/)
- [Django Documentation](https://docs.djangoproject.com/)
- [Django: Step-by-step Slack integration](https://adrienvanthong.medium.com/django-step-by-step-slack-integration-8e16ad976013)
