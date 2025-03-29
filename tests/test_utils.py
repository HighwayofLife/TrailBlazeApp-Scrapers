"""Tests for the utils module."""

import pytest
from datetime import datetime
from app.utils import parse_date, parse_time, extract_city_state_country, generate_file_name

# Helper to compare expected time without date part
def assert_time_equal(dt1, dt2):
    """Assert that two datetime objects are equal, ignoring the date part."""
    assert dt1.hour == dt2.hour
    assert dt1.minute == dt2.minute
    assert dt1.second == dt2.second
    assert dt1.microsecond == dt2.microsecond

def test_parse_date_standard_format():
    """Test parsing date in standard format."""
    result = parse_date("2025-03-20")
    assert isinstance(result, datetime)
    assert result.year == 2025
    assert result.month == 3
    assert result.day == 20


def test_parse_date_alternate_formats():
    """Test parsing dates in various formats."""
    test_cases = [
        ("Mar 20, 2025", datetime(2025, 3, 20)),
        ("20-Mar-2025", datetime(2025, 3, 20)),
        ("March 20th, 2025", datetime(2025, 3, 20))
    ]
    for date_string, expected in test_cases:
        result = parse_date(date_string)
        assert result == expected


def test_parse_date_invalid():
    """Test parsing invalid date raises ValueError."""
    with pytest.raises(ValueError):
        parse_date("invalid date")


def test_parse_time_standard_format():
    """Test parsing time in standard format."""
    result = parse_time("07:00 am")
    assert isinstance(result, datetime)
    assert result.hour == 7
    assert result.minute == 0


def test_parse_time_alternate_formats():
    """Test parsing times in various formats."""
    test_cases = [
        ("7:00 AM", datetime.now().replace(hour=7, minute=0)),
        ("19:00", datetime.now().replace(hour=19, minute=0)),
        ("7:00PM", datetime.now().replace(hour=19, minute=0))
    ]
    for time_string, expected in test_cases:
        result = parse_time(time_string)
        # Use helper for comparison
        assert_time_equal(result, expected)


def test_parse_time_invalid():
    """Test parsing invalid time raises ValueError."""
    with pytest.raises(ValueError):
        parse_time("invalid time")


# New comprehensive, parameterized test for extract_city_state_country
@pytest.mark.parametrize(
    "location_string, expected_city, expected_state, expected_country",
    [
        # Standard US formats
        ("Cityville, CA", "Cityville", "CA", "USA"),
        ("Some Place, Cityville, CA", "Cityville", "CA", "USA"),
        ("123 Main St, Cityville, CA", "Cityville", "CA", "USA"),
        ("Venue Name, Cityville, CA", "Cityville", "CA", "USA"),
        ("Cityville CA", "Cityville", "CA", "USA"), # No comma
        ("  Cityville,  CA  ", "Cityville", "CA", "USA"), # Extra spaces
        ("Cityville, California", None, "California", "USA"), # Full state name - current logic might not handle well
        ("Anytown, USA", "Anytown", None, "USA"), # No state

        # Canadian formats
        ("Townsborough, ON", "Townsborough", "ON", "Canada"),
        ("The Ranch, Townsborough, ON", "Townsborough", "ON", "Canada"),
        ("Townsborough ON", "Townsborough", "ON", "Canada"),
        ("Maple Creek, SK, Canada", "Maple Creek", "SK", "Canada"), # Explicit country
        ("Maple Creek, SK Canada", "Maple Creek", "SK", "Canada"), # Explicit country, no comma
        ("National Park, Somewhere, AB", "Somewhere", "AB", "Canada"),

        # Edge cases and tricky formats
        ("Only City", "Only City", None, "USA"),
        ("TX", None, "TX", "USA"), # Only state
        ("BC", None, "BC", "Canada"), # Only province
        ("", None, None, "USA"), # Empty string
        (None, None, None, "USA"), # None input
        ("New York, NY Click Here for Directions via Google Maps", "New York", "NY", "USA"), # With map link
        ("St. Louis, MO, ", "St. Louis", "MO", "USA"), # Trailing comma
        (", , St. Louis, MO, ,", "St. Louis", "MO", "USA"), # Extra commas
        ("52 San Tomaso Rd, Alamogordo NM", "Alamogordo", "NM", "USA"), # Address, City State (from comments)
        ("Address Line 1, Address Line 2, Real City, NC", "Real City", "NC", "USA"), # Multi-line address
        ("City With Space, CA", "City With Space", "CA", "USA"),
        ("City With Space CA", "City With Space", "CA", "USA"),
    ]
)
def test_extract_city_state_country_comprehensive(location_string, expected_city, expected_state, expected_country):
    """Test extracting location components with various formats."""
    city, state, country = extract_city_state_country(location_string)
    assert city == expected_city
    assert state == expected_state
    assert country == expected_country


def test_generate_file_name():
    """Test generating standardized filenames."""
    test_cases = [
        (("12345", "AERC"), "aerc_12345.json"),
        (("ABC-123", "SERA"), "sera_abc_123.json")
    ]
    for (ride_id, source), expected in test_cases:
        assert generate_file_name(ride_id, source) == expected
