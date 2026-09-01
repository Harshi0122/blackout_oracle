"""
Blackout Oracle - Risk Schemas.

Pydantic schemas for grid-risk calculations, predictions,
assessments, risk factors, and operational risk summaries.

These schemas are independent of SQLAlchemy models and can be
used safely by the API, risk engine, ML services, simulation
services, and incident-management layer.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# ENUMS
# ============================================================


class RiskLevel(str, Enum):
    """Standard Blackout Oracle risk levels."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskType(str, Enum):
    """Types of risk evaluated by Blackout Oracle."""

    OVERALL = "overall"
    ELECTRICAL = "electrical"
    ASSET = "asset"
    WEATHER = "weather"
    ANOMALY = "anomaly"
    BLACKOUT = "blackout"
    CASCADE = "cascade"
    FORECAST = "forecast"


class RiskTrend(str, Enum):
    """Direction in which risk is changing."""

    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"
    UNKNOWN = "unknown"


# ============================================================
# RISK FACTOR
# ============================================================


class RiskFactor(BaseModel):
    """
    Individual contributor to an overall risk assessment.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the risk factor.",
    )

    score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Risk score from 0 to 100.",
    )

    weight: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Normalized contribution weight.",
    )

    contribution: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Weighted contribution to overall risk.",
    )

    severity: RiskLevel = Field(
        default=RiskLevel.VERY_LOW,
    )

    explanation: str | None = Field(
        default=None,
        max_length=5000,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# RISK SCORE
# ============================================================


class RiskScore(BaseModel):
    """
    Basic risk score representation.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
    )

    level: RiskLevel

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

    timestamp: datetime = Field(
        ...,
    )


# ============================================================
# RISK BASE
# ============================================================


class RiskBase(BaseModel):
    """
    Common fields shared by risk schemas.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    risk_type: RiskType = Field(
        ...,
        description="Category of risk being evaluated.",
    )

    score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Risk score from 0 to 100.",
    )

    level: RiskLevel = Field(
        ...,
        description="Categorical risk level.",
    )

    probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Estimated probability of the event.",
    )

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence in the risk estimate.",
    )

    trend: RiskTrend = Field(
        default=RiskTrend.UNKNOWN,
        description="Current risk trend.",
    )

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

    alert_required: bool = False

    critical: bool = False

    factors: list[RiskFactor] = Field(
        default_factory=list,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# RISK REQUEST
# ============================================================


class RiskAssessmentRequest(BaseModel):
    """
    Request payload for calculating grid risk.

    Individual components may be supplied as 0-100 scores.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    electrical_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    asset_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    weather_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    anomaly_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    blackout_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    cascade_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    forecast_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

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

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# RISK ASSESSMENT RESPONSE
# ============================================================


class RiskAssessmentResponse(RiskBase):
    """
    Complete API response for a risk assessment.
    """

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        extra="forbid",
    )

    id: int | None = Field(
        default=None,
        ge=1,
    )

    assessed_at: datetime = Field(
        ...,
    )

    valid_until: datetime | None = None

    engine: str | None = Field(
        default=None,
        max_length=255,
    )

    engine_version: str | None = Field(
        default=None,
        max_length=100,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# BLACKOUT RISK
# ============================================================


class BlackoutRiskRequest(BaseModel):
    """
    Request payload for blackout-risk calculation.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    model_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    affected_load_mw: float | None = Field(
        default=None,
        ge=0.0,
    )

    affected_load_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    region: str | None = Field(
        default=None,
        max_length=255,
    )

    substation_id: int | None = Field(
        default=None,
        ge=1,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class BlackoutRiskResponse(BaseModel):
    """
    Blackout-risk prediction response.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    risk_type: RiskType = RiskType.BLACKOUT

    score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
    )

    level: RiskLevel

    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    predicted_horizon_minutes: int | None = Field(
        default=None,
        ge=0,
    )

    affected_load_mw: float | None = Field(
        default=None,
        ge=0.0,
    )

    affected_load_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    factors: list[RiskFactor] = Field(
        default_factory=list,
    )

    assessed_at: datetime

    model_name: str | None = None

    model_version: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# CASCADE RISK
# ============================================================


class CascadeRiskRequest(BaseModel):
    """
    Request payload for cascading-failure risk analysis.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    network_stress: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    vulnerable_assets: int | None = Field(
        default=None,
        ge=0,
    )

    propagation_depth: int | None = Field(
        default=None,
        ge=0,
    )

    region: str | None = Field(
        default=None,
        max_length=255,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class CascadeRiskResponse(BaseModel):
    """
    Cascading-failure risk response.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    risk_type: RiskType = RiskType.CASCADE

    score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
    )

    level: RiskLevel

    probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    vulnerable_assets: int = Field(
        default=0,
        ge=0,
    )

    propagation_depth: int = Field(
        default=0,
        ge=0,
    )

    affected_assets: list[int] = Field(
        default_factory=list,
    )

    factors: list[RiskFactor] = Field(
        default_factory=list,
    )

    assessed_at: datetime

    model_name: str | None = None

    model_version: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# ASSET FAILURE RISK
# ============================================================


class AssetFailureRiskRequest(BaseModel):
    """
    Request payload for asset-failure risk prediction.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    asset_id: int = Field(
        ...,
        ge=1,
    )

    health_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    temperature: float | None = None

    loading_percent: float | None = Field(
        default=None,
        ge=0.0,
    )

    age_years: float | None = Field(
        default=None,
        ge=0.0,
    )

    anomaly_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class AssetFailureRiskResponse(BaseModel):
    """
    Asset-failure prediction response.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    asset_id: int = Field(
        ...,
        ge=1,
    )

    score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
    )

    level: RiskLevel

    failure_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    predicted_horizon_hours: float | None = Field(
        default=None,
        ge=0.0,
    )

    factors: list[RiskFactor] = Field(
        default_factory=list,
    )

    assessed_at: datetime

    model_name: str | None = None

    model_version: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# RISK TREND
# ============================================================


class RiskTrendPoint(BaseModel):
    """
    One point in a historical risk trend.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    timestamp: datetime

    score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
    )

    level: RiskLevel

    probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )


class RiskTrendResponse(BaseModel):
    """
    Historical risk trend response.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    risk_type: RiskType

    current_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
    )

    previous_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    trend: RiskTrend

    change: float | None = None

    points: list[RiskTrendPoint] = Field(
        default_factory=list,
    )

    start_time: datetime

    end_time: datetime


# ============================================================
# RISK SUMMARY
# ============================================================


class RiskSummaryResponse(BaseModel):
    """
    High-level summary of grid risk.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    overall_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
    )

    overall_level: RiskLevel

    overall_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    trend: RiskTrend = RiskTrend.UNKNOWN

    electrical_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    asset_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    weather_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    anomaly_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    blackout_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    cascade_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    forecast_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    active_alerts: int = Field(
        default=0,
        ge=0,
    )

    active_incidents: int = Field(
        default=0,
        ge=0,
    )

    critical_assets: int = Field(
        default=0,
        ge=0,
    )

    assessed_at: datetime

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# RISK CONFIGURATION
# ============================================================


class RiskWeightsSchema(BaseModel):
    """
    Configurable weights used by the risk-scoring engine.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    electrical: float = Field(
        default=0.25,
        ge=0.0,
    )

    asset: float = Field(
        default=0.20,
        ge=0.0,
    )

    weather: float = Field(
        default=0.10,
        ge=0.0,
    )

    anomaly: float = Field(
        default=0.15,
        ge=0.0,
    )

    blackout: float = Field(
        default=0.15,
        ge=0.0,
    )

    cascade: float = Field(
        default=0.10,
        ge=0.0,
    )

    forecast: float = Field(
        default=0.05,
        ge=0.0,
    )


class RiskThresholds(BaseModel):
    """
    Threshold configuration for risk levels and alerts.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    low_threshold: float = Field(
        default=25.0,
        ge=0.0,
        le=100.0,
    )

    medium_threshold: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
    )

    high_threshold: float = Field(
        default=75.0,
        ge=0.0,
        le=100.0,
    )

    critical_threshold: float = Field(
        default=90.0,
        ge=0.0,
        le=100.0,
    )

    alert_threshold: float = Field(
        default=75.0,
        ge=0.0,
        le=100.0,
    )


# ============================================================
# RISK FILTER
# ============================================================


class RiskFilter(BaseModel):
    """
    Filters for querying stored risk assessments.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    risk_type: RiskType | None = None

    level: RiskLevel | None = None

    trend: RiskTrend | None = None

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

    min_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    max_score: float | None = Field(
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
# RISK LIST RESPONSE
# ============================================================


class RiskListResponse(BaseModel):
    """
    Paginated collection of risk assessments.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[RiskAssessmentResponse] = Field(
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
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "RiskLevel",
    "RiskType",
    "RiskTrend",
    "RiskFactor",
    "RiskScore",
    "RiskBase",
    "RiskAssessmentRequest",
    "RiskAssessmentResponse",
    "BlackoutRiskRequest",
    "BlackoutRiskResponse",
    "CascadeRiskRequest",
    "CascadeRiskResponse",
    "AssetFailureRiskRequest",
    "AssetFailureRiskResponse",
    "RiskTrendPoint",
    "RiskTrendResponse",
    "RiskSummaryResponse",
    "RiskWeightsSchema",
    "RiskThresholds",
    "RiskFilter",
    "RiskListResponse",
]