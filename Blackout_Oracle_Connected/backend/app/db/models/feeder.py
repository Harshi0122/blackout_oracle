"""
Blackout Oracle - Distribution Feeder Database Model.

Represents distribution feeders monitored by Blackout Oracle.

A feeder carries electrical power from a substation toward downstream
distribution loads.

The feeder model is used for:

- Distribution-grid monitoring
- Load analysis
- Overload detection
- Fault analysis
- Reliability analysis
- Weather-impact analysis
- Blackout-risk prediction
- Grid topology
- Simulation and contingency analysis

IMPORTANT
---------

This model stores information about electrical infrastructure.

It does NOT provide direct control of physical grid equipment.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
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


class FeederType(str, Enum):
    """
    Type of distribution feeder.
    """

    RADIAL = "radial"
    RING = "ring"
    NETWORK = "network"
    URBAN = "urban"
    RURAL = "rural"
    INDUSTRIAL = "industrial"
    COMMERCIAL = "commercial"
    MIXED = "mixed"
    OTHER = "other"


class FeederStatus(str, Enum):
    """
    Operational status of a feeder.
    """

    UNKNOWN = "unknown"
    ENERGIZED = "energized"
    DE_ENERGIZED = "de_energized"
    DEGRADED = "degraded"
    OVERLOADED = "overloaded"
    FAULTED = "faulted"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class FeederCriticality(str, Enum):
    """
    Importance of the feeder to the distribution network.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# FEEDER MODEL
# ============================================================


class Feeder(Base):
    """
    SQLAlchemy model representing a distribution feeder.
    """

    __tablename__ = "feeders"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"FDR-{uuid4().hex[:12].upper()}"
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

    feeder_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=FeederType.OTHER.value,
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

    # ========================================================
    # CONNECTED SUBSTATION
    # ========================================================

    substation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    source_bus_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    destination_bus_id: Mapped[str | None] = mapped_column(
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

    # ========================================================
    # ELECTRICAL CHARACTERISTICS
    # ========================================================

    nominal_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    maximum_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    minimum_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rated_power_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rated_current_a: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # REAL-TIME ELECTRICAL VALUES
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

    current_a: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    frequency_hz: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    power_factor: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # LOADING
    # ========================================================

    loading_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    peak_loading_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    overload_duration_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # OPERATIONAL STATUS
    # ========================================================

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=FeederStatus.UNKNOWN.value,
        index=True,
    )

    criticality: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=FeederCriticality.MEDIUM.value,
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
    # CUSTOMER / LOAD INFORMATION
    # ========================================================

    connected_customers: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    estimated_peak_demand_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    current_demand_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    critical_load_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
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

    failure_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    historical_failure_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    health_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    reliability_score: Mapped[float | None] = mapped_column(
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

    vegetation_exposure_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # MAINTENANCE
    # ========================================================

    installation_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_maintenance_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    next_maintenance_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ========================================================
    # OWNERSHIP
    # ========================================================

    owner: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    operator: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    # ========================================================
    # METADATA
    # ========================================================

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
            "ix_feeders_region_type",
            "region_id",
            "feeder_type",
        ),
        Index(
            "ix_feeders_substation",
            "substation_id",
        ),
        Index(
            "ix_feeders_source_bus",
            "source_bus_id",
        ),
        Index(
            "ix_feeders_destination_bus",
            "destination_bus_id",
        ),
        Index(
            "ix_feeders_status_criticality",
            "status",
            "criticality",
        ),
        Index(
            "ix_feeders_monitoring",
            "is_monitored",
            "is_active",
        ),
        Index(
            "ix_feeders_location",
            "latitude",
            "longitude",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<Feeder("
            f"id='{self.id}', "
            f"name='{self.name}', "
            f"type='{self.feeder_type}', "
            f"status='{self.status}', "
            f"loading={self.loading_percent}"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Feeder",
    "FeederType",
    "FeederStatus",
    "FeederCriticality",
]