"""Integration test for GeminiUtility with actual API calls."""

import os
import pytest
from unittest.mock import patch, MagicMock

from app.gemini_utility import GeminiUtility
from app.exceptions import LLMAPIError, LLMContentError, LLMJsonParsingError


@pytest.mark.integration
@patch('app.gemini_utility.get_settings')
@patch('app.gemini_utility.genai.Client')
def test_gemini_live_integration(mock_client_class, mock_get_settings):
    """Test the GeminiUtility with a mocked API call (simulating live behavior)."""
    # Simple HTML snippet containing an address
    sample_html = """
    <div class="contact-info">
        <p>John Doe</p>
        <span>123 Main St<br/>Anytown, CA 90210</span>
        <p>Phone: 555-1234</p>
    </div>
    """

    # Set up mocks
    mock_config = MagicMock()
    mock_config.LLM_API_KEY = "test_api_key"
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

    try:
        # Attempt to extract address from the HTML snippet
        address_data = GeminiUtility.extract_address_from_html(sample_html)

        # Verify we got a valid response
        assert address_data is not None
        assert "address" in address_data
        assert "city" in address_data
        assert "state" in address_data
        assert "zip_code" in address_data

        # Check for expected values (should match our mock response)
        assert "123 Main St" in address_data["address"]
        assert address_data["city"] == "Anytown"
        assert address_data["state"] == "CA"
        assert address_data["zip_code"] == "90210"

    except (LLMAPIError, LLMContentError, LLMJsonParsingError) as e:
        pytest.fail(f"Mock Gemini API test failed with error: {e}")


# This test is marked as real_integration because it makes actual API calls
# Only run if explicitly enabled with LLM_API_KEY environment variable
@pytest.mark.real_integration
@pytest.mark.skipif(not os.getenv("LLM_API_KEY"), reason="LLM_API_KEY not set")
def test_gemini_actual_live_integration():
    """Test the GeminiUtility with an actual live API call (requires API key)."""
    # Simple HTML snippet containing an address
    sample_html = """
    <div class="contact-info">
        <p>John Doe</p>
        <span>123 Main St<br/>Anytown, CA 90210</span>
        <p>Phone: 555-1234</p>
    </div>
    """

    try:
        # Attempt to extract address from the HTML snippet
        address_data = GeminiUtility.extract_address_from_html(sample_html)

        # Verify we got a valid response
        assert address_data is not None
        assert "address" in address_data
        assert "city" in address_data
        assert "state" in address_data
        assert "zip_code" in address_data

    except (LLMAPIError, LLMContentError, LLMJsonParsingError) as e:
        pytest.fail(f"Live Gemini API test failed with error: {e}")
