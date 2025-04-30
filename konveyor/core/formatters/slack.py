"""
Slack message formatter for Konveyor.

This module provides a Slack-specific implementation of the FormatterInterface.
It handles formatting messages for Slack, including rich formatting with blocks.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from konveyor.core.formatters.interface import FormatterInterface

logger = logging.getLogger(__name__)


class SlackFormatter(FormatterInterface):
    """
    Slack-specific implementation of the FormatterInterface.

    This class provides methods for formatting messages for Slack, including
    rich formatting with blocks, code blocks, tables, and other Slack-specific
    formatting features.
    """

    def format_message(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Format a message for Slack.

        Args:
            text: The message text to format
            **kwargs: Additional formatting options
                - include_blocks: Whether to include blocks (default: True)
                - unfurl_links: Whether to unfurl links (default: False)
                - unfurl_media: Whether to unfurl media (default: True)

        Returns:
            Dictionary containing the formatted message
        """
        include_blocks = kwargs.get("include_blocks", True)
        unfurl_links = kwargs.get("unfurl_links", False)
        unfurl_media = kwargs.get("unfurl_media", True)

        # Basic text formatting (convert Markdown to Slack format)
        formatted_text = self._convert_markdown_to_slack(text)

        # Create response dictionary
        response = {
            "text": formatted_text,
            "unfurl_links": unfurl_links,
            "unfurl_media": unfurl_media,
        }

        # Add blocks if requested
        if include_blocks:
            blocks = self._create_blocks_from_text(text)
            if blocks:
                response["blocks"] = blocks

        return response

    def format_error(self, error: str, **kwargs) -> Dict[str, Any]:
        """
        Format an error message for Slack.

        Args:
            error: The error message to format
            **kwargs: Additional formatting options
                - include_blocks: Whether to include blocks (default: True)

        Returns:
            Dictionary containing the formatted error message
        """
        include_blocks = kwargs.get("include_blocks", True)

        # Create response dictionary
        response = {"text": f"Error: {error}"}

        # Add blocks if requested
        if include_blocks:
            blocks = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Error:* {error}"},
                }
            ]
            response["blocks"] = blocks

        return response

    def format_list(self, items: List[str], **kwargs) -> Dict[str, Any]:
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
        self, code: str, language: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Format code for Slack.

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

        # Format as text
        lang_spec = f"{language}" if language else ""
        text = f"{title}\n```{lang_spec}\n{code}\n```"

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
                    "text": {"type": "mrkdwn", "text": f"```{lang_spec}\n{code}\n```"},
                }
            )

            response["blocks"] = blocks

        return response

    def format_table(
        self, headers: List[str], rows: List[List[Any]], **kwargs
    ) -> Dict[str, Any]:
        """
        Format a table for Slack.

        Args:
            headers: The table headers
            rows: The table rows
            **kwargs: Additional formatting options
                - title: Optional title for the table
                - include_blocks: Whether to include blocks (default: True)

        Returns:
            Dictionary containing the formatted table
        """
        title = kwargs.get("title", "")
        include_blocks = kwargs.get("include_blocks", True)

        # Format as text (using fixed-width formatting)
        text = f"{title}\n" if title else ""

        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        # Add header row
        header_row = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        text += f"{header_row}\n"

        # Add separator row
        separator = " | ".join("-" * col_widths[i] for i in range(len(headers)))
        text += f"{separator}\n"

        # Add data rows
        for row in rows:
            data_row = " | ".join(
                str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)
            )
            text += f"{data_row}\n"

        # Create response dictionary
        response = {"text": f"```\n{text}\n```"}

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

            # Add table as a code block
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"```\n{text}\n```"},
                }
            )

            response["blocks"] = blocks

        return response

    def format_rich_message(
        self, blocks: List[Dict[str, Any]], **kwargs
    ) -> Dict[str, Any]:
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

    def parse_markdown(self, markdown: str, **kwargs) -> Dict[str, Any]:
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
        # Slack already supports most Markdown syntax, but we need to handle some edge cases

        # Replace triple backticks with single backticks for code blocks
        text = re.sub(r"```(\w*)\n(.*?)\n```", r"```\1\n\2\n```", text, flags=re.DOTALL)

        # Replace [text](url) with <url|text>
        text = re.sub(r"\[(.*?)\]\((.*?)\)", r"<\2|\1>", text)

        return text

    def _create_blocks_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Create Slack blocks from text.

        Args:
            text: The text to convert to blocks

        Returns:
            List of Slack blocks
        """
        blocks = []

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

        # Convert sections to blocks
        for section in sections:
            # Check if the section starts with a header
            if (
                section.startswith("# ")
                or section.startswith("## ")
                or section.startswith("### ")
            ):
                # Split the first line (header) from the rest
                lines = section.split("\n", 1)
                header = lines[0]
                content = lines[1] if len(lines) > 1 else ""

                # Add header as a section block
                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{header.lstrip('#').strip()}*",
                        },
                    }
                )

                # Add content as a section block if it exists
                if content.strip():
                    blocks.append(
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": content.strip()},
                        }
                    )
            else:
                # Add the entire section as a block
                blocks.append(
                    {"type": "section", "text": {"type": "mrkdwn", "text": section}}
                )

        # Add a divider at the end if there are multiple sections
        if len(sections) > 1:
            blocks.append({"type": "divider"})

        return blocks
