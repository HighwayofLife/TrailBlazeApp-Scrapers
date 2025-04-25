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


@patch("app.llm_utility.get_settings")
@patch("app.llm_utility.requests.post")
def test_extract_address_success(mock_post, mock_get_settings, mock_config):
    # Configure the mock_get_settings to return our mock_config
    mock_get_settings.return_value = mock_config

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "text": """
{
    "address": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip_code": "90210"
}"""
            }
        ]
    }
    mock_post.return_value = mock_response

    html_content = "<div>Some HTML content</div>"
    llm_utility = LLM_Utility()
    extracted_data = llm_utility.extract_address_from_html(html_content)

    assert extracted_data == {
        "address": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "zip_code": "90210",
    }
    mock_post.assert_called_once()


# Test case 2: Handling LLM API errors (non-200 status code)


@patch("app.llm_utility.requests.post")
@patch("app.llm_utility.get_settings")
def test_extract_address_api_error(mock_get_settings, mock_post):
    # Create a direct mock settings object (not using mock_config fixture)
    mock_config = MagicMock()
    mock_get_settings.return_value = mock_config

    # Configure mock settings explicitly
    mock_config.LLM_API_ENDPOINT = "http://fake-llm-api.com"
    mock_config.LLM_API_KEY = "fake_api_key"
    mock_config.LLM_MAX_RETRIES = 1  # Use 1 instead of 0 to ensure the loop runs once
    mock_config.LLM_REQUEST_TIMEOUT_SECONDS = 10

    # Create a response with an error
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    # Important: Set up the mocks in the right order
    # The post call should return our mock_response
    mock_post.return_value = mock_response
    # When raise_for_status is called on the response, it should raise HTTPError
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "500 Server Error"
    )

    html_content = "<div>Some HTML content</div>"
    llm_utility = LLM_Utility()

    # The method should raise LLMAPIError after handling the HTTPError
    with pytest.raises(LLMAPIError):
        llm_utility.extract_address_from_html(html_content)

    # Assert that post was called once
    mock_post.assert_called_once()


# Test case 3: Handling timeouts and connection issues


@patch("app.llm_utility.get_settings")
@patch("app.llm_utility.requests.post")
def test_extract_address_request_exception(mock_post, mock_get_settings, mock_config):
    # Configure the mock_get_settings to return our mock_config
    mock_get_settings.return_value = mock_config

    # Set to at least 1 to ensure the loop runs
    mock_config.LLM_MAX_RETRIES = 1

    mock_post.side_effect = requests.exceptions.RequestException("Connection error")

    html_content = "<div>Some HTML content</div>"
    llm_utility = LLM_Utility()

    with pytest.raises(LLMAPIError) as excinfo:
        llm_utility.extract_address_from_html(html_content)

    assert isinstance(excinfo.value, LLMAPIError)
    assert (
        mock_post.call_count == mock_config.LLM_MAX_RETRIES
    )  # Use LLM_MAX_RETRIES from the mock_config


# Test case 4: Handling malformed JSON responses


@patch("app.llm_utility.get_settings")
@patch("app.llm_utility.requests.post")
def test_extract_address_malformed_json(mock_post, mock_get_settings, mock_config):
    # Configure the mock_get_settings to return our mock_config
    mock_get_settings.return_value = mock_config

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError(
        "Invalid JSON", doc="{}", pos=1
    )
    mock_post.return_value = mock_response

    html_content = "<div>Some HTML content</div>"
    llm_utility = LLM_Utility()

    with pytest.raises(LLMJsonParsingError):
        llm_utility.extract_address_from_html(html_content)

    mock_post.assert_called_once()


# Test case 5: Handling LLM content moderation errors


@patch("app.llm_utility.get_settings")
@patch("app.llm_utility.requests.post")
def test_extract_address_content_error(mock_post, mock_get_settings, mock_config):
    # Configure the mock_get_settings to return our mock_config
    mock_get_settings.return_value = mock_config

    mock_response = MagicMock()
    mock_response.status_code = 200
    # Assuming the LLM returns a specific structure for content errors
    mock_response.json.return_value = {
        "error": {
            "message": "Content has been moderated.",
            "code": 400,
            "status": "INVALID_ARGUMENT",
        }
    }
    mock_post.return_value = mock_response

    html_content = "<div>Offensive content here</div>"
    llm_utility = LLM_Utility()

    with pytest.raises(LLMContentError):
        llm_utility.extract_address_from_html(html_content)

    mock_post.assert_called_once()


# Test case 6: Verification of retry logic


@patch("app.llm_utility.get_settings")
@patch("app.llm_utility.time.sleep")
@patch("app.llm_utility.requests.post")
def test_extract_address_retry_logic(
    mock_post, mock_sleep, mock_get_settings, mock_config
):
    # Configure the mock_get_settings to return our mock_config
    mock_get_settings.return_value = mock_config

    # Set the max retries to 3 to match our side_effect array
    mock_config.LLM_MAX_RETRIES = 3

    # Create a proper response object for the successful case
    success_response = MagicMock()
    success_response.status_code = 200
    success_response.json.return_value = {
        "choices": [
            {
                "text": """
{
    "address": "456 Oak Ave",
    "city": "Otherville",
    "state": "NY",
    "zip_code": "10001"
}"""
            }
        ]
    }

    # Simulate transient errors followed by success
    mock_post.side_effect = [
        requests.exceptions.RequestException("Transient error 1"),
        requests.exceptions.RequestException("Transient error 2"),
        success_response,
    ]

    html_content = "<div>Some HTML content</div>"
    llm_utility = LLM_Utility()
    extracted_data = llm_utility.extract_address_from_html(html_content)

    assert extracted_data == {
        "address": "456 Oak Ave",
        "city": "Otherville",
        "state": "NY",
        "zip_code": "10001",
    }
    # Expect 3 calls: initial attempt + 2 retries
    assert mock_post.call_count == 3
    # Expect 2 sleeps for 2 retries
    assert mock_sleep.call_count == 2
    # Make sure sleep was called with the expected delay time
    mock_sleep.assert_called_with(
        mock_config.LLM_RETRY_DELAY_SECONDS
    )  # Access attribute from mock settings instance
