"""
Blackout Oracle - Transmission Line Database Model.

Represents high-voltage transmission lines monitored by Blackout Oracle.

Transmission-line information is used for:

- Real-time grid monitoring
- Power-flow analysis
- Overload detection
- Congestion detection
- Fault detection
- Weather-risk analysis
- Failure prediction
- Blackout-risk calculation
- Cascading-failure analysis
- Contingency analysis
- Grid simulation
- Mitigation planning

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


class TransmissionLineType:
    """
    Type of transmission line.
    """

    OVERHEAD = "overhead"
    UNDERGROUND = "underground"
    SUBMARINE = "submarine"
    MIXED = "mixed"
    OTHER = "other"


class TransmissionLineStatus:
    """
    Current operational state of the transmission line.
    """

    UNKNOWN = "unknown"
    NORMAL = "normal"
    WARNING = "warning"
    OVERLOADED = "overloaded"
    FAULT = "fault"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"


class TransmissionLineCriticality:
    """
    Operational importance of the transmission line.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# TRANSMISSION LINE MODEL
# ============================================================


class TransmissionLine(Base):
    """
    SQLAlchemy model representing a monitored transmission line.
    """

    __tablename__ = "transmission_lines"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"TL-{uuid4().hex[:12].upper()}"
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

    line_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=TransmissionLineType.OVERHEAD,
        index=True,
    )

    # ========================================================
    # GRID RELATION
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
    # ENDPOINTS
    # ========================================================

    from_substation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    from_substation_name: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    to_substation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    to_substation_name: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    from_bus_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    to_bus_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # ========================================================
    # GEOGRAPHICAL INFORMATION
    # ========================================================

    start_latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    start_longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    end_latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    end_longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    corridor_length_km: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # LINE SPECIFICATIONS
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

    thermal_capacity_mva: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    emergency_capacity_mva: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # CONDUCTOR INFORMATION
    # ========================================================

    conductor_type: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    conductor_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    conductor_material: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    circuit_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    tower_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ========================================================
    # INSTALLATION INFORMATION
    # ========================================================

    installation_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    commissioning_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    expected_service_life_years: Mapped[
        int | None
    ] = mapped_column(
        Integer,
        nullable=True,
    )

    # ========================================================
    # ELECTRICAL PARAMETERS
    # ========================================================

    resistance_ohm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    reactance_ohm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    susceptance_us: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    impedance_ohm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    power_factor: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # REAL-TIME POWER FLOW
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

    frequency_hz: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # FROM-END MEASUREMENTS
    # ========================================================

    from_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    from_current_a: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    from_active_power_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    from_reactive_power_mvar: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    from_apparent_power_mva: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # TO-END MEASUREMENTS
    # ========================================================

    to_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    to_current_a: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    to_active_power_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    to_reactive_power_mvar: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    to_apparent_power_mva: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # LOADING
    # ========================================================

    loading_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        index=True,
    )

    from_loading_percent: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    to_loading_percent: Mapped[
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

    emergency_loading_percent: Mapped[
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

    emergency_overload: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    overload_duration_minutes: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # POWER LOSSES
    # ========================================================

    active_power_loss_mw: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    reactive_power_loss_mvar: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # OPERATIONAL STATUS
    # ========================================================

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=TransmissionLineStatus.UNKNOWN,
        index=True,
    )

    criticality: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TransmissionLineCriticality.MEDIUM,
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
    # BREAKER / PROTECTION INFORMATION
    # ========================================================

    breaker_open: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    protection_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    protection_trip: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    fault_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    fault_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    fault_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # LINE HEALTH
    # ========================================================

    health_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        index=True,
    )

    conductor_health_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    tower_health_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    insulation_health_score: Mapped[
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

    age_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # FAILURE PREDICTION
    # ========================================================

    failure_probability: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
        index=True,
    )

    predicted_failure_hours: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    predicted_failure_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
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

    blackout_probability: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    cascade_probability: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    risk_confidence: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # WEATHER EXPOSURE
    # ========================================================

    weather_risk_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    flood_risk_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    storm_risk_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    temperature_risk_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    ambient_temperature_c: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    wind_speed_kmh: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    rainfall_mm: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # ANOMALY DETECTION
    # ========================================================

    anomaly_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    anomaly_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    anomaly_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    anomaly_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # OUTAGE INFORMATION
    # ========================================================

    outage_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    outage_start_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    outage_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # MAINTENANCE
    # ========================================================

    last_maintenance_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    next_maintenance_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    maintenance_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    maintenance_notes: Mapped[str | None] = mapped_column(
        Text,
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

    telemetry_quality_score: Mapped[
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

    ai_failure_explanation: Mapped[
        str | None
    ] = mapped_column(
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

    external_line_id: Mapped[str | None] = mapped_column(
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
            "ix_transmission_lines_region_status",
            "region_id",
            "status",
        ),
        Index(
            "ix_transmission_lines_from_substation",
            "from_substation_id",
        ),
        Index(
            "ix_transmission_lines_to_substation",
            "to_substation_id",
        ),
        Index(
            "ix_transmission_lines_grid_zone",
            "grid_zone",
        ),
        Index(
            "ix_transmission_lines_loading",
            "loading_percent",
            "overloaded",
        ),
        Index(
            "ix_transmission_lines_health_failure",
            "health_score",
            "failure_probability",
        ),
        Index(
            "ix_transmission_lines_risk",
            "risk_score",
            "blackout_probability",
        ),
        Index(
            "ix_transmission_lines_anomaly",
            "anomaly_detected",
            "anomaly_score",
        ),
        Index(
            "ix_transmission_lines_fault",
            "fault_detected",
            "protection_trip",
        ),
        Index(
            "ix_transmission_lines_outage",
            "outage_active",
            "status",
        ),
        Index(
            "ix_transmission_lines_telemetry",
            "telemetry_asset_id",
            "last_telemetry_at",
        ),
        Index(
            "ix_transmission_lines_location",
            "start_latitude",
            "start_longitude",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<TransmissionLine("
            f"id='{self.id}', "
            f"name='{self.name}', "
            f"status='{self.status}', "
            f"loading={self.loading_percent}, "
            f"risk={self.risk_score}"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "TransmissionLine",
    "TransmissionLineType",
    "TransmissionLineStatus",
    "TransmissionLineCriticality",
]