"""
Blackout Oracle - Weather Feature Engineering.

Provides deterministic weather-derived features for:

- Grid risk scoring
- Asset stress analysis
- Outage prediction
- Weather-related anomaly detection
- Blackout prediction
- AI investigation

This module only calculates analytical features.
It does not fetch weather data and does not control
physical grid equipment.
"""

from __future__ import annotations

import math
from typing import Any


# ============================================================
# CONSTANTS
# ============================================================

EPSILON = 1e-9

DEFAULT_HIGH_WIND_SPEED = 50.0
DEFAULT_EXTREME_WIND_SPEED = 80.0

DEFAULT_HEAVY_RAINFALL = 50.0
DEFAULT_EXTREME_RAINFALL = 100.0

DEFAULT_HIGH_TEMPERATURE = 40.0
DEFAULT_EXTREME_TEMPERATURE = 45.0

DEFAULT_LOW_TEMPERATURE = 5.0

DEFAULT_HIGH_HUMIDITY = 85.0

DEFAULT_HIGH_LIGHTNING_RISK = 0.7


# ============================================================
# BASIC HELPERS
# ============================================================


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Safely convert a value to float.

    Invalid, NaN, and infinite values are replaced with
    the supplied default.
    """
    try:
        result = float(value)

        if not math.isfinite(result):
            return default

        return result

    except (TypeError, ValueError):
        return default


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    """
    Clamp a value to a specified range.
    """
    return max(
        minimum,
        min(maximum, value),
    )


# ============================================================
# TEMPERATURE FEATURES
# ============================================================


def temperature_stress_score(
    temperature_c: float,
    high_temperature_c: float = DEFAULT_HIGH_TEMPERATURE,
    extreme_temperature_c: float = DEFAULT_EXTREME_TEMPERATURE,
) -> float:
    """
    Calculate normalized high-temperature stress.

    Returns:
        Value between 0.0 and 1.0.

    Temperatures below the high-temperature threshold
    produce zero heat stress.
    """
    temperature = _safe_float(
        temperature_c
    )

    high = _safe_float(
        high_temperature_c,
        DEFAULT_HIGH_TEMPERATURE,
    )

    extreme = _safe_float(
        extreme_temperature_c,
        DEFAULT_EXTREME_TEMPERATURE,
    )

    if temperature <= high:
        return 0.0

    if extreme <= high:
        return 1.0

    if temperature >= extreme:
        return 1.0

    return _clamp(
        (temperature - high)
        / (extreme - high)
    )


def low_temperature_stress_score(
    temperature_c: float,
    low_temperature_c: float = DEFAULT_LOW_TEMPERATURE,
) -> float:
    """
    Calculate normalized low-temperature stress.

    Returns:
        Value between 0.0 and 1.0.
    """
    temperature = _safe_float(
        temperature_c
    )

    threshold = _safe_float(
        low_temperature_c,
        DEFAULT_LOW_TEMPERATURE,
    )

    if temperature >= threshold:
        return 0.0

    if threshold <= EPSILON:
        return 1.0

    return _clamp(
        (threshold - temperature)
        / max(
            abs(threshold),
            1.0,
        )
    )


def temperature_stress(
    temperature_c: float,
    high_temperature_c: float = DEFAULT_HIGH_TEMPERATURE,
    extreme_temperature_c: float = DEFAULT_EXTREME_TEMPERATURE,
    low_temperature_c: float = DEFAULT_LOW_TEMPERATURE,
) -> float:
    """
    Combine high- and low-temperature stress.
    """
    high_stress = temperature_stress_score(
        temperature_c,
        high_temperature_c,
        extreme_temperature_c,
    )

    low_stress = low_temperature_stress_score(
        temperature_c,
        low_temperature_c,
    )

    return max(
        high_stress,
        low_stress,
    )


# ============================================================
# WIND FEATURES
# ============================================================


def wind_stress_score(
    wind_speed_kmh: float,
    high_wind_speed_kmh: float = DEFAULT_HIGH_WIND_SPEED,
    extreme_wind_speed_kmh: float = DEFAULT_EXTREME_WIND_SPEED,
) -> float:
    """
    Calculate normalized wind stress.

    Returns:
        Value between 0.0 and 1.0.
    """
    wind = max(
        0.0,
        _safe_float(
            wind_speed_kmh
        ),
    )

    high = _safe_float(
        high_wind_speed_kmh,
        DEFAULT_HIGH_WIND_SPEED,
    )

    extreme = _safe_float(
        extreme_wind_speed_kmh,
        DEFAULT_EXTREME_WIND_SPEED,
    )

    if wind <= high:
        return 0.0

    if extreme <= high:
        return 1.0

    if wind >= extreme:
        return 1.0

    return _clamp(
        (wind - high)
        / (extreme - high)
    )


def is_high_wind(
    wind_speed_kmh: float,
    threshold_kmh: float = DEFAULT_HIGH_WIND_SPEED,
) -> bool:
    """
    Determine whether wind speed exceeds the configured
    analytical threshold.
    """
    return (
        _safe_float(wind_speed_kmh)
        >= _safe_float(
            threshold_kmh,
            DEFAULT_HIGH_WIND_SPEED,
        )
    )


def is_extreme_wind(
    wind_speed_kmh: float,
    threshold_kmh: float = DEFAULT_EXTREME_WIND_SPEED,
) -> bool:
    """
    Determine whether wind speed exceeds the extreme
    analytical threshold.
    """
    return (
        _safe_float(wind_speed_kmh)
        >= _safe_float(
            threshold_kmh,
            DEFAULT_EXTREME_WIND_SPEED,
        )
    )


# ============================================================
# RAINFALL FEATURES
# ============================================================


def rainfall_stress_score(
    rainfall_mm: float,
    heavy_rainfall_mm: float = DEFAULT_HEAVY_RAINFALL,
    extreme_rainfall_mm: float = DEFAULT_EXTREME_RAINFALL,
) -> float:
    """
    Calculate normalized rainfall stress.

    The rainfall value should represent the accumulation
    period used by the weather source.
    """
    rainfall = max(
        0.0,
        _safe_float(
            rainfall_mm
        ),
    )

    heavy = _safe_float(
        heavy_rainfall_mm,
        DEFAULT_HEAVY_RAINFALL,
    )

    extreme = _safe_float(
        extreme_rainfall_mm,
        DEFAULT_EXTREME_RAINFALL,
    )

    if rainfall <= heavy:
        return 0.0

    if extreme <= heavy:
        return 1.0

    if rainfall >= extreme:
        return 1.0

    return _clamp(
        (rainfall - heavy)
        / (extreme - heavy)
    )


def is_heavy_rainfall(
    rainfall_mm: float,
    threshold_mm: float = DEFAULT_HEAVY_RAINFALL,
) -> bool:
    """
    Determine whether rainfall exceeds the configured
    analytical threshold.
    """
    return (
        _safe_float(rainfall_mm)
        >= _safe_float(
            threshold_mm,
            DEFAULT_HEAVY_RAINFALL,
        )
    )


def is_extreme_rainfall(
    rainfall_mm: float,
    threshold_mm: float = DEFAULT_EXTREME_RAINFALL,
) -> bool:
    """
    Determine whether rainfall exceeds the extreme
    analytical threshold.
    """
    return (
        _safe_float(rainfall_mm)
        >= _safe_float(
            threshold_mm,
            DEFAULT_EXTREME_RAINFALL,
        )
    )


# ============================================================
# HUMIDITY FEATURES
# ============================================================


def humidity_stress_score(
    humidity_percent: float,
    high_humidity_percent: float = DEFAULT_HIGH_HUMIDITY,
) -> float:
    """
    Calculate normalized humidity stress.

    Returns:
        Value between 0.0 and 1.0.
    """
    humidity = _clamp(
        _safe_float(
            humidity_percent
        ),
        0.0,
        100.0,
    )

    threshold = _clamp(
        _safe_float(
            high_humidity_percent,
            DEFAULT_HIGH_HUMIDITY,
        ),
        0.0,
        100.0,
    )

    if humidity <= threshold:
        return 0.0

    remaining = 100.0 - threshold

    if remaining <= EPSILON:
        return 1.0

    return _clamp(
        (humidity - threshold)
        / remaining
    )


# ============================================================
# LIGHTNING FEATURES
# ============================================================


def lightning_stress_score(
    lightning_probability: float,
) -> float:
    """
    Normalize lightning probability.

    The input can be supplied either as:

        0.0 - 1.0

    or:

        0 - 100

    Values above 1.0 are interpreted as percentages.
    """
    value = _safe_float(
        lightning_probability
    )

    if value > 1.0:
        value /= 100.0

    return _clamp(value)


def high_lightning_risk(
    lightning_probability: float,
    threshold: float = DEFAULT_HIGH_LIGHTNING_RISK,
) -> bool:
    """
    Determine whether lightning probability is high.
    """
    probability = lightning_stress_score(
        lightning_probability
    )

    return (
        probability
        >= _clamp(
            _safe_float(
                threshold,
                DEFAULT_HIGH_LIGHTNING_RISK,
            )
        )
    )


# ============================================================
# WEATHER CONDITION FEATURES
# ============================================================


def precipitation_stress_score(
    precipitation_probability: float,
) -> float:
    """
    Normalize precipitation probability.

    Accepts either:

        0.0 - 1.0

    or:

        0 - 100
    """
    probability = _safe_float(
        precipitation_probability
    )

    if probability > 1.0:
        probability /= 100.0

    return _clamp(
        probability
    )


def visibility_stress_score(
    visibility_km: float,
    poor_visibility_km: float = 2.0,
) -> float:
    """
    Calculate normalized poor-visibility stress.

    Returns:
        Value between 0.0 and 1.0.
    """
    visibility = max(
        0.0,
        _safe_float(
            visibility_km
        ),
    )

    threshold = max(
        EPSILON,
        _safe_float(
            poor_visibility_km,
            2.0,
        ),
    )

    if visibility >= threshold:
        return 0.0

    return _clamp(
        1.0
        - (
            visibility
            / threshold
        )
    )


# ============================================================
# PRESSURE FEATURES
# ============================================================


def pressure_deviation(
    pressure_hpa: float,
    reference_pressure_hpa: float = 1013.25,
) -> float:
    """
    Calculate pressure deviation from a reference value.
    """
    pressure = _safe_float(
        pressure_hpa
    )

    reference = _safe_float(
        reference_pressure_hpa,
        1013.25,
    )

    if abs(reference) < EPSILON:
        return 0.0

    return (
        (pressure - reference)
        / reference
    ) * 100.0


# ============================================================
# WEATHER COMBINATION
# ============================================================


def weather_stress_score(
    temperature_stress: float,
    wind_stress: float,
    rainfall_stress: float,
    humidity_stress: float,
    lightning_stress: float,
    precipitation_stress: float = 0.0,
    visibility_stress: float = 0.0,
) -> float:
    """
    Combine weather-related stress indicators into a single
    normalized feature.

    Weighting:

        Wind            25%
        Rainfall        20%
        Temperature     15%
        Lightning       20%
        Humidity        10%
        Precipitation    5%
        Visibility       5%

    Returns:
        Value between 0.0 and 1.0.

    This is an analytical feature and is not a physical
    protection threshold.
    """
    temperature = _clamp(
        _safe_float(
            temperature_stress
        )
    )

    wind = _clamp(
        _safe_float(
            wind_stress
        )
    )

    rainfall = _clamp(
        _safe_float(
            rainfall_stress
        )
    )

    humidity = _clamp(
        _safe_float(
            humidity_stress
        )
    )

    lightning = _clamp(
        _safe_float(
            lightning_stress
        )
    )

    precipitation = _clamp(
        _safe_float(
            precipitation_stress
        )
    )

    visibility = _clamp(
        _safe_float(
            visibility_stress
        )
    )

    score = (
        wind * 0.25
        + rainfall * 0.20
        + temperature * 0.15
        + lightning * 0.20
        + humidity * 0.10
        + precipitation * 0.05
        + visibility * 0.05
    )

    return _clamp(score)


# ============================================================
# WEATHER-RELATED GRID RISK
# ============================================================


def weather_grid_risk_score(
    weather_stress: float,
    exposed_asset_ratio: float = 0.0,
    vulnerable_asset_ratio: float = 0.0,
) -> float:
    """
    Estimate weather-related grid risk.

    Args:
        weather_stress:
            Overall weather stress.

        exposed_asset_ratio:
            Fraction of relevant assets exposed to the
            weather condition.

        vulnerable_asset_ratio:
            Fraction of assets considered vulnerable.

    Returns:
        Value between 0.0 and 1.0.

    This is a feature-engineering score rather than a
    formal reliability index.
    """
    weather = _clamp(
        _safe_float(
            weather_stress
        )
    )

    exposed = _clamp(
        _safe_float(
            exposed_asset_ratio
        )
    )

    vulnerable = _clamp(
        _safe_float(
            vulnerable_asset_ratio
        )
    )

    return _clamp(
        weather
        * (
            0.50
            + exposed * 0.30
            + vulnerable * 0.20
        )
    )


# ============================================================
# COMPLETE WEATHER FEATURE EXTRACTION
# ============================================================


def extract_weather_features(
    data: dict[str, Any],
) -> dict[str, float | bool]:
    """
    Extract a standardized weather feature set.

    Supported input keys include:

        temperature_c
        temperature
        wind_speed_kmh
        wind_speed
        rainfall_mm
        rainfall
        humidity_percent
        humidity
        lightning_probability
        precipitation_probability
        visibility_km
        pressure_hpa
        exposed_asset_ratio
        vulnerable_asset_ratio

    Returns:
        Dictionary containing derived weather features.
    """

    # --------------------------------------------------------
    # Read raw measurements
    # --------------------------------------------------------

    temperature = _safe_float(
        data.get(
            "temperature_c",
            data.get(
                "temperature",
                0.0,
            ),
        )
    )

    wind_speed = _safe_float(
        data.get(
            "wind_speed_kmh",
            data.get(
                "wind_speed",
                0.0,
            ),
        )
    )

    rainfall = _safe_float(
        data.get(
            "rainfall_mm",
            data.get(
                "rainfall",
                0.0,
            ),
        )
    )

    humidity = _safe_float(
        data.get(
            "humidity_percent",
            data.get(
                "humidity",
                0.0,
            ),
        )
    )

    lightning_probability = _safe_float(
        data.get(
            "lightning_probability",
            0.0,
        )
    )

    precipitation_probability = _safe_float(
        data.get(
            "precipitation_probability",
            0.0,
        )
    )

    visibility = _safe_float(
        data.get(
            "visibility_km",
            0.0,
        )
    )

    pressure = _safe_float(
        data.get(
            "pressure_hpa",
            1013.25,
        )
    )

    # --------------------------------------------------------
    # Individual stress features
    # --------------------------------------------------------

    heat_stress = temperature_stress_score(
        temperature
    )

    cold_stress = low_temperature_stress_score(
        temperature
    )

    combined_temperature_stress = temperature_stress(
        temperature
    )

    wind_stress = wind_stress_score(
        wind_speed
    )

    rainfall_stress = rainfall_stress_score(
        rainfall
    )

    humidity_stress = humidity_stress_score(
        humidity
    )

    lightning_stress = lightning_stress_score(
        lightning_probability
    )

    precipitation_stress = precipitation_stress_score(
        precipitation_probability
    )

    visibility_stress = visibility_stress_score(
        visibility
    )

    # --------------------------------------------------------
    # Combined weather stress
    # --------------------------------------------------------

    combined_weather_stress = weather_stress_score(
        temperature_stress=combined_temperature_stress,
        wind_stress=wind_stress,
        rainfall_stress=rainfall_stress,
        humidity_stress=humidity_stress,
        lightning_stress=lightning_stress,
        precipitation_stress=precipitation_stress,
        visibility_stress=visibility_stress,
    )

    # --------------------------------------------------------
    # Exposure
    # --------------------------------------------------------

    exposed_asset_ratio = _clamp(
        _safe_float(
            data.get(
                "exposed_asset_ratio",
                0.0,
            )
        )
    )

    vulnerable_asset_ratio = _clamp(
        _safe_float(
            data.get(
                "vulnerable_asset_ratio",
                0.0,
            )
        )
    )

    grid_risk = weather_grid_risk_score(
        combined_weather_stress,
        exposed_asset_ratio,
        vulnerable_asset_ratio,
    )

    # --------------------------------------------------------
    # Final feature dictionary
    # --------------------------------------------------------

    return {
        "temperature_c": temperature,
        "heat_stress_score": heat_stress,
        "cold_stress_score": cold_stress,
        "temperature_stress_score": combined_temperature_stress,
        "wind_speed_kmh": wind_speed,
        "wind_stress_score": wind_stress,
        "high_wind": is_high_wind(
            wind_speed
        ),
        "extreme_wind": is_extreme_wind(
            wind_speed
        ),
        "rainfall_mm": rainfall,
        "rainfall_stress_score": rainfall_stress,
        "heavy_rainfall": is_heavy_rainfall(
            rainfall
        ),
        "extreme_rainfall": is_extreme_rainfall(
            rainfall
        ),
        "humidity_percent": humidity,
        "humidity_stress_score": humidity_stress,
        "lightning_probability": lightning_stress,
        "lightning_stress_score": lightning_stress,
        "high_lightning_risk": high_lightning_risk(
            lightning_probability
        ),
        "precipitation_probability": precipitation_stress,
        "precipitation_stress_score": precipitation_stress,
        "visibility_km": visibility,
        "visibility_stress_score": visibility_stress,
        "pressure_hpa": pressure,
        "pressure_deviation_percent": pressure_deviation(
            pressure
        ),
        "weather_stress_score": combined_weather_stress,
        "exposed_asset_ratio": exposed_asset_ratio,
        "vulnerable_asset_ratio": vulnerable_asset_ratio,
        "weather_grid_risk_score": grid_risk,
    }


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "temperature_stress_score",
    "low_temperature_stress_score",
    "temperature_stress",
    "wind_stress_score",
    "is_high_wind",
    "is_extreme_wind",
    "rainfall_stress_score",
    "is_heavy_rainfall",
    "is_extreme_rainfall",
    "humidity_stress_score",
    "lightning_stress_score",
    "high_lightning_risk",
    "precipitation_stress_score",
    "visibility_stress_score",
    "pressure_deviation",
    "weather_stress_score",
    "weather_grid_risk_score",
    "extract_weather_features",
]