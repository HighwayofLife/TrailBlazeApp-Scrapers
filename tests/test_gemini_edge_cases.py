"""Test edge cases for the GeminiUtility class."""

import pytest
from unittest.mock import patch, MagicMock

from app.gemini_utility import GeminiUtility
from app.exceptions import LLMAPIError, LLMContentError


@patch('app.gemini_utility.get_settings')
@patch('app.gemini_utility.genai.Client')
def test_client_initialization_error(mock_client_class, mock_get_settings):
    """Test behavior when client initialization raises an error."""
    # Configure mocks
    mock_config = MagicMock()
    mock_config.LLM_API_KEY = "fake_api_key"
    mock_config.MODEL_ID = "gemini-2.0-flash-001"
    mock_config.LLM_MAX_RETRIES = 3
    mock_config.LLM_RETRY_DELAY_SECONDS = 0.1  # Short retry delay for testing
    mock_get_settings.return_value = mock_config

    # Make client initialization raise an exception
    mock_client_class.side_effect = Exception("Failed to initialize client")

    # Test the method
    html_content = "<div>Some HTML content</div>"

    # Expect the method to raise LLMAPIError
    with pytest.raises(LLMAPIError):
        GeminiUtility.extract_address_from_html(html_content)


@patch('app.gemini_utility.get_settings')
def test_no_api_key(mock_get_settings):
    """Test behavior when API key is not configured."""
    # Configure mocks
    mock_config = MagicMock()
    mock_config.LLM_API_KEY = None
    mock_get_settings.return_value = mock_config

    # Test the method
    html_content = "<div>Some HTML content</div>"

    # Expect the method to return None when no API key is configured
    result = GeminiUtility.extract_address_from_html(html_content)
    assert result is None


@patch('app.gemini_utility.get_settings')
@patch('app.gemini_utility.genai.Client')
def test_content_moderation_block(mock_client_class, mock_get_settings):
    """Test behavior when content is blocked by moderation."""
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

    # Create mock model and handle the model_id parameter correctly
    mock_model = MagicMock()
    mock_client_instance.models.get = MagicMock(return_value=mock_model)

    # Create a mock response with block_reason
    mock_response = MagicMock()
    # Special setup for the prompt_feedback
    mock_feedback = MagicMock()
    mock_feedback.block_reason = "SAFETY"
    mock_response.prompt_feedback = mock_feedback

    mock_model.generate_content.return_value = mock_response

    # Test the method
    html_content = "<div>Some HTML content</div>"

    # Expect the method to raise LLMContentError
    with pytest.raises(LLMContentError):
        GeminiUtility.extract_address_from_html(html_content)
