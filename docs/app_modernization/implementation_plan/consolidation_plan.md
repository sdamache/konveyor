# Consolidation Plan

## Overview

This document outlines a comprehensive plan to consolidate redundant code identified in the [Redundancy Analysis](../analysis/redundancy_analysis.md). The plan is divided into phases to ensure a systematic approach to code consolidation.

## Goals

1. **Reduce Code Duplication**: Eliminate redundant implementations
2. **Improve Maintainability**: Make the codebase easier to maintain
3. **Enhance Extensibility**: Create a more modular and extensible architecture
4. **Preserve Functionality**: Ensure all existing features continue to work
5. **Minimize Disruption**: Implement changes with minimal impact on existing code

## Consolidation Phases

### Phase 1: Define Interfaces

**Objective**: Create clear interfaces for each component to establish a common contract.

#### Tasks:

1. **Create Conversation Interface**
   - Create `konveyor/core/conversation/interface.py`
   - Define `ConversationInterface` with methods for:
     - Creating conversations
     - Adding messages
     - Retrieving messages
     - Managing conversation context

2. **Create Message Formatting Interface**
   - Create `konveyor/core/formatters/interface.py`
   - Define `FormatterInterface` with methods for:
     - Formatting messages for different platforms (Slack, Teams, etc.)
     - Converting between formats

3. **Create Azure OpenAI Client Interface**
   - Create `konveyor/core/azure_utils/openai_interface.py`
   - Define `OpenAIClientInterface` with methods for:
     - Generating completions
     - Managing models and deployments
     - Handling errors and retries

4. **Create Response Generation Interface**
   - Create `konveyor/core/generation/interface.py`
   - Define `ResponseGeneratorInterface` with methods for:
     - Generating responses with or without context
     - Managing prompt templates
     - Handling different response types

### Phase 2: Refactor Core Components

**Objective**: Implement the interfaces defined in Phase 1 with concrete classes.

#### Tasks:

1. **Implement Unified Conversation Management**
   - Create `konveyor/core/conversation/memory.py` for in-memory storage
   - Refactor `konveyor/core/conversation/storage.py` to implement the interface
   - Create a factory for creating conversation managers

2. **Implement Consolidated Message Formatting**
   - Create `konveyor/core/formatters/slack.py` for Slack formatting
   - Create `konveyor/core/formatters/markdown.py` for general Markdown formatting
   - Create a factory for creating formatters

3. **Implement Unified Azure OpenAI Client**
   - Create `konveyor/core/azure_utils/openai_client.py`
   - Implement the interface with proper error handling and retries
   - Create a factory for creating clients

4. **Implement Integrated Response Generation**
   - Create `konveyor/core/generation/generator.py`
   - Implement the interface with support for RAG and direct generation
   - Create a factory for creating generators

### Phase 3: Update Implementations

**Objective**: Update existing code to use the new interfaces and implementations.

#### Tasks:

1. **Update ChatSkill**
   - Refactor `konveyor/core/chat/skill.py` to use the new interfaces
   - Remove redundant code
   - Ensure backward compatibility

2. **Update RAG Service**
   - Refactor `konveyor/core/rag/rag_service.py` to use the new interfaces
   - Remove redundant code
   - Ensure backward compatibility

3. **Update Bot Views**
   - Refactor `konveyor/apps/bot/views.py` to use the new interfaces
   - Remove redundant code
   - Ensure backward compatibility

4. **Update RAG Views**
   - Refactor `konveyor/apps/rag/views.py` to use the new interfaces
   - Remove redundant code
   - Ensure backward compatibility

### Phase 4: Clean Up

**Objective**: Remove redundant code and ensure the codebase is clean and well-documented.

#### Tasks:

1. **Remove Redundant Code**
   - Identify and remove any remaining redundant code
   - Update import statements
   - Ensure no dead code remains

2. **Update Documentation**
   - Update docstrings
   - Create architecture documentation
   - Update README files

3. **Add Tests**
   - Add unit tests for new components
   - Add integration tests
   - Ensure all tests pass

4. **Final Review**
   - Conduct code review
   - Address any issues
   - Finalize the consolidation

## Implementation Details

### 1. Unified Conversation Management

The unified conversation management will provide a common interface for managing conversations, with implementations for both in-memory and persistent storage.

```python
# konveyor/core/conversation/interface.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

class ConversationInterface(ABC):
    """Interface for conversation management."""
    
    @abstractmethod
    async def create_conversation(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new conversation."""
        pass
    
    @abstractmethod
    async def add_message(self, conversation_id: str, content: str, 
                         message_type: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Add a message to a conversation."""
        pass
    
    @abstractmethod
    async def get_conversation_messages(self, conversation_id: str, 
                                      limit: int = 50) -> List[Dict[str, Any]]:
        """Get messages for a conversation."""
        pass
    
    @abstractmethod
    async def get_conversation_context(self, conversation_id: str, 
                                     format: str = 'string') -> Any:
        """Get the conversation context in the specified format."""
        pass
```

### 2. Consolidated Message Formatting

The consolidated message formatting will provide a common interface for formatting messages for different platforms.

```python
# konveyor/core/formatters/interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class FormatterInterface(ABC):
    """Interface for message formatting."""
    
    @abstractmethod
    def format_message(self, text: str, **kwargs) -> Dict[str, Any]:
        """Format a message for the target platform."""
        pass
    
    @abstractmethod
    def format_error(self, error: str, **kwargs) -> Dict[str, Any]:
        """Format an error message for the target platform."""
        pass
    
    @abstractmethod
    def format_list(self, items: List[str], **kwargs) -> Dict[str, Any]:
        """Format a list for the target platform."""
        pass
```

### 3. Unified Azure OpenAI Client

The unified Azure OpenAI client will provide a common interface for interacting with Azure OpenAI services.

```python
# konveyor/core/azure_utils/openai_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class OpenAIClientInterface(ABC):
    """Interface for Azure OpenAI client."""
    
    @abstractmethod
    async def generate_completion(self, messages: List[Dict[str, str]], 
                                temperature: float = 0.7, 
                                max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Generate a completion from the given messages."""
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for the given text."""
        pass
    
    @abstractmethod
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a model."""
        pass
```

### 4. Integrated Response Generation

The integrated response generation will provide a common interface for generating responses, with support for both RAG and direct generation.

```python
# konveyor/core/generation/interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class ResponseGeneratorInterface(ABC):
    """Interface for response generation."""
    
    @abstractmethod
    async def generate_response(self, query: str, 
                              context: Optional[str] = None,
                              conversation_id: Optional[str] = None,
                              use_rag: bool = False,
                              **kwargs) -> Dict[str, Any]:
        """Generate a response for the given query."""
        pass
    
    @abstractmethod
    async def generate_with_rag(self, query: str,
                              conversation_id: Optional[str] = None,
                              **kwargs) -> Dict[str, Any]:
        """Generate a response using RAG."""
        pass
    
    @abstractmethod
    async def generate_direct(self, query: str,
                            context: Optional[str] = None,
                            conversation_id: Optional[str] = None,
                            **kwargs) -> Dict[str, Any]:
        """Generate a response directly without RAG."""
        pass
```

## Timeline

- **Phase 1**: 1 week
- **Phase 2**: 2 weeks
- **Phase 3**: 2 weeks
- **Phase 4**: 1 week

Total estimated time: 6 weeks

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Breaking existing functionality | High | Medium | Implement changes incrementally with thorough testing |
| Performance degradation | Medium | Low | Profile code before and after changes |
| Increased complexity | Medium | Medium | Ensure clear documentation and interfaces |
| Resistance to change | Medium | Low | Communicate benefits and involve stakeholders |
| Timeline slippage | Medium | Medium | Build in buffer time and prioritize tasks |

## Success Criteria

1. All redundant code is consolidated
2. All tests pass
3. No regression in functionality
4. Code is well-documented
5. Performance is maintained or improved

## Conclusion

This consolidation plan provides a systematic approach to addressing the redundancies identified in the analysis. By following this plan, we can improve the codebase's maintainability, extensibility, and overall quality while preserving existing functionality.
