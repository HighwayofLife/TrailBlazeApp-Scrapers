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
    Extract City, State/Province, and Country from a location string.
    Handles various formats like "City, ST", "Venue, City, ST", "Address, City ST".

    Args:
        location_string (str): The location string to parse.

    Returns:
        Tuple[Optional[str], Optional[str], str]: (city, state, country)
        Country defaults to "USA" unless a Canadian province is detected.
    """
    if not location_string:
        return None, None, "USA"

    # Basic cleaning - remove leading/trailing whitespace and commas
    cleaned = location_string.strip().strip(',').strip()
    # Remove map link text variations if present
    cleaned = re.sub(r'Click Here for Directions via Google Maps.*', '', cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'via Google Maps.*', '', cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'Directions via Google Maps.*', '', cleaned, flags=re.IGNORECASE).strip()

    # List of Canadian provinces/territories (add more if needed)
    canadian_provinces = {"AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT"}

    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "USA"  # Default to USA

    # Split by comma, removing empty parts
    parts = [part.strip() for part in cleaned.split(',') if part.strip()]

    if len(parts) >= 3:
        # Assume format like: Venue/Address, City, State/Province [, Country]?
        # State/Province is likely the last part, City the second to last.
        state_part = parts[-1]
        city = parts[-2]

        # Check if state_part contains country info (e.g., "MB Canada")
        state_split = state_part.rsplit(' ', 1)
        if len(state_split) == 2 and state_split[1].lower() == 'canada':
            state = state_split[0]
            country = "Canada"
        else:
            state = state_part  # Assume last part is state/province

        if state in canadian_provinces:
            country = "Canada"

    elif len(parts) == 2:
        # Could be: "City, State" or "Address/Venue, City State"
        first_part = parts[0]
        second_part = parts[1]

        # Try splitting the second part by the last space
        city_state_split = second_part.rsplit(' ', 1)

        if len(city_state_split) == 2:
            # Likely "Address/Venue, City State" (e.g., "52 San Tomaso Rd, Alamogordo NM")
            potential_city = city_state_split[0]
            potential_state = city_state_split[1]
            # Basic validation for state (e.g., 2 letters or Canadian province)
            if (len(potential_state) == 2 and potential_state.isalpha()) or potential_state in canadian_provinces:
                city = potential_city
                state = potential_state
                if state in canadian_provinces:
                    country = "Canada"
            else:
                 # Didn't look like "City State", maybe it's "City, State" format?
                 city = first_part
                 state = second_part # Treat full second part as state initially
                 if not ((len(state) == 2 and state.isalpha()) or state in canadian_provinces):
                     state = None # Invalid state format
                 elif state in canadian_provinces:
                      country = "Canada"

        elif len(city_state_split) == 1: # rsplit found no space in second_part
            # Likely "City, State" format (e.g., "Asheville, NC")
            city = first_part
            state = second_part
            if not ((len(state) == 2 and state.isalpha()) or state in canadian_provinces):
                state = None # Invalid state format
            elif state in canadian_provinces:
                 country = "Canada"

    elif len(parts) == 1:
        # Only one part, could be City, State, "City State", etc.
        # Try splitting by last space
        city_state_split = parts[0].rsplit(' ', 1)
        if len(city_state_split) == 2:
            # Potentially "City State" format
            potential_city = city_state_split[0]
            potential_state = city_state_split[1]
            if (len(potential_state) == 2 and potential_state.isalpha()) or potential_state in canadian_provinces:
                city = potential_city
                state = potential_state
                if state in canadian_provinces:
                    country = "Canada"
            else:
                # Doesn't look like "City State", treat as just City
                city = parts[0]
        else:
            # No space, could be just City or just State
            if (len(parts[0]) == 2 and parts[0].isalpha()) or parts[0] in canadian_provinces:
                state = parts[0]
                if state in canadian_provinces:
                    country = "Canada"
            else:
                city = parts[0]

    # Final check for country based on state
    if state and state in canadian_provinces:
        country = "Canada"
    elif state and country == "USA":
        # Optional: Add validation against a list of US states if needed
        pass

    # Trim final results just in case
    city = city.strip() if city else None
    state = state.strip() if state else None

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
