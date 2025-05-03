"""
User Knowledge Store for Konveyor.

This module provides functionality to store and retrieve user knowledge confidence scores  # noqa: E501
for different knowledge domains.
"""

import logging
from typing import Any, Dict, Optional  # noqa: F401, F401

logger = logging.getLogger(__name__)


class UserKnowledgeStore:
    """
    Store and retrieve user knowledge confidence scores.

    This class provides an in-memory store for user knowledge confidence scores.
    In a production environment, this would be replaced with a persistent store
    like Azure Cosmos DB or a SQL database.
    """

    def __init__(self):
        """Initialize the UserKnowledgeStore."""
        # In-memory store for user knowledge
        # Format: {user_id: {domain_id: confidence_score}}
        self.store = {}
        logger.info("Initialized UserKnowledgeStore")

    def get_confidence(self, user_id: str, domain_id: str) -> float:
        """
        Get the confidence score for a user in a specific domain.

        Args:
            user_id: Identifier for the user.
            domain_id: Identifier for the knowledge domain.

        Returns:
            float: Confidence score between 0.0 and 1.0. Default is 0.5 if not set.
        """
        # Get the user's knowledge store, or create if it doesn't exist
        user_knowledge = self.store.get(user_id, {})

        # Get the confidence score, or default to 0.5 if not set
        confidence = user_knowledge.get(domain_id, 0.5)

        return confidence

    def set_confidence(self, user_id: str, domain_id: str, confidence: float) -> None:
        """
        Set the confidence score for a user in a specific domain.

        Args:
            user_id: Identifier for the user.
            domain_id: Identifier for the knowledge domain.
            confidence: Confidence score between 0.0 and 1.0.

        Raises:
            ValueError: If confidence is not between 0.0 and 1.0.
        """
        # Validate confidence score
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")

        # Get the user's knowledge store, or create if it doesn't exist
        if user_id not in self.store:
            self.store[user_id] = {}

        # Set the confidence score
        self.store[user_id][domain_id] = confidence
        logger.debug(
            f"Set confidence for user {user_id}, domain {domain_id}: {confidence}"
        )

    def get_user_knowledge(self, user_id: str) -> dict[str, float]:
        """
        Get all knowledge confidence scores for a user.

        Args:
            user_id: Identifier for the user.

        Returns:
            Dict[str, float]: Dictionary mapping domain IDs to confidence scores.
        """
        # Get the user's knowledge store, or empty dict if it doesn't exist
        return self.store.get(user_id, {})

    def reset_user_knowledge(self, user_id: str) -> None:
        """
        Reset all knowledge confidence scores for a user.

        Args:
            user_id: Identifier for the user.
        """
        # Remove the user's knowledge store
        if user_id in self.store:
            del self.store[user_id]
            logger.info(f"Reset knowledge for user {user_id}")

    def get_all_users(self) -> list:
        """
        Get a list of all user IDs in the store.

        Returns:
            list: List of user IDs.
        """
        return list(self.store.keys())

    def get_domain_average(self, domain_id: str) -> float:
        """
        Get the average confidence score for a domain across all users.

        Args:
            domain_id: Identifier for the knowledge domain.

        Returns:
            float: Average confidence score, or 0.0 if no scores exist.
        """
        scores = []

        # Collect scores for the domain from all users
        for user_id, domains in self.store.items():
            if domain_id in domains:
                scores.append(domains[domain_id])

        # Calculate average, or return 0.0 if no scores
        if scores:
            return sum(scores) / len(scores)
        else:
            return 0.0
