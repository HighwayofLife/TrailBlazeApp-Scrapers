# Class and Function Definitions (Scraper)

This doc outlines the necessary classes and functions for your AERC event scraping microservice.  Remember to implement these following the Test-Driven Development (TDD) methodology. Write the tests *before* you write the implementation code.

**Classes:**

1.  **`Scraper`:**
    *   Main class responsible for orchestrating the scraping process.
    * It should handle requesting and processing data from URLs.

2.  **`Event`:**
    *   A data class representing a single endurance riding event.  This class should mirror the expected JSON data structure but does *not* need to be a formal Pydantic model (though it could be). This provides a convenient way to represent data during processing.

**Functions (within the `Scraper` class):**

1.  **`__init__(self, source_name="AERC")`:**
    *   Constructor for the `Scraper` class. Initializes the source name (defaulting to "AERC").

2.  **`scrape(self, url)`:**
    *   Main entry point for scraping. Takes a URL as input, retrieves the HTML, parses it, and returns a dictionary of consolidated event data.

3.  **`get_html(self, url)`:**
    *   Retrieves the HTML content from the given URL. Handles HTTP requests and potential errors (timeouts, 404s, etc.).

4.  **`parse_html(self, html_content)`:**
    *   Parses the given HTML content using BeautifulSoup and returns a BeautifulSoup object.

5.  **`extract_event_data(self, soup)`:**
    *   Extracts data for all events from the BeautifulSoup object (representing the entire page).  Returns a list of dictionaries, one for each event *row* (before consolidation). Calls the helper functions below.

6.  **`_extract_name_and_id(self, calendar_row)`:**
    *   (Helper function) Extracts the event name, ride ID, and cancellation status from a single event row (`calendarRow`).

7.  **`_extract_region_date_location(self, calendar_row)`:**
    *   (Helper function) Extracts the region, start date, and location name from a single event row.

8.  **`_extract_manager_info(self, calendar_row)`:**
    *   (Helper function) Extracts the ride manager's name from a single event row.

9. **`_extract_website_flyer(self, calendar_row)`:**
     *  (Helper function) extract the website and/or flyer urls

10. **`_extract_details(self, calendar_row)`:**
    *   (Helper function) Extracts detailed information (location, manager details, control judges, distances, description, directions) from the expanded details section of a single event row.

11. **`_determine_event_type(self, calendar_row)`:**
    *   (Helper function) Determines the event type (defaults to "endurance").

12. **`_determine_has_intro_ride(self, calendar_row)`:**
    *   (Helper function) Determines if the event has an intro ride.

13. **`_determine_multi_day_and_pioneer(self, distances, date_start)`:**
    *   (Helper function) Determines if the event is multi-day or a pioneer ride, calculates the number of ride days, and determines the end date.

14. **`_consolidate_events(self, all_events)`:**
    *  Takes a list of events that might have same RideID, and consolidates to combine multi-day events.

15. **`_create_event_object(self, event_data)`:**
    * Takes the dictionary for a single event, and returns an `Event` data object.

16. **`create_final_output(self, consolidated_events)`:**
     * Transforms a dictionary of events into the final output for the service, which is a dictionary keyed by filenames
**Utility Functions (Outside the `Scraper` class):**

These are general-purpose functions that could be used in multiple places.  Place them in a separate module (e.g., `utils.py`) if desired.

1.  **`parse_date(date_string)`:**
    *   Parses a date string (potentially in various formats) and returns a standardized date object (YYYY-MM-DD).

2.  **`parse_time(time_string)`:**
    *   Parses a time string (e.g., "07:00 am") and returns a standardized time object.

3.  **`extract_city_state_country(location_string)`:**
    *  Takes the location string as input and determines city, state, and country

4. **`generate_file_name(ride_id, source)`**
    * Creates a standardized filename based on the ride ID.

**Key Instructions:**

*   **"Follow TDD."**  Remind the AI to write tests *before* implementing each function.
*   **"Use type hints."**  Encourage the use of type hints for function parameters and return values (e.g., `def get_html(self, url: str) -> str:`).
*   **"Handle errors gracefully."**  Functions should handle potential errors (e.g., invalid input, missing data) and either return appropriate values (e.g., `None`) or raise exceptions as needed.
*   **"Keep functions focused."** Each function should have a single, well-defined purpose.
*    **"Document your functions."**  Include docstrings to explain the purpose, parameters, and return values of each function.
