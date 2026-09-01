"""
Blackout Oracle - Historical Feature Engineering.

Provides deterministic feature calculations based on historical
grid observations.

Historical features are used for:

- Trend analysis
- Baseline calculation
- Anomaly detection
- Load forecasting
- Risk scoring
- Blackout prediction
- Asset degradation analysis
- Grid stability analysis

This module does not use an AI model. Numerical historical
features should remain deterministic and reproducible.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any


# ============================================================
# CONSTANTS
# ============================================================

EPSILON = 1e-9

DEFAULT_WINDOW_SIZE = 5

DEFAULT_ANOMALY_Z_SCORE = 3.0


# ============================================================
# BASIC HELPERS
# ============================================================


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Safely convert a value to float.

    Invalid, NaN, and infinite values are replaced by
    the supplied default.
    """
    try:
        result = float(value)

        if not math.isfinite(result):
            return default

        return result

    except (TypeError, ValueError):
        return default


def _clean_values(
    values: Sequence[Any],
) -> list[float]:
    """
    Convert a sequence into finite floating-point values.

    Invalid values are ignored.
    """
    cleaned: list[float] = []

    for value in values:
        try:
            converted = float(value)

            if math.isfinite(converted):
                cleaned.append(converted)

        except (TypeError, ValueError):
            continue

    return cleaned


# ============================================================
# BASIC STATISTICS
# ============================================================


def historical_mean(
    values: Sequence[Any],
) -> float:
    """
    Calculate the arithmetic mean of historical values.

    Returns:
        Mean value, or 0.0 if no valid values exist.
    """
    cleaned = _clean_values(values)

    if not cleaned:
        return 0.0

    return sum(cleaned) / len(cleaned)


def historical_minimum(
    values: Sequence[Any],
) -> float:
    """
    Return the minimum historical value.
    """
    cleaned = _clean_values(values)

    if not cleaned:
        return 0.0

    return min(cleaned)


def historical_maximum(
    values: Sequence[Any],
) -> float:
    """
    Return the maximum historical value.
    """
    cleaned = _clean_values(values)

    if not cleaned:
        return 0.0

    return max(cleaned)


def historical_range(
    values: Sequence[Any],
) -> float:
    """
    Calculate the historical range.

    Range = maximum - minimum.
    """
    cleaned = _clean_values(values)

    if not cleaned:
        return 0.0

    return max(cleaned) - min(cleaned)


def historical_variance(
    values: Sequence[Any],
) -> float:
    """
    Calculate population variance.
    """
    cleaned = _clean_values(values)

    if not cleaned:
        return 0.0

    mean = historical_mean(cleaned)

    return sum(
        (value - mean) ** 2
        for value in cleaned
    ) / len(cleaned)


def historical_standard_deviation(
    values: Sequence[Any],
) -> float:
    """
    Calculate population standard deviation.
    """
    return math.sqrt(
        historical_variance(values)
    )


# ============================================================
# MOVING STATISTICS
# ============================================================


def moving_average(
    values: Sequence[Any],
    window_size: int = DEFAULT_WINDOW_SIZE,
) -> list[float]:
    """
    Calculate a simple moving average.

    Args:
        values: Historical observations.
        window_size: Number of observations in each window.

    Returns:
        Moving-average values.
    """
    cleaned = _clean_values(values)

    if not cleaned:
        return []

    window = max(
        1,
        int(window_size),
    )

    result: list[float] = []

    for index in range(len(cleaned)):
        start = max(
            0,
            index - window + 1,
        )

        window_values = cleaned[
            start:index + 1
        ]

        result.append(
            sum(window_values)
            / len(window_values)
        )

    return result


def moving_standard_deviation(
    values: Sequence[Any],
    window_size: int = DEFAULT_WINDOW_SIZE,
) -> list[float]:
    """
    Calculate rolling standard deviation.
    """
    cleaned = _clean_values(values)

    if not cleaned:
        return []

    window = max(
        1,
        int(window_size),
    )

    result: list[float] = []

    for index in range(len(cleaned)):
        start = max(
            0,
            index - window + 1,
        )

        window_values = cleaned[
            start:index + 1
        ]

        result.append(
            historical_standard_deviation(
                window_values
            )
        )

    return result


# ============================================================
# TREND ANALYSIS
# ============================================================


def calculate_trend(
    values: Sequence[Any],
) -> float:
    """
    Estimate the linear trend of historical values.

    A positive value indicates an increasing trend.
    A negative value indicates a decreasing trend.
    A value near zero indicates a relatively stable trend.

    The result represents the approximate change per
    observation.
    """
    cleaned = _clean_values(values)

    count = len(cleaned)

    if count < 2:
        return 0.0

    x_values = list(
        range(count)
    )

    x_mean = historical_mean(
        x_values
    )

    y_mean = historical_mean(
        cleaned
    )

    numerator = sum(
        (
            x - x_mean
        ) * (
            y - y_mean
        )
        for x, y in zip(
            x_values,
            cleaned,
        )
    )

    denominator = sum(
        (
            x - x_mean
        ) ** 2
        for x in x_values
    )

    if abs(denominator) < EPSILON:
        return 0.0

    return numerator / denominator


def trend_direction(
    values: Sequence[Any],
    threshold: float = 0.0,
) -> str:
    """
    Classify the historical trend.

    Returns:

        "increasing"
        "decreasing"
        "stable"
    """
    trend = calculate_trend(values)

    threshold_value = abs(
        _safe_float(threshold)
    )

    if trend > threshold_value:
        return "increasing"

    if trend < -threshold_value:
        return "decreasing"

    return "stable"


def trend_strength(
    values: Sequence[Any],
) -> float:
    """
    Estimate normalized trend strength.

    Returns:
        Value between 0.0 and 1.0.
    """
    cleaned = _clean_values(values)

    if len(cleaned) < 2:
        return 0.0

    trend = abs(
        calculate_trend(cleaned)
    )

    average = abs(
        historical_mean(cleaned)
    )

    if average < EPSILON:
        return 1.0 if trend > 0 else 0.0

    return min(
        1.0,
        trend / average,
    )


# ============================================================
# CHANGE ANALYSIS
# ============================================================


def absolute_change(
    current_value: float,
    previous_value: float,
) -> float:
    """
    Calculate absolute change.
    """
    return (
        _safe_float(current_value)
        - _safe_float(previous_value)
    )


def percentage_change(
    current_value: float,
    previous_value: float,
) -> float:
    """
    Calculate percentage change between two observations.

    Returns:
        Percentage change.
    """
    current = _safe_float(
        current_value
    )

    previous = _safe_float(
        previous_value
    )

    if abs(previous) < EPSILON:
        return 0.0

    return (
        (current - previous)
        / abs(previous)
    ) * 100.0


def change_rate(
    values: Sequence[Any],
) -> float:
    """
    Calculate the average change per observation.

    Returns:
        Average first difference.
    """
    cleaned = _clean_values(values)

    if len(cleaned) < 2:
        return 0.0

    differences = [
        cleaned[index]
        - cleaned[index - 1]
        for index in range(
            1,
            len(cleaned),
        )
    ]

    return historical_mean(
        differences
    )


# ============================================================
# VOLATILITY
# ============================================================


def volatility_score(
    values: Sequence[Any],
) -> float:
    """
    Calculate a normalized historical volatility score.

    The score is based on the coefficient of variation:

        standard deviation / |mean|

    Returns:
        Value between 0.0 and 1.0.
    """
    cleaned = _clean_values(values)

    if len(cleaned) < 2:
        return 0.0

    mean = abs(
        historical_mean(cleaned)
    )

    standard_deviation = (
        historical_standard_deviation(
            cleaned
        )
    )

    if mean < EPSILON:
        return 1.0 if standard_deviation > 0 else 0.0

    coefficient = (
        standard_deviation / mean
    )

    return min(
        1.0,
        coefficient,
    )


# ============================================================
# BASELINE ANALYSIS
# ============================================================


def calculate_baseline(
    values: Sequence[Any],
    window_size: int = DEFAULT_WINDOW_SIZE,
) -> float:
    """
    Calculate a historical baseline.

    The baseline is the average of the most recent
    observations inside the requested window.
    """
    cleaned = _clean_values(values)

    if not cleaned:
        return 0.0

    window = max(
        1,
        int(window_size),
    )

    recent_values = cleaned[
        -window:
    ]

    return historical_mean(
        recent_values
    )


def deviation_from_baseline(
    current_value: float,
    values: Sequence[Any],
    window_size: int = DEFAULT_WINDOW_SIZE,
) -> float:
    """
    Calculate percentage deviation from the historical baseline.
    """
    baseline = calculate_baseline(
        values,
        window_size,
    )

    current = _safe_float(
        current_value
    )

    if abs(baseline) < EPSILON:
        return 0.0

    return (
        (current - baseline)
        / abs(baseline)
    ) * 100.0


# ============================================================
# Z-SCORE / ANOMALY FEATURES
# ============================================================


def z_score(
    value: float,
    historical_values: Sequence[Any],
) -> float:
    """
    Calculate the z-score of a value against historical data.

    Returns:
        Number of standard deviations from the historical mean.
    """
    cleaned = _clean_values(
        historical_values
    )

    if len(cleaned) < 2:
        return 0.0

    mean = historical_mean(
        cleaned
    )

    standard_deviation = (
        historical_standard_deviation(
            cleaned
        )
    )

    if standard_deviation < EPSILON:
        return 0.0

    return (
        _safe_float(value)
        - mean
    ) / standard_deviation


def anomaly_score(
    value: float,
    historical_values: Sequence[Any],
    anomaly_z_score: float = DEFAULT_ANOMALY_Z_SCORE,
) -> float:
    """
    Convert a historical z-score into a normalized anomaly score.

    Returns:
        Value between 0.0 and 1.0.
    """
    score = abs(
        z_score(
            value,
            historical_values,
        )
    )

    threshold = max(
        EPSILON,
        _safe_float(
            anomaly_z_score,
            DEFAULT_ANOMALY_Z_SCORE,
        ),
    )

    return min(
        1.0,
        score / threshold,
    )


def is_historical_anomaly(
    value: float,
    historical_values: Sequence[Any],
    threshold: float = DEFAULT_ANOMALY_Z_SCORE,
) -> bool:
    """
    Determine whether a value is statistically unusual
    compared with historical observations.
    """
    return abs(
        z_score(
            value,
            historical_values,
        )
    ) >= abs(
        _safe_float(
            threshold,
            DEFAULT_ANOMALY_Z_SCORE,
        )
    )


# ============================================================
# PERCENTILE
# ============================================================


def historical_percentile(
    values: Sequence[Any],
    percentile: float,
) -> float:
    """
    Calculate a percentile using linear interpolation.

    Args:
        values: Historical observations.
        percentile: Percentile from 0 to 100.

    Returns:
        Percentile value.
    """
    cleaned = sorted(
        _clean_values(values)
    )

    if not cleaned:
        return 0.0

    requested = max(
        0.0,
        min(
            100.0,
            _safe_float(percentile),
        ),
    )

    if len(cleaned) == 1:
        return cleaned[0]

    position = (
        requested / 100.0
    ) * (
        len(cleaned) - 1
    )

    lower_index = int(
        math.floor(position)
    )

    upper_index = int(
        math.ceil(position)
    )

    if lower_index == upper_index:
        return cleaned[lower_index]

    lower_value = cleaned[
        lower_index
    ]

    upper_value = cleaned[
        upper_index
    ]

    fraction = (
        position - lower_index
    )

    return (
        lower_value
        + (
            upper_value
            - lower_value
        )
        * fraction
    )


# ============================================================
# LOAD GROWTH
# ============================================================


def load_growth_rate(
    historical_load: Sequence[Any],
) -> float:
    """
    Calculate the percentage growth between the first and
    latest historical load values.

    Returns:
        Percentage growth.
    """
    cleaned = _clean_values(
        historical_load
    )

    if len(cleaned) < 2:
        return 0.0

    first = cleaned[0]
    latest = cleaned[-1]

    if abs(first) < EPSILON:
        return 0.0

    return (
        (latest - first)
        / abs(first)
    ) * 100.0


def recent_load_growth(
    historical_load: Sequence[Any],
    window_size: int = DEFAULT_WINDOW_SIZE,
) -> float:
    """
    Calculate percentage growth over the most recent
    historical window.
    """
    cleaned = _clean_values(
        historical_load
    )

    window = max(
        2,
        int(window_size),
    )

    if len(cleaned) < 2:
        return 0.0

    recent = cleaned[
        -window:
    ]

    if len(recent) < 2:
        return 0.0

    return load_growth_rate(
        recent
    )


# ============================================================
# PERSISTENCE
# ============================================================


def persistence_ratio(
    values: Sequence[Any],
    threshold: float,
) -> float:
    """
    Calculate the fraction of historical observations
    above a threshold.

    Returns:
        Value between 0.0 and 1.0.
    """
    cleaned = _clean_values(values)

    if not cleaned:
        return 0.0

    threshold_value = _safe_float(
        threshold
    )

    count = sum(
        value >= threshold_value
        for value in cleaned
    )

    return count / len(cleaned)


def high_load_persistence(
    loading_values: Sequence[Any],
    threshold_percent: float = 80.0,
) -> float:
    """
    Calculate how persistently an asset has operated
    above a high-loading threshold.

    Returns:
        Value between 0.0 and 1.0.
    """
    return persistence_ratio(
        loading_values,
        threshold_percent,
    )


# ============================================================
# HISTORICAL FEATURE EXTRACTION
# ============================================================


def extract_historical_features(
    values: Sequence[Any],
    current_value: float | None = None,
    window_size: int = DEFAULT_WINDOW_SIZE,
) -> dict[str, float | bool | str]:
    """
    Extract a standardized set of historical features.

    Args:
        values:
            Historical observations ordered from oldest
            to newest.

        current_value:
            Optional current observation.

        window_size:
            Number of recent observations used for
            rolling calculations.

    Returns:
        Dictionary of historical features.
    """
    cleaned = _clean_values(
        values
    )

    if not cleaned:
        return {
            "sample_count": 0.0,
            "mean": 0.0,
            "minimum": 0.0,
            "maximum": 0.0,
            "range": 0.0,
            "variance": 0.0,
            "standard_deviation": 0.0,
            "trend": 0.0,
            "trend_strength": 0.0,
            "volatility_score": 0.0,
            "baseline": 0.0,
            "load_growth_percent": 0.0,
            "recent_load_growth_percent": 0.0,
            "high_value_persistence": 0.0,
            "current_deviation_from_baseline": 0.0,
            "current_z_score": 0.0,
            "current_anomaly_score": 0.0,
            "current_is_anomaly": False,
            "trend_direction": "stable",
        }

    baseline = calculate_baseline(
        cleaned,
        window_size,
    )

    if current_value is None:
        current = cleaned[-1]
    else:
        current = _safe_float(
            current_value
        )

    current_z = z_score(
        current,
        cleaned,
    )

    current_anomaly = anomaly_score(
        current,
        cleaned,
    )

    return {
        "sample_count": float(
            len(cleaned)
        ),
        "mean": historical_mean(
            cleaned
        ),
        "minimum": historical_minimum(
            cleaned
        ),
        "maximum": historical_maximum(
            cleaned
        ),
        "range": historical_range(
            cleaned
        ),
        "variance": historical_variance(
            cleaned
        ),
        "standard_deviation": historical_standard_deviation(
            cleaned
        ),
        "trend": calculate_trend(
            cleaned
        ),
        "trend_strength": trend_strength(
            cleaned
        ),
        "volatility_score": volatility_score(
            cleaned
        ),
        "baseline": baseline,
        "load_growth_percent": load_growth_rate(
            cleaned
        ),
        "recent_load_growth_percent": recent_load_growth(
            cleaned,
            window_size,
        ),
        "high_value_persistence": persistence_ratio(
            cleaned,
            baseline,
        ),
        "current_deviation_from_baseline": deviation_from_baseline(
            current,
            cleaned,
            window_size,
        ),
        "current_z_score": current_z,
        "current_anomaly_score": current_anomaly,
        "current_is_anomaly": is_historical_anomaly(
            current,
            cleaned,
        ),
        "trend_direction": trend_direction(
            cleaned
        ),
    }


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "historical_mean",
    "historical_minimum",
    "historical_maximum",
    "historical_range",
    "historical_variance",
    "historical_standard_deviation",
    "moving_average",
    "moving_standard_deviation",
    "calculate_trend",
    "trend_direction",
    "trend_strength",
    "absolute_change",
    "percentage_change",
    "change_rate",
    "volatility_score",
    "calculate_baseline",
    "deviation_from_baseline",
    "z_score",
    "anomaly_score",
    "is_historical_anomaly",
    "historical_percentile",
    "load_growth_rate",
    "recent_load_growth",
    "persistence_ratio",
    "high_load_persistence",
    "extract_historical_features",
]