"""Tests for the utils module."""

import pytest
from datetime import datetime
from app.utils import parse_date, parse_time, extract_city_state_country, generate_file_name


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
        assert result.hour == expected.hour
        assert result.minute == expected.minute


def test_parse_time_invalid():
    """Test parsing invalid time raises ValueError."""
    with pytest.raises(ValueError):
        parse_time("invalid time")


def test_extract_city_state_country():
    """Test extracting location components."""
    test_cases = [
        (
            "Las Colinas Ranch, Wickenburg, AZ",
            ("Las Colinas Ranch", "Wickenburg", "AZ", "USA")
        ),
        (
            "Durham Forest, Durham, ON",
            ("Durham Forest", "Durham", "ON", "Canada")
        )
    ]
    for location_string, expected in test_cases:
        city, state, country = extract_city_state_country(location_string)
        assert (city, state, country) == expected[1:]


def test_extract_city_state_country_incomplete():
    """Test extracting location with missing components."""
    result = extract_city_state_country("Wickenburg, AZ")
    assert result == ("Wickenburg", "AZ", "USA")


def test_generate_file_name():
    """Test generating standardized filenames."""
    test_cases = [
        (("12345", "AERC"), "aerc_12345.json"),
        (("ABC-123", "SERA"), "sera_abc_123.json")
    ]
    for (ride_id, source), expected in test_cases:
        assert generate_file_name(ride_id, source) == expected
