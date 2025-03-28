"""Main entry point for the TrailBlazeApp-Scrapers project."""

import argparse
import sys
import os
import logging
from typing import Dict, Any, List

from app.config import get_settings, get_db_config
from app.database import DatabaseManager
from app.data_validator import DataValidator
from app.scrapers.aerc_scraper import AERCScraper
from app.logging_manager import get_logger


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="TrailBlazeApp-Scrapers - Event data scraper for endurance rides")
    parser.add_argument('--validate', action='store_true', help='Validate database operations after scraping')
    parser.add_argument('--no-db', action='store_true', help='Run without database operations (for testing)')
    parser.add_argument('--url', type=str, help='Override the default scraping URL')
    parser.add_argument('--sample', action='store_true', help='Use sample HTML file instead of live website')
    parser.add_argument('--sample-file', type=str,
                      default='tests/samples/aerc_calendar_sample.html',
                      help='Path to sample HTML file (default: tests/samples/aerc_calendar_sample.html)')
    return parser.parse_args()


def main() -> Dict[str, Any]:
    """
    Main application entry point.

    Initializes components, runs the scraper, and handles database operations.

    Returns:
        Dict[str, Any]: Dictionary of scraped and processed event data
    """
    # Parse command line arguments
    args = parse_arguments()

    # Set up logging
    setup_logging()
    logger = get_logger(__name__).logger

    try:
        # Load configuration
        settings = get_settings()
        db_config = get_db_config()

        # Initialize scraper
        scraper = AERCScraper(cache_ttl=settings.CACHE_TTL)

        # Initialize database components if needed
        db_manager = None
        data_validator = None
        if not args.no_db:
            db_manager = DatabaseManager(db_config, scraper)
            data_validator = DataValidator(db_manager)

            # Create database tables if they don't exist
            db_manager.create_tables()

        # Determine URL or use sample HTML
        scrape_url = None
        use_sample = args.sample
        sample_file = args.sample_file

        if use_sample:
            # Check if sample file exists
            if not os.path.exists(sample_file):
                logger.error(f"Sample file not found: {sample_file}")
                raise FileNotFoundError(f"Sample file not found: {sample_file}")

            logger.info(f"Using sample HTML file: {sample_file}")

            # Instead of scraping URL, use get_html to read the file
            with open(sample_file, 'r') as f:
                html_content = f.read()

            # Parse the HTML and extract events
            soup = scraper.parse_html(html_content)
            events_list = scraper.extract_event_data(soup)
            events_dict = scraper._consolidate_events(events_list)

            # Debug: print all events and identify which are multi-day
            logging.info("------------- EVENT DETAILS -------------")
            for ride_id, event in events_dict.items():
                multi_day = "MULTI-DAY" if event.get("is_multi_day_event") else "single-day"
                pioneer = "PIONEER" if event.get("is_pioneer_ride") else "regular"
                logging.info(f"Event {event.get('name')} (ID: {ride_id}): {multi_day}, {pioneer}, {event.get('ride_days')} days, {event.get('date_start')} to {event.get('date_end')}")

            # Create final output
            events = {}
            for event_id, event_data in events_dict.items():
                filename = f"aerc_{event_id}.json"
                events[filename] = event_data

            # Update metrics for final events
            scraper.metrics_manager.set("final_events", len(events))

        else:
            # Use URL for live scraping
            scrape_url = args.url if args.url else settings.AERC_CALENDAR_URL
            logger.info(f"Starting AERC calendar scrape from {scrape_url}...")
            events = scraper.scrape(scrape_url)

        # Store events in database if database operations are enabled
        if db_manager:
            validation_errors = []
            updated_event_count = 0

            logger.info(f"Processing {len(events)} events for database storage...")

            for event_id, event_data in events.items():
                try:
                    db_manager.insert_or_update_event(event_data)
                    updated_event_count += 1

                    # Validate database operation if requested
                    if args.validate and data_validator:
                        success, errors = data_validator.validate_database_operation(event_data)
                        if not success and errors:
                            validation_errors.extend(errors)

                except Exception as e:
                    logger.error(f"Error processing event {event_id}: {str(e)}")

            logger.info(f"Successfully processed {updated_event_count} events")

            if args.validate:
                if validation_errors:
                    logger.warning(f"Validation found {len(validation_errors)} errors")
                    for error in validation_errors[:5]:  # Show first 5 errors
                        logger.warning(f"Validation error: {error}")
                    if len(validation_errors) > 5:
                        logger.warning(f"... and {len(validation_errors) - 5} more errors")
                else:
                    logger.info("All database operations validated successfully")

        # Display metrics
        scraper.display_metrics()

        return events

    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)
