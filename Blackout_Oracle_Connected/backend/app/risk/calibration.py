"""
Blackout Oracle - Risk Calibration.

Utilities for calibrating raw risk scores and probabilities
produced by the ML and grid-risk layers.

The calibration layer provides:

- Risk-score normalization
- Probability calibration
- Temperature scaling
- Platt-style logistic calibration
- Reliability analysis
- Risk-level mapping
- Threshold calibration
- Calibration metrics
- Calibration summaries

This module is dependency-free and does not require NumPy,
pandas, or scikit-learn.

Important:
Calibration parameters should ideally be fitted using a
historical validation dataset and then applied to unseen data.
The default calibrator provides safe deterministic behavior
when no historical calibration data is available.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence


# ============================================================
# CONSTANTS
# ============================================================

EPSILON = 1e-12

DEFAULT_MIN_SCORE = 0.0
DEFAULT_MAX_SCORE = 100.0

DEFAULT_LOW_THRESHOLD = 25.0
DEFAULT_MEDIUM_THRESHOLD = 50.0
DEFAULT_HIGH_THRESHOLD = 75.0

DEFAULT_PROBABILITY_THRESHOLD = 0.5


# ============================================================
# HELPERS
# ============================================================


def _to_float(
    value: Any,
    name: str = "value",
) -> float:
    """Convert a value to a finite float."""

    try:
        numeric = float(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            f"{name} must be numeric."
        ) from exc

    if not math.isfinite(numeric):
        raise ValueError(
            f"{name} must be finite."
        )

    return numeric


def _clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """Clamp a value to a specified range."""

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def _safe_divide(
    numerator: float,
    denominator: float,
) -> float:
    """Perform division safely."""

    if abs(denominator) <= EPSILON:
        return 0.0

    return numerator / denominator


def _sigmoid(
    value: float,
) -> float:
    """Numerically stable sigmoid function."""

    if value >= 0.0:
        exponent = math.exp(
            -value
        )

        return 1.0 / (
            1.0 + exponent
        )

    exponent = math.exp(
        value
    )

    return exponent / (
        1.0 + exponent
    )


def _logit(
    probability: float,
) -> float:
    """Convert probability to log-odds."""

    probability = _clamp(
        probability,
        EPSILON,
        1.0 - EPSILON,
    )

    return math.log(
        probability
        / (
            1.0
            - probability
        )
    )


# ============================================================
# RISK LEVELS
# ============================================================


class RiskLevel:
    """Standard Blackout Oracle risk levels."""

    VERY_LOW = "very_low"

    LOW = "low"

    MEDIUM = "medium"

    HIGH = "high"

    CRITICAL = "critical"


RISK_LEVELS = (
    RiskLevel.VERY_LOW,
    RiskLevel.LOW,
    RiskLevel.MEDIUM,
    RiskLevel.HIGH,
    RiskLevel.CRITICAL,
)


# ============================================================
# CALIBRATION CONFIGURATION
# ============================================================


@dataclass
class CalibrationConfig:
    """
    Configuration for risk-score calibration.
    """

    min_score: float = DEFAULT_MIN_SCORE

    max_score: float = DEFAULT_MAX_SCORE

    low_threshold: float = DEFAULT_LOW_THRESHOLD

    medium_threshold: float = DEFAULT_MEDIUM_THRESHOLD

    high_threshold: float = DEFAULT_HIGH_THRESHOLD

    critical_threshold: float = 90.0

    probability_temperature: float = 1.0

    probability_threshold: float = (
        DEFAULT_PROBABILITY_THRESHOLD
    )

    def __post_init__(self) -> None:
        """Validate calibration configuration."""

        self.min_score = _to_float(
            self.min_score,
            "min_score",
        )

        self.max_score = _to_float(
            self.max_score,
            "max_score",
        )

        if (
            self.max_score
            <= self.min_score
        ):
            raise ValueError(
                "max_score must be greater "
                "than min_score."
            )

        thresholds = [
            self.low_threshold,
            self.medium_threshold,
            self.high_threshold,
            self.critical_threshold,
        ]

        for index, threshold in enumerate(
            thresholds
        ):
            thresholds[index] = _to_float(
                threshold,
                "risk threshold",
            )

        (
            self.low_threshold,
            self.medium_threshold,
            self.high_threshold,
            self.critical_threshold,
        ) = thresholds

        if not (
            self.low_threshold
            <= self.medium_threshold
            <= self.high_threshold
            <= self.critical_threshold
        ):
            raise ValueError(
                "Risk thresholds must be ordered."
            )

        self.probability_temperature = _to_float(
            self.probability_temperature,
            "probability_temperature",
        )

        if (
            self.probability_temperature
            <= 0.0
        ):
            raise ValueError(
                "probability_temperature must "
                "be greater than zero."
            )

        self.probability_threshold = _clamp(
            _to_float(
                self.probability_threshold,
                "probability_threshold",
            ),
            0.0,
            1.0,
        )


# ============================================================
# CALIBRATION RESULT
# ============================================================


@dataclass
class CalibratedRisk:
    """
    Result of calibrating one raw risk value.
    """

    raw_score: float

    calibrated_score: float

    normalized_score: float

    risk_level: str

    probability: float

    confidence: float

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert the calibrated risk to a dictionary."""

        return {
            "raw_score": self.raw_score,
            "calibrated_score": self.calibrated_score,
            "normalized_score": self.normalized_score,
            "risk_level": self.risk_level,
            "probability": self.probability,
            "confidence": self.confidence,
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# RELIABILITY BIN
# ============================================================


@dataclass
class ReliabilityBin:
    """
    One probability-calibration reliability bin.
    """

    lower_bound: float

    upper_bound: float

    sample_count: int

    average_predicted_probability: float

    observed_frequency: float

    calibration_error: float

    def to_dict(self) -> dict[str, Any]:
        """Convert reliability information to a dictionary."""

        return {
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "sample_count": self.sample_count,
            "average_predicted_probability": (
                self.average_predicted_probability
            ),
            "observed_frequency": (
                self.observed_frequency
            ),
            "calibration_error": (
                self.calibration_error
            ),
        }


# ============================================================
# CALIBRATION METRICS
# ============================================================


@dataclass
class CalibrationMetrics:
    """
    Metrics describing probability calibration.
    """

    brier_score: float

    log_loss: float

    expected_calibration_error: float

    maximum_calibration_error: float

    sample_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to a dictionary."""

        return {
            "brier_score": self.brier_score,
            "log_loss": self.log_loss,
            "expected_calibration_error": (
                self.expected_calibration_error
            ),
            "maximum_calibration_error": (
                self.maximum_calibration_error
            ),
            "sample_count": self.sample_count,
        }


# ============================================================
# RISK CALIBRATOR
# ============================================================


class RiskCalibrator:
    """
    High-level risk calibration service.

    This class converts raw model outputs into normalized,
    interpretable Blackout Oracle risk values.
    """

    def __init__(
        self,
        config: CalibrationConfig | None = None,
    ) -> None:
        """Initialize the risk calibrator."""

        self.config = (
            config
            if config is not None
            else CalibrationConfig()
        )

        self._platt_a = 1.0

        self._platt_b = 0.0

        self._fitted = False

    # ========================================================
    # SCORE NORMALIZATION
    # ========================================================

    def normalize_score(
        self,
        score: Any,
    ) -> float:
        """
        Normalize a raw risk score to 0-1.
        """

        value = _to_float(
            score,
            "risk score",
        )

        return _clamp(
            (
                value
                - self.config.min_score
            )
            / (
                self.config.max_score
                - self.config.min_score
            ),
            0.0,
            1.0,
        )

    # ========================================================
    # SCORE CALIBRATION
    # ========================================================

    def calibrate_score(
        self,
        score: Any,
    ) -> float:
        """
        Convert a raw score into the configured score range.
        """

        value = _to_float(
            score,
            "risk score",
        )

        return _clamp(
            value,
            self.config.min_score,
            self.config.max_score,
        )

    # ========================================================
    # RISK LEVEL
    # ========================================================

    def risk_level(
        self,
        score: Any,
    ) -> str:
        """
        Map a calibrated score to a risk level.
        """

        normalized = self.normalize_score(
            score
        )

        scaled_score = (
            normalized
            * 100.0
        )

        if (
            scaled_score
            >= self.config.critical_threshold
        ):
            return RiskLevel.CRITICAL

        if (
            scaled_score
            >= self.config.high_threshold
        ):
            return RiskLevel.HIGH

        if (
            scaled_score
            >= self.config.medium_threshold
        ):
            return RiskLevel.MEDIUM

        if (
            scaled_score
            >= self.config.low_threshold
        ):
            return RiskLevel.LOW

        return RiskLevel.VERY_LOW

    # ========================================================
    # SCORE TO PROBABILITY
    # ========================================================

    def score_to_probability(
        self,
        score: Any,
    ) -> float:
        """
        Convert a normalized risk score into a smooth probability.

        The transformation uses a logistic curve centered at 50%.
        """

        normalized = self.normalize_score(
            score
        )

        centered = (
            normalized
            - 0.5
        )

        temperature = (
            self.config.probability_temperature
        )

        probability = _sigmoid(
            centered
            * 10.0
            / temperature
        )

        return _clamp(
            probability,
            0.0,
            1.0,
        )

    # ========================================================
    # PROBABILITY CALIBRATION
    # ========================================================

    def calibrate_probability(
        self,
        probability: Any,
    ) -> float:
        """
        Calibrate a probability using the fitted Platt-style
        parameters and temperature scaling.
        """

        raw_probability = _clamp(
            _to_float(
                probability,
                "probability",
            ),
            0.0,
            1.0,
        )

        logit_value = _logit(
            raw_probability
        )

        calibrated_logit = (
            self._platt_a
            * logit_value
            + self._platt_b
        )

        temperature = (
            self.config.probability_temperature
        )

        calibrated = _sigmoid(
            calibrated_logit
            / temperature
        )

        return _clamp(
            calibrated,
            0.0,
            1.0,
        )

    # ========================================================
    # COMPLETE CALIBRATION
    # ========================================================

    def calibrate(
        self,
        score: Any,
        *,
        probability: float | None = None,
    ) -> CalibratedRisk:
        """
        Produce a complete calibrated-risk result.
        """

        raw_score = _to_float(
            score,
            "risk score",
        )

        calibrated_score = (
            self.calibrate_score(
                raw_score
            )
        )

        normalized_score = (
            self.normalize_score(
                calibrated_score
            )
        )

        level = self.risk_level(
            calibrated_score
        )

        if probability is None:
            calibrated_probability = (
                self.score_to_probability(
                    calibrated_score
                )
            )

        else:
            calibrated_probability = (
                self.calibrate_probability(
                    probability
                )
            )

        confidence = max(
            calibrated_probability,
            1.0
            - calibrated_probability,
        )

        return CalibratedRisk(
            raw_score=raw_score,
            calibrated_score=calibrated_score,
            normalized_score=normalized_score,
            risk_level=level,
            probability=calibrated_probability,
            confidence=confidence,
            metadata={
                "calibrated": True,
                "platt_fitted": self._fitted,
            },
        )

    # ========================================================
    # BATCH CALIBRATION
    # ========================================================

    def calibrate_many(
        self,
        scores: Iterable[Any],
    ) -> list[CalibratedRisk]:
        """
        Calibrate multiple risk scores.
        """

        return [
            self.calibrate(
                score
            )
            for score in scores
        ]

    # ========================================================
    # PLATT FIT
    # ========================================================

    def fit_probability_calibration(
        self,
        probabilities: Sequence[Any],
        actual: Sequence[Any],
        *,
        learning_rate: float = 0.05,
        iterations: int = 500,
    ) -> CalibrationMetrics:
        """
        Fit a lightweight Platt-style logistic calibrator.

        Parameters
        ----------
        probabilities:
            Raw predicted probabilities.

        actual:
            Binary observed outcomes.

        learning_rate:
            Gradient-descent learning rate.

        iterations:
            Number of optimization iterations.

        This is intentionally implemented without external ML
        dependencies.
        """

        if len(probabilities) != len(actual):
            raise ValueError(
                "probabilities and actual must "
                "have the same length."
            )

        if not probabilities:
            raise ValueError(
                "Calibration data cannot be empty."
            )

        learning_rate = _to_float(
            learning_rate,
            "learning_rate",
        )

        if learning_rate <= 0.0:
            raise ValueError(
                "learning_rate must be greater than zero."
            )

        if iterations < 1:
            raise ValueError(
                "iterations must be at least 1."
            )

        x_values: list[
            float
        ] = []

        y_values: list[
            float
        ] = []

        for probability, outcome in zip(
            probabilities,
            actual,
        ):
            probability_value = _clamp(
                _to_float(
                    probability,
                    "probability",
                ),
                EPSILON,
                1.0 - EPSILON,
            )

            outcome_value = _to_float(
                outcome,
                "actual outcome",
            )

            if outcome_value not in (
                0.0,
                1.0,
            ):
                raise ValueError(
                    "Actual outcomes must be 0 or 1."
                )

            x_values.append(
                _logit(
                    probability_value
                )
            )

            y_values.append(
                outcome_value
            )

        a = self._platt_a

        b = self._platt_b

        for _ in range(
            iterations
        ):
            gradient_a = 0.0

            gradient_b = 0.0

            for x_value, y_value in zip(
                x_values,
                y_values,
            ):
                prediction = _sigmoid(
                    a
                    * x_value
                    + b
                )

                error = (
                    prediction
                    - y_value
                )

                gradient_a += (
                    error
                    * x_value
                )

                gradient_b += error

            scale = (
                1.0
                / len(x_values)
            )

            gradient_a *= scale

            gradient_b *= scale

            a -= (
                learning_rate
                * gradient_a
            )

            b -= (
                learning_rate
                * gradient_b
            )

        self._platt_a = a

        self._platt_b = b

        self._fitted = True

        calibrated = [
            self.calibrate_probability(
                probability
            )
            for probability in probabilities
        ]

        return calibration_metrics(
            actual,
            calibrated,
        )

    # ========================================================
    # RELIABILITY ANALYSIS
    # ========================================================

    @staticmethod
    def reliability_bins(
        actual: Sequence[Any],
        probabilities: Sequence[Any],
        *,
        bin_count: int = 10,
    ) -> list[ReliabilityBin]:
        """
        Generate reliability bins for probability predictions.
        """

        if len(actual) != len(probabilities):
            raise ValueError(
                "actual and probabilities must "
                "have the same length."
            )

        if not actual:
            return []

        if bin_count < 1:
            raise ValueError(
                "bin_count must be at least 1."
            )

        bins: list[
            ReliabilityBin
        ] = []

        for index in range(
            bin_count
        ):
            lower = (
                index
                / bin_count
            )

            upper = (
                (index + 1)
                / bin_count
            )

            selected_probabilities: list[
                float
            ] = []

            selected_actual: list[
                float
            ] = []

            for outcome, probability in zip(
                actual,
                probabilities,
            ):
                probability_value = _clamp(
                    _to_float(
                        probability,
                        "probability",
                    ),
                    0.0,
                    1.0,
                )

                if index == (
                    bin_count - 1
                ):
                    belongs = (
                        lower
                        <= probability_value
                        <= upper
                    )

                else:
                    belongs = (
                        lower
                        <= probability_value
                        < upper
                    )

                if not belongs:
                    continue

                outcome_value = _to_float(
                    outcome,
                    "actual outcome",
                )

                if outcome_value not in (
                    0.0,
                    1.0,
                ):
                    raise ValueError(
                        "Actual outcomes must "
                        "be 0 or 1."
                    )

                selected_probabilities.append(
                    probability_value
                )

                selected_actual.append(
                    outcome_value
                )

            if selected_probabilities:
                average_probability = (
                    sum(
                        selected_probabilities
                    )
                    / len(
                        selected_probabilities
                    )
                )

                observed_frequency = (
                    sum(
                        selected_actual
                    )
                    / len(
                        selected_actual
                    )
                )

                error = abs(
                    average_probability
                    - observed_frequency
                )

            else:
                average_probability = 0.0

                observed_frequency = 0.0

                error = 0.0

            bins.append(
                ReliabilityBin(
                    lower_bound=lower,
                    upper_bound=upper,
                    sample_count=len(
                        selected_probabilities
                    ),
                    average_predicted_probability=(
                        average_probability
                    ),
                    observed_frequency=(
                        observed_frequency
                    ),
                    calibration_error=error,
                )
            )

        return bins

    # ========================================================
    # THRESHOLD OPTIMIZATION
    # ========================================================

    @staticmethod
    def find_probability_threshold(
        actual: Sequence[Any],
        probabilities: Sequence[Any],
        *,
        step: float = 0.01,
    ) -> float:
        """
        Find the probability threshold that maximizes F1 score.
        """

        if len(actual) != len(probabilities):
            raise ValueError(
                "actual and probabilities must "
                "have the same length."
            )

        if not actual:
            raise ValueError(
                "Calibration data cannot be empty."
            )

        step = _to_float(
            step,
            "step",
        )

        if step <= 0.0:
            raise ValueError(
                "step must be greater than zero."
            )

        best_threshold = 0.5

        best_f1 = -1.0

        threshold = 0.0

        while threshold <= 1.0 + EPSILON:
            true_positive = 0

            false_positive = 0

            false_negative = 0

            for outcome, probability in zip(
                actual,
                probabilities,
            ):
                outcome_value = _to_float(
                    outcome,
                    "actual outcome",
                )

                probability_value = _clamp(
                    _to_float(
                        probability,
                        "probability",
                    ),
                    0.0,
                    1.0,
                )

                predicted = (
                    probability_value
                    >= threshold
                )

                if (
                    outcome_value == 1.0
                    and predicted
                ):
                    true_positive += 1

                elif (
                    outcome_value == 0.0
                    and not predicted
                ):
                    pass

                elif (
                    outcome_value == 0.0
                    and predicted
                ):
                    false_positive += 1

                elif (
                    outcome_value == 1.0
                    and not predicted
                ):
                    false_negative += 1

                else:
                    raise ValueError(
                        "Actual outcomes must be "
                        "0 or 1."
                    )

            precision_value = _safe_divide(
                true_positive,
                true_positive
                + false_positive,
            )

            recall_value = _safe_divide(
                true_positive,
                true_positive
                + false_negative,
            )

            f1 = _safe_divide(
                2.0
                * precision_value
                * recall_value,
                precision_value
                + recall_value,
            )

            if f1 > best_f1:
                best_f1 = f1

                best_threshold = threshold

            threshold += step

        return _clamp(
            best_threshold,
            0.0,
            1.0,
        )

    # ========================================================
    # CONFIGURATION INFO
    # ========================================================

    def model_info(
        self,
    ) -> dict[str, Any]:
        """Return calibration-model information."""

        return {
            "model_name": "RiskCalibrator",
            "version": "1.0",
            "fitted": self._fitted,
            "platt_a": self._platt_a,
            "platt_b": self._platt_b,
            "config": {
                "min_score": (
                    self.config.min_score
                ),
                "max_score": (
                    self.config.max_score
                ),
                "low_threshold": (
                    self.config.low_threshold
                ),
                "medium_threshold": (
                    self.config.medium_threshold
                ),
                "high_threshold": (
                    self.config.high_threshold
                ),
                "critical_threshold": (
                    self.config.critical_threshold
                ),
                "probability_temperature": (
                    self.config.probability_temperature
                ),
                "probability_threshold": (
                    self.config.probability_threshold
                ),
            },
        }


# ============================================================
# CALIBRATION METRICS
# ============================================================


def calibration_metrics(
    actual: Sequence[Any],
    probabilities: Sequence[Any],
) -> CalibrationMetrics:
    """
    Calculate common probability-calibration metrics.
    """

    if len(actual) != len(probabilities):
        raise ValueError(
            "actual and probabilities must "
            "have the same length."
        )

    if not actual:
        raise ValueError(
            "Calibration data cannot be empty."
        )

    brier_total = 0.0

    log_loss_total = 0.0

    validated_actual: list[
        float
    ] = []

    validated_probabilities: list[
        float
    ] = []

    for outcome, probability in zip(
        actual,
        probabilities,
    ):
        outcome_value = _to_float(
            outcome,
            "actual outcome",
        )

        if outcome_value not in (
            0.0,
            1.0,
        ):
            raise ValueError(
                "Actual outcomes must be 0 or 1."
            )

        probability_value = _clamp(
            _to_float(
                probability,
                "probability",
            ),
            EPSILON,
            1.0 - EPSILON,
        )

        validated_actual.append(
            outcome_value
        )

        validated_probabilities.append(
            probability_value
        )

        brier_total += (
            probability_value
            - outcome_value
        ) ** 2

        log_loss_total += -(
            outcome_value
            * math.log(
                probability_value
            )
            + (
                1.0
                - outcome_value
            )
            * math.log(
                1.0
                - probability_value
            )
        )

    bins = RiskCalibrator.reliability_bins(
        validated_actual,
        validated_probabilities,
    )

    total_samples = len(
        validated_actual
    )

    expected_calibration_error = (
        sum(
            (
                bin_item.sample_count
                / total_samples
            )
            * bin_item.calibration_error
            for bin_item in bins
        )
    )

    maximum_calibration_error = max(
        (
            bin_item.calibration_error
            for bin_item in bins
            if bin_item.sample_count > 0
        ),
        default=0.0,
    )

    return CalibrationMetrics(
        brier_score=(
            brier_total
            / total_samples
        ),
        log_loss=(
            log_loss_total
            / total_samples
        ),
        expected_calibration_error=(
            expected_calibration_error
        ),
        maximum_calibration_error=(
            maximum_calibration_error
        ),
        sample_count=total_samples,
    )


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def calibrate_risk(
    score: Any,
    *,
    config: CalibrationConfig | None = None,
) -> CalibratedRisk:
    """
    Convenience function for calibrating one risk score.
    """

    calibrator = RiskCalibrator(
        config=config
    )

    return calibrator.calibrate(
        score
    )


def normalize_risk_score(
    score: Any,
    *,
    config: CalibrationConfig | None = None,
) -> float:
    """
    Convenience function for normalizing one risk score.
    """

    calibrator = RiskCalibrator(
        config=config
    )

    return calibrator.normalize_score(
        score
    )


def risk_level_from_score(
    score: Any,
    *,
    config: CalibrationConfig | None = None,
) -> str:
    """
    Convenience function for determining a risk level.
    """

    calibrator = RiskCalibrator(
        config=config
    )

    return calibrator.risk_level(
        score
    )


def score_to_probability(
    score: Any,
    *,
    config: CalibrationConfig | None = None,
) -> float:
    """
    Convenience function for converting a risk score to
    probability.
    """

    calibrator = RiskCalibrator(
        config=config
    )

    return calibrator.score_to_probability(
        score
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "RiskLevel",
    "RISK_LEVELS",
    "CalibrationConfig",
    "CalibratedRisk",
    "ReliabilityBin",
    "CalibrationMetrics",
    "RiskCalibrator",
    "calibration_metrics",
    "calibrate_risk",
    "normalize_risk_score",
    "risk_level_from_score",
    "score_to_probability",
]