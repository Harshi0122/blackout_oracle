"""
Blackout Oracle - Electrical Feature Engineering.

Converts raw electrical measurements into normalized features
that can be used by:

- Risk scoring
- Anomaly detection
- Failure prediction
- Blackout prediction
- Grid stability analysis
- AI investigation
- Simulation

The functions in this module are deterministic and do not
directly control physical grid equipment.
"""

from __future__ import annotations

import math
from typing import Any


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_VOLTAGE_TOLERANCE_PERCENT = 5.0
DEFAULT_FREQUENCY_NOMINAL_HZ = 50.0
DEFAULT_FREQUENCY_TOLERANCE_HZ = 0.5

DEFAULT_LOADING_WARNING_PERCENT = 80.0
DEFAULT_LOADING_CRITICAL_PERCENT = 100.0

DEFAULT_POWER_FACTOR_WARNING = 0.90

EPSILON = 1e-9


# ============================================================
# BASIC VALIDATION
# ============================================================


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Convert a value to float safely.

    Invalid, missing, NaN, and infinite values are replaced
    with the supplied default.
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
# VOLTAGE FEATURES
# ============================================================


def voltage_deviation(
    actual_voltage: float,
    nominal_voltage: float,
) -> float:
    """
    Calculate voltage deviation as a percentage.

    Example:

        nominal = 110 kV
        actual  = 105 kV

        deviation ≈ -4.55%
    """
    actual = _safe_float(actual_voltage)
    nominal = _safe_float(nominal_voltage)

    if abs(nominal) < EPSILON:
        return 0.0

    return (
        (actual - nominal)
        / nominal
    ) * 100.0


def voltage_deviation_magnitude(
    actual_voltage: float,
    nominal_voltage: float,
) -> float:
    """
    Return the absolute voltage deviation percentage.
    """
    return abs(
        voltage_deviation(
            actual_voltage,
            nominal_voltage,
        )
    )


def voltage_stress_score(
    actual_voltage: float,
    nominal_voltage: float,
    tolerance_percent: float = DEFAULT_VOLTAGE_TOLERANCE_PERCENT,
) -> float:
    """
    Calculate normalized voltage stress.

    Returns:
        Value between 0.0 and 1.0.

    0.0 = no significant deviation.
    1.0 = severe voltage deviation.

    This is a feature score, not a protection decision.
    """
    deviation = voltage_deviation_magnitude(
        actual_voltage,
        nominal_voltage,
    )

    tolerance = max(
        _safe_float(tolerance_percent),
        EPSILON,
    )

    stress = deviation / (
        tolerance * 2.0
    )

    return _clamp(stress)


def voltage_within_limits(
    actual_voltage: float,
    nominal_voltage: float,
    tolerance_percent: float = DEFAULT_VOLTAGE_TOLERANCE_PERCENT,
) -> bool:
    """
    Determine whether voltage is within the configured
    analytical tolerance.
    """
    deviation = voltage_deviation_magnitude(
        actual_voltage,
        nominal_voltage,
    )

    return deviation <= abs(
        _safe_float(tolerance_percent)
    )


# ============================================================
# CURRENT FEATURES
# ============================================================


def current_loading_percent(
    actual_current: float,
    rated_current: float,
) -> float:
    """
    Calculate current loading as a percentage of rated current.
    """
    actual = max(
        0.0,
        _safe_float(actual_current),
    )

    rated = _safe_float(rated_current)

    if rated <= EPSILON:
        return 0.0

    return (
        actual / rated
    ) * 100.0


def loading_stress_score(
    loading_percent: float,
    warning_percent: float = DEFAULT_LOADING_WARNING_PERCENT,
    critical_percent: float = DEFAULT_LOADING_CRITICAL_PERCENT,
) -> float:
    """
    Convert loading percentage into a normalized stress score.

    Below warning level:
        Low stress.

    Between warning and critical:
        Increasing stress.

    At or above critical:
        Maximum stress.
    """
    loading = max(
        0.0,
        _safe_float(loading_percent),
    )

    warning = _safe_float(
        warning_percent,
        DEFAULT_LOADING_WARNING_PERCENT,
    )

    critical = _safe_float(
        critical_percent,
        DEFAULT_LOADING_CRITICAL_PERCENT,
    )

    if critical <= warning:
        return 1.0 if loading >= warning else 0.0

    if loading <= warning:
        return 0.0

    if loading >= critical:
        return 1.0

    return _clamp(
        (loading - warning)
        / (critical - warning)
    )


def is_overloaded(
    loading_percent: float,
    threshold_percent: float = DEFAULT_LOADING_CRITICAL_PERCENT,
) -> bool:
    """
    Determine whether an asset is analytically overloaded.
    """
    return (
        _safe_float(loading_percent)
        >= _safe_float(threshold_percent)
    )


# ============================================================
# POWER FEATURES
# ============================================================


def apparent_power_mva(
    active_power_mw: float,
    reactive_power_mvar: float,
) -> float:
    """
    Calculate apparent power.

    S = sqrt(P² + Q²)
    """
    active = _safe_float(active_power_mw)
    reactive = _safe_float(reactive_power_mvar)

    return math.sqrt(
        active * active
        + reactive * reactive
    )


def calculate_power_factor(
    active_power_mw: float,
    apparent_power_mva: float | None = None,
    reactive_power_mvar: float | None = None,
) -> float:
    """
    Calculate power factor.

    If apparent power is supplied:

        PF = |P| / |S|

    Otherwise, apparent power is calculated from P and Q.

    Returns:
        Value between 0.0 and 1.0.
    """
    active = abs(
        _safe_float(active_power_mw)
    )

    if apparent_power_mva is None:
        reactive = _safe_float(
            reactive_power_mvar
        )

        apparent = math.sqrt(
            active * active
            + reactive * reactive
        )

    else:
        apparent = abs(
            _safe_float(apparent_power_mva)
        )

    if apparent < EPSILON:
        return 1.0

    return _clamp(
        active / apparent
    )


def reactive_power_ratio(
    active_power_mw: float,
    reactive_power_mvar: float,
) -> float:
    """
    Calculate the magnitude of reactive power relative
    to active power.
    """
    active = abs(
        _safe_float(active_power_mw)
    )

    reactive = abs(
        _safe_float(reactive_power_mvar)
    )

    if active < EPSILON:
        return 0.0

    return reactive / active


def power_factor_stress_score(
    power_factor: float,
    warning_threshold: float = DEFAULT_POWER_FACTOR_WARNING,
) -> float:
    """
    Convert power factor into a normalized stress score.

    Higher score means poorer power factor.
    """
    pf = _clamp(
        abs(_safe_float(power_factor))
    )

    threshold = _clamp(
        _safe_float(warning_threshold)
    )

    if pf >= threshold:
        return 0.0

    if threshold <= EPSILON:
        return 1.0

    return _clamp(
        (threshold - pf)
        / threshold
    )


# ============================================================
# FREQUENCY FEATURES
# ============================================================


def frequency_deviation(
    actual_frequency_hz: float,
    nominal_frequency_hz: float = DEFAULT_FREQUENCY_NOMINAL_HZ,
) -> float:
    """
    Calculate frequency deviation in Hz.
    """
    actual = _safe_float(
        actual_frequency_hz
    )

    nominal = _safe_float(
        nominal_frequency_hz,
        DEFAULT_FREQUENCY_NOMINAL_HZ,
    )

    return actual - nominal


def frequency_deviation_percent(
    actual_frequency_hz: float,
    nominal_frequency_hz: float = DEFAULT_FREQUENCY_NOMINAL_HZ,
) -> float:
    """
    Calculate frequency deviation as a percentage.
    """
    nominal = _safe_float(
        nominal_frequency_hz,
        DEFAULT_FREQUENCY_NOMINAL_HZ,
    )

    if abs(nominal) < EPSILON:
        return 0.0

    return (
        frequency_deviation(
            actual_frequency_hz,
            nominal,
        )
        / nominal
    ) * 100.0


def frequency_stress_score(
    actual_frequency_hz: float,
    nominal_frequency_hz: float = DEFAULT_FREQUENCY_NOMINAL_HZ,
    tolerance_hz: float = DEFAULT_FREQUENCY_TOLERANCE_HZ,
) -> float:
    """
    Calculate normalized frequency stress.

    Returns:
        Value between 0.0 and 1.0.
    """
    deviation = abs(
        frequency_deviation(
            actual_frequency_hz,
            nominal_frequency_hz,
        )
    )

    tolerance = max(
        _safe_float(
            tolerance_hz,
            DEFAULT_FREQUENCY_TOLERANCE_HZ,
        ),
        EPSILON,
    )

    return _clamp(
        deviation / (tolerance * 2.0)
    )


def frequency_within_limits(
    actual_frequency_hz: float,
    nominal_frequency_hz: float = DEFAULT_FREQUENCY_NOMINAL_HZ,
    tolerance_hz: float = DEFAULT_FREQUENCY_TOLERANCE_HZ,
) -> bool:
    """
    Determine whether frequency is within the analytical
    tolerance.
    """
    return (
        abs(
            frequency_deviation(
                actual_frequency_hz,
                nominal_frequency_hz,
            )
        )
        <= abs(
            _safe_float(
                tolerance_hz,
                DEFAULT_FREQUENCY_TOLERANCE_HZ,
            )
        )
    )


# ============================================================
# RATE OF CHANGE
# ============================================================


def rate_of_change(
    current_value: float,
    previous_value: float,
    elapsed_seconds: float,
) -> float:
    """
    Calculate the rate of change of a measurement.

    Returns:
        Change per second.
    """
    current = _safe_float(current_value)
    previous = _safe_float(previous_value)

    seconds = _safe_float(
        elapsed_seconds
    )

    if seconds <= EPSILON:
        return 0.0

    return (
        current - previous
    ) / seconds


def percentage_change(
    current_value: float,
    previous_value: float,
) -> float:
    """
    Calculate percentage change between two values.
    """
    current = _safe_float(current_value)
    previous = _safe_float(previous_value)

    if abs(previous) < EPSILON:
        return 0.0

    return (
        (current - previous)
        / abs(previous)
    ) * 100.0


# ============================================================
# VOLTAGE / POWER COMBINATION
# ============================================================


def electrical_stress_score(
    voltage_stress: float,
    loading_stress: float,
    frequency_stress: float,
    power_factor_stress: float = 0.0,
) -> float:
    """
    Combine major electrical stress indicators into a
    normalized electrical stress score.

    The weighting is intentionally deterministic:

        Voltage          25%
        Loading          35%
        Frequency        25%
        Power factor     15%

    Returns:
        Value between 0.0 and 1.0.

    This score is an analytical feature and should not be
    interpreted as a physical protection threshold.
    """
    voltage = _clamp(
        _safe_float(voltage_stress)
    )

    loading = _clamp(
        _safe_float(loading_stress)
    )

    frequency = _clamp(
        _safe_float(frequency_stress)
    )

    power_factor = _clamp(
        _safe_float(power_factor_stress)
    )

    score = (
        voltage * 0.25
        + loading * 0.35
        + frequency * 0.25
        + power_factor * 0.15
    )

    return _clamp(score)


# ============================================================
# FEATURE EXTRACTION
# ============================================================


def extract_electrical_features(
    data: dict[str, Any],
) -> dict[str, float | bool]:
    """
    Extract a standardized electrical feature set from
    a dictionary of raw measurements.

    Supported input keys include:

        voltage
        nominal_voltage
        current
        rated_current
        active_power
        reactive_power
        apparent_power
        power_factor
        frequency
        nominal_frequency
        previous_power
        previous_voltage
        previous_current
        elapsed_seconds

    Returns:
        Dictionary containing derived electrical features.
    """

    voltage = _safe_float(
        data.get("voltage")
    )

    nominal_voltage = _safe_float(
        data.get("nominal_voltage")
    )

    current = _safe_float(
        data.get("current")
    )

    rated_current = _safe_float(
        data.get("rated_current")
    )

    active_power = _safe_float(
        data.get("active_power")
    )

    reactive_power = _safe_float(
        data.get("reactive_power")
    )

    apparent_power_input = data.get(
        "apparent_power"
    )

    frequency = _safe_float(
        data.get("frequency"),
        DEFAULT_FREQUENCY_NOMINAL_HZ,
    )

    nominal_frequency = _safe_float(
        data.get("nominal_frequency"),
        DEFAULT_FREQUENCY_NOMINAL_HZ,
    )

    # --------------------------------------------------------
    # Apparent power
    # --------------------------------------------------------

    if apparent_power_input is None:
        apparent_power = apparent_power_mva(
            active_power,
            reactive_power,
        )
    else:
        apparent_power = max(
            0.0,
            _safe_float(
                apparent_power_input
            ),
        )

    # --------------------------------------------------------
    # Power factor
    # --------------------------------------------------------

    power_factor = calculate_power_factor(
        active_power,
        apparent_power,
    )

    # --------------------------------------------------------
    # Voltage
    # --------------------------------------------------------

    voltage_dev = voltage_deviation(
        voltage,
        nominal_voltage,
    )

    voltage_stress = voltage_stress_score(
        voltage,
        nominal_voltage,
    )

    # --------------------------------------------------------
    # Current / loading
    # --------------------------------------------------------

    loading = current_loading_percent(
        current,
        rated_current,
    )

    loading_stress = loading_stress_score(
        loading
    )

    overloaded = is_overloaded(
        loading
    )

    # --------------------------------------------------------
    # Frequency
    # --------------------------------------------------------

    frequency_dev = frequency_deviation(
        frequency,
        nominal_frequency,
    )

    frequency_stress = frequency_stress_score(
        frequency,
        nominal_frequency,
    )

    # --------------------------------------------------------
    # Power factor
    # --------------------------------------------------------

    pf_stress = power_factor_stress_score(
        power_factor
    )

    # --------------------------------------------------------
    # Combined electrical stress
    # --------------------------------------------------------

    electrical_stress = electrical_stress_score(
        voltage_stress=voltage_stress,
        loading_stress=loading_stress,
        frequency_stress=frequency_stress,
        power_factor_stress=pf_stress,
    )

    # --------------------------------------------------------
    # Optional temporal features
    # --------------------------------------------------------

    previous_power = data.get(
        "previous_power"
    )

    previous_voltage = data.get(
        "previous_voltage"
    )

    previous_current = data.get(
        "previous_current"
    )

    elapsed_seconds = _safe_float(
        data.get("elapsed_seconds"),
        0.0,
    )

    if previous_power is not None:
        power_rate = rate_of_change(
            active_power,
            _safe_float(previous_power),
            elapsed_seconds,
        )
    else:
        power_rate = 0.0

    if previous_voltage is not None:
        voltage_rate = rate_of_change(
            voltage,
            _safe_float(previous_voltage),
            elapsed_seconds,
        )
    else:
        voltage_rate = 0.0

    if previous_current is not None:
        current_rate = rate_of_change(
            current,
            _safe_float(previous_current),
            elapsed_seconds,
        )
    else:
        current_rate = 0.0

    # --------------------------------------------------------
    # Final feature dictionary
    # --------------------------------------------------------

    return {
        "voltage_deviation_percent": voltage_dev,
        "voltage_deviation_magnitude_percent": abs(
            voltage_dev
        ),
        "voltage_stress_score": voltage_stress,
        "voltage_within_limits": voltage_within_limits(
            voltage,
            nominal_voltage,
        ),
        "loading_percent": loading,
        "loading_stress_score": loading_stress,
        "overloaded": overloaded,
        "apparent_power_mva": apparent_power,
        "power_factor": power_factor,
        "power_factor_stress_score": pf_stress,
        "reactive_power_ratio": reactive_power_ratio(
            active_power,
            reactive_power,
        ),
        "frequency_deviation_hz": frequency_dev,
        "frequency_deviation_percent": frequency_deviation_percent(
            frequency,
            nominal_frequency,
        ),
        "frequency_stress_score": frequency_stress,
        "frequency_within_limits": frequency_within_limits(
            frequency,
            nominal_frequency,
        ),
        "power_rate_of_change": power_rate,
        "voltage_rate_of_change": voltage_rate,
        "current_rate_of_change": current_rate,
        "electrical_stress_score": electrical_stress,
    }


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "voltage_deviation",
    "voltage_deviation_magnitude",
    "voltage_stress_score",
    "voltage_within_limits",
    "current_loading_percent",
    "loading_stress_score",
    "is_overloaded",
    "apparent_power_mva",
    "calculate_power_factor",
    "reactive_power_ratio",
    "power_factor_stress_score",
    "frequency_deviation",
    "frequency_deviation_percent",
    "frequency_stress_score",
    "frequency_within_limits",
    "rate_of_change",
    "percentage_change",
    "electrical_stress_score",
    "extract_electrical_features",
]