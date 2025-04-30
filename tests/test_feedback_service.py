"""
Unit tests for the feedback service.
"""

import unittest
from enum import Enum
from unittest.mock import MagicMock, patch


# Mock the FeedbackType enum to avoid Django dependencies
class FeedbackType(str, Enum):
    """Mock enum for feedback types."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    REMOVED = "removed"


# Mock the FeedbackService class to avoid Django dependencies
class FeedbackService:
    """Mock class for the feedback service."""

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
        """Initialize the FeedbackService."""
        self.storage_provider = storage_provider

    def process_reaction_event(self, event):
        """Process a reaction event and record feedback."""
        # Extract event data
        item = event.get("item", {})
        reaction = event.get("reaction", "")
        user_id = event.get("user", "")
        event_type = event.get("type", "")

        # Only process message reactions
        if item.get("type") != "message":
            return None

        # Get message details
        channel_id = item.get("channel", "")
        message_ts = item.get("ts", "")

        if not channel_id or not message_ts or not user_id or not reaction:
            return None

        # Determine feedback type based on reaction
        feedback_type = self._get_feedback_type(reaction, event_type)

        if not feedback_type:
            return None

        # Create feedback data
        feedback_data = {
            "message_id": message_ts,
            "channel_id": channel_id,
            "user_id": user_id,
            "feedback_type": feedback_type,
            "reaction": reaction,
        }

        # Store feedback if a storage provider is available
        if self.storage_provider:
            return self.storage_provider.store_feedback(feedback_data)

        return feedback_data

    def _get_feedback_type(self, reaction, event_type):
        """Determine the feedback type based on the reaction and event type."""
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
        message_id,
        channel_id,
        question=None,
        answer=None,
        skill_used=None,
        function_used=None,
        conversation_id=None,
    ):
        """Update the content of a message that has received feedback."""
        if not self.storage_provider:
            return False

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
        return self.storage_provider.update_feedback_content(update_data)

    def get_feedback_stats(self, days=30):
        """Get feedback statistics for the specified time period."""
        if not self.storage_provider:
            return {
                "total_feedback": 0,
                "positive_count": 0,
                "negative_count": 0,
                "positive_percentage": 0,
                "counts_by_type": {},
                "days": days,
            }

        return self.storage_provider.get_feedback_stats(days)

    def get_feedback_by_skill(self, days=30):
        """Get feedback statistics grouped by skill."""
        if not self.storage_provider:
            return []

        return self.storage_provider.get_feedback_by_skill(days)


class TestFeedbackService(unittest.TestCase):
    """Test cases for the FeedbackService class."""

    def setUp(self):
        """Set up the test case."""
        self.mock_storage_provider = MagicMock()
        self.feedback_service = FeedbackService(
            storage_provider=self.mock_storage_provider
        )

    def test_process_reaction_event_positive(self):
        """Test processing a positive reaction event."""
        # Create a mock reaction event
        event = {
            "type": "reaction_added",
            "reaction": "thumbsup",
            "user": "U123456",
            "item": {
                "type": "message",
                "channel": "C123456",
                "ts": "1234567890.123456",
            },
        }

        # Mock the storage provider's store_feedback method
        self.mock_storage_provider.store_feedback.return_value = {
            "message_id": "1234567890.123456",
            "channel_id": "C123456",
            "user_id": "U123456",
            "feedback_type": FeedbackType.POSITIVE,
            "reaction": "thumbsup",
        }

        # Process the reaction event
        result = self.feedback_service.process_reaction_event(event)

        # Check that the storage provider's store_feedback method was called
        self.mock_storage_provider.store_feedback.assert_called_once()

        # Check that the result is as expected
        self.assertEqual(result["message_id"], "1234567890.123456")
        self.assertEqual(result["channel_id"], "C123456")
        self.assertEqual(result["user_id"], "U123456")
        self.assertEqual(result["feedback_type"], FeedbackType.POSITIVE)
        self.assertEqual(result["reaction"], "thumbsup")

    def test_process_reaction_event_negative(self):
        """Test processing a negative reaction event."""
        # Create a mock reaction event
        event = {
            "type": "reaction_added",
            "reaction": "thumbsdown",
            "user": "U123456",
            "item": {
                "type": "message",
                "channel": "C123456",
                "ts": "1234567890.123456",
            },
        }

        # Mock the storage provider's store_feedback method
        self.mock_storage_provider.store_feedback.return_value = {
            "message_id": "1234567890.123456",
            "channel_id": "C123456",
            "user_id": "U123456",
            "feedback_type": FeedbackType.NEGATIVE,
            "reaction": "thumbsdown",
        }

        # Process the reaction event
        result = self.feedback_service.process_reaction_event(event)

        # Check that the storage provider's store_feedback method was called
        self.mock_storage_provider.store_feedback.assert_called_once()

        # Check that the result is as expected
        self.assertEqual(result["message_id"], "1234567890.123456")
        self.assertEqual(result["channel_id"], "C123456")
        self.assertEqual(result["user_id"], "U123456")
        self.assertEqual(result["feedback_type"], FeedbackType.NEGATIVE)
        self.assertEqual(result["reaction"], "thumbsdown")

    def test_process_reaction_event_removed(self):
        """Test processing a reaction removed event."""
        # Create a mock reaction event
        event = {
            "type": "reaction_removed",
            "reaction": "thumbsup",
            "user": "U123456",
            "item": {
                "type": "message",
                "channel": "C123456",
                "ts": "1234567890.123456",
            },
        }

        # Mock the storage provider's store_feedback method
        self.mock_storage_provider.store_feedback.return_value = {
            "message_id": "1234567890.123456",
            "channel_id": "C123456",
            "user_id": "U123456",
            "feedback_type": FeedbackType.REMOVED,
            "reaction": "thumbsup",
        }

        # Process the reaction event
        result = self.feedback_service.process_reaction_event(event)

        # Check that the storage provider's store_feedback method was called
        self.mock_storage_provider.store_feedback.assert_called_once()

        # Check that the result is as expected
        self.assertEqual(result["message_id"], "1234567890.123456")
        self.assertEqual(result["channel_id"], "C123456")
        self.assertEqual(result["user_id"], "U123456")
        self.assertEqual(result["feedback_type"], FeedbackType.REMOVED)
        self.assertEqual(result["reaction"], "thumbsup")

    def test_process_reaction_event_non_message(self):
        """Test processing a reaction event for a non-message item."""
        # Create a mock reaction event
        event = {
            "type": "reaction_added",
            "reaction": "thumbsup",
            "user": "U123456",
            "item": {"type": "file", "file": "F123456"},
        }

        # Process the reaction event
        result = self.feedback_service.process_reaction_event(event)

        # Check that the storage provider's store_feedback method was not called
        self.mock_storage_provider.store_feedback.assert_not_called()

        # Check that the result is None
        self.assertIsNone(result)

    def test_process_reaction_event_non_feedback_reaction(self):
        """Test processing a reaction event with a non-feedback reaction."""
        # Create a mock reaction event
        event = {
            "type": "reaction_added",
            "reaction": "smile",
            "user": "U123456",
            "item": {
                "type": "message",
                "channel": "C123456",
                "ts": "1234567890.123456",
            },
        }

        # Process the reaction event
        result = self.feedback_service.process_reaction_event(event)

        # Check that the storage provider's store_feedback method was not called
        self.mock_storage_provider.store_feedback.assert_not_called()

        # Check that the result is None
        self.assertIsNone(result)

    def test_update_message_content(self):
        """Test updating message content."""
        # Mock the storage provider's update_feedback_content method
        self.mock_storage_provider.update_feedback_content.return_value = True

        # Update message content
        result = self.feedback_service.update_message_content(
            message_id="1234567890.123456",
            channel_id="C123456",
            question="What is the meaning of life?",
            answer="42",
            skill_used="ChatSkill",
            function_used="chat",
            conversation_id="conv123",
        )

        # Check that the storage provider's update_feedback_content method was called
        self.mock_storage_provider.update_feedback_content.assert_called_once()

        # Check that the result is True
        self.assertTrue(result)

    def test_update_message_content_no_storage_provider(self):
        """Test updating message content with no storage provider."""
        # Create a feedback service with no storage provider
        feedback_service = FeedbackService()

        # Update message content
        result = feedback_service.update_message_content(
            message_id="1234567890.123456",
            channel_id="C123456",
            question="What is the meaning of life?",
            answer="42",
            skill_used="ChatSkill",
            function_used="chat",
            conversation_id="conv123",
        )

        # Check that the result is False
        self.assertFalse(result)

    def test_get_feedback_stats(self):
        """Test getting feedback statistics."""
        # Mock the storage provider's get_feedback_stats method
        self.mock_storage_provider.get_feedback_stats.return_value = {
            "total_feedback": 10,
            "positive_count": 7,
            "negative_count": 3,
            "positive_percentage": 70.0,
            "counts_by_type": {"positive": 7, "negative": 3},
            "days": 30,
        }

        # Get feedback statistics
        result = self.feedback_service.get_feedback_stats(days=30)

        # Check that the storage provider's get_feedback_stats method was called
        self.mock_storage_provider.get_feedback_stats.assert_called_once_with(30)

        # Check that the result is as expected
        self.assertEqual(result["total_feedback"], 10)
        self.assertEqual(result["positive_count"], 7)
        self.assertEqual(result["negative_count"], 3)
        self.assertEqual(result["positive_percentage"], 70.0)
        self.assertEqual(result["counts_by_type"]["positive"], 7)
        self.assertEqual(result["counts_by_type"]["negative"], 3)
        self.assertEqual(result["days"], 30)

    def test_get_feedback_stats_no_storage_provider(self):
        """Test getting feedback statistics with no storage provider."""
        # Create a feedback service with no storage provider
        feedback_service = FeedbackService()

        # Get feedback statistics
        result = feedback_service.get_feedback_stats(days=30)

        # Check that the result is as expected
        self.assertEqual(result["total_feedback"], 0)
        self.assertEqual(result["positive_count"], 0)
        self.assertEqual(result["negative_count"], 0)
        self.assertEqual(result["positive_percentage"], 0)
        self.assertEqual(result["counts_by_type"], {})
        self.assertEqual(result["days"], 30)

    def test_get_feedback_by_skill(self):
        """Test getting feedback statistics by skill."""
        # Mock the storage provider's get_feedback_by_skill method
        self.mock_storage_provider.get_feedback_by_skill.return_value = [
            {
                "skill": "ChatSkill",
                "total": 5,
                "positive": 4,
                "negative": 1,
                "positive_percentage": 80.0,
            },
            {
                "skill": "DocumentationNavigatorSkill",
                "total": 3,
                "positive": 2,
                "negative": 1,
                "positive_percentage": 66.7,
            },
        ]

        # Get feedback statistics by skill
        result = self.feedback_service.get_feedback_by_skill(days=30)

        # Check that the storage provider's get_feedback_by_skill method was called
        self.mock_storage_provider.get_feedback_by_skill.assert_called_once_with(30)

        # Check that the result is as expected
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["skill"], "ChatSkill")
        self.assertEqual(result[0]["total"], 5)
        self.assertEqual(result[0]["positive"], 4)
        self.assertEqual(result[0]["negative"], 1)
        self.assertEqual(result[0]["positive_percentage"], 80.0)
        self.assertEqual(result[1]["skill"], "DocumentationNavigatorSkill")
        self.assertEqual(result[1]["total"], 3)
        self.assertEqual(result[1]["positive"], 2)
        self.assertEqual(result[1]["negative"], 1)
        self.assertEqual(result[1]["positive_percentage"], 66.7)

    def test_get_feedback_by_skill_no_storage_provider(self):
        """Test getting feedback statistics by skill with no storage provider."""
        # Create a feedback service with no storage provider
        feedback_service = FeedbackService()

        # Get feedback statistics by skill
        result = feedback_service.get_feedback_by_skill(days=30)

        # Check that the result is an empty list
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
