# Data Validation for Database Operations

This document describes how to validate that data inserted or updated in the database matches what was expected. The validation process ensures that your scraper correctly stores event data and helps identify any discrepancies.

## DataValidator Class

The `DataValidator` class provides methods to verify the success of database operations and validate the integrity of stored data.

### Key Features

1. **Schema Validation**: Ensures that data conforms to the expected schema using Pydantic models
2. **Existence Checks**: Verifies that records are properly inserted or deleted
3. **Data Comparison**: Compares expected data with what's actually stored in the database
4. **Detailed Error Messages**: Provides specific information about validation failures

## Using DataValidator

### Basic Setup

```python
from app.database import DatabaseManager
from app.data_validator import DataValidator

# Set up database manager
db_config = {
    "host": "localhost",
    "port": 5432,
    "database": "trailblaze",
    "user": "username",
    "password": "password"
}
db_manager = DatabaseManager(db_config)

# Create data validator
validator = DataValidator(db_manager)
```

### Validating Database Operations

After inserting or updating an event:

```python
# Insert an event
event_data = {
    "source": "AERC",
    "ride_id": "123",
    "name": "Desert Gold",
    # ... other event fields
}
db_manager.insert_or_update_event(event_data)

# Validate the operation
success, errors = validator.validate_database_operation(event_data, "insert")
if not success:
    print(f"Validation failed: {errors}")
```

### Validating Deletions

```python
# Delete an event
db_manager.delete_event("AERC", "123")

# Validate the deletion
success, errors = validator.validate_deletion("AERC", "123")
if not success:
    print(f"Deletion validation failed: {errors}")
```

## Integration with Scrapers

Here's how to integrate the DataValidator with your scraper:

```python
from app.base_scraper import BaseScraper
from app.database import DatabaseManager
from app.data_validator import DataValidator

class AERCScraper(BaseScraper):
    def run(self):
        # ... existing scraper code ...

        # Set up the validator
        validator = DataValidator(self.db_manager)
        validation_errors = []

        # Process events and validate
        for event_data in self.extract_all_events():
            # Insert/update the event
            self.db_manager.insert_or_update_event(event_data)

            # Validate the operation
            success, errors = validator.validate_database_operation(event_data)
            if not success:
                self.logger.warning(f"Validation failed for event {event_data['ride_id']}")
                validation_errors.extend(errors)

        # Check for validation errors
        if validation_errors:
            self.metrics_manager.increment('validation_errors', len(validation_errors))
            self.logger.error(f"Found {len(validation_errors)} validation errors")
            return False

        return True
```

## Tests and Examples

The DataValidator comes with comprehensive tests that demonstrate its functionality. These tests validate:

1. **Basic Functionality**: Initializing the validator, validating event data schema
2. **Database Operations**: Testing validation of database inserts, updates and deletions
3. **Data Comparison**: Testing comparison between expected and stored data
4. **Edge Cases**: Handling missing fields, value mismatches, and JSONB field comparison

To run the tests:

```bash
# Run DataValidator unit tests
python -m pytest tests/test_data_validator.py -v

# Run integration tests
python -m pytest tests/test_integration.py -v
```

The integration tests demonstrate how to use the DataValidator in a real scraper workflow to:

1. **Validate Successful Operations**: Verifying that data is properly stored
2. **Detect Data Mismatches**: Identifying when stored data doesn't match expectations
3. **Handle Special Data Types**: Properly comparing JSONB fields after storage

These tests serve as examples of how to integrate validation into your own scraper implementations.

## Best Practices

1. **Always Validate After Critical Operations**: Validate after inserts, updates, and deletes to ensure data integrity
2. **Handle Validation Errors Appropriately**: Log validation errors and take appropriate action (retry, alert, etc.)
3. **Include Validation In Test Suite**: Write tests that validate database operations to catch issues early
4. **Batch Validation**: For performance with large datasets, consider validating in batches
5. **Custom Validation Logic**: Extend the DataValidator if you need specific validation rules for your application

## Testing the DataValidator

The DataValidator itself has comprehensive tests in `tests/test_data_validator.py` that demonstrate its functionality and provide examples of how to use it.
