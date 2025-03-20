"""Data models module for the TrailBlazeApp-Scrapers project."""

from typing import List, Dict, Optional
from datetime import datetime
try:
    from pydantic import BaseModel, Field, validator
except ImportError:
    raise ImportError("Pydantic is required for data validation. Please install it with 'pip install pydantic==2.*'")


class ControlJudge(BaseModel):
    """Model for control judge data."""
    name: str
    role: str = "Control Judge"


class Distance(BaseModel):
    """Model for distance data."""
    distance: str
    date: str
    start_time: Optional[str] = None


class EventDataModel(BaseModel):
    """Model for event data validation."""
    source: str
    ride_id: str
    name: str
    region: str
    date_start: str
    date_end: Optional[str] = None
    location_name: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "USA"
    ride_manager: str
    manager_phone: Optional[str] = None
    manager_email: Optional[str] = None
    website: Optional[str] = None
    flyer_url: Optional[str] = None
    is_canceled: bool = False
    is_multi_day_event: bool = False
    is_pioneer_ride: bool = False
    ride_days: int = 1
    event_type: str = "endurance"
    has_intro_ride: bool = False
    description: Optional[str] = None
    directions: Optional[str] = None
    control_judges: List[Dict[str, str]] = Field(default_factory=list)
    distances: List[Dict[str, str]] = Field(default_factory=list)
    
    @validator('date_start', 'date_end')
    def validate_date_format(cls, v):
        """Validate date format is YYYY-MM-DD."""
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError as exc:
                raise ValueError('Date must be in format YYYY-MM-DD') from exc
        return v
    
    @validator('ride_days')
    def validate_ride_days(cls, v, values):
        """Validate ride_days is consistent with multi-day event status."""
        is_multi_day = values.get('is_multi_day_event', False)
        if is_multi_day and v < 2:
            raise ValueError('Multi-day events must have ride_days >= 2')
        if not is_multi_day and v != 1:
            raise ValueError('Single-day events must have ride_days = 1')
        return v
    
    @validator('is_pioneer_ride')
    def validate_pioneer_ride(cls, v, values):
        """Validate pioneer ride status is consistent with ride_days."""
        ride_days = values.get('ride_days', 1)
        if v and ride_days < 3:
            raise ValueError('Pioneer rides must have ride_days >= 3')
        return v
