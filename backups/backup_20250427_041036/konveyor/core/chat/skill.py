"""
ChatSkill for Konveyor.

This skill provides chat-related functionality using Azure OpenAI,
including question answering, conversation handling, and basic utility functions.
It combines both chat capabilities and basic demonstration functions.
"""

import logging
import traceback
from typing import List, Dict, Any, Optional
from semantic_kernel.functions import kernel_function
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from konveyor.core.kernel import create_kernel

logger = logging.getLogger(__name__)


class ChatSkill:
    """
    A skill for handling chat interactions with users.

    This skill provides functions for answering questions, maintaining
    conversation context, and basic utility functions. It's designed to be
    used with Slack or other chat interfaces and includes demonstration
    functions that show how Semantic Kernel skills work.
    """

    def __init__(self, kernel: Optional[Kernel] = None):
        """
        Initialize the ChatSkill.

        Args:
            kernel: Optional Semantic Kernel instance. If not provided, one will be created.
        """
        self.kernel = kernel if kernel is not None else self._create_kernel()
        logger.info("ChatSkill initialized with kernel")

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

    @kernel_function(
        description="Answer a question using Azure OpenAI",
        name="answer_question"
    )
    async def answer_question(self, question: str, context: Optional[str] = None, system_message: Optional[str] = None) -> str:
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
                messages.append({
                    "role": "system",
                    "content": "You are a helpful assistant for the Konveyor project. Provide clear, concise, and accurate responses."
                })

            # Add context as a system message if provided
            if context:
                messages.append({"role": "system", "content": f"Previous conversation: {context}"})

            # Add the user's question
            messages.append({"role": "user", "content": question})

            # Call the chat service
            try:
                # Based on the documentation at:
                # https://learn.microsoft.com/en-us/semantic-kernel/concepts/ai-services/chat-completion/?tabs=csharp-AzureOpenAI%2Cpython-AzureOpenAI%2Cjava-AzureOpenAI&pivots=programming-language-python

                # Convert our messages to the proper format
                from semantic_kernel.contents import ChatMessageContent, AuthorRole, ChatHistory

                # Create a ChatHistory object
                chat_history = ChatHistory()

                # Add messages to the chat history
                for msg in messages:
                    role = AuthorRole.USER if msg["role"] == "user" else AuthorRole.SYSTEM if msg["role"] == "system" else AuthorRole.ASSISTANT
                    chat_message = ChatMessageContent(
                        role=role,
                        content=msg["content"]
                    )
                    chat_history.add_message(chat_message)

                # Create execution settings
                settings = chat_service.get_prompt_execution_settings_class()()

                # Use asyncio to run the async method in a synchronous context
                import asyncio

                async def get_completion():
                    result = await chat_service.get_chat_message_content(chat_history, settings)
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
        description="Process a message in the context of a conversation",
        name="chat"
    )
    async def chat(self, message: str, history: str = "") -> Dict[str, Any]:
        """
        Process a message in the context of a conversation.

        Args:
            message: The user's message
            history: The conversation history

        Returns:
            Dict containing the response and updated history
        """
        logger.info(f"Processing chat message: {message[:50]}...")

        try:
            # Use the answer_question method to generate a response
            # In a real implementation, this would pass the history to provide context
            response = await self.answer_question(message, context=history)

            # Update history
            if history:
                updated_history = f"{history}\nUser: {message}\nAssistant: {response}"
            else:
                updated_history = f"User: {message}\nAssistant: {response}"

            return {
                "response": response,
                "history": updated_history,
                "skill_name": "ChatSkill",
                "function_name": "chat",
                "success": True
            }
        except Exception as e:
            logger.error(f"Error in chat function: {str(e)}")
            error_response = "I encountered an error while processing your message. Please try again later."

            # Update history even in case of error
            if history:
                updated_history = f"{history}\nUser: {message}\nAssistant: {error_response}"
            else:
                updated_history = f"User: {message}\nAssistant: {error_response}"

            return {
                "response": error_response,
                "history": updated_history,
                "skill_name": "ChatSkill",
                "function_name": "chat",
                "success": False,
                "error": str(e)
            }

    def format_for_slack(self, text: str, include_blocks: bool = True) -> Dict[str, Any]:
        """
        Format a response for Slack, handling Markdown conversion and creating blocks.

        Args:
            text: The text to format
            include_blocks: Whether to include rich formatting blocks

        Returns:
            Dictionary with text and blocks for Slack
        """
        # Basic text formatting
        formatted_text = text

        # Create blocks for rich formatting if requested
        blocks = []
        if include_blocks:
            # Split text into sections based on headers
            sections = []
            current_section = ""

            for line in text.split('\n'):
                if line.startswith('# ') or line.startswith('## ') or line.startswith('### '):
                    # If we have content in the current section, add it
                    if current_section.strip():
                        sections.append(current_section.strip())
                    # Start a new section with the header
                    current_section = line + '\n'
                else:
                    # Add line to current section
                    current_section += line + '\n'

            # Add the last section if it has content
            if current_section.strip():
                sections.append(current_section.strip())

            # Create blocks for each section
            for section in sections:
                lines = section.split('\n')

                # Check if the first line is a header
                if lines[0].startswith('# ') or lines[0].startswith('## ') or lines[0].startswith('### '):
                    # Add a header block
                    header_text = lines[0].lstrip('#').strip()
                    blocks.append({
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": header_text
                        }
                    })

                    # Add the rest as a section
                    if len(lines) > 1:
                        section_text = '\n'.join(lines[1:])
                        blocks.append({
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": section_text
                            }
                        })
                else:
                    # Add the whole section as a section block
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": section
                        }
                    })

                # Add a divider between sections
                blocks.append({
                    "type": "divider"
                })

            # Remove the last divider
            if blocks and blocks[-1]["type"] == "divider":
                blocks.pop()

        return {
            "text": formatted_text,
            "blocks": blocks if include_blocks else None
        }

    @kernel_function(
        description="Greet a person by name",
        name="greet"
    )
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
        lines = text.strip().split('\n')
        return '\n'.join([f"• {line.strip()}" for line in lines if line.strip()])
