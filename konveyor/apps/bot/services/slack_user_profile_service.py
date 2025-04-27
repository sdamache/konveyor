"""
Slack User Profile Service for Konveyor.

This module provides functionality for managing Slack user profiles,
including retrieving, creating, and updating user profiles.
"""

import logging
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from konveyor.apps.bot.models import SlackUserProfile
from konveyor.apps.bot.services.slack_service import SlackService

# Configure logging
logger = logging.getLogger(__name__)

class SlackUserProfileService:
    """
    Service for managing Slack user profiles.
    
    This service provides methods for retrieving, creating, and updating
    Slack user profiles, as well as managing user preferences.
    """
    
    def __init__(self, slack_service: Optional[SlackService] = None):
        """
        Initialize the Slack user profile service.
        
        Args:
            slack_service: Optional Slack service instance
        """
        self.slack_service = slack_service or SlackService()
        logger.info("Initialized SlackUserProfileService")
    
    def get_or_create_profile(self, slack_id: str) -> SlackUserProfile:
        """
        Get or create a Slack user profile.
        
        Args:
            slack_id: The Slack user ID
            
        Returns:
            The Slack user profile
        """
        try:
            # Try to get the existing profile
            profile = SlackUserProfile.objects.get(slack_id=slack_id)
            logger.debug(f"Found existing profile for user {slack_id}")
            
            # Update the interaction timestamp
            profile.update_interaction()
            
            return profile
        except SlackUserProfile.DoesNotExist:
            # Profile doesn't exist, create a new one
            logger.info(f"Creating new profile for user {slack_id}")
            
            # Get user info from Slack API
            user_info = self._get_user_info(slack_id)
            
            # Create the profile
            with transaction.atomic():
                profile = SlackUserProfile(
                    slack_id=slack_id,
                    slack_name=user_info.get('name', ''),
                    slack_email=user_info.get('email', ''),
                    slack_real_name=user_info.get('real_name', ''),
                    slack_display_name=user_info.get('display_name', ''),
                    slack_team_id=user_info.get('team_id', ''),
                    last_interaction=timezone.now(),
                    interaction_count=1
                )
                profile.save()
            
            logger.info(f"Created new profile for user {slack_id}")
            return profile
    
    def update_profile(self, slack_id: str) -> Optional[SlackUserProfile]:
        """
        Update a Slack user profile with the latest information from Slack.
        
        Args:
            slack_id: The Slack user ID
            
        Returns:
            The updated Slack user profile, or None if the profile doesn't exist
        """
        try:
            # Get the existing profile
            profile = SlackUserProfile.objects.get(slack_id=slack_id)
            
            # Get user info from Slack API
            user_info = self._get_user_info(slack_id)
            
            # Update the profile
            with transaction.atomic():
                profile.slack_name = user_info.get('name', profile.slack_name)
                profile.slack_email = user_info.get('email', profile.slack_email)
                profile.slack_real_name = user_info.get('real_name', profile.slack_real_name)
                profile.slack_display_name = user_info.get('display_name', profile.slack_display_name)
                profile.slack_team_id = user_info.get('team_id', profile.slack_team_id)
                profile.save()
            
            logger.info(f"Updated profile for user {slack_id}")
            return profile
        except SlackUserProfile.DoesNotExist:
            logger.warning(f"Profile not found for user {slack_id}")
            return None
    
    def update_preference(self, slack_id: str, preference_name: str, preference_value: str) -> Optional[SlackUserProfile]:
        """
        Update a user preference.
        
        Args:
            slack_id: The Slack user ID
            preference_name: The name of the preference to update
            preference_value: The new value for the preference
            
        Returns:
            The updated Slack user profile, or None if the profile doesn't exist
        """
        try:
            # Get the existing profile
            profile = SlackUserProfile.objects.get(slack_id=slack_id)
            
            # Update the preference
            with transaction.atomic():
                if preference_name == 'code_language':
                    profile.code_language_preference = preference_value
                elif preference_name == 'response_format':
                    profile.response_format_preference = preference_value
                else:
                    logger.warning(f"Unknown preference: {preference_name}")
                    return profile
                
                profile.save()
            
            logger.info(f"Updated {preference_name} preference for user {slack_id} to {preference_value}")
            return profile
        except SlackUserProfile.DoesNotExist:
            logger.warning(f"Profile not found for user {slack_id}")
            return None
    
    def get_all_profiles(self) -> List[SlackUserProfile]:
        """
        Get all Slack user profiles.
        
        Returns:
            A list of all Slack user profiles
        """
        return SlackUserProfile.objects.all()
    
    def get_active_profiles(self, days: int = 30) -> List[SlackUserProfile]:
        """
        Get active Slack user profiles.
        
        Args:
            days: Number of days to consider for activity
            
        Returns:
            A list of active Slack user profiles
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return SlackUserProfile.objects.filter(last_interaction__gte=cutoff_date)
    
    def _get_user_info(self, slack_id: str) -> Dict[str, Any]:
        """
        Get user information from Slack API.
        
        Args:
            slack_id: The Slack user ID
            
        Returns:
            A dictionary with user information
        """
        try:
            # Call the Slack API to get user info
            response = self.slack_service.client.users_info(user=slack_id)
            
            if not response.get('ok', False):
                logger.error(f"Error getting user info from Slack: {response.get('error', 'Unknown error')}")
                return {}
            
            user = response.get('user', {})
            
            # Extract relevant information
            user_info = {
                'name': user.get('name', ''),
                'email': user.get('profile', {}).get('email', ''),
                'real_name': user.get('profile', {}).get('real_name', ''),
                'display_name': user.get('profile', {}).get('display_name', ''),
                'team_id': user.get('team_id', '')
            }
            
            logger.debug(f"Retrieved user info for {slack_id}: {user_info['name']}")
            return user_info
        except Exception as e:
            logger.error(f"Error getting user info from Slack: {str(e)}")
            return {}
