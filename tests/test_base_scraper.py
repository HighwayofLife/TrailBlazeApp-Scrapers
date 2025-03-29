"""Tests for the BaseScraper abstract base class."""

from typing import Dict, Any
from unittest.mock import MagicMock, patch
from datetime import datetime
from bs4 import BeautifulSoup
import pytest

from app.base_scraper import BaseScraper


class TestScraper(BaseScraper):
    """Concrete implementation of BaseScraper for testing."""

    def scrape(self, url: str) -> Dict[str, Any]:
        """Test implementation of abstract method."""
        html = self.get_html(url)
        _ = self.parse_html(html)

        events = [{"ride_id": "test123", "name": "Test Event"}]
        return self._consolidate_events(events)

    def extract_event_data(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Minimal implementation for testing BaseScraper."""
        # This needs to be implemented for the TestScraper to be instantiated.
        # For most BaseScraper tests, the actual content doesn't matter.
        # Tests specifically needing extracted data should mock this method.
        return []


@pytest.fixture
def scraper():
    """Fixture providing TestScraper instance."""
    return TestScraper(source_name="TEST", cache_ttl=86400)


@pytest.fixture
def sample_html():
    """Fixture providing sample HTML content."""
    return "<html><body><div>Test content</div></body></html>"


@pytest.fixture
def sample_events():
    """Fixture providing sample event data."""
    return [
        {
            "ride_id": "123",
            "name": "Test Event",
            "date_start": "2025-03-20",
            "distances": [{"distance": "50", "date": "2025-03-20"}]
        },
        {
            "ride_id": "123",
            "name": "Test Event",
            "date_start": "2025-03-21",
            "distances": [{"distance": "75", "date": "2025-03-21"}]
        },
        {
            "ride_id": "456", # Pioneer ride
            "name": "Pioneer Event",
            "date_start": "2025-04-10",
            "distances": [{"distance": "50", "date": "2025-04-10"}]
        },
        {
            "ride_id": "456",
            "name": "Pioneer Event",
            "date_start": "2025-04-11",
            "distances": [{"distance": "50", "date": "2025-04-11"}]
        },
        {
            "ride_id": "456",
            "name": "Pioneer Event",
            "date_start": "2025-04-12",
            "distances": [{"distance": "50", "date": "2025-04-12"}]
        }
    ]


def test_init(scraper):
    """Test BaseScraper initialization."""
    assert scraper.source_name == "TEST"
    assert hasattr(scraper, "metrics")

    # Check that these expected metrics exist (without checking every metric)
    expected_metrics = [
        "raw_event_rows",
        "initial_events",
        "final_events",
        "multi_day_events",
        "database_inserts",
        "database_updates",
        "cache_hits",
        "cache_misses"
    ]

    for metric in expected_metrics:
        assert metric in scraper.metrics, f"Expected metric '{metric}' not found"
        assert isinstance(scraper.metrics[metric], int), f"Metric '{metric}' is not an integer"


def test_get_html_success(scraper):
    """Test successful HTML retrieval."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.text = "<html>Test</html>"
        mock_get.return_value.status_code = 200

        result = scraper.get_html("https://example.com")
        assert result == "<html>Test</html>"

        # Check that the URL is correct, but allow any other parameters
        assert mock_get.call_args[0][0] == "https://example.com"


def test_get_html_cached(scraper):
    """Test HTML retrieval from cache."""
    with patch('app.cache.Cache.get') as mock_cache_get:
        mock_cache_get.return_value = "<html>Cached</html>"

        result = scraper.get_html("https://example.com")
        assert result == "<html>Cached</html>"
        mock_cache_get.assert_called_once()


def test_parse_html(scraper, sample_html):
    """Test HTML parsing."""
    result = scraper.parse_html(sample_html)
    assert isinstance(result, BeautifulSoup)
    assert result.div is not None, "Div tag not found in parsed HTML"
    assert str(result.div.string) == "Test content"


def test_consolidate_events(scraper, sample_events):
    """Test event consolidation, including multi-day and pioneer rides."""
    result = scraper._consolidate_events(sample_events)

    assert isinstance(result, dict)

    # Check standard multi-day event (2 days)
    assert "123" in result
    event_123 = result["123"]
    assert len(event_123["distances"]) == 2
    assert event_123["is_multi_day_event"] is True
    assert event_123["is_pioneer_ride"] is False # Explicitly check pioneer is False for 2 days
    assert event_123["date_start"] == "2025-03-20"
    assert event_123["date_end"] == "2025-03-21"
    assert event_123["ride_days"] == 2

    # Check pioneer event (3 days)
    assert "456" in result
    event_456 = result["456"]
    assert len(event_456["distances"]) == 3
    assert event_456["is_multi_day_event"] is True
    assert event_456["is_pioneer_ride"] is True # Explicitly check pioneer is True for 3 days
    assert event_456["date_start"] == "2025-04-10"
    assert event_456["date_end"] == "2025-04-12"
    assert event_456["ride_days"] == 3


def test_create_final_output(scraper):
    """Test final output creation."""
    consolidated = {
        "123": {
            "ride_id": "123",
            "name": "Test Event",
            "source": "TEST",
            "region": "TEST",
            "date_start": "2025-03-20",
            "date_end": "2025-03-20",
            "location_name": "Test Location",
            "ride_manager": "Test Manager",
            "is_multi_day_event": False,
            "is_pioneer_ride": False,
            "ride_days": 1,
            "is_canceled": False,
            "event_type": "endurance",
            "has_intro_ride": False,
            "distances": [{"distance": "50", "date": "2025-03-20"}]
        }
    }

    result = scraper.create_final_output(consolidated)
    assert isinstance(result, dict)
    assert "test_123.json" in result


def test_metrics_property(scraper):
    """Test metrics property."""
    metrics = scraper.metrics
    assert isinstance(metrics, dict)

    # Check for the new metric names instead of the old ones
    expected_metrics = [
        "raw_event_rows",
        "initial_events",
        "final_events",
        "multi_day_events",
        "database_inserts",
        "database_updates",
        "cache_hits",
        "cache_misses"
    ]

    for metric in expected_metrics:
        assert metric in metrics, f"Expected metric '{metric}' not found"


def test_display_metrics(scraper, capsys):
    """Test metrics display."""
    scraper.display_metrics()
    captured = capsys.readouterr()
    assert "Scraping Summary for TEST" in captured.out
