# Database Interaction and Data Handling

This doc outlines the classes, functions, and methods required to interact with the PostgreSQL database, store scraped event data, and handle updates to existing records. Remember to use Test-Driven Development (TDD).

**Assumptions:**

*   You have a PostgreSQL database set up and running.
*   You have the database connection details (host, database name, user, password).
*   You will use a library like `psycopg2` or SQLAlchemy (Core or ORM) for database interaction.  This doc is agnostic to the specific choice, but examples below use general SQL concepts. *Choose one and be consistent*.
* We've decided to flatten the data, therefore we are no longer going to use an `Event` table, but instead just have the one table.

**Classes and Functions:**

1.  **`DatabaseManager` Class:**
    *   Responsible for all interactions with the PostgreSQL database.

    *   **`__init__(self, db_config)`:**
        *   Constructor. Takes a dictionary `db_config` containing the database connection parameters (host, database, user, password).
        *   Establishes a connection to the database (or creates a connection pool).

    *   **`close_connection(self)`:**
        *   Closes the database connection (or returns the connection to the pool).

    *   **`insert_or_update_event(self, event_data)`:**
        *   This is the *core* function. Takes a single event data dictionary (as produced by the scraper) as input.
        *   Checks if an event with the same `source` and `ride_id` already exists in the database.
        *   If the event exists, it updates the existing record with the new data.
        *   If the event does not exist, it inserts a new record.
        *   Handles potential database errors (e.g., connection errors, constraint violations).
        *    Uses helper functions (listed below) to perform the actual insertion and update operations.

    *   **`_event_exists(self, source, ride_id)`:**
        *   (Private helper function) Checks if an event with the given `source` and `ride_id` already exists in the database.
        *   Returns `True` if the event exists, `False` otherwise.

    *   **`_insert_event(self, event_data)`:**
        *   (Private helper function) Inserts a new event record into the database.
        *   Takes the `event_data` dictionary as input.
        *   Constructs and executes the appropriate SQL INSERT statement.
        *   Handles JSONB encoding for the `control_judges` and `distances` fields.

    *   **`_update_event(self, event_data)`:**
        *   (Private helper function) Updates an existing event record in the database.
        *   Takes the `event_data` dictionary as input.
        *   Constructs and executes the appropriate SQL UPDATE statement, updating *all* fields based on the provided data.  This ensures that even if a field is now missing in the scraped data, it will be updated (potentially to `NULL`).
        *   Handles JSONB encoding for the `control_judges` and `distances` fields.

    *   **`_execute_query(self, query, params=None)`:**
        *    Executes the query using the provided parameters
        *    Returns the results of the query

**Data Handling Logic (Within `insert_or_update_event`)**

1.  **Check for Existence:**
    *   Call `_event_exists(source, ride_id)` to determine if the event already exists.

2.  **Insert or Update:**
    *   If the event exists:
        *   Call `_update_event(event_data)`.
    *   If the event does not exist:
        *   Call `_insert_event(event_data)`.

**SQL Query Examples (Conceptual - Adapt to your chosen library):**

*   **`_event_exists`:**

    ```sql
    SELECT EXISTS(SELECT 1 FROM events WHERE source = %s AND ride_id = %s);
    ```

*   **`_insert_event`:**

    ```sql
    INSERT INTO events (name, source, event_type, date_start, date_end, location_name, city, state, country, region, is_canceled, is_multi_day_event, is_pioneer_ride, ride_days, ride_manager, manager_email, manager_phone, website, flyer_url, has_intro_ride,  ride_id, latitude, longitude, geocoding_attempted, description, control_judges, distances, directions)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s);
    ```

*   **`_update_event`:**

    ```sql
    UPDATE events
    SET name = %s, event_type = %s, date_start = %s, date_end = %s, location_name = %s, city = %s, state = %s, country = %s, region = %s, is_canceled = %s, is_multi_day_event = %s, is_pioneer_ride = %s, ride_days = %s, ride_manager = %s, manager_email = %s, manager_phone = %s, website = %s, flyer_url = %s, has_intro_ride = %s, latitude = %s, longitude = %s, geocoding_attempted = %s, description = %s, control_judges = %s::jsonb, distances = %s::jsonb, directions = %s
    WHERE source = %s AND ride_id = %s;
    ```

**Key Instructions:**

*   **"Follow TDD."** Write tests for each function *before* implementation.
*   **"Use parameterized queries."**  Use placeholders (`%s` in psycopg2, or named parameters) to prevent SQL injection vulnerabilities.  *Never* directly embed user-provided data into SQL queries.
*   **"Handle JSONB data correctly."** Use the appropriate functions in your chosen library to encode Python dictionaries as JSONB for storage in the database.
*   **"Handle database errors."** Use `try...except` blocks to catch potential database errors (e.g., connection errors, constraint violations) and handle them gracefully (log the error, potentially retry, etc.).
*   **"Ensure data consistency."** The `_update_event` function should update *all* fields, even if they are `NULL` in the incoming data. This ensures that the database reflects the latest scraped information.
*  **Use a context manager:** Use `with DatabaseManager(db_config) as db_manager:` to automatically handle opening and closing.
*  **Write unit tests for the execute_query method:** This should include mocking the database connection, creating sample queries.
