"""
Example script to demonstrate the usage of the KnowledgeTaxonomyLoader.

This script shows how to load the knowledge taxonomy and access its components.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the Python path to allow importing the module
parent_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(parent_dir))

from konveyor.skills.knowledge_analyzer.taxonomy import KnowledgeTaxonomyLoader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the example script."""
    logger.info("Starting Knowledge Taxonomy Example")
    
    # Create the taxonomy loader
    try:
        loader = KnowledgeTaxonomyLoader()
        logger.info("Successfully created KnowledgeTaxonomyLoader")
    except Exception as e:
        logger.error(f"Failed to create KnowledgeTaxonomyLoader: {e}")
        return
    
    # Get metadata
    metadata = loader.get_taxonomy_metadata()
    print(f"\nTaxonomy Metadata:")
    print(f"Version: {metadata['version']}")
    print(f"Last Updated: {metadata['last_updated']}")
    
    # Get all domains
    domains = loader.get_all_domains()
    print(f"\nKnowledge Domains ({len(domains)}):")
    for domain in domains:
        print(f"- {domain['name']}: {domain['description']}")
    
    # Get subcategories for a domain
    domain_id = "technologies"
    subcategories = loader.get_subcategories(domain_id)
    print(f"\nSubcategories for '{domain_id}' ({len(subcategories)}):")
    for subcategory in subcategories:
        print(f"- {subcategory['name']}: {subcategory['description']}")
        print(f"  Keywords: {', '.join(subcategory['keywords'])}")
    
    # Get learning paths
    learning_paths = loader.get_learning_paths()
    print(f"\nLearning Paths ({len(learning_paths)}):")
    for path in learning_paths:
        print(f"- {path['name']}: {path['description']}")
        print(f"  Domains:")
        for domain in path['domains']:
            print(f"  - {domain['id']} (Priority: {domain['priority']})")
    
    # Map a query to domains
    query = "How do I set up the CI/CD pipeline with GitHub Actions?"
    relevant_domains = loader.map_query_to_domains(query)
    print(f"\nRelevant domains for query '{query}':")
    for domain in relevant_domains:
        print(f"- {domain['name']}")
    
    # Find domains by keyword
    keyword = "semantic kernel"
    matching_domains = loader.find_domains_by_keyword(keyword)
    print(f"\nDomains matching keyword '{keyword}':")
    for domain in matching_domains:
        print(f"- {domain['name']}")

if __name__ == "__main__":
    main()
