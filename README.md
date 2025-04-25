# TrailBlazeApp-Scrapers

TrailBlazeApp-Scrapers is a modular, extensible framework for scraping and processing endurance riding event data from various sources. The initial implementation focuses on the AERC (American Endurance Ride Conference) calendar, with support for additional scrapers planned.

## Features

- **Pluggable Scraper Architecture:** Easily add new scrapers for different event sources.
- **Caching:** Efficiently caches HTML to minimize redundant requests.
- **Metrics:** Tracks records read, inserted, updated, and more.
- **Database Integration:** Uses SQLAlchemy ORM for robust, maintainable database operations.
- **Validation:** Optionally validates that scraped data matches what is stored in the database.
- **AI-Powered Data Extraction:** Uses Google Gemini to extract structured data from complex HTML.
- **Test Suite:** Comprehensive unit and integration tests.
- **Extensible:** Designed for easy addition of new scrapers and data sources.

## Quickstart

### 1. Configure Environment

Copy `.env.sample` to `.env` and fill in your database credentials and settings.

### 2. Build and Start Docker Containers

```bash
make build
make up
```

### 3. Run the AERC Scraper

Use the Makefile target to run the scraper inside the Docker container:

```bash
make scrape
```

#### Passing CLI Options

You can pass any CLI options to the scraper using the `ARGS` variable. For example, to validate database contents:

```bash
make scrape ARGS="--validate"
```

Other useful options:
- `--no-db` : Run without performing database operations.
- `--sample` : Use a sample HTML file instead of live scraping.
- `--sample-file <path>` : Specify a custom sample HTML file.
- `--url <url>` : Override the default scraping URL.

### 4. AI-Powered Data Extraction

The application uses Google's Gemini models to extract structured data from complex HTML snippets. To use this feature:

1. Set up your Google Gemini API key in the `.env` file:
   ```
   LLM_API_KEY="your_api_key_here"
   MODEL_ID="gemini-2.0-flash-001" # Or another available Gemini model
   ```

2. Use the `GeminiUtility` class in your scrapers:
   ```python
   from app.gemini_utility import GeminiUtility

   # Extract address information from HTML
   address_data = GeminiUtility.extract_address_from_html(html_snippet)
   ```

The utility handles retries, error conditions, and JSON parsing automatically.

### 5. View Metrics

At the end of each run, metrics are displayed, including:
- Number of records read from HTML
- Number of records inserted/updated in the database
- Cache hits/misses

## Project Structure

```
app/
  main.py           # Main entry point
  scrapers/         # Scraper implementations (AERC, etc.)
  base_scraper.py   # Abstract base class for scrapers
  cache.py          # Caching logic
  database.py       # Database manager (SQLAlchemy)
  data_validator.py # Data validation logic
  ...
docs/
  README.md         # Documentation index and links
tests/              # Unit and integration tests
```

## Documentation

Full documentation is available in the [docs/](docs/README.md) directory, including:

- [Scraping Guide (AERC)](docs/development/scraping_guide.md)
- [Development Guide](docs/development/development_guide.md)
- [Architecture & Structure](docs/development/structure.md)
- [Data Validation](docs/development/data_validation.md)
- [Metrics & Logging](docs/development/metrics_and_logging.md)
- [Testing & TDD](docs/development/tdd_guide_and_class.md)
- [Codebase Analysis](docs/CODEBASE_ANALYSIS.md)

See [docs/README.md](docs/README.md) for a full index.

## Contributing

Contributions are welcome! Please see the [development guide](docs/development/development_guide.md) for guidelines.

## License

This project is licensed under the Apache 2.0 License.
