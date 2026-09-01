"""
Blackout Oracle - Risk API Routes.

This module exposes HTTP endpoints for blackout and grid-instability
risk assessment.

The risk layer combines information such as:

- Grid telemetry
- Load and generation
- Voltage/frequency anomalies
- Asset condition
- Weather
- Rainfall
- Flood risk
- Temperature
- Historical incidents
- Forecast outputs
- Network topology
- Cascading-failure indicators

IMPORTANT
---------

This module is an API layer.

It does NOT:

- Directly control grid infrastructure.
- Operate breakers.
- Modify SCADA.
- Change substation configuration.
- Execute mitigation actions.

Actual risk calculations belong to the risk-engine/service layer.

The initial implementation uses an in-memory development store and
placeholder calculations. These will be replaced by the real risk
engine and database later.
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
    prefix="/risk",
    tags=["Risk"],
)


# ============================================================
# ENUMS
# ============================================================


class RiskLevel(str, Enum):
    """Blackout risk classification."""

    NORMAL = "normal"
    WATCH = "watch"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class RiskType(str, Enum):
    """Type of risk being assessed."""

    BLACKOUT = "blackout"
    CASCADE = "cascade"
    OVERLOAD = "overload"
    VOLTAGE = "voltage"
    FREQUENCY = "frequency"
    WEATHER = "weather"
    FLOOD = "flood"
    GENERATION_SHORTAGE = "generation_shortage"
    DEMAND_SURGE = "demand_surge"


# ============================================================
# REQUEST SCHEMAS
# ============================================================


class RiskAssessmentRequest(BaseModel):
    """
    Request model for calculating risk.

    In production, most of this information will be automatically collected
    from the telemetry, weather, forecasting, and asset services.
    """

    region_id: str | None = Field(
        default=None,
        max_length=100,
    )

    region_name: str | None = Field(
        default=None,
        max_length=200,
    )

    asset_ids: list[str] = Field(
        default_factory=list,
    )

    telemetry: dict[str, Any] = Field(
        default_factory=dict,
        description="Latest permitted grid telemetry.",
    )

    weather: dict[str, Any] = Field(
        default_factory=dict,
        description="Latest weather/environmental information.",
    )

    forecast: dict[str, Any] = Field(
        default_factory=dict,
        description="Load/generation forecast information.",
    )

    historical_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Relevant historical context.",
    )


# ============================================================
# RESPONSE SCHEMAS
# ============================================================


class RiskFactor(BaseModel):
    """A factor contributing to the calculated risk."""

    name: str

    category: RiskType

    contribution: float = Field(
        ...,
        ge=0,
        le=100,
    )

    severity: RiskLevel

    description: str

    evidence: dict[str, Any] = Field(
        default_factory=dict,
    )


class RiskAssessmentResponse(BaseModel):
    """Complete blackout-risk assessment."""

    id: str

    region_id: str | None = None

    region_name: str | None = None

    risk_type: RiskType

    risk_score: float = Field(
        ...,
        ge=0,
        le=100,
    )

    risk_level: RiskLevel

    confidence: float = Field(
        ...,
        ge=0,
        le=100,
    )

    blackout_probability: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    cascade_probability: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    warning_horizon_minutes: float | None = Field(
        default=None,
        ge=0,
    )

    affected_asset_ids: list[str] = Field(
        default_factory=list,
    )

    risk_factors: list[RiskFactor] = Field(
        default_factory=list,
    )

    model_name: str

    model_version: str

    data_timestamp: datetime

    calculated_at: datetime

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class RiskHistoryPoint(BaseModel):
    """Historical risk observation."""

    timestamp: datetime

    risk_score: float = Field(
        ...,
        ge=0,
        le=100,
    )

    risk_level: RiskLevel

    confidence: float = Field(
        ...,
        ge=0,
        le=100,
    )


class RiskSummaryResponse(BaseModel):
    """Summary of current and historical risk."""

    region_id: str | None = None

    region_name: str | None = None

    current_score: float

    current_level: RiskLevel

    average_score: float

    maximum_score: float

    minimum_score: float

    trend: str

    observations: int

    calculated_at: datetime


# ============================================================
# DEVELOPMENT STORE
# ============================================================

# Temporary in-memory risk store.
#
# Production implementation will use the database/time-series layer.

_RISK_ASSESSMENTS: dict[str, RiskAssessmentResponse] = {}

_RISK_HISTORY: list[RiskHistoryPoint] = []


# ============================================================
# RISK HELPERS
# ============================================================


def risk_level_from_score(
    score: float,
) -> RiskLevel:
    """
    Convert a 0-100 risk score into a risk level.
    """

    if score >= 95:
        return RiskLevel.CRITICAL

    if score >= 80:
        return RiskLevel.HIGH

    if score >= 60:
        return RiskLevel.ELEVATED

    if score >= 40:
        return RiskLevel.WATCH

    return RiskLevel.NORMAL


def calculate_placeholder_risk(
    request: RiskAssessmentRequest,
) -> tuple[float, list[RiskFactor]]:
    """
    Calculate a temporary development risk score.

    IMPORTANT:

    This is NOT the production Blackout Oracle risk model.

    It exists only so the API can be tested before the actual risk engine
    is implemented.

    The production implementation will use telemetry, ML models,
    power-system analysis, weather data, and topology-aware calculations.
    """

    score = 0.0

    factors: list[RiskFactor] = []

    # --------------------------------------------------------
    # Telemetry-based indicators
    # --------------------------------------------------------

    telemetry = request.telemetry

    load_ratio = telemetry.get(
        "load_ratio"
    )

    if isinstance(load_ratio, (int, float)):
        load_ratio = float(load_ratio)

        if load_ratio >= 1.0:
            contribution = 35.0

            factors.append(
                RiskFactor(
                    name="High system loading",
                    category=RiskType.OVERLOAD,
                    contribution=contribution,
                    severity=RiskLevel.HIGH,
                    description=(
                        "Observed loading is at or above the "
                        "configured capacity threshold."
                    ),
                    evidence={
                        "load_ratio": load_ratio,
                    },
                )
            )

            score += contribution

        elif load_ratio >= 0.85:
            contribution = 20.0

            factors.append(
                RiskFactor(
                    name="Elevated system loading",
                    category=RiskType.OVERLOAD,
                    contribution=contribution,
                    severity=RiskLevel.ELEVATED,
                    description=(
                        "Observed loading is approaching the "
                        "configured capacity threshold."
                    ),
                    evidence={
                        "load_ratio": load_ratio,
                    },
                )
            )

            score += contribution

    # --------------------------------------------------------
    # Weather indicators
    # --------------------------------------------------------

    weather = request.weather

    flood_risk = weather.get(
        "flood_risk"
    )

    if isinstance(flood_risk, (int, float)):
        flood_risk = float(flood_risk)

        contribution = min(
            20.0,
            flood_risk * 0.20,
        )

        if contribution > 0:
            factors.append(
                RiskFactor(
                    name="Flood risk",
                    category=RiskType.FLOOD,
                    contribution=contribution,
                    severity=risk_level_from_score(
                        flood_risk
                    ),
                    description=(
                        "Environmental conditions indicate "
                        "potential flood-related grid risk."
                    ),
                    evidence={
                        "flood_risk": flood_risk,
                    },
                )
            )

            score += contribution

    # --------------------------------------------------------
    # Temperature
    # --------------------------------------------------------

    temperature = weather.get(
        "temperature_c"
    )

    if isinstance(temperature, (int, float)):
        temperature = float(temperature)

        if temperature >= 40:
            contribution = 15.0

            factors.append(
                RiskFactor(
                    name="Extreme temperature",
                    category=RiskType.WEATHER,
                    contribution=contribution,
                    severity=RiskLevel.HIGH,
                    description=(
                        "High temperature may increase electrical "
                        "demand and equipment thermal stress."
                    ),
                    evidence={
                        "temperature_c": temperature,
                    },
                )
            )

            score += contribution

    # --------------------------------------------------------
    # Demand surge
    # --------------------------------------------------------

    demand_change = telemetry.get(
        "demand_change_percent"
    )

    if isinstance(
        demand_change,
        (int, float),
    ):
        demand_change = float(
            demand_change
        )

        if demand_change >= 15:
            contribution = 15.0

            factors.append(
                RiskFactor(
                    name="Demand surge",
                    category=RiskType.DEMAND_SURGE,
                    contribution=contribution,
                    severity=RiskLevel.HIGH,
                    description=(
                        "Electrical demand has increased significantly "
                        "over the configured baseline."
                    ),
                    evidence={
                        "demand_change_percent": demand_change,
                    },
                )
            )

            score += contribution

    # --------------------------------------------------------
    # Voltage anomaly
    # --------------------------------------------------------

    voltage_deviation = telemetry.get(
        "voltage_deviation_percent"
    )

    if isinstance(
        voltage_deviation,
        (int, float),
    ):
        voltage_deviation = abs(
            float(voltage_deviation)
        )

        if voltage_deviation >= 10:
            contribution = 20.0

            factors.append(
                RiskFactor(
                    name="Voltage instability",
                    category=RiskType.VOLTAGE,
                    contribution=contribution,
                    severity=RiskLevel.HIGH,
                    description=(
                        "Voltage deviation exceeds the configured "
                        "monitoring threshold."
                    ),
                    evidence={
                        "voltage_deviation_percent": (
                            voltage_deviation
                        ),
                    },
                )
            )

            score += contribution

    score = min(
        100.0,
        score,
    )

    return score, factors


# ============================================================
# CALCULATE RISK
# ============================================================


@router.post(
    "/assess",
    response_model=RiskAssessmentResponse,
)
async def assess_risk(
    request: RiskAssessmentRequest,
) -> RiskAssessmentResponse:
    """
    Calculate current blackout/grid risk.

    This endpoint currently uses a placeholder risk engine.

    The production version will call the dedicated risk-engine service.
    """

    score, factors = calculate_placeholder_risk(
        request
    )

    now = datetime.now(timezone.utc)

    risk_level = risk_level_from_score(
        score
    )

    # Conservative development default.
    confidence = 50.0

    assessment_id = (
        f"RISK-{uuid4().hex[:12].upper()}"
    )

    response = RiskAssessmentResponse(
        id=assessment_id,
        region_id=request.region_id,
        region_name=request.region_name,
        risk_type=RiskType.BLACKOUT,
        risk_score=score,
        risk_level=risk_level,
        confidence=confidence,
        blackout_probability=score / 100.0,
        cascade_probability=None,
        warning_horizon_minutes=None,
        affected_asset_ids=request.asset_ids,
        risk_factors=factors,
        model_name="blackout_oracle_placeholder",
        model_version="0.1.0",
        data_timestamp=now,
        calculated_at=now,
        metadata={
            "development_mode": True,
            "production_risk_engine": False,
        },
    )

    _RISK_ASSESSMENTS[
        assessment_id
    ] = response

    _RISK_HISTORY.append(
        RiskHistoryPoint(
            timestamp=now,
            risk_score=score,
            risk_level=risk_level,
            confidence=confidence,
        )
    )

    return response


# ============================================================
# GET LATEST RISK
# ============================================================


@router.get(
    "/latest",
    response_model=RiskAssessmentResponse,
)
async def get_latest_risk(
    region_id: str | None = Query(
        default=None,
        description="Optional region filter.",
    ),
) -> RiskAssessmentResponse:
    """
    Retrieve the latest risk assessment.
    """

    assessments = list(
        _RISK_ASSESSMENTS.values()
    )

    if region_id is not None:
        assessments = [
            assessment
            for assessment in assessments
            if assessment.region_id == region_id
        ]

    if not assessments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No risk assessment is available.",
        )

    assessments.sort(
        key=lambda assessment: assessment.calculated_at,
        reverse=True,
    )

    return assessments[0]


# ============================================================
# GET ASSESSMENT BY ID
# ============================================================


@router.get(
    "/assessments/{assessment_id}",
    response_model=RiskAssessmentResponse,
)
async def get_risk_assessment(
    assessment_id: str,
) -> RiskAssessmentResponse:
    """
    Retrieve a risk assessment by ID.
    """

    assessment = _RISK_ASSESSMENTS.get(
        assessment_id
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Risk assessment '{assessment_id}' was not found."
            ),
        )

    return assessment


# ============================================================
# RISK HISTORY
# ============================================================


@router.get(
    "/history",
    response_model=list[RiskHistoryPoint],
)
async def get_risk_history(
    limit: int = Query(
        default=100,
        ge=1,
        le=5000,
        description="Maximum number of historical observations.",
    ),
) -> list[RiskHistoryPoint]:
    """
    Return historical risk observations.

    Production implementation will query the time-series database.
    """

    history = sorted(
        _RISK_HISTORY,
        key=lambda point: point.timestamp,
        reverse=True,
    )

    return history[:limit]


# ============================================================
# RISK FACTORS
# ============================================================


@router.get(
    "/factors",
    response_model=list[RiskFactor],
)
async def get_current_risk_factors(
    region_id: str | None = Query(
        default=None,
    ),
) -> list[RiskFactor]:
    """
    Return the factors contributing to the latest risk assessment.
    """

    assessments = list(
        _RISK_ASSESSMENTS.values()
    )

    if region_id is not None:
        assessments = [
            assessment
            for assessment in assessments
            if assessment.region_id == region_id
        ]

    if not assessments:
        return []

    assessments.sort(
        key=lambda assessment: assessment.calculated_at,
        reverse=True,
    )

    return assessments[0].risk_factors


# ============================================================
# RISK SUMMARY
# ============================================================


@router.get(
    "/summary",
    response_model=RiskSummaryResponse,
)
async def get_risk_summary(
    region_id: str | None = Query(
        default=None,
    ),
) -> RiskSummaryResponse:
    """
    Return a summary of current and historical risk.
    """

    assessments = list(
        _RISK_ASSESSMENTS.values()
    )

    if region_id is not None:
        assessments = [
            assessment
            for assessment in assessments
            if assessment.region_id == region_id
        ]

    if not assessments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No risk data is available.",
        )

    scores = [
        assessment.risk_score
        for assessment in assessments
    ]

    assessments.sort(
        key=lambda assessment: assessment.calculated_at,
        reverse=True,
    )

    latest = assessments[0]

    trend = "stable"

    if len(scores) >= 2:
        newest = scores[0]
        oldest = scores[-1]

        difference = newest - oldest

        if difference >= 10:
            trend = "increasing"

        elif difference <= -10:
            trend = "decreasing"

    return RiskSummaryResponse(
        region_id=latest.region_id,
        region_name=latest.region_name,
        current_score=latest.risk_score,
        current_level=latest.risk_level,
        average_score=sum(scores) / len(scores),
        maximum_score=max(scores),
        minimum_score=min(scores),
        trend=trend,
        observations=len(scores),
        calculated_at=latest.calculated_at,
    )


# ============================================================
# RISK TYPES
# ============================================================


@router.get(
    "/types",
    response_model=list[str],
)
async def get_risk_types() -> list[str]:
    """
    Return all supported risk categories.
    """

    return [
        risk_type.value
        for risk_type in RiskType
    ]


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "router",
    "RiskLevel",
    "RiskType",
    "RiskAssessmentRequest",
    "RiskFactor",
    "RiskAssessmentResponse",
    "RiskHistoryPoint",
    "RiskSummaryResponse",
]