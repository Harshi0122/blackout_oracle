"""
Blackout Oracle - Weather Service.

Application-level service for weather observations, forecasts,
severe-weather analysis, and weather-related grid risk.

This service coordinates weather data with the rest of the
Blackout Oracle application without directly depending on any
specific external weather provider.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from app.schemas.weather import (
    SevereWeatherEvent,
    WeatherAlert,
    WeatherCondition,
    WeatherForecast,
    WeatherForecastPoint,
    WeatherGridImpact,
    WeatherLocation,
    WeatherObservation,
    WeatherRiskRequest,
    WeatherRiskResponse,
    WeatherSeverity,
    WeatherSource,
)


class WeatherService:
    """
    High-level service for weather-related application operations.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        source: Any | None = None,
    ) -> None:
        """
        Initialize the weather service.

        `source` may be any weather adapter implementing one of the
        commonly supported methods such as `get_current`,
        `get_forecast`, or `get_weather`.
        """

        self.source = source

    # ========================================================
    # LOCATION
    # ========================================================

    @staticmethod
    def validate_location(
        location: WeatherLocation,
    ) -> WeatherLocation:
        """
        Validate and normalize a weather location.
        """

        if not (
            -90.0
            <= float(location.latitude)
            <= 90.0
        ):
            raise ValueError(
                "Latitude must be between -90 and 90."
            )

        if not (
            -180.0
            <= float(location.longitude)
            <= 180.0
        ):
            raise ValueError(
                "Longitude must be between -180 and 180."
            )

        return location

    # ========================================================
    # CURRENT WEATHER
    # ========================================================

    def get_current_weather(
        self,
        location: WeatherLocation,
    ) -> WeatherObservation | None:
        """
        Fetch current weather from the configured source.

        Returns None when no source is configured or the source
        cannot provide a current observation.
        """

        self.validate_location(location)

        if self.source is None:
            return None

        methods = (
            "get_current",
            "get_current_weather",
            "get_weather",
            "fetch_current",
            "fetch_current_weather",
        )

        for method_name in methods:
            method = getattr(
                self.source,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:
                result = method(location)
            except TypeError:
                try:
                    result = method(
                        latitude=location.latitude,
                        longitude=location.longitude,
                    )
                except TypeError:
                    continue

            if result is None:
                return None

            if isinstance(
                result,
                WeatherObservation,
            ):
                return result

            if isinstance(
                result,
                dict,
            ):
                return self._observation_from_dict(
                    result,
                    location,
                )

            return self._observation_from_object(
                result,
                location,
            )

        return None

    # ========================================================
    # FORECAST
    # ========================================================

    def get_forecast(
        self,
        location: WeatherLocation,
        *,
        hours: int = 24,
    ) -> WeatherForecast | None:
        """
        Fetch a weather forecast from the configured source.
        """

        self.validate_location(location)

        if hours < 1:
            raise ValueError(
                "Forecast hours must be at least 1."
            )

        if self.source is None:
            return None

        methods = (
            "get_forecast",
            "get_weather_forecast",
            "fetch_forecast",
            "fetch_weather_forecast",
        )

        for method_name in methods:
            method = getattr(
                self.source,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:
                result = method(
                    location,
                    hours=hours,
                )
            except TypeError:
                try:
                    result = method(
                        latitude=location.latitude,
                        longitude=location.longitude,
                        hours=hours,
                    )
                except TypeError:
                    try:
                        result = method(location)
                    except TypeError:
                        continue

            if result is None:
                return None

            if isinstance(
                result,
                WeatherForecast,
            ):
                return result

            return self._forecast_from_result(
                result,
                location,
            )

        return None

    # ========================================================
    # SOURCE HELPERS
    # ========================================================

    @staticmethod
    def _get_value(
        obj: Any,
        *names: str,
        default: Any = None,
    ) -> Any:
        """
        Extract a value from a dictionary or object.
        """

        if obj is None:
            return default

        if isinstance(
            obj,
            dict,
        ):
            for name in names:
                if name in obj:
                    return obj[name]

            return default

        for name in names:
            value = getattr(
                obj,
                name,
                None,
            )

            if value is not None:
                return value

        return default

    @staticmethod
    def _to_float(
        value: Any,
        default: float | None = None,
    ) -> float | None:
        """
        Safely convert a value to float.
        """

        if value is None:
            return default

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return default

    @staticmethod
    def _to_datetime(
        value: Any,
        default: datetime | None = None,
    ) -> datetime | None:
        """
        Safely convert a value to datetime.
        """

        if value is None:
            return default

        if isinstance(
            value,
            datetime,
        ):
            return value

        if isinstance(
            value,
            str,
        ):
            try:
                return datetime.fromisoformat(
                    value.replace(
                        "Z",
                        "+00:00",
                    )
                )
            except ValueError:
                return default

        return default

    # ========================================================
    # CONDITION NORMALIZATION
    # ========================================================

    @staticmethod
    def normalize_condition(
        condition: Any,
    ) -> WeatherCondition:
        """
        Convert a provider-specific weather condition into the
        application's standard condition enum.
        """

        if isinstance(
            condition,
            WeatherCondition,
        ):
            return condition

        value = str(
            condition or ""
        ).strip().lower()

        mappings = {
            "clear": WeatherCondition.CLEAR,
            "sunny": WeatherCondition.CLEAR,
            "partly cloudy": WeatherCondition.PARTLY_CLOUDY,
            "partly_cloudy": WeatherCondition.PARTLY_CLOUDY,
            "cloudy": WeatherCondition.CLOUDY,
            "overcast": WeatherCondition.OVERCAST,
            "rain": WeatherCondition.RAIN,
            "rainy": WeatherCondition.RAIN,
            "heavy rain": WeatherCondition.HEAVY_RAIN,
            "heavy_rain": WeatherCondition.HEAVY_RAIN,
            "thunderstorm": WeatherCondition.THUNDERSTORM,
            "storm": WeatherCondition.THUNDERSTORM,
            "cyclone": WeatherCondition.CYCLONE,
            "flood": WeatherCondition.FLOOD,
            "fog": WeatherCondition.FOG,
            "dust storm": WeatherCondition.DUST_STORM,
            "dust_storm": WeatherCondition.DUST_STORM,
            "heatwave": WeatherCondition.HEATWAVE,
            "heat wave": WeatherCondition.HEATWAVE,
            "cold wave": WeatherCondition.COLD_WAVE,
            "cold_wave": WeatherCondition.COLD_WAVE,
            "high wind": WeatherCondition.HIGH_WIND,
            "high_wind": WeatherCondition.HIGH_WIND,
        }

        return mappings.get(
            value,
            WeatherCondition.UNKNOWN,
        )

    # ========================================================
    # OBSERVATION NORMALIZATION
    # ========================================================

    def _observation_from_dict(
        self,
        data: dict[str, Any],
        location: WeatherLocation,
    ) -> WeatherObservation:
        """
        Convert provider dictionary data into a normalized
        WeatherObservation.
        """

        timestamp = self._to_datetime(
            self._get_value(
                data,
                "timestamp",
                "time",
                "datetime",
            ),
            default=datetime.now(
                timezone.utc
            ),
        )

        condition = self.normalize_condition(
            self._get_value(
                data,
                "condition",
                "weather",
                "description",
            )
        )

        source_value = self._get_value(
            data,
            "source",
        )

        try:
            source = WeatherSource(
                str(source_value).lower()
            )
        except ValueError:
            source = WeatherSource.OTHER

        return WeatherObservation(
            timestamp=timestamp,
            location=location,
            condition=condition,
            temperature_c=self._to_float(
                self._get_value(
                    data,
                    "temperature_c",
                    "temperature",
                    "temp",
                )
            ),
            feels_like_c=self._to_float(
                self._get_value(
                    data,
                    "feels_like_c",
                    "feels_like",
                )
            ),
            humidity_percent=self._to_float(
                self._get_value(
                    data,
                    "humidity_percent",
                    "humidity",
                )
            ),
            pressure_hpa=self._to_float(
                self._get_value(
                    data,
                    "pressure_hpa",
                    "pressure",
                )
            ),
            wind_speed_kmh=self._to_float(
                self._get_value(
                    data,
                    "wind_speed_kmh",
                    "wind_speed",
                )
            ),
            wind_direction_deg=self._to_float(
                self._get_value(
                    data,
                    "wind_direction_deg",
                    "wind_direction",
                )
            ),
            wind_gust_kmh=self._to_float(
                self._get_value(
                    data,
                    "wind_gust_kmh",
                    "wind_gust",
                )
            ),
            precipitation_mm=self._to_float(
                self._get_value(
                    data,
                    "precipitation_mm",
                    "precipitation",
                    "rainfall",
                )
            ),
            precipitation_probability=self._to_float(
                self._get_value(
                    data,
                    "precipitation_probability",
                    "rain_probability",
                )
            ),
            cloud_cover_percent=self._to_float(
                self._get_value(
                    data,
                    "cloud_cover_percent",
                    "cloud_cover",
                )
            ),
            visibility_km=self._to_float(
                self._get_value(
                    data,
                    "visibility_km",
                    "visibility",
                )
            ),
            source=source,
            source_id=self._get_value(
                data,
                "source_id",
                "id",
            ),
            metadata=dict(
                self._get_value(
                    data,
                    "metadata",
                    default={},
                )
                or {}
            ),
        )

    def _observation_from_object(
        self,
        data: Any,
        location: WeatherLocation,
    ) -> WeatherObservation:
        """
        Convert an arbitrary weather-provider object into a
        normalized observation.
        """

        values = {
            "timestamp": self._get_value(
                data,
                "timestamp",
                "time",
                "datetime",
            ),
            "condition": self._get_value(
                data,
                "condition",
                "weather",
                "description",
            ),
            "temperature": self._get_value(
                data,
                "temperature_c",
                "temperature",
                "temp",
            ),
            "humidity": self._get_value(
                data,
                "humidity_percent",
                "humidity",
            ),
            "pressure": self._get_value(
                data,
                "pressure_hpa",
                "pressure",
            ),
            "wind_speed": self._get_value(
                data,
                "wind_speed_kmh",
                "wind_speed",
            ),
            "wind_direction": self._get_value(
                data,
                "wind_direction_deg",
                "wind_direction",
            ),
            "precipitation": self._get_value(
                data,
                "precipitation_mm",
                "precipitation",
                "rainfall",
            ),
            "cloud_cover": self._get_value(
                data,
                "cloud_cover_percent",
                "cloud_cover",
            ),
            "source": self._get_value(
                data,
                "source",
            ),
        }

        return self._observation_from_dict(
            values,
            location,
        )

    # ========================================================
    # FORECAST NORMALIZATION
    # ========================================================

    def _forecast_from_result(
        self,
        result: Any,
        location: WeatherLocation,
    ) -> WeatherForecast:
        """
        Normalize a provider forecast response.
        """

        if isinstance(
            result,
            dict,
        ):
            raw_points = self._get_value(
                result,
                "points",
                "forecast",
                "data",
                default=[],
            )

            generated_at = self._to_datetime(
                self._get_value(
                    result,
                    "generated_at",
                    "created_at",
                ),
                default=datetime.now(
                    timezone.utc
                ),
            )

            source_value = self._get_value(
                result,
                "source",
            )
        else:
            raw_points = self._get_value(
                result,
                "points",
                "forecast",
                "data",
                default=[],
            )

            generated_at = self._to_datetime(
                self._get_value(
                    result,
                    "generated_at",
                    "created_at",
                ),
                default=datetime.now(
                    timezone.utc
                ),
            )

            source_value = self._get_value(
                result,
                "source",
            )

        if raw_points is None:
            raw_points = []

        points: list[WeatherForecastPoint] = []

        for raw_point in raw_points:
            point = self._forecast_point_from_result(
                raw_point
            )

            if point is not None:
                points.append(point)

        try:
            source = WeatherSource(
                str(
                    source_value
                    or WeatherSource.OTHER.value
                ).lower()
            )
        except ValueError:
            source = WeatherSource.OTHER

        return WeatherForecast(
            location=location,
            generated_at=generated_at,
            source=source,
            points=points,
            model_name=(
                self._get_value(
                    result,
                    "model_name",
                )
                if not isinstance(
                    result,
                    list,
                )
                else None
            ),
            model_version=(
                self._get_value(
                    result,
                    "model_version",
                )
                if not isinstance(
                    result,
                    list,
                )
                else None
            ),
        )

    def _forecast_point_from_result(
        self,
        data: Any,
    ) -> WeatherForecastPoint | None:
        """
        Normalize one forecast point.
        """

        timestamp = self._to_datetime(
            self._get_value(
                data,
                "timestamp",
                "time",
                "datetime",
            )
        )

        if timestamp is None:
            return None

        return WeatherForecastPoint(
            timestamp=timestamp,
            condition=self.normalize_condition(
                self._get_value(
                    data,
                    "condition",
                    "weather",
                    "description",
                )
            ),
            temperature_c=self._to_float(
                self._get_value(
                    data,
                    "temperature_c",
                    "temperature",
                    "temp",
                )
            ),
            feels_like_c=self._to_float(
                self._get_value(
                    data,
                    "feels_like_c",
                    "feels_like",
                )
            ),
            humidity_percent=self._to_float(
                self._get_value(
                    data,
                    "humidity_percent",
                    "humidity",
                )
            ),
            pressure_hpa=self._to_float(
                self._get_value(
                    data,
                    "pressure_hpa",
                    "pressure",
                )
            ),
            wind_speed_kmh=self._to_float(
                self._get_value(
                    data,
                    "wind_speed_kmh",
                    "wind_speed",
                )
            ),
            wind_direction_deg=self._to_float(
                self._get_value(
                    data,
                    "wind_direction_deg",
                    "wind_direction",
                )
            ),
            wind_gust_kmh=self._to_float(
                self._get_value(
                    data,
                    "wind_gust_kmh",
                    "wind_gust",
                )
            ),
            precipitation_mm=self._to_float(
                self._get_value(
                    data,
                    "precipitation_mm",
                    "precipitation",
                    "rainfall",
                )
            ),
            precipitation_probability=self._to_float(
                self._get_value(
                    data,
                    "precipitation_probability",
                    "rain_probability",
                )
            ),
            cloud_cover_percent=self._to_float(
                self._get_value(
                    data,
                    "cloud_cover_percent",
                    "cloud_cover",
                )
            ),
            severe_weather_probability=self._to_float(
                self._get_value(
                    data,
                    "severe_weather_probability",
                    "severe_probability",
                )
            ),
            metadata=dict(
                self._get_value(
                    data,
                    "metadata",
                    default={},
                )
                or {}
            ),
        )

    # ========================================================
    # SEVERE WEATHER
    # ========================================================

    @staticmethod
    def classify_severity(
        *,
        wind_speed_kmh: float | None = None,
        precipitation_mm: float | None = None,
        probability: float | None = None,
        condition: WeatherCondition | str | None = None,
    ) -> WeatherSeverity:
        """
        Estimate weather-event severity using deterministic
        thresholds.

        These thresholds are screening values, not official
        meteorological warnings.
        """

        wind = float(
            wind_speed_kmh or 0.0
        )

        rain = float(
            precipitation_mm or 0.0
        )

        probability = max(
            0.0,
            min(
                1.0,
                float(
                    probability
                    if probability is not None
                    else 0.0
                ),
            ),
        )

        try:
            condition_value = WeatherCondition(
                str(
                    condition.value
                    if isinstance(
                        condition,
                        WeatherCondition,
                    )
                    else condition
                    or ""
                ).lower()
            )
        except ValueError:
            condition_value = WeatherCondition.UNKNOWN

        if condition_value in {
            WeatherCondition.CYCLONE,
            WeatherCondition.FLOOD,
        }:
            return WeatherSeverity.EXTREME

        if (
            wind >= 100.0
            or rain >= 100.0
        ):
            return WeatherSeverity.EXTREME

        if (
            wind >= 75.0
            or rain >= 50.0
            or probability >= 0.85
            or condition_value
            == WeatherCondition.THUNDERSTORM
        ):
            return WeatherSeverity.HIGH

        if (
            wind >= 50.0
            or rain >= 25.0
            or probability >= 0.60
        ):
            return WeatherSeverity.MODERATE

        if (
            wind >= 30.0
            or rain >= 10.0
            or probability >= 0.30
        ):
            return WeatherSeverity.LOW

        return WeatherSeverity.NONE

    # ========================================================
    # WEATHER RISK
    # ========================================================

    @classmethod
    def calculate_weather_risk(
        cls,
        observation: WeatherObservation | None = None,
        forecast: WeatherForecastPoint | None = None,
        event: SevereWeatherEvent | None = None,
    ) -> float:
        """
        Calculate a normalized weather-risk score from 0 to 100.
        """

        scores: list[float] = []

        data_points = [
            observation,
            forecast,
        ]

        for data in data_points:
            if data is None:
                continue

            wind = float(
                getattr(
                    data,
                    "wind_speed_kmh",
                    0.0,
                )
                or 0.0
            )

            gust = float(
                getattr(
                    data,
                    "wind_gust_kmh",
                    0.0,
                )
                or 0.0
            )

            rain = float(
                getattr(
                    data,
                    "precipitation_mm",
                    0.0,
                )
                or 0.0
            )

            rain_probability = float(
                getattr(
                    data,
                    "precipitation_probability",
                    0.0,
                )
                or 0.0
            )

            wind_score = min(
                100.0,
                wind / 100.0 * 100.0,
            )

            gust_score = min(
                100.0,
                gust / 120.0 * 100.0,
            )

            rain_score = min(
                100.0,
                rain / 100.0 * 100.0,
            )

            probability_score = (
                rain_probability * 100.0
            )

            condition = getattr(
                data,
                "condition",
                WeatherCondition.UNKNOWN,
            )

            condition_score = {
                WeatherCondition.CLEAR: 0.0,
                WeatherCondition.PARTLY_CLOUDY: 5.0,
                WeatherCondition.CLOUDY: 10.0,
                WeatherCondition.OVERCAST: 15.0,
                WeatherCondition.RAIN: 30.0,
                WeatherCondition.HEAVY_RAIN: 65.0,
                WeatherCondition.THUNDERSTORM: 80.0,
                WeatherCondition.CYCLONE: 100.0,
                WeatherCondition.FLOOD: 100.0,
                WeatherCondition.FOG: 25.0,
                WeatherCondition.DUST_STORM: 60.0,
                WeatherCondition.HEATWAVE: 55.0,
                WeatherCondition.COLD_WAVE: 45.0,
                WeatherCondition.HIGH_WIND: 65.0,
                WeatherCondition.UNKNOWN: 0.0,
            }.get(
                condition,
                0.0,
            )

            score = (
                wind_score * 0.25
                + gust_score * 0.15
                + rain_score * 0.25
                + probability_score * 0.10
                + condition_score * 0.25
            )

            scores.append(
                min(
                    100.0,
                    max(
                        0.0,
                        score,
                    ),
                )
            )

        if event is not None:
            severity_score = {
                WeatherSeverity.NONE: 0.0,
                WeatherSeverity.LOW: 25.0,
                WeatherSeverity.MODERATE: 50.0,
                WeatherSeverity.HIGH: 75.0,
                WeatherSeverity.EXTREME: 100.0,
            }.get(
                event.severity,
                0.0,
            )

            event_probability = (
                event.probability
                if event.probability is not None
                else 1.0
            )

            scores.append(
                severity_score
                * max(
                    0.0,
                    min(
                        1.0,
                        float(event_probability),
                    ),
                )
            )

        if not scores:
            return 0.0

        return round(
            max(scores),
            4,
        )

    # ========================================================
    # GRID IMPACT
    # ========================================================

    @classmethod
    def estimate_asset_impact(
        cls,
        asset: Any,
        *,
        observation: WeatherObservation | None = None,
        forecast: WeatherForecastPoint | None = None,
    ) -> WeatherGridImpact:
        """
        Estimate weather impact for one grid asset.
        """

        score = cls.calculate_weather_risk(
            observation=observation,
            forecast=forecast,
        )

        asset_type = str(
            cls._get_value(
                asset,
                "asset_type",
                default="unknown",
            )
        ).lower()

        # Some asset classes are more exposed to weather.
        exposure_multiplier = {
            "transmission_line": 1.15,
            "transmission": 1.15,
            "substation": 1.05,
            "transformer": 1.00,
            "generator": 0.95,
            "bus": 0.90,
        }.get(
            asset_type,
            1.00,
        )

        score = min(
            100.0,
            score * exposure_multiplier,
        )

        reasons: list[str] = []

        if observation is not None:
            if (
                observation.wind_speed_kmh is not None
                and observation.wind_speed_kmh >= 50.0
            ):
                reasons.append(
                    "Elevated wind conditions."
                )

            if (
                observation.precipitation_mm is not None
                and observation.precipitation_mm >= 25.0
            ):
                reasons.append(
                    "Significant precipitation."
                )

            if observation.condition in {
                WeatherCondition.THUNDERSTORM,
                WeatherCondition.CYCLONE,
                WeatherCondition.FLOOD,
                WeatherCondition.HEAVY_RAIN,
            }:
                reasons.append(
                    "Potentially disruptive weather condition."
                )

        if forecast is not None:
            if (
                forecast.wind_speed_kmh is not None
                and forecast.wind_speed_kmh >= 50.0
            ):
                reasons.append(
                    "Forecast elevated wind conditions."
                )

            if (
                forecast.precipitation_probability is not None
                and forecast.precipitation_probability >= 0.60
            ):
                reasons.append(
                    "High precipitation probability."
                )

        return WeatherGridImpact(
            asset_id=int(
                cls._get_value(
                    asset,
                    "id",
                    "asset_id",
                    default=0,
                )
            ),
            risk_score=score,
            failure_probability=min(
                1.0,
                score / 100.0 * 0.75,
            ),
            expected_loading_increase_percent=(
                min(
                    30.0,
                    score * 0.20,
                )
            ),
            expected_capacity_reduction_percent=(
                min(
                    40.0,
                    score * 0.30,
                )
            ),
            affected=score >= 50.0,
            reasons=reasons,
            metadata={
                "asset_type": asset_type,
            },
        )

    # ========================================================
    # RISK ASSESSMENT
    # ========================================================

    def assess_risk(
        self,
        request: WeatherRiskRequest,
    ) -> WeatherRiskResponse:
        """
        Perform a weather-related grid-risk assessment.
        """

        self.validate_location(
            request.location
        )

        score = self.calculate_weather_risk(
            forecast=request.forecast,
            event=request.event,
        )

        probability = min(
            1.0,
            max(
                0.0,
                score / 100.0,
            ),
        )

        severity = (
            request.event.severity
            if request.event is not None
            else self.classify_severity(
                wind_speed_kmh=(
                    request.forecast.wind_speed_kmh
                    if request.forecast is not None
                    else None
                ),
                precipitation_mm=(
                    request.forecast.precipitation_mm
                    if request.forecast is not None
                    else None
                ),
                probability=(
                    request.forecast.precipitation_probability
                    if request.forecast is not None
                    else None
                ),
                condition=(
                    request.forecast.condition
                    if request.forecast is not None
                    else None
                ),
            )
        )

        impacts: list[WeatherGridImpact] = []

        # Asset IDs are intentionally represented as identifiers
        # here; actual asset loading can be performed by the
        # calling grid service/repository.
        affected_assets: list[int] = []

        if score >= 50.0:
            affected_assets = list(
                request.asset_ids
            )

        factors = {
            "overall_weather": round(
                score,
                4,
            ),
        }

        if request.forecast is not None:
            if request.forecast.wind_speed_kmh is not None:
                factors["wind"] = min(
                    100.0,
                    request.forecast.wind_speed_kmh,
                )

            if request.forecast.precipitation_mm is not None:
                factors["precipitation"] = min(
                    100.0,
                    request.forecast.precipitation_mm,
                )

            if (
                request.forecast.precipitation_probability
                is not None
            ):
                factors["precipitation_probability"] = (
                    request.forecast.precipitation_probability
                    * 100.0
                )

        recommendations = self._build_recommendations(
            score=score,
            severity=severity,
        )

        now = datetime.now(
            timezone.utc
        )

        return WeatherRiskResponse(
            score=score,
            probability=probability,
            severity=severity,
            affected_assets=affected_assets,
            impacts=impacts,
            factors=factors,
            recommendations=recommendations,
            assessed_at=now,
            valid_until=None,
            metadata=request.metadata,
        )

    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    @staticmethod
    def _build_recommendations(
        *,
        score: float,
        severity: WeatherSeverity,
    ) -> list[str]:
        """
        Generate deterministic weather-risk recommendations.
        """

        recommendations: list[str] = []

        if severity == WeatherSeverity.EXTREME:
            recommendations.extend(
                [
                    "Immediate operator review is recommended.",
                    "Inspect weather-exposed critical assets.",
                    "Evaluate available contingency scenarios.",
                ]
            )

        elif severity == WeatherSeverity.HIGH:
            recommendations.extend(
                [
                    "Increase monitoring of weather-exposed assets.",
                    "Review vulnerable transmission and substation assets.",
                ]
            )

        elif severity == WeatherSeverity.MODERATE:
            recommendations.append(
                "Maintain enhanced monitoring of affected grid areas."
            )

        elif severity == WeatherSeverity.LOW:
            recommendations.append(
                "Continue normal monitoring and review weather trends."
            )

        else:
            recommendations.append(
                "No significant weather-related grid action is indicated."
            )

        if score >= 75.0:
            recommendations.append(
                "Consider running a contingency simulation "
                "for critical assets."
            )

        return recommendations

    # ========================================================
    # SEVERE WEATHER EVENT CREATION
    # ========================================================

    @staticmethod
    def create_weather_event(
        *,
        event_type: str,
        title: str,
        location: WeatherLocation,
        start_time: datetime,
        description: str | None = None,
        end_time: datetime | None = None,
        probability: float | None = None,
        wind_speed_kmh: float | None = None,
        precipitation_mm: float | None = None,
        source: WeatherSource = WeatherSource.OTHER,
        source_id: str | None = None,
    ) -> SevereWeatherEvent:
        """
        Create a normalized severe-weather event.
        """

        try:
            from app.schemas.weather import WeatherEventType

            normalized_type = WeatherEventType(
                event_type.lower()
            )
        except (
            ValueError,
            AttributeError,
        ):
            normalized_type = WeatherEventType.OTHER

        severity = WeatherService.classify_severity(
            wind_speed_kmh=wind_speed_kmh,
            precipitation_mm=precipitation_mm,
            probability=probability,
            condition=normalized_type.value,
        )

        return SevereWeatherEvent(
            event_id=source_id,
            event_type=normalized_type,
            severity=severity,
            title=title,
            description=description,
            location=location,
            start_time=start_time,
            end_time=end_time,
            probability=probability,
            wind_speed_kmh=wind_speed_kmh,
            precipitation_mm=precipitation_mm,
            source=source,
            source_id=source_id,
            metadata={},
        )

    # ========================================================
    # ALERT CREATION
    # ========================================================

    @staticmethod
    def create_weather_alert(
        event: SevereWeatherEvent,
        *,
        grid_risk_score: float | None = None,
        affected_asset_count: int = 0,
    ) -> WeatherAlert:
        """
        Convert a severe-weather event into a grid-facing
        weather alert.
        """

        message = (
            event.description
            or (
                f"{event.title} may affect "
                "electrical-grid infrastructure."
            )
        )

        return WeatherAlert(
            alert_id=event.event_id,
            event_type=event.event_type,
            severity=event.severity,
            title=event.title,
            message=message,
            location=event.location,
            issued_at=datetime.now(
                timezone.utc
            ),
            expires_at=event.end_time,
            probability=event.probability,
            grid_risk_score=grid_risk_score,
            affected_asset_count=max(
                0,
                int(affected_asset_count),
            ),
            source=event.source,
            metadata={
                "source_event_id": event.event_id,
            },
        )

    # ========================================================
    # FORECAST UTILITIES
    # ========================================================

    @staticmethod
    def highest_risk_forecast_point(
        forecast: WeatherForecast,
    ) -> WeatherForecastPoint | None:
        """
        Return the forecast point with the highest estimated
        weather risk.
        """

        if not forecast.points:
            return None

        best_point: WeatherForecastPoint | None = None
        best_score = -1.0

        for point in forecast.points:
            score = WeatherService.calculate_weather_risk(
                forecast=point
            )

            if score > best_score:
                best_score = score
                best_point = point

        return best_point

    @staticmethod
    def filter_forecast(
        forecast: WeatherForecast,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> WeatherForecast:
        """
        Return a forecast restricted to a requested time range.
        """

        points = forecast.points

        if start_time is not None:
            points = [
                point
                for point in points
                if point.timestamp >= start_time
            ]

        if end_time is not None:
            points = [
                point
                for point in points
                if point.timestamp <= end_time
            ]

        return WeatherForecast(
            location=forecast.location,
            generated_at=forecast.generated_at,
            source=forecast.source,
            points=points,
            model_name=forecast.model_name,
            model_version=forecast.model_version,
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    @classmethod
    def summarize_forecast(
        cls,
        forecast: WeatherForecast,
    ) -> dict[str, Any]:
        """
        Generate a compact forecast summary.
        """

        if not forecast.points:
            return {
                "location": forecast.location,
                "point_count": 0,
                "max_risk_score": 0.0,
                "average_temperature_c": None,
                "total_precipitation_mm": 0.0,
                "max_wind_speed_kmh": 0.0,
            }

        temperatures = [
            point.temperature_c
            for point in forecast.points
            if point.temperature_c is not None
        ]

        precipitation = [
            point.precipitation_mm
            for point in forecast.points
            if point.precipitation_mm is not None
        ]

        wind = [
            point.wind_speed_kmh
            for point in forecast.points
            if point.wind_speed_kmh is not None
        ]

        risk_scores = [
            cls.calculate_weather_risk(
                forecast=point
            )
            for point in forecast.points
        ]

        return {
            "location": forecast.location,
            "point_count": len(
                forecast.points
            ),
            "max_risk_score": max(
                risk_scores,
                default=0.0,
            ),
            "average_temperature_c": (
                sum(temperatures)
                / len(temperatures)
                if temperatures
                else None
            ),
            "total_precipitation_mm": sum(
                precipitation
            ),
            "max_wind_speed_kmh": max(
                wind,
                default=0.0,
            ),
            "generated_at": forecast.generated_at,
            "source": forecast.source,
        }


__all__ = [
    "WeatherService",
]