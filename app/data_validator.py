"""Data validation module for the TrailBlazeApp-Scrapers project."""

from typing import Dict, Any, List, Optional, Tuple
import json
from app.database import DatabaseManager
from app.models import EventDataModel
from app.exceptions import ValidationError
from app.logging_manager import get_logger


class DataValidator:
    """
    Class responsible for validating database operations.

    Provides methods to verify that data inserted/updated in the database
    matches what was expected from the scraper.
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        """
        Initialize the DataValidator with a database manager.

        Args:
            db_manager (DatabaseManager): Database manager instance to use for database operations
        """
        self.db_manager = db_manager
        self.logger = get_logger(__name__).logger

    def validate_database_operation(self, event_data: Dict[str, Any],
                                   expected_operation: str = "insert_or_update") -> Tuple[bool, Optional[List[str]]]:
        """
        Validate that a database operation was successful and data matches what was expected.

        Args:
            event_data (Dict[str, Any]): The event data that was supposed to be inserted/updated
            expected_operation (str): The expected operation type, one of "insert", "update",
                                     or "insert_or_update" (default)

        Returns:
            Tuple[bool, Optional[List[str]]]: A tuple containing:
                - Success flag (True if validation succeeded)
                - List of validation error messages (None if validation succeeded)
        """
        # Ensure event data is valid
        self._validate_event_data(event_data)

        # Get the stored event data
        source = event_data["source"]
        ride_id = event_data["ride_id"]
        stored_event = self.db_manager.get_event(source, ride_id)

        # If expected operation was insert, the event should exist
        if expected_operation in ["insert", "insert_or_update"] and stored_event is None:
            error_msg = f"Event {source}-{ride_id} was not found in database after insert operation"
            self.logger.error(error_msg)
            return False, [error_msg]

        # If expected operation was delete, the event should not exist
        if expected_operation == "delete" and stored_event is not None:
            error_msg = f"Event {source}-{ride_id} still exists in database after delete operation"
            self.logger.error(error_msg)
            return False, [error_msg]

        # For insert or update, compare the data
        if expected_operation in ["insert", "update", "insert_or_update"] and stored_event is not None:
            return self._compare_event_data(event_data, stored_event)

        return True, None

    def validate_deletion(self, source: str, ride_id: str) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate that an event was successfully deleted from the database.

        Args:
            source (str): Event source identifier
            ride_id (str): Unique ride identifier

        Returns:
            Tuple[bool, Optional[List[str]]]: A tuple containing:
                - Success flag (True if validation succeeded)
                - List of validation error messages (None if validation succeeded)
        """
        stored_event = self.db_manager.get_event(source, ride_id)

        if stored_event is not None:
            error_msg = f"Event {source}-{ride_id} still exists in database after delete operation"
            self.logger.error(error_msg)
            return False, [error_msg]

        self.logger.info(f"Successfully validated deletion of event {source}-{ride_id}")
        return True, None

    def _validate_event_data(self, event_data: Dict[str, Any]) -> None:
        """
        Validate that event data conforms to the expected schema.

        Args:
            event_data (Dict[str, Any]): Event data to validate

        Raises:
            ValidationError: If event data is invalid
        """
        try:
            # Use our Pydantic model to validate the event data
            EventDataModel(**event_data)
        except Exception as e:
            raise ValidationError(f"Invalid event data: {str(e)}") from e

    def _compare_event_data(self, expected_data: Dict[str, Any],
                           stored_data: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        """
        Compare expected event data with what is stored in the database.

        Args:
            expected_data (Dict[str, Any]): The expected event data
            stored_data (Dict[str, Any]): The event data retrieved from the database

        Returns:
            Tuple[bool, Optional[List[str]]]: A tuple containing:
                - Success flag (True if data matches)
                - List of validation error messages (None if data matches)
        """
        discrepancies = []

        # Compare all fields in expected_data
        for key, expected_value in expected_data.items():
            # Skip comparison for database-generated fields
            if key in ["id", "created_at", "updated_at"]:
                continue

            if key not in stored_data:
                discrepancies.append(f"Field '{key}' is missing in stored data")
                continue

            stored_value = stored_data[key]

            # Handle special case for JSONB fields (they may need to be parsed)
            if key in ["control_judges", "distances"] and isinstance(stored_value, str):
                try:
                    stored_value = json.loads(stored_value)
                except json.JSONDecodeError:
                    discrepancies.append(f"Could not parse JSONB field '{key}': {stored_value}")
                    continue

            # Compare values
            if expected_value != stored_value:
                discrepancies.append(
                    f"Field '{key}' value mismatch: expected={expected_value}, stored={stored_value}"
                )

        # Report results
        if discrepancies:
            discrepancy_str = "\n- ".join([""] + discrepancies)
            error_msg = f"Data validation failed for {expected_data['source']}-{expected_data['ride_id']}:{discrepancy_str}"
            self.logger.error(error_msg)
            return False, discrepancies

        self.logger.info(
            f"Successfully validated event data for {expected_data['source']}-{expected_data['ride_id']}"
        )
        return True, None
