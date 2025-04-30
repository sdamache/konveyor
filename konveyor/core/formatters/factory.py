"""
Formatter factory for Konveyor.

This module provides a factory for creating formatters based on the
specified format type.
"""

import logging
from typing import Dict, Any

from konveyor.core.formatters.interface import FormatterInterface
from konveyor.core.formatters.slack_formatter import SlackFormatter
from konveyor.core.formatters.markdown import MarkdownFormatter

logger = logging.getLogger(__name__)


class FormatterFactory:
    """
    Factory for creating formatters.

    This class provides methods for creating formatters based on the
    specified format type. It supports different output formats like
    Slack, Markdown, etc.
    """

    _formatters = {}

    @classmethod
    def get_formatter(cls, format_type: str) -> FormatterInterface:
        """
        Get a formatter for the specified format type.

        Args:
            format_type: Type of formatter to get ('slack', 'markdown')

        Returns:
            A formatter implementing the FormatterInterface

        Raises:
            ValueError: If the format type is not supported
        """
        # Check if we already have an instance of this formatter
        if format_type in cls._formatters:
            return cls._formatters[format_type]

        # Create a new formatter instance
        if format_type == "slack":
            logger.debug("Creating Slack formatter")
            formatter = SlackFormatter()
        elif format_type == "markdown":
            logger.debug("Creating Markdown formatter")
            formatter = MarkdownFormatter()
        else:
            logger.error(f"Unsupported format type: {format_type}")
            raise ValueError(f"Unsupported format type: {format_type}")

        # Cache the formatter instance
        cls._formatters[format_type] = formatter

        return formatter

    @classmethod
    def register_formatter(
        cls, format_type: str, formatter: FormatterInterface
    ) -> None:
        """
        Register a custom formatter.

        Args:
            format_type: Type of formatter to register
            formatter: The formatter instance

        Raises:
            ValueError: If the formatter does not implement FormatterInterface
        """
        if not isinstance(formatter, FormatterInterface):
            raise ValueError("Formatter must implement FormatterInterface")

        logger.debug(f"Registering custom formatter for {format_type}")
        cls._formatters[format_type] = formatter
