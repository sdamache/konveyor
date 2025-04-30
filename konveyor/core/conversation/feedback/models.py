"""
Feedback models for Konveyor.

This module defines the interfaces and abstract types for feedback storage and retrieval.
It does NOT contain actual Django models - those are defined in konveyor/apps/bot/models.py.

The separation between this module and the Django models allows for:
1. Clear separation of concerns between interface and implementation
2. Testing the feedback service without Django dependencies
3. Potential alternative implementations (e.g., using Azure Table Storage)

This follows the repository pattern, where:
- This module defines the interface (FeedbackStorageProvider)
- Concrete implementations (like DjangoFeedbackRepository) implement this interface
- The service layer (FeedbackService) depends on the interface, not the implementation
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class FeedbackType(str, Enum):
    """Enum for feedback types."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    REMOVED = "removed"


class FeedbackStorageProvider:
    """
    Interface for feedback storage providers.

    This class defines the interface that all feedback storage providers must implement.
    Concrete implementations can use different storage backends (e.g., database, file system).
    """

    def store_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store feedback data.

        Args:
            feedback_data: The feedback data to store

        Returns:
            The stored feedback data with any additional fields
        """
        raise NotImplementedError("Subclasses must implement store_feedback")

    def update_feedback_content(self, update_data: Dict[str, Any]) -> bool:
        """
        Update the content of feedback entries.

        Args:
            update_data: The data to update

        Returns:
            True if the update was successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement update_feedback_content")

    def get_feedback_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get feedback statistics for the specified time period.

        Args:
            days: Number of days to include in the statistics

        Returns:
            Dictionary containing feedback statistics
        """
        raise NotImplementedError("Subclasses must implement get_feedback_stats")

    def get_feedback_by_skill(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get feedback statistics grouped by skill.

        Args:
            days: Number of days to include in the statistics

        Returns:
            List of dictionaries containing feedback statistics by skill
        """
        raise NotImplementedError("Subclasses must implement get_feedback_by_skill")

    def get_feedback_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get raw feedback data for the specified time period.

        Args:
            days: Number of days to include in the data

        Returns:
            List of feedback data entries
        """
        raise NotImplementedError("Subclasses must implement get_feedback_data")
