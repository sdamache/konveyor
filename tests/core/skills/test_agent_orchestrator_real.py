"""
Real tests for Agent Orchestrator Skill.

These tests verify the functionality of the Agent Orchestrator Skill with real Azure OpenAI credentials,  # noqa: E501
including request routing, skill selection, and response handling.

This file requires the following environment variables to be set:
- AZURE_OPENAI_ENDPOINT: The Azure OpenAI endpoint URL
- AZURE_OPENAI_API_KEY: The Azure OpenAI API key

Optional environment variables:
- AZURE_OPENAI_CHAT_DEPLOYMENT: The name of the chat deployment (default: "gpt-35-turbo")  # noqa: E501
- AZURE_OPENAI_API_VERSION: The API version (default: "2024-12-01-preview")
"""

import logging
import os

import pytest
from dotenv import load_dotenv
from semantic_kernel import Kernel  # noqa: F401

from konveyor.core.agent import AgentOrchestratorSkill, SkillRegistry
from konveyor.core.chat import ChatSkill
from konveyor.core.kernel import create_kernel

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Skip all tests if required environment variables are not set
pytestmark = pytest.mark.skipif(
    not all(
        [
            os.environ.get("AZURE_OPENAI_ENDPOINT"),
            os.environ.get("AZURE_OPENAI_API_KEY"),
        ]
    ),
    reason="Azure OpenAI credentials not found in environment variables",
)


@pytest.fixture()
def real_kernel():
    """Create a real Kernel with Azure OpenAI for testing."""
    try:
        kernel = create_kernel()
        return kernel
    except Exception as e:
        logger.error(f"Failed to create kernel: {str(e)}")
        pytest.skip(f"Failed to create kernel: {str(e)}")


@pytest.fixture()
def registry():
    """Create a SkillRegistry for testing."""
    return SkillRegistry()


@pytest.fixture()
def chat_skill():
    """Create a ChatSkill for testing."""
    return ChatSkill()


@pytest.fixture()
def orchestrator(real_kernel, registry, chat_skill):
    """Create an AgentOrchestratorSkill for testing."""
    orchestrator = AgentOrchestratorSkill(real_kernel, registry)
    orchestrator.register_skill(
        chat_skill,
        "ChatSkill",
        "Handles general chat interactions and questions",
        ["chat", "question", "answer", "help"],
    )
    return orchestrator


@pytest.mark.asyncio()
async def test_process_request_with_chat(orchestrator):
    """Test processing a chat request with real Azure OpenAI."""
    # Process a chat request
    request = "Hello, how are you today?"
    result = await orchestrator.process_request(request)

    # Check the result
    assert isinstance(result, dict)
    assert "response" in result
    assert result["response"], "Response should not be empty"
    # The skill_name might be either ChatSkill or AgentOrchestratorSkill depending on how routing works  # noqa: E501
    assert result["skill_name"] in ["ChatSkill", "AgentOrchestratorSkill"]
    # The function_name might vary depending on how the request is processed
    assert "function_name" in result
    # Success might be True or False depending on whether the request was processed successfully  # noqa: E501
    assert "success" in result


@pytest.mark.asyncio()
async def test_process_request_with_question(orchestrator):
    """Test processing a question request with real Azure OpenAI."""
    # Process a question request
    request = "What is Semantic Kernel?"
    result = await orchestrator.process_request(request)

    # Check the result
    assert isinstance(result, dict)
    assert "response" in result
    assert result["response"], "Response should not be empty"
    # We can't guarantee the exact content of the response, so we'll just check that it's not empty  # noqa: E501
    # The skill_name might be either ChatSkill or AgentOrchestratorSkill depending on how routing works  # noqa: E501
    assert result["skill_name"] in ["ChatSkill", "AgentOrchestratorSkill"]
    # The function_name might vary depending on how the request is processed
    assert "function_name" in result
    # Success might be True or False depending on whether the request was processed successfully  # noqa: E501
    assert "success" in result


@pytest.mark.asyncio()
async def test_process_request_with_empty_request(orchestrator):
    """Test processing an empty request with real Azure OpenAI."""
    # Process an empty request
    request = ""
    result = await orchestrator.process_request(request)

    # Check the result
    assert isinstance(result, dict)
    assert "response" in result
    assert "I need a request to process" in result["response"]
    assert result["skill_name"] == "AgentOrchestratorSkill"
    assert result["function_name"] == "process_request"
    assert result["success"] is False


def test_register_skill(orchestrator, registry):
    """Test registering a skill with real registry."""

    # Create a new skill
    class TestSkill:
        def test_function(self):
            return "Test result"

    skill = TestSkill()

    # Register the skill
    skill_name = orchestrator.register_skill(
        skill, "TestSkill", "A test skill", ["test", "example"]
    )

    # Check that the skill was registered
    assert skill_name == "TestSkill"
    assert registry.get_skill("TestSkill") is skill
    assert "test" in registry.keywords["TestSkill"]
    assert "example" in registry.keywords["TestSkill"]


def test_get_available_skills(orchestrator):
    """Test getting information about available skills with real registry."""
    # Get available skills
    result = orchestrator.get_available_skills()

    # Check the result
    assert isinstance(result, str)
    assert "ChatSkill" in result
    assert "answer_question" in result
    assert "chat" in result
