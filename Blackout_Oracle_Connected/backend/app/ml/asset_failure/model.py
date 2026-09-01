"""
Blackout Oracle - Asset Failure Prediction Model.

Provides a lightweight asset-failure prediction model for
electrical-grid assets.

The model uses interpretable risk factors rather than requiring
a heavy machine-learning framework. This makes it suitable as a
baseline model and keeps the backend easy to run.

The model considers factors such as:

- Asset age
- Temperature
- Load/utilization
- Voltage stress
- Current stress
- Historical failures
- Maintenance condition
- Anomaly frequency
- Environmental stress

The output is a probability-like failure risk score between
0.0 and 1.0.

This module does not access the database or external services.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


# ============================================================
# ENUMS
# ============================================================


class AssetFailureRisk(str, Enum):
    """Classification of predicted asset-failure risk."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# CONFIGURATION
# ============================================================


@dataclass
class AssetFailureModelConfig:
    """
    Configuration for the asset-failure model.

    The weights determine how strongly each risk factor
    contributes to the final score.
    """

    age_weight: float = 0.15

    temperature_weight: float = 0.15

    load_weight: float = 0.15

    voltage_weight: float = 0.10

    current_weight: float = 0.10

    historical_failure_weight: float = 0.15

    maintenance_weight: float = 0.10

    anomaly_weight: float = 0.10

    environmental_weight: float = 0.05

    def __post_init__(self) -> None:
        """Validate and normalize model configuration."""

        weights = [
            self.age_weight,
            self.temperature_weight,
            self.load_weight,
            self.voltage_weight,
            self.current_weight,
            self.historical_failure_weight,
            self.maintenance_weight,
            self.anomaly_weight,
            self.environmental_weight,
        ]

        weights = [
            max(0.0, float(weight))
            for weight in weights
        ]

        total = sum(weights)

        if total <= 0.0:
            raise ValueError(
                "At least one model weight must be greater than zero."
            )

        (
            self.age_weight,
            self.temperature_weight,
            self.load_weight,
            self.voltage_weight,
            self.current_weight,
            self.historical_failure_weight,
            self.maintenance_weight,
            self.anomaly_weight,
            self.environmental_weight,
        ) = weights

        # Normalize weights so their total is exactly 1.0.
        self.age_weight /= total
        self.temperature_weight /= total
        self.load_weight /= total
        self.voltage_weight /= total
        self.current_weight /= total
        self.historical_failure_weight /= total
        self.maintenance_weight /= total
        self.anomaly_weight /= total
        self.environmental_weight /= total


# ============================================================
# INPUT DATA
# ============================================================


@dataclass
class AssetFailureFeatures:
    """
    Features used by the asset-failure model.

    All risk-oriented fields are expected to be approximately
    normalized between 0.0 and 1.0.

    A value of:

        0.0 = little or no risk
        1.0 = very high risk
    """

    age_risk: float = 0.0

    temperature_risk: float = 0.0

    load_risk: float = 0.0

    voltage_risk: float = 0.0

    current_risk: float = 0.0

    historical_failure_risk: float = 0.0

    maintenance_risk: float = 0.0

    anomaly_risk: float = 0.0

    environmental_risk: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """Clamp all risk values to the 0-1 range."""

        self.age_risk = _clamp(
            self.age_risk
        )

        self.temperature_risk = _clamp(
            self.temperature_risk
        )

        self.load_risk = _clamp(
            self.load_risk
        )

        self.voltage_risk = _clamp(
            self.voltage_risk
        )

        self.current_risk = _clamp(
            self.current_risk
        )

        self.historical_failure_risk = _clamp(
            self.historical_failure_risk
        )

        self.maintenance_risk = _clamp(
            self.maintenance_risk
        )

        self.anomaly_risk = _clamp(
            self.anomaly_risk
        )

        self.environmental_risk = _clamp(
            self.environmental_risk
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert features into a dictionary."""

        return {
            "age_risk": self.age_risk,
            "temperature_risk": self.temperature_risk,
            "load_risk": self.load_risk,
            "voltage_risk": self.voltage_risk,
            "current_risk": self.current_risk,
            "historical_failure_risk": (
                self.historical_failure_risk
            ),
            "maintenance_risk": self.maintenance_risk,
            "anomaly_risk": self.anomaly_risk,
            "environmental_risk": (
                self.environmental_risk
            ),
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# PREDICTION RESULT
# ============================================================


@dataclass
class AssetFailurePrediction:
    """
    Result produced by the asset-failure model.
    """

    asset_id: str | None

    failure_probability: float

    risk_score: float

    risk_level: AssetFailureRisk

    confidence: float

    contributing_factors: list[str] = field(
        default_factory=list
    )

    features: AssetFailureFeatures | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def is_high_risk(self) -> bool:
        """Return True when the asset has high or critical risk."""

        return self.risk_level in {
            AssetFailureRisk.HIGH,
            AssetFailureRisk.CRITICAL,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert prediction into a dictionary."""

        return {
            "asset_id": self.asset_id,
            "failure_probability": (
                self.failure_probability
            ),
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "confidence": self.confidence,
            "is_high_risk": self.is_high_risk,
            "contributing_factors": list(
                self.contributing_factors
            ),
            "features": (
                self.features.to_dict()
                if self.features is not None
                else None
            ),
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def _clamp(
    value: Any,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    """Convert a value to float and clamp it."""

    try:
        numeric = float(
            value
        )
    except (
        TypeError,
        ValueError,
    ):
        numeric = minimum

    if not math.isfinite(
        numeric
    ):
        numeric = minimum

    return max(
        minimum,
        min(
            maximum,
            numeric,
        ),
    )


def _number(
    data: Mapping[str, Any],
    *keys: str,
    default: float = 0.0,
) -> float:
    """Return the first usable numeric value from a mapping."""

    for key in keys:
        if key not in data:
            continue

        try:
            value = float(
                data[key]
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if math.isfinite(
            value
        ):
            return value

    return default


def _string(
    data: Mapping[str, Any],
    *keys: str,
) -> str | None:
    """Return the first non-empty string from a mapping."""

    for key in keys:
        if key not in data:
            continue

        value = data[key]

        if value is None:
            continue

        text = str(
            value
        ).strip()

        if text:
            return text

    return None


# ============================================================
# MODEL
# ============================================================


class AssetFailureModel:
    """
    Interpretable asset-failure risk model.

    This is a baseline scoring model. It is intentionally
    deterministic so that every prediction can be explained by
    its contributing factors.

    It can later be replaced or extended with a trained ML model
    without changing the service-level interface.
    """

    def __init__(
        self,
        config: AssetFailureModelConfig | None = None,
    ) -> None:
        """Initialize the model."""

        self.config = (
            config
            if config is not None
            else AssetFailureModelConfig()
        )

    # ========================================================
    # FEATURE CONSTRUCTION
    # ========================================================

    def build_features(
        self,
        data: Mapping[str, Any],
    ) -> AssetFailureFeatures:
        """
        Build normalized failure-risk features from raw asset
        telemetry and metadata.
        """

        age_risk = self._age_risk(
            _number(
                data,
                "age_years",
                "asset_age_years",
                default=0.0,
            )
        )

        temperature_risk = self._temperature_risk(
            _number(
                data,
                "temperature_c",
                "temperature",
                "temp_c",
                default=25.0,
            )
        )

        load_risk = self._load_risk(
            _number(
                data,
                "load_ratio",
                "utilization",
                "utilization_ratio",
                "loading_percent",
                default=0.0,
            )
        )

        voltage_risk = self._voltage_risk(
            _number(
                data,
                "voltage_deviation",
                "voltage_deviation_percent",
                default=0.0,
            )
        )

        current_risk = self._current_risk(
            _number(
                data,
                "current_ratio",
                "current_utilization",
                "current_loading_percent",
                default=0.0,
            )
        )

        historical_failure_risk = (
            self._historical_failure_risk(
                _number(
                    data,
                    "failure_count",
                    "historical_failures",
                    "past_failures",
                    default=0.0,
                )
            )
        )

        maintenance_risk = self._maintenance_risk(
            data
        )

        anomaly_risk = self._anomaly_risk(
            _number(
                data,
                "anomaly_score",
                "anomaly_risk",
                default=0.0,
            )
        )

        environmental_risk = (
            self._environmental_risk(
                data
            )
        )

        return AssetFailureFeatures(
            age_risk=age_risk,
            temperature_risk=temperature_risk,
            load_risk=load_risk,
            voltage_risk=voltage_risk,
            current_risk=current_risk,
            historical_failure_risk=(
                historical_failure_risk
            ),
            maintenance_risk=maintenance_risk,
            anomaly_risk=anomaly_risk,
            environmental_risk=(
                environmental_risk
            ),
        )

    # ========================================================
    # INDIVIDUAL FEATURE TRANSFORMS
    # ========================================================

    @staticmethod
    def _age_risk(
        age_years: float,
    ) -> float:
        """
        Convert asset age into a risk value.

        The model gradually increases risk with age and reaches
        maximum age-related risk around 40 years.
        """

        return _clamp(
            age_years / 40.0
        )

    @staticmethod
    def _temperature_risk(
        temperature_c: float,
    ) -> float:
        """
        Estimate thermal stress.

        Normal temperatures produce low risk. Risk increases
        substantially above approximately 70 C.
        """

        if temperature_c <= 50.0:
            return 0.0

        if temperature_c >= 120.0:
            return 1.0

        return _clamp(
            (
                temperature_c
                - 50.0
            )
            / 70.0
        )

    @staticmethod
    def _load_risk(
        load_ratio: float,
    ) -> float:
        """
        Estimate loading stress.

        Accepts either a ratio such as 0.85 or a percentage such
        as 85.
        """

        if load_ratio > 2.0:
            load_ratio /= 100.0

        load_ratio = _clamp(
            load_ratio
        )

        if load_ratio <= 0.70:
            return 0.0

        if load_ratio >= 1.20:
            return 1.0

        return _clamp(
            (
                load_ratio
                - 0.70
            )
            / 0.50
        )

    @staticmethod
    def _voltage_risk(
        deviation: float,
    ) -> float:
        """
        Estimate voltage-stress risk.

        Accepts a deviation ratio or percentage.
        """

        deviation = abs(
            deviation
        )

        if deviation > 2.0:
            deviation /= 100.0

        if deviation <= 0.05:
            return 0.0

        if deviation >= 0.30:
            return 1.0

        return _clamp(
            (
                deviation
                - 0.05
            )
            / 0.25
        )

    @staticmethod
    def _current_risk(
        current_ratio: float,
    ) -> float:
        """
        Estimate current-loading risk.

        Accepts a ratio or percentage.
        """

        if current_ratio > 2.0:
            current_ratio /= 100.0

        current_ratio = _clamp(
            current_ratio
        )

        if current_ratio <= 0.70:
            return 0.0

        if current_ratio >= 1.20:
            return 1.0

        return _clamp(
            (
                current_ratio
                - 0.70
            )
            / 0.50
        )

    @staticmethod
    def _historical_failure_risk(
        failure_count: float,
    ) -> float:
        """
        Estimate risk based on historical failures.

        Risk saturates at five or more previous failures.
        """

        return _clamp(
            failure_count
            / 5.0
        )

    @staticmethod
    def _maintenance_risk(
        data: Mapping[str, Any],
    ) -> float:
        """
        Estimate maintenance-related risk.

        Supports:

        - maintenance_risk
        - maintenance_score
        - days_since_maintenance
        """

        if "maintenance_risk" in data:
            return _clamp(
                data["maintenance_risk"]
            )

        if "maintenance_score" in data:
            score = _clamp(
                data["maintenance_score"]
            )

            return 1.0 - score

        days = _number(
            data,
            "days_since_maintenance",
            "maintenance_age_days",
            default=0.0,
        )

        return _clamp(
            days / 730.0
        )

    @staticmethod
    def _anomaly_risk(
        anomaly_score: float,
    ) -> float:
        """
        Normalize an anomaly score.
        """

        return _clamp(
            anomaly_score
        )

    @staticmethod
    def _environmental_risk(
        data: Mapping[str, Any],
    ) -> float:
        """
        Estimate environmental risk.

        If a precomputed environmental risk is supplied, use it.

        Otherwise, derive a conservative score from:

        - Humidity
        - Wind speed
        - Rainfall
        - Flood risk
        """

        if "environmental_risk" in data:
            return _clamp(
                data["environmental_risk"]
            )

        risks: list[float] = []

        humidity = _number(
            data,
            "humidity_percent",
            "humidity",
            default=-1.0,
        )

        if humidity >= 0.0:
            risks.append(
                _clamp(
                    (
                        humidity
                        - 70.0
                    )
                    / 30.0
                )
            )

        wind_speed = _number(
            data,
            "wind_speed_kmh",
            "wind_speed",
            default=-1.0,
        )

        if wind_speed >= 0.0:
            risks.append(
                _clamp(
                    (
                        wind_speed
                        - 50.0
                    )
                    / 100.0
                )
            )

        rainfall = _number(
            data,
            "rainfall_mm",
            "rainfall",
            default=-1.0,
        )

        if rainfall >= 0.0:
            risks.append(
                _clamp(
                    (
                        rainfall
                        - 50.0
                    )
                    / 150.0
                )
            )

        flood_risk = _number(
            data,
            "flood_risk",
            default=-1.0,
        )

        if flood_risk >= 0.0:
            risks.append(
                _clamp(
                    flood_risk
                )
            )

        if not risks:
            return 0.0

        return sum(
            risks
        ) / len(
            risks
        )

    # ========================================================
    # PREDICTION
    # ========================================================

    def predict(
        self,
        data: Mapping[str, Any],
        *,
        asset_id: str | None = None,
    ) -> AssetFailurePrediction:
        """
        Predict asset-failure risk from raw feature data.
        """

        if not isinstance(
            data,
            Mapping,
        ):
            raise TypeError(
                "Asset data must be a mapping."
            )

        features = self.build_features(
            data
        )

        return self.predict_from_features(
            features,
            asset_id=(
                asset_id
                if asset_id is not None
                else _string(
                    data,
                    "asset_id",
                    "asset",
                    "id",
                )
            ),
        )

    def predict_from_features(
        self,
        features: AssetFailureFeatures,
        *,
        asset_id: str | None = None,
    ) -> AssetFailurePrediction:
        """
        Predict asset-failure risk from normalized features.
        """

        weighted_score = (
            features.age_risk
            * self.config.age_weight
            + features.temperature_risk
            * self.config.temperature_weight
            + features.load_risk
            * self.config.load_weight
            + features.voltage_risk
            * self.config.voltage_weight
            + features.current_risk
            * self.config.current_weight
            + features.historical_failure_risk
            * self.config.historical_failure_weight
            + features.maintenance_risk
            * self.config.maintenance_weight
            + features.anomaly_risk
            * self.config.anomaly_weight
            + features.environmental_risk
            * self.config.environmental_weight
        )

        risk_score = _clamp(
            weighted_score
        )

        # Convert the risk score into a probability-like value.
        #
        # This is a calibrated scoring output, not a statistically
        # trained probability. A future trained model can replace
        # this transformation.
        failure_probability = _clamp(
            risk_score
            * risk_score
        )

        risk_level = self.classify_risk(
            risk_score
        )

        confidence = self._estimate_confidence(
            features
        )

        contributing_factors = (
            self._get_contributing_factors(
                features
            )
        )

        return AssetFailurePrediction(
            asset_id=asset_id,
            failure_probability=round(
                failure_probability,
                4,
            ),
            risk_score=round(
                risk_score,
                4,
            ),
            risk_level=risk_level,
            confidence=round(
                confidence,
                4,
            ),
            contributing_factors=(
                contributing_factors
            ),
            features=features,
            metadata={
                "model_type": (
                    "weighted_risk_baseline"
                ),
                "calibrated": False,
            },
        )

    # ========================================================
    # BATCH PREDICTION
    # ========================================================

    def predict_many(
        self,
        assets: list[Mapping[str, Any]],
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
    # RISK CLASSIFICATION
    # ========================================================

    @staticmethod
    def classify_risk(
        risk_score: float,
    ) -> AssetFailureRisk:
        """
        Convert a 0-1 risk score into a risk category.
        """

        score = _clamp(
            risk_score
        )

        if score >= 0.85:
            return AssetFailureRisk.CRITICAL

        if score >= 0.65:
            return AssetFailureRisk.HIGH

        if score >= 0.40:
            return AssetFailureRisk.MEDIUM

        if score >= 0.20:
            return AssetFailureRisk.LOW

        return AssetFailureRisk.VERY_LOW

    # ========================================================
    # CONFIDENCE
    # ========================================================

    @staticmethod
    def _estimate_confidence(
        features: AssetFailureFeatures,
    ) -> float:
        """
        Estimate confidence based on the number of informative
        features.

        This is not model probability confidence. It indicates how
        much usable information was available to the baseline
        scoring model.
        """

        values = [
            features.age_risk,
            features.temperature_risk,
            features.load_risk,
            features.voltage_risk,
            features.current_risk,
            features.historical_failure_risk,
            features.maintenance_risk,
            features.anomaly_risk,
            features.environmental_risk,
        ]

        informative = sum(
            1
            for value in values
            if value > 0.0
        )

        return _clamp(
            0.40
            + (
                informative
                / len(values)
            )
            * 0.60
        )

    # ========================================================
    # CONTRIBUTING FACTORS
    # ========================================================

    @staticmethod
    def _get_contributing_factors(
        features: AssetFailureFeatures,
    ) -> list[str]:
        """
        Return the strongest risk contributors.
        """

        factors = [
            (
                "age",
                features.age_risk,
            ),
            (
                "temperature",
                features.temperature_risk,
            ),
            (
                "load",
                features.load_risk,
            ),
            (
                "voltage",
                features.voltage_risk,
            ),
            (
                "current",
                features.current_risk,
            ),
            (
                "historical_failures",
                features.historical_failure_risk,
            ),
            (
                "maintenance",
                features.maintenance_risk,
            ),
            (
                "anomalies",
                features.anomaly_risk,
            ),
            (
                "environment",
                features.environmental_risk,
            ),
        ]

        factors.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return [
            name
            for name, score in factors
            if score >= 0.50
        ]

    # ========================================================
    # MODEL INFORMATION
    # ========================================================

    def model_info(
        self,
    ) -> dict[str, Any]:
        """
        Return information about the model.
        """

        return {
            "model_name": (
                "Asset Failure Risk Model"
            ),
            "model_type": (
                "weighted_risk_baseline"
            ),
            "version": "1.0",
            "requires_training": False,
            "uses_external_dependencies": False,
            "weights": {
                "age": self.config.age_weight,
                "temperature": (
                    self.config.temperature_weight
                ),
                "load": self.config.load_weight,
                "voltage": self.config.voltage_weight,
                "current": self.config.current_weight,
                "historical_failure": (
                    self.config.historical_failure_weight
                ),
                "maintenance": (
                    self.config.maintenance_weight
                ),
                "anomaly": (
                    self.config.anomaly_weight
                ),
                "environmental": (
                    self.config.environmental_weight
                ),
            },
        }


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def predict_asset_failure(
    data: Mapping[str, Any],
    *,
    asset_id: str | None = None,
    config: AssetFailureModelConfig | None = None,
) -> AssetFailurePrediction:
    """
    Convenience function for predicting asset-failure risk.
    """

    model = AssetFailureModel(
        config=config
    )

    return model.predict(
        data,
        asset_id=asset_id,
    )


def classify_failure_risk(
    risk_score: float,
) -> AssetFailureRisk:
    """
    Convenience function for classifying a risk score.
    """

    return AssetFailureModel.classify_risk(
        risk_score
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "AssetFailureRisk",
    "AssetFailureModelConfig",
    "AssetFailureFeatures",
    "AssetFailurePrediction",
    "AssetFailureModel",
    "predict_asset_failure",
    "classify_failure_risk",
]