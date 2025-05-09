# Generated by Django 5.1.7 on 2025-04-28 21:01

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("konveyor_bot", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BotFeedback",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "slack_message_ts",
                    models.CharField(
                        db_index=True,
                        help_text="Slack message timestamp (used as message ID)",
                        max_length=50,
                    ),
                ),
                (
                    "slack_channel_id",
                    models.CharField(
                        db_index=True,
                        help_text="Slack channel ID where the message was posted",
                        max_length=50,
                    ),
                ),
                (
                    "conversation_id",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="Conversation ID if available",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "slack_user_id",
                    models.CharField(
                        db_index=True,
                        help_text="Slack user ID who provided the feedback",
                        max_length=50,
                    ),
                ),
                (
                    "feedback_type",
                    models.CharField(
                        choices=[
                            ("positive", "Positive (👍)"),
                            ("negative", "Negative (👎)"),
                            ("neutral", "Neutral"),
                            ("removed", "Removed"),
                        ],
                        help_text="Type of feedback provided",
                        max_length=20,
                    ),
                ),
                (
                    "reaction",
                    models.CharField(
                        blank=True,
                        help_text="The specific reaction emoji used",
                        max_length=50,
                        null=True,
                    ),
                ),
                (
                    "question",
                    models.TextField(
                        blank=True, help_text="The original user question", null=True
                    ),
                ),
                (
                    "answer",
                    models.TextField(
                        blank=True,
                        help_text="The bot's answer that received feedback",
                        null=True,
                    ),
                ),
                (
                    "skill_used",
                    models.CharField(
                        blank=True,
                        help_text="The skill that generated the answer",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "function_used",
                    models.CharField(
                        blank=True,
                        help_text="The function that generated the answer",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "feedback_timestamp",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        help_text="When the feedback was provided",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="bot_feedback",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Bot Feedback",
                "verbose_name_plural": "Bot Feedback",
                "unique_together": {("slack_message_ts", "slack_user_id", "reaction")},
            },
        ),
    ]
