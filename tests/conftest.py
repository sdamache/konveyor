"""Test configuration for Konveyor."""
import pytest

def pytest_configure(config):
    """Register custom marks."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test that requires Azure services"
    )
