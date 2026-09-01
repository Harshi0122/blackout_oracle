"""
Blackout Oracle - Database Base.

Defines the SQLAlchemy declarative base used by all
database models in the application.

Every model should inherit from:

    from app.db.base import Base

    class MyModel(Base):
        ...
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


# ============================================================
# DATABASE NAMING CONVENTION
# ============================================================

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# ============================================================
# DECLARATIVE BASE
# ============================================================


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy database models.
    """

    metadata = MetaData(
        naming_convention=NAMING_CONVENTION
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Base",
    "NAMING_CONVENTION",
]