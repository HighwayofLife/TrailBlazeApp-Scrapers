"""Tests for the AERCScraper class."""

import json
import os
from typing import Dict, Any
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
import pytest

from app.scrapers.aerc_scraper import AERCScraper


@pytest.fixture
def scraper():
    """Fixture providing AERCScraper instance."""
    return AERCScraper(cache_ttl=86400)


@pytest.fixture
def sample_html():
    """Fixture providing sample HTML content from file."""
    fixture_path = os.path.join(
        os.path.dirname(__file__),
        "fixtures",
        "input_file.html"
    )
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def expected_data():
    """Fixture providing expected data from JSON file."""
    fixture_path = os.path.join(
        os.path.dirname(__file__),
        "fixtures",
        "expected_data.json"
    )
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_init(scraper):
    """Test AERCScraper initialization."""
    assert scraper.source_name == "AERC"
    assert hasattr(scraper, "metrics")


def test_scrape_with_sample_data(scraper, sample_html, expected_data):
    """Test scraping with sample data."""
    with patch.object(scraper, 'get_html') as mock_get_html:
        mock_get_html.return_value = sample_html

        result = scraper.scrape("https://aerc.org/calendar")

        # Verify the scraper called get_html with the URL
        mock_get_html.assert_called_once_with("https://aerc.org/calendar")

        # Validate at least one event was extracted
        assert len(result) > 0

        # Check the structure of a sample event
        for ride_id, event_data in result.items():
            # Every event should have these basic properties
            assert "name" in event_data
            assert "ride_id" in event_data
            assert "date_start" in event_data
            assert "source" in event_data
            assert event_data["source"] == "AERC"


def test_create_final_output(scraper, sample_html, expected_data):
    """Test final output creation matches expected format."""
    with patch.object(scraper, 'get_html') as mock_get_html:
        mock_get_html.return_value = sample_html

        # Get consolidated events
        consolidated_events = scraper.scrape("https://aerc.org/calendar")

        # Create final output
        final_output = scraper.create_final_output(consolidated_events)

        # Check that we have output files
        assert len(final_output) > 0

        # Validate structure against expected data
        # The sample may not perfectly match expected_data.json, but should have same structure
        sample_event = next(iter(final_output.values()))
        expected_sample = next(iter(expected_data.values()))

        # Check key fields match in structure
        for key in ['name', 'source', 'event_type', 'date_start', 'date_end',
                   'location_name', 'region', 'is_canceled', 'is_multi_day_event',
                   'ride_days', 'ride_manager', 'ride_id']:
            assert key in sample_event, f"Missing key {key} in sample event"
            # Don't compare values, just make sure the structure is correct
            assert key in expected_sample, f"Missing key {key} in expected sample"


def test_extract_event_data(scraper, sample_html):
    """Test extracting event data from HTML."""
    soup = BeautifulSoup(sample_html, 'html.parser')
    events = scraper.extract_event_data(soup)

    # Check that we extracted events
    assert len(events) > 0

    # Validate structure of extracted events
    found_past_event = False
    for event in events:
        assert "name" in event
        assert "ride_id" in event
        assert "date_start" in event
        assert "is_canceled" in event
        # Standard fields expected for ALL events
        assert "location_name" in event
        assert "ride_manager" in event
        assert "event_type" in event
        assert "has_intro_ride" in event
        assert "source" in event
        assert "is_multi_day_event" in event
        assert "is_pioneer_ride" in event
        assert "ride_days" in event
        assert "date_end" in event
        assert "city" in event
        assert "state" in event
        assert "country" in event
        assert "distances" in event # Should be present, even if empty for past events

        # Specific checks for the known past event
        if event.get("ride_id") == "14446": # Barefoot In New Mexico
            found_past_event = True
            assert event["name"] == "Barefoot In New Mexico"
            assert event["date_start"] == "2024-12-01"
            assert event["date_end"] == "2024-12-01" # Should default to start date
            assert event["is_multi_day_event"] is False
            assert event["is_pioneer_ride"] is False
            assert event["ride_days"] == 1
            assert event["distances"] == [] # Explicitly check distances are empty
            assert "results_by_distance" not in event # Ensure results field is NOT present
            assert "is_past_event" not in event # Ensure is_past_event field is NOT present
            assert event["ride_manager"] == "Marcelle Hughes"
            assert event["location_name"] == "52 San Tomaso Rd., Alamogordo NM"
            assert event["city"] == "Alamogordo"
            assert event["state"] == "NM"
            assert event["country"] == "USA"

    assert found_past_event, "Did not find the expected past event (ride_id 14446) in extracted data"


def test_helper_functions(scraper, sample_html):
    """Test helper extraction functions individually."""
    soup = BeautifulSoup(sample_html, 'html.parser')
    calendar_rows = soup.find_all("div", class_="calendarRow")

    if not calendar_rows:
        pytest.skip("No calendar rows found in sample HTML")

    sample_row = calendar_rows[0]

    # Test name and ID extraction
    name, ride_id, is_canceled = scraper._extract_name_and_id(sample_row)
    assert isinstance(name, str)
    assert name, "Name should not be empty"
    assert ride_id, "Ride ID should not be empty"
    assert isinstance(is_canceled, bool)

    # Test region, date, location extraction
    region, date_start, location_name = scraper._extract_region_date_location(sample_row)
    if region:  # Region could be None if not found
        assert isinstance(region, str)
    if date_start:  # Date could be None if not found
        assert isinstance(date_start, str)
        # Check date format YYYY-MM-DD
        assert len(date_start.split("-")) == 3
    if location_name:  # Location could be None if not found
        assert isinstance(location_name, str)

    # Test website/flyer extraction
    website, flyer_url = scraper._extract_website_flyer(sample_row)
    # These can be None if not found
    if website:
        assert isinstance(website, str)
        assert website.startswith("http")
    if flyer_url:
        assert isinstance(flyer_url, str)
        assert flyer_url.startswith("http")


def test_consolidate_events(scraper):
    """Test consolidation of multi-day events."""
    # Create sample events with same ride_id but different days
    sample_events = [
        {
            "ride_id": "12345",
            "name": "Test Event",
            "date_start": "2025-06-01",
            "distances": [{"distance": "50", "date": "2025-06-01"}]
        },
        {
            "ride_id": "12345",
            "name": "Test Event",
            "date_start": "2025-06-02",
            "distances": [{"distance": "50", "date": "2025-06-02"}]
        }
    ]

    result = scraper._consolidate_events(sample_events)

    # Check that the events were consolidated
    assert "12345" in result
    assert result["12345"]["is_multi_day_event"] is True
    assert result["12345"]["date_start"] == "2025-06-01"
    assert result["12345"]["date_end"] == "2025-06-02"
    assert result["12345"]["ride_days"] == 2
    assert len(result["12345"]["distances"]) == 2
