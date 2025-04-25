"""Simple test case for the GeminiUtility class."""

import pytest
from unittest.mock import patch, MagicMock

from app.gemini_utility import GeminiUtility
from app.exceptions import LLMAPIError


def test_simple():
    """A simple test that should always pass."""
    assert True

@patch('app.gemini_utility.get_settings')
def test_no_api_key(mock_get_settings):
    """Test behavior when API key is not configured."""
    # Configure mock to return settings without API key
    mock_config = MagicMock()
    mock_config.LLM_API_KEY = None
    mock_get_settings.return_value = mock_config

    # Test the method without API key
    html_content = "<div>Test content</div>"

    # Expect the method to return None when no API key is configured
    result = GeminiUtility.extract_address_from_html(html_content)
    assert result is None
