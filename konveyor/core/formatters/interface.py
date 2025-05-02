"""
Message formatting interface for Konveyor.

This module defines the interface for message formatting, providing a common
contract for different implementations (Slack, Teams, Markdown, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union  # noqa: F401


class FormatterInterface(ABC):
    """
    Interface for message formatting.

    This interface defines the contract for formatting messages for different
    platforms and formats. Implementations can target specific platforms
    (Slack, Teams, etc.) while providing a consistent API.
    """

    @abstractmethod
    def format_message(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Format a message for the target platform.

        Args:
            text: The message text to format
            **kwargs: Additional formatting options

        Returns:
            Dictionary containing the formatted message
        """
        pass

    @abstractmethod
    def format_error(self, error: str, **kwargs) -> Dict[str, Any]:
        """
        Format an error message for the target platform.

        Args:
            error: The error message to format
            **kwargs: Additional formatting options

        Returns:
            Dictionary containing the formatted error message
        """
        pass

    @abstractmethod
    def format_list(self, items: List[str], **kwargs) -> Dict[str, Any]:
        """
        Format a list for the target platform.

        Args:
            items: The list items to format
            **kwargs: Additional formatting options

        Returns:
            Dictionary containing the formatted list
        """
        pass

    @abstractmethod
    def format_code(
        self, code: str, language: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Format code for the target platform.

        Args:
            code: The code to format
            language: The programming language of the code
            **kwargs: Additional formatting options

        Returns:
            Dictionary containing the formatted code
        """
        pass

    @abstractmethod
    def format_table(
        self, headers: List[str], rows: List[List[Any]], **kwargs
    ) -> Dict[str, Any]:
        """
        Format a table for the target platform.

        Args:
            headers: The table headers
            rows: The table rows
            **kwargs: Additional formatting options

        Returns:
            Dictionary containing the formatted table
        """
        pass

    @abstractmethod
    def format_rich_message(
        self, blocks: List[Dict[str, Any]], **kwargs
    ) -> Dict[str, Any]:
        """
        Format a rich message with custom blocks for the target platform.

        Args:
            blocks: The message blocks
            **kwargs: Additional formatting options

        Returns:
            Dictionary containing the formatted rich message
        """
        pass

    @abstractmethod
    def parse_markdown(self, markdown: str, **kwargs) -> Dict[str, Any]:
        """
        Parse Markdown and convert it to the target platform's format.

        Args:
            markdown: The Markdown text to parse
            **kwargs: Additional parsing options

        Returns:
            Dictionary containing the parsed and formatted message
        """
        pass
