"""
Models for the bot app.
"""

from django.db import models
from django.contrib.auth.models import User
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
