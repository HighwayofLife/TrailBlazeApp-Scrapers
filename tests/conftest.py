import pytest
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def mock_config():
    """
    Autouse fixture to provide a mock settings instance with configured LLM settings.
    This fixture is available to all tests in the 'tests' directory.
    """
    mock_settings_instance = MagicMock()
    mock_settings_instance.LLM_API_KEY = "fake_api_key"
    mock_settings_instance.LLM_API_ENDPOINT = "http://fake-llm-api.com"
    mock_settings_instance.LLM_MAX_RETRIES = 3
    mock_settings_instance.LLM_RETRY_DELAY_SECONDS = 1
    mock_settings_instance.LLM_REQUEST_TIMEOUT_SECONDS = 10
    yield mock_settings_instance
