"""
ChatSkill for Konveyor.

This module provides a proxy import for the ChatSkill class,
which has been moved to konveyor.core.chat.skill.

**IMPORTANT: REDUNDANCY NOTICE**
This implementation has some overlapping functionality with the existing RAG implementation
in konveyor/apps/rag/ and konveyor/core/rag/. Specifically:

1. Conversation history management: Both this ChatSkill and the RAG implementation
   (via ConversationManager) handle conversation history.

2. Message formatting: Both implementations have functions for formatting messages.

3. Integration with Azure OpenAI: Both directly or indirectly use Azure OpenAI services.

Future work in Task #3 (Agent Orchestration) should consider consolidating these
implementations or clearly defining their boundaries.
"""

import logging
from konveyor.core.chat.skill import ChatSkill

# Configure logging
logger = logging.getLogger(__name__)
logger.info("Using ChatSkill from konveyor.core.chat.skill")
