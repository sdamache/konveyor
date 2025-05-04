import os
import ssl
import time

import certifi
import pytest
from dotenv import load_dotenv
from slack_sdk import WebClient

load_dotenv()


# Integration test for real Slack Bot via ngrok
@pytest.mark.integration
def test_slack_e2e():
    # Load environment
    ngrok_url = os.getenv("NGROK_URL")
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    signing_secret = os.getenv("SLACK_SIGNING_SECRET")
    channel_id = os.getenv("SLACK_TEST_CHANNEL_ID")

    # Ensure env vars are set
    assert ngrok_url, "NGROK_URL must be set"
    assert bot_token, "SLACK_BOT_TOKEN must be set"
    assert signing_secret, "SLACK_SIGNING_SECRET must be set"
    assert channel_id, "SLACK_TEST_CHANNEL_ID must be set"

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    client = WebClient(token=bot_token, ssl=ssl_context)
    test_text = f"Integration test at {int(time.time())}"

    # Post message to trigger bot
    post = client.chat_postMessage(channel=channel_id, text=test_text)
    assert post.get("ok"), f"Failed to post message: {post}"

    # Poll for bot response
    timeout = 30
    interval = 5
    start = time.time()
    while time.time() - start < timeout:
        history = client.conversations_history(channel=channel_id, limit=10)
        messages = history.get("messages", [])
        for msg in messages:
            text = msg.get("text", "")
            # Skip our own test message
            if test_text in text:
                continue
            # Check for bot reply prefix
            if text.startswith("You said:"):
                return
        time.sleep(interval)
    pytest.fail("Bot response not found in channel history")
