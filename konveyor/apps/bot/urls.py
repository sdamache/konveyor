"""
URL configuration for the bot app.

This module contains URL patterns for the bot app, including the Slack webhook endpoint.
"""

import logging
from django.urls import path
from django.http import HttpResponse
from . import views

logger = logging.getLogger(__name__)

# Add a debug view to log all requests
def debug_view(request):
    logger.info(f"DEBUG VIEW: Received request to {request.path} with method {request.method}")
    logger.info(f"DEBUG VIEW: Headers: {request.headers}")
    try:
        body = request.body.decode('utf-8')
        logger.info(f"DEBUG VIEW: Request body: {body[:1000]}...")
    except Exception as e:
        logger.error(f"DEBUG VIEW: Error decoding request body: {str(e)}")

    return HttpResponse("Debug view - request logged")

app_name = 'bot'

urlpatterns = [
    path('', views.root_handler, name='root'),
    path('slack/events/', views.slack_webhook, name='slack_webhook'),
    path('debug/', debug_view, name='debug_view'),
]
