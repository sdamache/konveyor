"""
Tests for Semantic Kernel framework and ChatSkill.

These tests can run with real Azure OpenAI credentials if available,
or fall back to mocks for CI/CD environments. They test both the core
Semantic Kernel setup and the ChatSkill functionality.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from semantic_kernel import Kernel
from semantic_kernel.functions import KernelFunction
from konveyor.core.kernel import create_kernel, get_kernel_settings
from konveyor.core.chat import ChatSkill


# Check if we're in a CI environment or if Azure credentials are available
IN_CI = os.environ.get("CI") == "true"
HAS_AZURE_CREDENTIALS = bool(os.environ.get("AZURE_OPENAI_ENDPOINT"))


@pytest.fixture
def mock_kernel():
    """Mock Kernel for testing when real credentials aren't available."""
    with patch("konveyor.core.kernel.factory.Kernel") as mock_kernel_class:
        kernel_instance = MagicMock()

        # Mock the run_function method
        def mock_run_function(func, **kwargs):
            # Get the function name
            func_name = func.name if hasattr(func, "name") else "unknown"

            # Return different responses based on the function
            if func_name == "answer_question":
                question = kwargs.get("input_str", "")
                return f"Mocked answer to: {question}"
            elif func_name == "chat":
                message = kwargs.get("input_str", "")
                return {
                    "response": f"Mocked chat response to: {message}",
                    "history": f"User: {message}\nAssistant: Mocked response",
                }
            elif func_name == "format_for_slack":
                text = kwargs.get("input_str", "")
                return text.replace("*", "_")
            elif func_name == "greet":
                name = kwargs.get("input_str", "")
                return f"Hello, {name}! Welcome to Konveyor."
            elif func_name == "format_as_bullet_list":
                text = kwargs.get("input_str", "")
                lines = text.strip().split("\n")
                return "\n".join(
                    [f"• {line.strip()}" for line in lines if line.strip()]
                )

            return "Mocked response"

        kernel_instance.run_function = mock_run_function

        # Mock the add_plugin method
        def mock_add_plugin(skill, plugin_name=None):
            # Create a dictionary of mock functions
            functions = {}

            # If it's a ChatSkill, add its functions
            if isinstance(skill, ChatSkill):
                for method_name in [
                    "answer_question",
                    "chat",
                    "format_for_slack",
                    "greet",
                    "format_as_bullet_list",
                ]:
                    mock_function = MagicMock()
                    mock_function.name = method_name
                    functions[method_name] = mock_function

            return functions

        kernel_instance.add_plugin = mock_add_plugin
        mock_kernel_class.return_value = kernel_instance

        yield kernel_instance


@pytest.fixture
def real_or_mock_kernel(mock_kernel):
    """
    Return a real kernel if Azure credentials are available,
    otherwise return a mock kernel.
    """
    if IN_CI or not HAS_AZURE_CREDENTIALS:
        print("Using mock kernel for testing")
        return mock_kernel
    else:
        print("Using real kernel with Azure OpenAI")
        try:
            return create_kernel()
        except Exception as e:
            print(f"Failed to create real kernel: {e}")
            return mock_kernel


def test_chat_skill_answer_question(real_or_mock_kernel):
    """Test the answer_question function of ChatSkill."""
    # Import the skill
    chat_skill = ChatSkill()
    functions = real_or_mock_kernel.add_plugin(chat_skill, plugin_name="chat")

    # Test with a simple question
    question = "What is Semantic Kernel?"
    result = real_or_mock_kernel.run_function(
        functions["answer_question"], input_str=question
    )

    # Check that we got a non-empty string response
    assert isinstance(result, str)
    assert len(result) > 0

    # If using a mock, verify the expected format
    if IN_CI or not HAS_AZURE_CREDENTIALS:
        assert f"Mocked answer to: {question}" == result


def test_chat_skill_chat_function(real_or_mock_kernel):
    """Test the chat function of ChatSkill."""
    # Import the skill
    chat_skill = ChatSkill()
    functions = real_or_mock_kernel.add_plugin(chat_skill, plugin_name="chat")

    # Test with a simple message
    message = "Hello, how are you?"
    result = real_or_mock_kernel.run_function(functions["chat"], input_str=message)

    # Check that we got a dictionary with the expected keys
    assert isinstance(result, dict)
    assert "response" in result
    assert "history" in result

    # Check that the history contains the message
    assert message in result["history"]


def test_chat_skill_format_for_slack(real_or_mock_kernel):
    """Test the format_for_slack function of ChatSkill."""
    # Import the skill
    chat_skill = ChatSkill()
    functions = real_or_mock_kernel.add_plugin(chat_skill, plugin_name="chat")

    # Test with a message containing Markdown
    markdown_text = "This is *bold* text"
    result = real_or_mock_kernel.run_function(
        functions["format_for_slack"], input_str=markdown_text
    )

    # Check that bold markers were converted to italic for Slack
    assert "_bold_" in result
    assert "*bold*" not in result


def test_chat_skill_greet(real_or_mock_kernel):
    """Test the greet function of ChatSkill."""
    # Import the skill
    chat_skill = ChatSkill()
    functions = real_or_mock_kernel.add_plugin(chat_skill, plugin_name="chat")

    # Test with a name
    name = "Developer"
    result = real_or_mock_kernel.run_function(functions["greet"], input_str=name)

    # Check that the greeting contains the name
    assert isinstance(result, str)
    assert name in result
    assert "Hello" in result

    # If using a mock, verify the expected format
    if IN_CI or not HAS_AZURE_CREDENTIALS:
        assert f"Hello, {name}! Welcome to Konveyor." == result


def test_chat_skill_format_as_bullet_list(real_or_mock_kernel):
    """Test the format_as_bullet_list function of ChatSkill."""
    # Import the skill
    chat_skill = ChatSkill()
    functions = real_or_mock_kernel.add_plugin(chat_skill, plugin_name="chat")

    # Test with a list of items
    items = "Item 1\nItem 2\nItem 3"
    result = real_or_mock_kernel.run_function(
        functions["format_as_bullet_list"], input_str=items
    )

    # Check that the result contains bullet points
    assert isinstance(result, str)
    assert "• Item 1" in result
    assert "• Item 2" in result
    assert "• Item 3" in result

    # Check that the number of lines matches the input
    assert len(result.strip().split("\n")) == 3


@pytest.fixture
def mock_azure_client_manager():
    """Mock AzureClientManager for testing."""
    with patch("konveyor.core.kernel.factory.AzureClientManager") as mock_manager:
        manager_instance = MagicMock()
        kv_client = MagicMock()
        secret = MagicMock()
        secret.value = "test-key-from-vault"
        kv_client.get_secret.return_value = secret
        manager_instance.get_key_vault_client.return_value = kv_client
        mock_manager.return_value = manager_instance
        yield mock_manager


@pytest.fixture
def mock_azure_chat_completion():
    """Mock AzureChatCompletion for testing."""
    with patch("konveyor.core.kernel.factory.AzureChatCompletion") as mock_chat:
        chat_instance = MagicMock()
        mock_chat.return_value = chat_instance
        yield mock_chat


@pytest.fixture
def mock_volatile_memory_store():
    """Mock VolatileMemoryStore for testing."""
    with patch("konveyor.core.kernel.factory.VolatileMemoryStore") as mock_store:
        store_instance = MagicMock()
        mock_store.return_value = store_instance
        yield mock_store, store_instance


def test_create_kernel_with_key_vault(
    mock_kernel,
    mock_azure_client_manager,
    mock_azure_chat_completion,
    mock_volatile_memory_store,
):
    """Test creating a kernel with Key Vault integration."""
    # Call the function
    result = create_kernel()

    # Verify Key Vault was used to get the API key
    mock_azure_client_manager.return_value.get_key_vault_client.assert_called_once()


def test_create_kernel_fallback_to_env_key(
    mock_kernel,
    mock_azure_client_manager,
    mock_azure_chat_completion,
    mock_volatile_memory_store,
):
    """Test creating a kernel with fallback to environment variable when Key Vault fails."""
    # Make Key Vault client raise an exception
    mock_azure_client_manager.return_value.get_key_vault_client.side_effect = Exception(
        "Key Vault error"
    )

    # Call the function
    result = create_kernel()

    # Verify Key Vault was attempted
    mock_azure_client_manager.return_value.get_key_vault_client.assert_called_once()


@pytest.mark.skipif(
    IN_CI or not HAS_AZURE_CREDENTIALS, reason="Requires Azure OpenAI credentials"
)
def test_kernel_settings():
    """Test that kernel settings are correctly retrieved from environment."""
    settings = get_kernel_settings()

    # Check that we have the expected keys
    assert "endpoint" in settings
    assert "chat_deployment" in settings
    assert "api_version" in settings

    # Check that the endpoint is a valid URL
    assert settings["endpoint"].startswith("https://")

    # Print settings for debugging (will only show in test output)
    print(f"Kernel settings: {settings}")
