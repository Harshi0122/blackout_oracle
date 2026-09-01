"""
Blackout Oracle - Weather Database Model.

Stores weather observations and weather-derived risk information
associated with monitored grid regions and electrical assets.

Weather information can be used for:

- Weather-aware blackout prediction
- Flood-risk assessment
- Storm-risk assessment
- Extreme-temperature analysis
- Transmission-line risk analysis
- Substation risk analysis
- Transformer thermal-risk analysis
- Asset failure prediction
- Cascading-failure analysis
- Grid simulation
- AI investigation and recommendations

Weather data may originate from:

- Weather APIs
- Government weather services
- Meteorological stations
- Satellite-derived datasets
- IoT sensors
- External data providers
- Historical datasets

IMPORTANT
---------

This model stores environmental observations and analytical risk
information.

It does NOT directly control physical electrical-grid equipment.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# ============================================================
# ENUMS
# ============================================================


class WeatherSource:
    """
    Source of weather information.
    """

    WEATHER_API = "weather_api"
    GOVERNMENT = "government"
    METEOROLOGICAL_STATION = "meteorological_station"
    SATELLITE = "satellite"
    IOT_SENSOR = "iot_sensor"
    EXTERNAL_API = "external_api"
    HISTORICAL_DATASET = "historical_dataset"
    SIMULATION = "simulation"
    MANUAL = "manual"
    UNKNOWN = "unknown"


class WeatherCondition:
    """
    High-level weather condition.
    """

    CLEAR = "clear"
    CLOUDY = "cloudy"
    PARTLY_CLOUDY = "partly_cloudy"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    THUNDERSTORM = "thunderstorm"
    STORM = "storm"
    CYCLONE = "cyclone"
    FLOOD = "flood"
    HEATWAVE = "heatwave"
    OTHER = "other"
    UNKNOWN = "unknown"


class WeatherSeverity:
    """
    Severity of the weather event.
    """

    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"
    CRITICAL = "critical"


class WeatherDataQuality:
    """
    Quality of the weather observation.
    """

    GOOD = "good"
    WARNING = "warning"
    BAD = "bad"
    STALE = "stale"
    ESTIMATED = "estimated"
    SIMULATED = "simulated"
    UNKNOWN = "unknown"


# ============================================================
# WEATHER MODEL
# ============================================================


class Weather(Base):
    """
    SQLAlchemy model representing a weather observation and its
    associated grid-risk factors.
    """

    __tablename__ = "weather"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"WTH-{uuid4().hex[:12].upper()}"
        ),
    )

    # ========================================================
    # SOURCE INFORMATION
    # ========================================================

    source: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default=WeatherSource.UNKNOWN,
        index=True,
    )

    source_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    station_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    station_name: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    # ========================================================
    # LOCATION
    # ========================================================

    region_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    region_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    elevation_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # WEATHER CONDITION
    # ========================================================

    condition: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default=WeatherCondition.UNKNOWN,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=WeatherSeverity.NONE,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # TEMPERATURE
    # ========================================================

    temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    feels_like_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    apparent_temperature_c: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    minimum_temperature_c: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    maximum_temperature_c: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    temperature_anomaly_c: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    heat_index_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # HUMIDITY
    # ========================================================

    humidity_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    dew_point_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # PRECIPITATION
    # ========================================================

    rainfall_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rainfall_1h_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rainfall_3h_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rainfall_6h_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rainfall_12h_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rainfall_24h_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    precipitation_probability: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # WIND
    # ========================================================

    wind_speed_kmh: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    wind_gust_kmh: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    wind_direction_degrees: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # ATMOSPHERIC PRESSURE
    # ========================================================

    pressure_hpa: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    pressure_change_hpa: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # VISIBILITY / CLOUD COVER
    # ========================================================

    visibility_km: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    cloud_cover_percent: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # STORM INFORMATION
    # ========================================================

    thunderstorm_probability: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    lightning_probability: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    storm_probability: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    storm_distance_km: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    cyclone_probability: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # FLOOD INFORMATION
    # ========================================================

    flood_probability: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
        index=True,
    )

    flood_risk_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
        index=True,
    )

    water_level_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    water_level_change_m: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    soil_moisture_percent: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # WEATHER RISK
    # ========================================================

    weather_risk_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
        index=True,
    )

    temperature_risk_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    rainfall_risk_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    wind_risk_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    storm_risk_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    lightning_risk_score: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # GRID IMPACT ESTIMATION
    # ========================================================

    estimated_asset_failure_probability: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    estimated_transmission_risk: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    estimated_substation_risk: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    estimated_transformer_risk: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    estimated_feeder_risk: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # GRID ASSET RELATION
    # ========================================================

    asset_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    asset_type: Mapped[str | None] = mapped_column(
        String(60),
        nullable=True,
        index=True,
    )

    substation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    feeder_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    transmission_line_id: Mapped[
        str | None
    ] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    transformer_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # ========================================================
    # FORECAST INFORMATION
    # ========================================================

    is_forecast: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    forecast_hours: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    forecast_probability: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # DATA QUALITY
    # ========================================================

    quality: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=WeatherDataQuality.UNKNOWN,
        index=True,
    )

    quality_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    is_estimated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_simulated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # ========================================================
    # AI ANALYSIS
    # ========================================================

    ai_analyzed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    ai_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ai_grid_impact: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ai_model_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    ai_model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ========================================================
    # CORRELATION
    # ========================================================

    request_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    correlation_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    # ========================================================
    # ADDITIONAL DATA
    # ========================================================

    raw_payload_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        onupdate=lambda: datetime.now(
            timezone.utc
        ),
    )

    # ========================================================
    # DATABASE INDEXES
    # ========================================================

    __table_args__ = (
        Index(
            "ix_weather_region_observed",
            "region_id",
            "observed_at",
        ),
        Index(
            "ix_weather_station_observed",
            "station_id",
            "observed_at",
        ),
        Index(
            "ix_weather_asset_observed",
            "asset_id",
            "observed_at",
        ),
        Index(
            "ix_weather_condition_severity",
            "condition",
            "severity",
        ),
        Index(
            "ix_weather_risk",
            "weather_risk_score",
            "flood_risk_score",
        ),
        Index(
            "ix_weather_storm",
            "storm_probability",
            "storm_risk_score",
        ),
        Index(
            "ix_weather_forecast",
            "is_forecast",
            "forecast_hours",
        ),
        Index(
            "ix_weather_quality",
            "quality",
            "is_valid",
        ),
        Index(
            "ix_weather_location",
            "latitude",
            "longitude",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<Weather("
            f"id='{self.id}', "
            f"region='{self.region_id}', "
            f"condition='{self.condition}', "
            f"temperature={self.temperature_c}, "
            f"rainfall={self.rainfall_mm}, "
            f"risk={self.weather_risk_score}"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Weather",
    "WeatherSource",
    "WeatherCondition",
    "WeatherSeverity",
    "WeatherDataQuality",
]