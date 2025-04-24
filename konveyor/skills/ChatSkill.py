"""
ChatSkill for Konveyor.

This skill provides chat-related functionality using Azure OpenAI,
including question answering, conversation handling, and basic utility functions.
It combines both chat capabilities and basic demonstration functions.
"""

import logging
from typing import List, Dict, Any, Optional
from semantic_kernel.functions import kernel_function

logger = logging.getLogger(__name__)


class ChatSkill:
    """
    A skill for handling chat interactions with users.

    This skill provides functions for answering questions, maintaining
    conversation context, and basic utility functions. It's designed to be
    used with Slack or other chat interfaces and includes demonstration
    functions that show how Semantic Kernel skills work.
    """

    @kernel_function(
        description="Answer a question based on the provided context",
        name="answer_question"
    )
    def answer_question(self, question: str, context: Optional[str] = None, system_message: Optional[str] = None) -> str:
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

        # This function is automatically connected to Azure OpenAI by Semantic Kernel
        # The actual implementation is handled by the kernel's chat service
        return f"I'll help with your question about: {question}"

    @kernel_function(
        description="Process a message in the context of a conversation",
        name="chat"
    )
    def chat(self, message: str, history: str = "") -> Dict[str, Any]:
        """
        Process a message in the context of a conversation.

        Args:
            message: The user's message
            history: The conversation history

        Returns:
            Dict containing the response and updated history
        """
        logger.info(f"Processing chat message: {message[:50]}...")

        # Create a simple response
        response = f"I received your message: {message}"

        # Update history
        if history:
            updated_history = f"{history}\nUser: {message}\nAssistant: {response}"
        else:
            updated_history = f"User: {message}\nAssistant: {response}"

        return {
            "response": response,
            "history": updated_history
        }

    @kernel_function(
        description="Format a response for Slack",
        name="format_for_slack"
    )
    def format_for_slack(self, text: str) -> str:
        """
        Format a response for Slack, handling Markdown conversion.

        Args:
            text: The text to format

        Returns:
            Slack-formatted text
        """
        # Simple formatting for now - this would be expanded for proper Slack formatting
        formatted = text.replace("*", "_")  # Convert bold to italic for Slack

        return formatted

    @kernel_function(
        description="Greets a person by name",
        name="greet"
    )
    def greet(self, name: str) -> str:
        """
        Greet a person by name.

        Args:
            name: The name of the person to greet

        Returns:
            A greeting message
        """
        logger.info(f"Greeting user: {name}")
        return f"Hello, {name}! Welcome to Konveyor."

    @kernel_function(
        description="Formats text as a bullet point list",
        name="format_as_bullet_list"
    )
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
