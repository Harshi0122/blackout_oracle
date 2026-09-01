"""
Blackout Oracle - Region Database Model.

Represents geographical and electrical-grid monitoring regions used by
Blackout Oracle.

A region may represent:

- A city
- A district
- A state
- A grid zone
- A control area
- A distribution area
- A transmission region
- Any other logical monitoring boundary

Regions provide a common geographic reference for:

- Grid assets
- Substations
- Feeders
- Buses
- Generators
- Loads
- Weather observations
- Incidents
- Outages
- Predictions
- Alerts
- Recommendations

IMPORTANT
---------

This model stores geographic and organizational information.

It does NOT provide direct control over electrical-grid equipment.
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


class RegionType:
    """
    Type of region represented by the record.
    """

    CITY = "city"
    DISTRICT = "district"
    STATE = "state"
    COUNTRY = "country"

    GRID_ZONE = "grid_zone"
    CONTROL_AREA = "control_area"
    TRANSMISSION_REGION = "transmission_region"
    DISTRIBUTION_AREA = "distribution_area"

    CUSTOM = "custom"
    OTHER = "other"


class RegionStatus:
    """
    Operational status of a monitored region.
    """

    UNKNOWN = "unknown"
    NORMAL = "normal"
    ELEVATED_RISK = "elevated_risk"
    HIGH_RISK = "high_risk"
    CRITICAL = "critical"
    BLACKOUT = "blackout"
    PARTIAL_BLACKOUT = "partial_blackout"


class RegionCriticality:
    """
    Importance of the region to the monitored electrical network.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# REGION MODEL
# ============================================================


class Region(Base):
    """
    SQLAlchemy model representing a monitored geographical or
    electrical-grid region.
    """

    __tablename__ = "regions"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"REG-{uuid4().hex[:12].upper()}"
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

    code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
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

    region_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default=RegionType.CUSTOM,
        index=True,
    )

    # ========================================================
    # HIERARCHY
    # ========================================================

    parent_region_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    parent_region_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    country_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        index=True,
    )

    state_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )

    district_code: Mapped[str | None] = mapped_column(
        String(50),
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

    center_latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    center_longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    elevation_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    area_sq_km: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # BOUNDARY INFORMATION
    # ========================================================

    boundary_geojson: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    timezone: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ========================================================
    # GRID INFORMATION
    # ========================================================

    grid_operator: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    grid_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    grid_zone_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # ========================================================
    # REGION STATUS
    # ========================================================

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=RegionStatus.UNKNOWN,
        index=True,
    )

    criticality: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RegionCriticality.MEDIUM,
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
    # GRID STATISTICS
    # ========================================================

    asset_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    substation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    feeder_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    generator_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    load_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ========================================================
    # ELECTRICAL STATISTICS
    # ========================================================

    current_demand_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    current_generation_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    available_generation_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    reserve_capacity_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    demand_generation_margin_mw: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # RISK INFORMATION
    # ========================================================

    risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        index=True,
    )

    blackout_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    cascade_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    risk_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # WEATHER RISK
    # ========================================================

    weather_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    flood_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    storm_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    temperature_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # CURRENT IMPACT
    # ========================================================

    active_outage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    active_incident_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    affected_customers: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    lost_load_mw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    # ========================================================
    # POPULATION
    # ========================================================

    population: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    estimated_customers: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ========================================================
    # TELEMETRY
    # ========================================================

    telemetry_source: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    last_telemetry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ========================================================
    # WEATHER DATA
    # ========================================================

    weather_source: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    last_weather_update_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
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
            "ix_regions_type_status",
            "region_type",
            "status",
        ),
        Index(
            "ix_regions_parent",
            "parent_region_id",
        ),
        Index(
            "ix_regions_country_state",
            "country_code",
            "state_code",
        ),
        Index(
            "ix_regions_grid_zone",
            "grid_zone_code",
        ),
        Index(
            "ix_regions_risk",
            "risk_score",
            "blackout_probability",
        ),
        Index(
            "ix_regions_location",
            "latitude",
            "longitude",
        ),
        Index(
            "ix_regions_monitoring",
            "is_monitored",
            "is_active",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<Region("
            f"id='{self.id}', "
            f"name='{self.name}', "
            f"type='{self.region_type}', "
            f"status='{self.status}', "
            f"risk={self.risk_score}"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Region",
    "RegionType",
    "RegionStatus",
    "RegionCriticality",
]