"""
Blackout Oracle - Blackout Risk Model.

Provides a deterministic, interpretable model for estimating
grid-wide blackout risk from electrical, operational,
environmental, and network-stress indicators.

This is a baseline risk model, not a trained ML model.
It is intentionally dependency-free so it can run reliably
inside the backend before a trained model is introduced.

The output is a risk score between 0.0 and 1.0.

Risk score interpretation:

    0.00 - 0.19 : Very Low
    0.20 - 0.39 : Low
    0.40 - 0.59 : Medium
    0.60 - 0.79 : High
    0.80 - 1.00 : Critical

The model does NOT directly operate grid equipment and does
NOT create incidents or alerts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


# ============================================================
# ENUMS
# ============================================================


class BlackoutRiskLevel(str, Enum):
    """Classification of overall blackout risk."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# CONFIGURATION
# ============================================================


@dataclass
class BlackoutRiskModelConfig:
    """
    Configuration for the blackout-risk model.

    The weights determine the contribution of each risk category
    to the final score.
    """

    demand_supply_weight: float = 0.20

    frequency_weight: float = 0.15

    voltage_weight: float = 0.15

    transmission_loading_weight: float = 0.10

    generator_stress_weight: float = 0.10

    transformer_stress_weight: float = 0.10

    anomaly_weight: float = 0.05

    weather_weight: float = 0.05

    outage_weight: float = 0.05

    cascading_risk_weight: float = 0.05

    def __post_init__(self) -> None:
        """Validate and normalize model weights."""

        weights = [
            self.demand_supply_weight,
            self.frequency_weight,
            self.voltage_weight,
            self.transmission_loading_weight,
            self.generator_stress_weight,
            self.transformer_stress_weight,
            self.anomaly_weight,
            self.weather_weight,
            self.outage_weight,
            self.cascading_risk_weight,
        ]

        weights = [
            max(0.0, float(weight))
            for weight in weights
        ]

        total = sum(weights)

        if total <= 0.0:
            raise ValueError(
                "At least one blackout-risk model weight "
                "must be greater than zero."
            )

        (
            self.demand_supply_weight,
            self.frequency_weight,
            self.voltage_weight,
            self.transmission_loading_weight,
            self.generator_stress_weight,
            self.transformer_stress_weight,
            self.anomaly_weight,
            self.weather_weight,
            self.outage_weight,
            self.cascading_risk_weight,
        ) = weights

        self.demand_supply_weight /= total
        self.frequency_weight /= total
        self.voltage_weight /= total
        self.transmission_loading_weight /= total
        self.generator_stress_weight /= total
        self.transformer_stress_weight /= total
        self.anomaly_weight /= total
        self.weather_weight /= total
        self.outage_weight /= total
        self.cascading_risk_weight /= total


# ============================================================
# FEATURES
# ============================================================


@dataclass
class BlackoutRiskFeatures:
    """
    Normalized features used by the blackout-risk model.

    Every risk feature is represented between 0.0 and 1.0:

        0.0 = little or no risk
        1.0 = extremely high risk
    """

    demand_supply_risk: float = 0.0

    frequency_risk: float = 0.0

    voltage_risk: float = 0.0

    transmission_loading_risk: float = 0.0

    generator_stress_risk: float = 0.0

    transformer_stress_risk: float = 0.0

    anomaly_risk: float = 0.0

    weather_risk: float = 0.0

    outage_risk: float = 0.0

    cascading_risk: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """Clamp all feature values to 0-1."""

        self.demand_supply_risk = _clamp(
            self.demand_supply_risk
        )

        self.frequency_risk = _clamp(
            self.frequency_risk
        )

        self.voltage_risk = _clamp(
            self.voltage_risk
        )

        self.transmission_loading_risk = _clamp(
            self.transmission_loading_risk
        )

        self.generator_stress_risk = _clamp(
            self.generator_stress_risk
        )

        self.transformer_stress_risk = _clamp(
            self.transformer_stress_risk
        )

        self.anomaly_risk = _clamp(
            self.anomaly_risk
        )

        self.weather_risk = _clamp(
            self.weather_risk
        )

        self.outage_risk = _clamp(
            self.outage_risk
        )

        self.cascading_risk = _clamp(
            self.cascading_risk
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert features to a dictionary."""

        return {
            "demand_supply_risk": self.demand_supply_risk,
            "frequency_risk": self.frequency_risk,
            "voltage_risk": self.voltage_risk,
            "transmission_loading_risk": (
                self.transmission_loading_risk
            ),
            "generator_stress_risk": (
                self.generator_stress_risk
            ),
            "transformer_stress_risk": (
                self.transformer_stress_risk
            ),
            "anomaly_risk": self.anomaly_risk,
            "weather_risk": self.weather_risk,
            "outage_risk": self.outage_risk,
            "cascading_risk": self.cascading_risk,
            "metadata": dict(self.metadata),
        }


# ============================================================
# PREDICTION RESULT
# ============================================================


@dataclass
class BlackoutRiskPrediction:
    """
    Result produced by the blackout-risk model.
    """

    risk_score: float

    risk_level: BlackoutRiskLevel

    confidence: float

    estimated_probability: float

    contributing_factors: list[str] = field(
        default_factory=list
    )

    features: BlackoutRiskFeatures | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def is_high_risk(self) -> bool:
        """Return True when risk is high or critical."""

        return self.risk_level in {
            BlackoutRiskLevel.HIGH,
            BlackoutRiskLevel.CRITICAL,
        }

    @property
    def is_critical(self) -> bool:
        """Return True when risk is critical."""

        return (
            self.risk_level
            == BlackoutRiskLevel.CRITICAL
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert prediction to a dictionary."""

        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "confidence": self.confidence,
            "estimated_probability": (
                self.estimated_probability
            ),
            "is_high_risk": self.is_high_risk,
            "is_critical": self.is_critical,
            "contributing_factors": list(
                self.contributing_factors
            ),
            "features": (
                self.features.to_dict()
                if self.features is not None
                else None
            ),
            "metadata": dict(self.metadata),
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
        numeric = float(value)
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
    """Return the first usable numeric value."""

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


# ============================================================
# MODEL
# ============================================================


class BlackoutRiskModel:
    """
    Deterministic blackout-risk scoring model.

    The model combines several independent grid-stress
    indicators into one interpretable risk score.

    It is designed to work with telemetry and operational
    summaries coming from the rest of Blackout Oracle.
    """

    def __init__(
        self,
        config: BlackoutRiskModelConfig | None = None,
    ) -> None:
        """Initialize the blackout-risk model."""

        self.config = (
            config
            if config is not None
            else BlackoutRiskModelConfig()
        )

    # ========================================================
    # FEATURE BUILDING
    # ========================================================

    def build_features(
        self,
        data: Mapping[str, Any],
    ) -> BlackoutRiskFeatures:
        """
        Convert raw grid measurements into normalized risk
        features.
        """

        demand_supply_risk = (
            self._demand_supply_risk(
                data
            )
        )

        frequency_risk = (
            self._frequency_risk(
                data
            )
        )

        voltage_risk = (
            self._voltage_risk(
                data
            )
        )

        transmission_loading_risk = (
            self._transmission_loading_risk(
                data
            )
        )

        generator_stress_risk = (
            self._generator_stress_risk(
                data
            )
        )

        transformer_stress_risk = (
            self._transformer_stress_risk(
                data
            )
        )

        anomaly_risk = _clamp(
            _number(
                data,
                "anomaly_score",
                "anomaly_risk",
                default=0.0,
            )
        )

        weather_risk = (
            self._weather_risk(
                data
            )
        )

        outage_risk = (
            self._outage_risk(
                data
            )
        )

        cascading_risk = _clamp(
            _number(
                data,
                "cascading_risk",
                "cascade_risk",
                "cascading_failure_risk",
                default=0.0,
            )
        )

        return BlackoutRiskFeatures(
            demand_supply_risk=demand_supply_risk,
            frequency_risk=frequency_risk,
            voltage_risk=voltage_risk,
            transmission_loading_risk=(
                transmission_loading_risk
            ),
            generator_stress_risk=(
                generator_stress_risk
            ),
            transformer_stress_risk=(
                transformer_stress_risk
            ),
            anomaly_risk=anomaly_risk,
            weather_risk=weather_risk,
            outage_risk=outage_risk,
            cascading_risk=cascading_risk,
        )

    # ========================================================
    # DEMAND / SUPPLY
    # ========================================================

    @staticmethod
    def _demand_supply_risk(
        data: Mapping[str, Any],
    ) -> float:
        """
        Estimate risk from demand versus available generation.

        If both demand and generation are supplied, the ratio is:

            demand / generation

        Values approaching or exceeding 1.0 produce high risk.
        """

        explicit = _number(
            data,
            "demand_supply_risk",
            default=-1.0,
        )

        if explicit >= 0.0:
            return _clamp(
                explicit
            )

        demand = _number(
            data,
            "demand_mw",
            "load_mw",
            "total_demand_mw",
            default=-1.0,
        )

        generation = _number(
            data,
            "available_generation_mw",
            "available_power_mw",
            "generation_mw",
            "total_generation_mw",
            default=-1.0,
        )

        reserve = _number(
            data,
            "reserve_margin",
            "reserve_margin_ratio",
            default=-1.0,
        )

        if demand < 0.0:
            return 0.0

        if generation <= 0.0:
            return 1.0 if demand > 0.0 else 0.0

        ratio = (
            demand
            / generation
        )

        if ratio <= 0.70:
            risk = 0.0

        elif ratio >= 1.05:
            risk = 1.0

        else:
            risk = (
                ratio
                - 0.70
            ) / 0.35

        if reserve >= 0.0:
            if reserve > 1.0:
                reserve /= 100.0

            reserve_risk = _clamp(
                (
                    0.15
                    - reserve
                )
                / 0.15
            )

            risk = max(
                risk,
                reserve_risk,
            )

        return _clamp(
            risk
        )

    # ========================================================
    # FREQUENCY
    # ========================================================

    @staticmethod
    def _frequency_risk(
        data: Mapping[str, Any],
    ) -> float:
        """
        Estimate grid-frequency instability risk.

        50 Hz is used as the nominal reference because the
        Blackout Oracle project is intended for the Indian grid.

        The function accepts either frequency deviation or the
        actual frequency.
        """

        explicit = _number(
            data,
            "frequency_risk",
            default=-1.0,
        )

        if explicit >= 0.0:
            return _clamp(
                explicit
            )

        deviation = _number(
            data,
            "frequency_deviation",
            "frequency_deviation_hz",
            default=-1.0,
        )

        if deviation >= 0.0:
            if deviation > 1.0:
                deviation = abs(
                    deviation
                )

            else:
                deviation = abs(
                    deviation
                )

            if deviation <= 0.05:
                return 0.0

            if deviation >= 1.0:
                return 1.0

            return _clamp(
                (
                    deviation
                    - 0.05
                )
                / 0.95
            )

        frequency = _number(
            data,
            "frequency_hz",
            "frequency",
            default=50.0,
        )

        deviation = abs(
            frequency
            - 50.0
        )

        if deviation <= 0.05:
            return 0.0

        if deviation >= 1.0:
            return 1.0

        return _clamp(
            (
                deviation
                - 0.05
            )
            / 0.95
        )

    # ========================================================
    # VOLTAGE
    # ========================================================

    @staticmethod
    def _voltage_risk(
        data: Mapping[str, Any],
    ) -> float:
        """
        Estimate voltage instability risk.

        Uses supplied voltage deviation when available.
        """

        explicit = _number(
            data,
            "voltage_risk",
            default=-1.0,
        )

        if explicit >= 0.0:
            return _clamp(
                explicit
            )

        deviation = abs(
            _number(
                data,
                "voltage_deviation",
                "voltage_deviation_ratio",
                "voltage_deviation_percent",
                default=0.0,
            )
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

    # ========================================================
    # TRANSMISSION LOADING
    # ========================================================

    @staticmethod
    def _transmission_loading_risk(
        data: Mapping[str, Any],
    ) -> float:
        """
        Estimate risk caused by overloaded transmission lines.
        """

        explicit = _number(
            data,
            "transmission_loading_risk",
            default=-1.0,
        )

        if explicit >= 0.0:
            return _clamp(
                explicit
            )

        loading = _number(
            data,
            "transmission_loading_ratio",
            "line_loading_ratio",
            "transmission_utilization",
            "line_utilization",
            "transmission_loading_percent",
            default=0.0,
        )

        if loading > 2.0:
            loading /= 100.0

        loading = _clamp(
            loading
        )

        if loading <= 0.70:
            return 0.0

        if loading >= 1.20:
            return 1.0

        return _clamp(
            (
                loading
                - 0.70
            )
            / 0.50
        )

    # ========================================================
    # GENERATOR STRESS
    # ========================================================

    @staticmethod
    def _generator_stress_risk(
        data: Mapping[str, Any],
    ) -> float:
        """
        Estimate generator fleet stress.
        """

        explicit = _number(
            data,
            "generator_stress_risk",
            "generation_stress_risk",
            default=-1.0,
        )

        if explicit >= 0.0:
            return _clamp(
                explicit
            )

        utilization = _number(
            data,
            "generator_utilization",
            "generation_utilization",
            "generator_loading_ratio",
            "generation_loading_ratio",
            default=0.0,
        )

        if utilization > 2.0:
            utilization /= 100.0

        utilization = _clamp(
            utilization
        )

        if utilization <= 0.70:
            return 0.0

        if utilization >= 1.15:
            return 1.0

        return _clamp(
            (
                utilization
                - 0.70
            )
            / 0.45
        )

    # ========================================================
    # TRANSFORMER STRESS
    # ========================================================

    @staticmethod
    def _transformer_stress_risk(
        data: Mapping[str, Any],
    ) -> float:
        """
        Estimate transformer fleet stress.
        """

        explicit = _number(
            data,
            "transformer_stress_risk",
            default=-1.0,
        )

        if explicit >= 0.0:
            return _clamp(
                explicit
            )

        loading = _number(
            data,
            "transformer_loading_ratio",
            "transformer_utilization",
            "transformer_loading_percent",
            default=0.0,
        )

        if loading > 2.0:
            loading /= 100.0

        loading = _clamp(
            loading
        )

        temperature = _number(
            data,
            "transformer_temperature_c",
            "transformer_temp_c",
            default=-1.0,
        )

        loading_risk = 0.0

        if loading <= 0.70:
            loading_risk = 0.0

        elif loading >= 1.20:
            loading_risk = 1.0

        else:
            loading_risk = _clamp(
                (
                    loading
                    - 0.70
                )
                / 0.50
            )

        temperature_risk = 0.0

        if temperature >= 0.0:
            if temperature <= 60.0:
                temperature_risk = 0.0

            elif temperature >= 120.0:
                temperature_risk = 1.0

            else:
                temperature_risk = _clamp(
                    (
                        temperature
                        - 60.0
                    )
                    / 60.0
                )

        return max(
            loading_risk,
            temperature_risk,
        )

    # ========================================================
    # WEATHER
    # ========================================================

    @staticmethod
    def _weather_risk(
        data: Mapping[str, Any],
    ) -> float:
        """
        Estimate weather-related grid risk.

        Explicit weather-risk values take precedence.
        Otherwise a conservative combination of available
        environmental indicators is used.
        """

        explicit = _number(
            data,
            "weather_risk",
            "environmental_risk",
            default=-1.0,
        )

        if explicit >= 0.0:
            return _clamp(
                explicit
            )

        risks: list[float] = []

        wind = _number(
            data,
            "wind_speed_kmh",
            "wind_speed",
            default=-1.0,
        )

        if wind >= 0.0:
            if wind <= 40.0:
                risks.append(
                    0.0
                )

            elif wind >= 120.0:
                risks.append(
                    1.0
                )

            else:
                risks.append(
                    _clamp(
                        (
                            wind
                            - 40.0
                        )
                        / 80.0
                    )
                )

        rainfall = _number(
            data,
            "rainfall_mm",
            "rainfall",
            default=-1.0,
        )

        if rainfall >= 0.0:
            if rainfall <= 20.0:
                risks.append(
                    0.0
                )

            elif rainfall >= 150.0:
                risks.append(
                    1.0
                )

            else:
                risks.append(
                    _clamp(
                        (
                            rainfall
                            - 20.0
                        )
                        / 130.0
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

        storm_risk = _number(
            data,
            "storm_risk",
            "cyclone_risk",
            default=-1.0,
        )

        if storm_risk >= 0.0:
            risks.append(
                _clamp(
                    storm_risk
                )
            )

        if not risks:
            return 0.0

        return _clamp(
            sum(risks)
            / len(risks)
        )

    # ========================================================
    # OUTAGE RISK
    # ========================================================

    @staticmethod
    def _outage_risk(
        data: Mapping[str, Any],
    ) -> float:
        """
        Estimate current outage-related risk.
        """

        explicit = _number(
            data,
            "outage_risk",
            default=-1.0,
        )

        if explicit >= 0.0:
            return _clamp(
                explicit
            )

        active_outages = _number(
            data,
            "active_outages",
            "outage_count",
            default=0.0,
        )

        critical_outages = _number(
            data,
            "critical_outages",
            default=0.0,
        )

        total_assets = _number(
            data,
            "total_assets",
            "monitored_assets",
            default=-1.0,
        )

        if total_assets > 0.0:
            outage_ratio = (
                active_outages
                / total_assets
            )

            ratio_risk = _clamp(
                outage_ratio
                / 0.20
            )

        else:
            ratio_risk = _clamp(
                active_outages
                / 10.0
            )

        critical_risk = _clamp(
            critical_outages
            / 3.0
        )

        return max(
            ratio_risk,
            critical_risk,
        )

    # ========================================================
    # PREDICTION
    # ========================================================

    def predict(
        self,
        data: Mapping[str, Any],
    ) -> BlackoutRiskPrediction:
        """
        Predict overall blackout risk.
        """

        if not isinstance(
            data,
            Mapping,
        ):
            raise TypeError(
                "Blackout-risk input must be a mapping."
            )

        features = self.build_features(
            data
        )

        return self.predict_from_features(
            features
        )

    def predict_from_features(
        self,
        features: BlackoutRiskFeatures,
    ) -> BlackoutRiskPrediction:
        """
        Predict blackout risk from normalized features.
        """

        score = (
            features.demand_supply_risk
            * self.config.demand_supply_weight
            + features.frequency_risk
            * self.config.frequency_weight
            + features.voltage_risk
            * self.config.voltage_weight
            + features.transmission_loading_risk
            * self.config.transmission_loading_weight
            + features.generator_stress_risk
            * self.config.generator_stress_weight
            + features.transformer_stress_risk
            * self.config.transformer_stress_weight
            + features.anomaly_risk
            * self.config.anomaly_weight
            + features.weather_risk
            * self.config.weather_weight
            + features.outage_risk
            * self.config.outage_weight
            + features.cascading_risk
            * self.config.cascading_risk_weight
        )

        score = _clamp(
            score
        )

        # Add a modest interaction term for dangerous combinations.
        #
        # Individually moderate risks can become substantially more
        # concerning when they occur simultaneously.
        interaction = self._interaction_risk(
            features
        )

        score = _clamp(
            score
            + interaction
        )

        risk_level = self.classify_risk(
            score
        )

        estimated_probability = self._estimate_probability(
            score
        )

        confidence = self._estimate_confidence(
            features
        )

        contributing_factors = (
            self._get_contributing_factors(
                features
            )
        )

        return BlackoutRiskPrediction(
            risk_score=round(
                score,
                4,
            ),
            risk_level=risk_level,
            confidence=round(
                confidence,
                4,
            ),
            estimated_probability=round(
                estimated_probability,
                4,
            ),
            contributing_factors=(
                contributing_factors
            ),
            features=features,
            metadata={
                "model_type": (
                    "weighted_grid_risk_baseline"
                ),
                "model_version": "1.0",
                "trained": False,
                "probability_calibrated": False,
            },
        )

    # ========================================================
    # INTERACTION RISK
    # ========================================================

    @staticmethod
    def _interaction_risk(
        features: BlackoutRiskFeatures,
    ) -> float:
        """
        Account for combinations of simultaneous stress factors.

        This does not replace the weighted score. It adds a small
        additional penalty when multiple major grid risks are
        simultaneously elevated.
        """

        major_risks = [
            features.demand_supply_risk,
            features.frequency_risk,
            features.voltage_risk,
            features.transmission_loading_risk,
            features.generator_stress_risk,
            features.transformer_stress_risk,
            features.cascading_risk,
        ]

        high_risk_count = sum(
            1
            for risk in major_risks
            if risk >= 0.70
        )

        if high_risk_count <= 1:
            return 0.0

        if high_risk_count >= 5:
            return 0.10

        return 0.025 * (
            high_risk_count - 1
        )

    # ========================================================
    # PROBABILITY ESTIMATE
    # ========================================================

    @staticmethod
    def _estimate_probability(
        score: float,
    ) -> float:
        """
        Convert risk score into a probability-like value.

        Important:
        This is NOT a statistically calibrated probability.
        A trained model should replace this function when
        historical blackout labels become available.
        """

        score = _clamp(
            score
        )

        # Smooth nonlinear mapping that keeps very-low scores
        # conservative while increasing sharply at high risk.
        probability = score ** 1.35

        return _clamp(
            probability
        )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    @staticmethod
    def _estimate_confidence(
        features: BlackoutRiskFeatures,
    ) -> float:
        """
        Estimate confidence from the amount of information
        available.

        This is an information-coverage score, not model accuracy.
        """

        values = [
            features.demand_supply_risk,
            features.frequency_risk,
            features.voltage_risk,
            features.transmission_loading_risk,
            features.generator_stress_risk,
            features.transformer_stress_risk,
            features.anomaly_risk,
            features.weather_risk,
            features.outage_risk,
            features.cascading_risk,
        ]

        # A non-zero feature indicates that meaningful information
        # was supplied for that category.
        informative = sum(
            1
            for value in values
            if value != 0.0
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
        features: BlackoutRiskFeatures,
    ) -> list[str]:
        """
        Return major contributors to the current blackout risk.
        """

        factors = [
            (
                "demand_supply",
                features.demand_supply_risk,
            ),
            (
                "frequency",
                features.frequency_risk,
            ),
            (
                "voltage",
                features.voltage_risk,
            ),
            (
                "transmission_loading",
                features.transmission_loading_risk,
            ),
            (
                "generator_stress",
                features.generator_stress_risk,
            ),
            (
                "transformer_stress",
                features.transformer_stress_risk,
            ),
            (
                "anomalies",
                features.anomaly_risk,
            ),
            (
                "weather",
                features.weather_risk,
            ),
            (
                "outages",
                features.outage_risk,
            ),
            (
                "cascading_failure",
                features.cascading_risk,
            ),
        ]

        factors.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return [
            name
            for name, value in factors
            if value >= 0.50
        ]

    # ========================================================
    # RISK CLASSIFICATION
    # ========================================================

    @staticmethod
    def classify_risk(
        risk_score: float,
    ) -> BlackoutRiskLevel:
        """
        Convert a 0-1 risk score into a risk category.
        """

        score = _clamp(
            risk_score
        )

        if score >= 0.80:
            return BlackoutRiskLevel.CRITICAL

        if score >= 0.60:
            return BlackoutRiskLevel.HIGH

        if score >= 0.40:
            return BlackoutRiskLevel.MEDIUM

        if score >= 0.20:
            return BlackoutRiskLevel.LOW

        return BlackoutRiskLevel.VERY_LOW

    # ========================================================
    # MODEL INFORMATION
    # ========================================================

    def model_info(
        self,
    ) -> dict[str, Any]:
        """
        Return model metadata and configuration.
        """

        return {
            "model_name": (
                "Blackout Risk Model"
            ),
            "model_type": (
                "weighted_grid_risk_baseline"
            ),
            "version": "1.0",
            "trained": False,
            "probability_calibrated": False,
            "weights": {
                "demand_supply": (
                    self.config.demand_supply_weight
                ),
                "frequency": (
                    self.config.frequency_weight
                ),
                "voltage": (
                    self.config.voltage_weight
                ),
                "transmission_loading": (
                    self.config.transmission_loading_weight
                ),
                "generator_stress": (
                    self.config.generator_stress_weight
                ),
                "transformer_stress": (
                    self.config.transformer_stress_weight
                ),
                "anomaly": (
                    self.config.anomaly_weight
                ),
                "weather": (
                    self.config.weather_weight
                ),
                "outage": (
                    self.config.outage_weight
                ),
                "cascading_risk": (
                    self.config.cascading_risk_weight
                ),
            },
        }


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def predict_blackout_risk(
    data: Mapping[str, Any],
    *,
    config: BlackoutRiskModelConfig | None = None,
) -> BlackoutRiskPrediction:
    """
    Convenience function for blackout-risk prediction.
    """

    model = BlackoutRiskModel(
        config=config
    )

    return model.predict(
        data
    )


def classify_blackout_risk(
    risk_score: float,
) -> BlackoutRiskLevel:
    """
    Convenience function for risk classification.
    """

    return BlackoutRiskModel.classify_risk(
        risk_score
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "BlackoutRiskLevel",
    "BlackoutRiskModelConfig",
    "BlackoutRiskFeatures",
    "BlackoutRiskPrediction",
    "BlackoutRiskModel",
    "predict_blackout_risk",
    "classify_blackout_risk",
]