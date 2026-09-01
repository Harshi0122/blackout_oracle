"""
Blackout Oracle - Generator Database Model.

Represents electrical generation assets monitored by Blackout Oracle.

The generator model stores:

- Generator identity
- Generation capacity
- Current generation
- Operating state
- Fuel information
- Renewable generation information
- Telemetry information
- Reliability information
- Environmental exposure
- Maintenance information

This information can later be used by the forecasting and risk engines
to determine whether insufficient generation capacity could contribute
to a blackout or cascading grid failure.

IMPORTANT
---------

This model stores generation information.

It does NOT provide direct control over generators or other physical
electrical infrastructure.
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


class GeneratorType(str, Enum):
    """
    Type of electrical generator.
    """

    THERMAL = "thermal"
    COAL = "coal"
    GAS = "gas"
    DIESEL = "diesel"
    HYDRO = "hydro"
    NUCLEAR = "nuclear"
    SOLAR = "solar"
    WIND = "wind"
    BIOMASS = "biomass"
    BATTERY = "battery"
    OTHER = "other"


class GeneratorStatus(str, Enum):
    """
    Current operational status of a generator.
    """

    UNKNOWN = "unknown"
    ONLINE = "online"
    OFFLINE = "offline"
    STARTING = "starting"
    STOPPING = "stopping"
    MAINTENANCE = "maintenance"
    FAULTED = "faulted"
    DEGRADED = "degraded"


class GeneratorCriticality(str, Enum):
    """
    Importance of the generator to grid reliability.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# GENERATOR MODEL
# ============================================================


class Generator(Base):
    """
    SQLAlchemy model representing an electrical generator.
    """

    __tablename__ = "generators"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"GEN-{uuid4().hex[:12].upper()}"
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

    generator_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=GeneratorType.OTHER.value,
        index=True,
    )

    fuel_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
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

    plant_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    substation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    bus_id: Mapped[str | None] = mapped_column(
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
    # GENERATION CAPACITY
    # ========================================================

    rated_power_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    maximum_output_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    minimum_output_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    ramp_up_mw_per_minute: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    ramp_down_mw_per_minute: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # REAL-TIME GENERATION
    # ========================================================

    current_output_mw: Mapped[float | None] = mapped_column(
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

    current_power_factor: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    frequency_hz: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # GENERATION AVAILABILITY
    # ========================================================

    available_capacity_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    reserve_capacity_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    capacity_factor: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    efficiency_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # OPERATIONAL STATUS
    # ========================================================

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=GeneratorStatus.UNKNOWN.value,
        index=True,
    )

    criticality: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=GeneratorCriticality.MEDIUM.value,
        index=True,
    )

    is_online: Mapped[bool] = mapped_column(
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
    # RELIABILITY
    # ========================================================

    health_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    reliability_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    failure_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    historical_failure_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    forced_outage_rate: Mapped[float | None] = mapped_column(
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

    heat_stress_score: Mapped[float | None] = mapped_column(
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
    # MAINTENANCE
    # ========================================================

    installation_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    commissioning_date: Mapped[datetime | None] = mapped_column(
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
            "ix_generators_region_type",
            "region_id",
            "generator_type",
        ),
        Index(
            "ix_generators_plant",
            "plant_id",
        ),
        Index(
            "ix_generators_substation",
            "substation_id",
        ),
        Index(
            "ix_generators_bus",
            "bus_id",
        ),
        Index(
            "ix_generators_status_criticality",
            "status",
            "criticality",
        ),
        Index(
            "ix_generators_monitoring",
            "is_monitored",
            "is_active",
        ),
        Index(
            "ix_generators_location",
            "latitude",
            "longitude",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<Generator("
            f"id='{self.id}', "
            f"name='{self.name}', "
            f"type='{self.generator_type}', "
            f"status='{self.status}', "
            f"output={self.current_output_mw}MW"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Generator",
    "GeneratorType",
    "GeneratorStatus",
    "GeneratorCriticality",
]