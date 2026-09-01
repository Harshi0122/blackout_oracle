"""
Blackout Oracle - Substation Database Model.

Represents electrical substations monitored by Blackout Oracle.

A substation may contain:

- Transformers
- Busbars
- Circuit breakers
- Disconnectors
- Protection equipment
- Capacitor banks
- Voltage regulation equipment
- Other electrical assets

The substation model provides Blackout Oracle with a high-level view
of the operational condition of a substation.

This information can be used for:

- Real-time monitoring
- Anomaly detection
- Overload detection
- Voltage monitoring
- Frequency monitoring
- Equipment-health analysis
- Weather-risk analysis
- Flood-risk analysis
- Blackout prediction
- Cascading-failure analysis
- Simulation
- Incident detection
- Recommendation generation

IMPORTANT
---------

This model stores monitoring and analytical information.

It does NOT directly control physical electrical-grid equipment.
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


class SubstationType:
    """
    Type of electrical substation.
    """

    TRANSMISSION = "transmission"
    DISTRIBUTION = "distribution"
    GRID = "grid"
    SWITCHING = "switching"
    STEP_UP = "step_up"
    STEP_DOWN = "step_down"
    CONVERTER = "converter"
    MIXED = "mixed"
    OTHER = "other"


class SubstationStatus:
    """
    Current operational status of the substation.
    """

    UNKNOWN = "unknown"
    NORMAL = "normal"
    DEGRADED = "degraded"
    WARNING = "warning"
    FAULT = "fault"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"


class SubstationCriticality:
    """
    Operational importance of the substation.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# SUBSTATION MODEL
# ============================================================


class Substation(Base):
    """
    SQLAlchemy model representing an electrical substation.
    """

    __tablename__ = "substations"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"SUB-{uuid4().hex[:12].upper()}"
        ),
    )

    # ========================================================
    # IDENTIFICATION
    # ========================================================

    name: Mapped[str] = mapped_column(
        String(250),
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

    substation_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default=SubstationType.MIXED,
        index=True,
    )

    # ========================================================
    # REGION
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

    grid_zone: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    grid_operator: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
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

    address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # ========================================================
    # VOLTAGE LEVELS
    # ========================================================

    highest_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    incoming_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    outgoing_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    nominal_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # CAPACITY
    # ========================================================

    installed_capacity_mva: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    available_capacity_mva: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    transformer_capacity_mva: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # TRANSFORMER INFORMATION
    # ========================================================

    transformer_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    operational_transformer_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failed_transformer_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ========================================================
    # NETWORK ELEMENTS
    # ========================================================

    bus_count: Mapped[int] = mapped_column(
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

    connected_load_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ========================================================
    # OPERATIONAL STATUS
    # ========================================================

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=SubstationStatus.UNKNOWN,
        index=True,
    )

    criticality: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SubstationCriticality.MEDIUM,
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
    # REAL-TIME ELECTRICAL DATA
    # ========================================================

    current_demand_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    current_generation_mw: Mapped[float | None] = mapped_column(
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

    frequency_hz: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    power_factor: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    loading_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        index=True,
    )

    # ========================================================
    # VOLTAGE ANALYSIS
    # ========================================================

    voltage_deviation_percent: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    voltage_min_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    voltage_max_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    voltage_violation: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    # ========================================================
    # FREQUENCY ANALYSIS
    # ========================================================

    frequency_deviation_hz: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    frequency_violation: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    # ========================================================
    # LOAD / CAPACITY ANALYSIS
    # ========================================================

    peak_demand_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    reserve_capacity_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    demand_capacity_margin_mw: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    overload_threshold_percent: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    overloaded: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    # ========================================================
    # EQUIPMENT HEALTH
    # ========================================================

    equipment_health_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    transformer_health_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    breaker_health_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    protection_health_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    equipment_fault_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
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

    failure_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    risk_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # WEATHER EXPOSURE
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

    rainfall_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    wind_speed_kmh: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # OUTAGE / INCIDENT INFORMATION
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

    total_outage_count: Mapped[int] = mapped_column(
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
    # BLACKOUT INFORMATION
    # ========================================================

    blackout_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    partial_blackout: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    cascade_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
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

    telemetry_quality_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    telemetry_completeness: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    last_telemetry_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # ========================================================
    # AI ANALYSIS
    # ========================================================

    ai_analyzed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    ai_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ai_root_cause: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ai_model_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    ai_model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ========================================================
    # EXTERNAL INFORMATION
    # ========================================================

    external_substation_id: Mapped[
        str | None
    ] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    external_source: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    # ========================================================
    # ADDITIONAL DATA
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
            "ix_substations_region_status",
            "region_id",
            "status",
        ),
        Index(
            "ix_substations_region_created",
            "region_id",
            "created_at",
        ),
        Index(
            "ix_substations_grid_zone",
            "grid_zone",
        ),
        Index(
            "ix_substations_loading",
            "loading_percent",
            "overloaded",
        ),
        Index(
            "ix_substations_risk",
            "risk_score",
            "blackout_probability",
        ),
        Index(
            "ix_substations_blackout",
            "blackout_active",
            "partial_blackout",
        ),
        Index(
            "ix_substations_weather_risk",
            "weather_risk_score",
            "flood_risk_score",
        ),
        Index(
            "ix_substations_telemetry",
            "telemetry_asset_id",
            "last_telemetry_at",
        ),
        Index(
            "ix_substations_location",
            "latitude",
            "longitude",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<Substation("
            f"id='{self.id}', "
            f"name='{self.name}', "
            f"type='{self.substation_type}', "
            f"status='{self.status}', "
            f"risk={self.risk_score}"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Substation",
    "SubstationType",
    "SubstationStatus",
    "SubstationCriticality",
]