import os
import time

import pytest
import pytest_asyncio

from konveyor.core.azure_utils.clients import AzureClientManager
from konveyor.core.rag.context_service import ContextService


@pytest.fixture(scope="session")
def client_manager():
    """
    Provides a real AzureClientManager for integration testing.
    Ensures required environment variables are set.
    """
    os.environ.setdefault(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"),
    )
    os.environ.setdefault(
        "AZURE_OPENAI_API_VERSION",
        os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    )
    return AzureClientManager()


@pytest_asyncio.fixture
async def context_service(client_manager):
    """Instantiate ContextService with real Azure clients"""
    return ContextService(client_manager)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_retrieve_context_integration(context_service, client_manager):
    """
    Indexes a test document and retrieves it via ContextService.retrieve_context
    to validate real vector search functionality.
    """
    # Prepare test document
    content = "Integration test document content for RAG context"
    openai_client = client_manager.get_openai_client()
    # Generate embedding for document
    embedding_resp = await openai_client.embeddings.create(
        model=client_manager.config.openai_embedding_deployment, input=content
    )
    vector = embedding_resp.data[0].embedding

    # Index document in cognitive search
    _, search_client = client_manager.get_search_clients("konveyor-documents")
    doc_id = "test_context_doc"
    document = {
        "id": doc_id,
        "content": content,
        "content_vector": vector,
        "source": "test_context.md",
        "page_number": 1,
        "metadata": {"file_type": "md", "chunk_index": 0},
    }
    await search_client.upload_documents([document])
    # Allow time for indexing commit
    time.sleep(2)

    # Retrieve context via service
    results = await context_service.retrieve_context(content)
    # Verify that our test document is returned
    assert any(
        r["content"] == content for r in results
    ), f"Expected document content in results: {results}"
    assert all(r["relevance_score"] >= 0.3 for r in results)

    # Cleanup: delete test document from index
    await search_client.delete_documents([{"id": doc_id}])


def test_format_context():
    """
    Unit test for ContextService.format_context without external dependencies.
    """
    cs = ContextService(AzureClientManager())
    chunks = [
        {
            "content": "Sample context text",
            "source": "sample.md",
            "page": 2,
            "relevance_score": 0.5,
            "metadata": {"file_type": "md"},
        }
    ]
    formatted = cs.format_context(chunks)
    assert "Sample context text" in formatted
    # Check citation formatting
    assert "[Source: sample.md, Page 2, Type: md, Relevance: 0.50]" in formatted
