"""Utility functions for the TrailBlazeApp-Scrapers project."""

from typing import Tuple, Optional
from datetime import datetime
import re
from dateutil import parser


def parse_date(date_string: str) -> datetime:
    """
    Parse a date string into a datetime object.

    Args:
        date_string (str): Date string in various possible formats (e.g., "Mar 20, 2025")

    Returns:
        datetime: Parsed datetime object

    Raises:
        ValueError: If the date string cannot be parsed
    """
    if not date_string:
        raise ValueError("Date string is empty")

    # Clean up the input
    date_string = date_string.strip()

    # If the input is already in YYYY-MM-DD format, just parse it directly
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_string):
        return datetime.strptime(date_string, "%Y-%m-%d")

    # Try to parse the date string using dateutil.parser, should handle most cases
    try:
        return parser.parse(date_string)
    except ValueError as e:
        raise ValueError(f"Could not parse date string: {date_string}") from e


def parse_time(time_string: str) -> datetime:
    """
    Parse a time string into a datetime object.

    Args:
        time_string (str): Time string (e.g., "07:00 am")

    Returns:
        datetime: Datetime object with current date and parsed time

    Raises:
        ValueError: If the time string cannot be parsed
    """
    # Clean up the input
    time_string = time_string.strip().upper()

    try:
        return parser.parse(time_string, default=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
    except ValueError as e:
        raise ValueError(f"Could not parse time string: {time_string}") from e


def extract_city_state_country(location_string: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    Extract city, state, and country from a location string.

    Args:
        location_string (str): Full location string (e.g., "Test Ranch, Test City, AZ")

    Returns:
        Tuple[Optional[str], Optional[str], str]: Tuple containing (city, state, country)
    """
    # Default country is USA unless specified
    country = "USA"

    if not location_string:
        return None, None, country

    # Clean up the input
    location = location_string.strip()

    # Check for Canadian provinces
    canadian_provinces = {
        "AB": "Canada", "BC": "Canada", "MB": "Canada", "NB": "Canada",
        "NL": "Canada", "NS": "Canada", "NT": "Canada", "NU": "Canada",
        "ON": "Canada", "PE": "Canada", "QC": "Canada", "SK": "Canada",
        "YT": "Canada", "Alberta": "Canada", "British Columbia": "Canada",
        "Manitoba": "Canada", "New Brunswick": "Canada", "Newfoundland": "Canada",
        "Nova Scotia": "Canada", "Northwest Territories": "Canada", "Nunavut": "Canada",
        "Ontario": "Canada", "Prince Edward Island": "Canada", "Quebec": "Canada",
        "Saskatchewan": "Canada", "Yukon": "Canada"
    }

    # Split by commas
    parts = [part.strip() for part in location.split(",")]

    # Default values
    city = None
    state = None

    if len(parts) >= 3:
        # Format: Ranch/Venue, City, State
        # Last part is likely state
        state = parts[-1]
        # Second to last part is likely city
        city = parts[-2]

        # Check if state is a Canadian province
        if state in canadian_provinces:
            country = "Canada"
    elif len(parts) == 2:
        # Format: City, State
        city = parts[0]
        state = parts[1]

        # Check if state is a Canadian province
        if state in canadian_provinces:
            country = "Canada"
    elif len(parts) == 1:
        # Only one part, might be just the state or just the city
        # Check if it's a state code (2 letters)
        if re.match(r"^[A-Z]{2}$", parts[0]):
            state = parts[0]

            # Check if state is a Canadian province
            if state in canadian_provinces:
                country = "Canada"
        else:
            city = parts[0]

    return city, state, country


def generate_file_name(ride_id: str, source: str) -> str:
    """
    Generate a standardized filename based on ride ID and source.

    Args:
        ride_id (str): The unique identifier for the ride
        source (str): The source of the ride data (e.g., "AERC")

    Returns:
        str: A standardized filename
    """
    # Standardize: lowercase and replace hyphens with underscores
    ride_id_clean = ride_id.lower().replace('-', '_')
    source_clean = source.lower()

    return f"{source_clean}_{ride_id_clean}.json"
