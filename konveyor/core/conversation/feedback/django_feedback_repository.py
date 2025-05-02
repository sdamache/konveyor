"""
Django implementation of the feedback storage provider.

This module provides a Django-based implementation of the feedback storage provider
that uses Django models for storage and retrieval. It serves as a data access layer
between the feedback service and the Django ORM.

This repository pattern separates the data access logic from the business logic,
making the code more maintainable and testable.

This implementation leverages the existing conversation storage mechanisms in
konveyor/core/conversation/storage.py and memory.py for metadata storage,
while using Django models for the primary feedback data.

TODO: Repository Enhancements
- Create AzureFeedbackRepository implementation (Task 8.1)
  - Implement Azure AI Search indexing for feedback content
  - Add fallback mechanism for when Azure is unavailable
  - Create migration tools for existing feedback data

- Optimize database queries for better performance (Technical Debt)
  - Add caching for frequently accessed feedback data
  - Implement batch processing for high-volume feedback

- Enhance error handling and logging (Short-Term)
  - Improve error recovery mechanisms
  - Add more detailed logging for debugging
  - Implement retry logic for transient failures
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

from django.db.models import Count, Q
from django.utils import timezone

from konveyor.apps.bot.models import BotFeedback
from konveyor.core.conversation.factory import ConversationManagerFactory
from konveyor.core.conversation.feedback.models import (
    FeedbackStorageProvider,
    FeedbackType,
)

logger = logging.getLogger(__name__)


class DjangoFeedbackRepository(FeedbackStorageProvider):
    """
    Django implementation of the feedback storage provider.

    This class uses Django models to store and retrieve feedback data.
    It implements the FeedbackStorageProvider interface, allowing the
    feedback service to work with Django models without direct dependencies.

    Additionally, it leverages the existing conversation storage mechanisms
    for storing metadata and linking feedback to conversations.
    """

    def __init__(self):
        """Initialize the repository with conversation storage."""
        # Initialize the conversation manager for metadata storage
        self.conversation_manager = None
        self._init_conversation_manager()

    def _init_conversation_manager(self):
        """Initialize the conversation manager asynchronously."""
        try:
            # Create a task to initialize the conversation manager
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.conversation_manager = loop.run_until_complete(
                ConversationManagerFactory.create_manager()
            )
            loop.close()
            logger.info("Initialized conversation manager for feedback repository")
        except Exception as e:
            logger.error(f"Error initializing conversation manager: {str(e)}")
            self.conversation_manager = None

    def store_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store feedback data using Django models and conversation storage.

        This method stores the primary feedback data in the Django database
        and additional metadata in the conversation storage if available.

        Args:
            feedback_data: The feedback data to store

        Returns:
            The stored feedback data with any additional fields
        """
        # Extract data from the feedback_data dictionary
        message_id = feedback_data.get("message_id")
        channel_id = feedback_data.get("channel_id")
        user_id = feedback_data.get("user_id")
        feedback_type = feedback_data.get("feedback_type")
        reaction = feedback_data.get("reaction")
        question = feedback_data.get("question")
        answer = feedback_data.get("answer")
        skill_used = feedback_data.get("skill_used")
        function_used = feedback_data.get("function_used")
        conversation_id = feedback_data.get("conversation_id")
        timestamp = feedback_data.get("timestamp")

        # First, check for pending feedback entries for this message
        try:
            pending_entries = BotFeedback.objects.filter(
                slack_message_ts=message_id, slack_user_id="pending", reaction="pending"
            )

            # If pending entries exist, get their content
            if pending_entries.exists():
                pending_entry = pending_entries.first()
                # Get content from pending entry if not provided
                question = question or pending_entry.question
                answer = answer or pending_entry.answer
                skill_used = skill_used or pending_entry.skill_used
                function_used = function_used or pending_entry.function_used
                conversation_id = conversation_id or pending_entry.conversation_id

                # Delete the pending entry
                pending_entry.delete()
                logger.info(
                    f"Used content from pending feedback entry for message {message_id}"
                )
        except Exception as e:
            logger.error(f"Error checking for pending feedback entries: {str(e)}")

        # Try to find an existing feedback entry
        try:
            feedback = BotFeedback.objects.get(
                slack_message_ts=message_id, slack_user_id=user_id, reaction=reaction
            )
            # Update the existing feedback
            feedback.feedback_type = feedback_type
            feedback.feedback_timestamp = timezone.now()

            # Update content if available
            if question is not None:
                feedback.question = question
            if answer is not None:
                feedback.answer = answer
            if skill_used is not None:
                feedback.skill_used = skill_used
            if function_used is not None:
                feedback.function_used = function_used
            if conversation_id is not None:
                feedback.conversation_id = conversation_id

            feedback.save()
            logger.info(f"Updated existing feedback: {feedback}")
        except BotFeedback.DoesNotExist:
            # Create a new feedback entry
            feedback = BotFeedback.objects.create(
                slack_message_ts=message_id,
                slack_channel_id=channel_id,
                slack_user_id=user_id,
                feedback_type=feedback_type,
                reaction=reaction,
                question=question,
                answer=answer,
                skill_used=skill_used,
                function_used=function_used,
                conversation_id=conversation_id,
            )
            logger.info(f"Created new feedback: {feedback}")

        # Store additional metadata in conversation storage if available
        if self.conversation_manager and conversation_id:
            try:
                # Store feedback metadata in the conversation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def store_feedback_metadata():
                    # Update conversation metadata with feedback information
                    await self.conversation_manager.update_conversation_metadata(
                        conversation_id=conversation_id,
                        metadata={
                            f"feedback_{message_id}": {
                                "type": feedback_type,
                                "reaction": reaction,
                                "timestamp": timestamp or datetime.now().isoformat(),
                                "user_id": user_id,
                            }
                        },
                    )
                    logger.debug(
                        f"Stored feedback metadata in conversation {conversation_id}"
                    )

                loop.run_until_complete(store_feedback_metadata())
                loop.close()
            except Exception as e:
                logger.error(
                    f"Error storing feedback metadata in conversation: {str(e)}"
                )

        # Convert the model instance to a dictionary
        return {
            "id": feedback.id,
            "message_id": feedback.slack_message_ts,
            "channel_id": feedback.slack_channel_id,
            "user_id": feedback.slack_user_id,
            "feedback_type": feedback.feedback_type,
            "reaction": feedback.reaction,
            "question": feedback.question,
            "answer": feedback.answer,
            "skill_used": feedback.skill_used,
            "function_used": feedback.function_used,
            "conversation_id": feedback.conversation_id,
            "timestamp": (
                feedback.feedback_timestamp.isoformat()
                if feedback.feedback_timestamp
                else None
            ),
        }

    def update_feedback_content(self, update_data: Dict[str, Any]) -> bool:
        """
        Update the content of feedback entries in both Django and conversation storage.

        If no feedback entries exist yet, this method will store the content in a
        temporary "pending feedback" entry that can be used when feedback is received later.

        Args:
            update_data: The data to update

        Returns:
            True if the update was successful, False otherwise
        """
        # Extract data from the update_data dictionary
        message_id = update_data.get("message_id")
        channel_id = update_data.get("channel_id")
        conversation_id = update_data.get("conversation_id")

        if not message_id or not channel_id:
            logger.warning("Missing required fields for updating feedback content")
            return False

        success = False

        # Update Django models
        try:
            # Find all feedback entries for this message
            feedback_entries = BotFeedback.objects.filter(
                slack_message_ts=message_id, slack_channel_id=channel_id
            )

            # Prepare update fields
            update_fields = {}
            if "question" in update_data:
                update_fields["question"] = update_data["question"]
            if "answer" in update_data:
                update_fields["answer"] = update_data["answer"]
            if "skill_used" in update_data:
                update_fields["skill_used"] = update_data["skill_used"]
            if "function_used" in update_data:
                update_fields["function_used"] = update_data["function_used"]
            if "conversation_id" in update_data:
                update_fields["conversation_id"] = update_data["conversation_id"]

            if not feedback_entries.exists():
                logger.debug(
                    f"No feedback entries found for message {message_id}, creating pending entry"
                )

                # Create a "pending feedback" entry with neutral type
                # This will be updated when actual feedback is received
                try:
                    pending_feedback = BotFeedback(
                        slack_message_ts=message_id,
                        slack_channel_id=channel_id,
                        slack_user_id="pending",  # Placeholder user ID
                        feedback_type="neutral",  # Neutral type for pending entries
                        reaction="pending",  # Placeholder reaction
                    )

                    # Add the content fields
                    for field, value in update_fields.items():
                        setattr(pending_feedback, field, value)

                    # Save the pending entry
                    pending_feedback.save()
                    logger.info(
                        f"Created pending feedback entry for message {message_id}"
                    )
                    success = True
                except Exception as e:
                    logger.error(f"Error creating pending feedback entry: {str(e)}")
            else:
                # Update existing entries
                if update_fields:
                    feedback_entries.update(**update_fields)
                    logger.info(
                        f"Updated {feedback_entries.count()} feedback entries for message {message_id}"
                    )
                    success = True
                else:
                    logger.debug("No fields to update in Django models")
        except Exception as e:
            logger.error(f"Error updating feedback content in Django models: {str(e)}")

        # Update conversation storage if available
        if self.conversation_manager and conversation_id:
            try:
                # Create metadata for the conversation storage
                metadata_update = {}

                # Only include fields that are present in the update_data
                if "question" in update_data:
                    metadata_update["question"] = update_data["question"]
                if "answer" in update_data:
                    metadata_update["answer"] = update_data["answer"]
                if "skill_used" in update_data:
                    metadata_update["skill_used"] = update_data["skill_used"]
                if "function_used" in update_data:
                    metadata_update["function_used"] = update_data["function_used"]

                if metadata_update:
                    # Store feedback metadata in the conversation
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    async def update_feedback_metadata():
                        # Get existing metadata
                        conversation = (
                            await self.conversation_manager.get_user_conversations(
                                user_id=None,  # We're using conversation_id directly
                                limit=1,
                            )
                        )

                        if conversation and len(conversation) > 0:
                            # Update the feedback metadata
                            existing_metadata = conversation[0].get("metadata", {})
                            feedback_key = f"feedback_{message_id}"

                            if feedback_key in existing_metadata:
                                # Update existing feedback metadata
                                existing_metadata[feedback_key].update(metadata_update)
                            else:
                                # Create new feedback metadata
                                existing_metadata[feedback_key] = metadata_update

                            # Save the updated metadata
                            await self.conversation_manager.update_conversation_metadata(
                                conversation_id=conversation_id,
                                metadata=existing_metadata,
                            )
                            logger.debug(
                                f"Updated feedback metadata in conversation {conversation_id}"
                            )
                            return True
                        return False

                    metadata_success = loop.run_until_complete(
                        update_feedback_metadata()
                    )
                    loop.close()

                    # If Django update failed but conversation update succeeded, mark as success
                    if metadata_success:
                        success = True
                else:
                    logger.debug("No fields to update in conversation metadata")
            except Exception as e:
                logger.error(
                    f"Error updating feedback metadata in conversation: {str(e)}"
                )

        return success

    def get_feedback_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get feedback statistics for the specified time period.

        This method combines feedback data from both Django models and
        conversation storage to provide comprehensive statistics.

        Args:
            days: Number of days to include in the statistics

        Returns:
            Dictionary containing feedback statistics
        """
        # Calculate the start date
        start_date = timezone.now() - timezone.timedelta(days=days)

        # Initialize stats dictionary
        stats = {
            "total_feedback": 0,
            "positive_count": 0,
            "negative_count": 0,
            "positive_percentage": 0,
            "counts_by_type": {},
            "days": days,
            "sources": {"django": True, "conversation_storage": False},
        }

        # Get stats from Django models
        try:
            # Get feedback counts by type
            feedback_counts = (
                BotFeedback.objects.filter(feedback_timestamp__gte=start_date)
                .values("feedback_type")
                .annotate(count=Count("id"))
            )

            # Convert to a dictionary
            counts_by_type = {
                item["feedback_type"]: item["count"] for item in feedback_counts
            }

            # Calculate totals
            total_feedback = sum(counts_by_type.values())
            positive_count = counts_by_type.get(FeedbackType.POSITIVE, 0)
            negative_count = counts_by_type.get(FeedbackType.NEGATIVE, 0)

            # Calculate positive percentage
            positive_percentage = 0
            if total_feedback > 0:
                positive_percentage = (positive_count / total_feedback) * 100

            # Update stats
            stats.update(
                {
                    "total_feedback": total_feedback,
                    "positive_count": positive_count,
                    "negative_count": negative_count,
                    "positive_percentage": positive_percentage,
                    "counts_by_type": counts_by_type,
                }
            )
        except Exception as e:
            logger.error(f"Error getting feedback stats from Django models: {str(e)}")
            stats["sources"]["django"] = False

        # Get additional stats from conversation storage if available
        if self.conversation_manager:
            try:
                # Create a task to get conversation feedback
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def get_conversation_feedback():
                    # Check if the conversation manager has the required method
                    if not hasattr(self.conversation_manager, "get_all_conversations"):
                        logger.warning(
                            "Conversation manager does not support get_all_conversations method"
                        )
                        return []

                    try:
                        # Get recent conversations
                        conversations = (
                            await self.conversation_manager.get_all_conversations(
                                limit=100
                            )
                        )

                        # Extract feedback from conversation metadata
                        conversation_feedback = []
                        for conversation in conversations:
                            metadata = conversation.get("metadata", {})
                            # Look for feedback entries in metadata
                            for key, value in metadata.items():
                                if key.startswith("feedback_"):
                                    # Check if the feedback is within the time range
                                    timestamp = value.get("timestamp")
                                    if timestamp:
                                        try:
                                            feedback_date = datetime.fromisoformat(
                                                timestamp
                                            )
                                            if feedback_date >= start_date:
                                                conversation_feedback.append(value)
                                        except (ValueError, TypeError):
                                            # Skip entries with invalid timestamps
                                            pass

                        return conversation_feedback
                    except Exception as e:
                        logger.error(f"Error retrieving conversations: {str(e)}")
                        return []

                # Get feedback from conversations
                conversation_feedback = loop.run_until_complete(
                    get_conversation_feedback()
                )
                loop.close()

                if conversation_feedback:
                    # Mark conversation storage as a source
                    stats["sources"]["conversation_storage"] = True

                    # Count feedback by type
                    conv_counts_by_type = {}
                    for feedback in conversation_feedback:
                        feedback_type = feedback.get("type")
                        if feedback_type:
                            conv_counts_by_type[feedback_type] = (
                                conv_counts_by_type.get(feedback_type, 0) + 1
                            )

                    # Add conversation feedback to stats
                    for feedback_type, count in conv_counts_by_type.items():
                        # Update counts_by_type
                        stats["counts_by_type"][feedback_type] = (
                            stats["counts_by_type"].get(feedback_type, 0) + count
                        )

                        # Update specific counters
                        if feedback_type == FeedbackType.POSITIVE:
                            stats["positive_count"] += count
                        elif feedback_type == FeedbackType.NEGATIVE:
                            stats["negative_count"] += count

                    # Recalculate totals
                    stats["total_feedback"] = sum(stats["counts_by_type"].values())

                    # Recalculate positive percentage
                    if stats["total_feedback"] > 0:
                        stats["positive_percentage"] = (
                            stats["positive_count"] / stats["total_feedback"]
                        ) * 100
            except Exception as e:
                logger.error(
                    f"Error getting feedback stats from conversation storage: {str(e)}"
                )

        return stats

    def get_feedback_by_skill(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get feedback statistics grouped by skill.

        This method combines feedback data from both Django models and
        conversation storage to provide comprehensive statistics by skill.

        Args:
            days: Number of days to include in the statistics

        Returns:
            List of dictionaries containing feedback statistics by skill
        """
        # Calculate the start date
        start_date = timezone.now() - timezone.timedelta(days=days)

        # Initialize result dictionary to store combined stats
        skill_stats = {}

        # Get stats from Django models
        try:
            # Get feedback counts by skill and type
            skill_feedback = (
                BotFeedback.objects.filter(
                    feedback_timestamp__gte=start_date, skill_used__isnull=False
                )
                .values("skill_used")
                .annotate(
                    total=Count("id"),
                    positive=Count("id", filter=Q(feedback_type=FeedbackType.POSITIVE)),
                    negative=Count("id", filter=Q(feedback_type=FeedbackType.NEGATIVE)),
                )
            )

            # Add to combined stats
            for item in skill_feedback:
                skill_name = item["skill_used"]
                if skill_name not in skill_stats:
                    skill_stats[skill_name] = {
                        "skill": skill_name,
                        "total": 0,
                        "positive": 0,
                        "negative": 0,
                        "sources": ["django"],
                    }

                # Update stats
                skill_stats[skill_name]["total"] += item["total"]
                skill_stats[skill_name]["positive"] += item["positive"]
                skill_stats[skill_name]["negative"] += item["negative"]
        except Exception as e:
            logger.error(
                f"Error getting feedback by skill from Django models: {str(e)}"
            )

        # Get additional stats from conversation storage if available
        if self.conversation_manager:
            try:
                # Create a task to get conversation feedback
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def get_conversation_feedback_by_skill():
                    # Check if the conversation manager has the required method
                    if not hasattr(self.conversation_manager, "get_all_conversations"):
                        logger.warning(
                            "Conversation manager does not support get_all_conversations method"
                        )
                        return {}

                    try:
                        # Get recent conversations
                        conversations = (
                            await self.conversation_manager.get_all_conversations(
                                limit=100
                            )
                        )

                        # Extract feedback from conversation metadata
                        skill_feedback = {}
                        for conversation in conversations:
                            metadata = conversation.get("metadata", {})
                            # Look for feedback entries in metadata
                            for key, value in metadata.items():
                                if key.startswith("feedback_"):
                                    # Check if the feedback is within the time range
                                    timestamp = value.get("timestamp")
                                    skill_used = value.get("skill_used")
                                    feedback_type = value.get("type")

                                    if timestamp and skill_used and feedback_type:
                                        try:
                                            feedback_date = datetime.fromisoformat(
                                                timestamp
                                            )
                                            if feedback_date >= start_date:
                                                # Initialize skill stats if needed
                                                if skill_used not in skill_feedback:
                                                    skill_feedback[skill_used] = {
                                                        "total": 0,
                                                        "positive": 0,
                                                        "negative": 0,
                                                    }

                                                # Update stats
                                                skill_feedback[skill_used]["total"] += 1
                                                if (
                                                    feedback_type
                                                    == FeedbackType.POSITIVE
                                                ):
                                                    skill_feedback[skill_used][
                                                        "positive"
                                                    ] += 1
                                                elif (
                                                    feedback_type
                                                    == FeedbackType.NEGATIVE
                                                ):
                                                    skill_feedback[skill_used][
                                                        "negative"
                                                    ] += 1
                                        except (ValueError, TypeError):
                                            # Skip entries with invalid timestamps
                                            pass

                        return skill_feedback
                    except Exception as e:
                        logger.error(f"Error retrieving conversations: {str(e)}")
                        return {}

                # Get feedback from conversations
                conversation_skill_feedback = loop.run_until_complete(
                    get_conversation_feedback_by_skill()
                )
                loop.close()

                # Add conversation feedback to combined stats
                for skill_name, stats in conversation_skill_feedback.items():
                    if skill_name not in skill_stats:
                        skill_stats[skill_name] = {
                            "skill": skill_name,
                            "total": 0,
                            "positive": 0,
                            "negative": 0,
                            "sources": ["conversation_storage"],
                        }
                    else:
                        skill_stats[skill_name]["sources"].append(
                            "conversation_storage"
                        )

                    # Update stats
                    skill_stats[skill_name]["total"] += stats["total"]
                    skill_stats[skill_name]["positive"] += stats["positive"]
                    skill_stats[skill_name]["negative"] += stats["negative"]
            except Exception as e:
                logger.error(
                    f"Error getting feedback by skill from conversation storage: {str(e)}"
                )

        # Calculate percentages and convert to list
        result = []
        for skill_data in skill_stats.values():
            total = skill_data["total"]
            positive = skill_data["positive"]

            # Calculate positive percentage
            positive_percentage = 0
            if total > 0:
                positive_percentage = (positive / total) * 100

            # Add percentage to the data
            skill_data["positive_percentage"] = positive_percentage

            # Add to result list
            result.append(skill_data)

        # Sort by total feedback count (descending)
        result.sort(key=lambda x: x["total"], reverse=True)

        return result

    def get_feedback_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get raw feedback data for the specified time period.

        This method combines feedback data from both Django models and
        conversation storage to provide comprehensive feedback data.

        Args:
            days: Number of days to include in the data

        Returns:
            List of feedback data entries
        """
        # Calculate the start date
        start_date = timezone.now() - timezone.timedelta(days=days)

        # Initialize result list
        result = []

        # Get data from Django models
        try:
            # Get all feedback entries for the specified time period
            feedback_entries = BotFeedback.objects.filter(
                feedback_timestamp__gte=start_date
            ).order_by("-feedback_timestamp")

            # Convert to a list of dictionaries
            for entry in feedback_entries:
                result.append(
                    {
                        "id": entry.id,
                        "message_id": entry.slack_message_ts,
                        "channel_id": entry.slack_channel_id,
                        "user_id": entry.slack_user_id,
                        "feedback_type": entry.feedback_type,
                        "reaction": entry.reaction,
                        "question": entry.question,
                        "answer": entry.answer,
                        "skill_used": entry.skill_used,
                        "function_used": entry.function_used,
                        "conversation_id": entry.conversation_id,
                        "timestamp": (
                            entry.feedback_timestamp.isoformat()
                            if entry.feedback_timestamp
                            else None
                        ),
                        "source": "django",
                    }
                )
        except Exception as e:
            logger.error(f"Error getting feedback data from Django models: {str(e)}")

        # Get additional data from conversation storage if available
        if self.conversation_manager:
            try:
                # Create a task to get conversation feedback
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def get_conversation_feedback_data():
                    # Check if the conversation manager has the required method
                    if not hasattr(self.conversation_manager, "get_all_conversations"):
                        logger.warning(
                            "Conversation manager does not support get_all_conversations method"
                        )
                        return []

                    try:
                        # Get recent conversations
                        conversations = (
                            await self.conversation_manager.get_all_conversations(
                                limit=100
                            )
                        )

                        # Extract feedback from conversation metadata
                        conversation_feedback = []
                        for conversation in conversations:
                            conversation_id = conversation.get("id")
                            metadata = conversation.get("metadata", {})

                            # Look for feedback entries in metadata
                            for key, value in metadata.items():
                                if key.startswith("feedback_"):
                                    # Extract message_id from the key (format: feedback_<message_id>)
                                    message_id = key.replace("feedback_", "")

                                    # Check if the feedback is within the time range
                                    timestamp = value.get("timestamp")
                                    if timestamp:
                                        try:
                                            feedback_date = datetime.fromisoformat(
                                                timestamp
                                            )
                                            if feedback_date >= start_date:
                                                # Create a feedback entry
                                                feedback_entry = {
                                                    "message_id": message_id,
                                                    "conversation_id": conversation_id,
                                                    "timestamp": timestamp,
                                                    "source": "conversation_storage",
                                                }

                                                # Add all available fields from the metadata
                                                for field, field_value in value.items():
                                                    if (
                                                        field != "timestamp"
                                                    ):  # Already added
                                                        feedback_entry[field] = (
                                                            field_value
                                                        )

                                                conversation_feedback.append(
                                                    feedback_entry
                                                )
                                        except (ValueError, TypeError):
                                            # Skip entries with invalid timestamps
                                            pass

                        return conversation_feedback
                    except Exception as e:
                        logger.error(f"Error retrieving conversations: {str(e)}")
                        return []

                # Get feedback from conversations
                conversation_feedback = loop.run_until_complete(
                    get_conversation_feedback_data()
                )
                loop.close()

                # Add conversation feedback to result
                result.extend(conversation_feedback)
            except Exception as e:
                logger.error(
                    f"Error getting feedback data from conversation storage: {str(e)}"
                )

        # Sort by timestamp (descending)
        result.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return result
