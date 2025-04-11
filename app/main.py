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
from app.base_scraper import BaseScraper
from app.logging_manager import get_logger

# --- Scraper Registry --- #
# Dynamically import other scrapers if they exist or define them here
# Example: from app.scrapers.sera_scraper import SERAScraper

# Maps scraper names (used in CLI) to their classes and default URLs/sample files
SCRAPER_REGISTRY = {
    "aerc": {
        "class": AERCScraper,
        "url_setting": "AERC_CALENDAR_URL",
        "sample_file": "tests/samples/aerc_calendar_sample.html"
    },
    # "sera": {
    #     "class": SERAScraper, # Assuming SERAScraper exists
    #     "url_setting": "SERA_CALENDAR_URL", # Add this to Settings if needed
    #     "sample_file": "tests/samples/sera_calendar_sample.html" # Create this file if needed
    # },
}
# --- End Scraper Registry --- #


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
                      help='Path to sample HTML file (overrides scraper default)')
    # Add argument to select scraper(s)
    parser.add_argument('--scrapers', type=str, nargs='+',
                      default=["aerc"], # Default to AERC
                      choices=list(SCRAPER_REGISTRY.keys()),
                      help=f"Select which scraper(s) to run (available: {list(SCRAPER_REGISTRY.keys())})")

    return parser.parse_args()


def main() -> Dict[str, Any]:
    """
    Main application entry point.

    Initializes components, runs the selected scraper(s), and handles database operations.

    Returns:
        Dict[str, Any]: Dictionary of all scraped and processed event data from all run scrapers
    """
    # Parse command line arguments
    args = parse_arguments()

    # Set up logging
    setup_logging()
    logger = get_logger(__name__).logger

    all_scraped_events = {}
    scrapers_to_run: List[str] = args.scrapers

    try:
        # Load configuration
        settings = get_settings()
        db_config = get_db_config()

        # Initialize database components (only once, can be shared by scrapers)
        db_manager = None
        data_validator = None
        if not args.no_db:
            # Pass scraper=None initially, can be set per-scraper if needed by DBManager
            db_manager = DatabaseManager(db_config, scraper=None)
            data_validator = DataValidator(db_manager)
            # Create database tables if they don't exist (do this once)
            db_manager.create_tables()

        # --- Loop through selected scrapers --- #
        for scraper_name in scrapers_to_run:
            logger.info(f"--- Running scraper: {scraper_name.upper()} ---")
            scraper_info = SCRAPER_REGISTRY.get(scraper_name)
            if not scraper_info:
                logger.warning(f"Scraper '{scraper_name}' not found in registry. Skipping.")
                continue

            # Initialize the specific scraper
            ScraperClass = scraper_info["class"]
            scraper: BaseScraper = ScraperClass(cache_ttl=settings.CACHE_TTL)

            # Optionally, pass scraper instance to db_manager if it needs per-scraper context (like metrics)
            if db_manager:
                db_manager.scraper = scraper # Link current scraper to DB manager for metrics

            # Determine URL or sample file for this specific scraper
            scrape_url = None
            use_sample = args.sample
            # Use CLI sample file if provided, else use scraper default
            sample_file = args.sample_file if args.sample_file else scraper_info["sample_file"]

            events = {}
            try:
                if use_sample:
                    # Check if sample file exists
                    if not os.path.exists(sample_file):
                        logger.error(f"Sample file not found for {scraper_name}: {sample_file}")
                        raise FileNotFoundError(f"Sample file not found: {sample_file}")

                    logger.info(f"Using sample HTML file: {sample_file}")

                    # Read the file content
                    with open(sample_file, 'r', encoding='utf-8') as f:
                        html_content = f.read()

                    # Use scraper methods to parse and extract (avoiding consolidate here, do it after extraction)
                    soup = scraper.parse_html(html_content)
                    events_list = scraper.extract_event_data(soup)
                    # Consolidate events specifically for this scraper run
                    consolidated_events = scraper.consolidate_events(events_list)
                    # Create final output format
                    events = scraper.create_final_output(consolidated_events)

                else:
                    # Use URL for live scraping
                    # Use CLI URL if provided, else use scraper default from settings
                    default_url_setting = scraper_info["url_setting"]
                    scrape_url = args.url if args.url else getattr(settings, default_url_setting, None)
                    if not scrape_url:
                        logger.error(f"Scraping URL not configured for {scraper_name} (checked Settings.{default_url_setting} and --url arg). Skipping.")
                        continue

                    logger.info(f"Starting {scraper_name.upper()} scrape from {scrape_url}...")
                    # The scrape method should handle get_html, parse_html, extract, consolidate, create_final_output
                    events = scraper.scrape(scrape_url)

                logger.info(f"Scraper {scraper_name.upper()} finished. Found {len(events)} final events.")
                all_scraped_events.update(events) # Add events to the main dictionary

                # --- Database Operations for this scraper's events --- #
                if db_manager:
                    validation_errors = []
                    updated_event_count = 0
                    logger.info(f"Processing {len(events)} events from {scraper_name.upper()} for database storage...")

                    for _, event_data in events.items():
                        try:
                            db_manager.insert_or_update_event(event_data)
                            updated_event_count += 1

                            if args.validate and data_validator:
                                success, errors = data_validator.validate_database_operation(event_data)
                                if not success and errors:
                                    validation_errors.extend(errors)

                        except (KeyError, ValueError, TypeError) as e:
                            logger.error(f"Error processing event {event_data.get('source', 'unknown')}-{event_data.get('ride_id', 'unknown')}: {str(e)}")

                    logger.info(f"Successfully processed {updated_event_count} DB operations for {scraper_name.upper()} events")

                    if args.validate:
                        if validation_errors:
                            logger.warning(f"Validation found {len(validation_errors)} errors for {scraper_name.upper()}")
                            for error in validation_errors[:5]:
                                logger.warning(f"  - {error}")
                            if len(validation_errors) > 5:
                                logger.warning(f"  ... and {len(validation_errors) - 5} more errors")
                        else:
                            logger.info(f"All database operations validated successfully for {scraper_name.upper()}")
                # --- End Database Operations --- #

                # Display metrics for this scraper
                scraper.display_metrics()

            except (FileNotFoundError, KeyError, ValueError, TypeError) as e:
                logger.error(f"Error during {scraper_name.upper()} scraping: {str(e)}")
                # Optionally continue to the next scraper instead of raising immediately
                # raise # Uncomment this to stop execution on the first scraper error

        # --- End loop through scrapers --- #

        logger.info(f"--- All scraping finished. Total unique events processed: {len(all_scraped_events)} ---")
        return all_scraped_events

    except (FileNotFoundError, KeyError, ValueError, TypeError) as e:
        logger.critical(f"Unhandled error in main execution: {str(e)}") # Use critical for top-level errors
        raise


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except (FileNotFoundError, KeyError, ValueError, TypeError) as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)
