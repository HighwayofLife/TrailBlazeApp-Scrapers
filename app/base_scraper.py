"""Base scraper module for the TrailBlazeApp-Scrapers project."""

import abc
import requests
from typing import Dict, List, Any

from app.logging_manager import get_logger
from app.metrics_manager import MetricsManager
from app.cache import Cache


class BaseScraper(abc.ABC):
    """
    Abstract base class for all scrapers in the TrailBlazeApp-Scrapers project.

    Provides common functionality and defines the interface that all scrapers must implement.
    Uses BeautifulSoup for HTML parsing and implements caching for HTTP requests.
    Includes logging and metrics collection functionality.
    """

    def __init__(self, source_name: str = "AERC", cache_ttl: int = 86400) -> None:
        """
        Initialize the BaseScraper.

        Args:
            source_name (str): The name of the data source (default: "AERC")
            cache_ttl (int): Cache time-to-live in seconds (default: 86400 (24 hours))
        """
        self.source_name = source_name
        self.cache = Cache(ttl=cache_ttl, scraper=self)
        self.metrics_manager = MetricsManager(source_name=source_name)
        self.logging_manager = get_logger(__name__)
        self.logger = self.logging_manager.logger
        self.metrics_manager.reset()

    @abc.abstractmethod
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Main entry point for scraping. Retrieves HTML, parses it, and returns structured data.

        Args:
            url (str): The URL to scrape

        Returns:
            Dict[str, Any]: Dictionary of consolidated event data
        """
        self.logger.info(f"Starting scraping process for URL: {url}", ":rocket:")
        self.metrics_manager.reset_event_metrics()
        # Concrete implementations should call get_html, parse_html, and display_metrics

    def get_html(self, url: str) -> str:
        """
        Retrieve HTML content from URL, using cache if available and valid.

        Args:
            url (str): The URL to fetch HTML from

        Returns:
            str: The HTML content

        Raises:
            requests.RequestException: If the request fails
        """
        key = f"html_content_{url}"
        cached_html = self.cache.get(key)
        if cached_html:
            self.metrics_manager.increment('cache_hits')
            self.logger.info(f"Cache hit for URL: {url}", emoji=":rocket:")
            return cached_html
        else:
            self.metrics_manager.increment('cache_misses')
            self.logger.info(f"Cache miss for URL: {url}, fetching...", emoji=":hourglass:")
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                html_content = response.text

                # Store in cache
                self.cache.set(key, html_content)

                return html_content
            except requests.RequestException as e:
                self.logger.error(f"Failed to fetch HTML from URL: {url}. Error: {str(e)}", ":x:")
                raise

    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content using BeautifulSoup.

        Args:
            html_content (str): Raw HTML content to parse

        Returns:
            BeautifulSoup: Parsed HTML document
        """
        self.logger.debug("Parsing HTML content with BeautifulSoup", ":mag:")
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all calendar rows
        calendar_rows = soup.find_all(class_="calendarRow")
        self.metrics_manager.set("raw_event_rows", len(calendar_rows))
        self.logger.info(f"Found {len(calendar_rows)} calendar rows", ":scroll:")

        return soup

    def _consolidate_events(self, all_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Consolidate events with the same ride ID into single events.

        Args:
            all_events (List[Dict[str, Any]]): List of all events before consolidation

        Returns:
            Dict[str, Any]: Dictionary of consolidated events, keyed by ride_id
        """
        self.logger.info(f"Consolidating {len(all_events)} events", ":card_index_dividers:")
        self.metrics_manager.set("initial_events", len(all_events))

        consolidated = {}

        for event in all_events:
            ride_id = event.get("ride_id")
            if not ride_id:
                self.logger.warning("Event without ride_id found, skipping", ":warning:")
                continue

            if ride_id not in consolidated:
                consolidated[ride_id] = event
            else:
                # This is a multi-day event that needs consolidation
                self.metrics_manager.increment("multi_day_events")
                self.logger.debug(f"Found multi-day event with ride_id: {ride_id}", ":date:")

                # Merge the events (implementation details would depend on specific requirements)
                # For example, you might want to combine distances, update end date, etc.

        self.logger.info(
            f"Consolidated to {len(consolidated)} events ({self.metrics_manager.get('multi_day_events')} multi-day events)",
            ":sparkles:"
        )

        self.metrics_manager.set('events_consolidated', len(consolidated))
        self.logger.info(f"Consolidated {len(consolidated)} events.", emoji=":check_mark_button:")

        return consolidated

    def create_final_output(self, consolidated_events: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format consolidated events into final output structure.

        Args:
            consolidated_events (Dict[str, Any]): Dictionary of consolidated events

        Returns:
            Dict[str, Any]: Final output dictionary keyed by filenames
        """
        self.logger.info("Creating final output", ":package:")

        # Set the final events count metric
        self.metrics_manager.set("final_events", len(consolidated_events))

        # Create the final output structure
        final_output = {}

        for ride_id, event in consolidated_events.items():
            # Generate a filename based on event details
            filename = f"{self.source_name.lower()}_{ride_id}.json"

            # Add to final output
            final_output[filename] = event

        self.logger.info(f"Final output created with {len(final_output)} events", ":white_check_mark:")

        self.metrics_manager.set('final_events', len(final_output))
        self.logger.info(f"Created final output for {len(final_output)} events.", emoji=":file_folder:")

        return final_output

    def display_metrics(self) -> None:
        """Display collected metrics in a user-friendly format with colors and emojis."""
        self.metrics_manager.display_metrics()

    @property
    def metrics(self) -> Dict[str, int]:
        """
        Get the current metrics.

        Returns:
            Dict[str, int]: Dictionary of metric names and values
        """
        return self.metrics_manager.get_all_metrics()
