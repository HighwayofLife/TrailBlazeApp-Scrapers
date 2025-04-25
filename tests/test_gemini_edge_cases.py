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
    mock_config.MODEL_ID = "gemini-2.0-flash-001"
    mock_config.LLM_MAX_RETRIES = 1  # Set to 1 to avoid long retries in tests
    mock_config.LLM_RETRY_DELAY_SECONDS = 0  # No delay for tests
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

    # Create mock model
    mock_model = MagicMock()

    # Make models.get() a proper mock function that accepts a parameter
    mock_client_instance.models.get = MagicMock()
    mock_client_instance.models.get.return_value = mock_model

    # Create a mock response with block_reason
    mock_response = MagicMock()

    # Special setup for the prompt_feedback with block_reason
    mock_feedback = MagicMock()
    mock_feedback.block_reason = "SAFETY"
    mock_response.prompt_feedback = mock_feedback

    # Set up text property to prevent empty response error
    mock_response.text = "This content would be blocked"

    mock_model.generate_content.return_value = mock_response

    # Test the method
    html_content = "<div>Some HTML content</div>"

    # Expect the method to raise LLMContentError
    with pytest.raises(LLMContentError):
        GeminiUtility.extract_address_from_html(html_content)


@patch('app.gemini_utility.get_settings')
@patch('app.gemini_utility.genai.Client')
@patch('json.loads')
@patch('app.gemini_utility.hasattr')
def test_invalid_json_response(mock_hasattr, mock_json_loads, mock_client_class, mock_get_settings):
    """Test behavior when Gemini returns invalid JSON."""
    # Configure mocks
    mock_config = MagicMock()
    mock_config.LLM_API_KEY = "fake_api_key"
    mock_config.MODEL_ID = "gemini-2.0-flash-001"
    mock_config.LLM_MAX_RETRIES = 1
    mock_config.LLM_RETRY_DELAY_SECONDS = 0
    mock_get_settings.return_value = mock_config

    # Custom hasattr replacement to avoid prompt_feedback checks
    def custom_hasattr(obj, name):
        if name == "prompt_feedback":
            return False
        return True
    mock_hasattr.side_effect = custom_hasattr

    # Create mock client and model
    mock_client_instance = MagicMock()
    mock_client_class.return_value = mock_client_instance

    # Create mock model
    mock_model = MagicMock()
    mock_client_instance.models.get = MagicMock(return_value=mock_model)

    # Mock response with text content that will pass the empty check
    mock_response = MagicMock()
    mock_response.text = "This is not a valid JSON response"
    mock_model.generate_content.return_value = mock_response

    # Make json.loads raise a JSONDecodeError when called
    mock_json_loads.side_effect = json.JSONDecodeError("Invalid JSON", "This is not a valid JSON response", 0)

    # Test the method
    html_content = "<div>Some HTML content</div>"

    # Expect the method to raise LLMJsonParsingError
    with pytest.raises(LLMJsonParsingError):
        GeminiUtility.extract_address_from_html(html_content)


@patch('app.gemini_utility.get_settings')
@patch('app.gemini_utility.genai.Client')
@patch('json.loads')
@patch('app.gemini_utility.hasattr')
def test_missing_keys_json_response(mock_hasattr, mock_json_loads, mock_client_class, mock_get_settings):
    """Test behavior when Gemini returns JSON missing required keys."""
    # Configure mocks
    mock_config = MagicMock()
    mock_config.LLM_API_KEY = "fake_api_key"
    mock_config.MODEL_ID = "gemini-2.0-flash-001"
    mock_config.LLM_MAX_RETRIES = 1
    mock_config.LLM_RETRY_DELAY_SECONDS = 0
    mock_get_settings.return_value = mock_config

    # Custom hasattr replacement to avoid prompt_feedback checks
    def custom_hasattr(obj, name):
        if name == "prompt_feedback":
            return False
        return True
    mock_hasattr.side_effect = custom_hasattr

    # Create mock client and model
    mock_client_instance = MagicMock()
    mock_client_class.return_value = mock_client_instance

    # Create mock model
    mock_model = MagicMock()
    mock_client_instance.models.get = MagicMock(return_value=mock_model)

    # Mock response with text (this will be properly JSON-parsed but missing keys)
    mock_response = MagicMock()
    mock_response.text = """{"address": "123 Main St", "city": "Anytown"}"""  # Missing state and zip_code
    mock_model.generate_content.return_value = mock_response

    # Make json.loads return a dictionary missing required keys
    mock_json_loads.return_value = {"address": "123 Main St", "city": "Anytown"}

    # Test the method
    html_content = "<div>Some HTML content</div>"

    # Expect the method to raise LLMJsonParsingError
    with pytest.raises(LLMJsonParsingError):
        GeminiUtility.extract_address_from_html(html_content)


@patch('app.gemini_utility.get_settings')
@patch('app.gemini_utility.genai.Client')
@patch('app.gemini_utility.hasattr')
@patch('json.loads')
def test_api_retries(mock_json_loads, mock_hasattr, mock_client_class, mock_get_settings):
    """Test retry mechanism for API failures."""
    # Configure mocks
    mock_config = MagicMock()
    mock_config.LLM_API_KEY = "fake_api_key"
    mock_config.MODEL_ID = "gemini-2.0-flash-001"
    mock_config.LLM_MAX_RETRIES = 3
    mock_config.LLM_RETRY_DELAY_SECONDS = 0  # Set to 0 for fast testing
    mock_get_settings.return_value = mock_config

    # Custom hasattr replacement to avoid prompt_feedback checks
    def custom_hasattr(obj, name):
        if name == "prompt_feedback":
            return False
        return hasattr(obj, name)
    mock_hasattr.side_effect = custom_hasattr

    # Set up json.loads to return a proper dictionary
    mock_json_loads.return_value = {
        "address": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "zip_code": "90210"
    }

    # Create mock client instance
    mock_client_instance = MagicMock()
    mock_client_class.return_value = mock_client_instance

    # Create mock model
    mock_model = MagicMock()
    mock_client_instance.models.get = MagicMock(return_value=mock_model)

    # Create successful response
    success_response = MagicMock()
    success_response.text = """{"address": "123 Main St", "city": "Anytown", "state": "CA", "zip_code": "90210"}"""

    # Set up the side effects for generate_content
    def generate_content_side_effect(*args, **kwargs):
        # First two calls will raise an exception
        call_count = mock_model.generate_content.call_count
        if call_count < 2:
            raise Exception(f"API error on attempt {call_count + 1}")
        # Third call succeeds
        return success_response

    # Apply the side effect to the generate_content method
    mock_model.generate_content.side_effect = generate_content_side_effect

    # Test the method
    html_content = "<div>Some HTML content</div>"
    result = GeminiUtility.extract_address_from_html(html_content)

    # Assert successful result after retries
    assert result is not None
    assert result["address"] == "123 Main St"
    assert mock_model.generate_content.call_count == 3  # Should have been called 3 times
