"""
Blackout Oracle - Recommendation Schemas.

Pydantic schemas for AI-generated and rule-based operational
recommendations.

Recommendations are decision-support outputs. They should be
reviewed by qualified grid operators before any real-world
control action is taken.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# ENUMS
# ============================================================


class RecommendationPriority(str, Enum):
    """Priority assigned to a recommendation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendationType(str, Enum):
    """Category of recommended action."""

    MONITOR = "monitor"
    INSPECT = "inspect"
    INVESTIGATE = "investigate"
    MAINTENANCE = "maintenance"
    LOAD_MANAGEMENT = "load_management"
    GENERATION_MANAGEMENT = "generation_management"
    NETWORK_RECONFIGURATION = "network_reconfiguration"
    CONTINGENCY = "contingency"
    WEATHER_PREPARATION = "weather_preparation"
    DATA_VALIDATION = "data_validation"
    SIMULATION = "simulation"
    OPERATOR_REVIEW = "operator_review"
    OTHER = "other"


class RecommendationStatus(str, Enum):
    """Lifecycle state of a recommendation."""

    PENDING = "pending"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class RecommendationSource(str, Enum):
    """Source that produced a recommendation."""

    RULE_ENGINE = "rule_engine"
    ML_MODEL = "ml_model"
    RISK_ENGINE = "risk_engine"
    INCIDENT_MANAGER = "incident_manager"
    SIMULATION = "simulation"
    OPERATOR = "operator"
    HYBRID = "hybrid"


# ============================================================
# BASE RECOMMENDATION
# ============================================================


class RecommendationBase(BaseModel):
    """
    Common fields shared by recommendation schemas.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Short recommendation title.",
    )

    description: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Detailed recommended action.",
    )

    recommendation_type: RecommendationType = Field(
        ...,
        description="Type of recommended action.",
    )

    priority: RecommendationPriority = Field(
        default=RecommendationPriority.MEDIUM,
        description="Operational priority.",
    )

    status: RecommendationStatus = Field(
        default=RecommendationStatus.PENDING,
        description="Current recommendation status.",
    )

    source: RecommendationSource = Field(
        default=RecommendationSource.RISK_ENGINE,
        description="System that generated the recommendation.",
    )

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence in the recommendation.",
    )

    risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Risk score that triggered the recommendation.",
    )

    region: str | None = Field(
        default=None,
        max_length=255,
        description="Affected geographical or operational region.",
    )

    substation_id: int | None = Field(
        default=None,
        ge=1,
        description="Related substation identifier.",
    )

    transformer_id: int | None = Field(
        default=None,
        ge=1,
        description="Related transformer identifier.",
    )

    transmission_line_id: int | None = Field(
        default=None,
        ge=1,
        description="Related transmission-line identifier.",
    )

    asset_id: int | None = Field(
        default=None,
        ge=1,
        description="Related generic asset identifier.",
    )

    incident_id: int | None = Field(
        default=None,
        ge=1,
        description="Related incident identifier.",
    )

    alert_id: int | None = Field(
        default=None,
        ge=1,
        description="Related alert identifier.",
    )

    rationale: str | None = Field(
        default=None,
        max_length=5000,
        description="Reason the recommendation was generated.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured recommendation information.",
    )


# ============================================================
# RECOMMENDATION CREATE
# ============================================================


class RecommendationCreate(RecommendationBase):
    """
    Schema used when creating a recommendation.
    """

    expires_at: datetime | None = Field(
        default=None,
        description="Optional time after which the recommendation expires.",
    )

    created_by: str | None = Field(
        default=None,
        max_length=255,
        description="User or service that created the recommendation.",
    )


# ============================================================
# RECOMMENDATION UPDATE
# ============================================================


class RecommendationUpdate(BaseModel):
    """
    Schema used for partial recommendation updates.
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
        min_length=1,
        max_length=5000,
    )

    recommendation_type: RecommendationType | None = None

    priority: RecommendationPriority | None = None

    status: RecommendationStatus | None = None

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    rationale: str | None = Field(
        default=None,
        max_length=5000,
    )

    expires_at: datetime | None = None

    metadata: dict[str, Any] | None = None


# ============================================================
# REVIEW
# ============================================================


class RecommendationReview(BaseModel):
    """
    Schema used when an operator reviews a recommendation.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    status: RecommendationStatus

    reviewed_by: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    review_comment: str | None = Field(
        default=None,
        max_length=5000,
    )


# ============================================================
# EXECUTION
# ============================================================


class RecommendationExecution(BaseModel):
    """
    Schema recording the outcome of an accepted recommendation.

    The recommendation itself does not execute grid-control
    commands. This schema records an externally performed action
    or operator-confirmed outcome.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    executed_by: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    executed_at: datetime

    outcome: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )

    success: bool

    notes: str | None = Field(
        default=None,
        max_length=5000,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# RECOMMENDATION RESPONSE
# ============================================================


class RecommendationResponse(RecommendationBase):
    """
    API response representing a stored recommendation.
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

    created_by: str | None = None

    created_at: datetime

    updated_at: datetime

    expires_at: datetime | None = None

    reviewed_at: datetime | None = None

    reviewed_by: str | None = None

    review_comment: str | None = None

    executed_at: datetime | None = None

    executed_by: str | None = None

    execution_outcome: str | None = None


# ============================================================
# FILTERS
# ============================================================


class RecommendationFilter(BaseModel):
    """
    Filters used when querying recommendations.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    recommendation_type: RecommendationType | None = None

    priority: RecommendationPriority | None = None

    status: RecommendationStatus | None = None

    source: RecommendationSource | None = None

    region: str | None = Field(
        default=None,
        max_length=255,
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

    incident_id: int | None = Field(
        default=None,
        ge=1,
    )

    alert_id: int | None = Field(
        default=None,
        ge=1,
    )

    min_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    max_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
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

    include_expired: bool = False

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
# LIST RESPONSE
# ============================================================


class RecommendationListResponse(BaseModel):
    """
    Paginated collection of recommendations.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[RecommendationResponse] = Field(
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
# SUMMARY
# ============================================================


class RecommendationSummary(BaseModel):
    """
    Aggregated recommendation statistics.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    total: int = Field(
        default=0,
        ge=0,
    )

    pending: int = Field(
        default=0,
        ge=0,
    )

    reviewed: int = Field(
        default=0,
        ge=0,
    )

    accepted: int = Field(
        default=0,
        ge=0,
    )

    rejected: int = Field(
        default=0,
        ge=0,
    )

    executed: int = Field(
        default=0,
        ge=0,
    )

    expired: int = Field(
        default=0,
        ge=0,
    )

    cancelled: int = Field(
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
# RECOMMENDATION FACTOR
# ============================================================


class RecommendationFactor(BaseModel):
    """
    A single factor supporting a recommendation.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    value: float | str | bool | None = None

    importance: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )


# ============================================================
# AI RECOMMENDATION
# ============================================================


class AIRecommendation(BaseModel):
    """
    Recommendation generated by an ML/AI component.

    This schema captures the model's reasoning inputs without
    requiring the API layer to know the implementation details
    of the underlying model.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    recommendation_type: RecommendationType

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    description: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )

    priority: RecommendationPriority

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    rationale: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )

    factors: list[RecommendationFactor] = Field(
        default_factory=list,
    )

    expected_benefit: str | None = Field(
        default=None,
        max_length=2000,
    )

    potential_risks: list[str] = Field(
        default_factory=list,
    )

    requires_operator_approval: bool = True

    generated_at: datetime = Field(
        ...,
    )

    model_name: str | None = Field(
        default=None,
        max_length=255,
    )

    model_version: str | None = Field(
        default=None,
        max_length=100,
    )


# ============================================================
# RECOMMENDATION EVENT
# ============================================================


class RecommendationEvent(BaseModel):
    """
    Event representation for recommendation notifications.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    recommendation_id: int = Field(
        ...,
        ge=1,
    )

    event_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    timestamp: datetime

    status: RecommendationStatus

    priority: RecommendationPriority

    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "RecommendationPriority",
    "RecommendationType",
    "RecommendationStatus",
    "RecommendationSource",
    "RecommendationBase",
    "RecommendationCreate",
    "RecommendationUpdate",
    "RecommendationReview",
    "RecommendationExecution",
    "RecommendationResponse",
    "RecommendationFilter",
    "RecommendationListResponse",
    "RecommendationSummary",
    "RecommendationFactor",
    "AIRecommendation",
    "RecommendationEvent",
]