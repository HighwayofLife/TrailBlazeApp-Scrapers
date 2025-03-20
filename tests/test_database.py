"""Tests for the DatabaseManager module."""

import json
import os
import pytest
from unittest.mock import MagicMock, patch
from app.database import DatabaseManager


@pytest.fixture
def fixtures_path():
    """Fixture for the fixtures directory path."""
    return os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.fixture
def expected_data(fixtures_path):
    """Load expected data from fixtures."""
    with open(os.path.join(fixtures_path, 'expected_data.json'), 'r') as f:
        return json.load(f)


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
def mock_scraper():
    """Fixture for mock scraper with metrics."""
    scraper = MagicMock()
    scraper.metrics = {"database_inserts": 0, "database_updates": 0}
    return scraper


@pytest.fixture
def db_manager(db_config, mock_scraper):
    """Fixture for DatabaseManager instance."""
    return DatabaseManager(db_config, mock_scraper)


@pytest.fixture
def sample_event(expected_data):
    """Fixture for sample event data using the Old Pueblo event from fixtures."""
    return expected_data["old_pueblo_event.html"]


def test_connection_context_manager(db_manager):
    """Test database connection context manager."""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        with db_manager.connection() as conn:
            assert conn == mock_connect.return_value

        mock_conn.close.assert_called_once()


def test_event_exists(db_manager, sample_event):
    """Test checking if event exists in database."""
    with patch.object(db_manager, '_execute_query') as mock_execute:
        mock_execute.return_value = True
        assert db_manager._event_exists("AERC", sample_event["ride_id"]) is True
        mock_execute.assert_called_once()


def test_insert_event(db_manager, sample_event, mock_scraper):
    """Test inserting new event."""
    with patch.object(db_manager, '_execute_query') as mock_execute:
        db_manager._insert_event(sample_event)
        mock_execute.assert_called_once()
        assert mock_scraper.metrics["database_inserts"] == 1


def test_update_event(db_manager, sample_event, mock_scraper):
    """Test updating existing event."""
    with patch.object(db_manager, '_execute_query') as mock_execute:
        db_manager._update_event(sample_event)
        mock_execute.assert_called_once()
        assert mock_scraper.metrics["database_updates"] == 1


def test_insert_or_update_event_new(db_manager, sample_event):
    """Test insert_or_update_event with new event."""
    with patch.object(db_manager, '_event_exists') as mock_exists, \
         patch.object(db_manager, '_insert_event') as mock_insert, \
         patch.object(db_manager, '_update_event') as mock_update:

        mock_exists.return_value = False
        result = db_manager.insert_or_update_event(sample_event)

        mock_exists.assert_called_once_with(sample_event["source"], sample_event["ride_id"])
        mock_insert.assert_called_once_with(sample_event)
        mock_update.assert_not_called()
        assert result is True


def test_insert_or_update_event_existing(db_manager, sample_event):
    """Test insert_or_update_event with existing event."""
    with patch.object(db_manager, '_event_exists') as mock_exists, \
         patch.object(db_manager, '_insert_event') as mock_insert, \
         patch.object(db_manager, '_update_event') as mock_update:

        mock_exists.return_value = True
        result = db_manager.insert_or_update_event(sample_event)

        mock_exists.assert_called_once_with(sample_event["source"], sample_event["ride_id"])
        mock_update.assert_called_once_with(sample_event)
        mock_insert.assert_not_called()
        assert result is True


def test_execute_query(db_manager):
    """Test query execution with parameters."""
    with patch.object(db_manager, 'connection') as mock_ctx:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        query = "SELECT * FROM events WHERE id = %s"
        params = (1,)
        db_manager._execute_query(query, params)

        mock_cursor.execute.assert_called_once_with(query, params)


def test_execute_query_error(db_manager):
    """Test query execution error handling."""
    with patch.object(db_manager, 'connection') as mock_ctx:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            db_manager._execute_query("SELECT 1")


def test_get_events_by_source(db_manager, expected_data):
    """Test retrieving all events from a specific source."""
    # Create a list of events from the same source
    events = [event for event in expected_data.values() if event["source"] == "AERC"]
    
    with patch.object(db_manager, '_execute_query') as mock_execute:
        mock_execute.return_value = events
        result = db_manager.get_events_by_source("AERC")
        
        assert result == events
        mock_execute.assert_called_once()


def test_get_event(db_manager, sample_event):
    """Test retrieving a specific event by source and ride_id."""
    with patch.object(db_manager, '_execute_query') as mock_execute:
        mock_execute.return_value = [sample_event]
        result = db_manager.get_event(sample_event["source"], sample_event["ride_id"])
        
        assert result == sample_event
        mock_execute.assert_called_once()


def test_get_event_not_found(db_manager):
    """Test retrieving a non-existent event."""
    with patch.object(db_manager, '_execute_query') as mock_execute:
        mock_execute.return_value = []
        result = db_manager.get_event("AERC", "non-existent-id")
        
        assert result is None
        mock_execute.assert_called_once()


def test_delete_event(db_manager, sample_event):
    """Test deleting an event."""
    with patch.object(db_manager, '_execute_query') as mock_execute:
        mock_execute.return_value = 1  # Rows affected
        result = db_manager.delete_event(sample_event["source"], sample_event["ride_id"])
        
        assert result is True
        mock_execute.assert_called_once()


def test_delete_event_not_found(db_manager):
    """Test deleting a non-existent event."""
    with patch.object(db_manager, '_execute_query') as mock_execute:
        mock_execute.return_value = 0  # No rows affected
        result = db_manager.delete_event("AERC", "non-existent-id")
        
        assert result is False
        mock_execute.assert_called_once()


def test_create_tables(db_manager):
    """Test creating database tables."""
    with patch.object(db_manager, '_execute_query') as mock_execute:
        db_manager.create_tables()
        mock_execute.assert_called_once()


@pytest.fixture
def multi_day_event(expected_data):
    """Fixture for a multi-day event from fixtures."""
    return expected_data["cuyama_pioneer_event.html"]


@pytest.fixture
def cancelled_event(expected_data):
    """Fixture for a cancelled event from fixtures."""
    return expected_data["biltmore_cancelled_event.html"]


def test_insert_multi_day_event(db_manager, multi_day_event):
    """Test inserting a multi-day event."""
    with patch.object(db_manager, '_execute_query') as mock_execute:
        db_manager._insert_event(multi_day_event)
        mock_execute.assert_called_once()
        # Verify the query contains the correct parameters for a multi-day event
        args = mock_execute.call_args[0]
        assert "is_multi_day_event" in args[0]


def test_insert_cancelled_event(db_manager, cancelled_event):
    """Test inserting a cancelled event."""
    with patch.object(db_manager, '_execute_query') as mock_execute:
        db_manager._insert_event(cancelled_event)
        mock_execute.assert_called_once()
        # Verify the query contains the correct parameters for a cancelled event
        args = mock_execute.call_args[0]
        assert "is_canceled" in args[0]
