#!/usr/bin/env python
"""
Test script to simulate a Slack reaction event.

This script sends a simulated Slack reaction event to the webhook endpoint
to test the feedback mechanism.
"""

import json
import requests
import sys
import time

# Slack event for a reaction_added event
reaction_event = {
    "token": "verification_token",
    "team_id": "T123456",
    "api_app_id": "A123456",
    "event": {
        "type": "reaction_added",
        "user": "U123456",
        "reaction": "thumbsdown",
        "item": {
            "type": "message",
            "channel": "C123456",
            "ts": "1234567890.123460"  # Use a new timestamp for a new feedback entry
        },
        "event_ts": "1234567890.123456"
    },
    "type": "event_callback",
    "event_id": "Ev123457",
    "event_time": 1234567890
}

# URL for the Slack webhook endpoint
webhook_url = "http://localhost:8000/api/bot/slack/events/"

# Send the event to the webhook
print(f"Sending reaction_added event to {webhook_url}...")
response = requests.post(
    webhook_url,
    headers={"Content-Type": "application/json"},
    data=json.dumps(reaction_event)
)

# Print the response
print(f"Response status code: {response.status_code}")
print(f"Response body: {response.text}")

# Wait a moment for the server to process the event
time.sleep(1)

# Check if the feedback was recorded
print("\nChecking if feedback was recorded...")
stats_response = requests.get("http://localhost:8000/api/bot/feedback/stats/")
print(f"Stats response: {stats_response.json()}")

# Check feedback by skill
skill_response = requests.get("http://localhost:8000/api/bot/feedback/by-skill/")
print(f"Skill response: {skill_response.json()}")

# Export feedback data
export_response = requests.get("http://localhost:8000/api/bot/feedback/export/")
print(f"Export response: {export_response.json()}")
