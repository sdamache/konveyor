"""
Tests for the Slack user profile service.
"""

import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone

from konveyor.apps.bot.models import SlackUserProfile
from konveyor.apps.bot.services.slack_user_profile_service import (
    SlackUserProfileService,
)


@pytest.mark.django_db
def test_get_or_create_profile_existing():
    """Test getting an existing profile."""
    # Create a test profile
    profile = SlackUserProfile.objects.create(
        slack_id="test_user",
        slack_name="Test User",
        slack_email="test@example.com",
        interaction_count=5,
        last_interaction=timezone.now(),
    )

    # Mock the Slack service
    mock_slack_service = MagicMock()

    # Create the service
    service = SlackUserProfileService(slack_service=mock_slack_service)

    # Get the profile
    result = service.get_or_create_profile("test_user")

    # Verify the result
    assert result is not None
    assert result.slack_id == "test_user"
    assert result.slack_name == "Test User"
    assert result.slack_email == "test@example.com"
    assert result.interaction_count == 6  # Should be incremented

    # Verify the Slack service was not called
    mock_slack_service.client.users_info.assert_not_called()


@pytest.mark.django_db
def test_get_or_create_profile_new():
    """Test creating a new profile."""
    # Mock the Slack service
    mock_slack_service = MagicMock()
    mock_slack_service.client.users_info.return_value = {
        "ok": True,
        "user": {
            "id": "new_user",
            "name": "New User",
            "profile": {
                "email": "new@example.com",
                "real_name": "New Real Name",
                "display_name": "New Display Name",
            },
            "team_id": "T12345",
        },
    }

    # Create the service
    service = SlackUserProfileService(slack_service=mock_slack_service)

    # Get or create the profile
    result = service.get_or_create_profile("new_user")

    # Verify the result
    assert result is not None
    assert result.slack_id == "new_user"
    assert result.slack_name == "New User"
    assert result.slack_email == "new@example.com"
    assert result.slack_real_name == "New Real Name"
    assert result.slack_display_name == "New Display Name"
    assert result.slack_team_id == "T12345"
    assert result.interaction_count == 1

    # Verify the Slack service was called
    mock_slack_service.client.users_info.assert_called_once_with(user="new_user")


@pytest.mark.django_db
def test_update_profile():
    """Test updating a profile."""
    # Create a test profile
    profile = SlackUserProfile.objects.create(
        slack_id="test_user", slack_name="Test User", slack_email="test@example.com"
    )

    # Mock the Slack service
    mock_slack_service = MagicMock()
    mock_slack_service.client.users_info.return_value = {
        "ok": True,
        "user": {
            "id": "test_user",
            "name": "Updated User",
            "profile": {
                "email": "updated@example.com",
                "real_name": "Updated Real Name",
                "display_name": "Updated Display Name",
            },
            "team_id": "T12345",
        },
    }

    # Create the service
    service = SlackUserProfileService(slack_service=mock_slack_service)

    # Update the profile
    result = service.update_profile("test_user")

    # Verify the result
    assert result is not None
    assert result.slack_id == "test_user"
    assert result.slack_name == "Updated User"
    assert result.slack_email == "updated@example.com"
    assert result.slack_real_name == "Updated Real Name"
    assert result.slack_display_name == "Updated Display Name"
    assert result.slack_team_id == "T12345"

    # Verify the Slack service was called
    mock_slack_service.client.users_info.assert_called_once_with(user="test_user")


@pytest.mark.django_db
def test_update_preference():
    """Test updating a user preference."""
    # Create a test profile
    profile = SlackUserProfile.objects.create(
        slack_id="test_user",
        slack_name="Test User",
        slack_email="test@example.com",
        code_language_preference="python",
        response_format_preference="concise",
    )

    # Create the service
    service = SlackUserProfileService()

    # Update the code language preference
    result = service.update_preference("test_user", "code_language", "javascript")

    # Verify the result
    assert result is not None
    assert result.code_language_preference == "javascript"
    assert result.response_format_preference == "concise"  # Unchanged

    # Update the response format preference
    result = service.update_preference("test_user", "response_format", "detailed")

    # Verify the result
    assert result is not None
    assert result.code_language_preference == "javascript"  # Unchanged
    assert result.response_format_preference == "detailed"

    # Test with unknown preference
    result = service.update_preference("test_user", "unknown", "value")

    # Verify the result (should be unchanged)
    assert result is not None
    assert result.code_language_preference == "javascript"
    assert result.response_format_preference == "detailed"


@pytest.mark.django_db
def test_get_active_profiles():
    """Test getting active profiles."""
    # Create test profiles
    active_profile = SlackUserProfile.objects.create(
        slack_id="active_user",
        slack_name="Active User",
        last_interaction=timezone.now(),
    )

    # Create an inactive profile (31 days ago)
    inactive_profile = SlackUserProfile.objects.create(
        slack_id="inactive_user",
        slack_name="Inactive User",
        last_interaction=timezone.now() - timezone.timedelta(days=31),
    )

    # Create the service
    service = SlackUserProfileService()

    # Get active profiles (default 30 days)
    active_profiles = service.get_active_profiles()

    # Verify the result
    assert len(active_profiles) == 1
    assert active_profiles[0].slack_id == "active_user"

    # Get active profiles with custom days
    all_profiles = service.get_active_profiles(days=60)

    # Verify the result
    assert len(all_profiles) == 2
