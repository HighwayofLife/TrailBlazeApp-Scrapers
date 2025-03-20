"""Database management module for the TrailBlazeApp-Scrapers project."""

import json
from typing import Dict, Any, Optional, List, Union, Tuple
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import Json
from app.logging_manager import get_logger


class DatabaseManager:
    """
    Manages database interactions for the TrailBlazeApp-Scrapers project.

    Handles connection pooling, data insertion, updating, and retrieval
    for event data in the PostgreSQL database.
    """

    def __init__(self, db_config: Dict[str, str], scraper: Any = None) -> None:
        """
        Initialize DatabaseManager with database configuration.

        Args:
            db_config (Dict[str, str]): Database configuration parameters
            scraper (Any, optional): Scraper instance for metrics updates. Defaults to None.
        """
        self.db_config = db_config
        self.scraper = scraper # Store scraper instance
        self._connection_pool = None
        self.logger = get_logger(__name__).logger # Use LoggingManager logger
        self._create_connection_pool()

    def close_connection(self) -> None:
        """
        Closes the database connection.

        Should be called when the DatabaseManager is no longer needed to free up resources.
        """
        if self._connection_pool is not None:
            self._connection_pool.closeall()
            self.logger.info("Database connections closed")

    @contextmanager
    def connection(self):
        """
        Context manager for database connections.

        Creates a new connection, yields it for use in a with block, and ensures
        proper cleanup of resources when the block exits, even if an exception occurs.

        Yields:
            connection: Database connection object

        Raises:
            Exception: If connection creation fails
        """
        conn = None
        try:
            # Use directly the db_config with proper keys for PostgreSQL
            # Expected keys: host, port, dbname, user, password
            conn = psycopg2.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                dbname=self.db_config.get('database'),
                user=self.db_config.get('user'),
                password=self.db_config.get('password')
            )
            yield conn
        except Exception as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if conn is not None:
                conn.close()

    def insert_or_update_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Insert a new event or update an existing event in the database.

        Checks if an event with the same source and ride_id already exists.
        If it exists, updates the record; otherwise, inserts a new record.

        Args:
            event_data (Dict[str, Any]): Event data dictionary

        Returns:
            bool: True if operation was successful, False otherwise
        """
        source = event_data['source']
        ride_id = event_data['ride_id']

        if self._event_exists(source, ride_id):
            self._update_event(event_data)
            if self.scraper: # Check if scraper is provided
                self.scraper.metrics_manager.increment('database_updates') # Increment metric
            self.logger.info(f"Updated event: {source} - {ride_id}") # Use logging_manager
            return True
        else:
            self._insert_event(event_data)
            if self.scraper: # Check if scraper is provided
                self.scraper.metrics_manager.increment('database_inserts') # Increment metric
            self.logger.info(f"Inserted new event: {source} - {ride_id}") # Use logging_manager
            return True

    def _event_exists(self, source: str, ride_id: str) -> bool:
        """
        Check if an event with the given source and ride_id exists in the database.

        Args:
            source (str): Event source identifier (e.g., "AERC", "SERA")
            ride_id (str): Unique ride identifier within the source

        Returns:
            bool: True if event exists, False otherwise

        Raises:
            Exception: If database query fails
        """
        query = "SELECT EXISTS(SELECT 1 FROM events WHERE source = %s AND ride_id = %s);"
        result = self._execute_query(query, (source, ride_id))

        # The result is a tuple containing a single boolean value
        return result[0][0] if result else False

    def _insert_event(self, event_data: Dict[str, Any]) -> None:
        """
        Insert a new event record into the database.

        Constructs and executes an SQL INSERT statement with all event fields.
        Handles proper encoding of JSONB fields (control_judges, distances).

        Args:
            event_data (Dict[str, Any]): Complete event data dictionary

        Raises:
            Exception: If insert operation fails
        """
        # Convert control_judges and distances to JSONB format
        control_judges = Json(event_data.get('control_judges', []))
        distances = Json(event_data.get('distances', []))

        query = """
        INSERT INTO events (
            name, source, event_type, date_start, date_end, location_name,
            city, state, country, region, is_canceled, is_multi_day_event,
            is_pioneer_ride, ride_days, ride_manager, manager_email,
            manager_phone, website, flyer_url, has_intro_ride, ride_id,
            latitude, longitude, geocoding_attempted, description,
            control_judges, distances, directions
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
        """

        # Extract values from event_data, defaulting to None if not present
        params = (
            event_data.get('name'),
            event_data.get('source'),
            event_data.get('event_type'),
            event_data.get('date_start'),
            event_data.get('date_end'),
            event_data.get('location_name'),
            event_data.get('city'),
            event_data.get('state'),
            event_data.get('country'),
            event_data.get('region'),
            event_data.get('is_canceled'),
            event_data.get('is_multi_day_event'),
            event_data.get('is_pioneer_ride'),
            event_data.get('ride_days'),
            event_data.get('ride_manager'),
            event_data.get('manager_email'),
            event_data.get('manager_phone'),
            event_data.get('website'),
            event_data.get('flyer_url'),
            event_data.get('has_intro_ride'),
            event_data.get('ride_id'),
            event_data.get('latitude'),
            event_data.get('longitude'),
            event_data.get('geocoding_attempted', False),
            event_data.get('description'),
            control_judges,
            distances,
            event_data.get('directions')
        )

        self._execute_query(query, params)

    def _update_event(self, event_data: Dict[str, Any]) -> None:
        """
        Update an existing event record in the database.

        Updates all fields of an existing event based on source and ride_id.
        Ensures all fields are updated, even if they are NULL in the new data.
        Handles proper encoding of JSONB fields (control_judges, distances).

        Args:
            event_data (Dict[str, Any]): Updated event data dictionary

        Raises:
            Exception: If update operation fails
        """
        # Convert control_judges and distances to JSONB format
        control_judges = Json(event_data.get('control_judges', []))
        distances = Json(event_data.get('distances', []))

        query = """
        UPDATE events
        SET name = %s, event_type = %s, date_start = %s, date_end = %s,
            location_name = %s, city = %s, state = %s, country = %s,
            region = %s, is_canceled = %s, is_multi_day_event = %s,
            is_pioneer_ride = %s, ride_days = %s, ride_manager = %s,
            manager_email = %s, manager_phone = %s, website = %s,
            flyer_url = %s, has_intro_ride = %s, latitude = %s,
            longitude = %s, geocoding_attempted = %s, description = %s,
            control_judges = %s, distances = %s, directions = %s
        WHERE source = %s AND ride_id = %s;
        """

        # Extract values from event_data, defaulting to None if not present
        params = (
            event_data.get('name'),
            event_data.get('event_type'),
            event_data.get('date_start'),
            event_data.get('date_end'),
            event_data.get('location_name'),
            event_data.get('city'),
            event_data.get('state'),
            event_data.get('country'),
            event_data.get('region'),
            event_data.get('is_canceled'),
            event_data.get('is_multi_day_event'),
            event_data.get('is_pioneer_ride'),
            event_data.get('ride_days'),
            event_data.get('ride_manager'),
            event_data.get('manager_email'),
            event_data.get('manager_phone'),
            event_data.get('website'),
            event_data.get('flyer_url'),
            event_data.get('has_intro_ride'),
            event_data.get('latitude'),
            event_data.get('longitude'),
            event_data.get('geocoding_attempted', False),
            event_data.get('description'),
            control_judges,
            distances,
            event_data.get('directions'),
            # WHERE clause parameters
            event_data.get('source'),
            event_data.get('ride_id')
        )

        self._execute_query(query, params)

    def _execute_query(self, query: str, params: Optional[Union[tuple, Dict[str, Any]]] = None) -> Any:
        """
        Execute a parameterized SQL query safely.

        Handles connection management and parameterized query execution to prevent
        SQL injection. Can be used for any type of query (SELECT, INSERT, UPDATE, DELETE).

        Args:
            query (str): SQL query with parameter placeholders
            params (Optional[Union[tuple, Dict[str, Any]]]): Query parameters as tuple or dict.
                                                           Defaults to None.

        Returns:
            Any: Query results for SELECT queries, or None for other query types

        Raises:
            Exception: If query execution fails
        """
        result = None
        with self.connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(query, params)

                    # Check if the query is a SELECT query
                    if query.strip().upper().startswith("SELECT"):
                        result = cursor.fetchall()

                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    self.logger.error(f"Query execution error: {str(e)}")
                    self.logger.error(f"Query: {query}")
                    self.logger.error(f"Params: {params}")
                    raise

        return result

    def get_events_by_source(self, source: str) -> List[Dict[str, Any]]:
        """
        Retrieve all events from a specific source.

        Args:
            source (str): Event source identifier (e.g., "AERC", "SERA")

        Returns:
            List[Dict[str, Any]]: List of event dictionaries

        Raises:
            Exception: If query execution fails
        """
        query = "SELECT * FROM events WHERE source = %s;"
        rows = self._execute_query(query, (source,))

        if not rows:
            return []

        # Convert rows to list of dictionaries
        events = []
        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'events';")
                columns = [col[0] for col in cursor.fetchall()]

        for row in rows:
            event = {}
            for i, column in enumerate(columns):
                # Handle JSONB fields
                if column in ['control_judges', 'distances'] and row[i] is not None:
                    event[column] = json.loads(row[i]) if isinstance(row[i], str) else row[i]
                else:
                    event[column] = row[i]
            events.append(event)

        return events

    def get_event(self, source: str, ride_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific event by source and ride_id.

        Args:
            source (str): Event source identifier
            ride_id (str): Unique ride identifier

        Returns:
            Optional[Dict[str, Any]]: Event data dictionary or None if not found

        Raises:
            Exception: If query execution fails
        """
        query = "SELECT * FROM events WHERE source = %s AND ride_id = %s;"
        rows = self._execute_query(query, (source, ride_id))

        if not rows:
            return None

        # Convert row to dictionary
        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'events';")
                columns = [col[0] for col in cursor.fetchall()]

        row = rows[0]  # Get the first (and should be only) row
        event = {}
        for i, column in enumerate(columns):
            # Handle JSONB fields
            if column in ['control_judges', 'distances'] and row[i] is not None:
                event[column] = json.loads(row[i]) if isinstance(row[i], str) else row[i]
            else:
                event[column] = row[i]

        return event

    def delete_event(self, source: str, ride_id: str) -> bool:
        """
        Delete a specific event from the database.

        Args:
            source (str): Event source identifier
            ride_id (str): Unique ride identifier

        Returns:
            bool: True if event was deleted, False if event wasn't found

        Raises:
            Exception: If delete operation fails
        """
        # First check if the event exists
        if not self._event_exists(source, ride_id):
            self.logger.info(f"Event {source}-{ride_id} not found, nothing to delete")
            return False

        query = "DELETE FROM events WHERE source = %s AND ride_id = %s;"
        self._execute_query(query, (source, ride_id))

        # Verify deletion
        if not self._event_exists(source, ride_id):
            self.logger.info(f"Successfully deleted event: {source} - {ride_id}")
            return True

        self.logger.error(f"Failed to delete event: {source} - {ride_id}")
        return False

    def create_tables(self) -> None:
        """
        Create the necessary database tables if they don't exist.

        Creates the events table with all required columns and appropriate data types.
        Safe to call multiple times as it uses CREATE TABLE IF NOT EXISTS.

        Raises:
            Exception: If table creation fails
        """
        create_table_query = """
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            source VARCHAR(50) NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            date_start DATE NOT NULL,
            date_end DATE,
            location_name VARCHAR(255),
            city VARCHAR(100),
            state VARCHAR(100),
            country VARCHAR(100),
            region VARCHAR(50),
            is_canceled BOOLEAN DEFAULT FALSE,
            is_multi_day_event BOOLEAN DEFAULT FALSE,
            is_pioneer_ride BOOLEAN DEFAULT FALSE,
            ride_days INTEGER,
            ride_manager VARCHAR(255),
            manager_email VARCHAR(255),
            manager_phone VARCHAR(50),
            website VARCHAR(255),
            flyer_url VARCHAR(255),
            has_intro_ride BOOLEAN DEFAULT FALSE,
            ride_id VARCHAR(50),
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            geocoding_attempted BOOLEAN DEFAULT FALSE,
            description TEXT,
            control_judges JSONB,
            distances JSONB,
            directions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (source, ride_id)
        );
        """

        self._execute_query(create_table_query)
        self.logger.info("Events table created or already exists")

    def _create_connection_pool(self) -> None:
        """
        Create a connection pool for database connections.

        This is a placeholder for future implementation of connection pooling.
        Currently, connections are created as needed via the connection() context manager.
        """
        # This is a placeholder for future connection pooling implementation
        # For now, connections are created as needed via the connection() context manager
        self.logger.info("Database connection setup complete")
