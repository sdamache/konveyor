# Knowledge Analyzer for Konveyor

This module provides a knowledge taxonomy and gap analysis system for the Konveyor project, helping identify and address knowledge gaps during the onboarding of new team members.

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


### 3. User Knowledge Store

The `user_knowledge.py` module provides the `UserKnowledgeStore` class, which:

- Stores and retrieves user knowledge confidence scores
- Tracks confidence levels for each user in different knowledge domains
- Provides methods to update confidence scores based on interactions
- Supports resetting user knowledge and calculating domain averages

### 4. Knowledge Gap Analyzer Skill

The `knowledge_gap_analyzer.py` module provides the `KnowledgeGapAnalyzerSkill` class, which:

- Analyzes user questions and maps them to knowledge domains
- Tracks user confidence in different knowledge areas
- Identifies knowledge gaps based on low confidence scores
- Suggests relevant documentation for addressing knowledge gaps
- Provides personalized learning paths based on role and knowledge gaps

## Usage

### Using the Taxonomy Loader
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


### Using the Knowledge Gap Analyzer

```python
from semantic_kernel import Kernel
from konveyor.skills.knowledge_analyzer import KnowledgeGapAnalyzerSkill

# Create the analyzer (optionally with a Semantic Kernel instance)
kernel = Kernel()  # In a real implementation, configure with Azure OpenAI
analyzer = KnowledgeGapAnalyzerSkill(kernel)

# Analyze a question
user_id = "user123"
question = "How do I set up the CI/CD pipeline?"
analysis_json = analyzer.analyze_question(question, user_id)

# Get a user's knowledge profile
profile_json = analyzer.get_knowledge_profile(user_id)

# Identify knowledge gaps
gaps_json = analyzer.identify_gaps(user_id)

# Get a personalized learning path
path_json = analyzer.get_learning_path("new_developer", user_id)
```

### Example Scripts

Example scripts are provided in the `examples/` directory:

- `taxonomy_example.py`: Demonstrates the usage of the `KnowledgeTaxonomyLoader` class
- `gap_analyzer_example.py`: Demonstrates the usage of the `KnowledgeGapAnalyzerSkill` class

To run the examples:

```bash
# Run the taxonomy example
python -m konveyor.skills.knowledge_analyzer.examples.taxonomy_example

# Run the gap analyzer example
python -m konveyor.skills.knowledge_analyzer.examples.gap_analyzer_example
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

Unit tests for the taxonomy loader and knowledge gap analyzer are provided in the `tests/` directory. To run the tests:

```bash
python -m pytest tests/test_knowledge_taxonomy.py -v
python -m pytest tests/test_knowledge_gap_analyzer.py -v
```

## Future Improvements

Several enhancements have been identified for future implementation. These are documented with TODO comments in the code and in the `docs/future_improvements.md` file. Key areas for improvement include:

### 1. Semantic Mapping Enhancements
- Replace keyword-based mapping with semantic understanding using LLMs
- Integrate with Semantic Kernel's LLM capabilities
- Use embeddings to calculate semantic similarity between questions and knowledge domains

### 2. Dynamic Resource Suggestions
- Replace hardcoded resource suggestions with dynamic, AI-powered recommendations
- Connect to actual documentation repository
- Use semantic search to find relevant documentation

### 3. Persistent Knowledge Storage
- Replace in-memory user knowledge store with persistent storage
- Implement database backend (PostgreSQL or Azure Cosmos DB)
- Add user authentication integration

### 4. Advanced Confidence Scoring
- Implement more sophisticated confidence scoring algorithms
- Analyze question intent (confusion vs. confirmation)
- Track answer quality and user feedback

For a complete list of planned improvements, see `docs/future_improvements.md`.
