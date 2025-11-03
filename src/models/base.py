"""
PingMonitor Pro v2.0 - Database Base
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Base class for all models
Base = declarative_base()


class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DatabaseManager:
    """Database connection and session manager"""

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, database_url: str = None):
        """
        Initialize database connection

        Args:
            database_url: SQLAlchemy database URL
        """
        if database_url is None:
            db_path = Path.home() / ".pingmonitor" / "pingmonitor.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            database_url = f"sqlite:///{db_path}"

        self._engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600
        )

        self._session_factory = scoped_session(
            sessionmaker(bind=self._engine, autocommit=False, autoflush=False)
        )

        # Create all tables
        Base.metadata.create_all(self._engine)
        logger.info("Database initialized successfully")

    def get_session(self):
        """Get a new database session"""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._session_factory()

    def close(self):
        """Close database connection"""
        if self._session_factory:
            self._session_factory.remove()
        if self._engine:
            self._engine.dispose()
        logger.info("Database connection closed")


# Global instance
db_manager = DatabaseManager()
