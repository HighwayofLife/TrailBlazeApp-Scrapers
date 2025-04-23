import json

import requests

import pytest
from unittest.mock import patch, MagicMock

# Assuming LLM_Utility is in app/llm_utility.py
from app.llm_utility import LLM_Utility
from app.exceptions import LLMJsonParsingError

from app.exceptions import LLMAPIError, LLMContentError

# Mock the config to avoid external dependencies


@pytest.fixture
def mock_config():
    # Return a MagicMock instance with necessary attributes
    mock_settings_instance = MagicMock()
    mock_settings_instance.LLM_API_KEY = "fake_api_key"
    mock_settings_instance.LLM_API_ENDPOINT = "http://fake-llm-api.com"
    mock_settings_instance.LLM_MAX_RETRIES = 3  # Use integer value
    mock_settings_instance.LLM_RETRY_DELAY_SECONDS = 1  # Use integer value
    mock_settings_instance.LLM_REQUEST_TIMEOUT_SECONDS = 10  # Use integer value
    yield mock_settings_instance

# Test case 1: Successful data extraction


@patch('app.llm_utility.requests.post')
def test_extract_address_success(mock_post, mock_config):  # Added mock_config
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{
            "text": """
{
    "address": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip_code": "90210"
}"""
        }]
    }
    mock_post.return_value = mock_response

    html_content = "<div>Some HTML content</div>"
    llm_utility = LLM_Utility()
    extracted_data = llm_utility.extract_address_from_html(html_content)

    assert extracted_data == {
        "address": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "zip_code": "90210"
    }
    mock_post.assert_called_once()

# Test case 2: Handling LLM API errors (non-200 status code)


@patch('app.llm_utility.requests.post')
@patch('app.llm_utility.requests.post')
def test_extract_address_api_error(mock_post, mock_config):  # Added mock_config
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_post.return_value = mock_response

    html_content = "<div>Some HTML content</div>"
    llm_utility = LLM_Utility()

    with pytest.raises(LLMAPIError) as excinfo:
        llm_utility.extract_address_from_html(html_content)

    assert "LLM API returned status code 500" in str(excinfo.value)
    mock_post.assert_called_once()

# Test case 3: Handling timeouts and connection issues


@patch('app.llm_utility.requests.post')
@patch('app.llm_utility.requests.post')
def test_extract_address_request_exception(mock_post, mock_config):  # Removed mock_get_settings, added mock_config
    mock_post.side_effect = requests.exceptions.RequestException("Connection error")

    html_content = "<div>Some HTML content</div>"
    llm_utility = LLM_Utility()

    with pytest.raises(LLMAPIError) as excinfo:
        llm_utility.extract_address_from_html(html_content)

    assert isinstance(excinfo.value, LLMAPIError)
    assert "API request failed: Connection error" in str(excinfo.value)  # Corrected assertion string
    assert mock_post.call_count == mock_config.MAX_RETRIES  # Access MAX_RETRIES from the mock settings instance

# Test case 4: Handling malformed JSON responses


@patch('app.llm_utility.requests.post')
@patch('app.llm_utility.requests.post')
def test_extract_address_malformed_json(mock_post, mock_config):  # Added mock_config
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", doc="{}", pos=1)
    mock_post.return_value = mock_response

    html_content = "<div>Some HTML content</div>"
    llm_utility = LLM_Utility()

    with pytest.raises(LLMJsonParsingError) as excinfo:
        llm_utility.extract_address_from_html(html_content)

    assert "Failed to parse JSON response from LLM API" in str(excinfo.value)
    mock_post.assert_called_once()

# Test case 5: Handling LLM content moderation errors


@patch('app.llm_utility.requests.post')
def test_extract_address_content_error(mock_post, mock_config):  # Added mock_config
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Assuming the LLM returns a specific structure for content errors
    mock_response.json.return_value = {
        "error": {
            "message": "Content has been moderated.",
            "code": 400,
            "status": "INVALID_ARGUMENT"
        }
    }
    mock_post.return_value = mock_response

    html_content = "<div>Offensive content here</div>"
    llm_utility = LLM_Utility()

    with pytest.raises(LLMContentError) as excinfo:
        llm_utility.extract_address_from_html(html_content)

    assert "LLM API error: {'message': 'Content has been moderated.', 'code': 400, 'status': 'INVALID_ARGUMENT'}" in str(excinfo.value)  # Corrected assertion string
    mock_post.assert_called_once()

# Test case 6: Verification of retry logic


@patch('app.llm_utility.requests.post')
@patch('app.llm_utility.time.sleep')
@patch('app.llm_utility.requests.post')
@patch('app.llm_utility.time.sleep')
def test_extract_address_retry_logic(mock_sleep, mock_post, mock_config):  # Removed mock_get_settings
    # Simulate transient errors followed by success
    mock_post.side_effect = [
        requests.exceptions.RequestException("Transient error 1"),
        requests.exceptions.RequestException("Transient error 2"),
        MagicMock(status_code=200, json=lambda: {
            "choices": [{
                "text": """
{
    "address": "456 Oak Ave",
    "city": "Otherville",
    "state": "NY",
    "zip_code": "10001"
}"""
            }]
        })
    ]

    html_content = "<div>Some HTML content</div>"
    llm_utility = LLM_Utility()
    extracted_data = llm_utility.extract_address_from_html(html_content)

    assert extracted_data == {
        "address": "456 Oak Ave",
        "city": "Otherville",
        "state": "NY",
        "zip_code": "10001"
    }
    # Expect 3 calls: initial attempt + 2 retries
    assert mock_post.call_count == 3
    # Expect 2 sleeps for 2 retries
    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(mock_config.RETRY_DELAY_SECONDS)  # Access attribute from mock settings instance
