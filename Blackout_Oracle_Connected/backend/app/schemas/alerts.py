"""
Blackout Oracle - Alert Schemas.

Pydantic schemas for creating, updating, filtering, and returning
grid-risk alerts.

These schemas are used by the API layer and incident-management
services. They are deliberately independent of SQLAlchemy models
to keep the API contract separate from the database layer.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# ENUMS
# ============================================================


class AlertSeverity(str, Enum):
    """Severity levels supported by Blackout Oracle."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Lifecycle states for an alert."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class AlertType(str, Enum):
    """Types of grid alerts."""

    ANOMALY = "anomaly"
    OVERLOAD = "overload"
    VOLTAGE = "voltage"
    FREQUENCY = "frequency"
    ASSET_FAILURE = "asset_failure"
    BLACKOUT_RISK = "blackout_risk"
    CASCADE_RISK = "cascade_risk"
    WEATHER = "weather"
    FORECAST = "forecast"
    DATA_QUALITY = "data_quality"
    SYSTEM = "system"


# ============================================================
# BASE ALERT SCHEMA
# ============================================================


class AlertBase(BaseModel):
    """
    Common fields shared by alert creation and response schemas.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Short human-readable alert title.",
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Detailed alert description.",
    )

    alert_type: AlertType = Field(
        ...,
        description="Category of the alert.",
    )

    severity: AlertSeverity = Field(
        ...,
        description="Severity assigned to the alert.",
    )

    status: AlertStatus = Field(
        default=AlertStatus.ACTIVE,
        description="Current alert lifecycle status.",
    )

    risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Associated risk score from 0 to 100.",
    )

    probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Associated risk probability from 0 to 1.",
    )

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence in the alert assessment.",
    )

    substation_id: int | None = Field(
        default=None,
        ge=1,
        description="Associated substation identifier.",
    )

    transformer_id: int | None = Field(
        default=None,
        ge=1,
        description="Associated transformer identifier.",
    )

    transmission_line_id: int | None = Field(
        default=None,
        ge=1,
        description="Associated transmission-line identifier.",
    )

    asset_id: int | None = Field(
        default=None,
        ge=1,
        description="Generic associated asset identifier.",
    )

    region: str | None = Field(
        default=None,
        max_length=255,
        description="Geographical or operational region.",
    )

    source: str | None = Field(
        default=None,
        max_length=255,
        description="System or model that generated the alert.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured alert information.",
    )


# ============================================================
# CREATE
# ============================================================


class AlertCreate(AlertBase):
    """
    Schema used when creating a new alert.
    """

    detected_at: datetime | None = Field(
        default=None,
        description="Time at which the underlying condition was detected.",
    )


# ============================================================
# UPDATE
# ============================================================


class AlertUpdate(BaseModel):
    """
    Schema used when updating an existing alert.

    All fields are optional so that partial updates are possible.
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

    message: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
    )

    severity: AlertSeverity | None = None

    status: AlertStatus | None = None

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

    metadata: dict[str, Any] | None = None


# ============================================================
# ACKNOWLEDGE
# ============================================================


class AlertAcknowledge(BaseModel):
    """
    Schema used when acknowledging an alert.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    acknowledged_by: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Operator or service acknowledging the alert.",
    )

    comment: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional acknowledgement comment.",
    )


# ============================================================
# RESOLVE
# ============================================================


class AlertResolve(BaseModel):
    """
    Schema used when resolving an alert.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    resolved_by: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Operator or service resolving the alert.",
    )

    resolution_note: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional explanation of the resolution.",
    )


# ============================================================
# DISMISS
# ============================================================


class AlertDismiss(BaseModel):
    """
    Schema used when dismissing an alert.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    dismissed_by: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Operator or service dismissing the alert.",
    )

    reason: str | None = Field(
        default=None,
        max_length=2000,
        description="Reason for dismissing the alert.",
    )


# ============================================================
# FILTERS
# ============================================================


class AlertFilter(BaseModel):
    """
    Filters used when querying alerts.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    alert_type: AlertType | None = None

    severity: AlertSeverity | None = None

    status: AlertStatus | None = None

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

    region: str | None = Field(
        default=None,
        max_length=255,
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
# RESPONSE
# ============================================================


class AlertResponse(AlertBase):
    """
    API response schema representing a stored alert.
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

    detected_at: datetime

    acknowledged_at: datetime | None = None

    acknowledged_by: str | None = None

    resolved_at: datetime | None = None

    resolved_by: str | None = None

    dismissed_at: datetime | None = None

    dismissed_by: str | None = None

    created_at: datetime

    updated_at: datetime


# ============================================================
# ALERT LIST RESPONSE
# ============================================================


class AlertListResponse(BaseModel):
    """
    Paginated collection of alerts.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[AlertResponse] = Field(
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
# ALERT SUMMARY
# ============================================================


class AlertSummary(BaseModel):
    """
    Aggregated alert statistics.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    total: int = Field(
        default=0,
        ge=0,
    )

    active: int = Field(
        default=0,
        ge=0,
    )

    acknowledged: int = Field(
        default=0,
        ge=0,
    )

    resolved: int = Field(
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
# ALERT EVENT
# ============================================================


class AlertEvent(BaseModel):
    """
    Lightweight event representation used when publishing an
    alert through an event/notification layer.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    alert_id: int = Field(
        ...,
        ge=1,
    )

    event_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    timestamp: datetime

    severity: AlertSeverity

    status: AlertStatus

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "AlertSeverity",
    "AlertStatus",
    "AlertType",
    "AlertBase",
    "AlertCreate",
    "AlertUpdate",
    "AlertAcknowledge",
    "AlertResolve",
    "AlertDismiss",
    "AlertFilter",
    "AlertResponse",
    "AlertListResponse",
    "AlertSummary",
    "AlertEvent",
]