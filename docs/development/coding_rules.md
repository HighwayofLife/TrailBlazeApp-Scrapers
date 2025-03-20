# Coding Rules

1.  **TDD Always:** Write a failing test *before* writing any implementation code (Red-Green-Refactor).
2.  **KISS:** Keep It Simple, Stupid. Favor the simplest solution.
3.  **DRY:** Don't Repeat Yourself. Avoid code duplication.
4.  **YAGNI:** You Ain't Gonna Need It. Don't implement unnecessary features.
5.  **SOLID Principles:** Adhere to SOLID principles for object-oriented design.
6.  **PEP 8:** Follow the PEP 8 style guide. Use a linter.
7.  **Type Hints:** Use type hints for all function parameters and return values.
8.  **Docstrings:** Write clear docstrings for all classes, functions, and methods.
9.  **Small Functions:** Keep functions short and focused on one task.
10. **Small Classes:** Keep classes focused and relatively small, with a single responsibility.
11. **Modularity:** Design for modularity and independent components.
12. **Extendability:** Design classes with the future in mind.
13. **Centralized Logging:** Use the `logging` module; log to standard output.
14. **Centralized Metrics:** Track key metrics in a dictionary; display a summary.
15. **Config File:** Use a `config.py` file for all configuration and to load environment variables.
16. **Utilize utils.py:** Use a `utils.py` file for utility and helper functions.
17. **Test Data:** Use fixtures in `tests/fixtures` for sample Data.
18. **Parameterized Queries:** Prevent SQL injection; use parameterized queries.
19. **Handle Errors:** Handle database and other potential errors gracefully.
20. **JSONB:** Use JSONB for flexible data storage in PostgreSQL.
21. **Log Levels:** Use DEBUG, INFO, WARNING, ERROR, and CRITICAL appropriately.
22. **Context Manager**: Use context manager when connecting to the database.
23. **No Secrets in Code:** Never store secrets (passwords, API keys) directly in the code.
24. **Efficiency:** Write efficient code; avoid unnecessary computations or operations.
25. **Return Values from Functions:** Ensure that functions return meaningful and predictable values.
26. **No Premature Optimization:** Focus on working code first, optimize when performance is critical.
27. **Follow Instructions:** Adhere precisely to the instructions and specifications provided.
28. **Documentation:** Document the code and its usage clearly.
29. **Use `datetime` Module:** Use the `datetime` module for date and time manipulations.
30. **Use `requests` Module:** Use the `requests` module for HTTP requests.
31. **Use `BeautifulSoup4` for HTML Parsing**
32. **Use `pytest` for Testing**
33. **Use `pytest-fixtures` for Setup:** Use pytest fixtures for test setup and teardown.
34. **Use Python3.11+**
35. **Use `Dockerfile`, `docker-compose.yml`, and `.env` files for containerization and environment configuration.**
36. **Use `Makefile` for all script automation**, including launching docker-compose, running tests, and building the project.**
37. **Use `PydanticV2` for data validation and settings management.**
38. **Use `SQLAlchemy` for ORM and database interactions.**
