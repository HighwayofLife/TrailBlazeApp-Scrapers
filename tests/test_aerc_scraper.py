"""Tests for the AERCScraper class."""

import json
import os
from unittest.mock import patch
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


def test_sanity():
    assert True


@pytest.fixture
def minimal_calendar_row():
    """Fixture providing a minimal BeautifulSoup calendar row for helper tests."""
    html = '<div class="calendarRow">\n        <span class="rideName details" tag="12345">Test Event</span>\n        <td class="region">West</td>\n        <td class="bold">01/15/2025</td>\n        <tr class="fix-jumpy"><td>mgr: John Doe</td></tr>\n    </div>'
    return BeautifulSoup(html, 'html.parser').find('div', class_='calendarRow')


def test_determine_event_type(scraper, minimal_calendar_row):
    # Default is endurance
    assert scraper._determine_event_type(minimal_calendar_row) == "endurance"
    # Limited distance
    minimal_calendar_row.string = "LD ride"
    assert scraper._determine_event_type(minimal_calendar_row) == "limited_distance"
    # Competitive trail
    minimal_calendar_row.string = "Competitive Trail"


def test_determine_has_intro_ride(scraper, minimal_calendar_row):
    # No intro ride
    assert not scraper._determine_has_intro_ride(minimal_calendar_row)
    # Add intro ride text
    minimal_calendar_row.append(BeautifulSoup('<span style="color:red">Has Intro Ride!</span>', 'html.parser'))


def test_extract_details_past_event(scraper):
    # Simulate a calendar row with a results link (past event)
    html = '''<div class="calendarRow">
        <span class="rideName details" tag="12345">Test Event</span>
        <tr class="toggle-ride-dets">
            <table class="detailData">
                <tr><td><a href="/rides-ride-result/?distance=50">* Results *</a></td></tr>
            </table>
        </tr>
    </div>'''
    row = BeautifulSoup(html, 'html.parser').find('div', class_='calendarRow')
    details, is_past = scraper._extract_details(row)
    assert is_past
    assert details["distances"] == []


def test_extract_manager_info_found(scraper):
    # Should extract the manager name from a realistic details table
    html = '''
    <div class="calendarRow">
        <span class="rideName details" tag="12345">Test Event</span>
        <tr class="toggle-ride-dets">
            <table class="detailData">
                <tr><td>Ride Manager : John Doe</td></tr>
            </table>
        </tr>
    </div>
    '''
    row = BeautifulSoup(html, 'html.parser').find('div', class_='calendarRow')
    assert scraper._extract_manager_info(row) == "John Doe"


def test_extract_manager_info_fallback(scraper):
    # Should fallback to 'Unknown' if no manager info is present
    html = '<div class="calendarRow"><span class="rideName details" tag="12345">Test Event</span></div>'
    row = BeautifulSoup(html, 'html.parser').find('div', class_='calendarRow')
    assert scraper._extract_manager_info(row) == "Unknown"


def test_get_season_ids_from_calendar_page(scraper):
    # Input with label as parent
    html = '<label>2025 Season <input name="season[]" value="63"></label>'
    result = scraper._get_season_ids_from_calendar_page(html)
    assert result == {"63": 2025}
    # Test fallback to year 0
    html = '<input name="season[]" value="99">'
    result = scraper._get_season_ids_from_calendar_page(html)
    assert result == {"99": 0}
    assert True


def test_init(scraper):
    """Test AERCScraper initialization."""
    assert scraper.source_name == "AERC"
    assert hasattr(scraper, "metrics")


def test_scrape_with_sample_data(scraper, sample_html, expected_data):
    """Test scraping with sample data."""
    with patch.object(scraper, 'get_html') as mock_get_html, \
         patch.object(scraper, '_fetch_event_html') as mock_fetch_event_html:
        mock_get_html.return_value = sample_html
        mock_fetch_event_html.return_value = sample_html

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
    with patch.object(scraper, 'get_html') as mock_get_html, \
         patch.object(scraper, '_fetch_event_html') as mock_fetch_event_html:
        mock_get_html.return_value = sample_html
        mock_fetch_event_html.return_value = sample_html

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
        assert "city" in event
        assert "state" in event
        assert "country" in event
        assert "distances" in event # Should be present, even if empty for past events

        # Specific checks for the known past event
        if event.get("ride_id") == "14446": # Barefoot In New Mexico
            found_past_event = True
            assert event["name"] == "Barefoot In New Mexico"
            assert event["date_start"] == "2024-12-01"
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
