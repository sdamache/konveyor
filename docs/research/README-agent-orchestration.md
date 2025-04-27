# Agent Orchestration Layer

This document provides information about the modules, functions, and variables used in the Agent Orchestration Layer implementation.

## Semantic Kernel

The Agent Orchestration Layer is built on top of the [Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/) framework, which provides a way to integrate AI models into applications.

### Key Classes and Methods

#### Kernel

The `Kernel` class is the central component of Semantic Kernel that manages plugins, services, and function execution.

```python
from semantic_kernel import Kernel

# Create a kernel
kernel = Kernel()
```

**Key Methods:**

- `add_plugin(plugin, plugin_name=None)`: Registers a plugin with the kernel
  - `plugin`: The plugin instance to register
  - `plugin_name`: Optional name for the plugin (defaults to class name)

- `invoke(function, **kwargs)`: Invokes a function with the given arguments
  - `function`: The function to invoke
  - `**kwargs`: Arguments to pass to the function

#### Azure OpenAI Integration

Semantic Kernel provides integration with Azure OpenAI services through the `AzureChatCompletion` class.

```python
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

# Create a chat completion service
chat_service = AzureChatCompletion(
    endpoint="https://your-endpoint.openai.azure.com/",
    api_key="your-api-key",
    deployment_name="gpt-35-turbo",
    api_version="2024-12-01-preview",
    service_id="chat"
)

# Add the service to the kernel
kernel.add_service(chat_service)
```

**Required Parameters:**

- `endpoint`: The Azure OpenAI endpoint URL
- `api_key`: The Azure OpenAI API key
- `deployment_name`: The name of the deployment to use
- `api_version`: The API version to use

#### Kernel Functions

Semantic Kernel provides a decorator for creating kernel functions:

```python
from semantic_kernel.functions import kernel_function

class MySkill:
    @kernel_function(
        description="Description of the function",
        name="function_name"
    )
    def my_function(self, input: str) -> str:
        return f"Processed: {input}"
```

## Bot Framework

The Agent Orchestration Layer integrates with the [Bot Framework](https://dev.botframework.com/) to handle bot interactions.

### Key Classes and Methods

#### ActivityHandler

The `ActivityHandler` class is the base class for handling bot activities.

```python
from botbuilder.core import ActivityHandler, TurnContext

class MyBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        # Handle message activity
        await turn_context.send_activity("Hello, world!")
```

**Key Methods:**

- `on_message_activity(turn_context)`: Handles message activities
  - `turn_context`: The turn context containing the activity

- `on_members_added_activity(members_added, turn_context)`: Handles members added activities
  - `members_added`: The list of members added
  - `turn_context`: The turn context containing the activity

#### TurnContext

The `TurnContext` class provides context for a turn of the bot.

```python
from botbuilder.core import TurnContext

async def handle_turn(turn_context: TurnContext):
    # Access the activity
    activity = turn_context.activity
    
    # Send a response
    await turn_context.send_activity("Hello, world!")
```

**Key Properties:**

- `activity`: The activity being processed
- `responded`: Whether the bot has responded to the activity

**Key Methods:**

- `send_activity(activity_or_text)`: Sends an activity to the user
  - `activity_or_text`: The activity or text to send

## Testing

The Agent Orchestration Layer uses [pytest](https://docs.pytest.org/) for testing, with additional support for asynchronous testing and mocking.

### Key Modules and Functions

#### pytest-asyncio

The `pytest-asyncio` plugin provides support for testing asynchronous code.

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    # Test asynchronous code
    result = await my_async_function()
    assert result == expected_result
```

#### unittest.mock

The `unittest.mock` module provides support for mocking objects and functions.

```python
from unittest.mock import patch, MagicMock, AsyncMock

# Mock a synchronous function
with patch('module.function', return_value='mocked_result'):
    result = module.function()
    assert result == 'mocked_result'

# Mock an asynchronous function
with patch('module.async_function', new_callable=AsyncMock, return_value='mocked_result'):
    result = await module.async_function()
    assert result == 'mocked_result'
```

**Key Classes:**

- `MagicMock`: A mock object that records calls and provides assertions
- `AsyncMock`: A mock object for asynchronous functions
- `patch`: A function for temporarily replacing objects with mocks

## Agent Orchestration Layer

The Agent Orchestration Layer consists of the following components:

### SkillRegistry

The `SkillRegistry` class manages available skills and their metadata.

```python
from konveyor.skills.agent_orchestrator import SkillRegistry

# Create a registry
registry = SkillRegistry()

# Register a skill
registry.register_skill(skill, "SkillName", "Description", ["keyword1", "keyword2"])

# Find a skill for a request
skill_name = registry.find_skill_for_request("User request")
```

**Key Methods:**

- `register_skill(skill, skill_name=None, description=None, keywords=None)`: Registers a skill
  - `skill`: The skill instance to register
  - `skill_name`: Optional name for the skill
  - `description`: Optional description of the skill
  - `keywords`: Optional list of keywords associated with the skill

- `find_skill_for_request(request)`: Finds the most appropriate skill for a request
  - `request`: The user request

### AgentOrchestratorSkill

The `AgentOrchestratorSkill` class routes requests to the appropriate skills.

```python
from konveyor.skills.agent_orchestrator import AgentOrchestratorSkill

# Create an orchestrator
orchestrator = AgentOrchestratorSkill(kernel, registry)

# Process a request
result = await orchestrator.process_request("User request")
```

**Key Methods:**

- `process_request(request, context=None)`: Processes a user request
  - `request`: The user request
  - `context`: Optional context information

- `register_skill(skill, skill_name=None, description=None, keywords=None)`: Registers a skill
  - `skill`: The skill instance to register
  - `skill_name`: Optional name for the skill
  - `description`: Optional description of the skill
  - `keywords`: Optional list of keywords associated with the skill

## Environment Variables

The Agent Orchestration Layer requires the following environment variables:

- `AZURE_OPENAI_ENDPOINT`: The Azure OpenAI endpoint URL
- `AZURE_OPENAI_API_KEY`: The Azure OpenAI API key
- `AZURE_OPENAI_CHAT_DEPLOYMENT`: The name of the chat deployment to use (default: "gpt-35-turbo")
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`: The name of the embedding deployment to use (default: "text-embedding-ada-002")
- `AZURE_OPENAI_API_VERSION`: The API version to use (default: "2024-12-01-preview")

## Testing

The Agent Orchestration Layer includes both mock tests and real tests:

- **Mock Tests**: Use mocked dependencies to test functionality without external services
  - `tests/core/skills/test_agent_orchestrator_mock.py`: Unit tests with mocked dependencies
  - `tests/integration/test_agent_orchestration_mock.py`: Integration tests with mocked dependencies

- **Real Tests**: Use real Azure OpenAI credentials to test functionality with external services
  - `tests/core/skills/test_agent_orchestrator_real.py`: Unit tests with real dependencies
  - `tests/integration/test_agent_orchestration_real.py`: Integration tests with real dependencies

To run the tests:

```bash
# Run mock tests
python -m pytest tests/core/skills/test_agent_orchestrator_mock.py
python -m pytest tests/integration/test_agent_orchestration_mock.py

# Run real tests (requires Azure OpenAI credentials)
python -m pytest tests/core/skills/test_agent_orchestrator_real.py
python -m pytest tests/integration/test_agent_orchestration_real.py
```

## References

- [Semantic Kernel Documentation](https://learn.microsoft.com/en-us/semantic-kernel/)
- [Semantic Kernel Python API Reference](https://learn.microsoft.com/en-us/python/api/semantic-kernel/?view=semantic-kernel-python)
- [Bot Framework Documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Bot Framework Python SDK](https://docs.microsoft.com/en-us/python/api/botbuilder-core/?view=botbuilder-py-latest)
- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
