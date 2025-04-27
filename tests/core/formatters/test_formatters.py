"""
Tests for the formatter components.

This module contains tests for the formatter components,
including the SlackFormatter, MarkdownFormatter, and FormatterFactory.
"""

import pytest
from typing import Dict, Any, List

from konveyor.core.formatters.interface import FormatterInterface
from konveyor.core.formatters.slack import SlackFormatter
from konveyor.core.formatters.markdown import MarkdownFormatter
from konveyor.core.formatters.factory import FormatterFactory

def test_slack_formatter():
    """Test the SlackFormatter."""
    # Create a formatter
    formatter = SlackFormatter()
    
    # Test format_message
    message = formatter.format_message("Hello, world!")
    assert message is not None
    assert "text" in message
    assert message["text"] == "Hello, world!"
    assert "blocks" in message
    
    # Test format_message with include_blocks=False
    message = formatter.format_message("Hello, world!", include_blocks=False)
    assert message is not None
    assert "text" in message
    assert message["text"] == "Hello, world!"
    assert "blocks" not in message or message["blocks"] is None
    
    # Test format_error
    error = formatter.format_error("An error occurred")
    assert error is not None
    assert "text" in error
    assert "Error: An error occurred" in error["text"]
    assert "blocks" in error
    
    # Test format_list
    items = ["Item 1", "Item 2", "Item 3"]
    list_message = formatter.format_list(items, title="Test List")
    assert list_message is not None
    assert "text" in list_message
    assert "Test List" in list_message["text"]
    assert "Item 1" in list_message["text"]
    assert "blocks" in list_message
    
    # Test format_code
    code = "def hello_world():\n    print('Hello, world!')"
    code_message = formatter.format_code(code, language="python", title="Test Code")
    assert code_message is not None
    assert "text" in code_message
    assert "Test Code" in code_message["text"]
    assert "def hello_world()" in code_message["text"]
    assert "blocks" in code_message
    
    # Test format_table
    headers = ["Name", "Age", "City"]
    rows = [["Alice", 30, "New York"], ["Bob", 25, "San Francisco"]]
    table_message = formatter.format_table(headers, rows, title="Test Table")
    assert table_message is not None
    assert "text" in table_message
    assert "Test Table" in table_message["text"]
    assert "Name" in table_message["text"]
    assert "Alice" in table_message["text"]
    assert "blocks" in table_message
    
    # Test format_rich_message
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "Test Header"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "Test Section"}}
    ]
    rich_message = formatter.format_rich_message(blocks, text="Test Rich Message")
    assert rich_message is not None
    assert "text" in rich_message
    assert rich_message["text"] == "Test Rich Message"
    assert "blocks" in rich_message
    assert len(rich_message["blocks"]) == 2
    
    # Test parse_markdown
    markdown = "# Test Heading\n\nTest paragraph\n\n* Item 1\n* Item 2"
    parsed = formatter.parse_markdown(markdown)
    assert parsed is not None
    assert "text" in parsed
    assert "# Test Heading" in parsed["text"]
    assert "blocks" in parsed

def test_markdown_formatter():
    """Test the MarkdownFormatter."""
    # Create a formatter
    formatter = MarkdownFormatter()
    
    # Test format_message
    message = formatter.format_message("Hello, world!")
    assert message is not None
    assert "text" in message
    assert message["text"] == "Hello, world!"
    assert "format" in message
    assert message["format"] == "markdown"
    
    # Test format_message with title
    message = formatter.format_message("Hello, world!", title="Test Title")
    assert message is not None
    assert "text" in message
    assert "## Test Title" in message["text"]
    assert "Hello, world!" in message["text"]
    
    # Test format_error
    error = formatter.format_error("An error occurred")
    assert error is not None
    assert "text" in error
    assert "## Error" in error["text"]
    assert "An error occurred" in error["text"]
    assert "is_error" in error
    assert error["is_error"] is True
    
    # Test format_list
    items = ["Item 1", "Item 2", "Item 3"]
    list_message = formatter.format_list(items, title="Test List")
    assert list_message is not None
    assert "text" in list_message
    assert "## Test List" in list_message["text"]
    assert "- Item 1" in list_message["text"]
    
    # Test format_list with ordered=True
    list_message = formatter.format_list(items, title="Test List", ordered=True)
    assert list_message is not None
    assert "text" in list_message
    assert "## Test List" in list_message["text"]
    assert "1. Item 1" in list_message["text"]
    
    # Test format_code
    code = "def hello_world():\n    print('Hello, world!')"
    code_message = formatter.format_code(code, language="python", title="Test Code")
    assert code_message is not None
    assert "text" in code_message
    assert "## Test Code" in code_message["text"]
    assert "```python" in code_message["text"]
    assert "def hello_world()" in code_message["text"]
    
    # Test format_table
    headers = ["Name", "Age", "City"]
    rows = [["Alice", 30, "New York"], ["Bob", 25, "San Francisco"]]
    table_message = formatter.format_table(headers, rows, title="Test Table")
    assert table_message is not None
    assert "text" in table_message
    assert "## Test Table" in table_message["text"]
    assert "| Name | Age | City |" in table_message["text"]
    assert "| Alice | 30 | New York |" in table_message["text"]
    
    # Test format_rich_message
    blocks = [
        {"type": "header", "text": "Test Header"},
        {"type": "section", "text": {"text": "Test Section"}}
    ]
    rich_message = formatter.format_rich_message(blocks, title="Test Rich Message")
    assert rich_message is not None
    assert "text" in rich_message
    assert "## Test Rich Message" in rich_message["text"]
    
    # Test parse_markdown
    markdown = "# Test Heading\n\nTest paragraph\n\n* Item 1\n* Item 2"
    parsed = formatter.parse_markdown(markdown)
    assert parsed is not None
    assert "text" in parsed
    assert parsed["text"] == markdown
    assert "format" in parsed
    assert parsed["format"] == "markdown"

def test_formatter_factory():
    """Test the FormatterFactory."""
    # Get a Slack formatter
    slack_formatter = FormatterFactory.get_formatter("slack")
    assert slack_formatter is not None
    assert isinstance(slack_formatter, FormatterInterface)
    assert isinstance(slack_formatter, SlackFormatter)
    
    # Get a Markdown formatter
    markdown_formatter = FormatterFactory.get_formatter("markdown")
    assert markdown_formatter is not None
    assert isinstance(markdown_formatter, FormatterInterface)
    assert isinstance(markdown_formatter, MarkdownFormatter)
    
    # Test caching
    slack_formatter2 = FormatterFactory.get_formatter("slack")
    assert slack_formatter2 is slack_formatter
    
    # Test registering a custom formatter
    class CustomFormatter(FormatterInterface):
        def format_message(self, text: str, **kwargs) -> Dict[str, Any]:
            return {"text": f"Custom: {text}"}
        
        def format_error(self, error: str, **kwargs) -> Dict[str, Any]:
            return {"text": f"Custom Error: {error}"}
        
        def format_list(self, items: List[str], **kwargs) -> Dict[str, Any]:
            return {"text": f"Custom List: {', '.join(items)}"}
        
        def format_code(self, code: str, language: str = None, **kwargs) -> Dict[str, Any]:
            return {"text": f"Custom Code: {code}"}
        
        def format_table(self, headers: List[str], rows: List[List[Any]], **kwargs) -> Dict[str, Any]:
            return {"text": f"Custom Table: {headers}"}
        
        def format_rich_message(self, blocks: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
            return {"text": "Custom Rich Message"}
        
        def parse_markdown(self, markdown: str, **kwargs) -> Dict[str, Any]:
            return {"text": f"Custom Markdown: {markdown}"}
    
    custom_formatter = CustomFormatter()
    FormatterFactory.register_formatter("custom", custom_formatter)
    
    # Get the custom formatter
    custom_formatter2 = FormatterFactory.get_formatter("custom")
    assert custom_formatter2 is custom_formatter
    
    # Test the custom formatter
    message = custom_formatter2.format_message("Hello, world!")
    assert message is not None
    assert "text" in message
    assert message["text"] == "Custom: Hello, world!"
    
    # Test invalid formatter type
    with pytest.raises(ValueError):
        FormatterFactory.get_formatter("invalid")
    
    # Test invalid formatter registration
    with pytest.raises(ValueError):
        FormatterFactory.register_formatter("invalid", "not a formatter")

# Run the tests
if __name__ == "__main__":
    test_slack_formatter()
    test_markdown_formatter()
    test_formatter_factory()
