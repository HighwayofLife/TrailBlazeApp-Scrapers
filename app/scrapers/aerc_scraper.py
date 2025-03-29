"""AERC-specific scraper implementation for the TrailBlazeApp-Scrapers project."""

import re
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from bs4 import BeautifulSoup
import requests

from app.base_scraper import BaseScraper
from app.utils import parse_date, extract_city_state_country
from app.exceptions import HTMLDownloadError


class AERCScraper(BaseScraper):
    """
    AERC-specific scraper implementation.

    Handles the specific HTML structure and data extraction logic for the AERC calendar website.
    """

    def __init__(self, cache_ttl: int = 86400) -> None:
        """
        Initialize the AERCScraper.

        Args:
            cache_ttl (int): Cache time-to-live in seconds (default: 86400 (24 hours))
        """
        super().__init__(source_name="AERC", cache_ttl=cache_ttl)

    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Main entry point for scraping AERC calendar data.

        Args:
            url (str): The URL to scrape (AERC calendar URL)

        Returns:
            Dict[str, Any]: Dictionary of consolidated event data
        """
        # Use methods from BaseScraper to get and parse HTML
        html_content = self.get_html(url)
        soup = self.parse_html(html_content)

        # Extract events from the parsed HTML
        events = self.extract_event_data(soup)

        # Consolidate events (combine multi-day events)
        consolidated_events = self._consolidate_events(events)

        # Display metrics
        self.display_metrics()

        return consolidated_events

    def extract_event_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract data for all events from the parsed HTML.

        Args:
            soup (BeautifulSoup): Parsed HTML document

        Returns:
            List[Dict[str, Any]]: List of dictionaries, one for each event row
        """
        all_events = []

        # Find all calendar rows
        calendar_rows = soup.find_all("div", class_="calendarRow")

        for row in calendar_rows:
            try:
                # Initialize event data dictionary
                event_data = {}

                # Extract basic event details
                name, ride_id, is_canceled = self._extract_name_and_id(row)
                region, date_start, location_name = self._extract_region_date_location(row)
                ride_manager = self._extract_manager_info(row)
                website, flyer_url = self._extract_website_flyer(row)
                event_type = self._determine_event_type(row)
                has_intro_ride = self._determine_has_intro_ride(row)

                # Get detailed event information
                details, is_past = self._extract_details(row)
                event_data.update({
                    "name": name,
                    "ride_id": ride_id,
                    "is_canceled": is_canceled,
                    "region": region,
                    "date_start": date_start,
                    "location_name": location_name,
                    "ride_manager": ride_manager,
                    "website": website,
                    "flyer_url": flyer_url,
                    "event_type": event_type,
                    "has_intro_ride": has_intro_ride,
                    "source": self.source_name
                })

                # Update with details
                event_data.update(details)

                if is_past:
                    self.logging_manager.info(
                        f"Past event detected (Ride ID: {ride_id}). Skipping results parsing for DB compatibility.",
                        emoji=":calendar:"
                    )
                    # Set default values for past events as we are skipping results/detailed distance parsing
                    event_data.update({
                        "is_multi_day_event": False,
                        "is_pioneer_ride": False,
                        "ride_days": 1,
                        "date_end": date_start # Date end is same as start for non-multi-day
                    })
                else:
                    # Determine multi-day event and pioneer status based on distances (only for future events)
                    is_multi_day, is_pioneer, ride_days, date_end = self._determine_multi_day_and_pioneer(
                        event_data.get("distances", []), date_start
                    )
                    event_data.update({
                        "is_multi_day_event": is_multi_day,
                        "is_pioneer_ride": is_pioneer,
                        "ride_days": ride_days,
                        "date_end": date_end
                    })

                # Extract city, state, country from location
                city, state, country = extract_city_state_country(location_name)
                event_data.update({
                    "city": city,
                    "state": state,
                    "country": country
                })

                all_events.append(event_data)
                self.metrics_manager.increment("events_extracted")

            except (AttributeError, ValueError, TypeError) as e:
                self.logging_manager.error(f"Error extracting event data: {str(e)}")
                self.metrics_manager.increment("event_extraction_errors")

        self.logging_manager.info(f"Extracted {len(all_events)} events")
        return all_events

    def _extract_name_and_id(self, calendar_row: Any) -> Tuple[str, str, bool]:
        """
        Extract event name, ride ID, and cancellation status from a calendar row.

        Args:
            calendar_row (Any): BeautifulSoup element representing a calendar row

        Returns:
            Tuple[str, str, bool]: (name, ride_id, is_canceled)
        """
        # Find the span with class="rideName details"
        ride_name_span = calendar_row.find("span", class_="rideName details")

        if not ride_name_span:
            # If not found, try alternative selectors
            ride_name_span = calendar_row.find("span", class_="details")
            if not ride_name_span:
                raise ValueError("Could not find ride name and ID")

        # Extract ride_id from the tag attribute
        ride_id = ride_name_span.get("tag", "")
        if not ride_id:
            # Try other ways to extract ride ID
            onclick = ride_name_span.get("onclick", "")
            id_match = re.search(r"rideID(\d+)", onclick)
            if id_match:
                ride_id = id_match.group(1)
            else:
                # Last resort - generate from name
                ride_id = f"unknown_{hash(ride_name_span.text) % 10000}"

        # Extract name from the text content
        name = ride_name_span.text.strip()

        # Check for cancellation
        is_canceled = False
        cancel_span = ride_name_span.find("span", class_="red bold")
        if cancel_span and "cancelled" in cancel_span.text.lower():
            is_canceled = True

        return name, ride_id, is_canceled

    def _extract_region_date_location(self, calendar_row: Any) -> tuple:
        """
        Extract region, date, and location from calendar row.

        Args:
            calendar_row (Any): BeautifulSoup element representing a calendar row

        Returns:
            tuple: (region, date_start, location_name)
        """
        region = None
        date_start = None
        location_name = None

        try:
            # Extract region (usually in the first td with class="region")
            region_td = calendar_row.find("td", class_="region")
            if region_td:
                region = region_td.get_text().strip()

            # Find date in td with class="bold"
            date_td = calendar_row.find("td", class_="bold")
            if date_td:
                date_text = date_td.get_text().strip()
                try:
                    # First try direct parsing with utility function
                    dt = parse_date(date_text)
                    date_start = dt.strftime("%Y-%m-%d")
                except ValueError:
                    # Try MM/DD/YYYY format if direct parsing fails
                    date_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', date_text)
                    if date_match:
                        month, day, year = date_match.groups()
                        date_start = f"{year}-{month}-{day}"

            # Find location td - it's in the second row's second td cell
            fix_jumpy_rows = calendar_row.find_all("tr", class_="fix-jumpy")
            if fix_jumpy_rows and len(fix_jumpy_rows) > 1:
                location_td = fix_jumpy_rows[1].find_all("td")
                if len(location_td) > 1:  # Second td in the second tr.fix-jumpy
                    location_text = location_td[1].get_text().strip()
                    # Clean up location text (remove map link text)
                    location_match = re.match(r'(.*?)(?:Click Here for Directions|$)', location_text, re.DOTALL)
                    if location_match:
                        location_name = location_match.group(1).strip()

            # If location not found, try alternative method from details section
            if not location_name:
                details_section = calendar_row.find("table", class_="detailData")
                if details_section:
                    location_row = details_section.find("tr", string=lambda s: s and "Location :" in s)
                    if location_row:
                        location_text = location_row.find_all("td")[-1].get_text().strip()
                        location_match = re.match(r'(.*?)(?:Click Here for Directions|$)', location_text, re.DOTALL)
                        if location_match:
                            location_name = location_match.group(1).strip()

        except (AttributeError, ValueError, TypeError) as e:
            self.logging_manager.error(f"Error extracting region/date/location: {e}")

        return (region, date_start, location_name)

    def _extract_manager_info(self, calendar_row: Any) -> str:
        """
        Extract ride manager's name from a calendar row.

        Args:
            calendar_row (Any): BeautifulSoup element representing a calendar row

        Returns:
            str: Ride manager's name
        """
        # First try to get from details section since it's more structured
        # Call _extract_details and get the dictionary part of the tuple
        details_info_dict, _ = self._extract_details(calendar_row)
        if details_info_dict.get("ride_manager"):
            return details_info_dict["ride_manager"]

        # If not found in details, try the main calendar row
        # Find the third tr.fix-jumpy row which usually contains manager info
        fix_jumpy_rows = calendar_row.find_all("tr", class_="fix-jumpy")
        manager_tr = fix_jumpy_rows[2] if len(fix_jumpy_rows) > 2 else None

        if manager_tr:
            # Find the td containing "mgr:"
            manager_td = manager_tr.find(lambda tag: tag.name == "td" and "mgr:" in tag.get_text())
            if manager_td:
                mgr_text = manager_td.get_text(strip=True)
                # Extract just the name before any comma, phone, or email
                manager_match = re.search(r"mgr:\s*([^,(]*)", mgr_text)
                if manager_match:
                    return manager_match.group(1).strip()

        # Fallback if not found in standard places
        self.logging_manager.warning("Could not extract manager name.", ":person_shrugging:")
        return "Unknown"

    def _extract_website_flyer(self, calendar_row: Any) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract website and flyer URLs from a calendar row.

        Args:
            calendar_row (Any): BeautifulSoup element representing a calendar row

        Returns:
            Tuple[Optional[str], Optional[str]]: (website_url, flyer_url)
        """
        website_url = None
        flyer_url = None

        # First check links in the main calendar row
        for link in calendar_row.find_all("a"):
            href = link.get("href")
            if not href:
                continue

            link_text = link.text.lower().strip()
            if "website" in link_text:
                website_url = href
            elif any(text in link_text for text in ["entry", "flyer", "entry/flyer"]):
                flyer_url = href

        # Then check in the details section if not found
        if not website_url or not flyer_url:
            details_table = calendar_row.find("table", class_="detailData")
            if details_table:
                for link in details_table.find_all("a"):
                    href = link.get("href")
                    if not href:
                        continue

                    if not website_url and "website" in link.get_text().lower():
                        website_url = href
                        # If the link text says "follow this link", get the actual URL
                        if href.startswith("http"):
                            website_url = href
                    elif not flyer_url and any(text in link.get_text().lower() for text in ["entry", "flyer", "entry/flyer"]):
                        flyer_url = href

        return website_url, flyer_url

    def _extract_details(self, calendar_row: Any) -> Tuple[Dict[str, Any], bool]:
        """
        Extract detailed event information from the expanded details section.
        Detects if the event is a past event based on results data.

        Args:
            calendar_row (Any): BeautifulSoup element representing a calendar row

        Returns:
            Tuple[Dict[str, Any], bool]: Dictionary containing detailed event information
                                        and a boolean flag indicating if it's a past event.
        """
        details = {
            "control_judges": [],
            "distances": [], # Will remain empty for past events for now
            "description": None,
            "directions": None,
            "manager_email": None,
            "manager_phone": None,
            "ride_manager": None
            # NOTE: results_by_distance is intentionally omitted from this dict
        }
        is_past = False # Flag to indicate if this is a past event

        # Find the ride ID
        ride_id = None
        ride_name_span = calendar_row.find("span", class_="rideName details")
        if ride_name_span:
            ride_id = ride_name_span.get("tag", "")

        # Find the details row
        details_tr = None
        if ride_id:
            details_tr = calendar_row.find("tr", attrs={"name": f"{ride_id}Details"})

        if not details_tr:
            # Try to find by class
            details_tr = calendar_row.find("tr", class_="toggle-ride-dets")

        if not details_tr:
            return details, is_past

        # Find the detail data table
        detail_table = details_tr.find("table", class_="detailData")
        if not detail_table:
            # Check if this is because it's a past event (indicated by "* Results *" link)
            results_link = calendar_row.find("span", class_="details", string=lambda s: s and "* Results *" in s)
            if results_link:
                self.logging_manager.debug(f"Detected past event by '* Results *' link for ride_id: {ride_id}")
                is_past = True
                # Attempt to find the details table again, it might be there even with results link
                detail_table = details_tr.find("table", class_="detailData")
                if not detail_table:
                    return details, is_past # Return early if no details table found for past event
            else:
                return details, is_past # Return early if no details table found

        # Get the default date from the calendar row
        default_date = None
        region_date_location = self._extract_region_date_location(calendar_row)
        if region_date_location:
            default_date = region_date_location[1]  # date_start is the 2nd item

        # Process each row in the detail table
        for tr in detail_table.find_all("tr"):
            tds = tr.find_all("td")
            td_text = tr.get_text().strip()

            # Check for indicators of a past event's results section
            # Check for links like '.../rides-ride-result/?distance=...'
            results_links = tr.find_all("a", href=lambda href: href and "rides-ride-result" in href)
            if results_links:
                is_past = True
                self.logging_manager.debug(f"Detected past event by results link for ride_id: {ride_id}")
                # Attempt to extract minimal distance info from results row for context, but don't store full results
                try:
                    distance_text = tds[0].get_text(strip=True) if tds else "" # Might contain distance like '50 mi'
                    date_text = tds[1].get_text(strip=True) if len(tds) > 1 else "" # Contains date and time
                    results_info_text = tds[2].get_text(strip=True) if len(tds) > 2 else "" # Contains starters/finishers

                    # Try parsing basic distance info if needed later, but for now, skip adding to details['distances']
                    # Example: dist_match = re.search(r'(\d+)', distance_text)
                    # Example: date = parse_date(...) from date_text
                    # Example: start_time = re.search(...) from date_text

                    # Skip parsing the rest of this row as it's results data we're not storing yet
                    continue
                except Exception as e:
                    self.logging_manager.warning(f"Could not parse basic info from results row: {td_text} - Error: {e}")
                    continue # Move to next row

            # If already identified as past, skip standard distance processing
            if is_past and "Distances" in td_text:
                continue

            # Process manager info (common to past and future)
            if "Ride Manager" in td_text:
                # Extract manager name - everything before the first parenthesis or comma
                manager_match = re.search(r"Ride Manager\s*:\s*([^,(]*)", td_text)
                if manager_match:
                    details["ride_manager"] = manager_match.group(1).strip()

                # Extract phone number from parentheses
                phone_match = re.search(r"\(\s*([0-9\-\s]+)\s*\)", td_text)
                if phone_match:
                    details["manager_phone"] = phone_match.group(1).strip()

                # Extract email from parentheses containing @
                email_match = re.search(r"\(\s*([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\s*\)", td_text)
                if email_match:
                    details["manager_email"] = email_match.group(1).strip()

            # Process control judges (common to past and future)
            elif "Control Judge" in td_text:
                judge_match = re.search(r"(.*Control Judge)\s*:\s*(.*)", td_text)
                if judge_match:
                    role = judge_match.group(1).strip()
                    name = judge_match.group(2).strip()
                    details["control_judges"].append({"name": name, "role": role})

            # Process distances (only for future events)
            elif "Distances" in td_text and not is_past: # Added 'and not is_past' condition
                distances_text = td_text.replace("Distances", "").replace(":", "").strip()

                # Split by commas or "and"
                distance_parts = [d.strip() for d in re.split(r',|\s+and\s+', distances_text) if d.strip()]

                # Process each distance entry
                for dist in distance_parts:
                    # Initialize distance object with default date
                    distance_obj = {
                        "distance": "",
                        "date": default_date,
                        "start_time": "00:00"  # Provide a default start_time
                    }

                    # Extract distance value (e.g., "50", "100")
                    dist_match = re.search(r'(\d+)(?:\s*mi(?:les)?)?', dist)
                    if dist_match:
                        distance_value = dist_match.group(1)
                        distance_obj["distance"] = distance_value

                        # Look for "mi" or "miles" and include in the distance
                        if "mi" in dist or "miles" in dist:
                            distance_obj["distance"] = f"{distance_value} miles"
                    else:
                        continue  # Skip if no distance found

                    # Check for specific date in the distance description (e.g., "May 1")
                    date_match = re.search(r'\(((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:,?\s+\d{4})?)\)', dist)
                    if date_match:
                        date_text = date_match.group(1)
                        try:
                            # If the matched date doesn't include a year, add the year from default_date
                            if not re.search(r'\d{4}', date_text):
                                year = default_date.split('-')[0] if default_date else "2025"
                                date_text += f", {year}"

                            parsed_date = parse_date(date_text)
                            distance_obj["date"] = parsed_date
                        except ValueError:
                            # If parsing fails, keep the default date
                            self.logging_manager.warning(f"Could not parse date from distance: {date_text}")

                    # Try to extract start time if present
                    time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm))', dist.lower())
                    if time_match:
                        distance_obj["start_time"] = time_match.group(1)

                    details["distances"].append(distance_obj)

            # Process description (common to past and future)
            elif "Description" in td_text:
                desc_match = re.search(r"Description\s*:(.*?)(?:Directions|$)", td_text, re.DOTALL)
                if desc_match:
                    details["description"] = desc_match.group(1).strip()

            # Process directions (common to past and future)
            elif "Directions" in td_text:
                dir_match = re.search(r"Directions\s*:(.*)", td_text, re.DOTALL)
                if dir_match:
                    details["directions"] = dir_match.group(1).strip()

        # If it's a past event, clear the distances list as we didn't populate it meaningfully
        if is_past:
            details["distances"] = []

        return details, is_past

    def _determine_event_type(self, calendar_row: Any) -> str:
        """
        Determine the event type from a calendar row.

        Args:
            calendar_row (Any): BeautifulSoup element representing a calendar row

        Returns:
            str: Event type (defaults to "endurance")
        """
        # Look for indicators of non-endurance events
        text = calendar_row.get_text().lower()

        if "competitive trail" in text:
            return "competitive_trail"
        elif "ctc" in text:
            return "competitive_trail"
        elif "limited distance" in text:
            return "limited_distance"
        elif "ld" in text and not "old" in text.split("ld"):
            return "limited_distance"

        # Default to endurance
        return "endurance"

    def _determine_has_intro_ride(self, calendar_row: Any) -> bool:
        """
        Check if the event has an intro ride.

        Args:
            calendar_row (Any): BeautifulSoup element representing a calendar row

        Returns:
            bool: True if the event has an intro ride, False otherwise
        """
        # Look for "Has Intro Ride!" indicator
        intro_span = calendar_row.find("span", style=lambda s: s and "red" in s)
        if intro_span and "intro ride" in intro_span.text.lower():
            return True

        # Check in the text content
        text = calendar_row.get_text().lower()
        if "intro ride" in text:
            return True

        return False

    def _determine_multi_day_and_pioneer(
        self, distances: List[Dict[str, Any]], date_start: str
    ) -> Tuple[bool, bool, int, str]:
        """
        Determine if event is multi-day/pioneer and calculate ride days.

        Args:
            distances (List[Dict[str, Any]]): List of distances with their dates
            date_start (str): Start date of the event

        Returns:
            Tuple[bool, bool, int, str]: (is_multi_day_event, is_pioneer_ride, ride_days, date_end)
        """
        # Default values
        is_multi_day_event = False
        is_pioneer_ride = False
        ride_days = 1
        date_end = date_start

        # If there are no distances, use default values
        if not distances:
            return is_multi_day_event, is_pioneer_ride, ride_days, date_end

        # Get unique dates from distances
        unique_dates = set()
        for distance in distances:
            if "date" in distance and distance["date"]:
                unique_dates.add(distance["date"])

        self.logging_manager.debug(f"Found unique dates in distances: {unique_dates}")

        # If there's only one date, it's a single-day event
        if len(unique_dates) <= 1:
            return is_multi_day_event, is_pioneer_ride, ride_days, date_end

        # It's a multi-day event
        is_multi_day_event = True

        # Calculate ride days based on dates range
        date_list = sorted(list(unique_dates))
        date_end = date_list[-1]  # Latest date

        self.logging_manager.debug(f"Multi-day event detected with dates: {date_list}")

        # Convert to datetime objects to calculate days difference
        try:
            start_dt = datetime.strptime(date_start, "%Y-%m-%d")
            end_dt = datetime.strptime(date_end, "%Y-%m-%d")
            ride_days = (end_dt - start_dt).days + 1
        except (ValueError, TypeError):
            # If there's an error in date calculation, default to the length of unique dates
            ride_days = len(unique_dates)
            self.logging_manager.warning(f"Error calculating days difference, using {ride_days} from unique dates")

        # DEBUG: Print the date calculation
        self.logging_manager.debug(f"Date calculation: {date_start} to {date_end} = {ride_days} days")

        # Check for pioneer ride (3 or more days)
        # Ensure ride_days is at least 3 for pioneer rides
        if ride_days >= 3:
            is_pioneer_ride = True
            self.logging_manager.debug(f"Setting is_pioneer_ride=True because ride_days={ride_days} >= 3")
        else:
            # Ensure is_pioneer_ride is False if ride_days < 3
            is_pioneer_ride = False
            self.logging_manager.debug(f"Setting is_pioneer_ride=False because ride_days={ride_days} < 3")

        self.logging_manager.debug(f"Event details - multi-day: {is_multi_day_event}, pioneer: {is_pioneer_ride}, days: {ride_days}, start: {date_start}, end: {date_end}")

        return is_multi_day_event, is_pioneer_ride, ride_days, date_end

    def get_html(self, url: str) -> str:
        """
        Retrieve HTML content from the AERC calendar URL with proper headers.

        Args:
            url (str): The URL to fetch HTML from

        Returns:
            str: The HTML content

        Raises:
            HTMLDownloadError: If the HTML content cannot be downloaded
        """
        # Define headers required for the AERC site as specified in scraping_guide.md
        headers = {
            "Referer": "https://aerc.org/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }

        key = f"html_content_{url}"
        cached_html = self.cache.get(key)
        if cached_html:
            self.metrics_manager.increment('cache_hits')
            self.logging_manager.info(f"Cache hit for URL: {url}", emoji=":rocket:")
            return cached_html
        else:
            self.metrics_manager.increment('cache_misses')
            self.logging_manager.info(f"Cache miss for URL: {url}, fetching...", emoji=":hourglass:")
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                html_content = response.text

                # Store in cache
                self.cache.set(key, html_content)

                return html_content
            except requests.RequestException as e:
                self.logging_manager.error(f"Failed to fetch HTML from URL: {url}. Error: {str(e)}", ":x:")
                self.metrics_manager.increment('html_download_errors')
                raise HTMLDownloadError(f"Failed to download HTML from {url}: {str(e)}") from e
