"""
Blackout Oracle - Weather API Routes.

This module exposes API endpoints for collecting and querying environmental
conditions relevant to grid reliability and blackout prediction.

Weather inputs may include:

- Temperature
- Humidity
- Rainfall
- Wind speed
- Wind gusts
- Atmospheric pressure
- Storm conditions
- Lightning indicators
- Flood risk
- Visibility
- Weather alerts

IMPORTANT
---------

This module is an API layer only.

It does NOT directly control grid infrastructure.

Production weather data should be acquired through authorized APIs/services
and processed by a background ingestion pipeline.

The initial implementation uses an in-memory development store.
Production persistence will use the database/time-series layer.
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
    prefix="/weather",
    tags=["Weather"],
)


# ============================================================
# ENUMS
# ============================================================


class WeatherSeverity(str, Enum):
    """Severity of environmental conditions."""

    NORMAL = "normal"
    WATCH = "watch"
    WARNING = "warning"
    SEVERE = "severe"
    EXTREME = "extreme"


class WeatherSource(str, Enum):
    """Source categories for weather information."""

    SYNTHETIC = "synthetic"
    PUBLIC_API = "public_api"
    AUTHORIZED_PROVIDER = "authorized_provider"
    HISTORICAL = "historical"
    MANUAL = "manual"


# ============================================================
# REQUEST SCHEMAS
# ============================================================


class WeatherObservationCreate(BaseModel):
    """A single weather observation."""

    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
    )

    location_name: str | None = Field(
        default=None,
        max_length=200,
    )

    observed_at: datetime

    temperature_c: float | None = None

    feels_like_c: float | None = None

    humidity_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    rainfall_mm: float | None = Field(
        default=None,
        ge=0,
    )

    rainfall_rate_mm_per_hour: float | None = Field(
        default=None,
        ge=0,
    )

    wind_speed_kmh: float | None = Field(
        default=None,
        ge=0,
    )

    wind_gust_kmh: float | None = Field(
        default=None,
        ge=0,
    )

    pressure_hpa: float | None = Field(
        default=None,
        ge=0,
    )

    visibility_km: float | None = Field(
        default=None,
        ge=0,
    )

    lightning_detected: bool = False

    storm_detected: bool = False

    flood_risk: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    weather_severity: WeatherSeverity = (
        WeatherSeverity.NORMAL
    )

    source: WeatherSource = (
        WeatherSource.SYNTHETIC
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class WeatherForecastCreate(BaseModel):
    """A weather forecast observation."""

    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
    )

    location_name: str | None = Field(
        default=None,
        max_length=200,
    )

    forecast_time: datetime

    generated_at: datetime

    temperature_c: float | None = None

    rainfall_probability_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    predicted_rainfall_mm: float | None = Field(
        default=None,
        ge=0,
    )

    wind_speed_kmh: float | None = Field(
        default=None,
        ge=0,
    )

    wind_gust_kmh: float | None = Field(
        default=None,
        ge=0,
    )

    storm_probability_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    flood_probability_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    weather_severity: WeatherSeverity = (
        WeatherSeverity.NORMAL
    )

    source: WeatherSource = (
        WeatherSource.SYNTHETIC
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# RESPONSE SCHEMAS
# ============================================================


class WeatherObservationResponse(BaseModel):
    """Stored weather observation."""

    id: str

    latitude: float

    longitude: float

    location_name: str | None = None

    observed_at: datetime

    received_at: datetime

    temperature_c: float | None = None

    feels_like_c: float | None = None

    humidity_percent: float | None = None

    rainfall_mm: float | None = None

    rainfall_rate_mm_per_hour: float | None = None

    wind_speed_kmh: float | None = None

    wind_gust_kmh: float | None = None

    pressure_hpa: float | None = None

    visibility_km: float | None = None

    lightning_detected: bool

    storm_detected: bool

    flood_risk: float | None = None

    weather_severity: WeatherSeverity

    source: WeatherSource

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class WeatherForecastResponse(BaseModel):
    """Stored weather forecast."""

    id: str

    latitude: float

    longitude: float

    location_name: str | None = None

    forecast_time: datetime

    generated_at: datetime

    temperature_c: float | None = None

    rainfall_probability_percent: float | None = None

    predicted_rainfall_mm: float | None = None

    wind_speed_kmh: float | None = None

    wind_gust_kmh: float | None = None

    storm_probability_percent: float | None = None

    flood_probability_percent: float | None = None

    weather_severity: WeatherSeverity

    source: WeatherSource

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class WeatherHealthResponse(BaseModel):
    """Weather data freshness and availability."""

    available: bool

    latest_observation: datetime | None = None

    age_seconds: float | None = None

    stale: bool

    source: WeatherSource | None = None


# ============================================================
# DEVELOPMENT STORES
# ============================================================

# Temporary in-memory stores.
#
# Production:
#
# Weather API/provider
#       ↓
# Background ingestion worker
#       ↓
# Validation + normalization
#       ↓
# TimescaleDB
#       ↓
# Risk Engine
#       ↓
# Blackout Oracle Agent

_WEATHER_OBSERVATIONS: list[
    WeatherObservationResponse
] = []

_WEATHER_FORECASTS: list[
    WeatherForecastResponse
] = []


# ============================================================
# VALIDATION HELPERS
# ============================================================


def _validate_timestamp(
    timestamp: datetime,
) -> datetime:
    """
    Ensure weather timestamps contain timezone information and normalize
    them to UTC.
    """

    if timestamp.tzinfo is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Weather timestamp must include timezone information."
            ),
        )

    return timestamp.astimezone(
        timezone.utc
    )


# ============================================================
# CREATE WEATHER OBSERVATION
# ============================================================


@router.post(
    "/observations",
    response_model=WeatherObservationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_weather_observation(
    observation: WeatherObservationCreate,
) -> WeatherObservationResponse:
    """
    Store a weather observation.

    This endpoint is intended for authorized weather-data ingestion.
    """

    observed_at = _validate_timestamp(
        observation.observed_at
    )

    received_at = datetime.now(
        timezone.utc
    )

    observation_id = (
        f"WTH-{uuid4().hex[:12].upper()}"
    )

    response = WeatherObservationResponse(
        id=observation_id,
        latitude=observation.latitude,
        longitude=observation.longitude,
        location_name=observation.location_name,
        observed_at=observed_at,
        received_at=received_at,
        temperature_c=observation.temperature_c,
        feels_like_c=observation.feels_like_c,
        humidity_percent=observation.humidity_percent,
        rainfall_mm=observation.rainfall_mm,
        rainfall_rate_mm_per_hour=(
            observation.rainfall_rate_mm_per_hour
        ),
        wind_speed_kmh=observation.wind_speed_kmh,
        wind_gust_kmh=observation.wind_gust_kmh,
        pressure_hpa=observation.pressure_hpa,
        visibility_km=observation.visibility_km,
        lightning_detected=observation.lightning_detected,
        storm_detected=observation.storm_detected,
        flood_risk=observation.flood_risk,
        weather_severity=observation.weather_severity,
        source=observation.source,
        metadata=observation.metadata,
    )

    _WEATHER_OBSERVATIONS.append(
        response
    )

    return response


# ============================================================
# CREATE FORECAST
# ============================================================


@router.post(
    "/forecasts",
    response_model=WeatherForecastResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_weather_forecast(
    forecast: WeatherForecastCreate,
) -> WeatherForecastResponse:
    """
    Store a weather forecast.

    Forecasts are important because Blackout Oracle needs to reason about
    future environmental conditions, not just current weather.
    """

    forecast_time = _validate_timestamp(
        forecast.forecast_time
    )

    generated_at = _validate_timestamp(
        forecast.generated_at
    )

    forecast_id = (
        f"FCST-{uuid4().hex[:12].upper()}"
    )

    response = WeatherForecastResponse(
        id=forecast_id,
        latitude=forecast.latitude,
        longitude=forecast.longitude,
        location_name=forecast.location_name,
        forecast_time=forecast_time,
        generated_at=generated_at,
        temperature_c=forecast.temperature_c,
        rainfall_probability_percent=(
            forecast.rainfall_probability_percent
        ),
        predicted_rainfall_mm=(
            forecast.predicted_rainfall_mm
        ),
        wind_speed_kmh=forecast.wind_speed_kmh,
        wind_gust_kmh=forecast.wind_gust_kmh,
        storm_probability_percent=(
            forecast.storm_probability_percent
        ),
        flood_probability_percent=(
            forecast.flood_probability_percent
        ),
        weather_severity=forecast.weather_severity,
        source=forecast.source,
        metadata=forecast.metadata,
    )

    _WEATHER_FORECASTS.append(
        response
    )

    return response


# ============================================================
# LATEST OBSERVATION
# ============================================================


@router.get(
    "/latest",
    response_model=WeatherObservationResponse,
)
async def get_latest_weather(
    latitude: float = Query(
        ...,
        ge=-90,
        le=90,
    ),
    longitude: float = Query(
        ...,
        ge=-180,
        le=180,
    ),
) -> WeatherObservationResponse:
    """
    Return the latest weather observation near a requested coordinate.

    The production implementation will perform a geospatial query
    against the weather/time-series database.
    """

    if not _WEATHER_OBSERVATIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No weather observations are available.",
        )

    # Development implementation:
    # simply choose the most recent observation.
    #
    # Production:
    # use PostGIS/geospatial nearest-neighbor lookup.

    latest = max(
        _WEATHER_OBSERVATIONS,
        key=lambda observation: observation.observed_at,
    )

    return latest


# ============================================================
# OBSERVATION HISTORY
# ============================================================


@router.get(
    "/observations",
    response_model=list[WeatherObservationResponse],
)
async def list_weather_observations(
    start_time: datetime | None = Query(
        default=None,
    ),
    end_time: datetime | None = Query(
        default=None,
    ),
    source: WeatherSource | None = Query(
        default=None,
    ),
    severity: WeatherSeverity | None = Query(
        default=None,
    ),
    limit: int = Query(
        default=1000,
        ge=1,
        le=10000,
    ),
) -> list[WeatherObservationResponse]:
    """
    Query historical weather observations.
    """

    observations = list(
        _WEATHER_OBSERVATIONS
    )

    if start_time is not None:
        start_time = _validate_timestamp(
            start_time
        )

        observations = [
            observation
            for observation in observations
            if observation.observed_at >= start_time
        ]

    if end_time is not None:
        end_time = _validate_timestamp(
            end_time
        )

        observations = [
            observation
            for observation in observations
            if observation.observed_at <= end_time
        ]

    if source is not None:
        observations = [
            observation
            for observation in observations
            if observation.source == source
        ]

    if severity is not None:
        observations = [
            observation
            for observation in observations
            if observation.weather_severity
            == severity
        ]

    observations.sort(
        key=lambda observation: observation.observed_at,
        reverse=True,
    )

    return observations[:limit]


# ============================================================
# FORECASTS
# ============================================================


@router.get(
    "/forecasts",
    response_model=list[WeatherForecastResponse],
)
async def list_weather_forecasts(
    start_time: datetime | None = Query(
        default=None,
    ),
    end_time: datetime | None = Query(
        default=None,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
) -> list[WeatherForecastResponse]:
    """
    Return weather forecasts within a requested time range.
    """

    forecasts = list(
        _WEATHER_FORECASTS
    )

    if start_time is not None:
        start_time = _validate_timestamp(
            start_time
        )

        forecasts = [
            forecast
            for forecast in forecasts
            if forecast.forecast_time >= start_time
        ]

    if end_time is not None:
        end_time = _validate_timestamp(
            end_time
        )

        forecasts = [
            forecast
            for forecast in forecasts
            if forecast.forecast_time <= end_time
        ]

    forecasts.sort(
        key=lambda forecast: forecast.forecast_time,
    )

    return forecasts[:limit]


# ============================================================
# WEATHER HEALTH
# ============================================================


@router.get(
    "/health",
    response_model=WeatherHealthResponse,
)
async def weather_health() -> WeatherHealthResponse:
    """
    Check weather-data freshness.

    Blackout Oracle should not use stale environmental data as if it were
    real-time information.
    """

    if not _WEATHER_OBSERVATIONS:
        return WeatherHealthResponse(
            available=False,
            latest_observation=None,
            age_seconds=None,
            stale=True,
            source=None,
        )

    latest = max(
        _WEATHER_OBSERVATIONS,
        key=lambda observation: observation.observed_at,
    )

    now = datetime.now(
        timezone.utc
    )

    age_seconds = max(
        0.0,
        (
            now - latest.observed_at
        ).total_seconds(),
    )

    # Five-minute freshness threshold for development.
    stale = age_seconds > 300

    return WeatherHealthResponse(
        available=True,
        latest_observation=latest.observed_at,
        age_seconds=age_seconds,
        stale=stale,
        source=latest.source,
    )


# ============================================================
# WEATHER RISK
# ============================================================


@router.get(
    "/risk",
    response_model=dict[str, Any],
)
async def weather_risk() -> dict[str, Any]:
    """
    Produce a simple environmental-risk summary.

    IMPORTANT:

    This is a development-level summary only.

    The production environmental-risk model will combine weather forecasts,
    historical weather, infrastructure exposure, flood maps, asset
    vulnerability, and grid topology.
    """

    if not _WEATHER_OBSERVATIONS:
        return {
            "available": False,
            "risk_score": None,
            "risk_level": "unknown",
            "factors": [],
        }

    latest = max(
        _WEATHER_OBSERVATIONS,
        key=lambda observation: observation.observed_at,
    )

    score = 0.0
    factors: list[dict[str, Any]] = []

    # --------------------------------------------------------
    # Rainfall
    # --------------------------------------------------------

    if (
        latest.rainfall_rate_mm_per_hour
        is not None
        and latest.rainfall_rate_mm_per_hour >= 50
    ):
        score += 30

        factors.append(
            {
                "factor": "heavy_rainfall",
                "value": (
                    latest.rainfall_rate_mm_per_hour
                ),
                "unit": "mm/hour",
            }
        )

    # --------------------------------------------------------
    # Flood risk
    # --------------------------------------------------------

    if latest.flood_risk is not None:

        flood_contribution = (
            latest.flood_risk * 0.40
        )

        score += min(
            40,
            flood_contribution,
        )

        factors.append(
            {
                "factor": "flood_risk",
                "value": latest.flood_risk,
                "unit": "percent",
            }
        )

    # --------------------------------------------------------
    # Wind
    # --------------------------------------------------------

    if (
        latest.wind_gust_kmh is not None
        and latest.wind_gust_kmh >= 80
    ):
        score += 20

        factors.append(
            {
                "factor": "strong_wind",
                "value": latest.wind_gust_kmh,
                "unit": "km/h",
            }
        )

    # --------------------------------------------------------
    # Lightning
    # --------------------------------------------------------

    if latest.lightning_detected:
        score += 10

        factors.append(
            {
                "factor": "lightning",
                "value": True,
            }
        )

    score = min(
        100,
        score,
    )

    if score >= 80:
        risk_level = "extreme"
    elif score >= 60:
        risk_level = "severe"
    elif score >= 40:
        risk_level = "warning"
    elif score >= 20:
        risk_level = "watch"
    else:
        risk_level = "normal"

    return {
        "available": True,
        "risk_score": score,
        "risk_level": risk_level,
        "observed_at": latest.observed_at.isoformat(),
        "factors": factors,
    }


# ============================================================
# SUMMARY
# ============================================================


@router.get(
    "/summary",
    response_model=dict[str, Any],
)
async def weather_summary() -> dict[str, Any]:
    """
    Return a summary of weather data available to Blackout Oracle.
    """

    if not _WEATHER_OBSERVATIONS:
        return {
            "observations": 0,
            "forecasts": len(
                _WEATHER_FORECASTS
            ),
            "sources": {},
            "severity_counts": {},
        }

    source_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}

    for observation in _WEATHER_OBSERVATIONS:

        source_key = observation.source.value

        source_counts[
            source_key
        ] = (
            source_counts.get(
                source_key,
                0,
            )
            + 1
        )

        severity_key = (
            observation.weather_severity.value
        )

        severity_counts[
            severity_key
        ] = (
            severity_counts.get(
                severity_key,
                0,
            )
            + 1
        )

    latest = max(
        _WEATHER_OBSERVATIONS,
        key=lambda observation: observation.observed_at,
    )

    return {
        "observations": len(
            _WEATHER_OBSERVATIONS
        ),
        "forecasts": len(
            _WEATHER_FORECASTS
        ),
        "sources": source_counts,
        "severity_counts": severity_counts,
        "latest_observation": (
            latest.observed_at.isoformat()
        ),
    }


# ============================================================
# DEVELOPMENT DATA RESET
# ============================================================


@router.delete(
    "/development/clear",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_development_weather() -> None:
    """
    Clear development weather data.

    DEVELOPMENT ONLY.

    Remove or disable this endpoint before production deployment.
    """

    _WEATHER_OBSERVATIONS.clear()
    _WEATHER_FORECASTS.clear()


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "router",
    "WeatherSeverity",
    "WeatherSource",
    "WeatherObservationCreate",
    "WeatherForecastCreate",
    "WeatherObservationResponse",
    "WeatherForecastResponse",
    "WeatherHealthResponse",
]