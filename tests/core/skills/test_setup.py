import os  # noqa: F401
import traceback

import pytest
from semantic_kernel import Kernel

from konveyor.core.azure_utils.config import AzureConfig
from konveyor.core.kernel import create_kernel

config = AzureConfig()


@pytest.mark.integration()
@pytest.mark.skipif(
    not config.get_setting("AZURE_OPENAI_ENDPOINT")
    or not config.get_setting("AZURE_OPENAI_API_KEY"),
    reason="Azure OpenAI environment not configured",
)
@pytest.mark.asyncio()
async def test_create_kernel_services_real():
    """
    Robust integration test for Semantic Kernel with Azure OpenAI.
    Prints and checks all relevant config, catches and logs exceptions, and asserts on config presence.  # noqa: E501
    """
    endpoint = config.get_endpoint("OPENAI")
    api_key = config.get_key("OPENAI")
    deployment = config.get_setting("AZURE_OPENAI_CHAT_DEPLOYMENT")
    api_version = config.get_setting("AZURE_OPENAI_API_VERSION")

    # Mask API key for logging
    masked_api_key = (  # noqa: F841
        api_key[:4] + "..." + api_key[-4:]
        if api_key and len(api_key) > 8
        else "(not set)"
    )
    print("DEBUG: endpoint =", endpoint)
    print("DEBUG: deployment =", deployment)
    print("DEBUG: api_version =", api_version)
    print("DEBUG: api_key (first 5 chars) =", api_key[:5])

    assert endpoint, "AZURE_OPENAI_ENDPOINT is not set!"
    assert api_key, "AZURE_OPENAI_API_KEY is not set!"
    assert deployment, "AZURE_OPENAI_CHAT_DEPLOYMENT is not set!"
    assert api_version, "AZURE_OPENAI_API_VERSION is not set!"

    kernel = create_kernel()
    assert isinstance(kernel, Kernel)

    # Verify chat AI service is registered
    chat = kernel.get_service("chat")
    assert chat is not None

    # Verify volatile memory store is registered
    mem_store = kernel.get_service("volatile")
    assert mem_store is not None

    # Test a real prompt using ChatCompletionAgent (recommended SK API)
    from semantic_kernel.agents import ChatCompletionAgent

    try:
        agent = ChatCompletionAgent(
            kernel=kernel,
            name="TestAgent",
            instructions="Answer as an assistant.",
        )
        response = await agent.get_response(messages="Hello, world!")
        print(f"[DEBUG] Agent response: {response}")
        assert hasattr(response, "name") and hasattr(response, "thread")
        assert isinstance(str(response), str) and str(response)
    except Exception as e:
        print("\n[ERROR] Exception during agent chat invocation:")
        traceback.print_exc()
        pytest.fail(f"Agent chat invocation failed: {e}")
