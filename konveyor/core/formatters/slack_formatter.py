"""
Slack message formatter.

This module provides formatting utilities for Slack messages, including rich formatting
for code blocks, tables, and other technical content.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union  # noqa: F401

from konveyor.core.formatters.interface import FormatterInterface

# Configure logging
logger = logging.getLogger(__name__)


class SlackFormatter(FormatterInterface):
    """
    Formatter for Slack messages.

    This class provides methods to format messages for Slack, including rich formatting
    for code blocks, tables, and other technical content.
    """

    def __init__(self):
        """Initialize the Slack formatter."""

    def format_message(self, text: str, **kwargs) -> dict[str, Any]:
        """
        Format a message for Slack.

        Args:
            text: The message text to format
            **kwargs: Additional formatting options
                - include_blocks: Whether to include Block Kit blocks in the response
                - unfurl_links: Whether to unfurl links (default: False)
                - unfurl_media: Whether to unfurl media (default: True)

        Returns:
            A dictionary with the formatted message
        """
        include_blocks = kwargs.get("include_blocks", True)
        unfurl_links = kwargs.get("unfurl_links", False)
        unfurl_media = kwargs.get("unfurl_media", True)

        # Process the text for any special formatting
        processed_text = self._convert_markdown_to_slack(text)

        # Create response dictionary
        response = {
            "text": processed_text,
            "unfurl_links": unfurl_links,
            "unfurl_media": unfurl_media,
        }

        # If blocks are requested, generate them
        if include_blocks:
            blocks = self._create_blocks_from_text(processed_text)
            if blocks:
                response["blocks"] = blocks

        return response

    def format_error(self, error: str, **kwargs) -> dict[str, Any]:
        """
        Format an error message for Slack.

        Args:
            error: The error message to format
            **kwargs: Additional formatting options
                - include_blocks: Whether to include blocks (default: True)

        Returns:
            A dictionary with the formatted error message
        """
        include_blocks = kwargs.get("include_blocks", True)

        # Create response dictionary
        response = {"text": f"Error: {error}"}

        # Add blocks if requested
        if include_blocks:
            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "Error", "emoji": True},
                },
                {"type": "section", "text": {"type": "mrkdwn", "text": error}},
            ]
            response["blocks"] = blocks

        return response

    def format_code_block(
        self, code: str, language: str | None = None
    ) -> dict[str, Any]:
        """
        Format a code block for Slack with syntax highlighting.

        Args:
            code: The code to format
            language: The programming language for syntax highlighting

        Returns:
            A dictionary with the formatted code block
        """
        # Clean up the code (remove extra whitespace at beginning/end)
        code = code.strip()

        # Format the code with triple backticks and language for syntax highlighting
        # Make sure language is lowercase for better compatibility with Slack's syntax highlighting  # noqa: E501
        lang_tag = language.lower() if language else ""

        # Ensure we're using the correct language identifier for Slack
        # Map common language names to their Slack syntax highlighting equivalents
        lang_map = {
            "python": "python",
            "py": "python",
            "javascript": "javascript",
            "js": "javascript",
            "typescript": "typescript",
            "ts": "typescript",
            "java": "java",
            "csharp": "csharp",
            "cs": "csharp",
            "c#": "csharp",
            "cpp": "cpp",
            "c++": "cpp",
            "go": "go",
            "ruby": "ruby",
            "rust": "rust",
            "php": "php",
            "html": "html",
            "css": "css",
            "sql": "sql",
            "shell": "shell",
            "bash": "bash",
            "sh": "bash",
            "json": "json",
            "xml": "xml",
            "yaml": "yaml",
            "yml": "yaml",
            "markdown": "markdown",
            "md": "markdown",
        }

        # Use the mapped language if available
        if lang_tag and lang_tag in lang_map:
            lang_tag = lang_map[lang_tag]

        formatted_code = f"```{lang_tag}\n{code}\n```"

        # Create blocks for rich display
        blocks = [
            {"type": "section", "text": {"type": "mrkdwn", "text": formatted_code}}
        ]

        # If a language is specified, add a context block with the language
        if language:
            # Use a more readable language name for display
            display_lang = language.lower()
            # Map short language codes to full names for display
            display_lang_map = {
                "py": "python",
                "js": "javascript",
                "ts": "typescript",
                "cs": "csharp",
                "c#": "C#",
                "cpp": "C++",
                "sh": "shell",
                "md": "markdown",
                "yml": "yaml",
            }
            if display_lang in display_lang_map:
                display_lang = display_lang_map[display_lang]

            # Capitalize the first letter for better presentation
            display_lang = display_lang[0].upper() + display_lang[1:]

            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"*Language:* {display_lang}"}
                    ],
                }
            )

        return {"text": formatted_code, "blocks": blocks}

    def format_table(
        self, headers: list[str], rows: list[list[Any]], **kwargs
    ) -> dict[str, Any]:
        """
        Format a table for Slack.

        Args:
            headers: The table headers
            rows: The table rows
            **kwargs: Additional formatting options
                - title: Optional title for the table
                - include_blocks: Whether to include blocks (default: True)

        Returns:
            A dictionary with the formatted table
        """
        title = kwargs.get("title", "")
        include_blocks = kwargs.get("include_blocks", True)

        # Create a markdown table
        table_md = []

        # Add headers
        header_row = "| " + " | ".join(headers) + " |"
        table_md.append(header_row)

        # Add separator
        separator = "| " + " | ".join(["---"] * len(headers)) + " |"
        table_md.append(separator)

        # Add rows
        for row in rows:
            row_str = "| " + " | ".join(str(cell) for cell in row) + " |"
            table_md.append(row_str)

        # Join the table rows
        table_text = "\n".join(table_md)

        # Add title if provided
        if title:
            table_text = f"*{title}*\n\n{table_text}"

        # Create response dictionary
        response = {"text": table_text}

        # Add blocks if requested
        if include_blocks:
            blocks = []

            # Add title if provided
            if title:
                blocks.append(
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*{title}*"},
                    }
                )

            # Add table as a markdown block
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            table_text
                            if not title
                            else table_text.replace(f"*{title}*\n\n", "")
                        ),
                    },
                }
            )

            response["blocks"] = blocks

        return response

    def format_visualization(
        self, title: str, description: str, image_url: str | None = None
    ) -> dict[str, Any]:
        """
        Format a visualization for Slack.

        Args:
            title: The visualization title
            description: The visualization description
            image_url: Optional URL to an image

        Returns:
            A dictionary with the formatted visualization
        """
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": title, "emoji": True},
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": description}},
        ]

        # Add image if provided
        if image_url:
            blocks.append(
                {
                    "type": "image",
                    "title": {"type": "plain_text", "text": title},
                    "image_url": image_url,
                    "alt_text": title,
                }
            )

        return {"text": f"{title}: {description}", "blocks": blocks}

    def format_list(self, items: list[str], **kwargs) -> dict[str, Any]:
        """
        Format a list for Slack.

        Args:
            items: The list items to format
            **kwargs: Additional formatting options
                - title: Optional title for the list
                - include_blocks: Whether to include blocks (default: True)

        Returns:
            Dictionary containing the formatted list
        """
        title = kwargs.get("title", "")
        include_blocks = kwargs.get("include_blocks", True)

        # Format as text
        text = f"{title}\n" if title else ""
        for i, item in enumerate(items, 1):
            text += f"{i}. {item}\n"

        # Create response dictionary
        response = {"text": text}

        # Add blocks if requested
        if include_blocks:
            blocks = []

            # Add title if provided
            if title:
                blocks.append(
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*{title}*"},
                    }
                )

            # Add list items
            list_text = ""
            for item in items:
                list_text += f"• {item}\n"

            blocks.append(
                {"type": "section", "text": {"type": "mrkdwn", "text": list_text}}
            )

            response["blocks"] = blocks

        return response

    def format_code(
        self, code: str, language: str | None = None, **kwargs
    ) -> dict[str, Any]:
        """
        Format code for Slack with syntax highlighting.

        Args:
            code: The code to format
            language: The programming language of the code
            **kwargs: Additional formatting options
                - title: Optional title for the code block
                - include_blocks: Whether to include blocks (default: True)

        Returns:
            Dictionary containing the formatted code
        """
        title = kwargs.get("title", "")
        include_blocks = kwargs.get("include_blocks", True)

        # Clean up the code (remove extra whitespace at beginning/end)
        code = code.strip()

        # Format the code with triple backticks and language for syntax highlighting
        # Make sure language is lowercase for better compatibility with Slack's syntax highlighting  # noqa: E501
        lang_tag = language.lower() if language else ""

        # Ensure we're using the correct language identifier for Slack
        # Map common language names to their Slack syntax highlighting equivalents
        lang_map = {
            "python": "python",
            "py": "python",
            "javascript": "javascript",
            "js": "javascript",
            "typescript": "typescript",
            "ts": "typescript",
            "java": "java",
            "csharp": "csharp",
            "cs": "csharp",
            "c#": "csharp",
            "cpp": "cpp",
            "c++": "cpp",
            "go": "go",
            "ruby": "ruby",
            "rust": "rust",
            "php": "php",
            "html": "html",
            "css": "css",
            "sql": "sql",
            "shell": "shell",
            "bash": "bash",
            "sh": "bash",
            "json": "json",
            "xml": "xml",
            "yaml": "yaml",
            "yml": "yaml",
            "markdown": "markdown",
            "md": "markdown",
        }

        # Use the mapped language if available
        if lang_tag and lang_tag in lang_map:
            lang_tag = lang_map[lang_tag]

        text = (
            f"{title}\n```{lang_tag}\n{code}\n```"
            if title
            else f"```{lang_tag}\n{code}\n```"
        )

        # Create response dictionary
        response = {"text": text}

        # Add blocks if requested
        if include_blocks:
            blocks = []

            # Add title if provided
            if title:
                blocks.append(
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*{title}*"},
                    }
                )

            # Add code block
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"```{lang_tag}\n{code}\n```"},
                }
            )

            # If a language is specified, add a context block with the language
            if language:
                # Use a more readable language name for display
                display_lang = language.lower()
                # Map short language codes to full names for display
                display_lang_map = {
                    "py": "python",
                    "js": "javascript",
                    "ts": "typescript",
                    "cs": "csharp",
                    "c#": "C#",
                    "cpp": "C++",
                    "sh": "shell",
                    "md": "markdown",
                    "yml": "yaml",
                }
                if display_lang in display_lang_map:
                    display_lang = display_lang_map[display_lang]

                # Capitalize the first letter for better presentation
                display_lang = display_lang[0].upper() + display_lang[1:]

                blocks.append(
                    {
                        "type": "context",
                        "elements": [
                            {"type": "mrkdwn", "text": f"*Language:* {display_lang}"}
                        ],
                    }
                )

            response["blocks"] = blocks

        return response

    def format_rich_message(
        self, blocks: list[dict[str, Any]], **kwargs
    ) -> dict[str, Any]:
        """
        Format a rich message with custom blocks for Slack.

        Args:
            blocks: The message blocks
            **kwargs: Additional formatting options
                - text: Optional fallback text

        Returns:
            Dictionary containing the formatted rich message
        """
        text = kwargs.get("text", "This message contains rich content.")

        return {"text": text, "blocks": blocks}

    def parse_markdown(self, markdown: str, **kwargs) -> dict[str, Any]:
        """
        Parse Markdown and convert it to Slack format.

        Args:
            markdown: The Markdown text to parse
            **kwargs: Additional parsing options
                - include_blocks: Whether to include blocks (default: True)

        Returns:
            Dictionary containing the parsed and formatted message
        """
        include_blocks = kwargs.get("include_blocks", True)

        # Convert Markdown to Slack format
        slack_text = self._convert_markdown_to_slack(markdown)

        # Create response dictionary
        response = {"text": slack_text}

        # Add blocks if requested
        if include_blocks:
            blocks = self._create_blocks_from_text(markdown)
            if blocks:
                response["blocks"] = blocks

        return response

    def _convert_markdown_to_slack(self, text: str) -> str:
        """
        Convert Markdown formatting to Slack formatting.

        Args:
            text: The Markdown text to convert

        Returns:
            The text with Slack formatting
        """
        # Slack already supports most Markdown syntax, but we need to handle some edge cases  # noqa: E501

        # Replace triple backticks with single backticks for code blocks
        text = re.sub(r"```(\w*)\n(.*?)\n```", r"```\1\n\2\n```", text, flags=re.DOTALL)

        # Replace [text](url) with <url|text>
        text = re.sub(r"\[(.*?)\]\((.*?)\)", r"<\2|\1>", text)

        return text

    def _create_blocks_from_text(self, text: str) -> list[dict[str, Any]]:
        """
        Create Block Kit blocks from text.

        This method parses the text and creates appropriate Block Kit blocks,
        handling code blocks, tables, and other special formatting.

        Args:
            text: The text to parse

        Returns:
            A list of Block Kit blocks
        """
        blocks = []

        # Split the text into sections based on code blocks
        # This regex matches triple backtick code blocks with optional language
        code_block_pattern = r"```(?P<lang>\w*)\n(?P<code>[\s\S]*?)\n```"

        # Find all code blocks
        code_blocks = list(re.finditer(code_block_pattern, text))

        if not code_blocks:
            # If no code blocks, just add the text as a section
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})
            return blocks

        # Process text with code blocks
        last_end = 0
        for match in code_blocks:
            # Add text before the code block
            if match.start() > last_end:
                pre_text = text[last_end : match.start()]
                if pre_text.strip():
                    blocks.append(
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": pre_text},
                        }
                    )

            # Add the code block
            lang = match.group("lang")
            code = match.group("code")

            # Clean up the code (remove extra whitespace at beginning/end)
            code = code.strip()

            # Make sure language is lowercase for better compatibility with Slack's syntax highlighting  # noqa: E501
            lang_tag = lang.lower() if lang else ""

            # Ensure we're using the correct language identifier for Slack
            # Map common language names to their Slack syntax highlighting equivalents
            lang_map = {
                "python": "python",
                "py": "python",
                "javascript": "javascript",
                "js": "javascript",
                "typescript": "typescript",
                "ts": "typescript",
                "java": "java",
                "csharp": "csharp",
                "cs": "csharp",
                "c#": "csharp",
                "cpp": "cpp",
                "c++": "cpp",
                "go": "go",
                "ruby": "ruby",
                "rust": "rust",
                "php": "php",
                "html": "html",
                "css": "css",
                "sql": "sql",
                "shell": "shell",
                "bash": "bash",
                "sh": "bash",
                "json": "json",
                "xml": "xml",
                "yaml": "yaml",
                "yml": "yaml",
                "markdown": "markdown",
                "md": "markdown",
            }

            # Use the mapped language if available
            if lang_tag and lang_tag in lang_map:
                lang_tag = lang_map[lang_tag]

            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"```{lang_tag}\n{code}\n```"},
                }
            )

            # If a language is specified, add a context block with the language
            if lang:
                # Use a more readable language name for display
                display_lang = lang.lower()
                # Map short language codes to full names for display
                display_lang_map = {
                    "py": "python",
                    "js": "javascript",
                    "ts": "typescript",
                    "cs": "csharp",
                    "c#": "C#",
                    "cpp": "C++",
                    "sh": "shell",
                    "md": "markdown",
                    "yml": "yaml",
                }
                if display_lang in display_lang_map:
                    display_lang = display_lang_map[display_lang]

                # Capitalize the first letter for better presentation
                display_lang = display_lang[0].upper() + display_lang[1:]

                blocks.append(
                    {
                        "type": "context",
                        "elements": [
                            {"type": "mrkdwn", "text": f"*Language:* {display_lang}"}
                        ],
                    }
                )

            last_end = match.end()

        # Add any remaining text after the last code block
        if last_end < len(text):
            post_text = text[last_end:]
            if post_text.strip():
                blocks.append(
                    {"type": "section", "text": {"type": "mrkdwn", "text": post_text}}
                )

        return blocks
