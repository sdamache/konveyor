"""
Markdown formatter for Konveyor.

This module provides a Markdown implementation of the FormatterInterface.
It handles formatting messages in Markdown format for general use.
"""

import logging
from typing import Dict, Any, List, Optional

from konveyor.core.formatters.interface import FormatterInterface

logger = logging.getLogger(__name__)


class MarkdownFormatter(FormatterInterface):
    """
    Markdown implementation of the FormatterInterface.

    This class provides methods for formatting messages in Markdown format,
    which can be used for general purpose formatting or as a base for
    platform-specific formatters.
    """

    def format_message(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Format a message in Markdown.

        Args:
            text: The message text to format
            **kwargs: Additional formatting options
                - title: Optional title for the message

        Returns:
            Dictionary containing the formatted message
        """
        title = kwargs.get("title", "")

        # Format the message
        formatted_text = f"## {title}\n\n{text}" if title else text

        return {"text": formatted_text, "format": "markdown"}

    def format_error(self, error: str, **kwargs) -> Dict[str, Any]:
        """
        Format an error message in Markdown.

        Args:
            error: The error message to format
            **kwargs: Additional formatting options

        Returns:
            Dictionary containing the formatted error message
        """
        formatted_text = f"## Error\n\n{error}"

        return {"text": formatted_text, "format": "markdown", "is_error": True}

    def format_list(self, items: List[str], **kwargs) -> Dict[str, Any]:
        """
        Format a list in Markdown.

        Args:
            items: The list items to format
            **kwargs: Additional formatting options
                - title: Optional title for the list
                - ordered: Whether to use an ordered list (default: False)

        Returns:
            Dictionary containing the formatted list
        """
        title = kwargs.get("title", "")
        ordered = kwargs.get("ordered", False)

        # Format the list
        formatted_text = f"## {title}\n\n" if title else ""

        for i, item in enumerate(items, 1):
            if ordered:
                formatted_text += f"{i}. {item}\n"
            else:
                formatted_text += f"- {item}\n"

        return {"text": formatted_text, "format": "markdown"}

    def format_code(
        self, code: str, language: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Format code in Markdown.

        Args:
            code: The code to format
            language: The programming language of the code
            **kwargs: Additional formatting options
                - title: Optional title for the code block

        Returns:
            Dictionary containing the formatted code
        """
        title = kwargs.get("title", "")

        # Format the code block
        lang_spec = language if language else ""
        formatted_text = f"## {title}\n\n" if title else ""
        formatted_text += f"```{lang_spec}\n{code}\n```"

        return {"text": formatted_text, "format": "markdown", "language": language}

    def format_table(
        self, headers: List[str], rows: List[List[Any]], **kwargs
    ) -> Dict[str, Any]:
        """
        Format a table in Markdown.

        Args:
            headers: The table headers
            rows: The table rows
            **kwargs: Additional formatting options
                - title: Optional title for the table

        Returns:
            Dictionary containing the formatted table
        """
        title = kwargs.get("title", "")

        # Format the table
        formatted_text = f"## {title}\n\n" if title else ""

        # Add header row
        formatted_text += "| " + " | ".join(headers) + " |\n"

        # Add separator row
        formatted_text += "| " + " | ".join(["---"] * len(headers)) + " |\n"

        # Add data rows
        for row in rows:
            formatted_text += "| " + " | ".join(str(cell) for cell in row) + " |\n"

        return {"text": formatted_text, "format": "markdown"}

    def format_rich_message(
        self, blocks: List[Dict[str, Any]], **kwargs
    ) -> Dict[str, Any]:
        """
        Format a rich message in Markdown.

        Args:
            blocks: The message blocks
            **kwargs: Additional formatting options
                - title: Optional title for the message

        Returns:
            Dictionary containing the formatted rich message
        """
        title = kwargs.get("title", "")

        # Convert blocks to Markdown
        formatted_text = f"## {title}\n\n" if title else ""

        for block in blocks:
            block_type = block.get("type", "")

            if block_type == "header":
                formatted_text += f"## {block.get('text', '')}\n\n"

            elif block_type == "section":
                text = block.get("text", {}).get("text", "")
                formatted_text += f"{text}\n\n"

            elif block_type == "divider":
                formatted_text += "---\n\n"

            elif block_type == "code":
                language = block.get("language", "")
                code = block.get("text", "")
                formatted_text += f"```{language}\n{code}\n```\n\n"

        return {"text": formatted_text, "format": "markdown"}

    def parse_markdown(self, markdown: str, **kwargs) -> Dict[str, Any]:
        """
        Parse Markdown and return it as is.

        Args:
            markdown: The Markdown text to parse
            **kwargs: Additional parsing options

        Returns:
            Dictionary containing the parsed Markdown
        """
        return {"text": markdown, "format": "markdown"}
