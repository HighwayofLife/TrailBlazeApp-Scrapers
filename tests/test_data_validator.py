"""Tests for the DataValidator module."""

import pytest
from unittest.mock import MagicMock, patch
import json
from app.data_validator import DataValidator
from app.exceptions import ValidationError


@pytest.fixture
def sample_event_data():
    """Fixture for sample event data."""
    return {
        "source": "AERC",
        "ride_id": "test-123",
        "name": "Test Event",
        "region": "West",
        "date_start": "2023-05-15",
        "location_name": "Test Location",
        "country": "USA",
        "ride_manager": "Test Manager",
        "ride_days": 1,
        "event_type": "endurance"
    }


@pytest.fixture
def mock_db_manager():
    """Fixture for mock database manager."""
    mock_db = MagicMock()
    # Set up get_event to return None by default (no event found)
    mock_db.get_event.return_value = None
    return mock_db


@pytest.fixture
def data_validator(mock_db_manager):
    """Fixture for DataValidator instance."""
    return DataValidator(mock_db_manager)


def test_init_data_validator(mock_db_manager):
    """Test initializing the DataValidator class."""
    validator = DataValidator(mock_db_manager)
    assert validator.db_manager == mock_db_manager
    assert validator.logger is not None


def test_validate_event_data_valid(data_validator, sample_event_data):
    """Test validation of valid event data."""
    # This should not raise any exceptions
    data_validator._validate_event_data(sample_event_data)


def test_validate_event_data_invalid(data_validator):
    """Test validation of invalid event data."""
    # Missing required fields
    invalid_data = {
        "source": "AERC",
        "ride_id": "test-123",
        # Missing name, region, date_start, etc.
    }

    with pytest.raises(ValidationError):
        data_validator._validate_event_data(invalid_data)


def test_validate_database_operation_insert_not_found(data_validator, sample_event_data, mock_db_manager):
    """Test validation when an inserted event is not found."""
    # Mock get_event to return None (not found)
    mock_db_manager.get_event.return_value = None

    # Validate with expected operation "insert"
    success, errors = data_validator.validate_database_operation(sample_event_data, "insert")

    assert success is False
    assert len(errors) == 1
    assert "not found in database" in errors[0]
    mock_db_manager.get_event.assert_called_once_with(sample_event_data["source"], sample_event_data["ride_id"])


def test_validate_database_operation_delete_still_exists(data_validator, sample_event_data, mock_db_manager):
    """Test validation when a deleted event still exists."""
    # Mock get_event to return some data (event still exists after delete)
    mock_db_manager.get_event.return_value = sample_event_data.copy()

    # Validate with expected operation "delete"
    success, errors = data_validator.validate_database_operation(sample_event_data, "delete")

    assert success is False
    assert len(errors) == 1
    assert "still exists in database" in errors[0]


def test_validate_database_operation_insert_success(data_validator, sample_event_data, mock_db_manager):
    """Test successful validation of an inserted event."""
    # Mock get_event to return matching data
    mock_db_manager.get_event.return_value = sample_event_data.copy()

    # Patch the _compare_event_data method to return success
    with patch.object(data_validator, '_compare_event_data') as mock_compare:
        mock_compare.return_value = (True, None)

        # Validate with expected operation "insert"
        success, errors = data_validator.validate_database_operation(sample_event_data, "insert")

        assert success is True
        assert errors is None
        mock_compare.assert_called_once_with(sample_event_data, sample_event_data.copy())


def test_validate_database_operation_update_success(data_validator, sample_event_data, mock_db_manager):
    """Test successful validation of an updated event."""
    # Mock get_event to return matching data
    mock_db_manager.get_event.return_value = sample_event_data.copy()

    # Patch the _compare_event_data method to return success
    with patch.object(data_validator, '_compare_event_data') as mock_compare:
        mock_compare.return_value = (True, None)

        # Validate with expected operation "update"
        success, errors = data_validator.validate_database_operation(sample_event_data, "update")

        assert success is True
        assert errors is None
        mock_compare.assert_called_once_with(sample_event_data, sample_event_data.copy())


def test_validate_deletion_success(data_validator, mock_db_manager):
    """Test successful validation of a deleted event."""
    # Mock get_event to return None (event was deleted)
    mock_db_manager.get_event.return_value = None

    # Validate deletion
    success, errors = data_validator.validate_deletion("AERC", "test-123")

    assert success is True
    assert errors is None
    mock_db_manager.get_event.assert_called_once_with("AERC", "test-123")


def test_validate_deletion_failure(data_validator, sample_event_data, mock_db_manager):
    """Test failed validation of a deleted event."""
    # Mock get_event to return data (event still exists)
    mock_db_manager.get_event.return_value = sample_event_data.copy()

    # Validate deletion
    success, errors = data_validator.validate_deletion("AERC", "test-123")

    assert success is False
    assert len(errors) == 1
    assert "still exists in database" in errors[0]
    mock_db_manager.get_event.assert_called_once_with("AERC", "test-123")


def test_compare_event_data_match(data_validator):
    """Test comparison of matching event data."""
    expected_data = {
        "source": "AERC",
        "ride_id": "test-123",
        "name": "Test Event",
        "region": "West",
        "date_start": "2023-05-15",
        "location_name": "Test Location",
        "distances": [{"distance": "50", "date": "2023-05-15"}],
        "control_judges": [{"name": "Judge A", "role": "Control Judge"}]
    }

    # Create a copy with the same values for comparing
    stored_data = expected_data.copy()

    # Compare the data
    success, errors = data_validator._compare_event_data(expected_data, stored_data)

    assert success is True
    assert errors is None


def test_compare_event_data_missing_field(data_validator):
    """Test comparison when stored data is missing a field."""
    expected_data = {
        "source": "AERC",
        "ride_id": "test-123",
        "name": "Test Event",
        "region": "West"
    }

    stored_data = {
        "source": "AERC",
        "ride_id": "test-123",
        # Missing "name" field
        "region": "West"
    }

    # Compare the data
    success, errors = data_validator._compare_event_data(expected_data, stored_data)

    assert success is False
    assert len(errors) == 1
    assert "missing" in errors[0]


def test_compare_event_data_value_mismatch(data_validator):
    """Test comparison when a field value doesn't match."""
    expected_data = {
        "source": "AERC",
        "ride_id": "test-123",
        "name": "Test Event",
        "region": "West"
    }

    stored_data = {
        "source": "AERC",
        "ride_id": "test-123",
        "name": "Different Event Name",  # Different name
        "region": "West"
    }

    # Compare the data
    success, errors = data_validator._compare_event_data(expected_data, stored_data)

    assert success is False
    assert len(errors) == 1
    assert "mismatch" in errors[0]
    assert "name" in errors[0]


def test_compare_event_data_jsonb_fields(data_validator):
    """Test comparison with JSONB fields."""
    expected_data = {
        "source": "AERC",
        "ride_id": "test-123",
        "distances": [{"distance": "50", "date": "2023-05-15"}],
        "control_judges": [{"name": "Judge A", "role": "Control Judge"}]
    }

    # Stored data with JSONB fields as strings
    stored_data = {
        "source": "AERC",
        "ride_id": "test-123",
        "distances": json.dumps([{"distance": "50", "date": "2023-05-15"}]),
        "control_judges": json.dumps([{"name": "Judge A", "role": "Control Judge"}])
    }

    # Compare the data
    success, errors = data_validator._compare_event_data(expected_data, stored_data)

    assert success is True
    assert errors is None


def test_compare_event_data_skip_db_fields(data_validator):
    """Test that database-generated fields are skipped in comparison."""
    expected_data = {
        "source": "AERC",
        "ride_id": "test-123",
        "name": "Test Event"
    }

    stored_data = {
        "source": "AERC",
        "ride_id": "test-123",
        "name": "Test Event",
        "id": 42,  # Database-generated ID
        "created_at": "2023-05-15T10:00:00Z",  # Database timestamp
        "updated_at": "2023-05-15T11:00:00Z"   # Database timestamp
    }

    # Compare the data
    success, errors = data_validator._compare_event_data(expected_data, stored_data)

    assert success is True
    assert errors is None


def test_compare_event_data_invalid_jsonb(data_validator):
    """Test comparison with invalid JSONB data."""
    expected_data = {
        "source": "AERC",
        "ride_id": "test-123",
        "distances": [{"distance": "50", "date": "2023-05-15"}]
    }

    # Stored data with invalid JSON
    stored_data = {
        "source": "AERC",
        "ride_id": "test-123",
        "distances": "{invalid json"
    }

    # Compare the data
    success, errors = data_validator._compare_event_data(expected_data, stored_data)

    assert success is False
    assert len(errors) == 1
    assert "Could not parse JSONB field" in errors[0]
