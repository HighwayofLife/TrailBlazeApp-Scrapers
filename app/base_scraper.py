"""Base scraper module for the TrailBlazeApp-Scrapers project."""

import abc
import requests
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

from app.logging_manager import get_logger, LoggingManager
from app.metrics_manager import MetricsManager
from app.cache import Cache
from app.exceptions import HTMLDownloadError, DataExtractionError, ValidationError
from app.models import EventDataModel


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
        self.metrics_manager = MetricsManager(source_name=source_name)
        self.logging_manager = get_logger(f"{__name__}.{source_name}")
        self.cache = Cache(ttl=cache_ttl, scraper=self)
        self.metrics_manager.reset()

    @abc.abstractmethod
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Main entry point for scraping. Retrieves HTML, parses it, and returns structured data.

        Args:
            url (str): The URL to scrape

        Returns:
            Dict[str, Any]: Dictionary of consolidated event data
            
        Raises:
            HTMLDownloadError: If HTML content cannot be downloaded
            DataExtractionError: If data cannot be extracted from HTML
        """
        self.logging_manager.info(f"Starting scraping process for URL: {url}", ":rocket:")
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
            HTMLDownloadError: If the HTML content cannot be downloaded
        """
        key = f"html_content_{url}"
        cached_html = self.cache.get(key)
        if cached_html:
            self.metrics_manager.increment('cache_hits')
            self.logging_manager.info(f"Cache hit for URL: {url}", emoji=":rocket:")
            return cached_html
        else:
            self.metrics_manager.increment('cache_misses')
            self.logging_manager.info(f"Cache miss for URL: {url}, fetching...", emoji=":hourglass:")
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                html_content = response.text

                # Store in cache
                self.cache.set(key, html_content)

                return html_content
            except requests.RequestException as e:
                self.logging_manager.error(f"Failed to fetch HTML from URL: {url}. Error: {str(e)}", ":x:")
                self.metrics_manager.increment('html_download_errors')
                raise HTMLDownloadError(f"Failed to download HTML from {url}: {str(e)}")

    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content using BeautifulSoup.

        Args:
            html_content (str): Raw HTML content to parse

        Returns:
            BeautifulSoup: Parsed HTML document
            
        Raises:
            DataExtractionError: If HTML content cannot be parsed
        """
        try:
            self.logging_manager.debug("Parsing HTML content with BeautifulSoup", ":mag:")
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find all calendar rows
            calendar_rows = soup.find_all(class_="calendarRow")
            self.metrics_manager.set("raw_event_rows", len(calendar_rows))
            self.logging_manager.info(f"Found {len(calendar_rows)} calendar rows", ":scroll:")

            return soup
        except Exception as e:
            self.logging_manager.error(f"Failed to parse HTML content: {str(e)}", ":x:")
            self.metrics_manager.increment('html_parsing_errors')
            raise DataExtractionError(f"Failed to parse HTML content: {str(e)}")

    def _consolidate_events(self, all_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Consolidate events with the same ride ID into single events.

        Args:
            all_events (List[Dict[str, Any]]): List of all events before consolidation

        Returns:
            Dict[str, Any]: Dictionary of consolidated events, keyed by ride_id
        """
        self.logging_manager.info(f"Consolidating {len(all_events)} events", ":card_index_dividers:")
        self.metrics_manager.set("initial_events", len(all_events))

        consolidated = {}

        for event in all_events:
            ride_id = event.get("ride_id")
            if not ride_id:
                self.logging_manager.warning("Event without ride_id found, skipping", ":warning:")
                self.metrics_manager.increment('events_without_ride_id')
                continue

            if ride_id not in consolidated:
                consolidated[ride_id] = event
            else:
                # This is a multi-day event that needs consolidation
                self.metrics_manager.increment("multi_day_events")
                self.logging_manager.debug(f"Found multi-day event with ride_id: {ride_id}", ":date:")

                # Merge the events (implementation details would depend on specific requirements)
                # For example, you might want to combine distances, update end date, etc.
                if 'distances' in event and 'distances' in consolidated[ride_id]:
                    consolidated[ride_id]['distances'].extend(event['distances'])

        self.logging_manager.info(
            f"Consolidated to {len(consolidated)} events ({self.metrics_manager.get('multi_day_events')} multi-day events)",
            ":sparkles:"
        )

        self.metrics_manager.set('events_consolidated', len(consolidated))
        self.logging_manager.info(f"Consolidated {len(consolidated)} events.", emoji=":check_mark_button:")

        return consolidated

    def create_final_output(self, consolidated_events: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format consolidated events into final output structure.

        Args:
            consolidated_events (Dict[str, Any]): Dictionary of consolidated events

        Returns:
            Dict[str, Any]: Final output dictionary keyed by filenames
        """
        self.logging_manager.info("Creating final output", ":package:")

        # Set the final events count metric
        self.metrics_manager.set("final_events", len(consolidated_events))

        # Create the final output structure
        final_output = {}
        validated_count = 0

        for ride_id, event in consolidated_events.items():
            # Validate event data
            validated_event = self.validate_event_data(event)
            if validated_event:
                validated_count += 1
                # Generate a filename based on event details
                filename = f"{self.source_name.lower()}_{ride_id}.json"
                # Add to final output
                final_output[filename] = validated_event
            else:
                self.logging_manager.warning(f"Skipping invalid event with ride_id: {ride_id}", ":warning:")
                self.metrics_manager.increment('invalid_events_skipped')

        self.logging_manager.info(f"Final output created with {len(final_output)} events", ":white_check_mark:")
        self.metrics_manager.set('final_events', len(final_output))
        self.metrics_manager.set('validated_events', validated_count)
        self.logging_manager.info(f"Created final output for {len(final_output)} events.", emoji=":file_folder:")

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
        
    def validate_event_data(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate event data using the Pydantic model.
        
        Args:
            event_data (Dict[str, Any]): Event data to validate
            
        Returns:
            Optional[Dict[str, Any]]: Validated event data or None if validation fails
        """
        try:
            # Ensure source is set
            if 'source' not in event_data:
                event_data['source'] = self.source_name
                
            # Validate with Pydantic model
            validated_data = EventDataModel(**event_data).dict()
            return validated_data
        except Exception as e:
            self.logging_manager.warning(
                f"Validation error for event: {str(e)}", 
                emoji=":warning:"
            )
            self.metrics_manager.increment('validation_errors')
            return None
