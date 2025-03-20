# Scraping Guide for the AERC Calendar

This document provides a detailed guide for scraping the AERC calendar. The goal is to extract event data from the AERC website and store it in a structured format for further processing.
The scraping process is divided into several phases, each with specific steps and requirements. This guide will cover the data structure, database schema, and step-by-step instructions for implementing the scraping logic.


**Phase 1: Data Structure and Database Schema**
(complete)

**Phase 2: Scraping Implementation (Step-by-Step Instructions)**

Use libraries like `requests` (or similar) and `BeautifulSoup4`. Add to `requirements.txt`

**Step 1: Request the HTML**

1.  **Input:**
  ### AERC URLs
  - base_url: "https://aerc.org/wp-admin/admin-ajax.php"
  - calendar_url: "https://aerc.org/calendar" (URL to scrape)

  ### Additional headers for AERC site
  - "Referer": "https://aerc.org/",
  - "Sec-Fetch-Dest": "document",
  - "Sec-Fetch-Mode": "navigate",
  - "Sec-Fetch-Site": "same-origin",
  - "Sec-Fetch-User": "?1",
  - "Upgrade-Insecure-Requests": "1"
  - Need headers for User-Agent, Accept-Language, etc. to mimic a real browser request.

1.  **Action:** Use the `requests` library (or equivalent) to make an HTTP GET request to the provided URL.
    * **Note:** If the TTL on the cache is not expired, use the cached HTML file instead of making a new request.  This can be done using Python's built-in file handling methods.
2.  **Error Handling:**
    *   Check the HTTP status code. If it's not 200 (OK), raise an exception or log an error, indicating the URL is invalid or the server is unreachable.
    *   Handle potential network errors (e.g., timeouts, connection errors) using `try...except` blocks.
3.  **Output:** If the request is successful, store the HTML content (response.text) in a variable.
4.  **Cache the HTML:** Save the HTML content to a file (e.g., `cache/aerc_calendar_{timestamp}.html`) for future reference or debugging. This can be done using Python's built-in file handling methods.

**Step 2: Parse the HTML with BeautifulSoup**

1.  **Input:** The HTML content (string).
2.  **Action:** Create a `BeautifulSoup` object: `soup = BeautifulSoup(html_content, 'html.parser')`.  Use the `'html.parser'` (or `lxml` if available for speed).
3.  **Output:** A `BeautifulSoup` object representing the parsed HTML document.

**Step 3: Extract Event Data (Iterate through Event Blocks)**

1.  **Input:** The `BeautifulSoup` object.
2.  **Action:**
    *   Find all event blocks.  Use `soup.find_all('div', class_='calendarRow')` to locate each event's container. This gives a list of `div` elements.
    *   Iterate through each `div` element (each `calendarRow`) found in the previous step.  For each `calendarRow`:
        *   Initialize an empty dictionary `event_data` to store the scraped data for the *current* event.
        *   Call helper functions (described below) to extract specific data points. Pass the current `calendarRow` (the `div` for the current event) to each helper function.  Each helper function returns a specific piece of data, which is added to the `event_data` dictionary.
        *   After all helper functions have run, append the `event_data` dictionary to a list called `all_events`.
3. **Output:** all_events which contains dictionaries, each holding data for one ride.

**Step 4: Helper Functions (Data Extraction)**

These functions are called *within* the loop in Step 3. Each takes a single `calendarRow` (a BeautifulSoup Tag object representing a single event's `div`) as input.

*   **`extract_name_and_id(calendar_row)`:**
    *   Find the `span` with `class="rideName details"`.
    *   Extract the text content: this is the `name`.
    *   Extract the `tag` attribute: this is the `ride_id`.
    *   Check for cancellation: If the `span` contains a child `span` with `class="red bold"` and text containing "Cancelled", set `is_canceled` to `True`.  Otherwise, `is_canceled` is `False`.
    *   Return `name`, `ride_id`, `is_canceled`.

*   **`extract_region_date_location(calendar_row)`:**
    *   Find the `td` with `class="region"`: extract the text content: this is the `region`.
    *   Find the first `td` with `class="bold"` immediately following the region: extract the text and parse it into a `YYYY-MM-DD` format string: this is `date_start`.
    *   Find the `td` containing the location information (use the structure of the table rows).  Extract the text. This is `location_name`.
    *   Return `region`, `date_start`, `location_name`.

*   **`extract_manager_info(calendar_row)`:**
    *   Find the `tr` with `id` starting with "TRrideID".
    *   Find the `td` containing "mgr:": extract the text after "mgr: " (removing leading/trailing whitespace). This is `ride_manager`.
    *   Return `ride_manager`.

*   **`extract_details(calendar_row)`:**
    *   Find the `tr` with `name` ending in "Details" and `class="toggle-ride-dets"`. This is the row containing the detailed information table.
    *   Within this row, find the `table` with `class="detailData"`.
    *   **Extract Location Details:**
        *   Find the `tr` containing "Location :".
        *   Extract the text from the following `td`, clean it, and split it into `location_name`, `city`, and `state` based on commas and the presence of a postal code (e.g., "MB").  Handle Canadian vs. US postal codes appropriately. Set country based on state.
    *   **Extract Manager Details:**
        *   Find the `tr` containing "Ride Manager :".
        *   Extract the manager's name, phone, and email from the following `td`. Use regular expressions to separate these values reliably.
    *   **Extract Control Judges:**
        *   Find the `tr` containing "Control Judges".
        *   Find all subsequent `tr` elements that contain "Control Judge :" or "Head Control Judge :". For each, extract the judge's name and role. Store these as a list of dictionaries: `[{"name": "...", "role": "..."}]`.
    *   **Extract Distances:**
        *   Find all `tr` elements containing "Distances".
        *   For each `tr`, extract the distance (e.g., "25&nbsp;") and the start time. Clean the distance string (remove "&nbsp;").
        *   Extract the corresponding date and time.
        *   Combine the date from the main ride entry with the specific distance start time. Format as `YYYY-MM-DD` for date and `HH:MM am/pm` for time.  Store distances as list of dictionaries.
    *   **Extract Description and Directions:**
        *   Find the `tr` containing "Descriptive".
        *   Extract the text content of the following `td` for both "Description:" and "Directions:". Use `<br>` tags to split the text appropriately.
    *  **Extract Website/Flyer**
        * Within the main event block (not the details section), find 'a' tags with 'Website' and 'Entry/Flyer' text, extract 'href'
    *   Return all extracted values.

* **`determine_event_type(calendar_row)`:**
    *    Defaults to "endurance"
    *    Return `event_type`

* **`determine_has_intro_ride(calendar_row)`:**
     *   Check within the initial event details (not expanded details) for a span with `style="color: red"` and inner text that contains "Has Intro Ride!".
    * Return boolean

* **`determine_multi_day_and_pioneer(distances, date_start)`:**
    *   Initialize `is_multi_day_event` and `is_pioneer_ride` to `False`.
    *    Initialize `ride_days` to 1.
    *   Initialize `date_end` to `date_start`
    *   If there are multiple dates within the `distances` list:
        *   Set `is_multi_day_event` to `True`.
        * Find the maximum date from all distances, and set it as the `date_end` in format `YYYY-MM-DD`.
        *   Calculate `ride_days` by taking the difference between `date_end` and `date_start` (in days) and adding 1.
        *   If `ride_days` is 3 or greater, set `is_pioneer_ride` to `True`.
    *   Return `is_multi_day_event`, `is_pioneer_ride`, `ride_days`, `date_end`.

**Step 5: Consolidate Multi-Day Events**

1.  **Input:** `all_events` (list of dictionaries, one per *row* in the HTML).
2.  **Action:**
    *   Create a new dictionary called `consolidated_events`, keyed by `ride_id`.
    *   Iterate through `all_events`:
        *   If the `ride_id` is *not* already a key in `consolidated_events`, add the event data as a new entry.
        *   If the `ride_id` *is* already a key in `consolidated_events`:
            *   This indicates a multi-day event. *Merge* the `distances` arrays. The other details should already exist
3. **Output:** The `consolidated_events` which will be a dictionary, where each entry represents a full event, including combined distances for multi-day events.
