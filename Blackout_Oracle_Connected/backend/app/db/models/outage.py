"""
Blackout Oracle - Outage Database Model.

Represents electrical power outages detected or recorded by
Blackout Oracle.

An outage may be associated with:

- A substation
- A feeder
- A bus
- A generator
- A transmission asset
- A geographic region
- A larger grid incident

The outage model stores:

- Outage classification
- Affected infrastructure
- Affected customers
- Lost load
- Start and restoration times
- Duration
- Cause information
- Weather contribution
- Risk information
- Detection and restoration information

IMPORTANT
---------

This model records outage information.

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


class OutageType:
    """
    Categories of power outages.
    """

    PLANNED = "planned"
    UNPLANNED = "unplanned"
    PARTIAL = "partial"
    COMPLETE = "complete"
    MOMENTARY = "momentary"
    SUSTAINED = "sustained"
    CASCADING = "cascading"
    WEATHER_RELATED = "weather_related"
    UNKNOWN = "unknown"


class OutageStatus:
    """
    Current lifecycle state of an outage.
    """

    DETECTED = "detected"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    RESTORING = "restoring"
    PARTIALLY_RESTORED = "partially_restored"
    RESTORED = "restored"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class OutageCause:
    """
    Possible causes of an outage.
    """

    EQUIPMENT_FAILURE = "equipment_failure"
    TRANSFORMER_FAILURE = "transformer_failure"
    FEEDER_FAILURE = "feeder_failure"
    TRANSMISSION_FAILURE = "transmission_failure"
    GENERATOR_FAILURE = "generator_failure"
    OVERLOAD = "overload"
    VOLTAGE_INSTABILITY = "voltage_instability"
    FREQUENCY_INSTABILITY = "frequency_instability"

    STORM = "storm"
    HEAVY_RAIN = "heavy_rain"
    FLOOD = "flood"
    LIGHTNING = "lightning"
    EXTREME_HEAT = "extreme_heat"
    FIRE = "fire"
    VEGETATION = "vegetation"

    HUMAN_ERROR = "human_error"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class OutageSeverity:
    """
    Severity of the outage.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# OUTAGE MODEL
# ============================================================


class Outage(Base):
    """
    SQLAlchemy model representing an electrical power outage.
    """

    __tablename__ = "outages"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"OUT-{uuid4().hex[:12].upper()}"
        ),
    )

    # ========================================================
    # OUTAGE CLASSIFICATION
    # ========================================================

    outage_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=OutageType.UNPLANNED,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=OutageStatus.DETECTED,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=OutageSeverity.MEDIUM,
        index=True,
    )

    cause: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default=OutageCause.UNKNOWN,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # LOCATION
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

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # AFFECTED GRID INFRASTRUCTURE
    # ========================================================

    asset_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
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

    generator_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # ========================================================
    # ELECTRICAL IMPACT
    # ========================================================

    lost_load_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    lost_generation_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    affected_capacity_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    remaining_capacity_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    voltage_before_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    voltage_during_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    frequency_before_hz: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    frequency_during_hz: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # CUSTOMER IMPACT
    # ========================================================

    affected_customers: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    critical_customers: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    estimated_population_affected: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ========================================================
    # OUTAGE DURATION
    # ========================================================

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        index=True,
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    restoration_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    restored_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    duration_minutes: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # OUTAGE DETECTION
    # ========================================================

    detection_source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    detection_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    automatically_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    # ========================================================
    # WEATHER CONTRIBUTION
    # ========================================================

    weather_related: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    weather_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rainfall_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    flood_risk_score: Mapped[float | None] = mapped_column(
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
    # BLACKOUT / CASCADE INFORMATION
    # ========================================================

    blackout_related: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    cascade_related: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    cascade_depth: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    parent_outage_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # ========================================================
    # RISK INFORMATION
    # ========================================================

    pre_outage_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    blackout_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    cascade_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    prediction_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
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

    ai_root_cause: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ai_summary: Mapped[str | None] = mapped_column(
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
    # RESTORATION
    # ========================================================

    restoration_plan: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    restoration_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    estimated_restoration_minutes: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # EXTERNAL REFERENCES
    # ========================================================

    external_outage_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    external_source: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    incident_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
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
            "ix_outages_region_status",
            "region_id",
            "status",
        ),
        Index(
            "ix_outages_region_detected",
            "region_id",
            "detected_at",
        ),
        Index(
            "ix_outages_substation",
            "substation_id",
        ),
        Index(
            "ix_outages_feeder",
            "feeder_id",
        ),
        Index(
            "ix_outages_asset",
            "asset_id",
        ),
        Index(
            "ix_outages_severity_status",
            "severity",
            "status",
        ),
        Index(
            "ix_outages_blackout_cascade",
            "blackout_related",
            "cascade_related",
        ),
        Index(
            "ix_outages_weather",
            "weather_related",
            "flood_risk_score",
        ),
        Index(
            "ix_outages_started_restored",
            "started_at",
            "restored_at",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<Outage("
            f"id='{self.id}', "
            f"type='{self.outage_type}', "
            f"status='{self.status}', "
            f"severity='{self.severity}', "
            f"affected_customers="
            f"{self.affected_customers}"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Outage",
    "OutageType",
    "OutageStatus",
    "OutageCause",
    "OutageSeverity",
]