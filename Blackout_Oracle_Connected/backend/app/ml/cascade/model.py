"""
Blackout Oracle - Cascading Failure Model.

Provides a deterministic and interpretable model for estimating
the risk that a failure in one grid component may propagate to
other components.

The model considers:

- Initial asset failures
- Transmission-line loading
- Transformer loading
- Generator stress
- Load stress
- Network connectivity
- Redundancy
- Contingency count
- Existing outages
- Frequency instability
- Voltage instability

This is a baseline cascade-risk model. It is not a trained
machine-learning model and does not directly control electrical
equipment.

The model is intentionally dependency-free.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


# ============================================================
# ENUMS
# ============================================================


class CascadeRiskLevel(str, Enum):
    """Classification of cascading-failure risk."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CascadeState(str, Enum):
    """Overall state of the cascade analysis."""

    STABLE = "stable"
    STRESSED = "stressed"
    PROPAGATING = "propagating"
    CRITICAL = "critical"


# ============================================================
# CONFIGURATION
# ============================================================


@dataclass
class CascadeModelConfig:
    """
    Configuration for the cascade-risk model.

    All weights are normalized automatically.
    """

    initial_failure_weight: float = 0.15

    transmission_loading_weight: float = 0.15

    transformer_loading_weight: float = 0.10

    generator_stress_weight: float = 0.10

    load_stress_weight: float = 0.10

    connectivity_weight: float = 0.10

    redundancy_weight: float = 0.10

    outage_weight: float = 0.05

    frequency_weight: float = 0.05

    voltage_weight: float = 0.05

    contingency_weight: float = 0.05

    def __post_init__(self) -> None:
        """Validate and normalize weights."""

        weights = [
            self.initial_failure_weight,
            self.transmission_loading_weight,
            self.transformer_loading_weight,
            self.generator_stress_weight,
            self.load_stress_weight,
            self.connectivity_weight,
            self.redundancy_weight,
            self.outage_weight,
            self.frequency_weight,
            self.voltage_weight,
            self.contingency_weight,
        ]

        weights = [
            max(
                0.0,
                float(weight),
            )
            for weight in weights
        ]

        total = sum(weights)

        if total <= 0.0:
            raise ValueError(
                "At least one cascade-model weight "
                "must be greater than zero."
            )

        (
            self.initial_failure_weight,
            self.transmission_loading_weight,
            self.transformer_loading_weight,
            self.generator_stress_weight,
            self.load_stress_weight,
            self.connectivity_weight,
            self.redundancy_weight,
            self.outage_weight,
            self.frequency_weight,
            self.voltage_weight,
            self.contingency_weight,
        ) = weights

        self.initial_failure_weight /= total
        self.transmission_loading_weight /= total
        self.transformer_loading_weight /= total
        self.generator_stress_weight /= total
        self.load_stress_weight /= total
        self.connectivity_weight /= total
        self.redundancy_weight /= total
        self.outage_weight /= total
        self.frequency_weight /= total
        self.voltage_weight /= total
        self.contingency_weight /= total


# ============================================================
# FEATURES
# ============================================================


@dataclass
class CascadeFeatures:
    """
    Normalized features used for cascade-risk estimation.

    Every risk value is between 0.0 and 1.0:

        0.0 = little or no risk
        1.0 = extreme risk
    """

    initial_failure_risk: float = 0.0

    transmission_loading_risk: float = 0.0

    transformer_loading_risk: float = 0.0

    generator_stress_risk: float = 0.0

    load_stress_risk: float = 0.0

    connectivity_risk: float = 0.0

    redundancy_risk: float = 0.0

    outage_risk: float = 0.0

    frequency_risk: float = 0.0

    voltage_risk: float = 0.0

    contingency_risk: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """Clamp all risk values to 0-1."""

        self.initial_failure_risk = _clamp(
            self.initial_failure_risk
        )

        self.transmission_loading_risk = _clamp(
            self.transmission_loading_risk
        )

        self.transformer_loading_risk = _clamp(
            self.transformer_loading_risk
        )

        self.generator_stress_risk = _clamp(
            self.generator_stress_risk
        )

        self.load_stress_risk = _clamp(
            self.load_stress_risk
        )

        self.connectivity_risk = _clamp(
            self.connectivity_risk
        )

        self.redundancy_risk = _clamp(
            self.redundancy_risk
        )

        self.outage_risk = _clamp(
            self.outage_risk
        )

        self.frequency_risk = _clamp(
            self.frequency_risk
        )

        self.voltage_risk = _clamp(
            self.voltage_risk
        )

        self.contingency_risk = _clamp(
            self.contingency_risk
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert features to a dictionary."""

        return {
            "initial_failure_risk": (
                self.initial_failure_risk
            ),
            "transmission_loading_risk": (
                self.transmission_loading_risk
            ),
            "transformer_loading_risk": (
                self.transformer_loading_risk
            ),
            "generator_stress_risk": (
                self.generator_stress_risk
            ),
            "load_stress_risk": (
                self.load_stress_risk
            ),
            "connectivity_risk": (
                self.connectivity_risk
            ),
            "redundancy_risk": (
                self.redundancy_risk
            ),
            "outage_risk": (
                self.outage_risk
            ),
            "frequency_risk": (
                self.frequency_risk
            ),
            "voltage_risk": (
                self.voltage_risk
            ),
            "contingency_risk": (
                self.contingency_risk
            ),
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# PREDICTION
# ============================================================


@dataclass
class CascadePrediction:
    """
    Result produced by the cascade-risk model.
    """

    cascade_score: float

    cascade_probability: float

    risk_level: CascadeRiskLevel

    state: CascadeState

    confidence: float

    estimated_affected_assets: int

    propagation_factor: float

    contributing_factors: list[str] = field(
        default_factory=list
    )

    features: CascadeFeatures | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def is_high_risk(self) -> bool:
        """Return True when cascade risk is high or critical."""

        return self.risk_level in {
            CascadeRiskLevel.HIGH,
            CascadeRiskLevel.CRITICAL,
        }

    @property
    def is_propagating(self) -> bool:
        """Return True when the system appears to be propagating."""

        return self.state in {
            CascadeState.PROPAGATING,
            CascadeState.CRITICAL,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert prediction to a dictionary."""

        return {
            "cascade_score": self.cascade_score,
            "cascade_probability": (
                self.cascade_probability
            ),
            "risk_level": self.risk_level.value,
            "state": self.state.value,
            "confidence": self.confidence,
            "estimated_affected_assets": (
                self.estimated_affected_assets
            ),
            "propagation_factor": (
                self.propagation_factor
            ),
            "is_high_risk": self.is_high_risk,
            "is_propagating": self.is_propagating,
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
# CASCADE MODEL
# ============================================================


class CascadeModel:
    """
    Deterministic cascading-failure risk model.

    The model estimates whether stress or failures in one part of
    the grid could propagate to additional components.

    It is a decision-support model only. It does not directly
    operate or disconnect grid equipment.
    """

    def __init__(
        self,
        config: CascadeModelConfig | None = None,
    ) -> None:
        """Initialize the cascade model."""

        self.config = (
            config
            if config is not None
            else CascadeModelConfig()
        )

    # ========================================================
    # FEATURE BUILDING
    # ========================================================

    def build_features(
        self,
        data: Mapping[str, Any],
    ) -> CascadeFeatures:
        """
        Convert raw grid information into normalized cascade-risk
        features.
        """

        return CascadeFeatures(
            initial_failure_risk=(
                self._initial_failure_risk(
                    data
                )
            ),
            transmission_loading_risk=(
                self._transmission_loading_risk(
                    data
                )
            ),
            transformer_loading_risk=(
                self._transformer_loading_risk(
                    data
                )
            ),
            generator_stress_risk=(
                self._generator_stress_risk(
                    data
                )
            ),
            load_stress_risk=(
                self._load_stress_risk(
                    data
                )
            ),
            connectivity_risk=(
                self._connectivity_risk(
                    data
                )
            ),
            redundancy_risk=(
                self._redundancy_risk(
                    data
                )
            ),
            outage_risk=(
                self._outage_risk(
                    data
                )
            ),
            frequency_risk=(
                self._frequency_risk(
                    data
                )
            ),
            voltage_risk=(
                self._voltage_risk(
                    data
                )
            ),
            contingency_risk=(
                self._contingency_risk(
                    data
                )
            ),
        )

    # ========================================================
    # INITIAL FAILURE
    # ========================================================

    @staticmethod
    def _initial_failure_risk(
        data: Mapping[str, Any],
    ) -> float:
        """Estimate the risk originating from existing failures."""

        explicit = _number(
            data,
            "initial_failure_risk",
            "initial_failure_score",
            default=-1.0,
        )

        if explicit >= 0.0:
            return _clamp(
                explicit
            )

        failures = _number(
            data,
            "initial_failures",
            "failed_assets",
            "recent_failures",
            "new_failures",
            default=0.0,
        )

        critical_failures = _number(
            data,
            "critical_failures",
            default=0.0,
        )

        failure_risk = _clamp(
            failures / 10.0
        )

        critical_risk = _clamp(
            critical_failures / 3.0
        )

        return max(
            failure_risk,
            critical_risk,
        )

    # ========================================================
    # TRANSMISSION LOADING
    # ========================================================

    @staticmethod
    def _transmission_loading_risk(
        data: Mapping[str, Any],
    ) -> float:
        """Estimate transmission-line overload risk."""

        explicit = _number(
            data,
            "transmission_loading_risk",
            "line_loading_risk",
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
            "line_loading_percent",
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
    # TRANSFORMER LOADING
    # ========================================================

    @staticmethod
    def _transformer_loading_risk(
        data: Mapping[str, Any],
    ) -> float:
        """Estimate transformer overload risk."""

        explicit = _number(
            data,
            "transformer_loading_risk",
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
        """Estimate generator stress risk."""

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
            "generator_loading_percent",
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
    # LOAD STRESS
    # ========================================================

    @staticmethod
    def _load_stress_risk(
        data: Mapping[str, Any],
    ) -> float:
        """Estimate load-related stress."""

        explicit = _number(
            data,
            "load_stress_risk",
            "load_risk",
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
            "generation_mw",
            "available_generation_mw",
            "available_power_mw",
            default=-1.0,
        )

        if demand < 0.0:
            return 0.0

        if generation <= 0.0:
            return (
                1.0
                if demand > 0.0
                else 0.0
            )

        ratio = (
            demand
            / generation
        )

        if ratio <= 0.70:
            return 0.0

        if ratio >= 1.05:
            return 1.0

        return _clamp(
            (
                ratio
                - 0.70
            )
            / 0.35
        )

    # ========================================================
    # CONNECTIVITY
    # ========================================================

    @staticmethod
    def _connectivity_risk(
        data: Mapping[str, Any],
    ) -> float:
        """
        Estimate risk from network connectivity loss.

        Higher disconnected fractions produce higher risk.
        """

        explicit = _number(
            data,
            "connectivity_risk",
            "network_connectivity_risk",
            default=-1.0,
        )

        if explicit >= 0.0:
            return _clamp(
                explicit
            )

        disconnected = _number(
            data,
            "disconnected_assets",
            "isolated_assets",
            "disconnected_buses",
            default=0.0,
        )

        total = _number(
            data,
            "total_assets",
            "total_buses",
            "total_nodes",
            default=-1.0,
        )

        if total > 0.0:
            return _clamp(
                disconnected
                / total
                / 0.20
            )

        return _clamp(
            disconnected
            / 10.0
        )

    # ========================================================
    # REDUNDANCY
    # ========================================================

    @staticmethod
    def _redundancy_risk(
        data: Mapping[str, Any],
    ) -> float:
        """
        Estimate risk caused by insufficient redundancy.

        A low redundancy value means high risk.
        """

        explicit = _number(
            data,
            "redundancy_risk",
            default=-1.0,
        )

        if explicit >= 0.0:
            return _clamp(
                explicit
            )

        redundancy = _number(
            data,
            "redundancy_ratio",
            "network_redundancy",
            "reserve_redundancy",
            default=-1.0,
        )

        if redundancy < 0.0:
            return 0.0

        if redundancy > 2.0:
            redundancy /= 100.0

        redundancy = _clamp(
            redundancy
        )

        return 1.0 - redundancy

    # ========================================================
    # OUTAGES
    # ========================================================

    @staticmethod
    def _outage_risk(
        data: Mapping[str, Any],
    ) -> float:
        """Estimate risk caused by existing outages."""

        explicit = _number(
            data,
            "outage_risk",
            default=-1.0,
        )

        if explicit >= 0.0:
            return _clamp(
                explicit
            )

        outages = _number(
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

        outage_risk = _clamp(
            outages / 10.0
        )

        critical_risk = _clamp(
            critical_outages / 3.0
        )

        return max(
            outage_risk,
            critical_risk,
        )

    # ========================================================
    # FREQUENCY
    # ========================================================

    @staticmethod
    def _frequency_risk(
        data: Mapping[str, Any],
    ) -> float:
        """Estimate risk caused by frequency instability."""

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
            "frequency_deviation_hz",
            "frequency_deviation",
            default=-1.0,
        )

        if deviation >= 0.0:
            deviation = abs(
                deviation
            )

        else:
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
        """Estimate voltage instability risk."""

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
    # CONTINGENCY
    # ========================================================

    @staticmethod
    def _contingency_risk(
        data: Mapping[str, Any],
    ) -> float:
        """
        Estimate risk from simultaneous or expected contingencies.
        """

        explicit = _number(
            data,
            "contingency_risk",
            "contingency_score",
            default=-1.0,
        )

        if explicit >= 0.0:
            return _clamp(
                explicit
            )

        contingencies = _number(
            data,
            "contingency_count",
            "simultaneous_failures",
            "expected_failures",
            default=0.0,
        )

        return _clamp(
            contingencies
            / 5.0
        )

    # ========================================================
    # PREDICTION
    # ========================================================

    def predict(
        self,
        data: Mapping[str, Any],
    ) -> CascadePrediction:
        """
        Predict cascade risk from raw grid information.
        """

        if not isinstance(
            data,
            Mapping,
        ):
            raise TypeError(
                "Cascade input must be a mapping."
            )

        features = self.build_features(
            data
        )

        return self.predict_from_features(
            features,
            data=data,
        )

    def predict_from_features(
        self,
        features: CascadeFeatures,
        *,
        data: Mapping[str, Any] | None = None,
    ) -> CascadePrediction:
        """
        Predict cascade risk from normalized features.
        """

        score = (
            features.initial_failure_risk
            * self.config.initial_failure_weight
            + features.transmission_loading_risk
            * self.config.transmission_loading_weight
            + features.transformer_loading_risk
            * self.config.transformer_loading_weight
            + features.generator_stress_risk
            * self.config.generator_stress_weight
            + features.load_stress_risk
            * self.config.load_stress_weight
            + features.connectivity_risk
            * self.config.connectivity_weight
            + features.redundancy_risk
            * self.config.redundancy_weight
            + features.outage_risk
            * self.config.outage_weight
            + features.frequency_risk
            * self.config.frequency_weight
            + features.voltage_risk
            * self.config.voltage_weight
            + features.contingency_risk
            * self.config.contingency_weight
        )

        score = _clamp(
            score
        )

        propagation_factor = (
            self._propagation_factor(
                features
            )
        )

        # Simultaneous high-risk factors can amplify cascade
        # potential.
        score = _clamp(
            score
            + propagation_factor
            * 0.15
        )

        risk_level = self.classify_risk(
            score
        )

        state = self.classify_state(
            score,
            features,
        )

        cascade_probability = (
            self._estimate_probability(
                score
            )
        )

        confidence = (
            self._estimate_confidence(
                features
            )
        )

        affected_assets = (
            self._estimate_affected_assets(
                score,
                features,
                data,
            )
        )

        contributing_factors = (
            self._get_contributing_factors(
                features
            )
        )

        return CascadePrediction(
            cascade_score=round(
                score,
                4,
            ),
            cascade_probability=round(
                cascade_probability,
                4,
            ),
            risk_level=risk_level,
            state=state,
            confidence=round(
                confidence,
                4,
            ),
            estimated_affected_assets=(
                affected_assets
            ),
            propagation_factor=round(
                propagation_factor,
                4,
            ),
            contributing_factors=(
                contributing_factors
            ),
            features=features,
            metadata={
                "model_type": (
                    "weighted_cascade_risk_baseline"
                ),
                "model_version": "1.0",
                "trained": False,
                "probability_calibrated": False,
            },
        )

    # ========================================================
    # PROPAGATION
    # ========================================================

    @staticmethod
    def _propagation_factor(
        features: CascadeFeatures,
    ) -> float:
        """
        Estimate how strongly failures could propagate.

        Propagation is more concerning when multiple network
        stress factors are simultaneously elevated.
        """

        risks = [
            features.transmission_loading_risk,
            features.transformer_loading_risk,
            features.generator_stress_risk,
            features.load_stress_risk,
            features.connectivity_risk,
            features.redundancy_risk,
            features.outage_risk,
        ]

        high_count = sum(
            1
            for risk in risks
            if risk >= 0.60
        )

        extreme_count = sum(
            1
            for risk in risks
            if risk >= 0.85
        )

        if high_count <= 1:
            factor = 0.0

        elif high_count == 2:
            factor = 0.15

        elif high_count == 3:
            factor = 0.30

        elif high_count == 4:
            factor = 0.50

        else:
            factor = 0.70

        factor += (
            extreme_count
            * 0.08
        )

        return _clamp(
            factor
        )

    # ========================================================
    # PROBABILITY
    # ========================================================

    @staticmethod
    def _estimate_probability(
        score: float,
    ) -> float:
        """
        Convert cascade score to a probability-like estimate.

        This is NOT a statistically calibrated probability.
        """

        score = _clamp(
            score
        )

        return _clamp(
            score ** 1.30
        )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    @staticmethod
    def _estimate_confidence(
        features: CascadeFeatures,
    ) -> float:
        """
        Estimate information coverage.

        This is not a model-accuracy measurement.
        """

        values = [
            features.initial_failure_risk,
            features.transmission_loading_risk,
            features.transformer_loading_risk,
            features.generator_stress_risk,
            features.load_stress_risk,
            features.connectivity_risk,
            features.redundancy_risk,
            features.outage_risk,
            features.frequency_risk,
            features.voltage_risk,
            features.contingency_risk,
        ]

        informative = sum(
            1
            for value in values
            if value != 0.0
        )

        return _clamp(
            0.35
            + (
                informative
                / len(values)
            )
            * 0.65
        )

    # ========================================================
    # AFFECTED ASSETS
    # ========================================================

    @staticmethod
    def _estimate_affected_assets(
        score: float,
        features: CascadeFeatures,
        data: Mapping[str, Any] | None,
    ) -> int:
        """
        Estimate the number of potentially affected assets.

        If a caller supplies an explicit estimate, it is respected.
        Otherwise the value is a conservative model-derived estimate.
        """

        if data is not None:
            explicit = _number(
                data,
                "estimated_affected_assets",
                "potentially_affected_assets",
                default=-1.0,
            )

            if explicit >= 0.0:
                return max(
                    0,
                    int(
                        round(
                            explicit
                        )
                    ),
                )

            total_assets = _number(
                data,
                "total_assets",
                "monitored_assets",
                default=-1.0,
            )

        else:
            total_assets = -1.0

        stress_factor = max(
            features.connectivity_risk,
            features.transmission_loading_risk,
            features.outage_risk,
            features.contingency_risk,
        )

        affected_fraction = _clamp(
            score
            * 0.30
            + stress_factor
            * 0.20
        )

        if total_assets > 0.0:
            estimate = int(
                round(
                    total_assets
                    * affected_fraction
                )
            )

            return max(
                0,
                estimate,
            )

        return max(
            0,
            int(
                round(
                    affected_fraction
                    * 20.0
                )
            ),
        )

    # ========================================================
    # RISK CLASSIFICATION
    # ========================================================

    @staticmethod
    def classify_risk(
        score: float,
    ) -> CascadeRiskLevel:
        """
        Convert cascade score into a risk level.
        """

        score = _clamp(
            score
        )

        if score >= 0.80:
            return CascadeRiskLevel.CRITICAL

        if score >= 0.60:
            return CascadeRiskLevel.HIGH

        if score >= 0.40:
            return CascadeRiskLevel.MEDIUM

        if score >= 0.20:
            return CascadeRiskLevel.LOW

        return CascadeRiskLevel.VERY_LOW

    # ========================================================
    # STATE CLASSIFICATION
    # ========================================================

    @staticmethod
    def classify_state(
        score: float,
        features: CascadeFeatures,
    ) -> CascadeState:
        """
        Classify the current cascade state.
        """

        if (
            score >= 0.80
            or features.cascading_condition()
        ):
            return CascadeState.CRITICAL

        if (
            features.initial_failure_risk >= 0.60
            and (
                features.transmission_loading_risk
                >= 0.60
                or features.transformer_loading_risk
                >= 0.60
                or features.connectivity_risk
                >= 0.60
            )
        ):
            return CascadeState.PROPAGATING

        if score >= 0.40:
            return CascadeState.STRESSED

        return CascadeState.STABLE

    # ========================================================
    # CONTRIBUTING FACTORS
    # ========================================================

    @staticmethod
    def _get_contributing_factors(
        features: CascadeFeatures,
    ) -> list[str]:
        """
        Return the major contributors to cascade risk.
        """

        factors = [
            (
                "initial_failures",
                features.initial_failure_risk,
            ),
            (
                "transmission_overloading",
                features.transmission_loading_risk,
            ),
            (
                "transformer_overloading",
                features.transformer_loading_risk,
            ),
            (
                "generator_stress",
                features.generator_stress_risk,
            ),
            (
                "load_stress",
                features.load_stress_risk,
            ),
            (
                "network_connectivity",
                features.connectivity_risk,
            ),
            (
                "low_redundancy",
                features.redundancy_risk,
            ),
            (
                "existing_outages",
                features.outage_risk,
            ),
            (
                "frequency_instability",
                features.frequency_risk,
            ),
            (
                "voltage_instability",
                features.voltage_risk,
            ),
            (
                "contingencies",
                features.contingency_risk,
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
                "Cascade Risk Model"
            ),
            "model_type": (
                "weighted_cascade_risk_baseline"
            ),
            "version": "1.0",
            "trained": False,
            "probability_calibrated": False,
            "weights": {
                "initial_failure": (
                    self.config.initial_failure_weight
                ),
                "transmission_loading": (
                    self.config.transmission_loading_weight
                ),
                "transformer_loading": (
                    self.config.transformer_loading_weight
                ),
                "generator_stress": (
                    self.config.generator_stress_weight
                ),
                "load_stress": (
                    self.config.load_stress_weight
                ),
                "connectivity": (
                    self.config.connectivity_weight
                ),
                "redundancy": (
                    self.config.redundancy_weight
                ),
                "outage": (
                    self.config.outage_weight
                ),
                "frequency": (
                    self.config.frequency_weight
                ),
                "voltage": (
                    self.config.voltage_weight
                ),
                "contingency": (
                    self.config.contingency_weight
                ),
            },
        }


# ============================================================
# FEATURE EXTENSION
# ============================================================


def _cascade_condition(
    features: CascadeFeatures,
) -> bool:
    """
    Determine whether multiple severe propagation factors are
    simultaneously present.
    """

    severe = [
        features.transmission_loading_risk,
        features.transformer_loading_risk,
        features.generator_stress_risk,
        features.connectivity_risk,
        features.redundancy_risk,
        features.outage_risk,
    ]

    return sum(
        1
        for value in severe
        if value >= 0.80
    ) >= 3


# Attach a small compatibility helper to the feature class.
# This keeps the main dataclass clean while allowing
# classify_state() to perform the combined check.
def _features_cascading_condition(
    self: CascadeFeatures,
) -> bool:
    """Return True when severe cascade conditions coexist."""

    return _cascade_condition(
        self
    )


CascadeFeatures.cascading_condition = (
    _features_cascading_condition
)  # type: ignore[attr-defined]


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def predict_cascade_risk(
    data: Mapping[str, Any],
    *,
    config: CascadeModelConfig | None = None,
) -> CascadePrediction:
    """
    Convenience function for cascade-risk prediction.
    """

    model = CascadeModel(
        config=config
    )

    return model.predict(
        data
    )


def classify_cascade_risk(
    score: float,
) -> CascadeRiskLevel:
    """
    Convenience function for cascade-risk classification.
    """

    return CascadeModel.classify_risk(
        score
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "CascadeRiskLevel",
    "CascadeState",
    "CascadeModelConfig",
    "CascadeFeatures",
    "CascadePrediction",
    "CascadeModel",
    "predict_cascade_risk",
    "classify_cascade_risk",
]