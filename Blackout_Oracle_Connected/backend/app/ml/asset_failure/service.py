"""
Blackout Oracle - Asset Failure Prediction Service.

Application-level service for estimating failure risk across
electrical-grid assets.

Responsibilities:

- Run asset-failure predictions
- Process individual assets
- Process batches of assets
- Rank assets by failure risk
- Identify high-risk and critical assets
- Produce dashboard-friendly summaries
- Convert model predictions into alert candidates

The actual scoring logic is implemented by:

    app.ml.asset_failure.model.AssetFailureModel

This service intentionally does not access the database or
external APIs directly.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from app.ml.asset_failure.model import (
    AssetFailureFeatures,
    AssetFailureModel,
    AssetFailureModelConfig,
    AssetFailurePrediction,
    AssetFailureRisk,
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_TOP_ASSETS = 10

DEFAULT_HIGH_RISK_THRESHOLD = (
    AssetFailureRisk.HIGH
)


# ============================================================
# SERVICE RESULT
# ============================================================


@dataclass
class AssetFailureServiceResult:
    """
    Application-level result returned by the asset-failure
    prediction service.
    """

    success: bool = True

    message: str = ""

    predictions: list[AssetFailurePrediction] = field(
        default_factory=list
    )

    high_risk_assets: list[AssetFailurePrediction] = field(
        default_factory=list
    )

    critical_assets: list[AssetFailurePrediction] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def total_assets(self) -> int:
        """Return the number of processed assets."""

        return len(
            self.predictions
        )

    @property
    def high_risk_count(self) -> int:
        """Return the number of high-risk assets."""

        return len(
            self.high_risk_assets
        )

    @property
    def critical_count(self) -> int:
        """Return the number of critical assets."""

        return len(
            self.critical_assets
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the service result to a dictionary."""

        return {
            "success": self.success,
            "message": self.message,
            "total_assets": self.total_assets,
            "high_risk_count": self.high_risk_count,
            "critical_count": self.critical_count,
            "predictions": [
                prediction.to_dict()
                for prediction in self.predictions
            ],
            "high_risk_assets": [
                prediction.to_dict()
                for prediction in self.high_risk_assets
            ],
            "critical_assets": [
                prediction.to_dict()
                for prediction in self.critical_assets
            ],
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# SERVICE
# ============================================================


class AssetFailureService:
    """
    High-level service around AssetFailureModel.

    Other application layers should preferably use this service
    instead of directly implementing asset-failure calculations.
    """

    def __init__(
        self,
        model: AssetFailureModel | None = None,
        config: AssetFailureModelConfig | None = None,
    ) -> None:
        """
        Initialize the asset-failure service.
        """

        if model is not None:
            self.model = model

        else:
            self.model = AssetFailureModel(
                config=config
            )

    # ========================================================
    # SINGLE ASSET
    # ========================================================

    def predict(
        self,
        asset: Mapping[str, Any],
        *,
        asset_id: str | None = None,
    ) -> AssetFailurePrediction:
        """
        Predict failure risk for one asset.
        """

        if not isinstance(
            asset,
            Mapping,
        ):
            raise TypeError(
                "Asset data must be a mapping."
            )

        return self.model.predict(
            asset,
            asset_id=asset_id,
        )

    # ========================================================
    # NORMALIZED FEATURES
    # ========================================================

    def predict_from_features(
        self,
        features: AssetFailureFeatures,
        *,
        asset_id: str | None = None,
    ) -> AssetFailurePrediction:
        """
        Predict failure risk from already-normalized features.
        """

        return self.model.predict_from_features(
            features,
            asset_id=asset_id,
        )

    # ========================================================
    # BATCH PREDICTION
    # ========================================================

    def predict_many(
        self,
        assets: Iterable[Mapping[str, Any]],
    ) -> list[AssetFailurePrediction]:
        """
        Predict failure risk for multiple assets.
        """

        predictions: list[
            AssetFailurePrediction
        ] = []

        for asset in assets:
            predictions.append(
                self.predict(
                    asset
                )
            )

        return predictions

    # ========================================================
    # SAFE BATCH PREDICTION
    # ========================================================

    def predict_many_safe(
        self,
        assets: Iterable[Mapping[str, Any]],
    ) -> AssetFailureServiceResult:
        """
        Predict multiple assets while collecting individual
        processing errors instead of stopping the entire batch.
        """

        predictions: list[
            AssetFailurePrediction
        ] = []

        errors: list[dict[str, Any]] = []

        for index, asset in enumerate(
            assets,
            start=1,
        ):
            try:
                predictions.append(
                    self.predict(
                        asset
                    )
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

        high_risk = self.get_high_risk_assets(
            predictions
        )

        critical = self.get_critical_assets(
            predictions
        )

        return AssetFailureServiceResult(
            success=not bool(
                errors
            ),
            message=(
                "Asset-failure prediction completed."
                if not errors
                else (
                    "Asset-failure prediction completed "
                    "with some errors."
                )
            ),
            predictions=predictions,
            high_risk_assets=high_risk,
            critical_assets=critical,
            metadata={
                "error_count": len(
                    errors
                ),
                "errors": errors,
            },
        )

    # ========================================================
    # TOP RISK ASSETS
    # ========================================================

    @staticmethod
    def rank_by_risk(
        predictions: Iterable[AssetFailurePrediction],
        *,
        top_n: int | None = None,
    ) -> list[AssetFailurePrediction]:
        """
        Sort predictions from highest risk to lowest risk.
        """

        ranked = sorted(
            predictions,
            key=lambda prediction: (
                prediction.risk_score,
                prediction.failure_probability,
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
    # HIGH RISK
    # ========================================================

    @staticmethod
    def get_high_risk_assets(
        predictions: Iterable[AssetFailurePrediction],
    ) -> list[AssetFailurePrediction]:
        """
        Return high and critical-risk assets.
        """

        high_risk_levels = {
            AssetFailureRisk.HIGH,
            AssetFailureRisk.CRITICAL,
        }

        result = [
            prediction
            for prediction in predictions
            if prediction.risk_level
            in high_risk_levels
        ]

        return AssetFailureService.rank_by_risk(
            result
        )

    # ========================================================
    # CRITICAL
    # ========================================================

    @staticmethod
    def get_critical_assets(
        predictions: Iterable[AssetFailurePrediction],
    ) -> list[AssetFailurePrediction]:
        """
        Return only critical-risk assets.
        """

        result = [
            prediction
            for prediction in predictions
            if prediction.risk_level
            == AssetFailureRisk.CRITICAL
        ]

        return AssetFailureService.rank_by_risk(
            result
        )

    # ========================================================
    # LOW RISK
    # ========================================================

    @staticmethod
    def get_low_risk_assets(
        predictions: Iterable[AssetFailurePrediction],
    ) -> list[AssetFailurePrediction]:
        """
        Return assets classified as very-low or low risk.
        """

        low_risk_levels = {
            AssetFailureRisk.VERY_LOW,
            AssetFailureRisk.LOW,
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
        predictions: Iterable[AssetFailurePrediction],
    ) -> dict[str, int]:
        """
        Count assets in each risk category.
        """

        distribution = {
            AssetFailureRisk.VERY_LOW.value: 0,
            AssetFailureRisk.LOW.value: 0,
            AssetFailureRisk.MEDIUM.value: 0,
            AssetFailureRisk.HIGH.value: 0,
            AssetFailureRisk.CRITICAL.value: 0,
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
        predictions: Iterable[AssetFailurePrediction],
    ) -> dict[str, Any]:
        """
        Produce a dashboard-friendly summary.
        """

        prediction_list = list(
            predictions
        )

        if not prediction_list:
            return {
                "total_assets": 0,
                "average_risk_score": 0.0,
                "maximum_risk_score": 0.0,
                "average_failure_probability": 0.0,
                "maximum_failure_probability": 0.0,
                "risk_distribution": (
                    AssetFailureService.risk_distribution(
                        []
                    )
                ),
            }

        risk_scores = [
            prediction.risk_score
            for prediction in prediction_list
        ]

        probabilities = [
            prediction.failure_probability
            for prediction in prediction_list
        ]

        return {
            "total_assets": len(
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
            "average_failure_probability": (
                sum(
                    probabilities
                )
                / len(
                    probabilities
                )
            ),
            "maximum_failure_probability": max(
                probabilities
            ),
            "high_risk_count": len(
                AssetFailureService.get_high_risk_assets(
                    prediction_list
                )
            ),
            "critical_count": len(
                AssetFailureService.get_critical_assets(
                    prediction_list
                )
            ),
            "risk_distribution": (
                AssetFailureService.risk_distribution(
                    prediction_list
                )
            ),
        }

    # ========================================================
    # ALERT CANDIDATES
    # ========================================================

    @staticmethod
    def get_alert_candidates(
        predictions: Iterable[AssetFailurePrediction],
        *,
        minimum_risk: AssetFailureRisk = (
            DEFAULT_HIGH_RISK_THRESHOLD
        ),
    ) -> list[AssetFailurePrediction]:
        """
        Return assets that may require attention.

        This method only identifies candidates. It does not create
        an incident or send an alert.
        """

        minimum_rank = (
            AssetFailureService.risk_rank(
                minimum_risk
            )
        )

        result = [
            prediction
            for prediction in predictions
            if (
                AssetFailureService.risk_rank(
                    prediction.risk_level
                )
                >= minimum_rank
            )
        ]

        return AssetFailureService.rank_by_risk(
            result
        )

    # ========================================================
    # CONTRIBUTING FACTORS
    # ========================================================

    @staticmethod
    def factor_summary(
        predictions: Iterable[AssetFailurePrediction],
    ) -> dict[str, int]:
        """
        Count how often each risk factor appears among the
        contributing factors.
        """

        summary: dict[str, int] = {}

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
    # ASSET LOOKUP
    # ========================================================

    @staticmethod
    def find_asset(
        predictions: Iterable[AssetFailurePrediction],
        asset_id: str,
    ) -> AssetFailurePrediction | None:
        """
        Find a prediction for a specific asset ID.
        """

        target = str(
            asset_id
        ).strip()

        for prediction in predictions:
            if prediction.asset_id == target:
                return prediction

        return None

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


def predict_asset(
    asset: Mapping[str, Any],
    *,
    asset_id: str | None = None,
    config: AssetFailureModelConfig | None = None,
) -> AssetFailurePrediction:
    """
    Convenience function for one asset.
    """

    service = AssetFailureService(
        config=config
    )

    return service.predict(
        asset,
        asset_id=asset_id,
    )


def predict_assets(
    assets: Iterable[Mapping[str, Any]],
    *,
    config: AssetFailureModelConfig | None = None,
) -> list[AssetFailurePrediction]:
    """
    Convenience function for multiple assets.
    """

    service = AssetFailureService(
        config=config
    )

    return service.predict_many(
        assets
    )


def analyze_asset_risk(
    assets: Iterable[Mapping[str, Any]],
    *,
    config: AssetFailureModelConfig | None = None,
) -> AssetFailureServiceResult:
    """
    Convenience function for complete asset-risk analysis.
    """

    service = AssetFailureService(
        config=config
    )

    return service.predict_many_safe(
        assets
    )


def rank_asset_risk(
    predictions: Iterable[AssetFailurePrediction],
    *,
    top_n: int | None = None,
) -> list[AssetFailurePrediction]:
    """
    Convenience function for ranking asset predictions.
    """

    return AssetFailureService.rank_by_risk(
        predictions,
        top_n=top_n,
    )


def get_high_risk_assets(
    predictions: Iterable[AssetFailurePrediction],
) -> list[AssetFailurePrediction]:
    """
    Convenience function for retrieving high-risk assets.
    """

    return AssetFailureService.get_high_risk_assets(
        predictions
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "AssetFailureServiceResult",
    "AssetFailureService",
    "predict_asset",
    "predict_assets",
    "analyze_asset_risk",
    "rank_asset_risk",
    "get_high_risk_assets",
]