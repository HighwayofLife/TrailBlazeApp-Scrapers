# Utility Module

Create a Python *module* named `utils.py`. Modules provide a clean namespace and avoid unnecessary object instantiation.

**What to Put in `utils.py`:**

*   **`parse_date(date_string)`:** Parses a date string and returns a standardized date object.
*   **`parse_time(time_string)`:** Parses a time string and returns a standardized time object.
*   **`extract_city_state_country(location_string)`:** Extracts city, state, and country from a location string.
*   **`generate_file_name(ride_id, source)`:** Creates a standardized filename.

**Why a Utility Module is Beneficial:**

*   **Reusability:** These functions are likely to be useful in multiple parts of the codebase (e.g., both the scraper and potentially the database interaction logic).
*   **Organization:**  It keeps the main `Scraper` and `DatabaseManager` classes cleaner and more focused on their core responsibilities.
*   **Testability:** Utility functions are easy to test in isolation.
*   **Maintainability:**  Changes to these utility functions are localized and less likely to have unintended consequences in other parts of the code.
* **Readability:** Separating these functions makes the main logic less cluttered, and self-documenting in many ways.
