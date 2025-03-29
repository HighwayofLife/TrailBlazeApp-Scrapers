"""Integration tests for the TrailBlazeApp-Scrapers project."""

import pytest
from unittest.mock import MagicMock, patch
import json
from app.database import DatabaseManager
from app.data_validator import DataValidator
from app.base_scraper import BaseScraper
from app.exceptions import ValidationError
from bs4 import BeautifulSoup
from typing import Any


@pytest.fixture
def db_config():
    """Fixture for database configuration."""
    return {
        "host": "localhost",
        "port": 5432,
        "database": "test_db",
        "user": "test_user",
        "password": "test_pass"
    }


@pytest.fixture
def sample_event_data():
    """Fixture for sample event data."""
    return {
        "source": "TEST",
        "ride_id": "event-123",
        "name": "Test Endurance Ride",
        "region": "West",
        "date_start": "2023-06-15",
        "location_name": "Test Location",
        "country": "USA",
        "ride_manager": "Test Manager",
        "ride_days": 1,
        "event_type": "endurance",
        "distances": [{"distance": "50", "date": "2023-06-15"}],
        "control_judges": [{"name": "Test Judge", "role": "Control Judge"}]
    }


class TestScraper(BaseScraper):
    """Test scraper class for integration testing."""

    def __init__(self, db_config):
        """Initialize with database configuration."""
        self.db_manager = MagicMock()
        self.logger = MagicMock()
        self.metrics_manager = MagicMock()
        self.data_validator = DataValidator(self.db_manager)

    def extract_all_events(self):
        """Mock event extraction."""
        return []

    def extract_event_data(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Minimal implementation for testing BaseScraper."""
        # Required by the BaseScraper ABC
        # Integration tests typically mock the overall scrape/
        # extract_all_events process rather than needing this.
        return []

    def scrape(self):
        """
        Implement the required abstract method from BaseScraper.

        This is a mock implementation for testing.
        """
        return self.extract_all_events()


@pytest.fixture
def test_scraper(db_config):
    """Fixture for the test scraper."""
    return TestScraper(db_config)


def test_scraper_with_validator_integration(test_scraper, sample_event_data):
    """
    Test integration between scraper, database manager, and data validator.

    This test demonstrates how to use the DataValidator to validate
    that data inserted by a scraper is stored correctly in the database.
    """
    # Set up mock events
    test_scraper.extract_all_events = MagicMock(return_value=[sample_event_data])

    # Patch the db_manager to control its responses
    test_scraper.db_manager.insert_or_update_event = MagicMock(return_value=True)
    test_scraper.db_manager.get_event = MagicMock(return_value=sample_event_data)

    # Define our run method with validation
    def run_with_validation():
        validation_errors = []

        # Process and validate events
        for event_data in test_scraper.extract_all_events():
            # Insert the event
            test_scraper.db_manager.insert_or_update_event(event_data)

            # Validate the operation was successful
            success, errors = test_scraper.data_validator.validate_database_operation(
                event_data, "insert_or_update"
            )

            if not success:
                validation_errors.extend(errors)

        # Check if we had any validation errors
        if validation_errors:
            test_scraper.metrics_manager.increment.assert_called_with(
                'validation_errors', len(validation_errors)
            )
            return False

        return True

    # Run the test with validation
    result = run_with_validation()

    # Verify the test passed
    assert result is True
    test_scraper.db_manager.insert_or_update_event.assert_called_once_with(sample_event_data)
    test_scraper.db_manager.get_event.assert_called_once_with(
        sample_event_data["source"], sample_event_data["ride_id"]
    )


def test_scraper_with_validator_integration_mismatch(test_scraper, sample_event_data):
    """
    Test integration when there's a data mismatch between what was expected and what was stored.

    This demonstrates detection of data integrity issues.
    """
    # Set up mock events
    test_scraper.extract_all_events = MagicMock(return_value=[sample_event_data])

    # Return a different event data from the database to simulate a mismatch
    modified_data = sample_event_data.copy()
    modified_data["name"] = "Different Name"  # Introduce a mismatch
    test_scraper.db_manager.insert_or_update_event = MagicMock(return_value=True)
    test_scraper.db_manager.get_event = MagicMock(return_value=modified_data)

    # Define our run method with validation
    def run_with_validation():
        validation_errors = []

        # Process and validate events
        for event_data in test_scraper.extract_all_events():
            # Insert the event
            test_scraper.db_manager.insert_or_update_event(event_data)

            # Validate the operation was successful
            success, errors = test_scraper.data_validator.validate_database_operation(
                event_data, "insert_or_update"
            )

            if not success:
                validation_errors.extend(errors)

        # Check if we had any validation errors
        if validation_errors:
            return False

        return True

    # Run the test with validation
    result = run_with_validation()

    # Verify the test failed due to data mismatch
    assert result is False
    test_scraper.db_manager.insert_or_update_event.assert_called_once_with(sample_event_data)
    test_scraper.db_manager.get_event.assert_called_once_with(
        sample_event_data["source"], sample_event_data["ride_id"]
    )


def test_scraper_with_validator_jsonb_fields(test_scraper, sample_event_data):
    """
    Test integration with JSONB fields to ensure they're compared correctly.

    This shows how the validator handles complex nested fields stored as JSON.
    """
    # Set up mock events
    test_scraper.extract_all_events = MagicMock(return_value=[sample_event_data])

    # Return event data with JSONB fields as strings to simulate database storage
    db_data = sample_event_data.copy()
    db_data["distances"] = json.dumps(db_data["distances"])
    db_data["control_judges"] = json.dumps(db_data["control_judges"])

    test_scraper.db_manager.insert_or_update_event = MagicMock(return_value=True)
    test_scraper.db_manager.get_event = MagicMock(return_value=db_data)

    # Validate the operation
    success, errors = test_scraper.data_validator.validate_database_operation(
        sample_event_data, "insert_or_update"
    )

    # Validation should succeed despite the JSONB serialization difference
    assert success is True
    assert errors is None
