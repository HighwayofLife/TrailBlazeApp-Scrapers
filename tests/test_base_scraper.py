"""Tests for the BaseScraper abstract base class."""

import pytest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, Any

from app.base_scraper import BaseScraper


class TestScraper(BaseScraper):
    """Concrete implementation of BaseScraper for testing."""

    def scrape(self, url: str) -> Dict[str, Any]:
        """Test implementation of abstract method."""
        html = self.get_html(url)
        soup = self.parse_html(html)
        events = [{"ride_id": "test123", "name": "Test Event"}]
        return self._consolidate_events(events)


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
            "date": "2025-03-20",
            "distances": [{"distance": "50"}]
        },
        {
            "ride_id": "123",
            "name": "Test Event",
            "date": "2025-03-21",
            "distances": [{"distance": "75"}]
        }
    ]


def test_init(scraper):
    """Test BaseScraper initialization."""
    assert scraper.source_name == "TEST"
    assert hasattr(scraper, "metrics")
    assert scraper.metrics == {
        "events_processed": 0,
        "events_consolidated": 0,
        "database_inserts": 0,
        "database_updates": 0
    }


def test_get_html_success(scraper):
    """Test successful HTML retrieval."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.text = "<html>Test</html>"
        mock_get.return_value.status_code = 200

        result = scraper.get_html("https://example.com")
        assert result == "<html>Test</html>"
        mock_get.assert_called_once_with("https://example.com")


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
    assert str(result.div.string) == "Test content"


def test_consolidate_events(scraper, sample_events):
    """Test event consolidation."""
    result = scraper._consolidate_events(sample_events)

    assert isinstance(result, dict)
    assert "123" in result
    assert len(result["123"]["distances"]) == 2
    assert result["123"]["is_multi_day_event"] is True


def test_create_final_output(scraper):
    """Test final output creation."""
    consolidated = {
        "123": {
            "ride_id": "123",
            "name": "Test Event",
            "source": "TEST"
        }
    }

    result = scraper.create_final_output(consolidated)
    assert isinstance(result, dict)
    assert "test_123.json" in result


def test_metrics_property(scraper):
    """Test metrics property."""
    metrics = scraper.metrics
    assert isinstance(metrics, dict)
    assert "events_processed" in metrics
    assert "events_consolidated" in metrics


def test_display_metrics(scraper, capsys):
    """Test metrics display."""
    scraper.display_metrics()
    captured = capsys.readouterr()
    assert "Scraping Metrics" in captured.out
