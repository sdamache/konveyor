"""
Mock tests for Agent Orchestrator Skill.

These tests verify the functionality of the Agent Orchestrator Skill using mocked dependencies,  # noqa: E501
including request routing, skill selection, and error handling.

This file uses unittest.mock to mock the Semantic Kernel and its dependencies,
allowing tests to run without requiring real Azure OpenAI credentials.
"""

import logging  # noqa: F401
from unittest.mock import AsyncMock, MagicMock, patch  # noqa: F401

import pytest
from semantic_kernel import Kernel

from konveyor.core.agent import AgentOrchestratorSkill, SkillRegistry
from konveyor.core.chat import ChatSkill


@pytest.fixture()
def mock_kernel():
    """Mock Kernel for testing."""
    kernel = MagicMock(spec=Kernel)
    kernel.plugins = {}

    # Mock the invoke method
    async def mock_invoke(function, **kwargs):
        # Return different responses based on the function name
        if hasattr(function, "name"):
            if function.name == "answer_question":
                return f"Answer to: {kwargs.get('question', '')}"
            elif function.name == "chat":
                return {
                    "response": f"Chat response to: {kwargs.get('message', '')}",
                    "history": f"User: {kwargs.get('message', '')}\nAssistant: Chat response",  # noqa: E501
                }
            elif function.name == "greet":
                return f"Hello, {kwargs.get('name', 'there')}!"
            elif function.name == "format_as_bullet_list":
                text = kwargs.get("text", "")
                lines = text.strip().split("\n")
                return "\n".join(
                    [f"• {line.strip()}" for line in lines if line.strip()]
                )

        return "Mock response"

    kernel.invoke = AsyncMock(side_effect=mock_invoke)

    # Mock the add_plugin method
    def mock_add_plugin(skill, plugin_name=None):
        # Create a dictionary of mock functions
        functions = {}

        # If it's a ChatSkill, add its functions
        if isinstance(skill, ChatSkill):
            for method_name in [
                "answer_question",
                "chat",
                "greet",
                "format_as_bullet_list",
            ]:
                mock_function = MagicMock()
                mock_function.name = method_name
                functions[method_name] = mock_function

        # Store in the plugins dictionary
        if plugin_name:
            kernel.plugins[plugin_name] = functions

        return functions

    kernel.add_plugin = mock_add_plugin

    return kernel


@pytest.fixture()
def registry():
    """Create a SkillRegistry for testing."""
    return SkillRegistry()


@pytest.fixture()
def chat_skill():
    """Create a ChatSkill for testing."""
    return ChatSkill()


@pytest.fixture()
def orchestrator(mock_kernel, registry, chat_skill):
    """Create an AgentOrchestratorSkill for testing."""
    orchestrator = AgentOrchestratorSkill(mock_kernel, registry)
    orchestrator.register_skill(
        chat_skill,
        "ChatSkill",
        "Handles general chat interactions and questions",
        ["chat", "question", "answer", "help"],
    )
    return orchestrator


@pytest.mark.asyncio()
async def test_process_request_with_chat(orchestrator, mock_kernel):
    """Test processing a chat request."""
    # Process a chat request
    request = "Hello, how are you today?"
    result = await orchestrator.process_request(request)

    # Check the result
    assert isinstance(result, dict)
    assert "response" in result
    # The response could be either format depending on the mock implementation
    assert (
        "Chat response to: Hello, how are you today?" in result["response"]
        or "Hello" in result["response"]
    )
    assert result["skill_name"] == "ChatSkill"
    assert result["function_name"] in [
        "chat",
        "greet",
    ]  # Could be either depending on the implementation
    assert result["success"] is True


@pytest.mark.asyncio()
async def test_process_request_with_question(orchestrator, mock_kernel):
    """Test processing a question request."""
    # Process a question request
    request = "What is Semantic Kernel?"
    result = await orchestrator.process_request(request)

    # Check the result
    assert isinstance(result, dict)
    assert "response" in result
    assert "Answer to: What is Semantic Kernel?" in result["response"]
    assert result["skill_name"] == "ChatSkill"
    assert result["function_name"] == "answer_question"
    assert result["success"] is True


@pytest.mark.asyncio()
async def test_process_request_with_greeting(orchestrator, mock_kernel):
    """Test processing a greeting request."""
    # Process a greeting request
    request = "Hello John"
    result = await orchestrator.process_request(request)

    # Check the result
    assert isinstance(result, dict)
    assert "response" in result
    assert "Hello, John!" in result["response"]
    assert result["skill_name"] == "ChatSkill"
    assert result["function_name"] == "greet"
    assert result["success"] is True


@pytest.mark.asyncio()
async def test_process_request_with_formatting(orchestrator, mock_kernel):
    """Test processing a formatting request."""
    # Process a formatting request
    request = "Please format this as a bullet list: Item 1, Item 2, Item 3"
    result = await orchestrator.process_request(request)

    # Check the result
    assert isinstance(result, dict)
    assert "response" in result
    assert "•" in result["response"]
    assert result["skill_name"] == "ChatSkill"
    assert result["function_name"] == "format_as_bullet_list"
    assert result["success"] is True


@pytest.mark.asyncio()
async def test_process_request_with_empty_request(orchestrator):
    """Test processing an empty request."""
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


@pytest.mark.asyncio()
async def test_process_request_with_error(orchestrator, mock_kernel):
    """Test processing a request that causes an error."""
    # Make the kernel.invoke method raise an exception
    mock_kernel.invoke.side_effect = Exception("Test error")

    # Process a request
    request = "Hello, how are you today?"
    result = await orchestrator.process_request(request)

    # Check the result
    assert isinstance(result, dict)
    assert "response" in result
    assert "error" in result
    assert "Test error" in result["error"]
    assert result["skill_name"] == "AgentOrchestratorSkill"
    assert result["function_name"] == "process_request"
    assert result["success"] is False


def test_register_skill(orchestrator, registry):
    """Test registering a skill."""

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


def test_get_available_skills(orchestrator, registry, chat_skill):
    """Test getting information about available skills."""
    # Get available skills
    result = orchestrator.get_available_skills()

    # Check the result
    assert isinstance(result, str)
    assert "ChatSkill" in result
    assert "answer_question" in result
    assert "chat" in result
    assert "greet" in result
    assert "format_as_bullet_list" in result


def test_find_skills_by_keywords(registry):
    """Test finding skills by keywords."""

    # Register a test skill
    class TestSkill:
        def test_function(self):
            return "Test result"

    skill = TestSkill()
    registry.register_skill(
        skill, "TestSkill", "A test skill for testing", ["test", "example", "demo"]
    )

    # Find skills by keywords
    matches = registry.find_skills_by_keywords("test example")

    # Check the result
    assert "TestSkill" in matches

    # Find skills by partial match
    matches = registry.find_skills_by_keywords("testing demo")

    # Check the result
    assert "TestSkill" in matches
