"""
Factory for creating feedback service instances.

This module provides a factory for creating feedback service instances
with the appropriate storage provider. It follows the factory pattern
to abstract the creation of complex objects and their dependencies.
"""

import logging
from typing import Optional

from django.conf import settings

from konveyor.core.conversation.feedback.django_feedback_repository import (
    DjangoFeedbackRepository,
)
from konveyor.core.conversation.feedback.service import FeedbackService

logger = logging.getLogger(__name__)


def create_feedback_service() -> FeedbackService:
    """
    Create a feedback service instance with the appropriate storage provider.

    This factory method creates a FeedbackService instance with the appropriate
    storage provider based on the current environment. It handles the creation
    of the repository and any necessary configuration.

    Returns:
        A configured FeedbackService instance
    """
    # Create the Django feedback repository
    try:
        repository = DjangoFeedbackRepository()
        logger.info("Created Django feedback repository")
    except Exception as e:
        logger.error(f"Error creating Django feedback repository: {str(e)}")
        repository = None

    # Create the feedback service with the repository
    service = FeedbackService(storage_provider=repository)
    logger.info("Created feedback service")

    return service
