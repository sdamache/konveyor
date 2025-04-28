# Knowledge Taxonomy for Konveyor

This module provides a knowledge taxonomy for the Konveyor project, defining organizational knowledge domains relevant for onboarding new team members.

## Overview

The knowledge taxonomy is a structured representation of the knowledge areas that are important for understanding the Konveyor project. It includes:

- Knowledge domains (e.g., System Architecture, Development Practices)
- Subcategories within each domain
- Keywords associated with each subcategory
- Relationships between domains
- Learning paths for different roles

This taxonomy serves as the foundation for the Knowledge Gap Analyzer, which helps identify areas where a user might need additional information or training.

## Components

### 1. Knowledge Taxonomy YAML

The `knowledge_taxonomy.yaml` file defines the structure of the knowledge taxonomy, including:

- **Domains**: Top-level knowledge areas (e.g., System Architecture, Development Practices)
- **Subcategories**: More specific topics within each domain
- **Keywords**: Terms associated with each subcategory for matching user queries
- **Relationships**: Connections between different domains
- **Learning Paths**: Recommended learning sequences for different roles

### 2. Taxonomy Loader

The `taxonomy.py` module provides the `KnowledgeTaxonomyLoader` class, which:

- Loads the taxonomy from the YAML file
- Provides methods to access and query the taxonomy
- Maps user queries to relevant knowledge domains
- Retrieves learning paths for different roles

## Usage

### Basic Usage

```python
from konveyor.skills.knowledge_analyzer.taxonomy import KnowledgeTaxonomyLoader

# Create the taxonomy loader
loader = KnowledgeTaxonomyLoader()

# Get all knowledge domains
domains = loader.get_all_domains()

# Get subcategories for a domain
subcategories = loader.get_subcategories('technologies')

# Map a query to relevant domains
query = "How do I set up the CI/CD pipeline?"
relevant_domains = loader.map_query_to_domains(query)

# Get a learning path for a role
path = loader.get_learning_path_by_role('new_developer')
```

### Example Script

An example script is provided in `examples/taxonomy_example.py` that demonstrates the usage of the `KnowledgeTaxonomyLoader` class.

To run the example:

```bash
python -m konveyor.skills.knowledge_analyzer.examples.taxonomy_example
```

## Extending the Taxonomy

To extend or modify the taxonomy:

1. Edit the `knowledge_taxonomy.yaml` file to add or modify domains, subcategories, keywords, relationships, or learning paths.
2. The changes will be automatically picked up by the `KnowledgeTaxonomyLoader` class.

## Integration with Knowledge Gap Analyzer

This taxonomy will be used by the Knowledge Gap Analyzer (Task 7) to:

1. Map user queries to knowledge domains
2. Track user knowledge and confidence in different domains
3. Identify knowledge gaps
4. Suggest learning paths based on the user's role and current knowledge

## Testing

Unit tests for the taxonomy loader are provided in `tests/test_knowledge_taxonomy.py`. To run the tests:

```bash
python -m pytest tests/test_knowledge_taxonomy.py -v
```
