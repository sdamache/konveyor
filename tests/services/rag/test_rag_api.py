import pytest
import pytest_asyncio
from django.test import AsyncClient


@pytest_asyncio.fixture
async def api_client():
    """Async HTTP client for testing Django async views"""
    return AsyncClient()


@pytest.mark.integration()
@pytest.mark.asyncio()
async def test_create_conversation(api_client):
    """Test creating a new conversation via API"""
    response = await api_client.post("/api/rag/conversations/")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data, f"Unexpected response payload: {data}"


@pytest.mark.integration()
@pytest.mark.asyncio()
async def test_ask_and_history(api_client):
    """Test asking a question and retrieving conversation history"""
    # Create conversation
    create_resp = await api_client.post("/api/rag/conversations/")
    conv_id = create_resp.json().get("id")
    assert conv_id, "Conversation ID not returned"

    # Ask a question
    ask_resp = await api_client.post(
        f"/api/rag/conversations/{conv_id}/ask/",
        {"query": "What is a Pod?"},
        content_type="application/json",
    )
    assert ask_resp.status_code == 200, f"Ask failed: {ask_resp.content}"
    ask_data = ask_resp.json()
    assert "response" in ask_data and ask_data.get("conversation_id") == conv_id

    # Retrieve history
    hist_resp = await api_client.get(f"/api/rag/conversations/{conv_id}/history/")
    assert hist_resp.status_code == 200, f"History failed: {hist_resp.content}"
    messages = hist_resp.json()
    assert isinstance(messages, list)
    assert any(m.get("content") == "What is a Pod?" for m in messages)
