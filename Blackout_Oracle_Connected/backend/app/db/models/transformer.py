"""
Blackout Oracle - Transformer Database Model.

Represents power transformers monitored by Blackout Oracle.

Transformer data is used for:

- Real-time monitoring
- Overload detection
- Thermal monitoring
- Equipment-health analysis
- Failure prediction
- Anomaly detection
- Weather-risk analysis
- Blackout-risk calculation
- Cascading-failure analysis
- Simulation
- Maintenance recommendations

IMPORTANT
---------

This model stores monitoring and analytical information.

It does NOT directly control or operate physical transformer
equipment.
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


class TransformerType:
    """
    Type of transformer.
    """

    POWER = "power"
    DISTRIBUTION = "distribution"
    STEP_UP = "step_up"
    STEP_DOWN = "step_down"
    AUTOTRANSFORMER = "autotransformer"
    INTERCONNECTING = "interconnecting"
    AUXILIARY = "auxiliary"
    OTHER = "other"


class TransformerStatus:
    """
    Current operational state of the transformer.
    """

    UNKNOWN = "unknown"
    NORMAL = "normal"
    WARNING = "warning"
    OVERLOADED = "overloaded"
    FAULT = "fault"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"


class TransformerCriticality:
    """
    Operational importance of the transformer.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# TRANSFORMER MODEL
# ============================================================


class Transformer(Base):
    """
    SQLAlchemy model representing a monitored power transformer.
    """

    __tablename__ = "transformers"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"TRF-{uuid4().hex[:12].upper()}"
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

    transformer_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default=TransformerType.POWER,
        index=True,
    )

    # ========================================================
    # LOCATION / GRID RELATION
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

    substation_name: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    asset_id: Mapped[str | None] = mapped_column(
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
    # MANUFACTURER INFORMATION
    # ========================================================

    manufacturer: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    model_number: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    serial_number: Mapped[str | None] = mapped_column(
        String(150),
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
    # TRANSFORMER RATINGS
    # ========================================================

    rated_power_mva: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rated_capacity_mva: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    available_capacity_mva: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # VOLTAGE RATINGS
    # ========================================================

    primary_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    secondary_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    tertiary_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # ELECTRICAL CONFIGURATION
    # ========================================================

    phase_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    frequency_rating_hz: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    vector_group: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    tap_position: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    tap_position_min: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    tap_position_max: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ========================================================
    # COOLING
    # ========================================================

    cooling_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    cooling_stage: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    cooling_system_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # ========================================================
    # INSULATION / OIL
    # ========================================================

    insulation_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    oil_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    oil_level_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    oil_temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    winding_temperature_c: Mapped[
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

    # ========================================================
    # REAL-TIME ELECTRICAL DATA
    # ========================================================

    primary_voltage_kv_actual: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    secondary_voltage_kv_actual: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    primary_current_a: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    secondary_current_a: Mapped[float | None] = mapped_column(
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

    power_factor: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    frequency_hz: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    loading_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        index=True,
    )

    # ========================================================
    # LOADING / OVERLOAD
    # ========================================================

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
    # STATUS
    # ========================================================

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=TransformerStatus.UNKNOWN,
        index=True,
    )

    criticality: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TransformerCriticality.MEDIUM,
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
    # PROTECTION / FAULT INFORMATION
    # ========================================================

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
    # HEALTH
    # ========================================================

    health_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        index=True,
    )

    thermal_health_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    insulation_health_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    oil_health_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    mechanical_health_score: Mapped[
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

    failure_probability: Mapped[float | None] = mapped_column(
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

    external_transformer_id: Mapped[
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
            "ix_transformers_region_status",
            "region_id",
            "status",
        ),
        Index(
            "ix_transformers_substation_status",
            "substation_id",
            "status",
        ),
        Index(
            "ix_transformers_loading",
            "loading_percent",
            "overloaded",
        ),
        Index(
            "ix_transformers_health_failure",
            "health_score",
            "failure_probability",
        ),
        Index(
            "ix_transformers_risk",
            "risk_score",
            "blackout_probability",
        ),
        Index(
            "ix_transformers_anomaly",
            "anomaly_detected",
            "anomaly_score",
        ),
        Index(
            "ix_transformers_fault",
            "fault_detected",
            "protection_trip",
        ),
        Index(
            "ix_transformers_outage",
            "outage_active",
            "status",
        ),
        Index(
            "ix_transformers_telemetry",
            "telemetry_asset_id",
            "last_telemetry_at",
        ),
        Index(
            "ix_transformers_maintenance",
            "maintenance_required",
            "next_maintenance_at",
        ),
        Index(
            "ix_transformers_location",
            "latitude",
            "longitude",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<Transformer("
            f"id='{self.id}', "
            f"name='{self.name}', "
            f"type='{self.transformer_type}', "
            f"status='{self.status}', "
            f"loading={self.loading_percent}, "
            f"risk={self.risk_score}"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Transformer",
    "TransformerType",
    "TransformerStatus",
    "TransformerCriticality",
]