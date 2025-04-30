"""
Unit tests for the Knowledge Gap Analyzer.
"""

import json
import pytest
from konveyor.skills.knowledge_analyzer.knowledge_gap_analyzer import (
    KnowledgeGapAnalyzerSkill,
)
from konveyor.skills.knowledge_analyzer.user_knowledge import UserKnowledgeStore


class TestUserKnowledgeStore:
    """Test cases for the UserKnowledgeStore class."""

    def test_get_confidence_default(self):
        """Test that default confidence is 0.5."""
        store = UserKnowledgeStore()
        confidence = store.get_confidence("test_user", "architecture")
        assert confidence == 0.5

    def test_set_and_get_confidence(self):
        """Test setting and getting confidence scores."""
        store = UserKnowledgeStore()
        store.set_confidence("test_user", "architecture", 0.8)
        confidence = store.get_confidence("test_user", "architecture")
        assert confidence == 0.8

    def test_set_confidence_validation(self):
        """Test validation of confidence scores."""
        store = UserKnowledgeStore()
        with pytest.raises(ValueError):
            store.set_confidence("test_user", "architecture", 1.5)
        with pytest.raises(ValueError):
            store.set_confidence("test_user", "architecture", -0.1)

    def test_get_user_knowledge(self):
        """Test getting all knowledge for a user."""
        store = UserKnowledgeStore()
        store.set_confidence("test_user", "architecture", 0.8)
        store.set_confidence("test_user", "development", 0.6)
        knowledge = store.get_user_knowledge("test_user")
        assert knowledge == {"architecture": 0.8, "development": 0.6}

    def test_reset_user_knowledge(self):
        """Test resetting user knowledge."""
        store = UserKnowledgeStore()
        store.set_confidence("test_user", "architecture", 0.8)
        store.reset_user_knowledge("test_user")
        knowledge = store.get_user_knowledge("test_user")
        assert knowledge == {}

    def test_get_all_users(self):
        """Test getting all users."""
        store = UserKnowledgeStore()
        store.set_confidence("user1", "architecture", 0.8)
        store.set_confidence("user2", "development", 0.6)
        users = store.get_all_users()
        assert set(users) == {"user1", "user2"}

    def test_get_domain_average(self):
        """Test getting average confidence for a domain."""
        store = UserKnowledgeStore()
        store.set_confidence("user1", "architecture", 0.8)
        store.set_confidence("user2", "architecture", 0.6)
        average = store.get_domain_average("architecture")
        assert average == 0.7


class TestKnowledgeGapAnalyzerSkill:
    """Test cases for the KnowledgeGapAnalyzerSkill class."""

    def test_analyze_question(self):
        """Test analyzing a question."""
        analyzer = KnowledgeGapAnalyzerSkill()
        result = analyzer.analyze_question(
            "How do I set up the CI/CD pipeline?", "test_user"
        )
        result_dict = json.loads(result)

        assert "question" in result_dict
        assert "relevant_domains" in result_dict
        assert "knowledge_gaps" in result_dict

        # Check that the question was mapped to the deployment domain
        domain_ids = [domain["id"] for domain in result_dict["relevant_domains"]]
        assert "deployment" in domain_ids

    def test_get_knowledge_profile(self):
        """Test getting a knowledge profile."""
        analyzer = KnowledgeGapAnalyzerSkill()
        result = analyzer.get_knowledge_profile("test_user")
        result_dict = json.loads(result)

        assert "user_id" in result_dict
        assert "knowledge_areas" in result_dict
        assert len(result_dict["knowledge_areas"]) > 0

    def test_identify_gaps(self):
        """Test identifying knowledge gaps."""
        analyzer = KnowledgeGapAnalyzerSkill()

        # Set up some knowledge scores
        analyzer.user_knowledge.set_confidence("test_user", "architecture", 0.3)
        analyzer.user_knowledge.set_confidence("test_user", "development", 0.8)

        result = analyzer.identify_gaps("test_user")
        result_dict = json.loads(result)

        assert "user_id" in result_dict
        assert "knowledge_gaps" in result_dict

        # Check that architecture is identified as a gap
        gap_ids = [gap["id"] for gap in result_dict["knowledge_gaps"]]
        assert "architecture" in gap_ids

        # Check that development is not identified as a gap
        assert "development" not in gap_ids

    def test_get_learning_path(self):
        """Test getting a learning path."""
        analyzer = KnowledgeGapAnalyzerSkill()

        # Set up some knowledge scores
        analyzer.user_knowledge.set_confidence("test_user", "architecture", 0.3)
        analyzer.user_knowledge.set_confidence("test_user", "development", 0.8)

        result = analyzer.get_learning_path("new_developer", "test_user")
        result_dict = json.loads(result)

        assert "user_id" in result_dict
        assert "role" in result_dict
        assert "path_name" in result_dict
        assert "domains" in result_dict

        # Check that the learning path includes the domains
        domain_ids = [domain["id"] for domain in result_dict["domains"]]
        assert "architecture" in domain_ids
        assert "development" in domain_ids

        # Check that architecture is marked as a gap
        for domain in result_dict["domains"]:
            if domain["id"] == "architecture":
                assert domain["is_gap"] is True
                assert (
                    domain["priority"] == "high"
                )  # Should be high priority because it's a gap
