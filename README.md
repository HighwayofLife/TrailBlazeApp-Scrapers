# TrailBlazeApp-Scrapers

TrailBlazeApp-Scrapers is a modular, extensible framework for scraping and processing endurance riding event data from various sources. The initial implementation focuses on the AERC (American Endurance Ride Conference) calendar, with support for additional scrapers planned.

## Features

- **Pluggable Scraper Architecture:** Easily add new scrapers for different event sources.
- **Caching:** Efficiently caches HTML to minimize redundant requests.
- **Metrics:** Tracks records read, inserted, updated, and more.
- **Database Integration:** Uses SQLAlchemy ORM for robust, maintainable database operations.
- **Validation:** Optionally validates that scraped data matches what is stored in the database.
- **Test Suite:** Comprehensive unit and integration tests.
- **Extensible:** Designed for easy addition of new scrapers and data sources.

## Quickstart

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.sample` to `.env` and fill in your database credentials and settings.

### 3. Run the AERC Scraper

```bash
python app/main.py --scrapers aerc
```

#### Common CLI Options

- `--validate` : Validate that database contents match scraped data.
- `--no-db` : Run without performing database operations.
- `--sample` : Use a sample HTML file instead of live scraping.
- `--sample-file <path>` : Specify a custom sample HTML file.
- `--url <url>` : Override the default scraping URL.

Example:

```bash
python app/main.py --scrapers aerc --validate
```

### 4. View Metrics

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

This project is licensed under the MIT License.
