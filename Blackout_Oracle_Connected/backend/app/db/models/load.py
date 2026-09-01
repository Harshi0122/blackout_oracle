"""
Blackout Oracle - Load Database Model.

Represents electrical loads and demand points monitored by
Blackout Oracle.

Loads may represent:

- Residential demand
- Commercial demand
- Industrial demand
- Agricultural demand
- Critical infrastructure
- Hospitals
- Data centers
- Public services
- Mixed distribution loads
- Aggregated regional demand

This information can be used by Blackout Oracle for:

- Demand forecasting
- Load anomaly detection
- Peak-demand prediction
- Supply-demand balance analysis
- Overload detection
- Blackout-risk prediction
- Cascade-risk analysis
- Digital-twin simulations

IMPORTANT
---------

This model stores electrical demand information.

It does NOT provide direct control over physical electrical
equipment or customer loads.
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


class LoadType(str, Enum):
    """
    Category of electrical load.
    """

    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    AGRICULTURAL = "agricultural"
    GOVERNMENT = "government"
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    HOSPITAL = "hospital"
    DATA_CENTER = "data_center"
    TRANSPORTATION = "transportation"
    MIXED = "mixed"
    OTHER = "other"


class LoadStatus(str, Enum):
    """
    Current operational state of the load.
    """

    UNKNOWN = "unknown"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    INTERRUPTED = "interrupted"
    DEGRADED = "degraded"
    RESTORED = "restored"


class LoadCriticality(str, Enum):
    """
    Importance of the load to grid reliability and public services.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# LOAD MODEL
# ============================================================


class Load(Base):
    """
    SQLAlchemy model representing an electrical load.
    """

    __tablename__ = "loads"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"LOD-{uuid4().hex[:12].upper()}"
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

    load_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default=LoadType.MIXED.value,
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

    feeder_id: Mapped[str | None] = mapped_column(
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
    # ELECTRICAL CHARACTERISTICS
    # ========================================================

    nominal_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rated_power_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    maximum_demand_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    minimum_demand_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # REAL-TIME DEMAND
    # ========================================================

    current_demand_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

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

    power_factor: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    frequency_hz: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # DEMAND FORECASTING
    # ========================================================

    forecast_demand_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    forecast_horizon_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    forecast_error_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    demand_growth_rate_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # LOAD FACTOR / PEAK INFORMATION
    # ========================================================

    load_factor: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    peak_demand_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    peak_demand_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ========================================================
    # OPERATIONAL STATUS
    # ========================================================

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=LoadStatus.UNKNOWN.value,
        index=True,
    )

    criticality: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=LoadCriticality.MEDIUM.value,
        index=True,
    )

    is_connected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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
    # CRITICAL LOAD INFORMATION
    # ========================================================

    is_critical_load: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    critical_load_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    estimated_customers: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ========================================================
    # RELIABILITY
    # ========================================================

    interruption_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    average_interruption_minutes: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    reliability_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # WEATHER SENSITIVITY
    # ========================================================

    weather_sensitivity_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    temperature_sensitivity_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    flood_exposure_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    storm_exposure_score: Mapped[float | None] = mapped_column(
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
            "ix_loads_region_type",
            "region_id",
            "load_type",
        ),
        Index(
            "ix_loads_substation",
            "substation_id",
        ),
        Index(
            "ix_loads_feeder",
            "feeder_id",
        ),
        Index(
            "ix_loads_bus",
            "bus_id",
        ),
        Index(
            "ix_loads_status_criticality",
            "status",
            "criticality",
        ),
        Index(
            "ix_loads_monitoring",
            "is_monitored",
            "is_active",
        ),
        Index(
            "ix_loads_critical",
            "is_critical_load",
            "status",
        ),
        Index(
            "ix_loads_location",
            "latitude",
            "longitude",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<Load("
            f"id='{self.id}', "
            f"name='{self.name}', "
            f"type='{self.load_type}', "
            f"demand={self.current_demand_mw}MW, "
            f"status='{self.status}'"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Load",
    "LoadType",
    "LoadStatus",
    "LoadCriticality",
]