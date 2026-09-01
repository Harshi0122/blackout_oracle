"""
Blackout Oracle - Cascade Risk Service.

Application-level service for analyzing cascading-failure risk
across the electrical grid.

Responsibilities:

- Run cascade-risk predictions
- Analyze individual grid states
- Analyze multiple grid states
- Rank cascade-risk predictions
- Identify propagating conditions
- Identify high-risk and critical cascade conditions
- Produce dashboard-friendly summaries
- Generate alert candidates
- Summarize cascade contributors

The underlying scoring logic is implemented by:

    app.ml.cascade.model.CascadeModel

This service does not directly operate grid equipment.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from app.ml.cascade.model import (
    CascadeFeatures,
    CascadeModel,
    CascadeModelConfig,
    CascadePrediction,
    CascadeRiskLevel,
    CascadeState,
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_ALERT_LEVEL = CascadeRiskLevel.HIGH

DEFAULT_TOP_RISKS = 10


# ============================================================
# SERVICE RESULT
# ============================================================


@dataclass
class CascadeServiceResult:
    """
    Result returned by the cascade analysis service.
    """

    success: bool = True

    message: str = ""

    predictions: list[CascadePrediction] = field(
        default_factory=list
    )

    high_risk_predictions: list[CascadePrediction] = field(
        default_factory=list
    )

    critical_predictions: list[CascadePrediction] = field(
        default_factory=list
    )

    propagating_predictions: list[CascadePrediction] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def total_predictions(self) -> int:
        """Return the number of processed predictions."""

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

    @property
    def propagating_count(self) -> int:
        """Return the number of propagating predictions."""

        return len(
            self.propagating_predictions
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the result into a dictionary."""

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
            "propagating_count": (
                self.propagating_count
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
            "propagating_predictions": [
                prediction.to_dict()
                for prediction in self.propagating_predictions
            ],
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# SERVICE
# ============================================================


class CascadeService:
    """
    High-level service around CascadeModel.

    This class provides the application-facing interface for
    cascade-risk analysis.
    """

    def __init__(
        self,
        model: CascadeModel | None = None,
        config: CascadeModelConfig | None = None,
    ) -> None:
        """
        Initialize the cascade service.
        """

        if model is not None:
            self.model = model

        else:
            self.model = CascadeModel(
                config=config
            )

    # ========================================================
    # SINGLE PREDICTION
    # ========================================================

    def predict(
        self,
        data: Mapping[str, Any],
    ) -> CascadePrediction:
        """
        Predict cascade risk for one grid state.
        """

        if not isinstance(
            data,
            Mapping,
        ):
            raise TypeError(
                "Cascade input must be a mapping."
            )

        return self.model.predict(
            data
        )

    # ========================================================
    # NORMALIZED FEATURES
    # ========================================================

    def predict_from_features(
        self,
        features: CascadeFeatures,
    ) -> CascadePrediction:
        """
        Predict cascade risk from normalized features.
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
    ) -> list[CascadePrediction]:
        """
        Predict cascade risk for multiple grid states.
        """

        predictions: list[
            CascadePrediction
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
    ) -> CascadeServiceResult:
        """
        Process multiple grid states without allowing one
        invalid record to stop the entire batch.
        """

        predictions: list[
            CascadePrediction
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

        propagating = (
            self.get_propagating_predictions(
                predictions
            )
        )

        return CascadeServiceResult(
            success=not bool(
                errors
            ),
            message=(
                "Cascade analysis completed."
                if not errors
                else (
                    "Cascade analysis completed "
                    "with some errors."
                )
            ),
            predictions=predictions,
            high_risk_predictions=high_risk,
            critical_predictions=critical,
            propagating_predictions=propagating,
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
        predictions: Iterable[CascadePrediction],
        *,
        top_n: int | None = None,
    ) -> list[CascadePrediction]:
        """
        Sort predictions from highest cascade risk to lowest.
        """

        ranked = sorted(
            predictions,
            key=lambda prediction: (
                prediction.cascade_score,
                prediction.cascade_probability,
                prediction.propagation_factor,
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
    # HIGH-RISK
    # ========================================================

    @staticmethod
    def get_high_risk_predictions(
        predictions: Iterable[CascadePrediction],
    ) -> list[CascadePrediction]:
        """
        Return high and critical cascade-risk predictions.
        """

        levels = {
            CascadeRiskLevel.HIGH,
            CascadeRiskLevel.CRITICAL,
        }

        result = [
            prediction
            for prediction in predictions
            if prediction.risk_level
            in levels
        ]

        return CascadeService.rank_by_risk(
            result
        )

    # ========================================================
    # CRITICAL
    # ========================================================

    @staticmethod
    def get_critical_predictions(
        predictions: Iterable[CascadePrediction],
    ) -> list[CascadePrediction]:
        """
        Return only critical cascade-risk predictions.
        """

        result = [
            prediction
            for prediction in predictions
            if prediction.risk_level
            == CascadeRiskLevel.CRITICAL
        ]

        return CascadeService.rank_by_risk(
            result
        )

    # ========================================================
    # PROPAGATING
    # ========================================================

    @staticmethod
    def get_propagating_predictions(
        predictions: Iterable[CascadePrediction],
    ) -> list[CascadePrediction]:
        """
        Return predictions where the cascade state is
        propagating or critical.
        """

        result = [
            prediction
            for prediction in predictions
            if prediction.state
            in {
                CascadeState.PROPAGATING,
                CascadeState.CRITICAL,
            }
        ]

        return CascadeService.rank_by_risk(
            result
        )

    # ========================================================
    # STRESSED
    # ========================================================

    @staticmethod
    def get_stressed_predictions(
        predictions: Iterable[CascadePrediction],
    ) -> list[CascadePrediction]:
        """
        Return predictions classified as stressed,
        propagating, or critical.
        """

        states = {
            CascadeState.STRESSED,
            CascadeState.PROPAGATING,
            CascadeState.CRITICAL,
        }

        result = [
            prediction
            for prediction in predictions
            if prediction.state
            in states
        ]

        return CascadeService.rank_by_risk(
            result
        )

    # ========================================================
    # RISK DISTRIBUTION
    # ========================================================

    @staticmethod
    def risk_distribution(
        predictions: Iterable[CascadePrediction],
    ) -> dict[str, int]:
        """
        Count predictions by cascade-risk level.
        """

        distribution = {
            CascadeRiskLevel.VERY_LOW.value: 0,
            CascadeRiskLevel.LOW.value: 0,
            CascadeRiskLevel.MEDIUM.value: 0,
            CascadeRiskLevel.HIGH.value: 0,
            CascadeRiskLevel.CRITICAL.value: 0,
        }

        for prediction in predictions:
            level = prediction.risk_level.value

            if level in distribution:
                distribution[
                    level
                ] += 1

        return distribution

    # ========================================================
    # STATE DISTRIBUTION
    # ========================================================

    @staticmethod
    def state_distribution(
        predictions: Iterable[CascadePrediction],
    ) -> dict[str, int]:
        """
        Count predictions by cascade state.
        """

        distribution = {
            CascadeState.STABLE.value: 0,
            CascadeState.STRESSED.value: 0,
            CascadeState.PROPAGATING.value: 0,
            CascadeState.CRITICAL.value: 0,
        }

        for prediction in predictions:
            state = prediction.state.value

            if state in distribution:
                distribution[
                    state
                ] += 1

        return distribution

    # ========================================================
    # SUMMARY
    # ========================================================

    @staticmethod
    def summarize(
        predictions: Iterable[CascadePrediction],
    ) -> dict[str, Any]:
        """
        Produce a dashboard-friendly cascade-risk summary.
        """

        prediction_list = list(
            predictions
        )

        if not prediction_list:
            return {
                "total": 0,
                "average_cascade_score": 0.0,
                "maximum_cascade_score": 0.0,
                "average_probability": 0.0,
                "maximum_probability": 0.0,
                "average_propagation_factor": 0.0,
                "high_risk_count": 0,
                "critical_count": 0,
                "propagating_count": 0,
                "risk_distribution": (
                    CascadeService.risk_distribution(
                        []
                    )
                ),
                "state_distribution": (
                    CascadeService.state_distribution(
                        []
                    )
                ),
            }

        scores = [
            prediction.cascade_score
            for prediction in prediction_list
        ]

        probabilities = [
            prediction.cascade_probability
            for prediction in prediction_list
        ]

        propagation_factors = [
            prediction.propagation_factor
            for prediction in prediction_list
        ]

        high_risk_count = len(
            CascadeService.get_high_risk_predictions(
                prediction_list
            )
        )

        critical_count = len(
            CascadeService.get_critical_predictions(
                prediction_list
            )
        )

        propagating_count = len(
            CascadeService.get_propagating_predictions(
                prediction_list
            )
        )

        return {
            "total": len(
                prediction_list
            ),
            "average_cascade_score": (
                sum(scores)
                / len(scores)
            ),
            "maximum_cascade_score": max(
                scores
            ),
            "average_probability": (
                sum(probabilities)
                / len(probabilities)
            ),
            "maximum_probability": max(
                probabilities
            ),
            "average_propagation_factor": (
                sum(propagation_factors)
                / len(propagation_factors)
            ),
            "high_risk_count": high_risk_count,
            "critical_count": critical_count,
            "propagating_count": propagating_count,
            "risk_distribution": (
                CascadeService.risk_distribution(
                    prediction_list
                )
            ),
            "state_distribution": (
                CascadeService.state_distribution(
                    prediction_list
                )
            ),
        }

    # ========================================================
    # ALERT CANDIDATES
    # ========================================================

    @staticmethod
    def get_alert_candidates(
        predictions: Iterable[CascadePrediction],
        *,
        minimum_level: CascadeRiskLevel = (
            DEFAULT_ALERT_LEVEL
        ),
    ) -> list[CascadePrediction]:
        """
        Return predictions that may warrant an alert.

        This method only identifies candidates.
        It does not create or send an alert.
        """

        minimum_rank = (
            CascadeService.risk_rank(
                minimum_level
            )
        )

        candidates = [
            prediction
            for prediction in predictions
            if (
                CascadeService.risk_rank(
                    prediction.risk_level
                )
                >= minimum_rank
            )
        ]

        return CascadeService.rank_by_risk(
            candidates
        )

    # ========================================================
    # PROPAGATION ALERT CANDIDATES
    # ========================================================

    @staticmethod
    def get_propagation_alert_candidates(
        predictions: Iterable[CascadePrediction],
    ) -> list[CascadePrediction]:
        """
        Return predictions where the cascade state is actively
        propagating or critical.
        """

        candidates = [
            prediction
            for prediction in predictions
            if prediction.state
            in {
                CascadeState.PROPAGATING,
                CascadeState.CRITICAL,
            }
        ]

        return CascadeService.rank_by_risk(
            candidates
        )

    # ========================================================
    # PRIMARY CONTRIBUTOR
    # ========================================================

    @staticmethod
    def get_primary_contributor(
        prediction: CascadePrediction,
    ) -> str | None:
        """
        Return the strongest contributing factor.
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
        predictions: Iterable[CascadePrediction],
    ) -> dict[str, int]:
        """
        Count how frequently each factor contributes to
        cascade-risk predictions.
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
    # MOST DANGEROUS PREDICTION
    # ========================================================

    @staticmethod
    def get_most_dangerous(
        predictions: Iterable[CascadePrediction],
    ) -> CascadePrediction | None:
        """
        Return the single highest-risk prediction.
        """

        ranked = CascadeService.rank_by_risk(
            predictions,
            top_n=1,
        )

        if not ranked:
            return None

        return ranked[0]

    # ========================================================
    # RISK RANK
    # ========================================================

    @staticmethod
    def risk_rank(
        level: CascadeRiskLevel,
    ) -> int:
        """
        Convert a cascade-risk level to an integer rank.
        """

        ranks = {
            CascadeRiskLevel.VERY_LOW: 0,
            CascadeRiskLevel.LOW: 1,
            CascadeRiskLevel.MEDIUM: 2,
            CascadeRiskLevel.HIGH: 3,
            CascadeRiskLevel.CRITICAL: 4,
        }

        return ranks.get(
            level,
            0,
        )

    # ========================================================
    # GRID CASCADE HEALTH
    # ========================================================

    @staticmethod
    def grid_cascade_health(
        prediction: CascadePrediction,
    ) -> dict[str, Any]:
        """
        Produce a compact cascade-health summary suitable for
        dashboards and API responses.
        """

        if prediction.state == (
            CascadeState.CRITICAL
        ):
            status = "critical"

        elif prediction.state == (
            CascadeState.PROPAGATING
        ):
            status = "propagating"

        elif prediction.state == (
            CascadeState.STRESSED
        ):
            status = "stressed"

        else:
            status = "stable"

        return {
            "status": status,
            "cascade_score": (
                prediction.cascade_score
            ),
            "cascade_probability": (
                prediction.cascade_probability
            ),
            "risk_level": (
                prediction.risk_level.value
            ),
            "state": (
                prediction.state.value
            ),
            "confidence": (
                prediction.confidence
            ),
            "propagation_factor": (
                prediction.propagation_factor
            ),
            "estimated_affected_assets": (
                prediction.estimated_affected_assets
            ),
            "primary_contributor": (
                CascadeService.get_primary_contributor(
                    prediction
                )
            ),
            "contributing_factors": list(
                prediction.contributing_factors
            ),
        }

    # ========================================================
    # MODEL INFORMATION
    # ========================================================

    def model_info(
        self,
    ) -> dict[str, Any]:
        """
        Return information about the underlying cascade model.
        """

        return self.model.model_info()


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def predict_cascade_risk(
    data: Mapping[str, Any],
    *,
    config: CascadeModelConfig | None = None,
) -> CascadePrediction:
    """
    Convenience function for a single cascade-risk prediction.
    """

    service = CascadeService(
        config=config
    )

    return service.predict(
        data
    )


def analyze_cascade_risk(
    records: Iterable[Mapping[str, Any]],
    *,
    config: CascadeModelConfig | None = None,
) -> CascadeServiceResult:
    """
    Convenience function for batch cascade-risk analysis.
    """

    service = CascadeService(
        config=config
    )

    return service.predict_many_safe(
        records
    )


def rank_cascade_risks(
    predictions: Iterable[CascadePrediction],
    *,
    top_n: int | None = None,
) -> list[CascadePrediction]:
    """
    Convenience function for cascade-risk ranking.
    """

    return CascadeService.rank_by_risk(
        predictions,
        top_n=top_n,
    )


def get_cascade_alert_candidates(
    predictions: Iterable[CascadePrediction],
    *,
    minimum_level: CascadeRiskLevel = (
        DEFAULT_ALERT_LEVEL
    ),
) -> list[CascadePrediction]:
    """
    Convenience function for obtaining cascade alert candidates.
    """

    return CascadeService.get_alert_candidates(
        predictions,
        minimum_level=minimum_level,
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "CascadeServiceResult",
    "CascadeService",
    "predict_cascade_risk",
    "analyze_cascade_risk",
    "rank_cascade_risks",
    "get_cascade_alert_candidates",
]