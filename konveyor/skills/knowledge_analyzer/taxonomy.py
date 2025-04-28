"""
Knowledge Taxonomy Loader and Accessor Module.

This module provides functionality to load and access the knowledge taxonomy
defined in the knowledge_taxonomy.yaml file.
"""

import os
import yaml
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class KnowledgeTaxonomyLoader:
    """
    Loads and provides access to the knowledge taxonomy.

    This class is responsible for loading the knowledge taxonomy from the YAML file
    and providing methods to access and query the taxonomy.
    """

    def __init__(self, taxonomy_file: Optional[str] = None):
        """
        Initialize the KnowledgeTaxonomyLoader.

        Args:
            taxonomy_file: Optional path to the taxonomy YAML file. If not provided,
                           the default file in the same directory will be used.
        """
        if taxonomy_file is None:
            # Use the default file in the same directory as this module
            module_dir = Path(__file__).parent
            taxonomy_file = module_dir / "knowledge_taxonomy.yaml"

        self.taxonomy_file = taxonomy_file
        self.taxonomy = self._load_taxonomy()
        logger.info(f"Loaded knowledge taxonomy from {taxonomy_file}")

    def _load_taxonomy(self) -> Dict[str, Any]:
        """
        Load the taxonomy from the YAML file.

        Returns:
            Dict[str, Any]: The loaded taxonomy as a dictionary.

        Raises:
            FileNotFoundError: If the taxonomy file does not exist.
            yaml.YAMLError: If the YAML file is invalid.
        """
        try:
            with open(self.taxonomy_file, 'r') as file:
                taxonomy = yaml.safe_load(file)
                logger.debug(f"Successfully loaded taxonomy: {len(taxonomy.get('domains', []))} domains")
                return taxonomy
        except FileNotFoundError:
            logger.error(f"Taxonomy file not found: {self.taxonomy_file}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing taxonomy YAML: {e}")
            raise

    def get_all_domains(self) -> List[Dict[str, Any]]:
        """
        Get all knowledge domains.

        Returns:
            List[Dict[str, Any]]: List of all knowledge domains.
        """
        return self.taxonomy.get('domains', [])

    def get_domain_by_id(self, domain_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a domain by its ID.

        Args:
            domain_id: The ID of the domain to retrieve.

        Returns:
            Optional[Dict[str, Any]]: The domain if found, None otherwise.
        """
        for domain in self.taxonomy.get('domains', []):
            if domain.get('id') == domain_id:
                return domain
        return None

    def get_subcategories(self, domain_id: str) -> List[Dict[str, Any]]:
        """
        Get all subcategories for a domain.

        Args:
            domain_id: The ID of the domain.

        Returns:
            List[Dict[str, Any]]: List of subcategories for the domain.
        """
        domain = self.get_domain_by_id(domain_id)
        if domain:
            return domain.get('subcategories', [])
        return []

    def get_learning_paths(self) -> List[Dict[str, Any]]:
        """
        Get all learning paths.

        Returns:
            List[Dict[str, Any]]: List of all learning paths.
        """
        return self.taxonomy.get('learning_paths', [])

    def get_learning_path_by_role(self, role: str) -> Optional[Dict[str, Any]]:
        """
        Get a learning path by role.

        Args:
            role: The role to retrieve the learning path for.

        Returns:
            Optional[Dict[str, Any]]: The learning path if found, None otherwise.
        """
        for path in self.taxonomy.get('learning_paths', []):
            if path.get('role') == role:
                return path
        return None

    def get_relationships(self) -> List[Dict[str, Any]]:
        """
        Get all relationships between domains.

        Returns:
            List[Dict[str, Any]]: List of all relationships.
        """
        return self.taxonomy.get('relationships', [])

    def get_keywords_for_domain(self, domain_id: str) -> List[str]:
        """
        Get all keywords associated with a domain and its subcategories.

        Args:
            domain_id: The ID of the domain.

        Returns:
            List[str]: List of keywords.
        """
        keywords = []
        subcategories = self.get_subcategories(domain_id)

        for subcategory in subcategories:
            keywords.extend(subcategory.get('keywords', []))

        return keywords

    def find_domains_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Find domains that contain a specific keyword in their subcategories.

        Args:
            keyword: The keyword to search for.

        Returns:
            List[Dict[str, Any]]: List of domains that match the keyword.
        """
        matching_domains = []
        keyword = keyword.lower()

        for domain in self.get_all_domains():
            for subcategory in domain.get('subcategories', []):
                if any(keyword in kw.lower() for kw in subcategory.get('keywords', [])):
                    matching_domains.append(domain)
                    break

        return matching_domains

    def get_taxonomy_metadata(self) -> Dict[str, str]:
        """
        Get metadata about the taxonomy.

        Returns:
            Dict[str, str]: Dictionary containing metadata.
        """
        return {
            'version': self.taxonomy.get('version', 'unknown'),
            'last_updated': self.taxonomy.get('last_updated', 'unknown')
        }

    def map_query_to_domains(self, query: str) -> List[Dict[str, Any]]:
        """
        Map a user query to relevant knowledge domains.

        This is a simple keyword-based mapping. In a more advanced implementation,
        this could use embeddings or more sophisticated NLP techniques.

        Args:
            query: The user query to map.

        Returns:
            List[Dict[str, Any]]: List of relevant domains.
        """
        # TODO: [ENHANCEMENT] Replace keyword matching with semantic understanding
        # - Integrate with Semantic Kernel's LLM capabilities
        # - Use embeddings to calculate semantic similarity
        # - Create prompt templates for question analysis
        # - See docs/future_improvements.md for details

        query = query.lower()
        relevant_domains = []

        # Check each domain and its keywords
        for domain in self.get_all_domains():
            domain_id = domain.get('id')
            keywords = self.get_keywords_for_domain(domain_id)

            # Check if any keyword is in the query
            if any(keyword.lower() in query for keyword in keywords):
                relevant_domains.append(domain)

        return relevant_domains
