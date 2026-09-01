"""
Blackout Oracle - Blackout Risk Service.

Application-level service for estimating overall electrical-grid
blackout risk.

Responsibilities:

- Run blackout-risk predictions
- Analyze a single grid state
- Analyze multiple grid states
- Rank risk observations
- Identify high-risk and critical conditions
- Produce dashboard-friendly summaries
- Identify alert candidates
- Explain the major contributors to current risk

The underlying scoring logic is implemented by:

    app.ml.blackout_risk.model.BlackoutRiskModel

This service does not directly access the database, external APIs,
or grid-control systems.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from app.ml.blackout_risk.model import (
    BlackoutRiskFeatures,
    BlackoutRiskLevel,
    BlackoutRiskModel,
    BlackoutRiskModelConfig,
    BlackoutRiskPrediction,
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_TOP_RISKS = 10

DEFAULT_ALERT_LEVEL = BlackoutRiskLevel.HIGH


# ============================================================
# SERVICE RESULT
# ============================================================


@dataclass
class BlackoutRiskServiceResult:
    """
    Application-level result returned by the blackout-risk
    service.
    """

    success: bool = True

    message: str = ""

    predictions: list[BlackoutRiskPrediction] = field(
        default_factory=list
    )

    high_risk_predictions: list[BlackoutRiskPrediction] = field(
        default_factory=list
    )

    critical_predictions: list[BlackoutRiskPrediction] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def total_predictions(self) -> int:
        """Return the number of predictions."""

        return len(
            self.predictions
        )

    @property
    def high_risk_count(self) -> int:
        """Return the number of high-risk predictions."""

        return len(
            self.high_risk_predictions
        )

    @property
    def critical_count(self) -> int:
        """Return the number of critical predictions."""

        return len(
            self.critical_predictions
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the service result into a dictionary."""

        return {
            "success": self.success,
            "message": self.message,
            "total_predictions": (
                self.total_predictions
            ),
            "high_risk_count": (
                self.high_risk_count
            ),
            "critical_count": (
                self.critical_count
            ),
            "predictions": [
                prediction.to_dict()
                for prediction in self.predictions
            ],
            "high_risk_predictions": [
                prediction.to_dict()
                for prediction in self.high_risk_predictions
            ],
            "critical_predictions": [
                prediction.to_dict()
                for prediction in self.critical_predictions
            ],
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# SERVICE
# ============================================================


class BlackoutRiskService:
    """
    High-level service around BlackoutRiskModel.

    Other application layers should preferably use this service
    rather than directly implementing blackout-risk calculations.
    """

    def __init__(
        self,
        model: BlackoutRiskModel | None = None,
        config: BlackoutRiskModelConfig | None = None,
    ) -> None:
        """
        Initialize the blackout-risk service.
        """

        if model is not None:
            self.model = model

        else:
            self.model = BlackoutRiskModel(
                config=config
            )

    # ========================================================
    # SINGLE PREDICTION
    # ========================================================

    def predict(
        self,
        data: Mapping[str, Any],
    ) -> BlackoutRiskPrediction:
        """
        Predict blackout risk for one grid state.
        """

        if not isinstance(
            data,
            Mapping,
        ):
            raise TypeError(
                "Blackout-risk input must be a mapping."
            )

        return self.model.predict(
            data
        )

    # ========================================================
    # NORMALIZED FEATURES
    # ========================================================

    def predict_from_features(
        self,
        features: BlackoutRiskFeatures,
    ) -> BlackoutRiskPrediction:
        """
        Predict blackout risk from normalized features.
        """

        return self.model.predict_from_features(
            features
        )

    # ========================================================
    # BATCH PREDICTION
    # ========================================================

    def predict_many(
        self,
        records: Iterable[Mapping[str, Any]],
    ) -> list[BlackoutRiskPrediction]:
        """
        Predict blackout risk for multiple grid states.
        """

        predictions: list[
            BlackoutRiskPrediction
        ] = []

        for record in records:
            predictions.append(
                self.predict(
                    record
                )
            )

        return predictions

    # ========================================================
    # SAFE BATCH PREDICTION
    # ========================================================

    def predict_many_safe(
        self,
        records: Iterable[Mapping[str, Any]],
    ) -> BlackoutRiskServiceResult:
        """
        Predict multiple grid states while collecting errors
        instead of stopping the entire batch.
        """

        predictions: list[
            BlackoutRiskPrediction
        ] = []

        errors: list[
            dict[str, Any]
        ] = []

        for index, record in enumerate(
            records,
            start=1,
        ):
            try:
                prediction = self.predict(
                    record
                )

                predictions.append(
                    prediction
                )

            except Exception as exc:
                errors.append(
                    {
                        "index": index,
                        "error": str(exc),
                        "exception_type": (
                            type(exc).__name__
                        ),
                    }
                )

        high_risk = (
            self.get_high_risk_predictions(
                predictions
            )
        )

        critical = (
            self.get_critical_predictions(
                predictions
            )
        )

        return BlackoutRiskServiceResult(
            success=not bool(
                errors
            ),
            message=(
                "Blackout-risk analysis completed."
                if not errors
                else (
                    "Blackout-risk analysis completed "
                    "with some errors."
                )
            ),
            predictions=predictions,
            high_risk_predictions=high_risk,
            critical_predictions=critical,
            metadata={
                "error_count": len(
                    errors
                ),
                "errors": errors,
            },
        )

    # ========================================================
    # RANKING
    # ========================================================

    @staticmethod
    def rank_by_risk(
        predictions: Iterable[BlackoutRiskPrediction],
        *,
        top_n: int | None = None,
    ) -> list[BlackoutRiskPrediction]:
        """
        Sort predictions from highest risk to lowest risk.
        """

        ranked = sorted(
            predictions,
            key=lambda prediction: (
                prediction.risk_score,
                prediction.estimated_probability,
            ),
            reverse=True,
        )

        if top_n is None:
            return ranked

        return ranked[
            : max(
                0,
                int(top_n),
            )
        ]

    # ========================================================
    # HIGH-RISK PREDICTIONS
    # ========================================================

    @staticmethod
    def get_high_risk_predictions(
        predictions: Iterable[BlackoutRiskPrediction],
    ) -> list[BlackoutRiskPrediction]:
        """
        Return high and critical risk predictions.
        """

        high_risk_levels = {
            BlackoutRiskLevel.HIGH,
            BlackoutRiskLevel.CRITICAL,
        }

        result = [
            prediction
            for prediction in predictions
            if prediction.risk_level
            in high_risk_levels
        ]

        return BlackoutRiskService.rank_by_risk(
            result
        )

    # ========================================================
    # CRITICAL PREDICTIONS
    # ========================================================

    @staticmethod
    def get_critical_predictions(
        predictions: Iterable[BlackoutRiskPrediction],
    ) -> list[BlackoutRiskPrediction]:
        """
        Return only critical-risk predictions.
        """

        result = [
            prediction
            for prediction in predictions
            if prediction.risk_level
            == BlackoutRiskLevel.CRITICAL
        ]

        return BlackoutRiskService.rank_by_risk(
            result
        )

    # ========================================================
    # LOW-RISK PREDICTIONS
    # ========================================================

    @staticmethod
    def get_low_risk_predictions(
        predictions: Iterable[BlackoutRiskPrediction],
    ) -> list[BlackoutRiskPrediction]:
        """
        Return very-low and low-risk predictions.
        """

        low_risk_levels = {
            BlackoutRiskLevel.VERY_LOW,
            BlackoutRiskLevel.LOW,
        }

        return [
            prediction
            for prediction in predictions
            if prediction.risk_level
            in low_risk_levels
        ]

    # ========================================================
    # RISK DISTRIBUTION
    # ========================================================

    @staticmethod
    def risk_distribution(
        predictions: Iterable[BlackoutRiskPrediction],
    ) -> dict[str, int]:
        """
        Count predictions by risk level.
        """

        distribution = {
            BlackoutRiskLevel.VERY_LOW.value: 0,
            BlackoutRiskLevel.LOW.value: 0,
            BlackoutRiskLevel.MEDIUM.value: 0,
            BlackoutRiskLevel.HIGH.value: 0,
            BlackoutRiskLevel.CRITICAL.value: 0,
        }

        for prediction in predictions:
            level = prediction.risk_level.value

            if level in distribution:
                distribution[
                    level
                ] += 1

        return distribution

    # ========================================================
    # SUMMARY
    # ========================================================

    @staticmethod
    def summarize(
        predictions: Iterable[BlackoutRiskPrediction],
    ) -> dict[str, Any]:
        """
        Produce a dashboard-friendly summary.
        """

        prediction_list = list(
            predictions
        )

        if not prediction_list:
            return {
                "total": 0,
                "average_risk_score": 0.0,
                "maximum_risk_score": 0.0,
                "average_probability": 0.0,
                "maximum_probability": 0.0,
                "high_risk_count": 0,
                "critical_count": 0,
                "risk_distribution": (
                    BlackoutRiskService.risk_distribution(
                        []
                    )
                ),
            }

        risk_scores = [
            prediction.risk_score
            for prediction in prediction_list
        ]

        probabilities = [
            prediction.estimated_probability
            for prediction in prediction_list
        ]

        high_risk_count = len(
            BlackoutRiskService.get_high_risk_predictions(
                prediction_list
            )
        )

        critical_count = len(
            BlackoutRiskService.get_critical_predictions(
                prediction_list
            )
        )

        return {
            "total": len(
                prediction_list
            ),
            "average_risk_score": (
                sum(
                    risk_scores
                )
                / len(
                    risk_scores
                )
            ),
            "maximum_risk_score": max(
                risk_scores
            ),
            "average_probability": (
                sum(
                    probabilities
                )
                / len(
                    probabilities
                )
            ),
            "maximum_probability": max(
                probabilities
            ),
            "high_risk_count": high_risk_count,
            "critical_count": critical_count,
            "risk_distribution": (
                BlackoutRiskService.risk_distribution(
                    prediction_list
                )
            ),
        }

    # ========================================================
    # ALERT CANDIDATES
    # ========================================================

    @staticmethod
    def get_alert_candidates(
        predictions: Iterable[BlackoutRiskPrediction],
        *,
        minimum_level: BlackoutRiskLevel = (
            DEFAULT_ALERT_LEVEL
        ),
    ) -> list[BlackoutRiskPrediction]:
        """
        Return predictions that may warrant an alert.

        This function only identifies candidates. It does not
        create or send an alert.
        """

        minimum_rank = (
            BlackoutRiskService.risk_rank(
                minimum_level
            )
        )

        candidates = [
            prediction
            for prediction in predictions
            if (
                BlackoutRiskService.risk_rank(
                    prediction.risk_level
                )
                >= minimum_rank
            )
        ]

        return BlackoutRiskService.rank_by_risk(
            candidates
        )

    # ========================================================
    # MOST IMPORTANT CONDITION
    # ========================================================

    @staticmethod
    def get_primary_contributor(
        prediction: BlackoutRiskPrediction,
    ) -> str | None:
        """
        Return the strongest contributing risk factor.
        """

        if not prediction.contributing_factors:
            return None

        return prediction.contributing_factors[
            0
        ]

    # ========================================================
    # CONTRIBUTOR SUMMARY
    # ========================================================

    @staticmethod
    def contributor_summary(
        predictions: Iterable[BlackoutRiskPrediction],
    ) -> dict[str, int]:
        """
        Count how frequently each risk factor contributes to
        blackout-risk predictions.
        """

        summary: dict[
            str,
            int,
        ] = {}

        for prediction in predictions:
            for factor in prediction.contributing_factors:
                summary[factor] = (
                    summary.get(
                        factor,
                        0,
                    )
                    + 1
                )

        return dict(
            sorted(
                summary.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

    # ========================================================
    # CURRENT GRID HEALTH
    # ========================================================

    @staticmethod
    def grid_health(
        prediction: BlackoutRiskPrediction,
    ) -> dict[str, Any]:
        """
        Produce a compact current-grid-health summary.
        """

        if prediction.risk_level == (
            BlackoutRiskLevel.CRITICAL
        ):
            status = "critical"

        elif prediction.risk_level == (
            BlackoutRiskLevel.HIGH
        ):
            status = "warning"

        elif prediction.risk_level == (
            BlackoutRiskLevel.MEDIUM
        ):
            status = "attention"

        else:
            status = "normal"

        return {
            "status": status,
            "risk_score": prediction.risk_score,
            "risk_level": prediction.risk_level.value,
            "estimated_probability": (
                prediction.estimated_probability
            ),
            "confidence": prediction.confidence,
            "primary_contributor": (
                BlackoutRiskService.get_primary_contributor(
                    prediction
                )
            ),
            "contributing_factors": list(
                prediction.contributing_factors
            ),
        }

    # ========================================================
    # RISK RANK
    # ========================================================

    @staticmethod
    def risk_rank(
        level: BlackoutRiskLevel,
    ) -> int:
        """
        Convert risk level to an integer rank.
        """

        ranks = {
            BlackoutRiskLevel.VERY_LOW: 0,
            BlackoutRiskLevel.LOW: 1,
            BlackoutRiskLevel.MEDIUM: 2,
            BlackoutRiskLevel.HIGH: 3,
            BlackoutRiskLevel.CRITICAL: 4,
        }

        return ranks.get(
            level,
            0,
        )

    # ========================================================
    # MODEL INFORMATION
    # ========================================================

    def model_info(
        self,
    ) -> dict[str, Any]:
        """
        Return information about the underlying model.
        """

        return self.model.model_info()


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def predict_blackout_risk(
    data: Mapping[str, Any],
    *,
    config: BlackoutRiskModelConfig | None = None,
) -> BlackoutRiskPrediction:
    """
    Convenience function for one grid-state prediction.
    """

    service = BlackoutRiskService(
        config=config
    )

    return service.predict(
        data
    )


def analyze_blackout_risk(
    records: Iterable[Mapping[str, Any]],
    *,
    config: BlackoutRiskModelConfig | None = None,
) -> BlackoutRiskServiceResult:
    """
    Convenience function for batch blackout-risk analysis.
    """

    service = BlackoutRiskService(
        config=config
    )

    return service.predict_many_safe(
        records
    )


def rank_blackout_risks(
    predictions: Iterable[BlackoutRiskPrediction],
    *,
    top_n: int | None = None,
) -> list[BlackoutRiskPrediction]:
    """
    Convenience function for risk ranking.
    """

    return BlackoutRiskService.rank_by_risk(
        predictions,
        top_n=top_n,
    )


def get_blackout_alert_candidates(
    predictions: Iterable[BlackoutRiskPrediction],
    *,
    minimum_level: BlackoutRiskLevel = (
        DEFAULT_ALERT_LEVEL
    ),
) -> list[BlackoutRiskPrediction]:
    """
    Convenience function for obtaining alert candidates.
    """

    return BlackoutRiskService.get_alert_candidates(
        predictions,
        minimum_level=minimum_level,
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "BlackoutRiskServiceResult",
    "BlackoutRiskService",
    "predict_blackout_risk",
    "analyze_blackout_risk",
    "rank_blackout_risks",
    "get_blackout_alert_candidates",
]