"""Base scraper module for the TrailBlazeApp-Scrapers project."""

import abc
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from bs4 import BeautifulSoup


class BaseScraper(abc.ABC):
    """
    Abstract base class for all scrapers in the TrailBlazeApp-Scrapers project.

    Provides common functionality and defines the interface that all scrapers must implement.
    Uses BeautifulSoup for HTML parsing and implements caching for HTTP requests.
    """

    def __init__(self, source_name: str = "AERC", cache_ttl: int = 86400) -> None:
        """
        Initialize the BaseScraper.

        Args:
            source_name (str): The name of the data source (default: "AERC")
            cache_ttl (int): Cache time-to-live in seconds (default: 86400 (24 hours))
        """
        pass

    @abc.abstractmethod
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Main entry point for scraping. Retrieves HTML, parses it, and returns structured data.

        Args:
            url (str): The URL to scrape

        Returns:
            Dict[str, Any]: Dictionary of consolidated event data
        """
        pass

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
        pass

    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content using BeautifulSoup.

        Args:
            html_content (str): Raw HTML content to parse

        Returns:
            BeautifulSoup: Parsed HTML document
        """
        pass

    def _consolidate_events(self, all_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Consolidate events with the same ride ID into single events.

        Args:
            all_events (List[Dict[str, Any]]): List of all events before consolidation

        Returns:
            Dict[str, Any]: Dictionary of consolidated events, keyed by ride_id
        """
        pass

    def create_final_output(self, consolidated_events: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format consolidated events into final output structure.

        Args:
            consolidated_events (Dict[str, Any]): Dictionary of consolidated events

        Returns:
            Dict[str, Any]: Final output dictionary keyed by filenames
        """
        pass

    def display_metrics(self) -> None:
        """Display collected metrics in a user-friendly format with colors and emojis."""
        pass

    @property
    def metrics(self) -> Dict[str, int]:
        """
        Get the current metrics.

        Returns:
            Dict[str, int]: Dictionary of metric names and values
        """
        pass
