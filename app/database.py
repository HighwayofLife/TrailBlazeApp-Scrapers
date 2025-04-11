"""Database management module for the TrailBlazeApp-Scrapers project."""

from typing import Dict, Any, Optional, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from app.logging_manager import get_logger
from app.orm_models import Base, Event


class DatabaseManager:
    """
    Manages database interactions for the TrailBlazeApp-Scrapers project using SQLAlchemy ORM.
    """

    def __init__(
        self, db_config: Dict[str, str], scraper: Any = None, db_url: str = ""
    ) -> None:
        """
        Initialize DatabaseManager with database configuration.

        Args:
            db_config (Dict[str, str]): Database configuration parameters
            scraper (Any, optional): Scraper instance for metrics updates. Defaults to None.
            db_url (str, optional): SQLAlchemy database URL (for testing or custom DBs).
        """
        self.db_config = db_config
        self.scraper = scraper
        self.logger = get_logger(__name__).logger

        # Use db_url if provided (for testing), else build from db_config
        if db_url is not None:
            url = db_url
        elif "url" in db_config and db_config["url"]:
            url = db_config["url"]
        else:
            url = (
                f"postgresql+psycopg2://{db_config.get('user')}:"
                f"{db_config.get('password')}@{db_config.get('host', 'localhost')}:"
                f"{db_config.get('port', 5432)}/{db_config.get('database')}"
            )
        try:
            self.engine = create_engine(url, pool_pre_ping=True)
            self.Session = scoped_session(sessionmaker(bind=self.engine))
            self.logger.info("SQLAlchemy engine and sessionmaker initialized.")
        except Exception as e:
            self.logger.error(f"Failed to initialize SQLAlchemy engine: {e}")
            raise

    def close_pool(self) -> None:
        """Dispose of the SQLAlchemy engine and remove session."""
        if hasattr(self, "Session"):
            self.Session.remove()
        if hasattr(self, "engine"):
            self.engine.dispose()
        self.logger.info("SQLAlchemy engine disposed and session removed.")

    def insert_or_update_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Insert a new event or update an existing event in the database.

        Checks if an event with the same source and ride_id already exists.
        If it exists, updates the record; otherwise, inserts a new record.

        Args:
            event_data (Dict[str, Any]): Event data dictionary

        Returns:
            bool: True if operation was successful, False otherwise
        """
        source = event_data['source']
        ride_id = event_data['ride_id']

        session = self.Session()
        try:
            event = session.query(Event).filter_by(source=source, ride_id=ride_id).first()
            if event:
                # Update all fields
                for key, value in event_data.items():
                    if hasattr(event, key):
                        setattr(event, key, value)
                if self.scraper:
                    self.scraper.metrics_manager.increment('database_updates')
                self.logger.info(f"Updated event: {source} - {ride_id}")
            else:
                event = Event(**event_data)
                session.add(event)
                if self.scraper:
                    self.scraper.metrics_manager.increment('database_inserts')
                self.logger.info(f"Inserted new event: {source} - {ride_id}")
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error in insert_or_update_event: {e}")
            return False
        finally:
            session.close()

    def get_event(self, source: str, ride_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific event by source and ride_id.

        Args:
            source (str): Event source identifier
            ride_id (str): Unique ride identifier

        Returns:
            Optional[Dict[str, Any]]: Event data dictionary or None if not found
        """
        session = self.Session()
        try:
            event = session.query(Event).filter_by(source=source, ride_id=ride_id).first()
            if event:
                return self._event_to_dict(event)
            return None
        except SQLAlchemyError as e:
            self.logger.error(f"Error in get_event: {e}")
            return None
        finally:
            session.close()

    def get_events_by_source(self, source: str) -> List[Dict[str, Any]]:
        """
        Retrieve all events from a specific source.

        Args:
            source (str): Event source identifier (e.g., "AERC", "SERA")

        Returns:
            List[Dict[str, Any]]: List of event dictionaries

        Raises:
            Exception: If query execution fails
        """
        session = self.Session()
        try:
            events = session.query(Event).filter_by(source=source).all()
            result = [self._event_to_dict(event) for event in events]
            return result
        except SQLAlchemyError as e:
            self.logger.error(f"Error in get_events_by_source: {e}")
            return []
        finally:
            session.close()

    def delete_event(self, source: str, ride_id: str) -> bool:
        """
        Delete a specific event from the database.

        Args:
            source (str): Event source identifier
            ride_id (str): Unique ride identifier

        Returns:
            bool: True if event was deleted, False if event wasn't found

        Raises:
            Exception: If delete operation fails
        """
        session = self.Session()
        try:
            event = session.query(Event).filter_by(source=source, ride_id=ride_id).first()
            if not event:
                self.logger.info(f"Event {source}-{ride_id} not found, nothing to delete")
                return False
            session.delete(event)
            session.commit()
            self.logger.info(f"Successfully deleted event: {source} - {ride_id}")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error in delete_event: {e}")
            return False
        finally:
            session.close()

    def create_tables(self) -> None:
        """
        Create the necessary database tables if they don't exist.

        Uses SQLAlchemy's Base.metadata.create_all to create tables.
        Safe to call multiple times.

        Raises:
            Exception: If table creation fails
        """
        try:
            Base.metadata.create_all(self.engine)
            self.logger.info("Events table created or already exists (via SQLAlchemy ORM)")
        except Exception as e:
            self.logger.error(f"Failed to create tables: {e}")
            raise

    def _event_to_dict(self, event: Event) -> Dict[str, Any]:
        """Convert an Event ORM object to a dictionary, handling JSON fields."""
        return {
            "id": event.id,
            "name": event.name,
            "source": event.source,
            "event_type": event.event_type,
            "date_start": event.date_start.isoformat() if getattr(event, 'date_start', None) else None,
            "date_end": event.date_end.isoformat() if getattr(event, 'date_end', None) else None,
            "location_name": event.location_name,
            "city": event.city,
            "state": event.state,
            "country": event.country,
            "region": event.region,
            "is_canceled": event.is_canceled,
            "is_multi_day_event": event.is_multi_day_event,
            "is_pioneer_ride": event.is_pioneer_ride,
            "ride_days": event.ride_days,
            "ride_manager": event.ride_manager,
            "manager_email": event.manager_email,
            "manager_phone": event.manager_phone,
            "website": event.website,
            "flyer_url": event.flyer_url,
            "has_intro_ride": event.has_intro_ride,
            "ride_id": event.ride_id,
            "latitude": event.latitude,
            "longitude": event.longitude,
            "geocoding_attempted": event.geocoding_attempted,
            "description": event.description,
            "control_judges": event.control_judges,
            "distances": event.distances,
            "directions": event.directions,
            "created_at": event.created_at.isoformat() if getattr(event, 'created_at', None) else None,
            "updated_at": event.updated_at.isoformat() if event.updated_at is not None else None,
        }
