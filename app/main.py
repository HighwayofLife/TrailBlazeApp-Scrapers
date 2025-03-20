"""Main entry point for the TrailBlazeApp-Scrapers project."""

import logging
from typing import Dict, Any

from app.config import get_settings, get_db_config
from app.database import DatabaseManager
from app.scrapers.aerc_scraper import AERCScraper


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main() -> Dict[str, Any]:
    """
    Main application entry point.

    Initializes components, runs the scraper, and handles database operations.

    Returns:
        Dict[str, Any]: Dictionary of scraped and processed event data
    """
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Load configuration
        settings = get_settings()
        db_config = get_db_config()

        # Initialize scraper
        scraper = AERCScraper(cache_ttl=settings.CACHE_TTL)

        # Initialize database manager
        db_manager = DatabaseManager(db_config, scraper)

        # Run scraper
        logger.info("Starting AERC calendar scrape...")
        events = scraper.scrape(settings.AERC_CALENDAR_URL)

        # Process and store events
        for event in events.values():
            db_manager.insert_or_update_event(event)

        # Display metrics
        scraper.display_metrics()

        return events

    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise


if __name__ == "__main__":
    main()
