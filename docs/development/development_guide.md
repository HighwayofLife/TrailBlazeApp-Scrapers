**Rules of Engagement: Microservice Development**

These rules guide the development of microservices, ensuring code quality, maintainability, and adherence to best practices. Follow these rules consistently.

**I. Core Principles:**

1.  **KISS (Keep It Simple, Stupid):** Favor simplicity. Avoid over-engineering. Choose the simplest solution that meets the requirements.
2.  **DRY (Don't Repeat Yourself):**  Avoid code duplication.  Extract common logic into reusable functions or classes.
3.  **YAGNI (You Ain't Gonna Need It):** Don't implement features or functionality until they are actually needed.
4.  **SOLID Principles:** Adhere to SOLID principles for Object-Oriented design
    *   **Single Responsibility Principle:** Each class/function should have one, and only one reason to change.
    *   **Open-Closed Principle:** You should not have to edit existing code to add new functionality, instead extend it.
    *   **Liskov Substitution Principle:** Derived classes must be substitutable for their base classes.
    * **Interface Segregation Principle**: Do not force any client to implement an interface which is irrelevant to them.
    *  **Dependency Inversion Principle**: Depend on abstractions, not on concretions.

**II. Development Practices:**

1.  **Test-Driven Development (TDD):**
    *   **Red-Green-Refactor:** Write a failing test *before* writing any implementation code. Then write the *minimum* code to pass the test. Finally, refactor to improve the code while keeping the test passing.
    *   **Test Coverage:** Aim for high test coverage. Test all critical functions and edge cases.
    *   **Pytest:** Use Pytest as the testing framework.

2.  **Code Style:**
    *   **PEP 8:** Follow the PEP 8 style guide for Python code (use a linter like `flake8` or `pylint`).
    *   **Type Hints:** Use type hints for function parameters and return values.
    *   **Docstrings:** Write clear and concise docstrings for all classes, functions, and methods. Explain the *purpose*, *parameters*, and *return values*.
    *   **Meaningful Names:** Use descriptive names for variables, functions, and classes.

3.  **Code Structure:**
    *   **Small Functions:** Functions should be short (ideally under 20 lines) and focused on a single task.
    *   **Small Classes:** Classes should have a clear responsibility and be relatively small.
    *   **Modularity:** Design for modularity. Break down the application into well-defined, independent components.
    * **Extendability:** Design classes to be extensible in the future, consider design patterns.

4.  **Caching:**
    *   **Cache HTML:** Use the `Cache` class to cache fetched HTML content.
    *   **24-Hour TTL:** Use a 24-hour Time-To-Live (TTL) for the cache.

5.  **Logging and Metrics:**
    *   **Centralized Logging:** Use the Python `logging` module. Log to standard output.
    *   **Centralized Metrics:** Use a dictionary to store metrics.
    *   **Informative Output:**  Display a summary of metrics at the end of each scraping run, using color and emojis for clarity.
    *   **Log Levels:** Use appropriate logging levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    *   **Log Key Events:** Log important events (start/end of scraping, errors, warnings, database operations, cache hits/misses).

**III. Configuration and Data:**

1.  **Configuration:**
    *   **`config.py`:**  Store all configuration in a `config.py` file.
    *   **Environment Variables:** Load configuration values from environment variables (using `os.environ` or a library like `python-dotenv`).
    *   **`.env` file:** Use a `.env` file for local development to store environment variables.  *Do not commit the `.env` file to version control.*
2. **Database:**
    * Use the DatabaseManager to connect, and perform CRUD operations
3.  **Test Data:**
    *   **Fixtures:** Store sample HTML files for testing in a `tests/fixtures` directory.
    *    Do not include any secrets or sensitive data in the repo.
4.  **Data Handling:**
    *   **Parameterized Queries:**  Use parameterized queries (e.g., with `psycopg2` or SQLAlchemy) to prevent SQL injection vulnerabilities.
    *   **Error Handling:**  Handle potential database errors gracefully.
    *   **JSONB:** Use JSONB data type for flexible data storage in PostgreSQL.

**IV. Version Control (Git):**

1.  **Feature Branches:** Create a new branch for each feature or bug fix.
2.  **Descriptive Commits:** Write clear and concise commit messages.
3.  **Pull Requests:** Use pull requests for code reviews.

**V. Twelve-Factor App Principles:**

*   Strive to adhere to the Twelve-Factor App methodology for building robust and scalable applications.
