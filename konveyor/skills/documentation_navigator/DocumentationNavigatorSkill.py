"""
Documentation Navigator Skill for Konveyor.

This skill wraps the existing SearchService for documentation search and retrieval,
providing natural language query preprocessing and response formatting.
It also integrates with the conversation memory system to maintain context
across interactions.
"""

import asyncio
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

from konveyor.apps.search.services.search_service import SearchService
from konveyor.core.conversation.factory import ConversationManagerFactory
from konveyor.core.conversation.interface import ConversationInterface

# Configure logging
logger = logging.getLogger(__name__)


class DocumentationNavigatorSkill:
    """
    A skill for searching and navigating documentation.

    This skill wraps the existing SearchService to provide documentation search
    and retrieval capabilities, with additional features for query preprocessing,
    response formatting, and citation handling. It also integrates with the
    conversation memory system to maintain context across interactions.

    Attributes:
        search_service (SearchService): The search service for documentation retrieval
        kernel (Optional[Kernel]): The Semantic Kernel instance (if provided)
        conversation_manager (Optional[ConversationInterface]): The conversation manager for memory
    """

    def __init__(self, kernel: Optional[Kernel] = None):
        """
        Initialize the Documentation Navigator Skill.

        Args:
            kernel: Optional Semantic Kernel instance for memory integration
        """
        logger.info("Initializing DocumentationNavigatorSkill")
        self.search_service = SearchService()
        self.kernel = kernel
        self.conversation_manager = None
        self._init_conversation_manager()
        logger.info("DocumentationNavigatorSkill initialized successfully")

    def _init_conversation_manager(self):
        """Initialize the conversation manager."""
        try:
            # Use the factory to create a conversation manager
            # Note: We're not awaiting the coroutine here, but we'll await it when needed
            self.conversation_manager = ConversationManagerFactory.create_manager
            logger.info("Initialized conversation manager")
        except Exception as e:
            logger.warning(f"Failed to initialize conversation manager: {str(e)}")
            logger.warning(
                "Continuing without conversation memory - contextual conversations will be limited"
            )

            # Fallback to in-memory conversation manager
            try:
                from konveyor.core.conversation.memory import \
                    InMemoryConversationManager

                self.conversation_manager = lambda: InMemoryConversationManager()
                logger.info("Initialized fallback in-memory conversation manager")
            except Exception as e2:
                logger.error(
                    f"Failed to initialize fallback conversation manager: {str(e2)}"
                )
                self.conversation_manager = None

    async def _get_conversation_manager(self):
        """Get or create the conversation manager."""
        if (
            not hasattr(self, "_conversation_manager_instance")
            or self._conversation_manager_instance is None
        ):
            if self.conversation_manager:
                try:
                    self._conversation_manager_instance = (
                        await self.conversation_manager()
                    )
                except Exception as e:
                    logger.error(f"Error creating conversation manager: {str(e)}")
                    self._conversation_manager_instance = None
            else:
                self._conversation_manager_instance = None
        return self._conversation_manager_instance

    @kernel_function(
        description="Search documentation for information", name="search_documentation"
    )
    async def search_documentation(self, query: str, top: int = 5) -> Dict[str, Any]:
        """
        Search documentation for information related to the query.

        Args:
            query: The search query
            top: Maximum number of results to return

        Returns:
            Dictionary containing search results and metadata
        """
        logger.info(f"Searching documentation for: {query}")

        # Preprocess the query
        processed_query = self._preprocess_query(query)
        logger.info(f"Processed query: {processed_query}")

        try:
            # Perform search using the SearchService
            results = self.search_service.hybrid_search(
                query=processed_query, top=top, load_full_content=True
            )

            logger.info(f"Found {len(results)} results")

            # Format the results
            formatted_results = self._format_results(results)

            return {
                "original_query": query,
                "processed_query": processed_query,
                "results": formatted_results,
                "result_count": len(results),
                "success": True,
            }
        except Exception as e:
            logger.error(f"Error searching documentation: {str(e)}")
            return {
                "original_query": query,
                "processed_query": processed_query,
                "results": [],
                "result_count": 0,
                "error": str(e),
                "success": False,
            }

    @kernel_function(
        description="Answer a question using documentation", name="answer_question"
    )
    async def answer_question(
        self, question: str, top: int = 5, conversation_id: Optional[str] = None
    ) -> str:
        """
        Answer a question using documentation search.

        Args:
            question: The question to answer
            top: Maximum number of search results to use
            conversation_id: Optional conversation identifier for context

        Returns:
            Formatted answer with citations
        """
        logger.info(f"Answering question: {question}")

        # Search for relevant documentation
        search_results = await self.search_documentation(question, top)

        if not search_results["success"] or search_results["result_count"] == 0:
            logger.warning(f"No results found for question: {question}")
            return "I couldn't find any relevant information to answer your question. Could you please rephrase or ask something else?"

        # Format the answer with citations
        answer = self._format_answer_with_citations(question, search_results["results"])

        # Store in conversation history if available
        if conversation_id:
            try:
                # Get the conversation manager
                conversation_manager = await self._get_conversation_manager()

                if conversation_manager:
                    # Add user message
                    await conversation_manager.add_message(
                        conversation_id=conversation_id,
                        content=question,
                        message_type="user",
                    )

                    # Add assistant message
                    await conversation_manager.add_message(
                        conversation_id=conversation_id,
                        content=answer,
                        message_type="assistant",
                        metadata={
                            "search_results": search_results["results"],
                            "result_count": search_results["result_count"],
                            "query": question,
                        },
                    )
                    logger.info(f"Added Q&A to conversation history: {conversation_id}")
            except Exception as e:
                logger.error(f"Error updating conversation history: {str(e)}")

        return answer

    @kernel_function(
        description="Format search results in Slack-compatible Markdown",
        name="format_for_slack",
    )
    async def format_for_slack(
        self, query: str, top: int = 5, conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search documentation and format results in Slack-compatible Markdown.

        Args:
            query: The search query
            top: Maximum number of results to return
            conversation_id: Optional conversation identifier for context

        Returns:
            Dictionary with text and blocks for Slack
        """
        logger.info(f"Formatting search results for Slack: {query}")

        # Search for relevant documentation
        search_results = await self.search_documentation(query, top)

        if not search_results["success"] or search_results["result_count"] == 0:
            logger.warning(f"No results found for query: {query}")

            # Store in conversation history if available
            if conversation_id:
                try:
                    # Get the conversation manager
                    conversation_manager = await self._get_conversation_manager()

                    if conversation_manager:
                        await conversation_manager.add_message(
                            conversation_id=conversation_id,
                            content=query,
                            message_type="user",
                        )

                        await conversation_manager.add_message(
                            conversation_id=conversation_id,
                            content="I couldn't find any relevant information. Could you please rephrase your query?",
                            message_type="assistant",
                        )
                except Exception as e:
                    logger.error(f"Error updating conversation history: {str(e)}")

            return {
                "text": "I couldn't find any relevant information. Could you please rephrase your query?",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "I couldn't find any relevant information. Could you please rephrase your query?",
                        },
                    }
                ],
            }

        # Format the results for Slack
        slack_blocks = self._format_slack_blocks(query, search_results["results"])
        slack_text = self._format_slack_text(query, search_results["results"])

        # Store in conversation history if available
        if conversation_id:
            try:
                # Get the conversation manager
                conversation_manager = await self._get_conversation_manager()

                if conversation_manager:
                    # Add user message
                    await conversation_manager.add_message(
                        conversation_id=conversation_id,
                        content=query,
                        message_type="user",
                    )

                    # Add assistant message (using text version for simplicity)
                    await conversation_manager.add_message(
                        conversation_id=conversation_id,
                        content=slack_text,
                        message_type="assistant",
                        metadata={
                            "search_results": search_results["results"],
                            "result_count": search_results["result_count"],
                            "query": query,
                        },
                    )
                    logger.info(
                        f"Added search results to conversation history: {conversation_id}"
                    )
            except Exception as e:
                logger.error(f"Error updating conversation history: {str(e)}")

        return {"text": slack_text, "blocks": slack_blocks}

    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess the query to improve search results.

        This function applies several preprocessing steps to optimize the query:
        1. Identifies and enhances onboarding-related queries
        2. Removes question words and common filler words
        3. Identifies key concepts and adds relevant synonyms
        4. Preserves important technical terms

        Args:
            query: The original query

        Returns:
            Processed query
        """
        # Convert to lowercase
        processed = query.lower()

        # Detect and enhance onboarding-related questions
        onboarding_patterns = {
            "onboarding": [
                "onboarding process",
                "employee onboarding",
                "new hire",
                "orientation",
            ],
            "new employee": ["onboarding process", "first day", "getting started"],
            "getting started": ["onboarding", "setup guide", "initial steps"],
            "first day": ["onboarding", "orientation", "welcome"],
            "orientation": ["onboarding", "introduction", "welcome"],
            "setup": ["configuration", "installation", "environment setup"],
            "training": ["learning", "courses", "education", "onboarding"],
            "mentor": ["buddy", "coach", "onboarding support"],
            "benefits": ["employee benefits", "perks", "hr", "onboarding"],
            "handbook": ["employee handbook", "guide", "manual", "policies"],
        }

        # Check for onboarding-related patterns and enhance the query
        for keyword, enhancements in onboarding_patterns.items():
            if keyword in processed:
                # Add relevant terms to the query
                enhancement_text = " ".join(enhancements)
                processed = f"{processed} {enhancement_text}"
                logger.info(f"Enhanced onboarding query with terms: {enhancement_text}")
                break

        # Identify domain-specific terms to preserve
        technical_terms = [
            "api",
            "sdk",
            "cli",
            "ui",
            "ux",
            "git",
            "docker",
            "kubernetes",
            "k8s",
            "azure",
            "aws",
            "gcp",
            "cloud",
            "devops",
            "ci/cd",
            "pipeline",
            "semantic kernel",
            "llm",
            "openai",
            "gpt",
            "embedding",
            "vector",
            "database",
            "storage",
            "memory",
            "cache",
            "index",
            "search",
            "authentication",
            "authorization",
            "security",
            "encryption",
            "documentation",
            "markdown",
            "slack",
            "teams",
            "chat",
            "bot",
            "function",
            "method",
            "class",
            "object",
            "interface",
            "skill",
        ]

        # Remove question words and common filler words
        question_words = [
            "what",
            "how",
            "why",
            "when",
            "where",
            "who",
            "is",
            "are",
            "can",
            "could",
            "would",
            "should",
        ]
        filler_words = [
            "the",
            "a",
            "an",
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "by",
            "about",
            "like",
            "as",
            "of",
        ]

        # Only remove these words if they're standalone (not part of another word)
        words = processed.split()
        filtered_words = []

        for word in words:
            # Remove punctuation for comparison
            clean_word = re.sub(r"[^\w\s]", "", word)

            # Preserve technical terms
            if any(term == clean_word for term in technical_terms):
                filtered_words.append(word)
                continue

            # Filter out question words and filler words
            if clean_word not in question_words and clean_word not in filler_words:
                filtered_words.append(word)

        # If we've removed too many words, use the original query
        if len(filtered_words) < len(words) / 2:
            logger.info(f"Too many words removed, using original query: {query}")
            return query

        processed_query = " ".join(filtered_words)
        logger.info(f"Preprocessed query: '{query}' -> '{processed_query}'")
        return processed_query

    def _format_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format search results for presentation.

        Args:
            results: Raw search results from SearchService

        Returns:
            Formatted results
        """
        formatted = []

        for i, result in enumerate(results):
            # Extract relevant information
            document_id = result.get("document_id", "unknown")
            chunk_id = result.get("id", "unknown")
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            score = result.get("@search.score", 0)

            # Get document title from metadata
            title = metadata.get("title", f"Document {document_id}")

            # Format the result
            formatted_result = {
                "id": chunk_id,
                "document_id": document_id,
                "title": title,
                "content": content,
                "score": score,
                "citation": f"[{i+1}] {title}",
                "metadata": metadata,
            }

            formatted.append(formatted_result)

        return formatted

    def _format_answer_with_citations(
        self, question: str, results: List[Dict[str, Any]]
    ) -> str:
        """
        Format an answer with citations based on search results.

        Creates a well-structured response with inline citations and a
        dedicated sources section at the end. The formatting is optimized
        for readability in both plain text and Markdown renderers.

        Args:
            question: The original question
            results: Formatted search results

        Returns:
            Formatted answer with citations
        """
        if not results:
            return "I couldn't find any relevant information to answer your question."

        # Extract content and metadata from results
        contents = [result["content"] for result in results]
        titles = [result["title"] for result in results]
        citations = [result["citation"] for result in results]
        document_ids = [result["document_id"] for result in results]

        # Start with a clear introduction
        answer = (
            f"Based on the documentation, here's what I found about your question:\n\n"
        )

        # Add content with properly formatted citations
        for i, content in enumerate(contents):
            # Truncate content if too long, preserving sentence boundaries if possible
            if len(content) > 300:
                # Try to find the last sentence boundary within the first 300 chars
                last_period = content[:300].rfind(".")
                if (
                    last_period > 200
                ):  # Only use sentence boundary if it's not too short
                    content = content[: last_period + 1]
                else:
                    content = content[:300] + "..."

            # Format the citation as a superscript number
            citation_mark = f"[{i+1}]"

            # Add the content with citation
            answer += f"{content} {citation_mark}\n\n"

        # Add a horizontal rule before sources section
        answer += "---\n\n"

        # Add detailed sources section with document IDs and titles
        answer += "**Sources:**\n"
        for i, (title, doc_id) in enumerate(zip(titles, document_ids)):
            # Format each citation with number, title, and document ID
            answer += f"{i+1}. **{title}** (Document ID: `{doc_id}`)\n"

        return answer

    def _format_slack_blocks(
        self, query: str, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format search results as Slack blocks.

        Creates a rich, interactive Slack message with properly formatted blocks
        including header, search results with citations, and contextual actions.
        The formatting follows Slack Block Kit best practices for readability
        and interaction.

        Args:
            query: The original query
            results: Formatted search results

        Returns:
            List of Slack blocks
        """
        blocks = []

        # Add header with search query and result count
        blocks.append(
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Search Results ({len(results)} found)",
                    "emoji": True,
                },
            }
        )

        # Add context block with the original query
        blocks.append(
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"*Query:* _{query}_"}],
            }
        )

        blocks.append({"type": "divider"})

        # Add results with rich formatting
        for i, result in enumerate(results):
            title = result["title"]
            content = result["content"]
            document_id = result["document_id"]
            score = result.get("score", 0)

            # Format score as percentage for display
            relevance = int(score * 100) if score <= 1 else int(score)
            relevance_str = f"{relevance}% relevant" if relevance > 0 else ""

            # Truncate content if too long, preserving sentence boundaries if possible
            if len(content) > 300:
                # Try to find the last sentence boundary within the first 300 chars
                last_period = content[:300].rfind(".")
                if (
                    last_period > 200
                ):  # Only use sentence boundary if it's not too short
                    content = content[: last_period + 1]
                else:
                    content = content[:300] + "..."

            # Add result section with title and content
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{i+1}. {title}*\n{content}"},
                }
            )

            # Add context block with metadata
            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Source:* Document ID: `{document_id}` {' | ' + relevance_str if relevance_str else ''}",
                        }
                    ],
                }
            )

            # Add action buttons for each result (if needed in the future)
            # blocks.append({
            #     "type": "actions",
            #     "elements": [
            #         {
            #             "type": "button",
            #             "text": {
            #                 "type": "plain_text",
            #                 "text": "View Full Document",
            #                 "emoji": True
            #             },
            #             "value": document_id
            #         }
            #     ]
            # })

            blocks.append({"type": "divider"})

        # Add a final context block with a helpful message
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "💡 _Ask follow-up questions for more details on any of these results._",
                    }
                ],
            }
        )

        return blocks

    @kernel_function(
        description="Continue a conversation with follow-up questions",
        name="continue_conversation",
    )
    async def continue_conversation(
        self, follow_up_question: str, conversation_id: str, top: int = 5
    ) -> str:
        """
        Continue a conversation with follow-up questions, using conversation history for context.

        Args:
            follow_up_question: The follow-up question
            conversation_id: The conversation identifier
            top: Maximum number of search results to use

        Returns:
            Formatted answer with citations
        """
        logger.info(
            f"Processing follow-up question: {follow_up_question} in conversation: {conversation_id}"
        )

        # Get the conversation manager
        conversation_manager = await self._get_conversation_manager()

        if not conversation_manager:
            logger.warning(
                "Conversation manager not available, treating as standalone question"
            )
            return await self.answer_question(follow_up_question, top, conversation_id)

        try:
            # Get conversation context
            context = await conversation_manager.get_conversation_context(
                conversation_id=conversation_id, format="string"
            )
            logger.info(
                f"Retrieved conversation context with length: {len(context) if context else 0}"
            )

            # Extract previous queries from conversation history
            previous_queries = []
            previous_results = []

            # Get messages as dictionaries
            messages = await conversation_manager.get_conversation_messages(
                conversation_id=conversation_id, include_metadata=True
            )

            # Extract queries and results from user and assistant messages
            for message in messages:
                if message["type"] == "user":
                    previous_queries.append(message["content"])
                elif message["type"] == "assistant" and "metadata" in message:
                    metadata = message.get("metadata", {})
                    if "search_results" in metadata:
                        previous_results.extend(metadata["search_results"])

            # Enhance the query with context from previous interactions
            enhanced_query = self._enhance_query_with_context(
                follow_up_question, previous_queries
            )
            logger.info(f"Enhanced query: {enhanced_query}")

            # Search for relevant documentation
            search_results = await self.search_documentation(enhanced_query, top)

            if not search_results["success"] or search_results["result_count"] == 0:
                logger.warning(f"No results found for enhanced query: {enhanced_query}")

                # Try with original query as fallback
                search_results = await self.search_documentation(
                    follow_up_question, top
                )

                if not search_results["success"] or search_results["result_count"] == 0:
                    logger.warning(
                        f"No results found for original query either: {follow_up_question}"
                    )

                    # Add to conversation history
                    await conversation_manager.add_message(
                        conversation_id=conversation_id,
                        content=follow_up_question,
                        message_type="user",
                    )

                    no_results_response = "I couldn't find any relevant information to answer your follow-up question. Could you please rephrase or ask something else?"

                    await conversation_manager.add_message(
                        conversation_id=conversation_id,
                        content=no_results_response,
                        message_type="assistant",
                    )

                    return no_results_response

            # Format the answer with citations
            answer = self._format_answer_with_citations(
                follow_up_question, search_results["results"]
            )

            # Add to conversation history
            await conversation_manager.add_message(
                conversation_id=conversation_id,
                content=follow_up_question,
                message_type="user",
            )

            await conversation_manager.add_message(
                conversation_id=conversation_id,
                content=answer,
                message_type="assistant",
                metadata={
                    "search_results": search_results["results"],
                    "result_count": search_results["result_count"],
                    "query": enhanced_query,
                    "original_query": follow_up_question,
                },
            )

            return answer

        except Exception as e:
            logger.error(f"Error processing follow-up question: {str(e)}")
            # Fallback to treating it as a standalone question
            return await self.answer_question(follow_up_question, top, conversation_id)

    @kernel_function(
        description="Create a new conversation", name="create_conversation"
    )
    async def create_conversation(
        self, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new conversation for contextual interactions.

        Args:
            user_id: Optional user identifier

        Returns:
            Dictionary with conversation details
        """
        logger.info(f"Creating new conversation for user: {user_id}")

        # Get the conversation manager
        conversation_manager = await self._get_conversation_manager()

        if not conversation_manager:
            logger.warning(
                "Conversation manager not available, returning dummy conversation ID"
            )
            return {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
            }

        try:
            # Create a new conversation
            conversation = await conversation_manager.create_conversation(
                user_id=user_id
            )
            logger.info(f"Created new conversation: {conversation['id']}")
            return conversation
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            # Return a dummy conversation ID
            return {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
            }

    def _enhance_query_with_context(
        self, query: str, previous_queries: List[str], max_previous: int = 2
    ) -> str:
        """
        Enhance a query with context from previous queries.

        Args:
            query: The current query
            previous_queries: List of previous queries
            max_previous: Maximum number of previous queries to consider

        Returns:
            Enhanced query
        """
        if not previous_queries:
            return query

        # Take the most recent queries (limited by max_previous)
        recent_queries = (
            previous_queries[-max_previous:]
            if len(previous_queries) > max_previous
            else previous_queries
        )

        # Extract key terms from previous queries
        key_terms = set()
        for prev_query in recent_queries:
            # Preprocess to get key terms
            processed = self._preprocess_query(prev_query)
            key_terms.update(processed.split())

        # Remove terms that are already in the current query
        current_terms = set(query.lower().split())
        additional_terms = key_terms - current_terms

        # Add the most relevant additional terms to the query
        if additional_terms:
            # Limit to 5 additional terms to avoid query explosion
            limited_terms = list(additional_terms)[:5]
            enhanced_query = f"{query} {' '.join(limited_terms)}"
            logger.info(
                f"Enhanced query with terms from previous queries: {limited_terms}"
            )
            return enhanced_query

        return query

    def _format_slack_text(self, query: str, results: List[Dict[str, Any]]) -> str:
        """
        Format search results as plain text for Slack.

        Creates a fallback plain text version of the search results for clients
        that don't support Block Kit or when blocks fail to render. This ensures
        the information is still accessible in a readable format.

        Args:
            query: The original query
            results: Formatted search results

        Returns:
            Formatted text
        """
        # Start with a clear header
        text = f"📚 Search Results ({len(results)} found)\n"
        text += f"Query: {query}\n"
        text += "─────────────────────────────\n\n"

        # Add each result with proper formatting
        for i, result in enumerate(results):
            title = result["title"]
            content = result["content"]
            document_id = result["document_id"]

            # Truncate content if too long, preserving sentence boundaries if possible
            if len(content) > 150:
                # Try to find the last sentence boundary within the first 150 chars
                last_period = content[:150].rfind(".")
                if (
                    last_period > 100
                ):  # Only use sentence boundary if it's not too short
                    content = content[: last_period + 1]
                else:
                    content = content[:150] + "..."

            # Format the result with title, content, and source
            text += f"{i+1}. {title}\n"
            text += f"{content}\n"
            text += f"Source: Document ID: {document_id}\n"
            text += "─────────────────────────────\n\n"

        # Add a helpful footer
        text += "💡 Ask follow-up questions for more details on any of these results."

        return text
