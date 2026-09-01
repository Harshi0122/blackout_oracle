"""
Blackout Oracle - Risk Engine.

Central risk-assessment engine for the Blackout Oracle system.

The risk engine combines signals from:

- Electrical measurements
- Asset health
- Weather
- Grid topology
- Anomaly detection
- Forecasting
- Historical incidents
- Blackout-risk models
- Cascade-risk models

It produces a normalized 0-100 risk score, probability,
confidence, risk level, contributing factors, and recommended
actions.

This module is intentionally dependency-light. External ML
models and database repositories can be connected through the
input dictionaries without creating circular dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from app.risk.calibration import (
    CalibrationConfig,
    CalibratedRisk,
    RiskCalibrator,
    RiskLevel,
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_WEIGHT_ELECTRICAL = 0.25
DEFAULT_WEIGHT_ASSET = 0.20
DEFAULT_WEIGHT_WEATHER = 0.10
DEFAULT_WEIGHT_ANOMALY = 0.15
DEFAULT_WEIGHT_BLACKOUT = 0.15
DEFAULT_WEIGHT_CASCADE = 0.10
DEFAULT_WEIGHT_FORECAST = 0.05

DEFAULT_ALERT_THRESHOLD = 75.0
DEFAULT_CRITICAL_THRESHOLD = 90.0

MIN_SCORE = 0.0
MAX_SCORE = 100.0


# ============================================================
# DATA TYPES
# ============================================================


@dataclass
class RiskWeights:
    """
    Relative importance of individual risk contributors.

    The engine automatically normalizes the weights so their sum
    does not have to be exactly 1.0.
    """

    electrical: float = DEFAULT_WEIGHT_ELECTRICAL

    asset: float = DEFAULT_WEIGHT_ASSET

    weather: float = DEFAULT_WEIGHT_WEATHER

    anomaly: float = DEFAULT_WEIGHT_ANOMALY

    blackout: float = DEFAULT_WEIGHT_BLACKOUT

    cascade: float = DEFAULT_WEIGHT_CASCADE

    forecast: float = DEFAULT_WEIGHT_FORECAST

    def __post_init__(self) -> None:
        """Validate risk weights."""

        values = {
            "electrical": self.electrical,
            "asset": self.asset,
            "weather": self.weather,
            "anomaly": self.anomaly,
            "blackout": self.blackout,
            "cascade": self.cascade,
            "forecast": self.forecast,
        }

        for name, value in values.items():
            if value < 0.0:
                raise ValueError(
                    f"{name} weight cannot be negative."
                )

        if sum(values.values()) <= 0.0:
            raise ValueError(
                "At least one risk weight must be greater than zero."
            )

    def normalized(self) -> dict[str, float]:
        """Return weights normalized to sum to 1."""

        values = {
            "electrical": self.electrical,
            "asset": self.asset,
            "weather": self.weather,
            "anomaly": self.anomaly,
            "blackout": self.blackout,
            "cascade": self.cascade,
            "forecast": self.forecast,
        }

        total = sum(values.values())

        return {
            name: value / total
            for name, value in values.items()
        }

    def to_dict(self) -> dict[str, float]:
        """Return raw configured weights."""

        return {
            "electrical": self.electrical,
            "asset": self.asset,
            "weather": self.weather,
            "anomaly": self.anomaly,
            "blackout": self.blackout,
            "cascade": self.cascade,
            "forecast": self.forecast,
        }


@dataclass
class RiskFactor:
    """
    Represents one contributor to the overall grid risk.
    """

    name: str

    score: float

    weight: float

    contribution: float

    severity: str

    explanation: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert the risk factor to a dictionary."""

        return {
            "name": self.name,
            "score": self.score,
            "weight": self.weight,
            "contribution": self.contribution,
            "severity": self.severity,
            "explanation": self.explanation,
            "metadata": dict(self.metadata),
        }


@dataclass
class RiskAssessment:
    """
    Complete result of a Blackout Oracle risk assessment.
    """

    score: float

    probability: float

    confidence: float

    risk_level: str

    alert_required: bool

    critical: bool

    factors: list[RiskFactor] = field(
        default_factory=list
    )

    recommendations: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def top_factor(self) -> RiskFactor | None:
        """Return the strongest risk contributor."""

        if not self.factors:
            return None

        return max(
            self.factors,
            key=lambda factor: factor.contribution,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the assessment to a dictionary."""

        return {
            "score": self.score,
            "probability": self.probability,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "alert_required": self.alert_required,
            "critical": self.critical,
            "factors": [
                factor.to_dict()
                for factor in self.factors
            ],
            "recommendations": list(
                self.recommendations
            ),
            "metadata": dict(self.metadata),
        }


# ============================================================
# HELPERS
# ============================================================


def _clamp(
    value: float,
    minimum: float = MIN_SCORE,
    maximum: float = MAX_SCORE,
) -> float:
    """Clamp a value to a range."""

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def _to_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Convert a value to a finite float."""

    try:
        numeric = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default

    if not (
        numeric == numeric
    ):
        return default

    if numeric in (
        float("inf"),
        float("-inf"),
    ):
        return default

    return numeric


def _percentage_score(
    value: Any,
) -> float:
    """
    Convert a value expected to be either 0-1 or 0-100 into
    a 0-100 risk score.
    """

    numeric = _to_float(value)

    if 0.0 <= numeric <= 1.0:
        numeric *= 100.0

    return _clamp(numeric)


def _severity_from_score(
    score: float,
) -> str:
    """Convert a 0-100 score into a severity label."""

    if score >= 90.0:
        return RiskLevel.CRITICAL

    if score >= 75.0:
        return RiskLevel.HIGH

    if score >= 50.0:
        return RiskLevel.MEDIUM

    if score >= 25.0:
        return RiskLevel.LOW

    return RiskLevel.VERY_LOW


# ============================================================
# RISK ENGINE
# ============================================================


class RiskEngine:
    """
    Central grid-risk calculation engine.

    The engine is designed to accept outputs from multiple
    upstream systems and combine them into one operational risk
    assessment.
    """

    def __init__(
        self,
        *,
        weights: RiskWeights | None = None,
        calibrator: RiskCalibrator | None = None,
        calibration_config: CalibrationConfig | None = None,
        alert_threshold: float = DEFAULT_ALERT_THRESHOLD,
        critical_threshold: float = DEFAULT_CRITICAL_THRESHOLD,
    ) -> None:
        """Initialize the risk engine."""

        self.weights = (
            weights
            if weights is not None
            else RiskWeights()
        )

        self.calibrator = (
            calibrator
            if calibrator is not None
            else RiskCalibrator(
                config=calibration_config
            )
        )

        self.alert_threshold = _clamp(
            float(alert_threshold)
        )

        self.critical_threshold = _clamp(
            float(critical_threshold)
        )

        if (
            self.critical_threshold
            < self.alert_threshold
        ):
            raise ValueError(
                "critical_threshold must be greater "
                "than or equal to alert_threshold."
            )

    # ========================================================
    # MAIN ASSESSMENT
    # ========================================================

    def assess(
        self,
        *,
        electrical: Mapping[str, Any] | float | None = None,
        asset: Mapping[str, Any] | float | None = None,
        weather: Mapping[str, Any] | float | None = None,
        anomaly: Mapping[str, Any] | float | None = None,
        blackout: Mapping[str, Any] | float | None = None,
        cascade: Mapping[str, Any] | float | None = None,
        forecast: Mapping[str, Any] | float | None = None,
        region: str | None = None,
        substation: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> RiskAssessment:
        """
        Calculate overall grid risk.

        Each contributor can be supplied either as:

            0-100 score

        or:

            dictionary containing a score/probability field.

        Example:

            electrical={
                "frequency_score": 70,
                "voltage_score": 60,
                "loading_score": 80,
            }
        """

        factor_inputs = {
            "electrical": electrical,
            "asset": asset,
            "weather": weather,
            "anomaly": anomaly,
            "blackout": blackout,
            "cascade": cascade,
            "forecast": forecast,
        }

        normalized_weights = (
            self.weights.normalized()
        )

        factors: list[
            RiskFactor
        ] = []

        for name, source in factor_inputs.items():
            score = self._extract_factor_score(
                source
            )

            weight = normalized_weights[
                name
            ]

            contribution = (
                score * weight
            )

            factors.append(
                RiskFactor(
                    name=name,
                    score=round(
                        score,
                        4,
                    ),
                    weight=round(
                        weight,
                        6,
                    ),
                    contribution=round(
                        contribution,
                        4,
                    ),
                    severity=_severity_from_score(
                        score
                    ),
                    explanation=self._factor_explanation(
                        name,
                        score,
                    ),
                )
            )

        raw_score = sum(
            factor.contribution
            for factor in factors
        )

        calibrated = self.calibrator.calibrate(
            raw_score
        )

        recommendations = (
            self.generate_recommendations(
                factors,
                calibrated,
            )
        )

        return RiskAssessment(
            score=round(
                calibrated.calibrated_score,
                4,
            ),
            probability=round(
                calibrated.probability,
                6,
            ),
            confidence=round(
                calibrated.confidence,
                6,
            ),
            risk_level=self._risk_level_for_engine(
                calibrated.calibrated_score
            ),
            alert_required=(
                calibrated.calibrated_score
                >= self.alert_threshold
            ),
            critical=(
                calibrated.calibrated_score
                >= self.critical_threshold
            ),
            factors=sorted(
                factors,
                key=lambda factor: factor.contribution,
                reverse=True,
            ),
            recommendations=recommendations,
            metadata={
                **dict(metadata or {}),
                "region": region,
                "substation": substation,
                "engine": "RiskEngine",
                "version": "1.0",
                "weights": normalized_weights,
            },
        )

    # ========================================================
    # FACTOR SCORE EXTRACTION
    # ========================================================

    @staticmethod
    def _extract_factor_score(
        source: Mapping[str, Any] | float | None,
    ) -> float:
        """
        Extract a 0-100 risk score from a contributor.

        Recognized dictionary fields include:

            score
            risk_score
            probability
            risk_probability
            severity
            value

        If multiple fields exist, score/risk_score take priority.
        """

        if source is None:
            return 0.0

        if isinstance(
            source,
            Mapping,
        ):
            for key in (
                "score",
                "risk_score",
                "risk",
                "risk_value",
            ):
                if key in source:
                    return _percentage_score(
                        source[key]
                    )

            for key in (
                "probability",
                "risk_probability",
                "blackout_probability",
                "cascade_probability",
                "failure_probability",
            ):
                if key in source:
                    return _percentage_score(
                        source[key]
                    )

            if "severity" in source:
                severity = str(
                    source["severity"]
                ).lower()

                severity_map = {
                    "very_low": 10.0,
                    "low": 30.0,
                    "medium": 55.0,
                    "high": 80.0,
                    "critical": 95.0,
                }

                if severity in severity_map:
                    return severity_map[
                        severity
                    ]

            if "value" in source:
                return _percentage_score(
                    source["value"]
                )

            return 0.0

        return _percentage_score(
            source
        )

    # ========================================================
    # FACTOR EXPLANATIONS
    # ========================================================

    @staticmethod
    def _factor_explanation(
        name: str,
        score: float,
    ) -> str:
        """Generate a human-readable factor explanation."""

        if score >= 90.0:
            severity = "critical"

        elif score >= 75.0:
            severity = "high"

        elif score >= 50.0:
            severity = "moderate"

        elif score >= 25.0:
            severity = "low"

        else:
            severity = "minimal"

        explanations = {
            "electrical": (
                "Electrical operating conditions indicate "
                f"{severity} grid stress."
            ),
            "asset": (
                "Asset-health indicators indicate "
                f"{severity} equipment risk."
            ),
            "weather": (
                "Weather-related conditions indicate "
                f"{severity} environmental risk."
            ),
            "anomaly": (
                "Detected anomalies indicate "
                f"{severity} deviation from expected behavior."
            ),
            "blackout": (
                "Blackout prediction indicates "
                f"{severity} outage risk."
            ),
            "cascade": (
                "Cascading-failure analysis indicates "
                f"{severity} propagation risk."
            ),
            "forecast": (
                "Forecasted grid conditions indicate "
                f"{severity} future stress."
            ),
        }

        return explanations.get(
            name,
            f"{name} contributes {severity} risk.",
        )

    # ========================================================
    # ENGINE RISK LEVEL
    # ========================================================

    def _risk_level_for_engine(
        self,
        score: float,
    ) -> str:
        """Map score using engine-specific thresholds."""

        if score >= self.critical_threshold:
            return RiskLevel.CRITICAL

        if score >= self.alert_threshold:
            return RiskLevel.HIGH

        if score >= 50.0:
            return RiskLevel.MEDIUM

        if score >= 25.0:
            return RiskLevel.LOW

        return RiskLevel.VERY_LOW

    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    def generate_recommendations(
        self,
        factors: Sequence[RiskFactor],
        calibrated: CalibratedRisk,
    ) -> list[str]:
        """
        Generate operational recommendations based on risk
        contributors.

        These are decision-support recommendations, not automatic
        control commands.
        """

        recommendations: list[
            str
        ] = []

        for factor in factors:
            if factor.score < 50.0:
                continue

            if factor.name == "electrical":
                recommendations.append(
                    "Inspect voltage, frequency, loading, "
                    "and reactive-power conditions."
                )

            elif factor.name == "asset":
                recommendations.append(
                    "Inspect high-risk transformers, lines, "
                    "and other critical assets."
                )

            elif factor.name == "weather":
                recommendations.append(
                    "Review weather exposure and prepare "
                    "for weather-related grid stress."
                )

            elif factor.name == "anomaly":
                recommendations.append(
                    "Investigate anomalous telemetry and "
                    "verify sensor/data quality."
                )

            elif factor.name == "blackout":
                recommendations.append(
                    "Review blackout-risk drivers and "
                    "prepare appropriate contingency actions."
                )

            elif factor.name == "cascade":
                recommendations.append(
                    "Review vulnerable network paths and "
                    "simulate potential cascading failures."
                )

            elif factor.name == "forecast":
                recommendations.append(
                    "Review upcoming demand/generation "
                    "conditions and expected grid loading."
                )

        if calibrated.calibrated_score >= self.critical_threshold:
            recommendations.insert(
                0,
                "CRITICAL: Escalate the assessment to "
                "qualified grid operations personnel "
                "for immediate review.",
            )

        elif calibrated.calibrated_score >= self.alert_threshold:
            recommendations.insert(
                0,
                "HIGH RISK: Increase operational monitoring "
                "and review contingency readiness.",
            )

        if not recommendations:
            recommendations.append(
                "Continue normal grid monitoring."
            )

        return list(
            dict.fromkeys(
                recommendations
            )
        )

    # ========================================================
    # SIMPLE SCORE
    # ========================================================

    def score(
        self,
        **kwargs: Any,
    ) -> float:
        """
        Return only the overall risk score.
        """

        return self.assess(
            **kwargs
        ).score

    # ========================================================
    # PROBABILITY
    # ========================================================

    def probability(
        self,
        **kwargs: Any,
    ) -> float:
        """
        Return only the calibrated risk probability.
        """

        return self.assess(
            **kwargs
        ).probability

    # ========================================================
    # ALERT CHECK
    # ========================================================

    def requires_alert(
        self,
        **kwargs: Any,
    ) -> bool:
        """Return whether the calculated risk requires an alert."""

        return self.assess(
            **kwargs
        ).alert_required

    # ========================================================
    # CRITICAL CHECK
    # ========================================================

    def is_critical(
        self,
        **kwargs: Any,
    ) -> bool:
        """Return whether the calculated risk is critical."""

        return self.assess(
            **kwargs
        ).critical

    # ========================================================
    # FACTOR ASSESSMENT
    # ========================================================

    def assess_factor(
        self,
        name: str,
        value: Mapping[str, Any] | float,
    ) -> RiskFactor:
        """
        Assess one risk factor independently.
        """

        normalized_weights = (
            self.weights.normalized()
        )

        if name not in normalized_weights:
            raise ValueError(
                f"Unknown risk factor: {name}"
            )

        score = self._extract_factor_score(
            value
        )

        weight = normalized_weights[
            name
        ]

        contribution = (
            score * weight
        )

        return RiskFactor(
            name=name,
            score=round(
                score,
                4,
            ),
            weight=round(
                weight,
                6,
            ),
            contribution=round(
                contribution,
                4,
            ),
            severity=_severity_from_score(
                score
            ),
            explanation=self._factor_explanation(
                name,
                score,
            ),
        )

    # ========================================================
    # BATCH ASSESSMENT
    # ========================================================

    def assess_many(
        self,
        assessments: Sequence[
            Mapping[str, Any]
        ],
    ) -> list[RiskAssessment]:
        """
        Assess multiple grid-risk records.
        """

        results: list[
            RiskAssessment
        ] = []

        for item in assessments:
            results.append(
                self.assess(
                    **dict(item)
                )
            )

        return results

    # ========================================================
    # REGION ASSESSMENT
    # ========================================================

    def assess_region(
        self,
        region: str,
        *,
        electrical: Mapping[str, Any] | float | None = None,
        asset: Mapping[str, Any] | float | None = None,
        weather: Mapping[str, Any] | float | None = None,
        anomaly: Mapping[str, Any] | float | None = None,
        blackout: Mapping[str, Any] | float | None = None,
        cascade: Mapping[str, Any] | float | None = None,
        forecast: Mapping[str, Any] | float | None = None,
    ) -> RiskAssessment:
        """
        Assess risk for a named grid region.
        """

        if not region:
            raise ValueError(
                "region cannot be empty."
            )

        return self.assess(
            electrical=electrical,
            asset=asset,
            weather=weather,
            anomaly=anomaly,
            blackout=blackout,
            cascade=cascade,
            forecast=forecast,
            region=region,
        )

    # ========================================================
    # SUBSTATION ASSESSMENT
    # ========================================================

    def assess_substation(
        self,
        substation: str,
        *,
        electrical: Mapping[str, Any] | float | None = None,
        asset: Mapping[str, Any] | float | None = None,
        weather: Mapping[str, Any] | float | None = None,
        anomaly: Mapping[str, Any] | float | None = None,
        blackout: Mapping[str, Any] | float | None = None,
        cascade: Mapping[str, Any] | float | None = None,
        forecast: Mapping[str, Any] | float | None = None,
    ) -> RiskAssessment:
        """
        Assess risk for a named substation.
        """

        if not substation:
            raise ValueError(
                "substation cannot be empty."
            )

        return self.assess(
            electrical=electrical,
            asset=asset,
            weather=weather,
            anomaly=anomaly,
            blackout=blackout,
            cascade=cascade,
            forecast=forecast,
            substation=substation,
        )

    # ========================================================
    # ENGINE INFORMATION
    # ========================================================

    def model_info(
        self,
    ) -> dict[str, Any]:
        """Return information about the risk engine."""

        return {
            "engine": "RiskEngine",
            "version": "1.0",
            "alert_threshold": self.alert_threshold,
            "critical_threshold": self.critical_threshold,
            "weights": self.weights.to_dict(),
            "normalized_weights": (
                self.weights.normalized()
            ),
            "calibration": (
                self.calibrator.model_info()
            ),
        }


# ============================================================
# DEFAULT GLOBAL ENGINE
# ============================================================


_default_engine = RiskEngine()


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def assess_risk(
    **kwargs: Any,
) -> RiskAssessment:
    """
    Assess grid risk using the default risk engine.
    """

    return _default_engine.assess(
        **kwargs
    )


def calculate_risk_score(
    **kwargs: Any,
) -> float:
    """
    Calculate only the overall risk score.
    """

    return _default_engine.score(
        **kwargs
    )


def calculate_risk_probability(
    **kwargs: Any,
) -> float:
    """
    Calculate only the overall risk probability.
    """

    return _default_engine.probability(
        **kwargs
    )


def risk_requires_alert(
    **kwargs: Any,
) -> bool:
    """
    Determine whether a risk alert is required.
    """

    return _default_engine.requires_alert(
        **kwargs
    )


def get_risk_engine() -> RiskEngine:
    """
    Return the default global risk engine.
    """

    return _default_engine


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "RiskWeights",
    "RiskFactor",
    "RiskAssessment",
    "RiskEngine",
    "assess_risk",
    "calculate_risk_score",
    "calculate_risk_probability",
    "risk_requires_alert",
    "get_risk_engine",
]