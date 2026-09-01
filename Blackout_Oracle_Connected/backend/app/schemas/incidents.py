"""
Blackout Oracle - Incident Schemas.

Pydantic schemas for grid incidents, including incident creation,
updates, responses, filtering, severity classification, and
incident lifecycle management.

These schemas are intentionally independent of SQLAlchemy models
so they can be safely used by API, incident-management, risk,
simulation, and ML layers.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# ENUMS
# ============================================================


class IncidentSeverity(str, Enum):
    """Severity classification for grid incidents."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Lifecycle status of a grid incident."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"
    DISMISSED = "dismissed"


class IncidentType(str, Enum):
    """Types of incidents monitored by Blackout Oracle."""

    POWER_OUTAGE = "power_outage"
    EQUIPMENT_FAILURE = "equipment_failure"
    TRANSFORMER_FAILURE = "transformer_failure"
    TRANSMISSION_LINE_FAILURE = "transmission_line_failure"
    SUBSTATION_FAILURE = "substation_failure"
    OVERLOAD = "overload"
    VOLTAGE_EVENT = "voltage_event"
    FREQUENCY_EVENT = "frequency_event"
    CASCADING_FAILURE = "cascading_failure"
    BLACKOUT = "blackout"
    PARTIAL_BLACKOUT = "partial_blackout"
    WEATHER_RELATED = "weather_related"
    FIRE = "fire"
    DATA_ANOMALY = "data_anomaly"
    UNKNOWN = "unknown"


class IncidentPriority(str, Enum):
    """Operational priority assigned to an incident."""

    P1 = "p1"
    P2 = "p2"
    P3 = "p3"
    P4 = "p4"


# ============================================================
# BASE INCIDENT
# ============================================================


class IncidentBase(BaseModel):
    """
    Common fields shared by incident schemas.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Short human-readable incident title.",
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Detailed description of the incident.",
    )

    incident_type: IncidentType = Field(
        ...,
        description="Type of grid incident.",
    )

    severity: IncidentSeverity = Field(
        default=IncidentSeverity.MEDIUM,
        description="Incident severity.",
    )

    priority: IncidentPriority = Field(
        default=IncidentPriority.P3,
        description="Operational incident priority.",
    )

    status: IncidentStatus = Field(
        default=IncidentStatus.OPEN,
        description="Current incident lifecycle status.",
    )

    risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Associated grid-risk score.",
    )

    probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Predicted probability of the incident.",
    )

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence in the incident assessment.",
    )

    region: str | None = Field(
        default=None,
        max_length=255,
        description="Geographical or operational region.",
    )

    state: str | None = Field(
        default=None,
        max_length=100,
        description="State containing the affected infrastructure.",
    )

    district: str | None = Field(
        default=None,
        max_length=100,
        description="District containing the affected infrastructure.",
    )

    latitude: float | None = Field(
        default=None,
        ge=-90.0,
        le=90.0,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180.0,
        le=180.0,
    )

    substation_id: int | None = Field(
        default=None,
        ge=1,
        description="Affected substation identifier.",
    )

    transformer_id: int | None = Field(
        default=None,
        ge=1,
        description="Affected transformer identifier.",
    )

    transmission_line_id: int | None = Field(
        default=None,
        ge=1,
        description="Affected transmission-line identifier.",
    )

    asset_id: int | None = Field(
        default=None,
        ge=1,
        description="Generic affected asset identifier.",
    )

    source: str | None = Field(
        default=None,
        max_length=255,
        description="System or source that detected the incident.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured incident information.",
    )


# ============================================================
# INCIDENT CREATE
# ============================================================


class IncidentCreate(IncidentBase):
    """
    Schema used when creating a new incident.
    """

    detected_at: datetime | None = Field(
        default=None,
        description="Time at which the incident was detected.",
    )

    started_at: datetime | None = Field(
        default=None,
        description="Estimated or known incident start time.",
    )

    external_id: str | None = Field(
        default=None,
        max_length=255,
        description="Identifier from an external grid system.",
    )


# ============================================================
# INCIDENT UPDATE
# ============================================================


class IncidentUpdate(BaseModel):
    """
    Schema used for partial incident updates.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    severity: IncidentSeverity | None = None

    priority: IncidentPriority | None = None

    status: IncidentStatus | None = None

    risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    region: str | None = Field(
        default=None,
        max_length=255,
    )

    state: str | None = Field(
        default=None,
        max_length=100,
    )

    district: str | None = Field(
        default=None,
        max_length=100,
    )

    latitude: float | None = Field(
        default=None,
        ge=-90.0,
        le=90.0,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180.0,
        le=180.0,
    )

    substation_id: int | None = Field(
        default=None,
        ge=1,
    )

    transformer_id: int | None = Field(
        default=None,
        ge=1,
    )

    transmission_line_id: int | None = Field(
        default=None,
        ge=1,
    )

    asset_id: int | None = Field(
        default=None,
        ge=1,
    )

    metadata: dict[str, Any] | None = None


# ============================================================
# INCIDENT STATUS UPDATE
# ============================================================


class IncidentStatusUpdate(BaseModel):
    """
    Schema used to change the lifecycle status of an incident.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    status: IncidentStatus

    updated_by: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    comment: str | None = Field(
        default=None,
        max_length=2000,
    )


# ============================================================
# INCIDENT ACKNOWLEDGEMENT
# ============================================================


class IncidentAcknowledge(BaseModel):
    """
    Schema used when an operator acknowledges an incident.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    acknowledged_by: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    comment: str | None = Field(
        default=None,
        max_length=2000,
    )


# ============================================================
# INCIDENT RESOLUTION
# ============================================================


class IncidentResolve(BaseModel):
    """
    Schema used to resolve an incident.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    resolved_by: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    resolution_note: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )

    root_cause: str | None = Field(
        default=None,
        max_length=5000,
    )

    corrective_action: str | None = Field(
        default=None,
        max_length=5000,
    )


# ============================================================
# INCIDENT DISMISSAL
# ============================================================


class IncidentDismiss(BaseModel):
    """
    Schema used when dismissing an incident.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    dismissed_by: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    reason: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )


# ============================================================
# INCIDENT RESPONSE
# ============================================================


class IncidentResponse(IncidentBase):
    """
    API response representing a stored incident.
    """

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        extra="forbid",
    )

    id: int = Field(
        ...,
        ge=1,
    )

    external_id: str | None = None

    detected_at: datetime

    started_at: datetime | None = None

    acknowledged_at: datetime | None = None

    acknowledged_by: str | None = None

    contained_at: datetime | None = None

    contained_by: str | None = None

    resolved_at: datetime | None = None

    resolved_by: str | None = None

    resolution_note: str | None = None

    root_cause: str | None = None

    corrective_action: str | None = None

    dismissed_at: datetime | None = None

    dismissed_by: str | None = None

    dismissal_reason: str | None = None

    created_at: datetime

    updated_at: datetime


# ============================================================
# INCIDENT FILTER
# ============================================================


class IncidentFilter(BaseModel):
    """
    Filters for querying incidents.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    incident_type: IncidentType | None = None

    severity: IncidentSeverity | None = None

    priority: IncidentPriority | None = None

    status: IncidentStatus | None = None

    region: str | None = Field(
        default=None,
        max_length=255,
    )

    state: str | None = Field(
        default=None,
        max_length=100,
    )

    district: str | None = Field(
        default=None,
        max_length=100,
    )

    substation_id: int | None = Field(
        default=None,
        ge=1,
    )

    transformer_id: int | None = Field(
        default=None,
        ge=1,
    )

    transmission_line_id: int | None = Field(
        default=None,
        ge=1,
    )

    asset_id: int | None = Field(
        default=None,
        ge=1,
    )

    source: str | None = Field(
        default=None,
        max_length=255,
    )

    min_risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    max_risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    start_time: datetime | None = None

    end_time: datetime | None = None

    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# INCIDENT LIST RESPONSE
# ============================================================


class IncidentListResponse(BaseModel):
    """
    Paginated collection of incidents.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[IncidentResponse] = Field(
        default_factory=list,
    )

    total: int = Field(
        default=0,
        ge=0,
    )

    limit: int = Field(
        default=100,
        ge=1,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# INCIDENT SUMMARY
# ============================================================


class IncidentSummary(BaseModel):
    """
    Aggregated incident statistics.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    total: int = Field(
        default=0,
        ge=0,
    )

    open: int = Field(
        default=0,
        ge=0,
    )

    investigating: int = Field(
        default=0,
        ge=0,
    )

    contained: int = Field(
        default=0,
        ge=0,
    )

    resolved: int = Field(
        default=0,
        ge=0,
    )

    closed: int = Field(
        default=0,
        ge=0,
    )

    dismissed: int = Field(
        default=0,
        ge=0,
    )

    info: int = Field(
        default=0,
        ge=0,
    )

    low: int = Field(
        default=0,
        ge=0,
    )

    medium: int = Field(
        default=0,
        ge=0,
    )

    high: int = Field(
        default=0,
        ge=0,
    )

    critical: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# INCIDENT EVENT
# ============================================================


class IncidentEvent(BaseModel):
    """
    Event representation for incident notifications and
    event-driven processing.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    incident_id: int = Field(
        ...,
        ge=1,
    )

    event_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    timestamp: datetime

    incident_type: IncidentType

    severity: IncidentSeverity

    status: IncidentStatus

    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# INCIDENT IMPACT
# ============================================================


class IncidentImpact(BaseModel):
    """
    Estimated impact of an incident on the electrical grid.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    affected_assets: int = Field(
        default=0,
        ge=0,
    )

    affected_substations: int = Field(
        default=0,
        ge=0,
    )

    affected_transmission_lines: int = Field(
        default=0,
        ge=0,
    )

    affected_customers: int | None = Field(
        default=None,
        ge=0,
    )

    affected_load_mw: float | None = Field(
        default=None,
        ge=0.0,
    )

    estimated_duration_minutes: float | None = Field(
        default=None,
        ge=0.0,
    )

    estimated_economic_impact: float | None = Field(
        default=None,
        ge=0.0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# INCIDENT ROOT CAUSE
# ============================================================


class IncidentRootCause(BaseModel):
    """
    Structured root-cause assessment for an incident.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    category: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    description: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    contributing_factors: list[str] = Field(
        default_factory=list,
    )

    evidence: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "IncidentSeverity",
    "IncidentStatus",
    "IncidentType",
    "IncidentPriority",
    "IncidentBase",
    "IncidentCreate",
    "IncidentUpdate",
    "IncidentStatusUpdate",
    "IncidentAcknowledge",
    "IncidentResolve",
    "IncidentDismiss",
    "IncidentResponse",
    "IncidentFilter",
    "IncidentListResponse",
    "IncidentSummary",
    "IncidentEvent",
    "IncidentImpact",
    "IncidentRootCause",
]