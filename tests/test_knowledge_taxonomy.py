"""
Unit tests for the Knowledge Taxonomy Loader.
"""

import os  # noqa: F401
from pathlib import Path  # noqa: F401

import pytest  # noqa: F401

from konveyor.skills.knowledge_analyzer.taxonomy import KnowledgeTaxonomyLoader


class TestKnowledgeTaxonomyLoader:
    """Test cases for the KnowledgeTaxonomyLoader class."""

    def test_load_taxonomy(self):
        """Test that the taxonomy can be loaded successfully."""
        loader = KnowledgeTaxonomyLoader()
        assert loader.taxonomy is not None
        assert "domains" in loader.taxonomy
        assert "learning_paths" in loader.taxonomy
        assert "relationships" in loader.taxonomy

    def test_get_all_domains(self):
        """Test retrieving all domains."""
        loader = KnowledgeTaxonomyLoader()
        domains = loader.get_all_domains()
        assert isinstance(domains, list)
        assert len(domains) > 0
        # Check that each domain has the required fields
        for domain in domains:
            assert "id" in domain
            assert "name" in domain
            assert "description" in domain

    def test_get_domain_by_id(self):
        """Test retrieving a domain by ID."""
        loader = KnowledgeTaxonomyLoader()
        # Test with a valid domain ID
        domain = loader.get_domain_by_id("architecture")
        assert domain is not None
        assert domain["id"] == "architecture"
        assert "name" in domain
        assert "description" in domain

        # Test with an invalid domain ID
        domain = loader.get_domain_by_id("nonexistent")
        assert domain is None

    def test_get_subcategories(self):
        """Test retrieving subcategories for a domain."""
        loader = KnowledgeTaxonomyLoader()
        subcategories = loader.get_subcategories("technologies")
        assert isinstance(subcategories, list)
        assert len(subcategories) > 0
        # Check that each subcategory has the required fields
        for subcategory in subcategories:
            assert "id" in subcategory
            assert "name" in subcategory
            assert "description" in subcategory
            assert "keywords" in subcategory

    def test_get_learning_paths(self):
        """Test retrieving all learning paths."""
        loader = KnowledgeTaxonomyLoader()
        paths = loader.get_learning_paths()
        assert isinstance(paths, list)
        assert len(paths) > 0
        # Check that each path has the required fields
        for path in paths:
            assert "role" in path
            assert "name" in path
            assert "description" in path
            assert "domains" in path

    def test_get_learning_path_by_role(self):
        """Test retrieving a learning path by role."""
        loader = KnowledgeTaxonomyLoader()
        # Test with a valid role
        path = loader.get_learning_path_by_role("new_developer")
        assert path is not None
        assert path["role"] == "new_developer"
        assert "name" in path
        assert "description" in path
        assert "domains" in path

        # Test with an invalid role
        path = loader.get_learning_path_by_role("nonexistent")
        assert path is None

    def test_get_keywords_for_domain(self):
        """Test retrieving keywords for a domain."""
        loader = KnowledgeTaxonomyLoader()
        keywords = loader.get_keywords_for_domain("technologies")
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # Check that the keywords include expected terms
        all_keywords = " ".join(keywords).lower()
        assert "python" in all_keywords
        assert "django" in all_keywords
        assert "azure" in all_keywords
        assert "semantic kernel" in all_keywords

    def test_find_domains_by_keyword(self):
        """Test finding domains by keyword."""
        loader = KnowledgeTaxonomyLoader()
        # Test with a keyword that should match
        domains = loader.find_domains_by_keyword("semantic kernel")
        assert isinstance(domains, list)
        assert len(domains) > 0
        assert any(domain["id"] == "technologies" for domain in domains)

        # Test with a keyword that shouldn't match
        domains = loader.find_domains_by_keyword("nonexistent_keyword")
        assert isinstance(domains, list)
        assert len(domains) == 0

    def test_map_query_to_domains(self):
        """Test mapping a query to domains."""
        loader = KnowledgeTaxonomyLoader()
        # Test with a query that should match multiple domains
        query = "How do I set up the CI/CD pipeline with GitHub Actions?"
        domains = loader.map_query_to_domains(query)
        assert isinstance(domains, list)
        assert len(domains) > 0
        domain_ids = [domain["id"] for domain in domains]
        assert "deployment" in domain_ids

        # Test with a query that should match a specific domain
        query = "What are the best practices for using Semantic Kernel?"
        domains = loader.map_query_to_domains(query)
        assert isinstance(domains, list)
        assert len(domains) > 0
        domain_ids = [domain["id"] for domain in domains]
        assert "technologies" in domain_ids
