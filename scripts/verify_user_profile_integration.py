#!/usr/bin/env python
"""
Verification script for user profile integration with Slack.

This script checks if user profiles are being created and updated correctly.
"""

import os
import sys
import logging
import json
from datetime import datetime

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'konveyor.settings.development')

import django
django.setup()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import after Django setup
from konveyor.apps.bot.models import SlackUserProfile
from django.db.models import Count, Max, Min, Avg

def verify_user_profiles():
    """Verify that user profiles exist and have the expected data."""
    logger.info("Verifying user profiles...")
    
    # Count profiles
    profile_count = SlackUserProfile.objects.count()
    logger.info(f"Found {profile_count} user profiles")
    
    if profile_count == 0:
        logger.error("No user profiles found. Integration may not be working correctly.")
        return False
    
    # Get profile statistics
    stats = {
        'with_email': SlackUserProfile.objects.exclude(slack_email='').count(),
        'with_code_language': SlackUserProfile.objects.exclude(code_language_preference='').count(),
        'with_response_format': SlackUserProfile.objects.exclude(response_format_preference='').count(),
        'avg_interactions': SlackUserProfile.objects.aggregate(Avg('interaction_count'))['interaction_count__avg'],
        'max_interactions': SlackUserProfile.objects.aggregate(Max('interaction_count'))['interaction_count__max'],
    }
    
    logger.info(f"Profile statistics:")
    logger.info(f"  Profiles with email: {stats['with_email']} ({stats['with_email']/profile_count*100:.1f}%)")
    logger.info(f"  Profiles with code language preference: {stats['with_code_language']} ({stats['with_code_language']/profile_count*100:.1f}%)")
    logger.info(f"  Profiles with response format preference: {stats['with_response_format']} ({stats['with_response_format']/profile_count*100:.1f}%)")
    logger.info(f"  Average interactions per profile: {stats['avg_interactions']:.1f}")
    logger.info(f"  Maximum interactions for a profile: {stats['max_interactions']}")
    
    # List all profiles
    logger.info("\nUser profiles:")
    for profile in SlackUserProfile.objects.all():
        logger.info(f"  {profile.slack_name} ({profile.slack_id}):")
        logger.info(f"    Email: {profile.slack_email}")
        logger.info(f"    Real name: {profile.slack_real_name}")
        logger.info(f"    Code language: {profile.code_language_preference or 'Not set'}")
        logger.info(f"    Response format: {profile.response_format_preference or 'Not set'}")
        logger.info(f"    Interactions: {profile.interaction_count}")
        logger.info(f"    Last interaction: {profile.last_interaction}")
    
    return True

def main():
    """Run verification checks."""
    logger.info("Starting user profile integration verification...")
    
    # Verify user profiles
    if verify_user_profiles():
        logger.info("User profile verification passed!")
    else:
        logger.error("User profile verification failed!")
        return 1
    
    logger.info("All verification checks passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
