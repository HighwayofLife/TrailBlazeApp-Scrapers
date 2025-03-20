# Multi-Scraper Framework Design Document

**1. Overview**

This document outlines a framework for building and managing multiple web scrapers, each targeting a different source of event data (e.g., AERC, SERA, specific event websites). The framework will provide a common structure for scraping, data processing, database interaction, caching, logging, and metrics, while allowing individual scrapers to customize their behavior as needed.

**2. Design Principles**

*   **Modularity:** Each scraper will be a separate module, independent but conforming to a common interface.
*   **Extensibility:** Adding new scrapers should be straightforward, requiring minimal changes to the core framework.
*   **Reusability:** Common functionality (database interaction, caching, logging) will be shared across all scrapers.
*   **Maintainability:**  Clear separation of concerns and consistent coding practices will improve maintainability.
*   **Testability:**  The design will facilitate unit and integration testing.

**3. Framework Components**

*   **Abstract Base Scraper:** An abstract base class (`BaseScraper`) will define the common interface for all scrapers. This ensures consistency and provides a blueprint for new scrapers.
*   **Concrete Scrapers:** Each specific scraper (e.g., `AERCScraper`, `SERAScraper`) will inherit from the `BaseScraper` and implement the abstract methods.
*   **Database Manager:** A single `DatabaseManager` class will handle all database interactions for all scrapers.
*   **Cache:** A single `Cache` class will handle caching of fetched HTML content, used by all scrapers.
*   **Configuration:** A `config.py` file will manage configuration settings, including database credentials, cache TTL, and scraper-specific settings.
*   **Utilities:** A `utils.py` module will contain helper functions used by multiple components.
*   **Metrics and Logging:**  Centralized logging and metrics collection, integrated into the `BaseScraper` and used by all concrete scrapers.
*   **Main Script:** A `main.py` (or similar) script will orchestrate the scraping process, allowing users to run specific scrapers or all scrapers.

**4. Abstract Base Class: `BaseScraper`**

The `BaseScraper` defines the following abstract methods (methods that *must* be implemented by concrete scraper classes):

*   `scrape(self, url)`:  The main entry point for scraping. Takes a URL, fetches the HTML, processes it, and returns a list of event data dictionaries.
*   `parse_html(self, html_content)`: Parses the HTML content and extracts event data. Returns a list of dictionaries, one for each event.
*   `get_source_name(self)`: Returns a string representing the source name (e.g., "AERC", "SERA").

The `BaseScraper` *also* provides the following *concrete* methods (methods with default implementations that can be overridden if needed):

*   `__init__(self, cache_ttl=86400)`: Constructor. Initializes the cache, logger, and metrics.
*   `get_html(self, url)`:  Fetches HTML, handling caching (using the `Cache` class).
*   `_consolidate_events(self, all_events)`: Consolidates multi-day events (same logic for all scrapers).
*    `create_final_output(self, consolidated_events)`: Formats the data into a standard output for the database.
*   `display_metrics(self)`: Displays the collected metrics.

**5. Concrete Scraper Example: `AERCScraper`**

The `AERCScraper` would implement the abstract methods from `BaseScraper`:

*   `scrape(self, url)`: Calls `get_html`, `parse_html`, and `_consolidate_events`.
*   `parse_html(self, html_content)`:  Implements the AERC-specific HTML parsing logic (using BeautifulSoup), calling the helper functions we defined earlier (_extract_name_and_id, _extract_details etc.).
*   `get_source_name(self)`: Returns "AERC".

It would also contain AERC *specific helper functions* like:
*   **`_extract_name_and_id(self, calendar_row)`**
*   **`_extract_region_date_location(self, calendar_row)`**
*   **`_extract_manager_info(self, calendar_row)`**
* **`_extract_website_flyer(self, calendar_row)`**
*   **`_extract_details(self, calendar_row)`**
*   **`_determine_event_type(self, calendar_row)`**
*   **`_determine_has_intro_ride(self, calendar_row)`**
*   **`_determine_multi_day_and_pioneer(self, distances, date_start)`**

**6. File Structure**

```
project_root/
├── app/
│   ├── main.py          # Main script to run scrapers
│   ├── config.py        # Configuration settings
│   ├── utils.py         # Utility functions
│   ├── database.py      # DatabaseManager class
│   ├── cache.py         # Cache class
│   ├── base_scraper.py  # Abstract BaseScraper class
│   └── scrapers/        # Directory for concrete scraper implementations
│       ├── aerc_scraper.py    # AERCScraper class
│       ├── sera_scraper.py   # (Example) SERAScraper class
│       └── __init__.py
└── tests/           # Unit and integration tests
│   ├── fixtures/    # Sample HTML files for testing
│   ├── test_aerc_scraper.py
│   ├── test_base_scraper.py
│   ├── test_cache.py
│   ├── test_database.py
│   └── test_utils.py
├── requirements.txt # Project dependencies
├── .env             # Local environment variables (not committed)
└── Dockerfile       # Docker configuration
```

**7. Workflow**

1.  **Configuration:**  `config.py` loads configuration from environment variables and/or a `.env` file.
2.  **Instantiation:** `main.py` creates instances of the desired scrapers (e.g., `AERCScraper`, `SERAScraper`).
3.  **Scraping:** For each scraper, `main.py` calls the `scrape(url)` method.
4.  **HTML Retrieval:**  The `get_html` method (in `BaseScraper`) checks the cache.  If the HTML is not cached, it fetches it from the URL and stores it in the cache.
5.  **Parsing:**  The `parse_html` method (implemented in the concrete scraper) extracts event data from the HTML.
6.  **Consolidation:**  The `_consolidate_events` method (in `BaseScraper`) combines multi-day events.
7. **Formatting:** The `create_final_output` method creates a dictionary keyed by filenames.
8.  **Database Storage:** The `DatabaseManager` (called from `main.py`) inserts or updates the event data in the database.
9.  **Metrics and Logging:**  Metrics are collected throughout the process, and logs are written to standard output.
10. **Display Metrics:** The `display_metrics()` method is invoked to present results.

**8. Adding New Scrapers**

To add a new scraper (e.g., `SERAScraper`):

1.  Create a new file `sera_scraper.py` in the `scrapers` directory.
2.  Create a `SERAScraper` class that inherits from `BaseScraper`.
3.  Implement the required abstract methods (`scrape`, `parse_html`, `get_source_name`).
4.  Add any scraper-specific helper functions.
5.  Write unit tests for the new scraper in `tests/test_sera_scraper.py`.
6.  Update `main.py` to include the new scraper (if desired).
