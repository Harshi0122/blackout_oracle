"""
Blackout Oracle - Recommendation API Routes.

This module exposes HTTP endpoints for viewing, creating, reviewing,
approving, rejecting, and superseding Blackout Oracle recommendations.

A recommendation is a decision-support artifact produced from:

    Grid telemetry
          ↓
    Risk assessment
          ↓
    AI investigation
          ↓
    Scenario generation
          ↓
    Power-system simulation
          ↓
    Scenario verification
          ↓
    Recommendation

IMPORTANT SAFETY RULES
----------------------

Recommendations are NOT direct grid-control commands.

This API does NOT:

- Operate breakers.
- Modify substations.
- Modify SCADA.
- Control generators.
- Change real grid configuration.
- Execute infrastructure commands.

Human approval is required before a recommendation can be considered
operationally accepted.

The initial implementation uses an in-memory development store.
Production persistence will be implemented through the database/service
layers.
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
    prefix="/recommendations",
    tags=["Recommendations"],
)


# ============================================================
# ENUMS
# ============================================================


class RecommendationStatus(str, Enum):
    """Lifecycle status of a recommendation."""

    GENERATED = "generated"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class VerificationStatus(str, Enum):
    """Verification status of the underlying scenario."""

    NOT_VERIFIED = "not_verified"
    VERIFIED = "verified"
    FAILED = "failed"


# ============================================================
# SCHEMAS
# ============================================================


class RecommendationCreate(BaseModel):
    """
    Request model for creating a recommendation.

    In the production system, recommendations should normally be generated
    by the agent/workflow rather than directly by an untrusted client.
    """

    incident_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Incident associated with the recommendation.",
    )

    scenario_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Verified simulation scenario ID.",
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Recommendation title.",
    )

    explanation: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Explanation of the recommendation.",
    )

    rationale: list[str] = Field(
        default_factory=list,
        description="Evidence-based reasons supporting the recommendation.",
    )

    risk_before: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Estimated risk before the scenario.",
    )

    risk_after: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Estimated risk after the scenario.",
    )

    confidence: float = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence in the recommendation.",
    )

    verification_status: VerificationStatus = Field(
        ...,
        description="Verification status of the underlying scenario.",
    )

    simulation_result: dict[str, Any] | None = Field(
        default=None,
        description="Relevant simulation result.",
    )

    verification_result: dict[str, Any] | None = Field(
        default=None,
        description="Relevant verification result.",
    )

    expected_impact: dict[str, Any] = Field(
        default_factory=dict,
        description="Expected impact of the scenario.",
    )

    risks_and_uncertainties: list[str] = Field(
        default_factory=list,
        description="Known risks and uncertainties.",
    )

    affected_asset_ids: list[str] = Field(
        default_factory=list,
        description="Potentially affected asset IDs.",
    )

    expires_at: datetime | None = Field(
        default=None,
        description="Optional recommendation expiration time.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class RecommendationResponse(BaseModel):
    """Response model representing a recommendation."""

    id: str

    incident_id: str

    scenario_id: str

    title: str

    explanation: str

    rationale: list[str] = Field(
        default_factory=list
    )

    risk_before: float | None = None

    risk_after: float | None = None

    confidence: float

    verification_status: VerificationStatus

    simulation_result: dict[str, Any] | None = None

    verification_result: dict[str, Any] | None = None

    expected_impact: dict[str, Any] = Field(
        default_factory=dict
    )

    risks_and_uncertainties: list[str] = Field(
        default_factory=list
    )

    affected_asset_ids: list[str] = Field(
        default_factory=list
    )

    status: RecommendationStatus

    requires_human_approval: bool

    created_at: datetime

    reviewed_at: datetime | None = None

    reviewed_by: str | None = None

    review_note: str | None = None

    expires_at: datetime | None = None

    superseded_by: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class RecommendationReviewRequest(BaseModel):
    """Request model for human review."""

    reviewer_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Authorized human reviewer identifier.",
    )

    note: str | None = Field(
        default=None,
        max_length=5000,
        description="Optional review note.",
    )


# ============================================================
# DEVELOPMENT STORE
# ============================================================

# Temporary in-memory store.
#
# Production implementation will use PostgreSQL through the repository
# and service layers.

_RECOMMENDATIONS: dict[str, RecommendationResponse] = {}


# ============================================================
# VALIDATION HELPERS
# ============================================================


def _validate_recommendation_creation(
    recommendation: RecommendationCreate,
) -> None:
    """
    Apply mandatory recommendation safety checks.

    A recommendation cannot be created as an operationally valid
    recommendation unless its scenario has passed verification.
    """

    if (
        recommendation.verification_status
        != VerificationStatus.VERIFIED
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "A recommendation can only be created from a "
                "VERIFIED scenario."
            ),
        )

    if recommendation.simulation_result is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "A verified recommendation must include a simulation result."
            ),
        )

    if recommendation.verification_result is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "A verified recommendation must include a verification result."
            ),
        )


# ============================================================
# CREATE RECOMMENDATION
# ============================================================


@router.post(
    "",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_recommendation(
    recommendation: RecommendationCreate,
) -> RecommendationResponse:
    """
    Create a recommendation from a verified scenario.

    The recommendation is initially placed into PENDING_REVIEW.

    It cannot be treated as operationally accepted until an authorized
    human reviewer approves it.
    """

    _validate_recommendation_creation(
        recommendation
    )

    recommendation_id = (
        f"REC-{uuid4().hex[:12].upper()}"
    )

    now = datetime.now(timezone.utc)

    response = RecommendationResponse(
        id=recommendation_id,
        incident_id=recommendation.incident_id,
        scenario_id=recommendation.scenario_id,
        title=recommendation.title,
        explanation=recommendation.explanation,
        rationale=recommendation.rationale,
        risk_before=recommendation.risk_before,
        risk_after=recommendation.risk_after,
        confidence=recommendation.confidence,
        verification_status=recommendation.verification_status,
        simulation_result=recommendation.simulation_result,
        verification_result=recommendation.verification_result,
        expected_impact=recommendation.expected_impact,
        risks_and_uncertainties=recommendation.risks_and_uncertainties,
        affected_asset_ids=recommendation.affected_asset_ids,
        status=RecommendationStatus.PENDING_REVIEW,
        requires_human_approval=True,
        created_at=now,
        expires_at=recommendation.expires_at,
        metadata=recommendation.metadata,
    )

    _RECOMMENDATIONS[
        recommendation_id
    ] = response

    return response


# ============================================================
# LIST RECOMMENDATIONS
# ============================================================


@router.get(
    "",
    response_model=list[RecommendationResponse],
)
async def list_recommendations(
    recommendation_status: RecommendationStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by recommendation status.",
    ),
    incident_id: str | None = Query(
        default=None,
        description="Filter by incident.",
    ),
    scenario_id: str | None = Query(
        default=None,
        description="Filter by scenario.",
    ),
    verification_status: VerificationStatus | None = Query(
        default=None,
        description="Filter by verification status.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of recommendations.",
    ),
) -> list[RecommendationResponse]:
    """
    List recommendations using optional filters.
    """

    recommendations = list(
        _RECOMMENDATIONS.values()
    )

    if recommendation_status is not None:
        recommendations = [
            recommendation
            for recommendation in recommendations
            if recommendation.status
            == recommendation_status
        ]

    if incident_id is not None:
        recommendations = [
            recommendation
            for recommendation in recommendations
            if recommendation.incident_id
            == incident_id
        ]

    if scenario_id is not None:
        recommendations = [
            recommendation
            for recommendation in recommendations
            if recommendation.scenario_id
            == scenario_id
        ]

    if verification_status is not None:
        recommendations = [
            recommendation
            for recommendation in recommendations
            if recommendation.verification_status
            == verification_status
        ]

    recommendations.sort(
        key=lambda recommendation: recommendation.created_at,
        reverse=True,
    )

    return recommendations[:limit]


# ============================================================
# GET RECOMMENDATION
# ============================================================


@router.get(
    "/{recommendation_id}",
    response_model=RecommendationResponse,
)
async def get_recommendation(
    recommendation_id: str,
) -> RecommendationResponse:
    """
    Retrieve a single recommendation.
    """

    recommendation = _RECOMMENDATIONS.get(
        recommendation_id
    )

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Recommendation '{recommendation_id}' was not found."
            ),
        )

    return recommendation


# ============================================================
# APPROVE RECOMMENDATION
# ============================================================


@router.post(
    "/{recommendation_id}/approve",
    response_model=RecommendationResponse,
)
async def approve_recommendation(
    recommendation_id: str,
    request: RecommendationReviewRequest,
) -> RecommendationResponse:
    """
    Approve a recommendation through human review.

    IMPORTANT:

    Approval changes the recommendation's lifecycle status only.

    It does NOT automatically execute the recommendation against
    electrical infrastructure.
    """

    recommendation = _RECOMMENDATIONS.get(
        recommendation_id
    )

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Recommendation '{recommendation_id}' was not found."
            ),
        )

    if (
        recommendation.verification_status
        != VerificationStatus.VERIFIED
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Only verified recommendations can be approved."
            ),
        )

    if recommendation.status in {
        RecommendationStatus.REJECTED,
        RecommendationStatus.EXPIRED,
        RecommendationStatus.SUPERSEDED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Recommendation cannot be approved from status "
                f"'{recommendation.status.value}'."
            ),
        )

    now = datetime.now(timezone.utc)

    recommendation.status = (
        RecommendationStatus.APPROVED
    )

    recommendation.reviewed_at = now
    recommendation.reviewed_by = request.reviewer_id
    recommendation.review_note = request.note

    return recommendation


# ============================================================
# REJECT RECOMMENDATION
# ============================================================


@router.post(
    "/{recommendation_id}/reject",
    response_model=RecommendationResponse,
)
async def reject_recommendation(
    recommendation_id: str,
    request: RecommendationReviewRequest,
) -> RecommendationResponse:
    """
    Reject a recommendation through human review.

    Rejection is recorded for auditing and future model evaluation.
    """

    recommendation = _RECOMMENDATIONS.get(
        recommendation_id
    )

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Recommendation '{recommendation_id}' was not found."
            ),
        )

    if recommendation.status in {
        RecommendationStatus.EXECUTED,
        RecommendationStatus.EXPIRED,
        RecommendationStatus.SUPERSEDED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Recommendation cannot be rejected from status "
                f"'{recommendation.status.value}'."
            ),
        )

    now = datetime.now(timezone.utc)

    recommendation.status = (
        RecommendationStatus.REJECTED
    )

    recommendation.reviewed_at = now
    recommendation.reviewed_by = request.reviewer_id
    recommendation.review_note = request.note

    return recommendation


# ============================================================
# MARK EXECUTED
# ============================================================


@router.post(
    "/{recommendation_id}/executed",
    response_model=RecommendationResponse,
)
async def mark_recommendation_executed(
    recommendation_id: str,
    request: RecommendationReviewRequest,
) -> RecommendationResponse:
    """
    Record that an approved recommendation was acted upon externally.

    IMPORTANT:

    This endpoint does NOT execute an electrical operation.

    It only records that an authorized human/operator reports that the
    recommendation was acted upon through an external operational system.
    """

    recommendation = _RECOMMENDATIONS.get(
        recommendation_id
    )

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Recommendation '{recommendation_id}' was not found."
            ),
        )

    if recommendation.status != RecommendationStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Only an approved recommendation can be marked as executed."
            ),
        )

    now = datetime.now(timezone.utc)

    recommendation.status = (
        RecommendationStatus.EXECUTED
    )

    recommendation.reviewed_at = now
    recommendation.reviewed_by = request.reviewer_id
    recommendation.review_note = request.note

    return recommendation


# ============================================================
# SUPERSEDE RECOMMENDATION
# ============================================================


@router.post(
    "/{recommendation_id}/supersede",
    response_model=RecommendationResponse,
)
async def supersede_recommendation(
    recommendation_id: str,
    replacement_recommendation_id: str = Query(
        ...,
        min_length=1,
        description="ID of the replacement recommendation.",
    ),
) -> RecommendationResponse:
    """
    Mark an older recommendation as superseded by a newer one.
    """

    recommendation = _RECOMMENDATIONS.get(
        recommendation_id
    )

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Recommendation '{recommendation_id}' was not found."
            ),
        )

    replacement = _RECOMMENDATIONS.get(
        replacement_recommendation_id
    )

    if replacement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Replacement recommendation "
                f"'{replacement_recommendation_id}' was not found."
            ),
        )

    if recommendation_id == replacement_recommendation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A recommendation cannot supersede itself."
            ),
        )

    recommendation.status = (
        RecommendationStatus.SUPERSEDED
    )

    recommendation.superseded_by = (
        replacement_recommendation_id
    )

    recommendation.reviewed_at = (
        datetime.now(timezone.utc)
    )

    return recommendation


# ============================================================
# RECOMMENDATION STATUS
# ============================================================


@router.get(
    "/{recommendation_id}/status",
    response_model=dict[str, Any],
)
async def get_recommendation_status(
    recommendation_id: str,
) -> dict[str, Any]:
    """
    Return a compact recommendation status.
    """

    recommendation = _RECOMMENDATIONS.get(
        recommendation_id
    )

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Recommendation '{recommendation_id}' was not found."
            ),
        )

    return {
        "recommendation_id": recommendation.id,
        "incident_id": recommendation.incident_id,
        "scenario_id": recommendation.scenario_id,
        "status": recommendation.status.value,
        "verification_status": (
            recommendation.verification_status.value
        ),
        "confidence": recommendation.confidence,
        "requires_human_approval": (
            recommendation.requires_human_approval
        ),
        "created_at": recommendation.created_at.isoformat(),
        "reviewed_at": (
            recommendation.reviewed_at.isoformat()
            if recommendation.reviewed_at
            else None
        ),
    }


# ============================================================
# PENDING REVIEW
# ============================================================


@router.get(
    "/review/pending",
    response_model=list[RecommendationResponse],
)
async def get_pending_recommendations(
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
) -> list[RecommendationResponse]:
    """
    Return recommendations waiting for human review.

    Useful for the future operator dashboard.
    """

    recommendations = [
        recommendation
        for recommendation in _RECOMMENDATIONS.values()
        if recommendation.status
        == RecommendationStatus.PENDING_REVIEW
    ]

    recommendations.sort(
        key=lambda recommendation: recommendation.created_at,
        reverse=True,
    )

    return recommendations[:limit]


# ============================================================
# SUMMARY
# ============================================================


@router.get(
    "/summary/counts",
    response_model=dict[str, int],
)
async def recommendation_summary() -> dict[str, int]:
    """
    Return recommendation counts grouped by lifecycle status.
    """

    summary: dict[str, int] = {
        "total": len(_RECOMMENDATIONS),
    }

    for recommendation_status in RecommendationStatus:
        summary[
            recommendation_status.value
        ] = 0

    for verification_status in VerificationStatus:
        summary[
            verification_status.value
        ] = 0

    for recommendation in _RECOMMENDATIONS.values():
        summary[
            recommendation.status.value
        ] += 1

        summary[
            recommendation.verification_status.value
        ] += 1

    return summary


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "router",
    "RecommendationStatus",
    "VerificationStatus",
    "RecommendationCreate",
    "RecommendationResponse",
    "RecommendationReviewRequest",
]