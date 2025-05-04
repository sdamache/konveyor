"""
Feedback module for Konveyor.

This module provides functionality for collecting, storing, and analyzing
user feedback on bot responses. It follows a layered architecture with:

1. Service layer (FeedbackService) - Contains business logic
2. Repository layer (FeedbackStorageProvider) - Defines storage interface
3. Implementation layer (DjangoFeedbackRepository) - Implements storage using Django

The module is designed to be extensible, allowing for different storage
implementations while maintaining a consistent API.
"""

from konveyor.core.conversation.feedback.django_feedback_repository import (
    DjangoFeedbackRepository,
)
from konveyor.core.conversation.feedback.factory import create_feedback_service
from konveyor.core.conversation.feedback.models import (
    FeedbackStorageProvider,
    FeedbackType,
)
from konveyor.core.conversation.feedback.service import FeedbackService

__all__ = [
    "FeedbackService",
    "FeedbackType",
    "FeedbackStorageProvider",
    "DjangoFeedbackRepository",
    "create_feedback_service",
]
