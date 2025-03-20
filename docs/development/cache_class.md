# Caching Scraped HTML Content

This doc describes how to implement a caching system to store the HTML content retrieved from the target URL. The cache should have a Time-To-Live (TTL) of 24 hours, after which the cached data is considered stale and should be refreshed. This caching layer will prevent unnecessary requests to the target website.

**Caching Strategy:**

We will use a simple in-memory cache. Since the scraping is infrequent (every 24 hours) and the data size (HTML content) is relatively small, an in-memory cache is sufficient.  For larger-scale or more persistent caching, consider using Redis or Memcached. We will use the `cachetools` library for its simplicity and built-in TTL functionality.

**Libraries:**

*   **`cachetools`:** Provides various cache implementations, including `TTLCache` which is perfect for our needs. Install with `pip install cachetools`.
*   **`datetime`:**  Standard Python library for working with dates and times (used for TTL calculations).
*   **`time`:** Also a standard library, and should be used for cache key generation

**Class and Function Definitions:**

1.  **`Cache` Class:**

    *   **`__init__(self, maxsize=128, ttl=86400)`:**
        *   Constructor.
        *   `maxsize`:  The maximum number of items to store in the cache.  128 is a reasonable default; we likely only need to cache one item (the HTML for a single URL).
        *   `ttl`: The Time-To-Live (in seconds).  86400 seconds = 24 hours.
        *   Initializes a `cachetools.TTLCache` instance with the specified `maxsize` and `ttl`.

    *   **`get(self, key)`:**
        *   Retrieves the cached value associated with the given `key`.
        *   Returns the cached value if it exists and is not expired.
        *   Returns `None` if the key is not found or the cached item has expired.

    *   **`set(self, key, value)`:**
        *   Stores the given `value` in the cache, associated with the given `key`.
        *   Automatically handles eviction of old items based on the `maxsize` and TTL.

    *   **`invalidate(self, key)`:**
        * Removes a given key from the cache.

2.  **Integration with `Scraper` Class:**

    *   Modify the `Scraper` class to incorporate the cache.

    *   **`__init__(self, source_name="AERC", cache_ttl=86400)`:**
        *   Modify the constructor to:
            *   Initialize a `Cache` instance as an instance variable (e.g., `self.cache = Cache(ttl=cache_ttl)`).
            *  Accept a cache_ttl parameter

    *   **`get_html(self, url)`:**
        *   Modify this function to use the cache:
            1.  **Generate Cache Key:** Create a unique cache key. A simple approach is to use the URL itself. However, to ensure that the key is consistent even if the URL has slight variations, we'll create a simple key: `"source_url"`
            2.  **Check Cache:** Call `self.cache.get(key)` to check if the HTML content is already cached.
            3.  **Return from Cache (if available):** If the cache returns a non-`None` value, return the cached HTML content *directly*.
            4.  **Fetch from URL (if not cached):** If the cache returns `None` (cache miss):
                *   Make the HTTP request to the URL (as before).
                *   Store the retrieved HTML content in the cache using `self.cache.set(key, html_content)`.
                *   Return the retrieved HTML content.
            5. Use `time.monotonic()` instead of `datetime` for a more reliable key

**Step-by-Step Integration (within `Scraper.get_html`):**

1.  **Cache Key:**
    ```python
    key = "source_url"  # Simple, consistent key
    ```

2.  **Check Cache:**

    ```python
    cached_html = self.cache.get(key)
    ```

3.  **Return from Cache (if hit):**

    ```python
    if cached_html:
        return cached_html
    ```

4.  **Fetch from URL (if miss) and Store in Cache:**

    ```python
    # ... (Existing code to make the HTTP request) ...
    html_content = response.text  # Assuming 'response' is the result of requests.get
    self.cache.set(key, html_content)
    return html_content
    ```
**Key Instructions:**

*   **"Use `cachetools.TTLCache`."**  Specifically instruct the use of this class for its TTL functionality.
*   **"Cache key generation."** Explain how to ensure the cache key is consistently "source_url".
*   **"Integrate with `Scraper.get_html`."**  Clearly outline the steps to modify the `get_html` function to check the cache *before* making an HTTP request.
*   **"Handle cache hits and misses."**  Explain the logic for returning cached content or fetching from the URL.
*   **"Set the TTL to 24 hours."** Be explicit about the desired TTL value (86400 seconds).
*   **"Test the caching."**  Write tests *specifically* for the caching functionality (see below).

**Testing the Cache:**

Add these test cases to the existing Pytest suite:

*   **`test_cache_hit`:**
    *   **Purpose:** Test that the cache returns the correct value when there's a cache hit.
    *   **Setup:**
        *   Create a `Cache` instance.
        *   Manually populate the cache with a known key and value (using `cache.set`).
        *   Mock `Scraper.get_html` using `unittest.mock` to prevent any network requests
    *   **Action:** Call `cache.get` with the same key.
    *   **Assertion:** Assert that the returned value matches the value you set.

*   **`test_cache_miss`:**
    *   **Purpose:** Test that `cache.get` returns `None` when there's a cache miss.
    *   **Setup:**
        *   Create a `Cache` instance.
        *   *Do not* populate the cache.
    *   **Action:** Call `cache.get` with a key that is not in the cache.
    *   **Assertion:** Assert that the returned value is `None`.

*   **`test_cache_ttl`:**
    *   **Purpose:** Test that the TTL is working correctly (items expire after the TTL).
    *   **Setup:**
        *   Create a `Cache` instance with a *short* TTL (e.g., 1 second) for testing purposes.
        *   Populate the cache with a key and value.
        *   Wait for longer than the TTL (e.g., `time.sleep(2)`).
    *   **Action:** Call `cache.get` with the same key.
    *   **Assertion:** Assert that the returned value is `None` (because the item should have expired).
*   **`test_cache_integration` (Integration Test):**
    *   Purpose: Test the cache is used properly within `Scraper.get_html`
    *   Setup:
        *   Create a `Scraper` instance (it has the cache inside.)
        *   Use `requests_mock` to mock the `get` method of requests.
    *   Action:
        *    Call `scraper.get_html` one time. Assert that requests were called.
        *    Call `scraper.get_html` again. Assert that requests *were not* called.
    *   Assertion: Check that the data is returned as expected in both instances.
