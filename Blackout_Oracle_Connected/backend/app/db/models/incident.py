"""
Blackout Oracle - Incident Database Model.

Represents real or detected electrical-grid incidents monitored by
Blackout Oracle.

Incidents may include:

- Equipment failures
- Substation failures
- Feeder failures
- Generator outages
- Transmission failures
- Voltage disturbances
- Frequency disturbances
- Overloads
- Weather-related failures
- Flood-related failures
- Cascading failures
- Partial or complete blackouts

The incident model stores the observed event and its lifecycle so that
the prediction, risk, simulation, alert, and AI-agent systems can
reference the same incident.

IMPORTANT
---------

This model records incidents and analysis results.

It does NOT directly control electrical-grid equipment.
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


class IncidentType:
    """
    Categories of electrical-grid incidents.
    """

    EQUIPMENT_FAILURE = "equipment_failure"
    SUBSTATION_FAILURE = "substation_failure"
    TRANSFORMER_FAILURE = "transformer_failure"
    FEEDER_FAILURE = "feeder_failure"
    TRANSMISSION_FAILURE = "transmission_failure"
    GENERATOR_OUTAGE = "generator_outage"

    OVERLOAD = "overload"
    VOLTAGE_DISTURBANCE = "voltage_disturbance"
    FREQUENCY_DISTURBANCE = "frequency_disturbance"

    WEATHER_DAMAGE = "weather_damage"
    FLOOD_DAMAGE = "flood_damage"
    FIRE = "fire"

    CYBER_EVENT = "cyber_event"

    CASCADING_FAILURE = "cascading_failure"
    PARTIAL_BLACKOUT = "partial_blackout"
    COMPLETE_BLACKOUT = "complete_blackout"

    UNKNOWN = "unknown"


class IncidentSeverity:
    """
    Severity classification of an incident.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus:
    """
    Lifecycle state of an incident.
    """

    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    MITIGATING = "mitigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class IncidentSource:
    """
    Source that detected or reported the incident.
    """

    TELEMETRY = "telemetry"
    WEATHER = "weather"
    USER = "user"
    OPERATOR = "operator"
    AI_AGENT = "ai_agent"
    AUTOMATED_RULE = "automated_rule"
    EXTERNAL_API = "external_api"
    SIMULATION = "simulation"
    UNKNOWN = "unknown"


# ============================================================
# INCIDENT MODEL
# ============================================================


class Incident(Base):
    """
    SQLAlchemy model representing a grid incident.
    """

    __tablename__ = "incidents"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"INC-{uuid4().hex[:12].upper()}"
        ),
    )

    # ========================================================
    # INCIDENT CLASSIFICATION
    # ========================================================

    incident_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=IncidentSeverity.MEDIUM,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=IncidentStatus.DETECTED,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=IncidentSource.UNKNOWN,
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
    # AFFECTED GRID ASSET
    # ========================================================

    asset_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    bus_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    feeder_id: Mapped[str | None] = mapped_column(
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
    # ELECTRICAL CONDITIONS
    # ========================================================

    voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    frequency_hz: Mapped[float | None] = mapped_column(
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

    current_a: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    loading_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # IMPACT
    # ========================================================

    affected_customers: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    estimated_load_lost_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    estimated_generation_lost_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    affected_assets_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    affected_regions_count: Mapped[int] = mapped_column(
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

    ai_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ai_root_cause: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ai_reasoning_summary: Mapped[str | None] = mapped_column(
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

    flood_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    temperature_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    storm_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # SIMULATION
    # ========================================================

    simulation_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    simulation_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    simulation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    simulation_result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # MITIGATION
    # ========================================================

    mitigation_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    mitigation_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    recommended_action: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    human_approval_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    approved_by: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    # ========================================================
    # EXTERNAL REFERENCE
    # ========================================================

    external_incident_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    external_source: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        index=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

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
    # ADDITIONAL DATA
    # ========================================================

    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # DATABASE INDEXES
    # ========================================================

    __table_args__ = (
        Index(
            "ix_incidents_region_status",
            "region_id",
            "status",
        ),
        Index(
            "ix_incidents_region_detected",
            "region_id",
            "detected_at",
        ),
        Index(
            "ix_incidents_asset_detected",
            "asset_id",
            "detected_at",
        ),
        Index(
            "ix_incidents_severity_status",
            "severity",
            "status",
        ),
        Index(
            "ix_incidents_type_detected",
            "incident_type",
            "detected_at",
        ),
        Index(
            "ix_incidents_risk",
            "risk_score",
            "blackout_probability",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<Incident("
            f"id='{self.id}', "
            f"type='{self.incident_type}', "
            f"severity='{self.severity}', "
            f"status='{self.status}'"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Incident",
    "IncidentType",
    "IncidentSeverity",
    "IncidentStatus",
    "IncidentSource",
]