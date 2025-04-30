"""
Models for the bot app.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from konveyor.apps.core.models import TimeStampedModel


class SlackUserProfile(TimeStampedModel):
    """
    Model to store Slack user profile information.
    """
    slack_id = models.CharField(max_length=50, unique=True)
    slack_name = models.CharField(max_length=100)
    slack_email = models.EmailField(blank=True, null=True)
    slack_real_name = models.CharField(max_length=100, blank=True, null=True)
    slack_display_name = models.CharField(max_length=100, blank=True, null=True)
    slack_team_id = models.CharField(max_length=50, blank=True, null=True)

    # Link to Django User if available
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='slack_profile')

    # User preferences
    code_language_preference = models.CharField(max_length=50, blank=True, null=True,
                                            help_text="Preferred programming language for code examples")
    response_format_preference = models.CharField(max_length=20, blank=True, null=True,
                                                choices=[
                                                    ('concise', 'Concise'),
                                                    ('detailed', 'Detailed'),
                                                    ('technical', 'Technical')
                                                ],
                                                default='concise',
                                                help_text="Preferred response format")

    # Interaction history
    last_interaction = models.DateTimeField(blank=True, null=True)
    interaction_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Slack User Profile"
        verbose_name_plural = "Slack User Profiles"

    def __str__(self):
        return f"{self.slack_name} ({self.slack_id})"

    def update_interaction(self):
        """Update the interaction count and timestamp."""
        from django.utils import timezone
        self.last_interaction = timezone.now()
        self.interaction_count += 1
        self.save(update_fields=['last_interaction', 'interaction_count'])

    def get_preferred_response_format(self):
        """Get the user's preferred response format."""
        return self.response_format_preference or 'concise'

    def get_preferred_code_language(self):
        """Get the user's preferred code language."""
        return self.code_language_preference


class BotFeedback(TimeStampedModel):
    """
    Django model to store user feedback on bot responses.

    This model tracks reactions (👍/👎) to bot messages in Slack,
    allowing us to measure response quality and improve the system.

    This is the concrete implementation of the feedback storage mechanism.
    It is used by the DjangoFeedbackRepository in konveyor/core/conversation/feedback/
    which implements the FeedbackStorageProvider interface.

    The separation between the interface (in core) and implementation (here)
    allows for better testability and flexibility in storage mechanisms.
    """
    # Message identifiers
    slack_message_ts = models.CharField(max_length=50, db_index=True,
                                help_text="Slack message timestamp (used as message ID)")
    slack_channel_id = models.CharField(max_length=50, db_index=True,
                                help_text="Slack channel ID where the message was posted")
    conversation_id = models.CharField(max_length=100, blank=True, null=True, db_index=True,
                                help_text="Conversation ID if available")

    # User who provided feedback
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                            related_name='bot_feedback')
    slack_user_id = models.CharField(max_length=50, db_index=True,
                                    help_text="Slack user ID who provided the feedback")

    # Feedback details
    FEEDBACK_CHOICES = [
        ('positive', 'Positive (👍)'),
        ('negative', 'Negative (👎)'),
        ('neutral', 'Neutral'),
        ('removed', 'Removed')
    ]
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_CHOICES,
                                    help_text="Type of feedback provided")
    reaction = models.CharField(max_length=50, blank=True, null=True,
                                    help_text="The specific reaction emoji used")

    # Message content (for reference)
    question = models.TextField(blank=True, null=True,
                            help_text="The original user question")
    answer = models.TextField(blank=True, null=True,
                            help_text="The bot's answer that received feedback")

    # Metadata
    skill_used = models.CharField(max_length=100, blank=True, null=True,
                                help_text="The skill that generated the answer")
    function_used = models.CharField(max_length=100, blank=True, null=True,
                                help_text="The function that generated the answer")
    feedback_timestamp = models.DateTimeField(default=timezone.now,
                                help_text="When the feedback was provided")

    class Meta:
        verbose_name = "Bot Feedback"
        verbose_name_plural = "Bot Feedback"
        # Ensure we don't have duplicate feedback entries for the same message and user
        unique_together = [['slack_message_ts', 'slack_user_id', 'reaction']]

    def __str__(self):
        return f"{self.get_feedback_type_display()} from {self.slack_user_id} on message {self.slack_message_ts}"

    @classmethod
    def record_feedback(cls, slack_message_ts, slack_channel_id, slack_user_id,
                        feedback_type, reaction=None, question=None, answer=None,
                        skill_used=None, function_used=None, conversation_id=None):
        """
        Record feedback for a bot message.

        Args:
            slack_message_ts: The Slack message timestamp (used as message ID)
            slack_channel_id: The Slack channel ID where the message was posted
            slack_user_id: The Slack user ID who provided the feedback
            feedback_type: The type of feedback (positive, negative, neutral, removed)
            reaction: The specific reaction emoji used (optional)
            question: The original user question (optional)
            answer: The bot's answer that received feedback (optional)
            skill_used: The skill that generated the answer (optional)
            function_used: The function that generated the answer (optional)
            conversation_id: The conversation ID if available (optional)

        Returns:
            The created or updated BotFeedback instance
        """
        # Try to find an existing feedback entry for this message and user
        try:
            feedback = cls.objects.get(
                slack_message_ts=slack_message_ts,
                slack_user_id=slack_user_id,
                reaction=reaction
            )
            # Update the existing feedback
            feedback.feedback_type = feedback_type
            feedback.feedback_timestamp = timezone.now()
            feedback.save(update_fields=['feedback_type', 'feedback_timestamp'])
        except cls.DoesNotExist:
            # Create a new feedback entry
            feedback = cls.objects.create(
                slack_message_ts=slack_message_ts,
                slack_channel_id=slack_channel_id,
                slack_user_id=slack_user_id,
                feedback_type=feedback_type,
                reaction=reaction,
                question=question,
                answer=answer,
                skill_used=skill_used,
                function_used=function_used,
                conversation_id=conversation_id
            )

        return feedback
