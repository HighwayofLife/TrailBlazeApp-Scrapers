"""Test cases for the GeminiUtility class."""

import json
import pytest
from unittest.mock import patch, MagicMock

from app.gemini_utility import GeminiUtility
from app.exceptions import LLMAPIError, LLMContentError, LLMJsonParsingError


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    mock_settings_instance = MagicMock()
    mock_settings_instance.LLM_API_KEY = "fake_api_key"
    mock_settings_instance.MODEL_ID = "gemini-2.0-flash-001"
    mock_settings_instance.LLM_MAX_RETRIES = 3
    mock_settings_instance.LLM_RETRY_DELAY_SECONDS = 1
    mock_settings_instance.LLM_REQUEST_TIMEOUT_SECONDS = 10
    return mock_settings_instance


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
    html_content = "<div>Some HTML content</div>"

    # Expect the method to return None when no API key is configured
    result = GeminiUtility.extract_address_from_html(html_content)
    assert result is None


@patch('app.gemini_utility.get_settings')
@patch('app.gemini_utility.genai.Client')
def test_extract_address_success(mock_client_class, mock_get_settings):
    """Test successful address extraction."""
    # Configure mocks
    mock_config = MagicMock()
    mock_config.LLM_API_KEY = "fake_api_key"
    mock_config.MODEL_ID = "gemini-2.0-flash-001"
    mock_config.LLM_MAX_RETRIES = 3
    mock_config.LLM_RETRY_DELAY_SECONDS = 1
    mock_get_settings.return_value = mock_config

    # Create mock client and model
    mock_client_instance = MagicMock()
    mock_client_class.return_value = mock_client_instance

    # Create mock model
    mock_model = MagicMock()
    mock_client_instance.models.get.return_value = mock_model

    # Mock response from Gemini
    mock_response = MagicMock()
    mock_response.text = """
{
    "address": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip_code": "90210"
}"""
    # Ensure prompt_feedback doesn't exist or its block_reason is None
    mock_response.prompt_feedback = None
    mock_model.generate_content.return_value = mock_response

    # Test the method
    html_content = "<div>Some HTML content</div>"
    extracted_data = GeminiUtility.extract_address_from_html(html_content)

    # Assert the result
    assert extracted_data == {
        "address": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "zip_code": "90210"
    }

    # Verify interactions
    mock_client_class.assert_called_once_with(api_key=mock_config.LLM_API_KEY)
    mock_client_instance.models.get.assert_called_once_with(mock_config.MODEL_ID)
    mock_model.generate_content.assert_called_once()
