import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from konveyor.core.rag.context_service import ContextService
from konveyor.core.azure_utils.storage import AzureStorageManager

@pytest.fixture
async def context_service():
    storage_manager = AsyncMock(spec=AzureStorageManager)
    search_client = AsyncMock()
    openai_client = AsyncMock()
    service = ContextService(storage_manager, search_client, openai_client)
    return service

@pytest.mark.asyncio
async def test_retrieve_context_kubernetes_scenario(context_service):
    """Test context retrieval for Kubernetes-related queries"""
    # Mock embedding generation
    context_service.openai_client.embeddings.create.return_value = {
        "data": [{"embedding": [0.1] * 1536}]  # Typical embedding dimension
    }
    
    # Mock search results for Kubernetes docs
    context_service.search_client.search.return_value = {
        "value": [
            {
                "id": "k8s_pod_doc",
                "content": "A Pod is the smallest deployable unit in Kubernetes...",
                "source": "kubernetes/docs/concepts/workloads/pods/pod-overview.md",
                "score": 0.95
            },
            {
                "id": "k8s_deployment_doc",
                "content": "A Deployment provides declarative updates for Pods and ReplicaSets...",
                "source": "kubernetes/docs/concepts/workloads/controllers/deployment.md",
                "score": 0.85
            }
        ]
    }

    query = "How do Kubernetes pods and deployments work together?"
    results = await context_service.retrieve_context(query)
    
    assert len(results) == 2
    assert "pod" in results[0]["content"].lower()
    assert "deployment" in results[1]["content"].lower()
    assert all(r["score"] >= 0.7 for r in results)

@pytest.mark.asyncio
async def test_retrieve_context_linux_scenario(context_service):
    """Test context retrieval for Linux kernel-related queries"""
    context_service.openai_client.embeddings.create.return_value = {
        "data": [{"embedding": [0.1] * 1536}]
    }
    
    context_service.search_client.search.return_value = {
        "value": [
            {
                "id": "linux_syscall_doc",
                "content": "System calls are the fundamental interface between an application and the Linux kernel...",
                "source": "linux/Documentation/admin-guide/syscalls.rst",
                "score": 0.92
            },
            {
                "id": "linux_process_doc",
                "content": "Process management in Linux involves creating, scheduling, and terminating processes...",
                "source": "linux/Documentation/admin-guide/pm/process.rst",
                "score": 0.88
            }
        ]
    }

    query = "How does Linux handle system calls and process management?"
    results = await context_service.retrieve_context(query)
    
    assert len(results) == 2
    assert "system calls" in results[0]["content"].lower()
    assert "process" in results[1]["content"].lower()
    assert all(r["score"] >= 0.7 for r in results)

@pytest.mark.asyncio
async def test_retrieve_context_hybrid_scenario(context_service):
    """Test context retrieval for queries involving both Linux and Kubernetes"""
    context_service.openai_client.embeddings.create.return_value = {
        "data": [{"embedding": [0.1] * 1536}]
    }
    
    context_service.search_client.search.return_value = {
        "value": [
            {
                "id": "k8s_linux_doc",
                "content": "Container runtime in Kubernetes interacts with Linux kernel namespaces and cgroups...",
                "source": "kubernetes/docs/concepts/containers/runtime.md",
                "score": 0.94
            },
            {
                "id": "linux_container_doc",
                "content": "Linux containers use kernel features like namespaces and cgroups for isolation...",
                "source": "linux/Documentation/admin-guide/containers.rst",
                "score": 0.91
            }
        ]
    }

    query = "How do Kubernetes containers use Linux kernel features?"
    results = await context_service.retrieve_context(query)
    
    assert len(results) == 2
    assert "kubernetes" in results[0]["content"].lower()
    assert "linux" in results[1]["content"].lower()
    assert all("container" in r["content"].lower() for r in results)
    assert all(r["score"] >= 0.7 for r in results)
