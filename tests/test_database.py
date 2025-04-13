"""Tests for the DatabaseManager module (SQLAlchemy ORM version)."""

from datetime import date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.database import DatabaseManager
from app.orm_models import Base
from app.config import get_db_config


@pytest.fixture
def db_config():
    config = get_db_config()
    config["url"] = "sqlite:///:memory:"
    return config


@pytest.fixture
def db_manager(db_config):
    # Pass db_url to DatabaseManager for SQLite in-memory
    mgr = DatabaseManager(db_config, db_url=db_config["url"])
    mgr.engine = create_engine(db_config["url"])
    mgr.Session = scoped_session(sessionmaker(bind=mgr.engine))
    Base.metadata.create_all(mgr.engine)
    return mgr


@pytest.fixture
def sample_event():
    return {
        "name": "Test Event",
        "source": "TEST",
        "event_type": "endurance",
        "date_start": date(2025, 1, 1),
        "date_end": date(2025, 1, 2),
        "location_name": "Test Location",
        "city": "Test City",
        "state": "TS",
        "country": "USA",
        "region": "West",
        "is_canceled": False,
        "is_multi_day_event": True,
        "is_pioneer_ride": False,
        "ride_days": 2,
        "ride_manager": "Test Manager",
        "manager_email": "test@example.com",
        "manager_phone": "123-456-7890",
        "website": "https://example.com",
        "flyer_url": "https://example.com/flyer.pdf",
        "has_intro_ride": False,
        "ride_id": "test-123",
        "latitude": 35.0,
        "longitude": -120.0,
        "geocoding_attempted": False,
        "description": "A test event.",
        "control_judges": [{"name": "Judge Judy", "role": "Control Judge"}],
        "distances": [{"distance": "50", "date": "2025-01-01"}],
        "directions": "Go north."
    }


def test_create_tables(db_manager):
    db_manager.create_tables()  # Should not raise


def test_insert_and_get_event(db_manager, sample_event):
    assert db_manager.insert_or_update_event(sample_event) is True
    event = db_manager.get_event("TEST", "test-123")
    assert event is not None
    assert event["name"] == "Test Event"
    assert event["ride_id"] == "test-123"
    assert event["control_judges"][0]["name"] == "Judge Judy"


def test_update_event(db_manager, sample_event):
    db_manager.insert_or_update_event(sample_event)
    updated = sample_event.copy()
    updated["name"] = "Updated Event"
    updated["is_canceled"] = True
    assert db_manager.insert_or_update_event(updated) is True
    event = db_manager.get_event("TEST", "test-123")
    assert event["name"] == "Updated Event"
    assert event["is_canceled"] is True


def test_get_events_by_source(db_manager, sample_event):
    db_manager.insert_or_update_event(sample_event)
    events = db_manager.get_events_by_source("TEST")
    assert isinstance(events, list)
    assert len(events) == 1
    assert events[0]["ride_id"] == "test-123"


def test_delete_event(db_manager, sample_event):
    db_manager.insert_or_update_event(sample_event)
    assert db_manager.delete_event("TEST", "test-123") is True
    assert db_manager.get_event("TEST", "test-123") is None


def test_delete_event_not_found(db_manager):
    assert db_manager.delete_event("TEST", "nonexistent") is False
