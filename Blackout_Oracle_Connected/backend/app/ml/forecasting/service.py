"""
Blackout Oracle - Forecasting Service.

Application-level service for generating forecasts from historical
grid measurements.

This service wraps BaselineForecastModel and provides:

- Single-series forecasting
- Multiple-series forecasting
- Named grid-metric forecasting
- Multiple forecasting methods
- Forecast summaries
- Forecast comparison
- Batch processing
- Dashboard/API-friendly output

The service does not directly access the database or external APIs.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from app.ml.forecasting.baseline import (
    BaselineForecastConfig,
    BaselineForecastModel,
    ForecastMethod,
    ForecastResult,
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_HORIZON = 1

DEFAULT_METHOD = ForecastMethod.EXPONENTIAL_SMOOTHING


# ============================================================
# RESULT TYPES
# ============================================================


@dataclass
class ForecastServiceResult:
    """
    Result returned by the forecasting service.
    """

    success: bool = True

    message: str = ""

    forecasts: dict[str, ForecastResult] = field(
        default_factory=dict
    )

    errors: dict[str, str] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def total_forecasts(self) -> int:
        """Return the number of successful forecasts."""

        return len(
            self.forecasts
        )

    @property
    def error_count(self) -> int:
        """Return the number of failed forecasts."""

        return len(
            self.errors
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the service result to a dictionary."""

        return {
            "success": self.success,
            "message": self.message,
            "total_forecasts": (
                self.total_forecasts
            ),
            "error_count": (
                self.error_count
            ),
            "forecasts": {
                name: result.to_dict()
                for name, result
                in self.forecasts.items()
            },
            "errors": dict(
                self.errors
            ),
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# FORECAST SERVICE
# ============================================================


class ForecastingService:
    """
    High-level forecasting service.

    The service provides a stable application interface around
    the baseline forecasting model.
    """

    def __init__(
        self,
        model: BaselineForecastModel | None = None,
        config: BaselineForecastConfig | None = None,
    ) -> None:
        """
        Initialize the forecasting service.
        """

        if model is not None:
            self.model = model

        else:
            self.model = BaselineForecastModel(
                config=config
            )

    # ========================================================
    # SINGLE SERIES
    # ========================================================

    def forecast(
        self,
        history: Iterable[Any],
        horizon: int = DEFAULT_HORIZON,
        method: str | None = None,
    ) -> ForecastResult:
        """
        Generate a forecast for one time series.
        """

        selected_method = (
            method
            if method is not None
            else self.model.config.default_method
        )

        return self.model.forecast(
            history,
            horizon=horizon,
            method=selected_method,
        )

    # ========================================================
    # PERSISTENCE
    # ========================================================

    def forecast_persistence(
        self,
        history: Iterable[Any],
        horizon: int = DEFAULT_HORIZON,
    ) -> ForecastResult:
        """
        Generate a persistence forecast.
        """

        return self.forecast(
            history,
            horizon=horizon,
            method=ForecastMethod.PERSISTENCE,
        )

    # ========================================================
    # MOVING AVERAGE
    # ========================================================

    def forecast_moving_average(
        self,
        history: Iterable[Any],
        horizon: int = DEFAULT_HORIZON,
    ) -> ForecastResult:
        """
        Generate a moving-average forecast.
        """

        return self.forecast(
            history,
            horizon=horizon,
            method=ForecastMethod.MOVING_AVERAGE,
        )

    # ========================================================
    # WEIGHTED MOVING AVERAGE
    # ========================================================

    def forecast_weighted_moving_average(
        self,
        history: Iterable[Any],
        horizon: int = DEFAULT_HORIZON,
    ) -> ForecastResult:
        """
        Generate a weighted moving-average forecast.
        """

        return self.forecast(
            history,
            horizon=horizon,
            method=(
                ForecastMethod.WEIGHTED_MOVING_AVERAGE
            ),
        )

    # ========================================================
    # LINEAR TREND
    # ========================================================

    def forecast_linear_trend(
        self,
        history: Iterable[Any],
        horizon: int = DEFAULT_HORIZON,
    ) -> ForecastResult:
        """
        Generate a linear-trend forecast.
        """

        return self.forecast(
            history,
            horizon=horizon,
            method=ForecastMethod.LINEAR_TREND,
        )

    # ========================================================
    # EXPONENTIAL SMOOTHING
    # ========================================================

    def forecast_exponential_smoothing(
        self,
        history: Iterable[Any],
        horizon: int = DEFAULT_HORIZON,
    ) -> ForecastResult:
        """
        Generate an exponential-smoothing forecast.
        """

        return self.forecast(
            history,
            horizon=horizon,
            method=(
                ForecastMethod.EXPONENTIAL_SMOOTHING
            ),
        )

    # ========================================================
    # GRID METRIC
    # ========================================================

    def forecast_metric(
        self,
        metric_name: str,
        history: Iterable[Any],
        horizon: int = DEFAULT_HORIZON,
        method: str | None = None,
    ) -> ForecastResult:
        """
        Forecast a named grid metric.

        Examples:

            demand_mw
            generation_mw
            frequency_hz
            voltage
            transformer_loading
            line_loading
        """

        if not metric_name:
            raise ValueError(
                "metric_name cannot be empty."
            )

        return self.forecast(
            history,
            horizon=horizon,
            method=method,
        )

    # ========================================================
    # MULTIPLE METRICS
    # ========================================================

    def forecast_metrics(
        self,
        metrics: Mapping[str, Iterable[Any]],
        horizon: int = DEFAULT_HORIZON,
        method: str | None = None,
    ) -> dict[str, ForecastResult]:
        """
        Forecast multiple named grid metrics.

        Example:

            {
                "demand_mw": [...],
                "generation_mw": [...],
                "frequency_hz": [...],
            }
        """

        results: dict[
            str,
            ForecastResult,
        ] = {}

        for metric_name, history in metrics.items():
            results[metric_name] = (
                self.forecast_metric(
                    metric_name,
                    history,
                    horizon=horizon,
                    method=method,
                )
            )

        return results

    # ========================================================
    # SAFE MULTI-METRIC FORECASTING
    # ========================================================

    def forecast_metrics_safe(
        self,
        metrics: Mapping[str, Iterable[Any]],
        horizon: int = DEFAULT_HORIZON,
        method: str | None = None,
    ) -> ForecastServiceResult:
        """
        Forecast multiple metrics while collecting errors
        instead of stopping the entire operation.
        """

        forecasts: dict[
            str,
            ForecastResult,
        ] = {}

        errors: dict[
            str,
            str,
        ] = {}

        for metric_name, history in metrics.items():
            try:
                forecasts[metric_name] = (
                    self.forecast_metric(
                        metric_name,
                        history,
                        horizon=horizon,
                        method=method,
                    )
                )

            except Exception as exc:
                errors[metric_name] = str(
                    exc
                )

        return ForecastServiceResult(
            success=not bool(
                errors
            ),
            message=(
                "Forecasting completed successfully."
                if not errors
                else (
                    "Forecasting completed with "
                    "some errors."
                )
            ),
            forecasts=forecasts,
            errors=errors,
            metadata={
                "horizon": horizon,
                "method": (
                    method
                    if method is not None
                    else self.model.config.default_method
                ),
            },
        )

    # ========================================================
    # FORECAST ALL METHODS
    # ========================================================

    def compare_methods(
        self,
        history: Iterable[Any],
        horizon: int = DEFAULT_HORIZON,
    ) -> dict[str, ForecastResult]:
        """
        Generate forecasts using all supported baseline methods.

        Useful for evaluating which baseline behaves best for a
        particular grid metric.
        """

        methods = [
            ForecastMethod.PERSISTENCE,
            ForecastMethod.MOVING_AVERAGE,
            ForecastMethod.WEIGHTED_MOVING_AVERAGE,
            ForecastMethod.LINEAR_TREND,
            ForecastMethod.EXPONENTIAL_SMOOTHING,
        ]

        results: dict[
            str,
            ForecastResult,
        ] = {}

        for method in methods:
            results[method] = self.forecast(
                history,
                horizon=horizon,
                method=method,
            )

        return results

    # ========================================================
    # NEXT VALUE
    # ========================================================

    def next_value(
        self,
        history: Iterable[Any],
        method: str | None = None,
    ) -> float:
        """
        Return the next predicted value.
        """

        result = self.forecast(
            history,
            horizon=1,
            method=method,
        )

        if result.next_value is None:
            raise ValueError(
                "Forecast did not produce a value."
            )

        return result.next_value

    # ========================================================
    # FORECAST SUMMARY
    # ========================================================

    @staticmethod
    def summarize_forecast(
        result: ForecastResult,
    ) -> dict[str, Any]:
        """
        Produce a compact summary of a forecast.
        """

        forecast_values = result.forecast

        if not forecast_values:
            return {
                "method": result.method,
                "horizon": result.horizon,
                "next_value": None,
                "minimum": None,
                "maximum": None,
                "average": None,
                "confidence": result.confidence,
            }

        return {
            "method": result.method,
            "horizon": result.horizon,
            "last_observed": (
                result.last_observed
            ),
            "next_value": (
                result.next_value
            ),
            "minimum": min(
                forecast_values
            ),
            "maximum": max(
                forecast_values
            ),
            "average": (
                sum(forecast_values)
                / len(forecast_values)
            ),
            "confidence": result.confidence,
        }

    # ========================================================
    # FORECAST DIRECTION
    # ========================================================

    @staticmethod
    def forecast_direction(
        result: ForecastResult,
        tolerance: float = 1e-6,
    ) -> str:
        """
        Determine whether the forecast is increasing,
        decreasing, or stable relative to the latest observation.
        """

        if not result.forecast:
            return "unknown"

        first_forecast = result.forecast[0]

        difference = (
            first_forecast
            - result.last_observed
        )

        if abs(difference) <= tolerance:
            return "stable"

        if difference > 0.0:
            return "increasing"

        return "decreasing"

    # ========================================================
    # FORECAST CHANGE
    # ========================================================

    @staticmethod
    def forecast_change(
        result: ForecastResult,
    ) -> float:
        """
        Return the absolute change between the latest observed
        value and the first forecast.
        """

        if not result.forecast:
            return 0.0

        return (
            result.forecast[0]
            - result.last_observed
        )

    # ========================================================
    # FORECAST CHANGE PERCENT
    # ========================================================

    @staticmethod
    def forecast_change_percent(
        result: ForecastResult,
    ) -> float:
        """
        Return the percentage change between the latest
        observation and the first forecast.

        Returns 0 when the latest observation is zero.
        """

        if not result.forecast:
            return 0.0

        if result.last_observed == 0:
            return 0.0

        return (
            (
                result.forecast[0]
                - result.last_observed
            )
            / abs(
                result.last_observed
            )
        ) * 100.0

    # ========================================================
    # TREND ANALYSIS
    # ========================================================

    @staticmethod
    def analyze_forecast(
        result: ForecastResult,
    ) -> dict[str, Any]:
        """
        Produce a dashboard-friendly forecast analysis.
        """

        return {
            "method": result.method,
            "horizon": result.horizon,
            "last_observed": (
                result.last_observed
            ),
            "next_value": (
                result.next_value
            ),
            "direction": (
                ForecastingService.forecast_direction(
                    result
                )
            ),
            "absolute_change": (
                ForecastingService.forecast_change(
                    result
                )
            ),
            "percentage_change": (
                ForecastingService.forecast_change_percent(
                    result
                )
            ),
            "confidence": result.confidence,
            "minimum_forecast": (
                min(result.forecast)
                if result.forecast
                else None
            ),
            "maximum_forecast": (
                max(result.forecast)
                if result.forecast
                else None
            ),
        }

    # ========================================================
    # MODEL INFORMATION
    # ========================================================

    def model_info(
        self,
    ) -> dict[str, Any]:
        """
        Return information about the underlying forecasting model.
        """

        return self.model.model_info()


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def forecast(
    history: Iterable[Any],
    horizon: int = DEFAULT_HORIZON,
    method: str = DEFAULT_METHOD,
) -> ForecastResult:
    """
    Convenience function for forecasting a single series.
    """

    service = ForecastingService()

    return service.forecast(
        history,
        horizon=horizon,
        method=method,
    )


def forecast_grid_metric(
    metric_name: str,
    history: Iterable[Any],
    horizon: int = DEFAULT_HORIZON,
    method: str = DEFAULT_METHOD,
) -> ForecastResult:
    """
    Convenience function for forecasting a named grid metric.
    """

    service = ForecastingService()

    return service.forecast_metric(
        metric_name,
        history,
        horizon=horizon,
        method=method,
    )


def forecast_grid_metrics(
    metrics: Mapping[str, Iterable[Any]],
    horizon: int = DEFAULT_HORIZON,
    method: str = DEFAULT_METHOD,
) -> ForecastServiceResult:
    """
    Convenience function for forecasting multiple grid metrics.
    """

    service = ForecastingService()

    return service.forecast_metrics_safe(
        metrics,
        horizon=horizon,
        method=method,
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "ForecastServiceResult",
    "ForecastingService",
    "forecast",
    "forecast_grid_metric",
    "forecast_grid_metrics",
]