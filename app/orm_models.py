"""SQLAlchemy ORM models for the TrailBlazeApp-Scrapers project."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    Float,
    Text,
    JSON,
    UniqueConstraint,
    TIMESTAMP,
    func,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Event(Base):
    """SQLAlchemy ORM model for the events table."""

    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("source", "ride_id", name="uq_source_ride_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False)
    event_type = Column(String(50), nullable=False)
    date_start = Column(Date, nullable=False)
    date_end = Column(Date, nullable=True)
    location_name = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True, default="USA")
    region = Column(String(50), nullable=True)
    is_canceled = Column(Boolean, default=False)
    is_multi_day_event = Column(Boolean, default=False)
    is_pioneer_ride = Column(Boolean, default=False)
    ride_days = Column(Integer, default=1)
    ride_manager = Column(String(255), nullable=True)
    manager_email = Column(String(255), nullable=True)
    manager_phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    flyer_url = Column(String(255), nullable=True)
    has_intro_ride = Column(Boolean, default=False)
    ride_id = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geocoding_attempted = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    control_judges = Column(JSON, nullable=True)
    distances = Column(JSON, nullable=True)
    directions = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())  # pylint: disable=E1102
    updated_at = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )  # pylint: disable=E1102
