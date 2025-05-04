"""
Slack Message Formatters for Konveyor.

This module provides utilities for formatting messages for Slack,
including Markdown conversion, block creation, and other formatting operations.
"""

import logging
from typing import Any, Dict, List, Optional  # noqa: F401

logger = logging.getLogger(__name__)


def format_for_slack(text: str, include_blocks: bool = True) -> dict[str, Any]:
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


def format_as_bullet_list(text: str) -> str:
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


def create_error_blocks(error_message: str) -> list[dict[str, Any]]:
    """
    Create error message blocks for Slack.

    Args:
        error_message: The error message to display

    Returns:
        List of Slack blocks for the error message
    """
    return [
        {"type": "header", "text": {"type": "plain_text", "text": "Error"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": error_message}},
    ]
