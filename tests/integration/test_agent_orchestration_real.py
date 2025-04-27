"""
Real integration tests for Agent Orchestration Layer.

These tests verify the end-to-end functionality of the Agent Orchestration Layer with real Azure OpenAI credentials,
including integration with the Bot Framework and Semantic Kernel skills.

This file requires the following environment variables to be set:
- AZURE_OPENAI_ENDPOINT: The Azure OpenAI endpoint URL
- AZURE_OPENAI_API_KEY: The Azure OpenAI API key

Optional environment variables:
- AZURE_OPENAI_CHAT_DEPLOYMENT: The name of the chat deployment (default: "gpt-35-turbo")
- AZURE_OPENAI_API_VERSION: The API version (default: "2024-12-01-preview")

Note: These tests use mocked Bot Framework components but real Azure OpenAI services.
"""

import pytest
import asyncio
import logging
import os
from dotenv import load_dotenv
from unittest.mock import patch, MagicMock, AsyncMock
from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ConversationAccount, ChannelAccount, ActivityTypes

from konveyor.apps.bot.bot import KonveyorBot
from konveyor.core.agent import AgentOrchestratorSkill, SkillRegistry
from konveyor.core.chat import ChatSkill
from konveyor.core.kernel import create_kernel

# Configure logging for tests
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Skip all tests if required environment variables are not set
pytestmark = pytest.mark.skipif(
    not all([
        os.environ.get('AZURE_OPENAI_ENDPOINT'),
        os.environ.get('AZURE_OPENAI_API_KEY')
    ]),
    reason="Azure OpenAI credentials not found in environment variables"
)


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


@pytest.mark.asyncio
async def test_bot_initialization():
    """Test that the bot initializes correctly with real Azure OpenAI."""
    try:
        # Create the bot
        bot = KonveyorBot()

        # Check that the components were initialized
        assert hasattr(bot, 'kernel')
        assert hasattr(bot, 'registry')
        assert hasattr(bot, 'orchestrator')
        assert hasattr(bot, 'conversations')
    except Exception as e:
        logger.error(f"Error initializing bot: {str(e)}")
        pytest.fail(f"Bot initialization failed: {str(e)}")


@pytest.mark.asyncio
async def test_bot_message_handling(mock_turn_context):
    """Test that the bot handles messages correctly with real Azure OpenAI."""
    try:
        # Create the bot
        bot = KonveyorBot()

        # Process a message
        await bot.on_message_activity(mock_turn_context)

        # Check that send_activity was called
        mock_turn_context.send_activity.assert_called()

        # Get the last call to send_activity
        last_call = mock_turn_context.send_activity.call_args_list[-1]
        activity = last_call[0][0]

        # Check the activity
        assert activity.type == ActivityTypes.message
        assert activity.text, "Response text should not be empty"
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        pytest.fail(f"Message handling failed: {str(e)}")


@pytest.mark.asyncio
async def test_bot_members_added():
    """Test that the bot handles new members correctly with real Azure OpenAI."""
    try:
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
    except Exception as e:
        logger.error(f"Error handling members added: {str(e)}")
        pytest.fail(f"Members added handling failed: {str(e)}")
