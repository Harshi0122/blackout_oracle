"""
Blackout Oracle - Baseline Forecasting Model.

A lightweight, dependency-free forecasting model for grid
measurements such as:

- Electrical demand
- Power generation
- Frequency
- Voltage
- Asset loading
- Other time-series measurements

This module provides simple and interpretable forecasting
methods suitable as a baseline before introducing more
advanced ML/time-series models.

Supported methods:

- Persistence forecasting
- Moving-average forecasting
- Weighted moving-average forecasting
- Linear-trend forecasting
- Exponential smoothing

No external ML dependencies are required.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence


# ============================================================
# CONSTANTS
# ============================================================

EPSILON = 1e-12


# ============================================================
# ENUMS
# ============================================================


class ForecastMethod:
    """Supported baseline forecasting methods."""

    PERSISTENCE = "persistence"
    MOVING_AVERAGE = "moving_average"
    WEIGHTED_MOVING_AVERAGE = "weighted_moving_average"
    LINEAR_TREND = "linear_trend"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"


# ============================================================
# CONFIGURATION
# ============================================================


@dataclass
class BaselineForecastConfig:
    """
    Configuration for the baseline forecasting model.
    """

    window_size: int = 5

    smoothing_alpha: float = 0.30

    default_method: str = (
        ForecastMethod.EXPONENTIAL_SMOOTHING
    )

    minimum_history: int = 2

    def __post_init__(self) -> None:
        """Validate forecasting configuration."""

        if self.window_size < 1:
            raise ValueError(
                "window_size must be at least 1."
            )

        if not 0.0 < self.smoothing_alpha <= 1.0:
            raise ValueError(
                "smoothing_alpha must be greater than "
                "0 and less than or equal to 1."
            )

        if self.minimum_history < 1:
            raise ValueError(
                "minimum_history must be at least 1."
            )

        valid_methods = {
            ForecastMethod.PERSISTENCE,
            ForecastMethod.MOVING_AVERAGE,
            ForecastMethod.WEIGHTED_MOVING_AVERAGE,
            ForecastMethod.LINEAR_TREND,
            ForecastMethod.EXPONENTIAL_SMOOTHING,
        }

        if self.default_method not in valid_methods:
            raise ValueError(
                f"Unsupported forecasting method: "
                f"{self.default_method}"
            )


# ============================================================
# FORECAST RESULT
# ============================================================


@dataclass
class ForecastResult:
    """
    Result returned by the baseline forecasting model.
    """

    forecast: list[float]

    method: str

    horizon: int

    last_observed: float

    confidence: float

    lower_bound: list[float] = field(
        default_factory=list
    )

    upper_bound: list[float] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def next_value(self) -> float | None:
        """Return the first forecasted value."""

        if not self.forecast:
            return None

        return self.forecast[0]

    def to_dict(self) -> dict[str, Any]:
        """Convert the forecast result to a dictionary."""

        return {
            "forecast": list(
                self.forecast
            ),
            "method": self.method,
            "horizon": self.horizon,
            "last_observed": self.last_observed,
            "next_value": self.next_value,
            "confidence": self.confidence,
            "lower_bound": list(
                self.lower_bound
            ),
            "upper_bound": list(
                self.upper_bound
            ),
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def _validate_history(
    history: Iterable[Any],
    minimum: int = 1,
) -> list[float]:
    """
    Validate and convert historical observations into floats.
    """

    values: list[float] = []

    for value in history:
        try:
            numeric = float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"Invalid historical value: {value!r}"
            ) from exc

        if not math.isfinite(numeric):
            raise ValueError(
                f"Historical values must be finite, "
                f"got {value!r}."
            )

        values.append(numeric)

    if len(values) < minimum:
        raise ValueError(
            f"At least {minimum} historical "
            f"observations are required."
        )

    return values


def _validate_horizon(
    horizon: int,
) -> int:
    """Validate forecast horizon."""

    try:
        horizon = int(horizon)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "Forecast horizon must be an integer."
        ) from exc

    if horizon < 1:
        raise ValueError(
            "Forecast horizon must be at least 1."
        )

    return horizon


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    """Clamp a numeric value."""

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


# ============================================================
# BASELINE FORECAST MODEL
# ============================================================


class BaselineForecastModel:
    """
    Simple dependency-free forecasting model.

    The model is intended to provide a robust baseline for
    Blackout Oracle before more sophisticated forecasting
    algorithms are introduced.
    """

    def __init__(
        self,
        config: BaselineForecastConfig | None = None,
    ) -> None:
        """Initialize the forecasting model."""

        self.config = (
            config
            if config is not None
            else BaselineForecastConfig()
        )

    # ========================================================
    # GENERIC FORECAST
    # ========================================================

    def forecast(
        self,
        history: Iterable[Any],
        horizon: int = 1,
        method: str | None = None,
    ) -> ForecastResult:
        """
        Generate a forecast using the selected method.
        """

        values = _validate_history(
            history,
            minimum=self.config.minimum_history,
        )

        horizon = _validate_horizon(
            horizon
        )

        selected_method = (
            method
            if method is not None
            else self.config.default_method
        )

        if selected_method == (
            ForecastMethod.PERSISTENCE
        ):
            forecast_values = (
                self.persistence(
                    values,
                    horizon,
                )
            )

        elif selected_method == (
            ForecastMethod.MOVING_AVERAGE
        ):
            forecast_values = (
                self.moving_average(
                    values,
                    horizon,
                )
            )

        elif selected_method == (
            ForecastMethod.WEIGHTED_MOVING_AVERAGE
        ):
            forecast_values = (
                self.weighted_moving_average(
                    values,
                    horizon,
                )
            )

        elif selected_method == (
            ForecastMethod.LINEAR_TREND
        ):
            forecast_values = (
                self.linear_trend(
                    values,
                    horizon,
                )
            )

        elif selected_method == (
            ForecastMethod.EXPONENTIAL_SMOOTHING
        ):
            forecast_values = (
                self.exponential_smoothing(
                    values,
                    horizon,
                )
            )

        else:
            raise ValueError(
                f"Unsupported forecasting method: "
                f"{selected_method}"
            )

        confidence = (
            self._estimate_confidence(
                values
            )
        )

        lower_bound, upper_bound = (
            self._prediction_bounds(
                values,
                forecast_values,
                confidence,
            )
        )

        return ForecastResult(
            forecast=[
                round(
                    value,
                    6,
                )
                for value in forecast_values
            ],
            method=selected_method,
            horizon=horizon,
            last_observed=values[-1],
            confidence=round(
                confidence,
                4,
            ),
            lower_bound=[
                round(
                    value,
                    6,
                )
                for value in lower_bound
            ],
            upper_bound=[
                round(
                    value,
                    6,
                )
                for value in upper_bound
            ],
            metadata={
                "model": (
                    "BaselineForecastModel"
                ),
                "version": "1.0",
                "history_size": len(values),
                "window_size": (
                    self.config.window_size
                ),
            },
        )

    # ========================================================
    # PERSISTENCE
    # ========================================================

    @staticmethod
    def persistence(
        history: Sequence[float],
        horizon: int,
    ) -> list[float]:
        """
        Persistence forecast.

        Every future value is assumed to equal the latest
        observed value.
        """

        if not history:
            raise ValueError(
                "History cannot be empty."
            )

        horizon = _validate_horizon(
            horizon
        )

        last_value = float(
            history[-1]
        )

        return [
            last_value
            for _ in range(horizon)
        ]

    # ========================================================
    # MOVING AVERAGE
    # ========================================================

    def moving_average(
        self,
        history: Sequence[float],
        horizon: int,
    ) -> list[float]:
        """
        Simple moving-average forecast.

        The average of the latest configured window is used for
        all future points.
        """

        if not history:
            raise ValueError(
                "History cannot be empty."
            )

        horizon = _validate_horizon(
            horizon
        )

        window = min(
            self.config.window_size,
            len(history),
        )

        recent = history[
            -window:
        ]

        average = (
            sum(recent)
            / len(recent)
        )

        return [
            average
            for _ in range(horizon)
        ]

    # ========================================================
    # WEIGHTED MOVING AVERAGE
    # ========================================================

    def weighted_moving_average(
        self,
        history: Sequence[float],
        horizon: int,
    ) -> list[float]:
        """
        Weighted moving-average forecast.

        More recent observations receive greater weight.
        """

        if not history:
            raise ValueError(
                "History cannot be empty."
            )

        horizon = _validate_horizon(
            horizon
        )

        window = min(
            self.config.window_size,
            len(history),
        )

        recent = list(
            history[
                -window:
            ]
        )

        weights = list(
            range(
                1,
                len(recent) + 1,
            )
        )

        total_weight = sum(
            weights
        )

        forecast_value = sum(
            value * weight
            for value, weight
            in zip(
                recent,
                weights,
            )
        ) / total_weight

        return [
            forecast_value
            for _ in range(horizon)
        ]

    # ========================================================
    # LINEAR TREND
    # ========================================================

    @staticmethod
    def linear_trend(
        history: Sequence[float],
        horizon: int,
    ) -> list[float]:
        """
        Forecast using a least-squares linear trend.

        x = observation index
        y = observed value
        """

        if len(history) < 2:
            return (
                BaselineForecastModel.persistence(
                    history,
                    horizon,
                )
            )

        horizon = _validate_horizon(
            horizon
        )

        n = len(history)

        x_values = list(
            range(n)
        )

        x_mean = (
            sum(x_values)
            / n
        )

        y_mean = (
            sum(history)
            / n
        )

        numerator = sum(
            (
                x - x_mean
            )
            * (
                y - y_mean
            )
            for x, y
            in zip(
                x_values,
                history,
            )
        )

        denominator = sum(
            (
                x - x_mean
            )
            ** 2
            for x in x_values
        )

        if abs(denominator) <= EPSILON:
            slope = 0.0

        else:
            slope = (
                numerator
                / denominator
            )

        intercept = (
            y_mean
            - slope
            * x_mean
        )

        return [
            intercept
            + slope
            * (
                n + step
            )
            for step in range(
                horizon
            )
        ]

    # ========================================================
    # EXPONENTIAL SMOOTHING
    # ========================================================

    def exponential_smoothing(
        self,
        history: Sequence[float],
        horizon: int,
    ) -> list[float]:
        """
        Simple exponential smoothing.

        The latest smoothed value is extended into the future.
        """

        if not history:
            raise ValueError(
                "History cannot be empty."
            )

        horizon = _validate_horizon(
            horizon
        )

        alpha = (
            self.config.smoothing_alpha
        )

        smoothed = float(
            history[0]
        )

        for value in history[1:]:
            smoothed = (
                alpha
                * value
                + (
                    1.0
                    - alpha
                )
                * smoothed
            )

        return [
            smoothed
            for _ in range(horizon)
        ]

    # ========================================================
    # CONFIDENCE
    # ========================================================

    @staticmethod
    def _estimate_confidence(
        history: Sequence[float],
    ) -> float:
        """
        Estimate confidence from historical variability.

        This is a heuristic confidence score, not a calibrated
        statistical confidence interval.
        """

        if len(history) < 2:
            return 0.25

        mean_value = (
            sum(history)
            / len(history)
        )

        if abs(mean_value) <= EPSILON:
            mean_absolute = (
                sum(
                    abs(value)
                    for value in history
                )
                / len(history)
            )

            if mean_absolute <= EPSILON:
                return 1.0

            denominator = mean_absolute

        else:
            denominator = abs(
                mean_value
            )

        variance = (
            sum(
                (
                    value
                    - mean_value
                )
                ** 2
                for value in history
            )
            / len(history)
        )

        standard_deviation = math.sqrt(
            variance
        )

        coefficient_of_variation = (
            standard_deviation
            / denominator
        )

        return _clamp(
            1.0
            - coefficient_of_variation
        )

    # ========================================================
    # PREDICTION BOUNDS
    # ========================================================

    @staticmethod
    def _prediction_bounds(
        history: Sequence[float],
        forecast: Sequence[float],
        confidence: float,
    ) -> tuple[
        list[float],
        list[float],
    ]:
        """
        Produce simple heuristic forecast bounds.
        """

        if len(history) < 2:
            spread = 0.0

        else:
            mean_value = (
                sum(history)
                / len(history)
            )

            variance = (
                sum(
                    (
                        value
                        - mean_value
                    )
                    ** 2
                    for value in history
                )
                / len(history)
            )

            spread = math.sqrt(
                variance
            )

        uncertainty = (
            spread
            * (
                1.0
                + (
                    1.0
                    - confidence
                )
            )
        )

        lower = [
            value - uncertainty
            for value in forecast
        ]

        upper = [
            value + uncertainty
            for value in forecast
        ]

        return lower, upper

    # ========================================================
    # MODEL INFORMATION
    # ========================================================

    def model_info(
        self,
    ) -> dict[str, Any]:
        """
        Return information about the forecasting model.
        """

        return {
            "model_name": (
                "Baseline Forecast Model"
            ),
            "model_type": (
                "dependency_free_time_series_baseline"
            ),
            "version": "1.0",
            "trained": False,
            "methods": [
                ForecastMethod.PERSISTENCE,
                ForecastMethod.MOVING_AVERAGE,
                ForecastMethod.WEIGHTED_MOVING_AVERAGE,
                ForecastMethod.LINEAR_TREND,
                ForecastMethod.EXPONENTIAL_SMOOTHING,
            ],
            "default_method": (
                self.config.default_method
            ),
            "window_size": (
                self.config.window_size
            ),
            "smoothing_alpha": (
                self.config.smoothing_alpha
            ),
        }


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def forecast_series(
    history: Iterable[Any],
    horizon: int = 1,
    method: str = (
        ForecastMethod.EXPONENTIAL_SMOOTHING
    ),
    *,
    config: BaselineForecastConfig | None = None,
) -> ForecastResult:
    """
    Convenience function for forecasting a time series.
    """

    model = BaselineForecastModel(
        config=config
    )

    return model.forecast(
        history,
        horizon=horizon,
        method=method,
    )


def persistence_forecast(
    history: Iterable[Any],
    horizon: int = 1,
) -> ForecastResult:
    """
    Convenience function for persistence forecasting.
    """

    return forecast_series(
        history,
        horizon=horizon,
        method=ForecastMethod.PERSISTENCE,
    )


def moving_average_forecast(
    history: Iterable[Any],
    horizon: int = 1,
    *,
    window_size: int = 5,
) -> ForecastResult:
    """
    Convenience function for moving-average forecasting.
    """

    config = BaselineForecastConfig(
        window_size=window_size,
        default_method=(
            ForecastMethod.MOVING_AVERAGE
        ),
    )

    return forecast_series(
        history,
        horizon=horizon,
        method=ForecastMethod.MOVING_AVERAGE,
        config=config,
    )


def linear_trend_forecast(
    history: Iterable[Any],
    horizon: int = 1,
) -> ForecastResult:
    """
    Convenience function for linear-trend forecasting.
    """

    return forecast_series(
        history,
        horizon=horizon,
        method=ForecastMethod.LINEAR_TREND,
    )


def exponential_smoothing_forecast(
    history: Iterable[Any],
    horizon: int = 1,
    *,
    alpha: float = 0.30,
) -> ForecastResult:
    """
    Convenience function for exponential-smoothing forecasting.
    """

    config = BaselineForecastConfig(
        smoothing_alpha=alpha,
        default_method=(
            ForecastMethod.EXPONENTIAL_SMOOTHING
        ),
    )

    return forecast_series(
        history,
        horizon=horizon,
        method=(
            ForecastMethod.EXPONENTIAL_SMOOTHING
        ),
        config=config,
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "ForecastMethod",
    "BaselineForecastConfig",
    "ForecastResult",
    "BaselineForecastModel",
    "forecast_series",
    "persistence_forecast",
    "moving_average_forecast",
    "linear_trend_forecast",
    "exponential_smoothing_forecast",
]