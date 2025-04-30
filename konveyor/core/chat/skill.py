"""
ChatSkill for Konveyor.

This skill provides chat-related functionality using Azure OpenAI,
including question answering, conversation handling, and basic utility functions.
It combines both chat capabilities and basic demonstration functions.

This updated version uses the new core components for conversation management,
message formatting, and response generation.
"""

import logging
import traceback
from typing import List, Dict, Any, Optional
from semantic_kernel.functions import kernel_function
from semantic_kernel import Kernel

from konveyor.core.conversation.factory import ConversationManagerFactory
from konveyor.core.formatters.factory import FormatterFactory
from konveyor.core.generation.factory import ResponseGeneratorFactory
from konveyor.core.kernel import create_kernel

logger = logging.getLogger(__name__)


class ChatSkill:
    """
    A skill for handling chat interactions with users.

    This skill provides functions for answering questions, maintaining
    conversation context, and basic utility functions. It's designed to be
    used with Slack or other chat interfaces and includes demonstration
    functions that show how Semantic Kernel skills work.

    This updated version uses the new core components for conversation management,
    message formatting, and response generation.
    """

    def __init__(self, kernel: Optional[Kernel] = None):
        """
        Initialize the ChatSkill.

        Args:
            kernel: Optional Semantic Kernel instance. If not provided, one will be created.
        """
        self.kernel = kernel if kernel is not None else self._create_kernel()

        # Initialize the conversation manager
        self.conversation_manager = None
        # Use a synchronous initialization for the conversation manager
        self._init_conversation_manager_sync()

        # Initialize the formatter
        self.formatter = FormatterFactory.get_formatter("slack")

        # Initialize the response generator
        self.response_generator = None
        self._init_response_generator()

        logger.info("ChatSkill initialized with new core components")

    def _create_kernel(self) -> Kernel:
        """
        Create a new kernel instance if one wasn't provided.

        Returns:
            Kernel: A configured Semantic Kernel instance
        """
        try:
            # Create a kernel with validation disabled to prevent errors during initialization
            kernel = create_kernel(validate=False)
            logger.info("Created new kernel instance for ChatSkill")
            return kernel
        except Exception as e:
            logger.error(f"Failed to create kernel: {str(e)}")
            logger.error(traceback.format_exc())
            # Return a minimal kernel without services as a fallback
            return Kernel()

    def _init_conversation_manager_sync(self):
        """Initialize the conversation manager synchronously."""
        try:
            # Use a simple in-memory conversation manager for synchronous initialization
            from konveyor.core.conversation.memory import InMemoryConversationManager

            self.conversation_manager = InMemoryConversationManager()
            logger.info("Initialized in-memory conversation manager synchronously")
        except Exception as e:
            logger.error(
                f"Failed to initialize conversation manager synchronously: {str(e)}"
            )
            logger.error(traceback.format_exc())

    async def _init_conversation_manager(self):
        """Initialize the conversation manager asynchronously."""
        try:
            self.conversation_manager = await ConversationManagerFactory.create_manager(
                "memory"
            )
            logger.info("Initialized conversation manager asynchronously")
        except Exception as e:
            logger.error(
                f"Failed to initialize conversation manager asynchronously: {str(e)}"
            )
            logger.error(traceback.format_exc())

    def _init_response_generator(self):
        """Initialize the response generator."""
        try:
            # Configure the response generator with the conversation manager
            # Only pass the conversation manager if it's initialized
            config = {}
            if self.conversation_manager:
                config["conversation_service"] = self.conversation_manager

            self.response_generator = ResponseGeneratorFactory.get_generator(
                "chat", config
            )
            logger.info("Initialized response generator")
        except Exception as e:
            logger.error(f"Failed to initialize response generator: {str(e)}")
            logger.error(traceback.format_exc())

    @kernel_function(
        description="Answer a question using Azure OpenAI", name="answer_question"
    )
    async def answer_question(
        self,
        question: str,
        context: Optional[str] = None,
        system_message: Optional[str] = None,
    ) -> str:
        """
        Answer a question using Azure OpenAI.

        Args:
            question: The question to answer
            context: Optional context to help answer the question
            system_message: System message to guide the AI's behavior

        Returns:
            The answer to the question
        """
        logger.info(f"Answering question: {question[:50]}...")

        if not question:
            return "I need a question to answer. Please provide one."

        # Log the context length if provided
        if context:
            logger.info(f"Context provided with length: {len(context)}")

        try:
            # Use the response generator to generate a response
            if self.response_generator:
                # Prepare additional options
                options = {}
                if system_message:
                    options["system_message"] = system_message

                # Generate the response
                response_data = await self.response_generator.generate_response(
                    query=question, context=context, use_rag=False, **options
                )

                return response_data.get(
                    "response", "I'm sorry, I couldn't generate a response."
                )

            # Fall back to the kernel if the response generator is not available
            logger.warning("Response generator not available, falling back to kernel")

            # Get the chat service from the kernel
            chat_service = self.kernel.get_service("chat")

            if not chat_service:
                logger.warning("No chat service available in kernel")
                return "I'm sorry, I'm currently experiencing connectivity issues with my AI backend. The team is working on resolving this. Please try again later."

            # Prepare messages for the chat service
            messages = []

            # Add system message if provided
            if system_message:
                messages.append({"role": "system", "content": system_message})
            else:
                # Default system message
                messages.append(
                    {
                        "role": "system",
                        "content": "You are a helpful assistant for the Konveyor project. Provide clear, concise, and accurate responses.",
                    }
                )

            # Add context as a system message if provided
            if context:
                messages.append(
                    {"role": "system", "content": f"Previous conversation: {context}"}
                )

            # Add the user's question
            messages.append({"role": "user", "content": question})

            # Call the chat service
            try:
                # Based on the documentation at:
                # https://learn.microsoft.com/en-us/semantic-kernel/concepts/ai-services/chat-completion/?tabs=csharp-AzureOpenAI%2Cpython-AzureOpenAI%2Cjava-AzureOpenAI&pivots=programming-language-python

                # Convert our messages to the proper format
                from semantic_kernel.contents import (
                    ChatMessageContent,
                    AuthorRole,
                    ChatHistory,
                )

                # Create a ChatHistory object
                chat_history = ChatHistory()

                # Add messages to the chat history
                for msg in messages:
                    role = (
                        AuthorRole.USER
                        if msg["role"] == "user"
                        else (
                            AuthorRole.SYSTEM
                            if msg["role"] == "system"
                            else AuthorRole.ASSISTANT
                        )
                    )
                    chat_message = ChatMessageContent(role=role, content=msg["content"])
                    chat_history.add_message(chat_message)

                # Create execution settings
                settings = chat_service.get_prompt_execution_settings_class()()

                # Use asyncio to run the async method in a synchronous context
                import asyncio

                async def get_completion():
                    result = await chat_service.get_chat_message_content(
                        chat_history, settings
                    )
                    return result

                # Since we're in an async function, we can just await the coroutine directly
                response = await get_completion()

                # Return the content
                return response.content

            except Exception as e:
                logger.error(f"Error calling chat service: {str(e)}")
                logger.error(traceback.format_exc())

                # Simple error message without hardcoded responses
                return "I encountered an error while connecting to the AI service. Please try again later."

        except Exception as e:
            logger.error(f"Error in answer_question: {str(e)}")
            logger.error(traceback.format_exc())
            return f"I encountered an error while processing your question. Please try again later."

    @kernel_function(
        description="Process a message in the context of a conversation", name="chat"
    )
    async def chat(
        self, message: str, conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a message in the context of a conversation.

        Args:
            message: The user's message
            conversation_id: Optional conversation identifier

        Returns:
            Dict containing the response and updated conversation details
        """
        logger.info(f"Processing chat message: {message[:50]}...")

        try:
            # Create a new conversation if needed
            if not conversation_id and self.conversation_manager:
                conversation = await self.conversation_manager.create_conversation()
                conversation_id = conversation["id"]
                logger.debug(f"Created new conversation: {conversation_id}")

            # Get conversation context if available
            context = None
            if conversation_id and self.conversation_manager:
                try:
                    context = await self.conversation_manager.get_conversation_context(
                        conversation_id=conversation_id, format="string"
                    )
                    logger.debug(
                        f"Retrieved conversation context with length: {len(context) if context else 0}"
                    )
                except Exception as e:
                    logger.error(f"Error retrieving conversation context: {str(e)}")

            # Use the response generator to generate a response
            if self.response_generator:
                # Generate the response
                response_data = await self.response_generator.generate_response(
                    query=message,
                    context=context,
                    conversation_id=conversation_id,
                    use_rag=False,
                    template_type="chat",
                )

                response = response_data.get(
                    "response", "I'm sorry, I couldn't generate a response."
                )
            else:
                # Fall back to the answer_question method
                logger.warning(
                    "Response generator not available, falling back to answer_question"
                )
                response = await self.answer_question(message, context=context)

                # Store in conversation history if available
                if conversation_id and self.conversation_manager:
                    try:
                        # Add user message
                        await self.conversation_manager.add_message(
                            conversation_id=conversation_id,
                            content=message,
                            message_type="user",
                        )

                        # Add assistant message
                        await self.conversation_manager.add_message(
                            conversation_id=conversation_id,
                            content=response,
                            message_type="assistant",
                        )
                    except Exception as e:
                        logger.error(f"Error updating conversation history: {str(e)}")

            return {
                "response": response,
                "conversation_id": conversation_id,
                "skill_name": "ChatSkill",
                "function_name": "chat",
                "success": True,
            }
        except Exception as e:
            logger.error(f"Error in chat function: {str(e)}")
            error_response = "I encountered an error while processing your message. Please try again later."

            return {
                "response": error_response,
                "conversation_id": conversation_id,
                "skill_name": "ChatSkill",
                "function_name": "chat",
                "success": False,
                "error": str(e),
            }

    def format_for_slack(
        self, text: str, include_blocks: bool = True
    ) -> Dict[str, Any]:
        """
        Format a response for Slack, handling Markdown conversion and creating blocks.

        Args:
            text: The text to format
            include_blocks: Whether to include rich formatting blocks

        Returns:
            Dictionary with text and blocks for Slack
        """
        # Use the Slack formatter
        if self.formatter:
            try:
                return self.formatter.format_message(
                    text=text, include_blocks=include_blocks
                )
            except Exception as e:
                logger.error(f"Error using formatter: {str(e)}")
                logger.error(traceback.format_exc())

        # Fall back to the original implementation if formatter is not available
        logger.warning(
            "Formatter not available, falling back to original implementation"
        )

        # Basic text formatting
        formatted_text = text

        # Create blocks for rich formatting if requested
        blocks = []
        if include_blocks:
            # Split text into sections based on headers
            sections = []
            current_section = ""

            for line in text.split("\n"):
                if (
                    line.startswith("# ")
                    or line.startswith("## ")
                    or line.startswith("### ")
                ):
                    # If we have content in the current section, add it
                    if current_section.strip():
                        sections.append(current_section.strip())
                    # Start a new section with the header
                    current_section = line + "\n"
                else:
                    # Add line to current section
                    current_section += line + "\n"

            # Add the last section if it has content
            if current_section.strip():
                sections.append(current_section.strip())

            # Create blocks for each section
            for section in sections:
                lines = section.split("\n")

                # Check if the first line is a header
                if (
                    lines[0].startswith("# ")
                    or lines[0].startswith("## ")
                    or lines[0].startswith("### ")
                ):
                    # Add a header block
                    header_text = lines[0].lstrip("#").strip()
                    blocks.append(
                        {
                            "type": "header",
                            "text": {"type": "plain_text", "text": header_text},
                        }
                    )

                    # Add the rest as a section
                    if len(lines) > 1:
                        section_text = "\n".join(lines[1:])
                        blocks.append(
                            {
                                "type": "section",
                                "text": {"type": "mrkdwn", "text": section_text},
                            }
                        )
                else:
                    # Add the whole section as a section block
                    blocks.append(
                        {"type": "section", "text": {"type": "mrkdwn", "text": section}}
                    )

                # Add a divider between sections
                blocks.append({"type": "divider"})

            # Remove the last divider
            if blocks and blocks[-1]["type"] == "divider":
                blocks.pop()

        return {"text": formatted_text, "blocks": blocks if include_blocks else None}

    @kernel_function(description="Greet a person by name", name="greet")
    async def greet(self, name: str = "there") -> str:
        """
        Greet a person by name.

        Args:
            name: The name of the person to greet (defaults to "there")

        Returns:
            A greeting message
        """
        logger.info(f"Greeting user: {name}")

        # Create a friendly greeting message
        greeting = f"Hello, {name}! Welcome to Konveyor. How can I help you today?"

        return greeting

    def format_as_bullet_list(self, text: str) -> str:
        """
        Format a newline-separated text as a bullet point list.

        Args:
            text: The text to format, with items separated by newlines

        Returns:
            A bullet point list
        """
        logger.info(f"Formatting text as bullet list: {text[:30]}...")
        lines = text.strip().split("\n")
        return "\n".join([f"• {line.strip()}" for line in lines if line.strip()])
