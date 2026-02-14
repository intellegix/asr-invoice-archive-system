"""
ASR Invoice Archive System - Database Models and Connection
PostgreSQL/SQLite compatible database setup with SQLAlchemy
"""

import os
from typing import Optional

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Database configuration
Base = declarative_base()
metadata = MetaData()

# Global engine and session factory
engine = None
SessionFactory = None


def init_db(database_url: Optional[str] = None) -> None:
    """Initialize database connection and create tables"""
    global engine, SessionFactory

    if database_url is None:
        database_url = os.getenv("DATABASE_URL", "sqlite:///./data/invoice_archive.db")

    # Configure engine based on database type
    if database_url.startswith("postgresql"):
        # PostgreSQL production configuration
        engine = create_engine(
            database_url,
            pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
            pool_pre_ping=True,  # Verify connections
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            echo=False
        )
    else:
        # SQLite development configuration
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )

    # Create session factory
    SessionFactory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False
    )

    # Create tables
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Get database session"""
    if SessionFactory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    return SessionFactory()


def close_db():
    """Close database connections"""
    global engine
    if engine:
        engine.dispose()
        engine = None