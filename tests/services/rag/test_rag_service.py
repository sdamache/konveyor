from unittest.mock import AsyncMock

import pytest

from konveyor.core.azure_utils.clients import AzureClientManager
from konveyor.core.rag.context_service import ContextService
from konveyor.core.rag.rag_service import RAGService


@pytest.fixture
async def rag_service():
    context_service = AsyncMock(spec=ContextService)
    storage_manager = AsyncMock(spec=AzureClientManager)
    openai_client = AsyncMock()
    service = RAGService(context_service, storage_manager, openai_client)
    return service


@pytest.mark.asyncio
async def test_generate_response_kubernetes_concepts(rag_service):
    """Test response generation for Kubernetes conceptual questions"""
    # Mock context retrieval
    rag_service.context_service.retrieve_context.return_value = [
        {
            "content": "A Pod is the smallest deployable unit in Kubernetes that can be created and managed.",
            "source": "kubernetes/docs/concepts/workloads/pods/pod-overview.md",
            "score": 0.95,
        }
    ]

    # Mock OpenAI response
    rag_service.openai_client.chat.completions.create.return_value = AsyncMock(
        choices=[
            AsyncMock(
                message=AsyncMock(
                    content="A Pod in Kubernetes is the smallest deployable unit..."
                )
            )
        ]
    )

    query = "What is a Kubernetes Pod?"
    response = await rag_service.generate_response(query)

    assert "pod" in response["answer"].lower()
    assert "kubernetes" in response["answer"].lower()
    assert response["sources"][0]["source"].endswith("pod-overview.md")


@pytest.mark.asyncio
async def test_generate_response_linux_kernel(rag_service):
    """Test response generation for Linux kernel questions"""
    rag_service.context_service.retrieve_context.return_value = [
        {
            "content": "System calls are the fundamental interface between applications and the Linux kernel.",
            "source": "linux/Documentation/admin-guide/syscalls.rst",
            "score": 0.92,
        }
    ]

    rag_service.openai_client.chat.completions.create.return_value = AsyncMock(
        choices=[
            AsyncMock(message=AsyncMock(content="System calls in Linux provide..."))
        ]
    )

    query = "How do Linux system calls work?"
    response = await rag_service.generate_response(query)

    assert "system calls" in response["answer"].lower()
    assert "linux" in response["answer"].lower()
    assert response["sources"][0]["source"].endswith("syscalls.rst")


@pytest.mark.asyncio
async def test_generate_response_with_code_examples(rag_service):
    """Test response generation with code examples"""
    rag_service.context_service.retrieve_context.return_value = [
        {
            "content": "```yaml\napiVersion: v1\nkind: Pod\nmetadata:\n  name: example\nspec:\n  containers:\n  - name: web\n    image: nginx\n```",
            "source": "kubernetes/docs/concepts/workloads/pods/pod-yaml.md",
            "score": 0.90,
        }
    ]

    rag_service.openai_client.chat.completions.create.return_value = AsyncMock(
        choices=[
            AsyncMock(
                message=AsyncMock(
                    content="Here's an example of a Pod YAML:\n```yaml\napiVersion: v1..."
                )
            )
        ]
    )

    query = "Show me an example Kubernetes Pod YAML"
    response = await rag_service.generate_response(query, template_type="code")

    assert "```yaml" in response["answer"]
    assert "kind: Pod" in response["answer"]
    assert response["sources"][0]["source"].endswith("pod-yaml.md")


@pytest.mark.asyncio
async def test_generate_response_with_multiple_sources(rag_service):
    """Test response generation combining multiple documentation sources"""
    rag_service.context_service.retrieve_context.return_value = [
        {
            "content": "Container runtime interfaces with Linux kernel namespaces...",
            "source": "kubernetes/docs/concepts/containers/runtime.md",
            "score": 0.94,
        },
        {
            "content": "Linux namespaces provide isolation for running processes...",
            "source": "linux/Documentation/admin-guide/namespaces.rst",
            "score": 0.91,
        },
    ]

    rag_service.openai_client.chat.completions.create.return_value = AsyncMock(
        choices=[
            AsyncMock(
                message=AsyncMock(
                    content="Kubernetes containers use Linux namespaces for isolation..."
                )
            )
        ]
    )

    query = "How do Kubernetes containers use Linux namespaces?"
    response = await rag_service.generate_response(query)

    assert len(response["sources"]) == 2
    assert any("kubernetes" in s["source"] for s in response["sources"])
    assert any("linux" in s["source"] for s in response["sources"])
    assert "namespaces" in response["answer"].lower()
