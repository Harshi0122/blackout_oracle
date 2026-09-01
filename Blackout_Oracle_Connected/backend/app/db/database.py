"""
Blackout Oracle - Database Configuration.

Creates the SQLAlchemy engine and provides the database
session used throughout the application.

Database flow:

    Application
         │
         ▼
    get_db()
         │
         ▼
    SQLAlchemy Session
         │
         ▼
    PostgreSQL
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


# ============================================================
# DATABASE ENGINE
# ============================================================

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)


# ============================================================
# SESSION FACTORY
# ============================================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# ============================================================
# DATABASE SESSION
# ============================================================


def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session.

    The session is automatically closed after the
    request or operation finishes.

    Yields:
        SQLAlchemy database session.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# DATABASE INITIALIZATION
# ============================================================


def init_db() -> None:
    """
    Initialize database tables.

    This creates all tables registered with SQLAlchemy's
    metadata.

    In production, Alembic migrations should be preferred
    over calling create_all() for schema changes.
    """

    # Import models so SQLAlchemy registers them with Base.metadata.
    from app.db import models  # noqa: F401

    from app.db.base import Base

    Base.metadata.create_all(
        bind=engine
    )


# ============================================================
# DATABASE HEALTH CHECK
# ============================================================


def check_database_connection() -> bool:
    """
    Check whether the application can connect to the database.

    Returns:
        True if the database connection succeeds,
        otherwise False.
    """
    from sqlalchemy import text

    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )

        return True

    except Exception:
        return False


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "check_database_connection",
]