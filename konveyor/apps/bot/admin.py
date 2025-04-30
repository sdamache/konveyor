"""
Admin configuration for the bot app.
"""

from django.contrib import admin
from konveyor.apps.bot.models import SlackUserProfile


@admin.register(SlackUserProfile)
class SlackUserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for the SlackUserProfile model."""

    list_display = (
        "slack_id",
        "slack_name",
        "slack_email",
        "interaction_count",
        "last_interaction",
    )
    list_filter = ("response_format_preference",)
    search_fields = (
        "slack_id",
        "slack_name",
        "slack_email",
        "slack_real_name",
        "slack_display_name",
    )
    readonly_fields = (
        "created_at",
        "modified_at",
        "interaction_count",
        "last_interaction",
    )
    fieldsets = (
        (
            "Slack Information",
            {
                "fields": (
                    "slack_id",
                    "slack_name",
                    "slack_email",
                    "slack_real_name",
                    "slack_display_name",
                    "slack_team_id",
                )
            },
        ),
        (
            "User Preferences",
            {"fields": ("code_language_preference", "response_format_preference")},
        ),
        ("Interaction History", {"fields": ("interaction_count", "last_interaction")}),
        ("Timestamps", {"fields": ("created_at", "modified_at")}),
    )
