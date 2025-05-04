"""
URL configuration for the bot app.

This module contains URL patterns for the bot app, including the Slack webhook endpoint.
"""

import logging

from django.http import HttpResponse
from django.urls import path

from . import views, views_feedback

logger = logging.getLogger(__name__)


# Add a debug view to log all requests
def debug_view(request):
    logger.info(
        f"DEBUG VIEW: Received request to {request.path} with method {request.method}"
    )
    logger.info(f"DEBUG VIEW: Headers: {request.headers}")
    try:
        body = request.body.decode("utf-8")
        logger.info(f"DEBUG VIEW: Request body: {body[:1000]}...")
    except Exception as e:
        logger.error(f"DEBUG VIEW: Error decoding request body: {str(e)}")

    return HttpResponse("Debug view - request logged")


app_name = "bot"

urlpatterns = [
    path("", views.root_handler, name="root"),
    path("slack/events/", views.slack_webhook, name="slack_webhook"),
    path("slack/commands/", views.slack_slash_command, name="slack_slash_command"),
    path("debug/", debug_view, name="debug_view"),
    # Feedback API endpoints
    path(
        "feedback/stats/", views_feedback.feedback_stats_api, name="feedback_stats_api"
    ),
    path(
        "feedback/by-skill/",
        views_feedback.feedback_by_skill_api,
        name="feedback_by_skill_api",
    ),
    path(
        "feedback/export/",
        views_feedback.export_feedback_api,
        name="feedback_export_api",
    ),
]
