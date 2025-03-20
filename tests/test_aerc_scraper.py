"""Tests for the AERC-specific scraper implementation."""

import pytest
from bs4 import BeautifulSoup
from unittest.mock import MagicMock, patch
from app.scrapers.aerc_scraper import AERCScraper


@pytest.fixture
def sample_html():
    """Fixture providing sample HTML content."""
    return """
    <div class="calendarRow">
        <span class="rideName details" tag="12345">Test Ride</span>
        <td class="region">W</td>
        <td class="bold">Mar 20, 2025</td>
        <td>Test Ranch, Test City, AZ</td>
        <tr id="TRrideID12345">
            <td>mgr: Test Manager</td>
        </tr>
        <tr name="12345Details" class="toggle-ride-dets">
            <table class="detailData">
                <tr><td>Location : Test Ranch, Test City, AZ</td></tr>
                <tr><td>Ride Manager : Test Manager (123-456-7890) test@example.com</td></tr>
                <tr><td>Head Control Judge : Dr. Test Judge</td></tr>
                <tr><td>Distances : 25, 50, 75</td></tr>
                <tr><td>Description: Test description</td></tr>
                <tr><td>Directions: Test directions</td></tr>
            </table>
        </tr>
        <a href="http://example.com">Website</a>
        <a href="http://example.com/flyer">Entry/Flyer</a>
        <span style="color: red">Has Intro Ride!</span>
    </div>
    """


@pytest.fixture
def scraper():
    """Fixture providing AERCScraper instance."""
    return AERCScraper(cache_ttl=86400)


@pytest.fixture
def sample_distances():
    """Fixture providing sample distances data."""
    return [
        {"distance": "50", "date": "2025-03-20", "time": "07:00 AM"},
        {"distance": "75", "date": "2025-03-21", "time": "06:00 AM"}
    ]


def test_scrape_success(scraper):
    """Test successful scraping of AERC calendar."""
    with patch.object(scraper, 'get_html') as mock_get_html, \
         patch.object(scraper, 'parse_html') as mock_parse_html, \
         patch.object(scraper, 'extract_event_data') as mock_extract, \
         patch.object(scraper, '_consolidate_events') as mock_consolidate:

        mock_get_html.return_value = "<html></html>"
        mock_parse_html.return_value = BeautifulSoup("<html></html>", "html.parser")
        mock_extract.return_value = [{"ride_id": "12345", "name": "Test Ride"}]
        mock_consolidate.return_value = {"12345": {"ride_id": "12345", "name": "Test Ride"}}

        result = scraper.scrape("https://example.com")
        assert isinstance(result, dict)
        assert "12345" in result


def test_extract_name_and_id(scraper, sample_html):
    """Test extraction of event name and ID."""
    soup = BeautifulSoup(sample_html, "html.parser")
    calendar_row = soup.find("div", class_="calendarRow")
    name, ride_id, is_canceled = scraper._extract_name_and_id(calendar_row)

    assert name == "Test Ride"
    assert ride_id == "12345"
    assert is_canceled is False


def test_extract_region_date_location(scraper, sample_html):
    """Test extraction of region, date, and location."""
    soup = BeautifulSoup(sample_html, "html.parser")
    calendar_row = soup.find("div", class_="calendarRow")
    region, date_start, location_name = scraper._extract_region_date_location(calendar_row)

    assert region == "W"
    assert date_start == "2025-03-20"
    assert location_name == "Test Ranch, Test City, AZ"


def test_extract_manager_info(scraper, sample_html):
    """Test extraction of ride manager information."""
    soup = BeautifulSoup(sample_html, "html.parser")
    calendar_row = soup.find("div", class_="calendarRow")
    manager = scraper._extract_manager_info(calendar_row)

    assert manager == "Test Manager"


def test_extract_website_flyer(scraper, sample_html):
    """Test extraction of website and flyer URLs."""
    soup = BeautifulSoup(sample_html, "html.parser")
    calendar_row = soup.find("div", class_="calendarRow")
    website, flyer = scraper._extract_website_flyer(calendar_row)

    assert website == "http://example.com"
    assert flyer == "http://example.com/flyer"


def test_extract_details(scraper, sample_html):
    """Test extraction of detailed event information."""
    soup = BeautifulSoup(sample_html, "html.parser")
    calendar_row = soup.find("div", class_="calendarRow")
    details = scraper._extract_details(calendar_row)

    assert details["ride_manager"] == "Test Manager"
    assert details["manager_email"] == "test@example.com"
    assert details["manager_phone"] == "123-456-7890"
    assert len(details["control_judges"]) == 1
    assert details["control_judges"][0]["name"] == "Dr. Test Judge"
    assert "description" in details
    assert "directions" in details


def test_determine_event_type(scraper, sample_html):
    """Test event type determination."""
    soup = BeautifulSoup(sample_html, "html.parser")
    calendar_row = soup.find("div", class_="calendarRow")
    event_type = scraper._determine_event_type(calendar_row)

    assert event_type == "endurance"


def test_determine_has_intro_ride(scraper, sample_html):
    """Test intro ride detection."""
    soup = BeautifulSoup(sample_html, "html.parser")
    calendar_row = soup.find("div", class_="calendarRow")
    has_intro = scraper._determine_has_intro_ride(calendar_row)

    assert has_intro is True


def test_determine_multi_day_and_pioneer(scraper, sample_distances):
    """Test multi-day and pioneer ride determination."""
    is_multi_day, is_pioneer, ride_days, date_end = scraper._determine_multi_day_and_pioneer(
        sample_distances, "2025-03-20"
    )

    assert is_multi_day is True
    assert is_pioneer is False
    assert ride_days == 2
    assert date_end == "2025-03-21"


def test_consolidate_events(scraper):
    """Test event consolidation."""
    events = [
        {"ride_id": "12345", "date": "2025-03-20", "distances": [{"distance": "50"}]},
        {"ride_id": "12345", "date": "2025-03-21", "distances": [{"distance": "75"}]}
    ]

    consolidated = scraper._consolidate_events(events)

    assert len(consolidated) == 1
    assert "12345" in consolidated
    assert len(consolidated["12345"]["distances"]) == 2
