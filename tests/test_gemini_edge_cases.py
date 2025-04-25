"""Test edge cases for the GeminiUtility class."""

import json
import pytest
from unittest.mock import patch, MagicMock

from app.gemini_utility import GeminiUtility
from app.exceptions import LLMAPIError, LLMContentError, LLMJsonParsingError


@patch('app.gemini_utility.get_settings')
@patch('app.gemini_utility.genai.Client')
def test_client_initialization_error(mock_client_class, mock_get_settings):
    """Test behavior when client initialization raises an error."""
    # Configure mocks
    mock_config = MagicMock()
    mock_config.LLM_API_KEY = "fake_api_key"
    mock_get_settings.return_value = mock_config

    # Make client initialization raise an exception
    mock_client_class.side_effect = Exception("Failed to initialize client")

    # Test the method
    html_content = "<div>Some HTML content</div>"

    # Expect the method to raise LLMAPIError
    with pytest.raises(LLMAPIError):
        GeminiUtility.extract_address_from_html(html_content)


@patch('app.gemini_utility.get_settings')
@patch('app.gemini_utility.genai.Client')
def test_empty_response(mock_client_class, mock_get_settings):
    """Test behavior when Gemini returns an empty response."""
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

    # Mock response with empty text
    mock_response = MagicMock()
    mock_response.text = ""  # Empty response
    mock_response.prompt_feedback = None
    mock_model.generate_content.return_value = mock_response

    # Test the method
    html_content = "<div>Some HTML content</div>"

    # Expect the method to raise LLMContentError
    with pytest.raises(LLMContentError):
        GeminiUtility.extract_address_from_html(html_content)


@patch('app.gemini_utility.get_settings')
@patch('app.gemini_utility.genai.Client')
def test_invalid_json_response(mock_client_class, mock_get_settings):
    """Test behavior when Gemini returns invalid JSON."""
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

    # Mock response with invalid JSON
    mock_response = MagicMock()
    mock_response.text = "This is not a valid JSON response"
    mock_response.prompt_feedback = None
    mock_model.generate_content.return_value = mock_response

    # Test the method
    html_content = "<div>Some HTML content</div>"

    # Expect the method to raise LLMJsonParsingError
    with pytest.raises(LLMJsonParsingError):
        GeminiUtility.extract_address_from_html(html_content)


@patch('app.gemini_utility.get_settings')
@patch('app.gemini_utility.genai.Client')
def test_missing_keys_json_response(mock_client_class, mock_get_settings):
    """Test behavior when Gemini returns JSON missing required keys."""
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

    # Mock response with incomplete JSON (missing keys)
    mock_response = MagicMock()
    mock_response.text = """{"address": "123 Main St", "city": "Anytown"}"""  # Missing state and zip_code
    mock_response.prompt_feedback = None
    mock_model.generate_content.return_value = mock_response

    # Test the method
    html_content = "<div>Some HTML content</div>"

    # Expect the method to raise LLMJsonParsingError
    with pytest.raises(LLMJsonParsingError):
        GeminiUtility.extract_address_from_html(html_content)


@patch('app.gemini_utility.get_settings')
@patch('app.gemini_utility.genai.Client')
def test_api_retries(mock_client_class, mock_get_settings):
    """Test retry mechanism for API failures."""
    # Configure mocks
    mock_config = MagicMock()
    mock_config.LLM_API_KEY = "fake_api_key"
    mock_config.MODEL_ID = "gemini-2.0-flash-001"
    mock_config.LLM_MAX_RETRIES = 3
    mock_config.LLM_RETRY_DELAY_SECONDS = 0.1  # Fast for testing
    mock_get_settings.return_value = mock_config

    # Create mock client and model
    mock_client_instance = MagicMock()
    mock_client_class.return_value = mock_client_instance

    # Create mock model
    mock_model = MagicMock()
    mock_client_instance.models.get.return_value = mock_model

    # Make the first two attempts fail, then succeed on third
    mock_model.generate_content.side_effect = [
        Exception("API error"),  # First attempt fails
        Exception("API error"),  # Second attempt fails
        MagicMock(  # Third attempt succeeds
            text="""{"address": "123 Main St", "city": "Anytown", "state": "CA", "zip_code": "90210"}""",
            prompt_feedback=None
        )
    ]

    # Test the method
    html_content = "<div>Some HTML content</div>"
    result = GeminiUtility.extract_address_from_html(html_content)

    # Assert successful result after retries
    assert result is not None
    assert result["address"] == "123 Main St"
    assert mock_model.generate_content.call_count == 3  # Should have been called 3 times


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

    # Create mock model
    mock_model = MagicMock()
    mock_client_instance.models.get.return_value = mock_model

    # Mock response with moderation block
    mock_response = MagicMock()
    mock_response.text = "This would never be returned in a real moderation block"
    mock_response.prompt_feedback = MagicMock()
    mock_response.prompt_feedback.block_reason = "SAFETY"
    mock_model.generate_content.return_value = mock_response

    # Test the method
    html_content = "<div>Some HTML content</div>"

    # Expect the method to raise LLMContentError
    with pytest.raises(LLMContentError):
        GeminiUtility.extract_address_from_html(html_content)
