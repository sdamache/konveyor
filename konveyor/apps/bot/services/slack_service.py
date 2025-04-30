"""
Slack Service for Konveyor.

This module provides a proxy import for the SlackService class,
which has been moved to konveyor.core.slack.client.
"""

import logging

from konveyor.core.slack.client import SlackService, retry_on_slack_error

# Configure logging
logger = logging.getLogger(__name__)
logger.info("Using SlackService from konveyor.core.slack.client")
