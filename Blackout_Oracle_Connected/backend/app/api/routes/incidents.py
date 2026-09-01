"""
Blackout Oracle - Incident API Routes.

This module exposes HTTP endpoints for creating, retrieving, updating,
listing, and resolving Blackout Oracle grid incidents.

An incident represents a potentially important grid event such as:

- Suspected equipment failure
- Abnormal load condition
- Transformer overload
- Transmission-line issue
- Severe weather impact
- Flood-related infrastructure risk
- Grid instability
- Predicted blackout
- Predicted cascading failure
- Confirmed outage

IMPORTANT
---------

This API manages Blackout Oracle's internal incident records.

It does NOT:

- Control electrical equipment.
- Operate breakers.
- Modify SCADA.
- Change substation configuration.
- Send commands to real infrastructure.

Operational decisions remain under authorized human control.
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
    prefix="/incidents",
    tags=["Incidents"],
)


# ============================================================
# ENUMS
# ============================================================


class IncidentType(str, Enum):
    """Types of incidents recognized by Blackout Oracle."""

    UNKNOWN = "unknown"
    EQUIPMENT_FAILURE = "equipment_failure"
    TRANSFORMER_OVERLOAD = "transformer_overload"
    TRANSMISSION_FAILURE = "transmission_failure"
    FEEDER_FAILURE = "feeder_failure"
    GENERATION_SHORTAGE = "generation_shortage"
    DEMAND_SURGE = "demand_surge"
    VOLTAGE_ANOMALY = "voltage_anomaly"
    FREQUENCY_ANOMALY = "frequency_anomaly"
    WEATHER_EVENT = "weather_event"
    FLOOD_RISK = "flood_risk"
    GRID_INSTABILITY = "grid_instability"
    CASCADING_FAILURE = "cascading_failure"
    PREDICTED_BLACKOUT = "predicted_blackout"
    CONFIRMED_OUTAGE = "confirmed_outage"


class IncidentSeverity(str, Enum):
    """Severity classification for an incident."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Lifecycle status of an incident."""

    DETECTED = "detected"
    INVESTIGATING = "investigating"
    PREDICTED = "predicted"
    MITIGATION_PENDING = "mitigation_pending"
    HUMAN_REVIEW = "human_review"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    FAILED = "failed"


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================


class IncidentCreate(BaseModel):
    """Request model for creating an incident."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Short incident title.",
    )

    description: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Detailed description of the incident.",
    )

    incident_type: IncidentType = Field(
        default=IncidentType.UNKNOWN,
        description="Type of incident.",
    )

    severity: IncidentSeverity = Field(
        default=IncidentSeverity.LOW,
        description="Incident severity.",
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

    affected_asset_ids: list[str] = Field(
        default_factory=list,
        description="IDs of potentially affected assets.",
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    risk_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Current estimated blackout risk.",
    )

    confidence: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Prediction confidence.",
    )

    warning_horizon_minutes: float | None = Field(
        default=None,
        ge=0,
        description="Estimated warning horizon.",
    )

    contributing_factors: list[str] = Field(
        default_factory=list,
        description="Factors contributing to the incident.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional incident metadata.",
    )


class IncidentUpdate(BaseModel):
    """Request model for updating an incident."""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        min_length=1,
        max_length=5000,
    )

    incident_type: IncidentType | None = None

    severity: IncidentSeverity | None = None

    status: IncidentStatus | None = None

    region_id: str | None = None

    region_name: str | None = None

    affected_asset_ids: list[str] | None = None

    risk_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    confidence: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    warning_horizon_minutes: float | None = Field(
        default=None,
        ge=0,
    )

    contributing_factors: list[str] | None = None

    metadata: dict[str, Any] | None = None


class IncidentResponse(BaseModel):
    """Response model representing an incident."""

    id: str

    title: str

    description: str

    incident_type: IncidentType

    severity: IncidentSeverity

    status: IncidentStatus

    region_id: str | None = None

    region_name: str | None = None

    affected_asset_ids: list[str] = Field(
        default_factory=list
    )

    latitude: float | None = None

    longitude: float | None = None

    risk_score: float | None = None

    confidence: float | None = None

    warning_horizon_minutes: float | None = None

    contributing_factors: list[str] = Field(
        default_factory=list
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    created_at: datetime

    updated_at: datetime

    resolved_at: datetime | None = None


class IncidentResolveRequest(BaseModel):
    """Request model for resolving an incident."""

    resolved_by: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Authorized person resolving the incident.",
    )

    resolution_note: str | None = Field(
        default=None,
        max_length=5000,
        description="Explanation of how the incident was resolved.",
    )

    resolution_type: str = Field(
        default="resolved",
        max_length=100,
        description="Resolution classification.",
    )


# ============================================================
# DEVELOPMENT STORE
# ============================================================

# Temporary in-memory store.
#
# Production implementation will use PostgreSQL/TimescaleDB through
# the repository/service layer.

_INCIDENTS: dict[str, IncidentResponse] = {}


# ============================================================
# CREATE INCIDENT
# ============================================================


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_incident(
    incident: IncidentCreate,
) -> IncidentResponse:
    """
    Create a new Blackout Oracle incident.

    This creates an internal incident record.

    In the production system, incidents will normally be created by
    the detection/risk pipeline rather than directly by the frontend.
    """

    incident_id = (
        f"INC-{uuid4().hex[:12].upper()}"
    )

    now = datetime.now(timezone.utc)

    response = IncidentResponse(
        id=incident_id,
        title=incident.title,
        description=incident.description,
        incident_type=incident.incident_type,
        severity=incident.severity,
        status=IncidentStatus.DETECTED,
        region_id=incident.region_id,
        region_name=incident.region_name,
        affected_asset_ids=incident.affected_asset_ids,
        latitude=incident.latitude,
        longitude=incident.longitude,
        risk_score=incident.risk_score,
        confidence=incident.confidence,
        warning_horizon_minutes=incident.warning_horizon_minutes,
        contributing_factors=incident.contributing_factors,
        metadata=incident.metadata,
        created_at=now,
        updated_at=now,
    )

    _INCIDENTS[incident_id] = response

    return response


# ============================================================
# LIST INCIDENTS
# ============================================================


@router.get(
    "",
    response_model=list[IncidentResponse],
)
async def list_incidents(
    incident_status: IncidentStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by incident status.",
    ),
    severity: IncidentSeverity | None = Query(
        default=None,
        description="Filter by severity.",
    ),
    incident_type: IncidentType | None = Query(
        default=None,
        description="Filter by incident type.",
    ),
    region_id: str | None = Query(
        default=None,
        description="Filter by grid region.",
    ),
    active_only: bool = Query(
        default=False,
        description="Return only unresolved incidents.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of incidents.",
    ),
) -> list[IncidentResponse]:
    """
    List incidents using optional filters.
    """

    incidents = list(
        _INCIDENTS.values()
    )

    if incident_status is not None:
        incidents = [
            incident
            for incident in incidents
            if incident.status == incident_status
        ]

    if severity is not None:
        incidents = [
            incident
            for incident in incidents
            if incident.severity == severity
        ]

    if incident_type is not None:
        incidents = [
            incident
            for incident in incidents
            if incident.incident_type == incident_type
        ]

    if region_id is not None:
        incidents = [
            incident
            for incident in incidents
            if incident.region_id == region_id
        ]

    if active_only:
        incidents = [
            incident
            for incident in incidents
            if incident.status
            not in {
                IncidentStatus.RESOLVED,
                IncidentStatus.FALSE_POSITIVE,
            }
        ]

    incidents.sort(
        key=lambda incident: incident.updated_at,
        reverse=True,
    )

    return incidents[:limit]


# ============================================================
# GET INCIDENT
# ============================================================


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
)
async def get_incident(
    incident_id: str,
) -> IncidentResponse:
    """
    Retrieve one incident by ID.
    """

    incident = _INCIDENTS.get(
        incident_id
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Incident '{incident_id}' was not found."
            ),
        )

    return incident


# ============================================================
# UPDATE INCIDENT
# ============================================================


@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
)
async def update_incident(
    incident_id: str,
    update: IncidentUpdate,
) -> IncidentResponse:
    """
    Update an internal incident record.

    In production, status transitions should be validated by a dedicated
    incident-management service.
    """

    incident = _INCIDENTS.get(
        incident_id
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Incident '{incident_id}' was not found."
            ),
        )

    update_data = update.model_dump(
        exclude_unset=True
    )

    for field_name, value in update_data.items():
        setattr(
            incident,
            field_name,
            value,
        )

    incident.updated_at = (
        datetime.now(timezone.utc)
    )

    if incident.status == IncidentStatus.RESOLVED:
        if incident.resolved_at is None:
            incident.resolved_at = (
                datetime.now(timezone.utc)
            )
    else:
        incident.resolved_at = None

    return incident


# ============================================================
# RESOLVE INCIDENT
# ============================================================


@router.post(
    "/{incident_id}/resolve",
    response_model=IncidentResponse,
)
async def resolve_incident(
    incident_id: str,
    request: IncidentResolveRequest,
) -> IncidentResponse:
    """
    Resolve an incident after human review.

    This changes the internal incident lifecycle only.
    It does not operate electrical infrastructure.
    """

    incident = _INCIDENTS.get(
        incident_id
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Incident '{incident_id}' was not found."
            ),
        )

    if incident.status == IncidentStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Incident is already resolved.",
        )

    now = datetime.now(timezone.utc)

    incident.status = IncidentStatus.RESOLVED
    incident.resolved_at = now
    incident.updated_at = now

    incident.metadata[
        "resolution"
    ] = {
        "resolved_by": request.resolved_by,
        "resolution_note": request.resolution_note,
        "resolution_type": request.resolution_type,
        "resolved_at": now.isoformat(),
    }

    return incident


# ============================================================
# MARK FALSE POSITIVE
# ============================================================


@router.post(
    "/{incident_id}/false-positive",
    response_model=IncidentResponse,
)
async def mark_false_positive(
    incident_id: str,
) -> IncidentResponse:
    """
    Mark an incident as a false positive.

    Useful for improving the prediction system and evaluating
    model performance.
    """

    incident = _INCIDENTS.get(
        incident_id
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Incident '{incident_id}' was not found."
            ),
        )

    if incident.status == IncidentStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A resolved incident cannot be marked as a false positive."
            ),
        )

    incident.status = (
        IncidentStatus.FALSE_POSITIVE
    )

    incident.updated_at = (
        datetime.now(timezone.utc)
    )

    return incident


# ============================================================
# INCIDENT STATUS
# ============================================================


@router.get(
    "/{incident_id}/status",
    response_model=dict[str, Any],
)
async def get_incident_status(
    incident_id: str,
) -> dict[str, Any]:
    """
    Return a compact status representation for an incident.
    """

    incident = _INCIDENTS.get(
        incident_id
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Incident '{incident_id}' was not found."
            ),
        )

    return {
        "incident_id": incident.id,
        "status": incident.status.value,
        "severity": incident.severity.value,
        "risk_score": incident.risk_score,
        "confidence": incident.confidence,
        "warning_horizon_minutes": (
            incident.warning_horizon_minutes
        ),
        "updated_at": incident.updated_at.isoformat(),
    }


# ============================================================
# INCIDENT TIMELINE
# ============================================================


@router.get(
    "/{incident_id}/timeline",
    response_model=list[dict[str, Any]],
)
async def get_incident_timeline(
    incident_id: str,
) -> list[dict[str, Any]]:
    """
    Return the event timeline for an incident.

    The production implementation will retrieve this from the audit/event
    store.
    """

    incident = _INCIDENTS.get(
        incident_id
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Incident '{incident_id}' was not found."
            ),
        )

    return [
        {
            "event": "incident_created",
            "timestamp": incident.created_at.isoformat(),
            "status": IncidentStatus.DETECTED.value,
        },
        {
            "event": "current_status",
            "timestamp": incident.updated_at.isoformat(),
            "status": incident.status.value,
        },
    ]


# ============================================================
# INCIDENT SUMMARY
# ============================================================


@router.get(
    "/summary/counts",
    response_model=dict[str, int],
)
async def incident_summary() -> dict[str, int]:
    """
    Return incident counts grouped by status and severity.
    """

    summary: dict[str, int] = {
        "total": len(_INCIDENTS),
    }

    for incident_status in IncidentStatus:
        summary[
            incident_status.value
        ] = 0

    for severity in IncidentSeverity:
        summary[
            severity.value
        ] = 0

    for incident in _INCIDENTS.values():
        summary[
            incident.status.value
        ] += 1

        summary[
            incident.severity.value
        ] += 1

    return summary


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "router",
    "IncidentType",
    "IncidentSeverity",
    "IncidentStatus",
    "IncidentCreate",
    "IncidentUpdate",
    "IncidentResponse",
    "IncidentResolveRequest",
]