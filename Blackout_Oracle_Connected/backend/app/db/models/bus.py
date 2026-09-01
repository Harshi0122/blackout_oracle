"""
Blackout Oracle - Bus Database Model.

Represents electrical buses / busbars within the monitored power grid.

A bus is a logical electrical node to which equipment such as:

- Transmission lines
- Distribution feeders
- Transformers
- Generators
- Circuit breakers
- Other grid equipment

may be connected.

Blackout Oracle can use bus information for:

- Grid topology
- Voltage monitoring
- Power-flow analysis
- Contingency analysis
- Cascade-risk analysis
- Digital-twin simulations

IMPORTANT
---------

This model stores grid topology and measurements.

It does NOT provide direct control of physical electrical equipment.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# ============================================================
# ENUMS
# ============================================================


class BusType:
    """
    Common electrical bus categories.

    These are represented as strings in the database so the model
    remains compatible with external grid-data sources.
    """

    SLACK = "slack"
    PV = "pv"
    PQ = "pq"
    LOAD = "load"
    GENERATION = "generation"
    TRANSFORMER = "transformer"
    DISTRIBUTION = "distribution"
    TRANSMISSION = "transmission"
    OTHER = "other"


class BusStatus:
    """
    Operational status values for a bus.
    """

    UNKNOWN = "unknown"
    ENERGIZED = "energized"
    DE_ENERGIZED = "de_energized"
    DEGRADED = "degraded"
    FAULTED = "faulted"
    MAINTENANCE = "maintenance"


# ============================================================
# BUS MODEL
# ============================================================


class Bus(Base):
    """
    SQLAlchemy model representing an electrical bus/busbar.
    """

    __tablename__ = "buses"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"BUS-{uuid4().hex[:12].upper()}"
        ),
    )

    # ========================================================
    # IDENTIFICATION
    # ========================================================

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    external_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        unique=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    bus_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=BusType.OTHER,
        index=True,
    )

    # ========================================================
    # GRID REGION
    # ========================================================

    region_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    region_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    substation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # ========================================================
    # LOCATION
    # ========================================================

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    elevation_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # ELECTRICAL CHARACTERISTICS
    # ========================================================

    nominal_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    minimum_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    maximum_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    base_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # POWER FLOW
    # ========================================================

    active_power_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    reactive_power_mvar: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    apparent_power_mva: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    power_factor: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # VOLTAGE / FREQUENCY
    # ========================================================

    voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    voltage_pu: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    frequency_hz: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # OPERATIONAL STATUS
    # ========================================================

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=BusStatus.UNKNOWN,
        index=True,
    )

    is_energized: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    is_monitored: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # ========================================================
    # CONNECTIVITY
    # ========================================================

    connected_asset_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    connected_bus_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ========================================================
    # TELEMETRY
    # ========================================================

    telemetry_source: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    telemetry_asset_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    last_telemetry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ========================================================
    # RELIABILITY
    # ========================================================

    health_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    overload_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    voltage_stability_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # ENVIRONMENTAL EXPOSURE
    # ========================================================

    flood_exposure_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    storm_exposure_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    temperature_exposure_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # METADATA
    # ========================================================

    owner: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    operator: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        onupdate=lambda: datetime.now(
            timezone.utc
        ),
    )

    # ========================================================
    # DATABASE INDEXES
    # ========================================================

    __table_args__ = (
        Index(
            "ix_buses_region_type",
            "region_id",
            "bus_type",
        ),
        Index(
            "ix_buses_substation",
            "substation_id",
        ),
        Index(
            "ix_buses_status_energized",
            "status",
            "is_energized",
        ),
        Index(
            "ix_buses_location",
            "latitude",
            "longitude",
        ),
        Index(
            "ix_buses_monitoring",
            "is_monitored",
            "is_active",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<Bus("
            f"id='{self.id}', "
            f"name='{self.name}', "
            f"type='{self.bus_type}', "
            f"status='{self.status}'"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Bus",
    "BusType",
    "BusStatus",
]