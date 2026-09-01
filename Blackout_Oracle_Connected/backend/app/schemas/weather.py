"""
Blackout Oracle - Weather Schemas.

Pydantic schemas for weather observations, forecasts, severe
weather events, weather-grid correlation, and weather-related
risk inputs.

These schemas are independent of SQLAlchemy models and can be
used by ingestion, API, ML, risk, and incident layers.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# ENUMS
# ============================================================


class WeatherCondition(str, Enum):
    """General weather conditions."""

    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    THUNDERSTORM = "thunderstorm"
    CYCLONE = "cyclone"
    FLOOD = "flood"
    FOG = "fog"
    DUST_STORM = "dust_storm"
    HEATWAVE = "heatwave"
    COLD_WAVE = "cold_wave"
    HIGH_WIND = "high_wind"
    UNKNOWN = "unknown"


class WeatherSeverity(str, Enum):
    """Severity of a weather event."""

    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


class WeatherSource(str, Enum):
    """Source of weather information."""

    IMD = "imd"
    OPENWEATHER = "openweather"
    WEATHER_API = "weather_api"
    SATELLITE = "satellite"
    RADAR = "radar"
    SENSOR = "sensor"
    HISTORICAL = "historical"
    SYNTHETIC = "synthetic"
    OTHER = "other"


class WeatherEventType(str, Enum):
    """Types of severe weather events."""

    HEAVY_RAIN = "heavy_rain"
    THUNDERSTORM = "thunderstorm"
    LIGHTNING = "lightning"
    HIGH_WIND = "high_wind"
    CYCLONE = "cyclone"
    FLOOD = "flood"
    EXTREME_HEAT = "extreme_heat"
    EXTREME_COLD = "extreme_cold"
    DROUGHT = "drought"
    FOG = "fog"
    DUST_STORM = "dust_storm"
    OTHER = "other"


# ============================================================
# WEATHER LOCATION
# ============================================================


class WeatherLocation(BaseModel):
    """
    Geographic location associated with weather data.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
    )

    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
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

    city: str | None = Field(
        default=None,
        max_length=100,
    )


# ============================================================
# BASE WEATHER
# ============================================================


class WeatherBase(BaseModel):
    """
    Common weather observation fields.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    timestamp: datetime

    location: WeatherLocation

    condition: WeatherCondition = (
        WeatherCondition.UNKNOWN
    )

    temperature_c: float | None = None

    feels_like_c: float | None = None

    humidity_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    pressure_hpa: float | None = Field(
        default=None,
        gt=0.0,
    )

    wind_speed_kmh: float | None = Field(
        default=None,
        ge=0.0,
    )

    wind_direction_deg: float | None = Field(
        default=None,
        ge=0.0,
        le=360.0,
    )

    wind_gust_kmh: float | None = Field(
        default=None,
        ge=0.0,
    )

    precipitation_mm: float | None = Field(
        default=None,
        ge=0.0,
    )

    precipitation_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    cloud_cover_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    visibility_km: float | None = Field(
        default=None,
        ge=0.0,
    )

    source: WeatherSource = (
        WeatherSource.OTHER
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# WEATHER OBSERVATION
# ============================================================


class WeatherObservation(WeatherBase):
    """
    Current or historical weather observation.
    """

    observation_id: str | None = Field(
        default=None,
        max_length=255,
    )

    source_timestamp: datetime | None = None

    quality_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )


class WeatherCreate(WeatherObservation):
    """
    Schema used to ingest a weather observation.
    """

    pass


class WeatherResponse(WeatherObservation):
    """
    API response representing a stored weather observation.
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

    created_at: datetime | None = None

    updated_at: datetime | None = None


# ============================================================
# WEATHER FORECAST
# ============================================================


class WeatherForecastPoint(BaseModel):
    """
    Forecast for a specific future time.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    timestamp: datetime

    condition: WeatherCondition = (
        WeatherCondition.UNKNOWN
    )

    temperature_c: float | None = None

    feels_like_c: float | None = None

    humidity_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    pressure_hpa: float | None = Field(
        default=None,
        gt=0.0,
    )

    wind_speed_kmh: float | None = Field(
        default=None,
        ge=0.0,
    )

    wind_direction_deg: float | None = Field(
        default=None,
        ge=0.0,
        le=360.0,
    )

    wind_gust_kmh: float | None = Field(
        default=None,
        ge=0.0,
    )

    precipitation_mm: float | None = Field(
        default=None,
        ge=0.0,
    )

    precipitation_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    cloud_cover_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    severe_weather_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class WeatherForecast(BaseModel):
    """
    Weather forecast covering a future time range.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    location: WeatherLocation

    generated_at: datetime

    source: WeatherSource

    points: list[WeatherForecastPoint] = Field(
        default_factory=list,
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
# SEVERE WEATHER EVENT
# ============================================================


class SevereWeatherEvent(BaseModel):
    """
    Severe weather event that may affect grid infrastructure.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    event_id: str | None = Field(
        default=None,
        max_length=255,
    )

    event_type: WeatherEventType

    severity: WeatherSeverity

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    location: WeatherLocation

    start_time: datetime

    end_time: datetime | None = None

    probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    wind_speed_kmh: float | None = Field(
        default=None,
        ge=0.0,
    )

    precipitation_mm: float | None = Field(
        default=None,
        ge=0.0,
    )

    source: WeatherSource

    source_id: str | None = Field(
        default=None,
        max_length=255,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# GRID WEATHER IMPACT
# ============================================================


class WeatherGridImpact(BaseModel):
    """
    Estimated impact of weather conditions on grid assets.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    asset_id: int = Field(
        ...,
        ge=1,
    )

    risk_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
    )

    failure_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    expected_loading_increase_percent: float | None = None

    expected_capacity_reduction_percent: float | None = None

    affected: bool = False

    reasons: list[str] = Field(
        default_factory=list,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# WEATHER RISK
# ============================================================


class WeatherRiskRequest(BaseModel):
    """
    Request for evaluating weather-related grid risk.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    location: WeatherLocation

    forecast: WeatherForecastPoint | None = None

    event: SevereWeatherEvent | None = None

    asset_ids: list[int] = Field(
        default_factory=list,
    )

    horizon_hours: float = Field(
        default=24.0,
        gt=0.0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class WeatherRiskResponse(BaseModel):
    """
    Weather-related grid-risk assessment.
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

    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    severity: WeatherSeverity

    affected_assets: list[int] = Field(
        default_factory=list,
    )

    impacts: list[WeatherGridImpact] = Field(
        default_factory=list,
    )

    factors: dict[str, float] = Field(
        default_factory=dict,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )

    assessed_at: datetime

    valid_until: datetime | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# WEATHER QUERY
# ============================================================


class WeatherQuery(BaseModel):
    """
    Query parameters for weather observations and forecasts.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
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

    source: WeatherSource | None = None

    condition: WeatherCondition | None = None

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
# WEATHER ALERT
# ============================================================


class WeatherAlert(BaseModel):
    """
    Weather alert relevant to grid operations.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    alert_id: str | None = Field(
        default=None,
        max_length=255,
    )

    event_type: WeatherEventType

    severity: WeatherSeverity

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )

    location: WeatherLocation

    issued_at: datetime

    expires_at: datetime | None = None

    probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    grid_risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    affected_asset_count: int = Field(
        default=0,
        ge=0,
    )

    source: WeatherSource

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# WEATHER LIST RESPONSE
# ============================================================


class WeatherListResponse(BaseModel):
    """
    Paginated weather observation response.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[WeatherResponse] = Field(
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
# WEATHER SUMMARY
# ============================================================


class WeatherSummary(BaseModel):
    """
    High-level weather summary for a grid region.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    location: WeatherLocation

    timestamp: datetime

    condition: WeatherCondition

    temperature_c: float | None = None

    rainfall_mm: float | None = Field(
        default=None,
        ge=0.0,
    )

    wind_speed_kmh: float | None = Field(
        default=None,
        ge=0.0,
    )

    severe_weather: bool = False

    severe_weather_severity: WeatherSeverity = (
        WeatherSeverity.NONE
    )

    grid_risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    active_alerts: int = Field(
        default=0,
        ge=0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "WeatherCondition",
    "WeatherSeverity",
    "WeatherSource",
    "WeatherEventType",
    "WeatherLocation",
    "WeatherBase",
    "WeatherObservation",
    "WeatherCreate",
    "WeatherResponse",
    "WeatherForecastPoint",
    "WeatherForecast",
    "SevereWeatherEvent",
    "WeatherGridImpact",
    "WeatherRiskRequest",
    "WeatherRiskResponse",
    "WeatherQuery",
    "WeatherAlert",
    "WeatherListResponse",
    "WeatherSummary",
]