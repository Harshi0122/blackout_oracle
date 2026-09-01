"""
Blackout Oracle - ML Evaluation Metrics.

Dependency-free evaluation utilities for the ML and risk-scoring
components used by Blackout Oracle.

Supported metrics include:

- Accuracy
- Precision
- Recall
- F1 score
- Specificity
- False-positive rate
- False-negative rate
- Mean absolute error
- Mean squared error
- Root mean squared error
- R-squared
- Binary log loss
- Brier score
- Confusion matrix
- Threshold analysis

The functions in this module operate on ordinary Python
iterables and do not require NumPy, pandas, scikit-learn,
or any other external ML package.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable, Sequence


# ============================================================
# CONSTANTS
# ============================================================

EPSILON = 1e-12


# ============================================================
# HELPERS
# ============================================================


def _as_list(
    values: Iterable[Any],
) -> list[Any]:
    """Convert an iterable to a list."""

    return list(values)


def _validate_equal_length(
    actual: Sequence[Any],
    predicted: Sequence[Any],
) -> None:
    """Ensure two sequences contain the same number of values."""

    if len(actual) != len(predicted):
        raise ValueError(
            "Actual and predicted values must have "
            "the same length."
        )


def _safe_divide(
    numerator: float,
    denominator: float,
) -> float:
    """Perform division without raising ZeroDivisionError."""

    if abs(denominator) <= EPSILON:
        return 0.0

    return numerator / denominator


def _validate_non_empty(
    values: Sequence[Any],
    name: str = "values",
) -> None:
    """Ensure a sequence is not empty."""

    if not values:
        raise ValueError(
            f"{name} must not be empty."
        )


def _validate_binary_label(
    value: Any,
) -> int:
    """
    Convert a binary label to 0 or 1.

    Accepted values include:

        0, 1
        False, True
        0.0, 1.0
    """

    if value is True:
        return 1

    if value is False:
        return 0

    try:
        numeric = float(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            f"Invalid binary label: {value!r}"
        ) from exc

    if numeric not in (0.0, 1.0):
        raise ValueError(
            f"Binary labels must be 0 or 1, "
            f"got {value!r}."
        )

    return int(numeric)


def _validate_probability(
    value: Any,
) -> float:
    """Convert and clamp a probability to the range 0-1."""

    try:
        probability = float(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            f"Invalid probability: {value!r}"
        ) from exc

    if not math.isfinite(
        probability
    ):
        raise ValueError(
            f"Probability must be finite, "
            f"got {value!r}."
        )

    return max(
        0.0,
        min(
            1.0,
            probability,
        ),
    )


def _validate_numeric(
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

    if not math.isfinite(
        numeric
    ):
        raise ValueError(
            f"{name} must be finite."
        )

    return numeric


# ============================================================
# CONFUSION MATRIX
# ============================================================


@dataclass
class ConfusionMatrix:
    """
    Binary classification confusion matrix.

    Fields:

        true_positive
        true_negative
        false_positive
        false_negative
    """

    true_positive: int = 0

    true_negative: int = 0

    false_positive: int = 0

    false_negative: int = 0

    @property
    def total(self) -> int:
        """Return the total number of observations."""

        return (
            self.true_positive
            + self.true_negative
            + self.false_positive
            + self.false_negative
        )

    @property
    def actual_positive(self) -> int:
        """Return the number of actual positive cases."""

        return (
            self.true_positive
            + self.false_negative
        )

    @property
    def actual_negative(self) -> int:
        """Return the number of actual negative cases."""

        return (
            self.true_negative
            + self.false_positive
        )

    @property
    def predicted_positive(self) -> int:
        """Return the number predicted positive."""

        return (
            self.true_positive
            + self.false_positive
        )

    @property
    def predicted_negative(self) -> int:
        """Return the number predicted negative."""

        return (
            self.true_negative
            + self.false_negative
        )

    def to_dict(self) -> dict[str, int]:
        """Convert the matrix to a dictionary."""

        return {
            "true_positive": self.true_positive,
            "true_negative": self.true_negative,
            "false_positive": self.false_positive,
            "false_negative": self.false_negative,
            "total": self.total,
        }


def confusion_matrix(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> ConfusionMatrix:
    """
    Calculate a binary confusion matrix.
    """

    actual_values = _as_list(
        actual
    )

    predicted_values = _as_list(
        predicted
    )

    _validate_equal_length(
        actual_values,
        predicted_values,
    )

    _validate_non_empty(
        actual_values,
        "actual",
    )

    matrix = ConfusionMatrix()

    for actual_value, predicted_value in zip(
        actual_values,
        predicted_values,
    ):
        actual_label = _validate_binary_label(
            actual_value
        )

        predicted_label = _validate_binary_label(
            predicted_value
        )

        if (
            actual_label == 1
            and predicted_label == 1
        ):
            matrix.true_positive += 1

        elif (
            actual_label == 0
            and predicted_label == 0
        ):
            matrix.true_negative += 1

        elif (
            actual_label == 0
            and predicted_label == 1
        ):
            matrix.false_positive += 1

        else:
            matrix.false_negative += 1

    return matrix


# ============================================================
# CLASSIFICATION METRICS
# ============================================================


def accuracy(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> float:
    """
    Calculate classification accuracy.

    Accuracy = correct predictions / total predictions
    """

    actual_values = _as_list(
        actual
    )

    predicted_values = _as_list(
        predicted
    )

    _validate_equal_length(
        actual_values,
        predicted_values,
    )

    _validate_non_empty(
        actual_values,
        "actual",
    )

    correct = sum(
        1
        for actual_value, predicted_value
        in zip(
            actual_values,
            predicted_values,
        )
        if actual_value == predicted_value
    )

    return _safe_divide(
        correct,
        len(actual_values),
    )


def precision(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> float:
    """
    Calculate binary precision.

    Precision = TP / (TP + FP)
    """

    matrix = confusion_matrix(
        actual,
        predicted,
    )

    return _safe_divide(
        matrix.true_positive,
        matrix.predicted_positive,
    )


def recall(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> float:
    """
    Calculate binary recall / sensitivity.

    Recall = TP / (TP + FN)
    """

    matrix = confusion_matrix(
        actual,
        predicted,
    )

    return _safe_divide(
        matrix.true_positive,
        matrix.actual_positive,
    )


def sensitivity(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> float:
    """Alias for recall."""

    return recall(
        actual,
        predicted,
    )


def specificity(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> float:
    """
    Calculate specificity.

    Specificity = TN / (TN + FP)
    """

    matrix = confusion_matrix(
        actual,
        predicted,
    )

    return _safe_divide(
        matrix.true_negative,
        matrix.actual_negative,
    )


def false_positive_rate(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> float:
    """
    Calculate false-positive rate.

    FPR = FP / (FP + TN)
    """

    matrix = confusion_matrix(
        actual,
        predicted,
    )

    return _safe_divide(
        matrix.false_positive,
        matrix.actual_negative,
    )


def false_negative_rate(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> float:
    """
    Calculate false-negative rate.

    FNR = FN / (FN + TP)
    """

    matrix = confusion_matrix(
        actual,
        predicted,
    )

    return _safe_divide(
        matrix.false_negative,
        matrix.actual_positive,
    )


def f1_score(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> float:
    """
    Calculate the binary F1 score.

    F1 = 2 * precision * recall / (precision + recall)
    """

    precision_value = precision(
        actual,
        predicted,
    )

    recall_value = recall(
        actual,
        predicted,
    )

    return _safe_divide(
        2.0
        * precision_value
        * recall_value,
        precision_value
        + recall_value,
    )


def balanced_accuracy(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> float:
    """
    Calculate balanced accuracy.

    Balanced accuracy is the average of sensitivity
    and specificity.
    """

    sensitivity_value = sensitivity(
        actual,
        predicted,
    )

    specificity_value = specificity(
        actual,
        predicted,
    )

    return (
        sensitivity_value
        + specificity_value
    ) / 2.0


# ============================================================
# REGRESSION / RISK-SCORE METRICS
# ============================================================


def mean_absolute_error(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> float:
    """
    Calculate mean absolute error.

    MAE = mean(|actual - predicted|)
    """

    actual_values = _as_list(
        actual
    )

    predicted_values = _as_list(
        predicted
    )

    _validate_equal_length(
        actual_values,
        predicted_values,
    )

    _validate_non_empty(
        actual_values,
        "actual",
    )

    errors = [
        abs(
            _validate_numeric(
                actual_value,
                "actual value",
            )
            - _validate_numeric(
                predicted_value,
                "predicted value",
            )
        )
        for actual_value, predicted_value
        in zip(
            actual_values,
            predicted_values,
        )
    ]

    return sum(
        errors
    ) / len(
        errors
    )


def mean_squared_error(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> float:
    """
    Calculate mean squared error.

    MSE = mean((actual - predicted)^2)
    """

    actual_values = _as_list(
        actual
    )

    predicted_values = _as_list(
        predicted
    )

    _validate_equal_length(
        actual_values,
        predicted_values,
    )

    _validate_non_empty(
        actual_values,
        "actual",
    )

    squared_errors = []

    for actual_value, predicted_value in zip(
        actual_values,
        predicted_values,
    ):
        actual_numeric = _validate_numeric(
            actual_value,
            "actual value",
        )

        predicted_numeric = _validate_numeric(
            predicted_value,
            "predicted value",
        )

        squared_errors.append(
            (
                actual_numeric
                - predicted_numeric
            )
            ** 2
        )

    return sum(
        squared_errors
    ) / len(
        squared_errors
    )


def root_mean_squared_error(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> float:
    """
    Calculate root mean squared error.
    """

    return math.sqrt(
        mean_squared_error(
            actual,
            predicted,
        )
    )


def r_squared(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> float:
    """
    Calculate coefficient of determination R².

    R² = 1 - SS_res / SS_tot

    If all actual values are identical, 0.0 is returned.
    """

    actual_values = [
        _validate_numeric(
            value,
            "actual value",
        )
        for value in actual
    ]

    predicted_values = [
        _validate_numeric(
            value,
            "predicted value",
        )
        for value in predicted
    ]

    _validate_equal_length(
        actual_values,
        predicted_values,
    )

    _validate_non_empty(
        actual_values,
        "actual",
    )

    mean_actual = (
        sum(actual_values)
        / len(actual_values)
    )

    ss_res = sum(
        (
            actual_value
            - predicted_value
        )
        ** 2
        for actual_value, predicted_value
        in zip(
            actual_values,
            predicted_values,
        )
    )

    ss_tot = sum(
        (
            actual_value
            - mean_actual
        )
        ** 2
        for actual_value in actual_values
    )

    if abs(ss_tot) <= EPSILON:
        return 0.0

    return 1.0 - (
        ss_res
        / ss_tot
    )


# ============================================================
# PROBABILITY METRICS
# ============================================================


def binary_log_loss(
    actual: Iterable[Any],
    probabilities: Iterable[Any],
) -> float:
    """
    Calculate binary log loss.

    Lower is better.

    Probabilities are clipped internally to avoid log(0).
    """

    actual_values = _as_list(
        actual
    )

    probability_values = _as_list(
        probabilities
    )

    _validate_equal_length(
        actual_values,
        probability_values,
    )

    _validate_non_empty(
        actual_values,
        "actual",
    )

    total_loss = 0.0

    for actual_value, probability in zip(
        actual_values,
        probability_values,
    ):
        label = _validate_binary_label(
            actual_value
        )

        probability_value = _validate_probability(
            probability
        )

        probability_value = max(
            EPSILON,
            min(
                1.0 - EPSILON,
                probability_value,
            ),
        )

        total_loss += -(
            label
            * math.log(
                probability_value
            )
            + (
                1 - label
            )
            * math.log(
                1.0
                - probability_value
            )
        )

    return total_loss / len(
        actual_values
    )


def brier_score(
    actual: Iterable[Any],
    probabilities: Iterable[Any],
) -> float:
    """
    Calculate the Brier score.

    Lower is better.

    Brier score = mean((probability - outcome)^2)
    """

    actual_values = _as_list(
        actual
    )

    probability_values = _as_list(
        probabilities
    )

    _validate_equal_length(
        actual_values,
        probability_values,
    )

    _validate_non_empty(
        actual_values,
        "actual",
    )

    squared_errors = []

    for actual_value, probability in zip(
        actual_values,
        probability_values,
    ):
        label = _validate_binary_label(
            actual_value
        )

        probability_value = _validate_probability(
            probability
        )

        squared_errors.append(
            (
                probability_value
                - label
            )
            ** 2
        )

    return sum(
        squared_errors
    ) / len(
        squared_errors
    )


# ============================================================
# THRESHOLD UTILITIES
# ============================================================


def probabilities_to_labels(
    probabilities: Iterable[Any],
    threshold: float = 0.5,
) -> list[int]:
    """
    Convert probabilities into binary labels.

    probability >= threshold -> 1
    probability < threshold  -> 0
    """

    threshold = _validate_probability(
        threshold
    )

    return [
        int(
            _validate_probability(
                probability
            )
            >= threshold
        )
        for probability in probabilities
    ]


@dataclass
class ThresholdMetrics:
    """
    Classification metrics associated with one probability
    threshold.
    """

    threshold: float

    accuracy: float

    precision: float

    recall: float

    specificity: float

    f1: float

    false_positive_rate: float

    false_negative_rate: float

    confusion_matrix: ConfusionMatrix

    def to_dict(self) -> dict[str, Any]:
        """Convert threshold metrics to a dictionary."""

        return {
            "threshold": self.threshold,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "specificity": self.specificity,
            "f1": self.f1,
            "false_positive_rate": (
                self.false_positive_rate
            ),
            "false_negative_rate": (
                self.false_negative_rate
            ),
            "confusion_matrix": (
                self.confusion_matrix.to_dict()
            ),
        }


def evaluate_threshold(
    actual: Iterable[Any],
    probabilities: Iterable[Any],
    threshold: float = 0.5,
) -> ThresholdMetrics:
    """
    Evaluate binary predictions at a selected threshold.
    """

    actual_values = _as_list(
        actual
    )

    probability_values = _as_list(
        probabilities
    )

    _validate_equal_length(
        actual_values,
        probability_values,
    )

    _validate_non_empty(
        actual_values,
        "actual",
    )

    predicted = probabilities_to_labels(
        probability_values,
        threshold=threshold,
    )

    matrix = confusion_matrix(
        actual_values,
        predicted,
    )

    return ThresholdMetrics(
        threshold=_validate_probability(
            threshold
        ),
        accuracy=accuracy(
            actual_values,
            predicted,
        ),
        precision=precision(
            actual_values,
            predicted,
        ),
        recall=recall(
            actual_values,
            predicted,
        ),
        specificity=specificity(
            actual_values,
            predicted,
        ),
        f1=f1_score(
            actual_values,
            predicted,
        ),
        false_positive_rate=(
            false_positive_rate(
                actual_values,
                predicted,
            )
        ),
        false_negative_rate=(
            false_negative_rate(
                actual_values,
                predicted,
            )
        ),
        confusion_matrix=matrix,
    )


def threshold_analysis(
    actual: Iterable[Any],
    probabilities: Iterable[Any],
    thresholds: Iterable[float] | None = None,
) -> list[ThresholdMetrics]:
    """
    Evaluate multiple probability thresholds.

    If thresholds are omitted, values from 0.05 through 0.95
    in increments of 0.05 are evaluated.
    """

    actual_values = _as_list(
        actual
    )

    probability_values = _as_list(
        probabilities
    )

    _validate_equal_length(
        actual_values,
        probability_values,
    )

    _validate_non_empty(
        actual_values,
        "actual",
    )

    if thresholds is None:
        threshold_values = [
            index / 100.0
            for index in range(
                5,
                100,
                5,
            )
        ]

    else:
        threshold_values = [
            _validate_probability(
                threshold
            )
            for threshold in thresholds
        ]

    return [
        evaluate_threshold(
            actual_values,
            probability_values,
            threshold,
        )
        for threshold in threshold_values
    ]


# ============================================================
# COMPLETE CLASSIFICATION REPORT
# ============================================================


@dataclass
class ClassificationMetrics:
    """
    Complete binary-classification evaluation report.
    """

    accuracy: float

    precision: float

    recall: float

    specificity: float

    f1: float

    balanced_accuracy: float

    false_positive_rate: float

    false_negative_rate: float

    confusion_matrix: ConfusionMatrix

    def to_dict(self) -> dict[str, Any]:
        """Convert the report to a dictionary."""

        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "specificity": self.specificity,
            "f1": self.f1,
            "balanced_accuracy": (
                self.balanced_accuracy
            ),
            "false_positive_rate": (
                self.false_positive_rate
            ),
            "false_negative_rate": (
                self.false_negative_rate
            ),
            "confusion_matrix": (
                self.confusion_matrix.to_dict()
            ),
        }


def classification_report(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> ClassificationMetrics:
    """
    Generate a complete binary classification report.
    """

    actual_values = _as_list(
        actual
    )

    predicted_values = _as_list(
        predicted
    )

    matrix = confusion_matrix(
        actual_values,
        predicted_values,
    )

    return ClassificationMetrics(
        accuracy=accuracy(
            actual_values,
            predicted_values,
        ),
        precision=precision(
            actual_values,
            predicted_values,
        ),
        recall=recall(
            actual_values,
            predicted_values,
        ),
        specificity=specificity(
            actual_values,
            predicted_values,
        ),
        f1=f1_score(
            actual_values,
            predicted_values,
        ),
        balanced_accuracy=balanced_accuracy(
            actual_values,
            predicted_values,
        ),
        false_positive_rate=(
            false_positive_rate(
                actual_values,
                predicted_values,
            )
        ),
        false_negative_rate=(
            false_negative_rate(
                actual_values,
                predicted_values,
            )
        ),
        confusion_matrix=matrix,
    )


# ============================================================
# RISK MODEL EVALUATION
# ============================================================


@dataclass
class RiskEvaluation:
    """
    Combined evaluation report for a risk-scoring model.
    """

    mae: float

    mse: float

    rmse: float

    r_squared: float

    brier_score: float | None = None

    log_loss: float | None = None

    classification: ClassificationMetrics | None = None

    threshold: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the evaluation report to a dictionary."""

        return {
            "mae": self.mae,
            "mse": self.mse,
            "rmse": self.rmse,
            "r_squared": self.r_squared,
            "brier_score": self.brier_score,
            "log_loss": self.log_loss,
            "classification": (
                self.classification.to_dict()
                if self.classification is not None
                else None
            ),
            "threshold": self.threshold,
        }


def evaluate_risk_predictions(
    actual_scores: Iterable[Any],
    predicted_scores: Iterable[Any],
) -> RiskEvaluation:
    """
    Evaluate continuous risk-score predictions.

    Useful for models such as:

        AssetFailureModel
        BlackoutRiskModel
        CascadeModel
    """

    actual_values = [
        _validate_numeric(
            value,
            "actual score",
        )
        for value in actual_scores
    ]

    predicted_values = [
        _validate_numeric(
            value,
            "predicted score",
        )
        for value in predicted_scores
    ]

    _validate_equal_length(
        actual_values,
        predicted_values,
    )

    return RiskEvaluation(
        mae=mean_absolute_error(
            actual_values,
            predicted_values,
        ),
        mse=mean_squared_error(
            actual_values,
            predicted_values,
        ),
        rmse=root_mean_squared_error(
            actual_values,
            predicted_values,
        ),
        r_squared=r_squared(
            actual_values,
            predicted_values,
        ),
    )


def evaluate_binary_risk_model(
    actual: Iterable[Any],
    probabilities: Iterable[Any],
    *,
    threshold: float = 0.5,
) -> RiskEvaluation:
    """
    Evaluate a binary risk model that produces probabilities.

    Example:

        actual = [0, 0, 1, 1]
        probabilities = [0.1, 0.3, 0.8, 0.9]
    """

    actual_values = _as_list(
        actual
    )

    probability_values = [
        _validate_probability(
            value
        )
        for value in probabilities
    ]

    _validate_equal_length(
        actual_values,
        probability_values,
    )

    predicted_labels = probabilities_to_labels(
        probability_values,
        threshold=threshold,
    )

    classification = classification_report(
        actual_values,
        predicted_labels,
    )

    return RiskEvaluation(
        mae=mean_absolute_error(
            actual_values,
            probability_values,
        ),
        mse=mean_squared_error(
            actual_values,
            probability_values,
        ),
        rmse=root_mean_squared_error(
            actual_values,
            probability_values,
        ),
        r_squared=r_squared(
            actual_values,
            probability_values,
        ),
        brier_score=brier_score(
            actual_values,
            probability_values,
        ),
        log_loss=binary_log_loss(
            actual_values,
            probability_values,
        ),
        classification=classification,
        threshold=threshold,
    )


# ============================================================
# MODEL SCORE SUMMARY
# ============================================================


def score_summary(
    actual: Iterable[Any],
    predicted: Iterable[Any],
) -> dict[str, float]:
    """
    Return common regression/risk-score metrics in dictionary
    form.
    """

    actual_values = _as_list(
        actual
    )

    predicted_values = _as_list(
        predicted
    )

    return {
        "mae": mean_absolute_error(
            actual_values,
            predicted_values,
        ),
        "mse": mean_squared_error(
            actual_values,
            predicted_values,
        ),
        "rmse": root_mean_squared_error(
            actual_values,
            predicted_values,
        ),
        "r_squared": r_squared(
            actual_values,
            predicted_values,
        ),
    }


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "ConfusionMatrix",
    "ThresholdMetrics",
    "ClassificationMetrics",
    "RiskEvaluation",
    "confusion_matrix",
    "accuracy",
    "precision",
    "recall",
    "sensitivity",
    "specificity",
    "false_positive_rate",
    "false_negative_rate",
    "f1_score",
    "balanced_accuracy",
    "mean_absolute_error",
    "mean_squared_error",
    "root_mean_squared_error",
    "r_squared",
    "binary_log_loss",
    "brier_score",
    "probabilities_to_labels",
    "evaluate_threshold",
    "threshold_analysis",
    "classification_report",
    "evaluate_risk_predictions",
    "evaluate_binary_risk_model",
    "score_summary",
]