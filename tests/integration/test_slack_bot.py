import pytest
from aiohttp import web

from konveyor.apps.bot.app import ADAPTER, APP, messages


class DummyResponse:
    def __init__(self, body=None, status=200):
        self.body = body
        self.status = status


async def dummy_process_activity(activity, auth_header, handler):
    # Simulate BotFrameworkAdapter.process_activity returning a bot reply
    return DummyResponse(body={"type": "message", "text": "Hello"}, status=200)


@pytest.mark.asyncio
async def test_slack_messages_returns_200(monkeypatch):
    # Monkeypatch the Adapter to avoid real processing
    monkeypatch.setattr(ADAPTER, "process_activity", dummy_process_activity)

    # Create a dummy request with valid JSON header
    class DummyRequest:
        def __init__(self):
            self.headers = {"Content-Type": "application/json"}

        async def json(self):
            return {"type": "message", "text": "Hi"}

    req = DummyRequest()
    resp = await messages(req)
    # Should return HTTP 200
    assert resp.status == 200


@pytest.fixture
async def client(aiohttp_client):
    """A test client for the Bot HTTP endpoint."""
    return await aiohttp_client(APP)


@pytest.mark.asyncio
async def test_slack_http_returns_200(client, monkeypatch):
    # Monkeypatch the Adapter.process_activity
    monkeypatch.setattr(ADAPTER, "process_activity", dummy_process_activity)
    headers = {"Content-Type": "application/json"}
    payload = {"type": "message", "text": "Hello via HTTP"}
    resp = await client.post("/api/messages", json=payload, headers=headers)
    assert resp.status == 200
