"""
Feedback Service for Konveyor.

This service handles user feedback on bot responses, including
recording reactions, analyzing feedback patterns, and generating reports.

This service follows the dependency inversion principle by depending on
the FeedbackStorageProvider interface rather than concrete implementations.
This allows for different storage mechanisms to be used without changing
the service logic.

The service is designed to work with the existing conversation storage
mechanisms in konveyor/core/conversation/storage.py and memory.py, but
uses a dedicated storage provider for feedback data to maintain separation
of concerns.

TODO: Feedback System Enhancements
- Implement Azure AI Search integration for feedback storage (Task 8.1)
  - Index all feedback content in Azure AI Search
  - Enable semantic search across feedback content
  - Implement advanced analytics on feedback patterns

- Enhance feedback correlation and analysis (Task 8.2)
  - Link feedback with user profiles and conversation history
  - Track feedback patterns by user or conversation type
  - Provide personalized improvements based on individual feedback

- Implement feedback lifecycle management (Task 8.3)
  - Add archiving/summarization of older feedback
  - Implement categorization/tagging for better organization
  - Create feedback review workflows for team analysis

- Add real-time feedback analytics (Task 8.4)
  - Create real-time dashboards for monitoring trends
  - Implement alerts for negative feedback patterns
  - Provide immediate insights to improve bot responses
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Enum for feedback types."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    REMOVED = "removed"


class FeedbackService:
    """
    Service for handling user feedback on bot responses.

    This service provides methods for recording feedback from reactions,
    retrieving feedback statistics, and analyzing feedback patterns.
    """

    # Map of reaction emojis to feedback types
    POSITIVE_REACTIONS = [
        "thumbsup",
        "+1",
        "thumbs_up",
        "clap",
        "raised_hands",
        "heart",
    ]
    NEGATIVE_REACTIONS = ["thumbsdown", "-1", "thumbs_down", "x", "no_entry"]

    def __init__(self, storage_provider=None):
        """
        Initialize the FeedbackService.

        Args:
            storage_provider: Optional storage provider for feedback data
        """
        self.storage_provider = storage_provider
        logger.info("Initialized FeedbackService")

    def process_reaction_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a reaction event and record feedback.

        Args:
            event: The reaction event data

        Returns:
            The recorded feedback data, or None if the event was not processed
        """
        # Extract event data
        item = event.get("item", {})
        reaction = event.get("reaction", "")
        user_id = event.get("user", "")
        event_type = event.get("type", "")  # 'reaction_added' or 'reaction_removed'

        # Only process message reactions
        if item.get("type") != "message":
            logger.debug(f"Ignoring non-message reaction: {reaction}")
            return None

        # Get message details
        channel_id = item.get("channel", "")
        message_ts = item.get("ts", "")

        if not channel_id or not message_ts or not user_id or not reaction:
            logger.warning("Missing required data in reaction event")
            return None

        # Determine feedback type based on reaction
        feedback_type = self._get_feedback_type(reaction, event_type)

        if not feedback_type:
            logger.debug(
                f"Ignoring reaction that is not mapped to feedback: {reaction}"
            )
            return None

        logger.info(
            f"Processing {feedback_type} feedback from user {user_id} on message {message_ts}"
        )

        # Create feedback data
        feedback_data = {
            "message_id": message_ts,
            "channel_id": channel_id,
            "user_id": user_id,
            "feedback_type": feedback_type,
            "reaction": reaction,
            "timestamp": datetime.now().isoformat(),
        }

        # Store feedback if a storage provider is available
        if self.storage_provider:
            try:
                result = self.storage_provider.store_feedback(feedback_data)
                logger.info(f"Stored feedback: {result}")
                return result
            except Exception as e:
                logger.error(f"Error storing feedback: {str(e)}")
                return feedback_data

        return feedback_data

    def _get_feedback_type(self, reaction: str, event_type: str) -> Optional[str]:
        """
        Determine the feedback type based on the reaction and event type.

        Args:
            reaction: The reaction emoji
            event_type: The event type ('reaction_added' or 'reaction_removed')

        Returns:
            The feedback type ('positive', 'negative', 'neutral', 'removed'), or None if not applicable
        """
        # Handle reaction removal
        if event_type == "reaction_removed":
            return FeedbackType.REMOVED

        # Check if this is a positive reaction
        if reaction in self.POSITIVE_REACTIONS:
            return FeedbackType.POSITIVE

        # Check if this is a negative reaction
        if reaction in self.NEGATIVE_REACTIONS:
            return FeedbackType.NEGATIVE

        # Not a feedback reaction
        return None

    def update_message_content(
        self,
        message_id: str,
        channel_id: str,
        question: str = None,
        answer: str = None,
        skill_used: str = None,
        function_used: str = None,
        conversation_id: str = None,
    ) -> bool:
        """
        Update the content of a message that has received feedback.

        This is used to retroactively add the question and answer content
        to feedback entries when they become available.

        Args:
            message_id: The message ID
            channel_id: The channel ID
            question: The original user question
            answer: The bot's answer
            skill_used: The skill that generated the answer
            function_used: The function that generated the answer
            conversation_id: The conversation ID

        Returns:
            True if the update was successful, False otherwise
        """
        if not self.storage_provider:
            logger.warning("No storage provider available for updating message content")
            return False

        try:
            # Create update data
            update_data = {"message_id": message_id, "channel_id": channel_id}

            # Add optional fields
            if question is not None:
                update_data["question"] = question
            if answer is not None:
                update_data["answer"] = answer
            if skill_used is not None:
                update_data["skill_used"] = skill_used
            if function_used is not None:
                update_data["function_used"] = function_used
            if conversation_id is not None:
                update_data["conversation_id"] = conversation_id

            # Update the feedback entries
            result = self.storage_provider.update_feedback_content(update_data)
            logger.info(f"Updated message content for feedback: {message_id}")
            return result
        except Exception as e:
            logger.error(f"Error updating message content: {str(e)}")
            return False

    def get_feedback_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get feedback statistics for the specified time period.

        Args:
            days: Number of days to include in the statistics

        Returns:
            Dictionary containing feedback statistics
        """
        if not self.storage_provider:
            logger.warning("No storage provider available for getting feedback stats")
            return {
                "total_feedback": 0,
                "positive_count": 0,
                "negative_count": 0,
                "positive_percentage": 0,
                "counts_by_type": {},
                "days": days,
            }

        try:
            return self.storage_provider.get_feedback_stats(days)
        except Exception as e:
            logger.error(f"Error getting feedback stats: {str(e)}")
            return {
                "total_feedback": 0,
                "positive_count": 0,
                "negative_count": 0,
                "positive_percentage": 0,
                "counts_by_type": {},
                "days": days,
                "error": str(e),
            }

    def get_feedback_by_skill(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get feedback statistics grouped by skill.

        Args:
            days: Number of days to include in the statistics

        Returns:
            List of dictionaries containing feedback statistics by skill
        """
        if not self.storage_provider:
            logger.warning(
                "No storage provider available for getting feedback by skill"
            )
            return []

        try:
            return self.storage_provider.get_feedback_by_skill(days)
        except Exception as e:
            logger.error(f"Error getting feedback by skill: {str(e)}")
            return []

    def export_feedback_data(self, days: int = 30, format: str = "json") -> str:
        """
        Export feedback data in the specified format.

        Args:
            days: Number of days to include in the export
            format: Export format ('json' or 'csv')

        Returns:
            Exported data as a string
        """
        if not self.storage_provider:
            logger.warning("No storage provider available for exporting feedback data")
            return ""

        try:
            data = self.storage_provider.get_feedback_data(days)

            if format.lower() == "json":
                return json.dumps(data, indent=2)
            elif format.lower() == "csv":
                # Simple CSV conversion
                if not data:
                    return "No data available"

                # Get headers from the first item
                headers = list(data[0].keys())
                csv_lines = [",".join(headers)]

                # Add data rows
                for item in data:
                    row = [str(item.get(header, "")) for header in headers]
                    csv_lines.append(",".join(row))

                return "\n".join(csv_lines)
            else:
                logger.error(f"Unsupported export format: {format}")
                return ""
        except Exception as e:
            logger.error(f"Error exporting feedback data: {str(e)}")
            return ""
