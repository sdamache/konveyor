"""
Tests for the Slack formatter.
"""

import pytest
from konveyor.core.formatters.slack_formatter import SlackFormatter


def test_format_message_simple():
    """Test formatting a simple message."""
    formatter = SlackFormatter()

    # Format a simple message
    result = formatter.format_message("Hello, world!")

    # Verify the result
    assert "text" in result
    assert result["text"] == "Hello, world!"
    assert "blocks" in result
    assert len(result["blocks"]) == 1
    assert result["blocks"][0]["type"] == "section"
    assert result["blocks"][0]["text"]["text"] == "Hello, world!"


def test_format_message_with_code_block():
    """Test formatting a message with a code block."""
    formatter = SlackFormatter()

    # Format a message with a code block
    message = "Here's some code:\n```python\ndef hello():\n    return 'Hello, world!'\n```\nThat's all!"
    result = formatter.format_message(message)

    # Verify the result
    assert "text" in result
    assert result["text"] == message
    assert "blocks" in result
    assert len(result["blocks"]) >= 3  # At least 3 blocks: text, code, text

    # Find the code block
    code_blocks = [block for block in result["blocks"]
                  if block["type"] == "section" and "```python" in block["text"]["text"]]
    assert len(code_blocks) == 1

    # Find the language context
    context_blocks = [block for block in result["blocks"] if block["type"] == "context"]
    assert len(context_blocks) == 1
    assert "Language" in context_blocks[0]["elements"][0]["text"]
    assert "python" in context_blocks[0]["elements"][0]["text"].lower()


def test_format_message_with_multiple_code_blocks():
    """Test formatting a message with multiple code blocks."""
    formatter = SlackFormatter()

    # Format a message with multiple code blocks
    message = """Here's some Python code:
```python
def hello():
    return 'Hello, world!'
```

And here's some JavaScript:
```javascript
function hello() {
    return 'Hello, world!';
}
```
"""
    result = formatter.format_message(message)

    # Verify the result
    assert "text" in result
    assert result["text"] == message
    assert "blocks" in result

    # Find the code blocks
    code_blocks = [block for block in result["blocks"]
                  if block["type"] == "section" and "```" in block["text"]["text"]]
    assert len(code_blocks) == 2

    # Find the language contexts
    context_blocks = [block for block in result["blocks"] if block["type"] == "context"]
    assert len(context_blocks) == 2

    # Verify languages
    languages = [block["elements"][0]["text"].lower() for block in context_blocks]
    assert any("python" in lang for lang in languages)
    assert any("javascript" in lang for lang in languages)


def test_format_error():
    """Test formatting an error message."""
    formatter = SlackFormatter()

    # Format an error message
    result = formatter.format_error("Something went wrong")

    # Verify the result
    assert "text" in result
    assert "Error" in result["text"]
    assert "Something went wrong" in result["text"]
    assert "blocks" in result
    assert len(result["blocks"]) == 2  # Header and message
    assert result["blocks"][0]["type"] == "header"
    assert "Error" in result["blocks"][0]["text"]["text"]
    assert result["blocks"][1]["type"] == "section"
    assert "Something went wrong" in result["blocks"][1]["text"]["text"]


def test_format_code_block():
    """Test formatting a standalone code block."""
    formatter = SlackFormatter()

    # Format a code block with language
    result = formatter.format_code_block("def hello():\n    return 'Hello, world!'", "python")

    # Verify the result
    assert "text" in result
    assert "```python" in result["text"]
    assert "blocks" in result
    assert len(result["blocks"]) == 2  # Code block and language context
    assert result["blocks"][0]["type"] == "section"
    assert "```python" in result["blocks"][0]["text"]["text"]
    assert result["blocks"][1]["type"] == "context"
    assert "Language" in result["blocks"][1]["elements"][0]["text"]
    assert "Python" in result["blocks"][1]["elements"][0]["text"]  # Capitalized language name

    # Format a code block with language alias
    result = formatter.format_code_block("x = 42", "py")

    # Verify the result
    assert "text" in result
    assert "```python" in result["text"]  # Should be mapped to python
    assert "blocks" in result
    assert len(result["blocks"]) == 2
    assert result["blocks"][1]["type"] == "context"
    assert "Python" in result["blocks"][1]["elements"][0]["text"]  # Should display full language name

    # Format a code block without language
    result = formatter.format_code_block("const x = 42;")

    # Verify the result
    assert "text" in result
    assert "```\nconst x = 42;\n```" in result["text"]
    assert "blocks" in result
    assert len(result["blocks"]) == 1  # Just the code block, no language context
    assert result["blocks"][0]["type"] == "section"
    assert "```\nconst x = 42;\n```" in result["blocks"][0]["text"]["text"]


def test_format_table():
    """Test formatting a table."""
    formatter = SlackFormatter()

    # Format a table
    headers = ["Name", "Age", "Role"]
    rows = [
        ["Alice", "30", "Engineer"],
        ["Bob", "25", "Designer"],
        ["Charlie", "35", "Manager"]
    ]
    result = formatter.format_table(headers, rows)

    # Verify the result
    assert "text" in result
    assert "| Name | Age | Role |" in result["text"]
    assert "| Alice | 30 | Engineer |" in result["text"]
    assert "blocks" in result
    assert len(result["blocks"]) == 1
    assert result["blocks"][0]["type"] == "section"
    assert "| Name | Age | Role |" in result["blocks"][0]["text"]["text"]
    assert "| Alice | 30 | Engineer |" in result["blocks"][0]["text"]["text"]


def test_format_visualization():
    """Test formatting a visualization."""
    formatter = SlackFormatter()

    # Format a visualization without image
    result = formatter.format_visualization("User Activity", "Chart showing user activity over time")

    # Verify the result
    assert "text" in result
    assert "User Activity" in result["text"]
    assert "Chart showing user activity over time" in result["text"]
    assert "blocks" in result
    assert len(result["blocks"]) == 2  # Header and description
    assert result["blocks"][0]["type"] == "header"
    assert "User Activity" in result["blocks"][0]["text"]["text"]
    assert result["blocks"][1]["type"] == "section"
    assert "Chart showing user activity over time" in result["blocks"][1]["text"]["text"]

    # Format a visualization with image
    result = formatter.format_visualization(
        "User Activity",
        "Chart showing user activity over time",
        "https://example.com/chart.png"
    )

    # Verify the result
    assert "text" in result
    assert "User Activity" in result["text"]
    assert "blocks" in result
    assert len(result["blocks"]) == 3  # Header, description, and image
    assert result["blocks"][0]["type"] == "header"
    assert result["blocks"][2]["type"] == "image"
    assert result["blocks"][2]["image_url"] == "https://example.com/chart.png"
