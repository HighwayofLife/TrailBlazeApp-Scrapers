# TDD Strategy

1.  **Red-Green-Refactor Cycle:** Emphasize the core TDD cycle:
    *   **Red:** Write a failing test. *First* write a test that *will* fail because the implementation code doesn't exist yet.
    *   **Green:** Write the *minimum* amount of code necessary to make the test pass.
    *   **Refactor:** Clean up the code (both the implementation and the test) while ensuring the test still passes.
2.  **Test-First Mentality:** *Always* write the test *before* writing any implementation code for a specific feature or function.
3.  **Small, Focused Tests:** Each test should focus on a single, well-defined aspect of the functionality.  Avoid large, complex tests that cover too much ground.
4. **Mock external requests:** Since we are creating a test suite for a scraper, we should mock the external requests to avoid hitting the server and to create deterministic testing.

**Pytest Structure and Test Cases**

**Phase 1: Setup and Project Structure**

1.  **Project Structure:**
    *   Create a `tests` directory at the project root.
    *   Within `tests`, create a file `test_scraper.py`.  This is where the tests will live.
    *   Create a subdirectory `tests/fixtures` to store sample HTML files for testing.
    *   Create a file for the scraper code, `scraper.py`

2.  **Imports:** In `test_scraper.py`, import necessary modules:
    *   `pytest`
    *   The functions from your scraper module (even if they don't exist yet – this is part of TDD).  For example: `from scraper import get_html, parse_html, extract_event_data, ...`
    *    `requests_mock` for creating mock responses.
3.  **Fixtures:** Explain the concept of Pytest fixtures: reusable setup code for tests.

**Phase 2: Test Cases (Organized by Functionality)**

Here's a breakdown of test cases, organized by the functions you'll likely have in your scraper.  For *each* test case, follow the Red-Green-Refactor cycle *strictly*.

**2.1. `get_html` (and related functions)**

*   **Test Case: `test_get_html_success`**
    *   **Purpose:** Test successful retrieval of HTML content.
    *   **Setup:** Use `requests_mock` to mock a successful GET request to a sample URL (e.g., "http://example.com/events"). Return a 200 status code and some simple, valid HTML content (can be stored in `tests/fixtures`).
    *   **Action:** Call `get_html` with the sample URL.
    *   **Assertion:** Assert that the returned value is the expected HTML content (as a string).
*   **Test Case: `test_get_html_failure_404`**
    *   **Purpose:** Test handling of a 404 Not Found error.
    *   **Setup:** Use `requests_mock` to mock a GET request that returns a 404 status code.
    *   **Action:** Call `get_html`.
    *   **Assertion:** Assert that an appropriate exception is raised (e.g., a custom `ScrapingError` or a `requests.HTTPError`).
*   **Test Case: `test_get_html_timeout`**
    *   **Purpose:** Test handling of a request timeout.
    *   **Setup:** Use `requests_mock` to mock a request that times out.
    *   **Action:** Call `get_html`.
    *   **Assertion:** Assert that an appropriate exception is raised (e.g., `requests.Timeout`).

**2.2. `parse_html`**

*   **Test Case: `test_parse_html_valid`**
    *   **Purpose:** Test successful parsing of valid HTML.
    *   **Setup:**  Provide valid HTML content (as a string) – ideally, a small, self-contained snippet representing a single event block.  This can come from a fixture file.
    *   **Action:** Call `parse_html` with the valid HTML.
    *   **Assertion:** Assert that the returned value is a `BeautifulSoup` object.  You can check this using `isinstance(result, BeautifulSoup)`.
*   **Test Case: `test_parse_html_invalid`**
    *   **Purpose:** Test handling of invalid HTML.
    *   **Setup:** Provide invalid HTML content (e.g., malformed tags).
    *   **Action:** Call `parse_html`.
    *   **Assertion:** Assert that an appropriate exception is raised (or that the function handles the invalid HTML gracefully in a defined way).  This might depend on how you want to handle errors.

**2.3. Helper Functions (e.g., `extract_name_and_id`, `extract_region_date_location`, etc.)**

For *each* helper function identified:

*   **Test Case: `test_[function_name]_basic`**
    *   **Purpose:** Test the basic, successful extraction of data.
    *   **Setup:** Create a Pytest fixture that uses `BeautifulSoup` to parse a *small* HTML snippet representing the *specific* part of the HTML that the helper function is responsible for.  For example, for `extract_name_and_id`, the fixture would contain just the relevant `span` element. This keeps tests focused.
    *   **Action:** Call the helper function with the parsed HTML snippet (from the fixture).
    *   **Assertion:** Assert that the returned value(s) match the expected data from the HTML snippet. Use precise assertions (e.g., `assert name == "Original Old Pueblo"`).
*   **Test Case: `test_[function_name]_missing_data`**
    *   **Purpose:** Test the function's behavior when expected data is missing.
    *   **Setup:** Create a fixture with HTML that is *missing* the element or attribute the function is trying to extract.
    *   **Action:** Call the helper function.
    *   **Assertion:** Assert that the function returns an appropriate value (e.g., `None`, an empty string, or raises a specific exception, depending on your design).
*   **Test Case: `test_[function_name]_edge_cases`**
    *   **Purpose:** Test any edge cases or unusual input.  Examples:
        *   For `extract_manager_info`, test with extra whitespace around the manager's name.
        *   For `extract_region_date_location`, test with different date formats (if you expect variations).
        *   For functions dealing with cancellation, test with and without the cancellation notice.
* **Test Case: for extract_details, test_extract_details_multi_day:**
    *   Specifically test that the date_end, is_multi_day_event, is_pioneer_ride and ride_days are properly determined when processing multiple dates within a single ride.

**2.4. `extract_event_data` (Integration Test)**

*   **Test Case: `test_extract_event_data_single_day`**
    *   **Purpose:** Test the integration of all helper functions for a single-day event.
    *   **Setup:** Create a fixture containing a complete, valid HTML snippet for a *single-day* event (from `tests/fixtures`).
    *   **Action:** Call `extract_event_data` with the parsed HTML of the event block.
    *   **Assertion:** Assert that the returned dictionary matches the expected data structure *exactly*.  Compare against a pre-defined dictionary containing the expected values.
*   **Test Case: `test_extract_event_data_multi_day`**
    *   **Purpose:** Test the integration for a *multi-day* event.
    *   **Setup:** Use a fixture with HTML for a multi-day event (like the "Cuyama XP Pioneer" example).
    *   **Action:** Call `extract_event_data`.
    *   **Assertion:** Assert that the returned dictionary is correct, paying close attention to `date_end`, `is_multi_day_event`, `is_pioneer_ride`, `ride_days`, and the combined `distances` list.

**2.5 Consolidate Multi-day Events:**

*   **Test Case: `test_consolidate_events_single`**
     * Test with a single day event, and verify it works with the consolidate events function
*    **Test Case: `test_consolidate_events_multiple`**
    *  Create a list of dictionaries, similar to the output of a non-consolidated scrape. Use a multi-day event to create at least 2 dictionaries in the list
    * Assert that the dictionaries have properly consolidated

**Phase 3: Iterative Development**

1.  **Iterate:**  You should always repeat the Red-Green-Refactor cycle for each function and test case, gradually building up the complete scraper and its test suite.
2.  **Refactoring:**  After each "Green" phase, look for opportunities to refactor (improve) the code *without* changing its functionality.  The tests should continue to pass after refactoring.
3.  **Regression:**  Run *all* tests frequently (ideally after every change) to ensure that new code doesn't break existing functionality (regression testing).

**Key Instructions:**

*   **"Write the test *first*."** Repeat this constantly.
*   **"Make the test *fail* initially."**
*   **"Write the *minimum* code to pass the test."**
*   **"Use descriptive test names."** (e.g., `test_extract_name_and_id_success`)
*   **"Use assertions effectively."** Be specific in your assertions.
*   **"Use fixtures to manage test setup."**
* **Use Mocks to handle requests and responses**
*   **"Keep tests small and focused."**
* **"Think about edge cases and error handling."**
*  **Run all tests frequently**
