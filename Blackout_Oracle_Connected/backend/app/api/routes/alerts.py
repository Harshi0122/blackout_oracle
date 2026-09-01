"""
Blackout Oracle - Alert API Routes.

This module exposes HTTP endpoints for creating, listing, retrieving,
acknowledging, and resolving Blackout Oracle alerts.

Important:
    These endpoints are part of a decision-support system.

    They do NOT:
        - Control electrical equipment
        - Operate breakers
        - Modify SCADA
        - Send commands to substations
        - Execute grid-control actions

Alerts communicate detected or predicted risks to authorized users.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)


# ============================================================
# ENUMS
# ============================================================


class AlertLevel(str, Enum):
    """Severity level of a Blackout Oracle alert."""

    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"
    BLACK = "black"


class AlertStatus(str, Enum):
    """Lifecycle status of an alert."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================


class AlertCreate(BaseModel):
    """
    Request model for creating an alert.

    In the production architecture, alerts should normally be generated
    by the risk/incident service rather than manually created by arbitrary
    clients.
    """

    incident_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Blackout Oracle incident identifier.",
    )

    region_id: str | None = Field(
        default=None,
        max_length=100,
        description="Grid region identifier.",
    )

    region_name: str | None = Field(
        default=None,
        max_length=200,
        description="Human-readable region name.",
    )

    level: AlertLevel = Field(
        ...,
        description="Alert severity level.",
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Short alert title.",
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Human-readable alert message.",
    )

    risk_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Estimated blackout/grid risk score.",
    )

    confidence: float = Field(
        ...,
        ge=0,
        le=100,
        description="Model confidence associated with the alert.",
    )

    warning_horizon_minutes: float | None = Field(
        default=None,
        ge=0,
        description="Estimated warning horizon in minutes.",
    )

    affected_assets: list[str] = Field(
        default_factory=list,
        description="Assets potentially affected by the incident.",
    )

    contributing_factors: list[str] = Field(
        default_factory=list,
        description="Factors contributing to the alert.",
    )

    recommendation: dict[str, Any] | None = Field(
        default=None,
        description="Verified recommendation associated with the alert.",
    )

    data_quality: str | None = Field(
        default=None,
        max_length=100,
        description="Description of the quality/freshness of input data.",
    )

    requires_human_review: bool = Field(
        default=True,
        description="Whether human review is required.",
    )


class AlertResponse(BaseModel):
    """Response model representing an alert."""

    id: str

    incident_id: str

    region_id: str | None = None
    region_name: str | None = None

    level: AlertLevel

    status: AlertStatus

    title: str
    message: str

    risk_score: float
    confidence: float

    warning_horizon_minutes: float | None = None

    affected_assets: list[str] = Field(
        default_factory=list
    )

    contributing_factors: list[str] = Field(
        default_factory=list
    )

    recommendation: dict[str, Any] | None = None

    data_quality: str | None = None

    requires_human_review: bool = True

    created_at: datetime

    acknowledged_at: datetime | None = None

    resolved_at: datetime | None = None


class AlertAcknowledgeRequest(BaseModel):
    """Request model for acknowledging an alert."""

    acknowledged_by: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Identifier of the authorized reviewer.",
    )

    note: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional acknowledgement note.",
    )


class AlertResolveRequest(BaseModel):
    """Request model for resolving an alert."""

    resolved_by: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Identifier of the authorized reviewer.",
    )

    note: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional resolution note.",
    )


# ============================================================
# TEMPORARY DEVELOPMENT STORE
# ============================================================

# IMPORTANT:
# This in-memory store is only for early development.
#
# It will eventually be replaced by the PostgreSQL/TimescaleDB persistence
# layer.

_ALERTS: dict[str, AlertResponse] = {}


# ============================================================
# CREATE ALERT
# ============================================================


@router.post(
    "",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_alert(
    alert: AlertCreate,
) -> AlertResponse:
    """
    Create a new Blackout Oracle alert.

    This endpoint currently stores alerts in memory.

    Production implementation should:
        1. Validate the incident.
        2. Validate risk/confidence.
        3. Run the alert policy.
        4. Persist the alert.
        5. Create an audit record.
        6. Dispatch notifications through an alert service.

    No electrical control operation occurs here.
    """

    alert_id = f"ALT-{uuid4().hex[:12].upper()}"

    created_at = datetime.now(timezone.utc)

    response = AlertResponse(
        id=alert_id,
        incident_id=alert.incident_id,
        region_id=alert.region_id,
        region_name=alert.region_name,
        level=alert.level,
        status=AlertStatus.ACTIVE,
        title=alert.title,
        message=alert.message,
        risk_score=alert.risk_score,
        confidence=alert.confidence,
        warning_horizon_minutes=alert.warning_horizon_minutes,
        affected_assets=alert.affected_assets,
        contributing_factors=alert.contributing_factors,
        recommendation=alert.recommendation,
        data_quality=alert.data_quality,
        requires_human_review=alert.requires_human_review,
        created_at=created_at,
    )

    _ALERTS[alert_id] = response

    return response


# ============================================================
# LIST ALERTS
# ============================================================


@router.get(
    "",
    response_model=list[AlertResponse],
)
async def list_alerts(
    level: AlertLevel | None = Query(
        default=None,
        description="Filter by alert level.",
    ),
    alert_status: AlertStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by alert status.",
    ),
    incident_id: str | None = Query(
        default=None,
        description="Filter by incident ID.",
    ),
    region_id: str | None = Query(
        default=None,
        description="Filter by region ID.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of alerts to return.",
    ),
) -> list[AlertResponse]:
    """
    Return alerts matching the supplied filters.

    Results are ordered newest first.
    """

    alerts = list(_ALERTS.values())

    if level is not None:
        alerts = [
            alert
            for alert in alerts
            if alert.level == level
        ]

    if alert_status is not None:
        alerts = [
            alert
            for alert in alerts
            if alert.status == alert_status
        ]

    if incident_id is not None:
        alerts = [
            alert
            for alert in alerts
            if alert.incident_id == incident_id
        ]

    if region_id is not None:
        alerts = [
            alert
            for alert in alerts
            if alert.region_id == region_id
        ]

    alerts.sort(
        key=lambda alert: alert.created_at,
        reverse=True,
    )

    return alerts[:limit]


# ============================================================
# GET ALERT
# ============================================================


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
)
async def get_alert(
    alert_id: str,
) -> AlertResponse:
    """
    Retrieve a single alert by ID.
    """

    alert = _ALERTS.get(alert_id)

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' was not found.",
        )

    return alert


# ============================================================
# ACKNOWLEDGE ALERT
# ============================================================


@router.post(
    "/{alert_id}/acknowledge",
    response_model=AlertResponse,
)
async def acknowledge_alert(
    alert_id: str,
    request: AlertAcknowledgeRequest,
) -> AlertResponse:
    """
    Acknowledge an active alert.

    This records human acknowledgement only.

    It does NOT authorize or perform any electrical-grid operation.
    """

    alert = _ALERTS.get(alert_id)

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' was not found.",
        )

    if alert.status == AlertStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A resolved alert cannot be acknowledged.",
        )

    if alert.status == AlertStatus.DISMISSED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A dismissed alert cannot be acknowledged.",
        )

    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_at = datetime.now(timezone.utc)

    return alert


# ============================================================
# RESOLVE ALERT
# ============================================================


@router.post(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
)
async def resolve_alert(
    alert_id: str,
    request: AlertResolveRequest,
) -> AlertResponse:
    """
    Resolve an alert after human review.

    Resolution records the lifecycle state of the alert.
    It does not execute any grid-control operation.
    """

    alert = _ALERTS.get(alert_id)

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' was not found.",
        )

    if alert.status == AlertStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Alert is already resolved.",
        )

    alert.status = AlertStatus.RESOLVED
    alert.resolved_at = datetime.now(timezone.utc)

    return alert


# ============================================================
# DISMISS ALERT
# ============================================================


@router.post(
    "/{alert_id}/dismiss",
    response_model=AlertResponse,
)
async def dismiss_alert(
    alert_id: str,
) -> AlertResponse:
    """
    Dismiss an alert.

    This should eventually require authenticated/authorized human access.
    """

    alert = _ALERTS.get(alert_id)

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' was not found.",
        )

    if alert.status == AlertStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A resolved alert cannot be dismissed.",
        )

    alert.status = AlertStatus.DISMISSED

    return alert


# ============================================================
# ALERT SUMMARY
# ============================================================


@router.get(
    "/summary/counts",
    response_model=dict[str, int],
)
async def alert_summary() -> dict[str, int]:
    """
    Return a basic alert-count summary.

    This endpoint is useful for the future frontend dashboard.
    """

    summary = {
        "total": len(_ALERTS),
        "active": 0,
        "acknowledged": 0,
        "resolved": 0,
        "dismissed": 0,
        "critical": 0,
        "high": 0,
    }

    for alert in _ALERTS.values():
        summary[alert.status.value] += 1

        if alert.level == AlertLevel.BLACK:
            summary["critical"] += 1

        elif alert.level == AlertLevel.RED:
            summary["high"] += 1

    return summary


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "router",
    "AlertLevel",
    "AlertStatus",
    "AlertCreate",
    "AlertResponse",
    "AlertAcknowledgeRequest",
    "AlertResolveRequest",
]