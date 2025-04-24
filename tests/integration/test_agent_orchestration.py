"""
Integration tests for Agent Orchestration Layer.

These tests verify the end-to-end functionality of the Agent Orchestration Layer,
including integration with the Bot Framework and Semantic Kernel skills.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ConversationAccount, ChannelAccount

from konveyor.apps.bot.bot import KonveyorBot
from konveyor.skills.agent_orchestrator import AgentOrchestratorSkill, SkillRegistry
from konveyor.skills.ChatSkill import ChatSkill


@pytest.fixture
def mock_turn_context():
    """Create a mock TurnContext for testing."""
    context = MagicMock(spec=TurnContext)

    # Mock the send_activity method
    context.send_activity = AsyncMock(return_value=None)
    context.send_activities = AsyncMock(return_value=None)

    # Create a mock activity
    activity = Activity(
        text="Hello, bot!",
        type="message",
        conversation=ConversationAccount(id="test-conversation"),
        from_property=ChannelAccount(id="test-user")
    )
    context.activity = activity

    return context


@pytest.fixture
def mock_kernel():
    """Mock Kernel for testing."""
    with patch('konveyor.skills.setup.create_kernel') as mock_create_kernel:
        kernel = MagicMock()

        # Mock the invoke method
        async def mock_invoke(function, **kwargs):
            # Return different responses based on the function name
            if hasattr(function, 'name'):
                if function.name == 'answer_question':
                    return f"Answer to: {kwargs.get('question', '')}"
                elif function.name == 'chat':
                    return {
                        "response": f"Chat response to: {kwargs.get('message', '')}",
                        "history": f"User: {kwargs.get('message', '')}\nAssistant: Chat response"
                    }
                elif function.name == 'process_request':
                    return {
                        "response": f"Processed: {kwargs.get('request', '')}",
                        "skill_name": "TestSkill",
                        "function_name": "test_function",
                        "success": True
                    }

            return "Mock response"

        kernel.invoke = AsyncMock(side_effect=mock_invoke)

        # Mock the add_plugin method
        def mock_add_plugin(skill, plugin_name=None):
            # Create a dictionary of mock functions
            functions = {}

            # If it's a ChatSkill, add its functions
            if isinstance(skill, ChatSkill):
                for method_name in ['answer_question', 'chat', 'greet', 'format_as_bullet_list']:
                    mock_function = MagicMock()
                    mock_function.name = method_name
                    functions[method_name] = mock_function
            elif isinstance(skill, AgentOrchestratorSkill):
                for method_name in ['process_request', 'register_skill', 'get_available_skills']:
                    mock_function = MagicMock()
                    mock_function.name = method_name
                    functions[method_name] = mock_function

            return functions

        kernel.add_plugin = mock_add_plugin
        kernel.plugins = {}

        mock_create_kernel.return_value = kernel
        yield kernel


@pytest.mark.asyncio
async def test_bot_initialization(mock_kernel):
    """Test that the bot initializes correctly."""
    # Patch the create_kernel function to avoid validation errors
    with patch('konveyor.apps.bot.bot.create_kernel', return_value=mock_kernel):
        # Create the bot
        bot = KonveyorBot()

        # Check that the components were initialized
        assert hasattr(bot, 'kernel')
        assert hasattr(bot, 'registry')
        assert hasattr(bot, 'orchestrator')
        assert hasattr(bot, 'conversations')


@pytest.mark.asyncio
async def test_bot_message_handling(mock_kernel, mock_turn_context):
    """Test that the bot handles messages correctly."""
    # Patch the create_kernel function to avoid validation errors
    with patch('konveyor.apps.bot.bot.create_kernel', return_value=mock_kernel):
        # Create the bot
        bot = KonveyorBot()

        # Set up the orchestrator to return a specific response
        bot.orchestrator.process_request = AsyncMock(return_value={
            "response": "Test response",
            "skill_name": "TestSkill",
            "function_name": "test_function",
            "success": True
        })

        # Process a message
        await bot.on_message_activity(mock_turn_context)

        # Check that the orchestrator was called
        bot.orchestrator.process_request.assert_called_once()

        # Check that send_activity was called with the expected response
        mock_turn_context.send_activity.assert_called()

        # Get the last call to send_activity
        last_call = mock_turn_context.send_activity.call_args_list[-1]
        activity = last_call[0][0]

        # Check the activity
        assert activity.type == ActivityTypes.message
        assert activity.text == "Test response"


@pytest.mark.asyncio
async def test_bot_error_handling(mock_kernel, mock_turn_context):
    """Test that the bot handles errors correctly."""
    # Patch the create_kernel function to avoid validation errors
    with patch('konveyor.apps.bot.bot.create_kernel', return_value=mock_kernel):
        # Create the bot
        bot = KonveyorBot()

        # Set up the orchestrator to raise an exception
        bot.orchestrator.process_request = AsyncMock(side_effect=Exception("Test error"))

        # Process a message
        await bot.on_message_activity(mock_turn_context)

        # Check that send_activity was called with an error message
        mock_turn_context.send_activity.assert_called()

        # Get the last call to send_activity
        last_call = mock_turn_context.send_activity.call_args_list[-1]
        activity = last_call[0][0]

        # Check the activity
        assert activity.type == ActivityTypes.message
        assert "error" in activity.text.lower()
        assert "Test error" in activity.text


@pytest.mark.asyncio
async def test_bot_conversation_state(mock_kernel, mock_turn_context):
    """Test that the bot maintains conversation state."""
    # Patch the create_kernel function to avoid validation errors
    with patch('konveyor.apps.bot.bot.create_kernel', return_value=mock_kernel):
        # Create the bot
        bot = KonveyorBot()

        # Set up the orchestrator to return a response with history
        bot.orchestrator.process_request = AsyncMock(return_value={
            "response": "Test response",
            "history": "User: Hello\nAssistant: Test response",
            "skill_name": "TestSkill",
            "function_name": "test_function",
            "success": True
        })

        # Process a message
        await bot.on_message_activity(mock_turn_context)

        # Check that the conversation state was updated
        conversation_id = mock_turn_context.activity.conversation.id
        assert conversation_id in bot.conversations
        assert bot.conversations[conversation_id]["history"] == "User: Hello\nAssistant: Test response"


@pytest.mark.asyncio
async def test_bot_members_added(mock_kernel):
    """Test that the bot handles new members correctly."""
    # Patch the create_kernel function to avoid validation errors
    with patch('konveyor.apps.bot.bot.create_kernel', return_value=mock_kernel):
        # Create the bot
        bot = KonveyorBot()

        # Create a mock turn context
        context = MagicMock(spec=TurnContext)
        context.send_activity = AsyncMock(return_value=None)

        # Create a mock activity
        activity = Activity(
            type="conversationUpdate",
            recipient=ChannelAccount(id="bot-id"),
            conversation=ConversationAccount(id="test-conversation")
        )
        context.activity = activity

        # Create a list of members added
        members_added = [
            ChannelAccount(id="user-id"),
            ChannelAccount(id="bot-id")
        ]

        # Process the members added event
        await bot.on_members_added_activity(members_added, context)

        # Check that send_activity was called for the user but not for the bot
        assert context.send_activity.call_count == 1
