"""
URL configuration for the bot app.

This module contains URL patterns for the bot app, including the Slack webhook endpoint.
"""

from django.urls import path
from . import views

app_name = 'bot'

urlpatterns = [
    path('', views.root_handler, name='root'),
    path('slack/events/', views.slack_webhook, name='slack_webhook'),
]
