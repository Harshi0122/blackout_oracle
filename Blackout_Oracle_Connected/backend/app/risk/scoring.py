"""
Blackout Oracle - Risk Scoring.

Provides deterministic risk-scoring utilities used by the
Blackout Oracle risk engine.

The scoring layer converts raw electrical, asset, weather,
anomaly, forecast, blackout, and cascade indicators into
standardized 0-100 risk scores.

This module is intentionally dependency-free.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence


# ============================================================
# CONSTANTS
# ============================================================

MIN_SCORE = 0.0
MAX_SCORE = 100.0

EPSILON = 1e-12


# ============================================================
# HELPERS
# ============================================================


def clamp(
    value: float,
    minimum: float = MIN_SCORE,
    maximum: float = MAX_SCORE,
) -> float:
    """Clamp a numeric value to the supplied range."""

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def to_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Safely convert a value to a finite float."""

    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default

    if not math.isfinite(result):
        return default

    return result


def normalize_01(
    value: Any,
    minimum: float,
    maximum: float,
) -> float:
    """
    Normalize a value into the 0-1 range.
    """

    minimum = to_float(
        minimum
    )

    maximum = to_float(
        maximum
    )

    if maximum <= minimum:
        raise ValueError(
            "maximum must be greater than minimum."
        )

    numeric = to_float(
        value
    )

    return max(
        0.0,
        min(
            1.0,
            (
                numeric - minimum
            )
            / (
                maximum - minimum
            ),
        ),
    )


def normalize_100(
    value: Any,
    minimum: float,
    maximum: float,
) -> float:
    """
    Normalize a value into the 0-100 range.
    """

    return (
        normalize_01(
            value,
            minimum,
            maximum,
        )
        * 100.0
    )


# ============================================================
# RISK LEVELS
# ============================================================


class RiskLevel:
    """Standard Blackout Oracle risk levels."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def risk_level(
    score: Any,
) -> str:
    """
    Convert a 0-100 score into a standard risk level.
    """

    score = clamp(
        to_float(score)
    )

    if score >= 90.0:
        return RiskLevel.CRITICAL

    if score >= 75.0:
        return RiskLevel.HIGH

    if score >= 50.0:
        return RiskLevel.MEDIUM

    if score >= 25.0:
        return RiskLevel.LOW

    return RiskLevel.VERY_LOW


# ============================================================
# SCORE RESULT
# ============================================================


@dataclass
class ScoreResult:
    """
    Result of a risk-scoring operation.
    """

    score: float

    level: str

    confidence: float = 1.0

    components: dict[str, float] = field(
        default_factory=dict
    )

    explanation: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert the score result to a dictionary."""

        return {
            "score": self.score,
            "level": self.level,
            "confidence": self.confidence,
            "components": dict(
                self.components
            ),
            "explanation": self.explanation,
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# WEIGHTED SCORING
# ============================================================


@dataclass
class WeightedScore:
    """
    Represents a weighted risk-score calculation.
    """

    name: str

    score: float

    weight: float

    contribution: float

    def to_dict(self) -> dict[str, float | str]:
        """Convert the weighted score to a dictionary."""

        return {
            "name": self.name,
            "score": self.score,
            "weight": self.weight,
            "contribution": self.contribution,
        }


def weighted_average(
    values: Mapping[str, Any],
    weights: Mapping[str, Any],
) -> float:
    """
    Calculate a weighted average on a 0-100 scale.

    Missing values are ignored.
    """

    numerator = 0.0
    denominator = 0.0

    for name, weight_value in weights.items():
        if name not in values:
            continue

        weight = max(
            0.0,
            to_float(
                weight_value
            ),
        )

        if weight <= 0.0:
            continue

        score = clamp(
            to_float(
                values[name]
            )
        )

        numerator += (
            score * weight
        )

        denominator += weight

    if denominator <= EPSILON:
        return 0.0

    return clamp(
        numerator / denominator
    )


def weighted_components(
    values: Mapping[str, Any],
    weights: Mapping[str, Any],
) -> list[WeightedScore]:
    """
    Return individual weighted score contributions.
    """

    total_weight = sum(
        max(
            0.0,
            to_float(
                weight
            ),
        )
        for weight in weights.values()
    )

    if total_weight <= EPSILON:
        return []

    results: list[
        WeightedScore
    ] = []

    for name, weight_value in weights.items():
        if name not in values:
            continue

        weight = max(
            0.0,
            to_float(
                weight_value
            ),
        )

        if weight <= 0.0:
            continue

        score = clamp(
            to_float(
                values[name]
            )
        )

        normalized_weight = (
            weight
            / total_weight
        )

        results.append(
            WeightedScore(
                name=name,
                score=score,
                weight=normalized_weight,
                contribution=(
                    score
                    * normalized_weight
                ),
            )
        )

    return results


# ============================================================
# ELECTRICAL RISK
# ============================================================


def frequency_risk(
    frequency_hz: Any,
    *,
    nominal_hz: float = 50.0,
    warning_deviation: float = 0.10,
    critical_deviation: float = 0.50,
) -> float:
    """
    Calculate frequency-related risk.

    The score increases as frequency moves farther from the
    nominal operating frequency.

    This is a generic risk heuristic and should be calibrated
    against the actual operating standards of the grid being
    monitored.
    """

    frequency = to_float(
        frequency_hz,
        nominal_hz,
    )

    deviation = abs(
        frequency
        - nominal_hz
    )

    warning_deviation = max(
        EPSILON,
        abs(
            to_float(
                warning_deviation
            )
        ),
    )

    critical_deviation = max(
        warning_deviation,
        abs(
            to_float(
                critical_deviation
            )
        ),
    )

    if deviation <= warning_deviation:
        return 0.0

    if deviation >= critical_deviation:
        return 100.0

    return clamp(
        (
            (
                deviation
                - warning_deviation
            )
            / (
                critical_deviation
                - warning_deviation
            )
        )
        * 100.0
    )


def voltage_risk(
    voltage_pu: Any,
    *,
    nominal_pu: float = 1.0,
    warning_deviation: float = 0.05,
    critical_deviation: float = 0.15,
) -> float:
    """
    Calculate voltage-related risk using per-unit voltage.
    """

    voltage = to_float(
        voltage_pu,
        nominal_pu,
    )

    deviation = abs(
        voltage
        - nominal_pu
    )

    warning_deviation = max(
        EPSILON,
        abs(
            to_float(
                warning_deviation
            )
        ),
    )

    critical_deviation = max(
        warning_deviation,
        abs(
            to_float(
                critical_deviation
            )
        ),
    )

    if deviation <= warning_deviation:
        return 0.0

    if deviation >= critical_deviation:
        return 100.0

    return clamp(
        (
            (
                deviation
                - warning_deviation
            )
            / (
                critical_deviation
                - warning_deviation
            )
        )
        * 100.0
    )


def loading_risk(
    loading_percent: Any,
) -> float:
    """
    Convert asset/grid loading percentage into risk.

    Below 70% is treated as relatively low risk.
    70-100% increases progressively.
    Above 100% is treated as critical.
    """

    loading = max(
        0.0,
        to_float(
            loading_percent
        ),
    )

    if loading <= 70.0:
        return 0.0

    if loading >= 120.0:
        return 100.0

    return clamp(
        (
            loading
            - 70.0
        )
        / 50.0
        * 100.0
    )


def electrical_risk(
    *,
    frequency_hz: float | None = None,
    voltage_pu: float | None = None,
    loading_percent: float | None = None,
    frequency_weight: float = 0.35,
    voltage_weight: float = 0.30,
    loading_weight: float = 0.35,
) -> ScoreResult:
    """
    Calculate combined electrical operating risk.
    """

    values: dict[
        str,
        float,
    ] = {}

    weights: dict[
        str,
        float,
    ] = {}

    if frequency_hz is not None:
        values["frequency"] = (
            frequency_risk(
                frequency_hz
            )
        )

        weights["frequency"] = (
            frequency_weight
        )

    if voltage_pu is not None:
        values["voltage"] = (
            voltage_risk(
                voltage_pu
            )
        )

        weights["voltage"] = (
            voltage_weight
        )

    if loading_percent is not None:
        values["loading"] = (
            loading_risk(
                loading_percent
            )
        )

        weights["loading"] = (
            loading_weight
        )

    score = weighted_average(
        values,
        weights,
    )

    return ScoreResult(
        score=round(
            score,
            4,
        ),
        level=risk_level(
            score
        ),
        confidence=(
            min(
                1.0,
                len(values)
                / 3.0,
            )
        ),
        components=values,
        explanation=(
            "Electrical operating conditions "
            "were evaluated using frequency, "
            "voltage, and loading indicators."
        ),
    )


# ============================================================
# ASSET RISK
# ============================================================


def asset_health_risk(
    health_score: Any,
) -> float:
    """
    Convert an asset-health score into risk.

    health_score is expected to be 0-100 where:

        100 = healthy
        0   = severely degraded
    """

    health = clamp(
        to_float(
            health_score
        )
    )

    return 100.0 - health


def temperature_risk(
    temperature: Any,
    *,
    warning_temperature: float,
    critical_temperature: float,
) -> float:
    """
    Calculate thermal risk.
    """

    value = to_float(
        temperature
    )

    warning = to_float(
        warning_temperature
    )

    critical = to_float(
        critical_temperature
    )

    if critical <= warning:
        raise ValueError(
            "critical_temperature must be greater "
            "than warning_temperature."
        )

    if value <= warning:
        return 0.0

    if value >= critical:
        return 100.0

    return clamp(
        (
            value
            - warning
        )
        / (
            critical
            - warning
        )
        * 100.0
    )


def asset_risk(
    *,
    health_score: float | None = None,
    temperature: float | None = None,
    temperature_warning: float | None = None,
    temperature_critical: float | None = None,
    failure_probability: float | None = None,
) -> ScoreResult:
    """
    Calculate combined asset risk.
    """

    values: dict[
        str,
        float,
    ] = {}

    weights: dict[
        str,
        float,
    ] = {}

    if health_score is not None:
        values["health"] = (
            asset_health_risk(
                health_score
            )
        )

        weights["health"] = 0.35

    if (
        temperature is not None
        and temperature_warning is not None
        and temperature_critical is not None
    ):
        values["temperature"] = (
            temperature_risk(
                temperature,
                warning_temperature=(
                    temperature_warning
                ),
                critical_temperature=(
                    temperature_critical
                ),
            )
        )

        weights["temperature"] = 0.25

    if failure_probability is not None:
        values["failure_probability"] = (
            clamp(
                to_float(
                    failure_probability
                )
                * 100.0
                if 0.0
                <= to_float(
                    failure_probability
                )
                <= 1.0
                else to_float(
                    failure_probability
                )
            )
        )

        weights["failure_probability"] = 0.40

    score = weighted_average(
        values,
        weights,
    )

    return ScoreResult(
        score=round(
            score,
            4,
        ),
        level=risk_level(
            score
        ),
        confidence=min(
            1.0,
            len(values)
            / 3.0,
        ),
        components=values,
        explanation=(
            "Asset risk was calculated from "
            "health, thermal, and failure-probability "
            "indicators."
        ),
    )


# ============================================================
# WEATHER RISK
# ============================================================


def weather_risk(
    *,
    severity: float | None = None,
    wind_speed: float | None = None,
    rainfall: float | None = None,
    temperature: float | None = None,
    lightning: float | None = None,
) -> ScoreResult:
    """
    Calculate weather-related grid risk.

    Input indicators are expected to be already normalized to
    0-100 where appropriate. Raw weather values can be supplied
    with simple generic thresholds.
    """

    components: dict[
        str,
        float,
    ] = {}

    weights: dict[
        str,
        float,
    ] = {}

    if severity is not None:
        components["severity"] = clamp(
            to_float(
                severity
            )
        )

        weights["severity"] = 0.35

    if wind_speed is not None:
        wind = max(
            0.0,
            to_float(
                wind_speed
            ),
        )

        components["wind"] = clamp(
            (
                max(
                    0.0,
                    wind - 40.0,
                )
                / 80.0
            )
            * 100.0
        )

        weights["wind"] = 0.20

    if rainfall is not None:
        rain = max(
            0.0,
            to_float(
                rainfall
            ),
        )

        components["rainfall"] = clamp(
            (
                max(
                    0.0,
                    rain - 20.0,
                )
                / 100.0
            )
            * 100.0
        )

        weights["rainfall"] = 0.15

    if temperature is not None:
        temp = abs(
            to_float(
                temperature
            )
        )

        components["temperature"] = clamp(
            (
                max(
                    0.0,
                    temp - 40.0,
                )
                / 20.0
            )
            * 100.0
        )

        weights["temperature"] = 0.15

    if lightning is not None:
        components["lightning"] = clamp(
            to_float(
                lightning
            )
            * 100.0
            if 0.0
            <= to_float(
                lightning
            )
            <= 1.0
            else to_float(
                lightning
            )
        )

        weights["lightning"] = 0.15

    score = weighted_average(
        components,
        weights,
    )

    return ScoreResult(
        score=round(
            score,
            4,
        ),
        level=risk_level(
            score
        ),
        confidence=min(
            1.0,
            len(components)
            / 5.0,
        ),
        components=components,
        explanation=(
            "Weather-related risk was estimated "
            "from the supplied environmental indicators."
        ),
    )


# ============================================================
# ANOMALY RISK
# ============================================================


def anomaly_risk(
    *,
    anomaly_score: float | None = None,
    anomaly_count: int | None = None,
    anomaly_severity: float | None = None,
) -> ScoreResult:
    """
    Calculate risk associated with anomalous grid behavior.
    """

    components: dict[
        str,
        float,
    ] = {}

    weights: dict[
        str,
        float,
    ] = {}

    if anomaly_score is not None:
        components["anomaly_score"] = clamp(
            to_float(
                anomaly_score
            )
        )

        weights["anomaly_score"] = 0.50

    if anomaly_count is not None:
        count = max(
            0,
            int(
                anomaly_count
            ),
        )

        components["anomaly_count"] = clamp(
            (
                min(
                    count,
                    20,
                )
                / 20.0
            )
            * 100.0
        )

        weights["anomaly_count"] = 0.20

    if anomaly_severity is not None:
        severity = to_float(
            anomaly_severity
        )

        components["severity"] = clamp(
            severity * 100.0
            if 0.0
            <= severity
            <= 1.0
            else severity
        )

        weights["severity"] = 0.30

    score = weighted_average(
        components,
        weights,
    )

    return ScoreResult(
        score=round(
            score,
            4,
        ),
        level=risk_level(
            score
        ),
        confidence=min(
            1.0,
            len(components)
            / 3.0,
        ),
        components=components,
        explanation=(
            "Anomaly risk was estimated from "
            "detected anomaly magnitude, frequency, "
            "and severity."
        ),
    )


# ============================================================
# FORECAST RISK
# ============================================================


def forecast_deviation_risk(
    actual: Any,
    forecast: Any,
    *,
    tolerance_percent: float = 5.0,
    critical_percent: float = 20.0,
) -> float:
    """
    Calculate risk from deviation between forecast and actual.
    """

    actual_value = to_float(
        actual
    )

    forecast_value = to_float(
        forecast
    )

    denominator = max(
        abs(actual_value),
        EPSILON,
    )

    deviation_percent = (
        abs(
            forecast_value
            - actual_value
        )
        / denominator
    ) * 100.0

    tolerance = max(
        0.0,
        to_float(
            tolerance_percent
        ),
    )

    critical = max(
        tolerance + EPSILON,
        to_float(
            critical_percent
        ),
    )

    if deviation_percent <= tolerance:
        return 0.0

    if deviation_percent >= critical:
        return 100.0

    return clamp(
        (
            deviation_percent
            - tolerance
        )
        / (
            critical
            - tolerance
        )
        * 100.0
    )


def forecast_risk(
    *,
    deviation_score: float | None = None,
    load_forecast: float | None = None,
    capacity: float | None = None,
) -> ScoreResult:
    """
    Calculate future forecast-related grid risk.
    """

    components: dict[
        str,
        float,
    ] = {}

    weights: dict[
        str,
        float,
    ] = {}

    if deviation_score is not None:
        components["deviation"] = clamp(
            to_float(
                deviation_score
            )
        )

        weights["deviation"] = 0.50

    if (
        load_forecast is not None
        and capacity is not None
    ):
        capacity_value = max(
            EPSILON,
            to_float(
                capacity
            ),
        )

        forecast_loading = (
            to_float(
                load_forecast
            )
            / capacity_value
        ) * 100.0

        components["forecast_loading"] = (
            loading_risk(
                forecast_loading
            )
        )

        weights["forecast_loading"] = 0.50

    score = weighted_average(
        components,
        weights,
    )

    return ScoreResult(
        score=round(
            score,
            4,
        ),
        level=risk_level(
            score
        ),
        confidence=min(
            1.0,
            len(components)
            / 2.0,
        ),
        components=components,
        explanation=(
            "Forecast risk was estimated from "
            "prediction deviation and projected loading."
        ),
    )


# ============================================================
# BLACKOUT RISK
# ============================================================


def blackout_probability_score(
    probability: Any,
) -> float:
    """
    Convert blackout probability to a 0-100 risk score.
    """

    value = to_float(
        probability
    )

    if 0.0 <= value <= 1.0:
        value *= 100.0

    return clamp(
        value
    )


def blackout_risk(
    *,
    probability: float | None = None,
    model_score: float | None = None,
    affected_load_percent: float | None = None,
) -> ScoreResult:
    """
    Calculate blackout risk.
    """

    components: dict[
        str,
        float,
    ] = {}

    weights: dict[
        str,
        float,
    ] = {}

    if probability is not None:
        components["probability"] = (
            blackout_probability_score(
                probability
            )
        )

        weights["probability"] = 0.60

    if model_score is not None:
        components["model_score"] = clamp(
            to_float(
                model_score
            )
        )

        weights["model_score"] = 0.25

    if affected_load_percent is not None:
        components["affected_load"] = clamp(
            to_float(
                affected_load_percent
            )
        )

        weights["affected_load"] = 0.15

    score = weighted_average(
        components,
        weights,
    )

    return ScoreResult(
        score=round(
            score,
            4,
        ),
        level=risk_level(
            score
        ),
        confidence=min(
            1.0,
            len(components)
            / 3.0,
        ),
        components=components,
        explanation=(
            "Blackout risk was estimated from "
            "predicted probability, model score, "
            "and potentially affected load."
        ),
    )


# ============================================================
# CASCADE RISK
# ============================================================


def cascade_risk(
    *,
    probability: float | None = None,
    vulnerable_assets: int | None = None,
    network_stress: float | None = None,
    propagation_depth: int | None = None,
) -> ScoreResult:
    """
    Calculate cascading-failure risk.
    """

    components: dict[
        str,
        float,
    ] = {}

    weights: dict[
        str,
        float,
    ] = {}

    if probability is not None:
        components["probability"] = (
            blackout_probability_score(
                probability
            )
        )

        weights["probability"] = 0.45

    if vulnerable_assets is not None:
        assets = max(
            0,
            int(
                vulnerable_assets
            ),
        )

        components["vulnerable_assets"] = clamp(
            (
                min(
                    assets,
                    20,
                )
                / 20.0
            )
            * 100.0
        )

        weights["vulnerable_assets"] = 0.20

    if network_stress is not None:
        components["network_stress"] = clamp(
            to_float(
                network_stress
            )
        )

        weights["network_stress"] = 0.25

    if propagation_depth is not None:
        depth = max(
            0,
            int(
                propagation_depth
            ),
        )

        components["propagation_depth"] = clamp(
            (
                min(
                    depth,
                    10,
                )
                / 10.0
            )
            * 100.0
        )

        weights["propagation_depth"] = 0.10

    score = weighted_average(
        components,
        weights,
    )

    return ScoreResult(
        score=round(
            score,
            4,
        ),
        level=risk_level(
            score
        ),
        confidence=min(
            1.0,
            len(components)
            / 4.0,
        ),
        components=components,
        explanation=(
            "Cascade risk was estimated from "
            "propagation probability, vulnerable assets, "
            "network stress, and propagation depth."
        ),
    )


# ============================================================
# OVERALL GRID RISK
# ============================================================


@dataclass
class GridRiskScorer:
    """
    Combines individual risk categories into an overall
    Blackout Oracle grid-risk score.
    """

    electrical_weight: float = 0.25

    asset_weight: float = 0.20

    weather_weight: float = 0.10

    anomaly_weight: float = 0.15

    blackout_weight: float = 0.15

    cascade_weight: float = 0.10

    forecast_weight: float = 0.05

    def __post_init__(self) -> None:
        """Validate scorer configuration."""

        weights = [
            self.electrical_weight,
            self.asset_weight,
            self.weather_weight,
            self.anomaly_weight,
            self.blackout_weight,
            self.cascade_weight,
            self.forecast_weight,
        ]

        if any(
            weight < 0.0
            for weight in weights
        ):
            raise ValueError(
                "Risk weights cannot be negative."
            )

        if sum(weights) <= EPSILON:
            raise ValueError(
                "At least one risk weight must be positive."
            )

    def normalized_weights(
        self,
    ) -> dict[str, float]:
        """Return normalized risk weights."""

        weights = {
            "electrical": self.electrical_weight,
            "asset": self.asset_weight,
            "weather": self.weather_weight,
            "anomaly": self.anomaly_weight,
            "blackout": self.blackout_weight,
            "cascade": self.cascade_weight,
            "forecast": self.forecast_weight,
        }

        total = sum(
            weights.values()
        )

        return {
            name: value / total
            for name, value in weights.items()
        }

    def score(
        self,
        *,
        electrical: float | ScoreResult = 0.0,
        asset: float | ScoreResult = 0.0,
        weather: float | ScoreResult = 0.0,
        anomaly: float | ScoreResult = 0.0,
        blackout: float | ScoreResult = 0.0,
        cascade: float | ScoreResult = 0.0,
        forecast: float | ScoreResult = 0.0,
    ) -> ScoreResult:
        """
        Calculate the overall grid-risk score.
        """

        values: dict[
            str,
            float,
        ] = {
            "electrical": _extract_score(
                electrical
            ),
            "asset": _extract_score(
                asset
            ),
            "weather": _extract_score(
                weather
            ),
            "anomaly": _extract_score(
                anomaly
            ),
            "blackout": _extract_score(
                blackout
            ),
            "cascade": _extract_score(
                cascade
            ),
            "forecast": _extract_score(
                forecast
            ),
        }

        weights = self.normalized_weights()

        components = weighted_components(
            values,
            weights,
        )

        overall = sum(
            component.contribution
            for component in components
        )

        confidence_values = [
            item.confidence
            for item in (
                electrical,
                asset,
                weather,
                anomaly,
                blackout,
                cascade,
                forecast,
            )
            if isinstance(
                item,
                ScoreResult,
            )
        ]

        if confidence_values:
            confidence = (
                sum(
                    confidence_values
                )
                / len(
                    confidence_values
                )
            )

        else:
            confidence = 1.0

        component_dict = {
            component.name: round(
                component.score,
                4,
            )
            for component in components
        }

        return ScoreResult(
            score=round(
                clamp(
                    overall
                ),
                4,
            ),
            level=risk_level(
                overall
            ),
            confidence=round(
                clamp(
                    confidence,
                    0.0,
                    1.0,
                ),
                4,
            ),
            components=component_dict,
            explanation=(
                "Overall grid risk was calculated "
                "as a weighted combination of "
                "electrical, asset, weather, anomaly, "
                "blackout, cascade, and forecast risk."
            ),
            metadata={
                "weights": weights,
                "weighted_components": [
                    component.to_dict()
                    for component in components
                ],
            },
        )


def _extract_score(
    value: float | ScoreResult,
) -> float:
    """Extract a numeric score from a value or ScoreResult."""

    if isinstance(
        value,
        ScoreResult,
    ):
        return clamp(
            value.score
        )

    return clamp(
        to_float(
            value
        )
    )


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def calculate_grid_risk(
    **kwargs: Any,
) -> ScoreResult:
    """
    Calculate overall grid risk using default weights.
    """

    scorer = GridRiskScorer()

    return scorer.score(
        **kwargs
    )


def calculate_electrical_risk(
    **kwargs: Any,
) -> ScoreResult:
    """Convenience wrapper for electrical risk."""

    return electrical_risk(
        **kwargs
    )


def calculate_asset_risk(
    **kwargs: Any,
) -> ScoreResult:
    """Convenience wrapper for asset risk."""

    return asset_risk(
        **kwargs
    )


def calculate_weather_risk(
    **kwargs: Any,
) -> ScoreResult:
    """Convenience wrapper for weather risk."""

    return weather_risk(
        **kwargs
    )


def calculate_anomaly_risk(
    **kwargs: Any,
) -> ScoreResult:
    """Convenience wrapper for anomaly risk."""

    return anomaly_risk(
        **kwargs
    )


def calculate_forecast_risk(
    **kwargs: Any,
) -> ScoreResult:
    """Convenience wrapper for forecast risk."""

    return forecast_risk(
        **kwargs
    )


def calculate_blackout_risk(
    **kwargs: Any,
) -> ScoreResult:
    """Convenience wrapper for blackout risk."""

    return blackout_risk(
        **kwargs
    )


def calculate_cascade_risk(
    **kwargs: Any,
) -> ScoreResult:
    """Convenience wrapper for cascade risk."""

    return cascade_risk(
        **kwargs
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "RiskLevel",
    "ScoreResult",
    "WeightedScore",
    "GridRiskScorer",
    "clamp",
    "to_float",
    "normalize_01",
    "normalize_100",
    "risk_level",
    "weighted_average",
    "weighted_components",
    "frequency_risk",
    "voltage_risk",
    "loading_risk",
    "electrical_risk",
    "asset_health_risk",
    "temperature_risk",
    "asset_risk",
    "weather_risk",
    "anomaly_risk",
    "forecast_deviation_risk",
    "forecast_risk",
    "blackout_probability_score",
    "blackout_risk",
    "cascade_risk",
    "calculate_grid_risk",
    "calculate_electrical_risk",
    "calculate_asset_risk",
    "calculate_weather_risk",
    "calculate_anomaly_risk",
    "calculate_forecast_risk",
    "calculate_blackout_risk",
    "calculate_cascade_risk",
]