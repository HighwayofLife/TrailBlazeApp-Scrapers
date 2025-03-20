# Metrics, Logging, and Validation

This document describes how to add metrics collection, logging, and validation to the scraping process. The goal is to track key statistics, provide informative output to the user, and detect potential data discrepancies.

**Libraries:**

*   **`logging`:** Standard Python library for logging.
*   **`colorama`:** For color-coded output in the console. Install with `pip install colorama`.
*   **`emoji`:** For adding emojis to the output. Install with `pip install emoji`.

**Metrics to Collect:**

1.  **`raw_event_rows`:** The number of `calendarRow` elements found in the initial HTML.
2.  **`initial_events`:** The number of events extracted *before* multi-day event consolidation.
3.  **`final_events`:** The number of events in the final, consolidated output.
4.  **`multi_day_events`:**  The number of multi-day events that were identified
5.   **`database_inserts`:** The number of new events inserted into the database.
6.  **`database_updates`:** The number of existing events updated in the database.
7.   **`cache_hits`:** The number of times the HTML content was retrieved from the cache.
8. **`cache_misses`**: The number of times content needed to be fetched.

**Class and Function Modifications:**

1.  **`Scraper` Class:**

    *   **`__init__(self, source_name="AERC", cache_ttl=86400)`:**
        *   Initialize a dictionary `self.metrics` to store the metrics.  Initialize all the metrics listed above to 0.
        *   Initialize a logger instance: `self.logger = logging.getLogger(__name__)`. Configure the logger (level, format, handlers) appropriately. A basic setup would log to the console.

    *   **`scrape(self, url)`:**
        *   Log the start of the scraping process (including the URL).
        *   Reset metrics related to events to 0
        *   Increment cache metrics appropriately
        *   After scraping, call a new method `self.display_metrics()` (defined below) to print the metrics summary.

    *   **`parse_html(self, html_content)`:**
        *   After finding all `calendarRow` elements, update `self.metrics['raw_event_rows']` with the count.
        *   Log the number of `calendarRow` elements found.

    *   **`extract_event_data(self, soup)`:**
        *   Update `self.metrics['initial_events']` with the number of events extracted *before* consolidation.
        *   Log the number of events extracted before consolidation.

    *   **`_determine_multi_day_and_pioneer(self, distances, date_start)`:**
        *   If the event is determined to be multi-day, increment self.metrics['multi_day_events']

    *   **`create_final_output(self, consolidated_events)`:**
        *   Update `self.metrics['final_events']` with the number of events in the final output.
        * Log the number of events after consolidation

    *   **`display_metrics(self)`:**
        *   This new method is responsible for displaying the collected metrics in a user-friendly, color-coded format with emojis.
        *   Use `colorama` to add color (e.g., green for success, red for errors, yellow for warnings).
        *   Use `emoji` to add relevant emojis (e.g., ✅, ⚠️, ❌).
        *   Perform validation:
            *   Check if `raw_event_rows` matches the expected value (you'll need to determine how to define the "expected" value – possibly a configuration setting or a separate file).
            *   Check if `initial_events` minus `multi_day_events` equals `final_events`
            *   If discrepancies are found, log warning or error messages, clearly indicating the problem.
        *   Example output (conceptual):

            ```
            🚀 Scraping Summary:
            📜 Raw Event Rows Found: 25
            🗓️  Initial Events Extracted: 25
            ✨ Final Events (Consolidated): 23
            📅 Multi-Day Events: 2
            💾 Database Inserts: 10
            🔄 Database Updates: 13
            ✅ All counts are valid!

            ⚠️ Warning: Raw event rows (25) do not match expected count (20).
            ❌ Error: Initial events (26) - multi-day events (2) != final events (23). Data discrepancy!
            ```

2.  **`DatabaseManager` Class:**

    *   **`insert_or_update_event(self, event_data)`:**
        *   Increment `self.scraper.metrics['database_inserts']` if a new event is inserted.
        *   Increment `self.scraper.metrics['database_updates']` if an existing event is updated.
        *   Log whether an insert or update operation was performed.

    *   **`__init__(self, db_config, scraper)`:**
         *  Accept a scraper object so it can update metrics, in addition to db_config

3. **Cache Class:**
    *  **`get(self, key)`:**
        *  Increment `self.scraper.metrics['cache_hits']` if a cache hit occurs.

    *  **`set(self, key, value)`:**
        * Increment `self.scraper.metrics['cache_misses']` if a cache miss occurred.

    *   **`__init__(self, maxsize=128, ttl=86400, scraper=None)`:**
        * Add a scraper instance so it can modify the metrics

**Logging Levels:**

*   **`DEBUG`:** Detailed information, useful for debugging.
*   **`INFO`:** General information about the scraping process.
*   **`WARNING`:** Indicate potential problems or unexpected situations.
*   **`ERROR`:** Indicate errors that may have affected the results.
*   **`CRITICAL`:** Indicate severe errors that may prevent the scraper from continuing.

**Step-by-Step Instructions:**

1.  **Initialize Metrics:** In the `Scraper` constructor, create the `self.metrics` dictionary and initialize all metrics to 0.
2.  **Increment Metrics:** Throughout the scraping process (in the appropriate functions), increment the relevant metrics.
3.  **Logging:** Add log statements at key points:
    *   Start and end of scraping.
    *   Number of `calendarRow` elements found.
    *   Number of events before and after consolidation.
    *   Database insert/update operations.
    *   Cache hits/misses
    *   Any errors or warnings.
4.  **`display_metrics` Implementation:**
    *   Create the `display_metrics` function in the `Scraper` class.
    *   Use `colorama` and `emoji` to create formatted output.
    *   Implement the validation checks.
    *   Log warning/error messages for discrepancies.
5.  **DatabaseManager Integration:**
    * Pass the scraper into the DatabaseManager constructor.
    *   Modify `DatabaseManager` to increment the `database_inserts` and `database_updates` metrics.
6. Cache Integration
    * Pass the scraper into the Cache Constructor.
    * Increment cache_hits and cache_misses appropriately.
7. **Testing**
    * Create tests for display_metrics, that check all edge cases, and make sure the function can catch errors.

**Key Instructions:**

*   **"Use descriptive log messages."**
*   **"Use appropriate logging levels."**
*   **"Implement the `display_metrics` function with color-coded output and emojis."**
*   **"Perform validation checks and report discrepancies."**
*   **"Integrate metrics updates with `DatabaseManager`."**
* **"Test edge cases for display_metrics."**
