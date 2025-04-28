# Documentation Navigator Skill

A Semantic Kernel skill for documentation search and retrieval that wraps the existing SearchService.

## Overview

The DocumentationNavigatorSkill provides natural language search capabilities for documentation, with features for query preprocessing, response formatting, and citation handling. It integrates with the existing SearchService to retrieve relevant documentation based on user queries.

## Enhanced Features

### Advanced Query Preprocessing

The skill includes sophisticated query preprocessing to improve search results:

- **Onboarding-Related Query Enhancement**: Automatically detects and enhances queries related to onboarding, new employees, getting started, etc.
- **Technical Term Preservation**: Preserves important technical terms like API, SDK, Git, Docker, etc.
- **Filler Word Removal**: Removes question words and common filler words to focus on key concepts
- **Sentence Boundary Preservation**: Maintains natural sentence boundaries when truncating content

### Contextual Conversation Memory

The skill integrates with Semantic Kernel Memory for contextual conversations:

- **Conversation History**: Maintains conversation history across interactions
- **Context-Aware Responses**: Uses previous queries and responses to improve search results
- **Follow-Up Questions**: Handles follow-up questions with context from previous interactions
- **Query Enhancement**: Enhances queries with relevant terms from previous interactions
- **Persistent Memory**: Optionally stores conversations in persistent storage for long-term context

### Slack-Compatible Response Formatting

The skill provides rich, interactive formatting for Slack:

- **Block Kit Integration**: Uses Slack's Block Kit for structured, interactive messages
- **Rich Citations**: Properly formatted citations with document IDs and relevance scores
- **Fallback Plain Text**: Ensures content is accessible even when blocks fail to render
- **Interactive Elements**: Contextual information and guidance for follow-up questions

## Features

- **Documentation Search**: Search for information in documentation using natural language queries
- **Advanced Query Preprocessing**:
  - Optimize queries for better search results
  - Special handling for onboarding-related questions
  - Preservation of technical terms
  - Intelligent removal of filler words
- **Enhanced Response Formatting**:
  - Format search results with proper citations and references
  - Preserve sentence boundaries when truncating content
  - Include document IDs and relevance scores
  - Structured sources section with detailed metadata
- **Rich Slack Integration**:
  - Block Kit formatting for interactive messages
  - Header, context, and divider blocks for readability
  - Relevance score display
  - Fallback plain text for compatibility
  - Guidance for follow-up questions

## Usage

### Basic Usage

```python
import asyncio
from konveyor.skills.setup import create_kernel
from konveyor.skills.documentation_navigator import DocumentationNavigatorSkill

async def search_documentation():
    # Create a kernel
    kernel = create_kernel()

    # Create the DocumentationNavigatorSkill
    doc_skill = DocumentationNavigatorSkill(kernel)

    # Add the skill to the kernel
    functions = kernel.add_plugin(doc_skill, plugin_name="documentation")

    # Search for documentation
    query = "What is the onboarding process for new employees?"
    search_result = await doc_skill.search_documentation(query)
    print(f"Found {search_result['result_count']} results")

    # Answer a question using documentation
    question = "How do I set up my development environment?"
    answer = await doc_skill.answer_question(question)
    print(f"Answer: {answer[:100]}...")

    # Format results for Slack
    slack_query = "company policies"
    slack_format = await doc_skill.format_for_slack(slack_query)
    print(f"Slack format has {len(slack_format['blocks'])} blocks")

# Run the example
asyncio.run(search_documentation())
```

### Contextual Conversation Example

```python
import asyncio
from konveyor.skills.setup import create_kernel
from konveyor.skills.documentation_navigator import DocumentationNavigatorSkill

async def contextual_conversation():
    # Create a kernel
    kernel = create_kernel()

    # Create the DocumentationNavigatorSkill
    doc_skill = DocumentationNavigatorSkill(kernel)

    # Create a new conversation
    conversation = await doc_skill.create_conversation(user_id="user123")
    conversation_id = conversation["id"]
    print(f"Created conversation: {conversation_id}")

    # Ask an initial question
    initial_question = "What is the onboarding process for new employees?"
    answer1 = await doc_skill.answer_question(
        question=initial_question,
        conversation_id=conversation_id
    )
    print(f"Initial answer: {answer1[:100]}...")

    # Ask a follow-up question
    follow_up = "What should I do on my first day?"
    answer2 = await doc_skill.continue_conversation(
        follow_up_question=follow_up,
        conversation_id=conversation_id
    )
    print(f"Follow-up answer: {answer2[:100]}...")

    # Ask another follow-up question
    follow_up2 = "Who should I contact for IT setup?"
    answer3 = await doc_skill.continue_conversation(
        follow_up_question=follow_up2,
        conversation_id=conversation_id
    )
    print(f"Second follow-up answer: {answer3[:100]}...")

# Run the example
asyncio.run(contextual_conversation())
```

### Integration with Agent Orchestrator

The DocumentationNavigatorSkill can be registered with the AgentOrchestratorSkill to handle documentation-related queries:

```python
import asyncio
from konveyor.skills.setup import create_kernel
from konveyor.skills.documentation_navigator import DocumentationNavigatorSkill
from konveyor.skills.agent_orchestrator.AgentOrchestratorSkill import AgentOrchestratorSkill
from konveyor.skills.agent_orchestrator.registry import SkillRegistry

async def register_skill():
    # Create a kernel
    kernel = create_kernel()

    # Create a skill registry
    registry = SkillRegistry()

    # Create the DocumentationNavigatorSkill
    doc_skill = DocumentationNavigatorSkill(kernel)

    # Create the AgentOrchestratorSkill
    orchestrator = AgentOrchestratorSkill(kernel, registry)

    # Register the DocumentationNavigatorSkill
    skill_name = orchestrator.register_skill(
        doc_skill,
        description="A skill for searching and navigating documentation",
        keywords=[
            "documentation", "docs", "search", "find", "information", "help",
            "guide", "manual", "reference", "lookup", "document", "article",
            "tutorial", "how-to", "faq", "question", "answer", "onboarding"
        ]
    )

    # Test the skill
    test_request = "Where can I find documentation about onboarding?"
    response = await orchestrator.process_request(test_request)
    print(f"Response: {response}")

# Run the registration
asyncio.run(register_skill())
```

## Methods

### `search_documentation(query: str, top: int = 5) -> Dict[str, Any]`

Search documentation for information related to the query.

- **Parameters**:
  - `query`: The search query
  - `top`: Maximum number of results to return (default: 5)
- **Returns**: Dictionary containing search results and metadata

### `answer_question(question: str, top: int = 5, conversation_id: Optional[str] = None) -> str`

Answer a question using documentation search.

- **Parameters**:
  - `question`: The question to answer
  - `top`: Maximum number of search results to use (default: 5)
  - `conversation_id`: Optional conversation identifier for context
- **Returns**: Formatted answer with citations

### `format_for_slack(query: str, top: int = 5, conversation_id: Optional[str] = None) -> Dict[str, Any]`

Search documentation and format results in Slack-compatible Markdown.

- **Parameters**:
  - `query`: The search query
  - `top`: Maximum number of results to return (default: 5)
  - `conversation_id`: Optional conversation identifier for context
- **Returns**: Dictionary with text and blocks for Slack

### `create_conversation(user_id: Optional[str] = None) -> Dict[str, Any]`

Create a new conversation for contextual interactions.

- **Parameters**:
  - `user_id`: Optional user identifier
- **Returns**: Dictionary with conversation details

### `continue_conversation(follow_up_question: str, conversation_id: str, top: int = 5) -> str`

Continue a conversation with follow-up questions, using conversation history for context.

- **Parameters**:
  - `follow_up_question`: The follow-up question
  - `conversation_id`: The conversation identifier
  - `top`: Maximum number of search results to use (default: 5)
- **Returns**: Formatted answer with citations

## Dependencies

- `konveyor.apps.search.services.SearchService`: The underlying search service
- `semantic_kernel`: For Semantic Kernel integration
