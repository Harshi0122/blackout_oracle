"""
Blackout Oracle - Anomaly Detector.

Provides lightweight statistical anomaly detection for electrical
grid telemetry and related numerical data.

The detector supports:

- Z-score based detection
- IQR based detection
- Rolling-window detection
- Multi-feature anomaly detection
- Severity classification
- Anomaly scoring
- Batch detection
- Per-record detection

This module is intentionally independent of:
- FastAPI
- SQLAlchemy
- Database models
- External APIs
- Heavy machine-learning frameworks

It can therefore be used as a reliable baseline before adding
more advanced ML models.
"""

from __future__ import annotations

import math
import statistics
from collections import deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ============================================================
# ENUMS
# ============================================================


class AnomalyMethod(str, Enum):
    """Supported anomaly-detection methods."""

    Z_SCORE = "z_score"
    IQR = "iqr"
    ROLLING = "rolling"
    COMBINED = "combined"


class AnomalySeverity(str, Enum):
    """Severity assigned to a detected anomaly."""

    NORMAL = "normal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# DATA CLASSES
# ============================================================


@dataclass
class AnomalyConfig:
    """
    Configuration for anomaly detection.

    Thresholds are intentionally configurable because different
    electrical measurements have different normal operating
    ranges.
    """

    z_score_threshold: float = 3.0

    high_z_score_threshold: float = 4.0

    critical_z_score_threshold: float = 5.0

    iqr_multiplier: float = 1.5

    rolling_window_size: int = 10

    rolling_z_score_threshold: float = 3.0

    minimum_samples: int = 5

    low_score_threshold: float = 0.50

    medium_score_threshold: float = 0.70

    high_score_threshold: float = 0.85

    critical_score_threshold: float = 0.95

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""

        self.z_score_threshold = max(
            0.1,
            float(self.z_score_threshold),
        )

        self.high_z_score_threshold = max(
            self.z_score_threshold,
            float(self.high_z_score_threshold),
        )

        self.critical_z_score_threshold = max(
            self.high_z_score_threshold,
            float(self.critical_z_score_threshold),
        )

        self.iqr_multiplier = max(
            0.1,
            float(self.iqr_multiplier),
        )

        self.rolling_window_size = max(
            2,
            int(self.rolling_window_size),
        )

        self.rolling_z_score_threshold = max(
            0.1,
            float(self.rolling_z_score_threshold),
        )

        self.minimum_samples = max(
            2,
            int(self.minimum_samples),
        )


@dataclass
class AnomalyResult:
    """
    Result for one evaluated observation.
    """

    feature: str

    value: float

    is_anomaly: bool

    score: float

    severity: AnomalySeverity

    method: AnomalyMethod

    z_score: float | None = None

    lower_bound: float | None = None

    upper_bound: float | None = None

    expected_value: float | None = None

    message: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert the result to a dictionary."""

        return {
            "feature": self.feature,
            "value": self.value,
            "is_anomaly": self.is_anomaly,
            "score": self.score,
            "severity": self.severity.value,
            "method": self.method.value,
            "z_score": self.z_score,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "expected_value": self.expected_value,
            "message": self.message,
            "metadata": dict(self.metadata),
        }


@dataclass
class RecordAnomalyResult:
    """
    Anomaly result for an entire telemetry record.
    """

    record_index: int

    timestamp: Any = None

    is_anomaly: bool = False

    overall_score: float = 0.0

    severity: AnomalySeverity = AnomalySeverity.NORMAL

    anomalies: list[AnomalyResult] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def anomaly_count(self) -> int:
        """Return the number of anomalous features."""

        return len(
            self.anomalies
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the result to a dictionary."""

        return {
            "record_index": self.record_index,
            "timestamp": self.timestamp,
            "is_anomaly": self.is_anomaly,
            "overall_score": self.overall_score,
            "severity": self.severity.value,
            "anomaly_count": self.anomaly_count,
            "anomalies": [
                anomaly.to_dict()
                for anomaly in self.anomalies
            ],
            "metadata": dict(self.metadata),
        }


@dataclass
class DetectionReport:
    """
    Complete anomaly-detection report for a dataset.
    """

    total_records: int = 0

    anomalous_records: int = 0

    normal_records: int = 0

    total_anomalies: int = 0

    results: list[RecordAnomalyResult] = field(
        default_factory=list
    )

    feature_statistics: dict[
        str,
        dict[str, float],
    ] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def anomaly_rate(self) -> float:
        """Return the percentage of anomalous records."""

        if self.total_records <= 0:
            return 0.0

        return (
            self.anomalous_records
            / self.total_records
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the report into a dictionary."""

        return {
            "total_records": self.total_records,
            "anomalous_records": self.anomalous_records,
            "normal_records": self.normal_records,
            "total_anomalies": self.total_anomalies,
            "anomaly_rate": self.anomaly_rate,
            "results": [
                result.to_dict()
                for result in self.results
            ],
            "feature_statistics": dict(
                self.feature_statistics
            ),
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def _to_float(
    value: Any,
) -> float | None:
    """Safely convert a value to float."""

    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return None

    try:
        result = float(
            value
        )
    except (
        TypeError,
        ValueError,
    ):
        return None

    if not math.isfinite(
        result
    ):
        return None

    return result


def _mean(
    values: Iterable[float],
) -> float:
    """Calculate the mean."""

    values_list = list(
        values
    )

    if not values_list:
        return 0.0

    return statistics.fmean(
        values_list
    )


def _standard_deviation(
    values: Iterable[float],
) -> float:
    """Calculate population standard deviation."""

    values_list = list(
        values
    )

    if len(
        values_list
    ) < 2:
        return 0.0

    return statistics.pstdev(
        values_list
    )


def _percentile(
    values: Iterable[float],
    percentile: float,
) -> float:
    """
    Calculate a percentile using linear interpolation.
    """

    values_list = sorted(
        values
    )

    if not values_list:
        return 0.0

    if len(
        values_list
    ) == 1:
        return values_list[0]

    percentile = max(
        0.0,
        min(
            100.0,
            percentile,
        ),
    )

    position = (
        (len(values_list) - 1)
        * percentile
        / 100.0
    )

    lower = int(
        math.floor(
            position
        )
    )

    upper = int(
        math.ceil(
            position
        )
    )

    if lower == upper:
        return values_list[lower]

    fraction = (
        position - lower
    )

    return (
        values_list[lower]
        + (
            values_list[upper]
            - values_list[lower]
        )
        * fraction
    )


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    """Clamp a value to a range."""

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


# ============================================================
# ANOMALY DETECTOR
# ============================================================


class AnomalyDetector:
    """
    Statistical anomaly detector for grid telemetry.

    The detector does not claim that an anomaly is necessarily
    a fault. It identifies observations that differ significantly
    from the supplied statistical baseline.
    """

    def __init__(
        self,
        config: AnomalyConfig | None = None,
    ) -> None:
        """Initialize the detector."""

        self.config = (
            config
            if config is not None
            else AnomalyConfig()
        )

    # ========================================================
    # Z-SCORE
    # ========================================================

    def calculate_z_score(
        self,
        value: float,
        values: Iterable[float],
    ) -> float:
        """
        Calculate the z-score of a value against a dataset.
        """

        values_list = list(
            values
        )

        if len(
            values_list
        ) < 2:
            return 0.0

        mean = _mean(
            values_list
        )

        standard_deviation = _standard_deviation(
            values_list
        )

        if standard_deviation <= 0.0:
            return 0.0

        return (
            value - mean
        ) / standard_deviation

    def detect_z_score(
        self,
        value: float,
        values: Iterable[float],
        feature: str = "value",
    ) -> AnomalyResult:
        """
        Detect an anomaly using a z-score.
        """

        values_list = list(
            values
        )

        mean = (
            _mean(
                values_list
            )
            if values_list
            else value
        )

        standard_deviation = (
            _standard_deviation(
                values_list
            )
            if len(values_list) >= 2
            else 0.0
        )

        z_score = self.calculate_z_score(
            value,
            values_list,
        )

        absolute_z = abs(
            z_score
        )

        threshold = (
            self.config.z_score_threshold
        )

        is_anomaly = (
            len(values_list)
            >= self.config.minimum_samples
            and absolute_z
            >= threshold
        )

        score = self._score_from_z_score(
            absolute_z
        )

        severity = self._severity_from_score(
            score
        )

        if is_anomaly:
            message = (
                f"{feature} is statistically unusual "
                f"(z-score={z_score:.2f})."
            )
        else:
            message = (
                f"{feature} is within the expected "
                "statistical range."
            )

        lower_bound = None
        upper_bound = None

        if standard_deviation > 0.0:
            lower_bound = (
                mean
                - threshold
                * standard_deviation
            )

            upper_bound = (
                mean
                + threshold
                * standard_deviation
            )

        return AnomalyResult(
            feature=feature,
            value=value,
            is_anomaly=is_anomaly,
            score=score,
            severity=severity,
            method=AnomalyMethod.Z_SCORE,
            z_score=z_score,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            expected_value=mean,
            message=message,
            metadata={
                "sample_count": len(
                    values_list
                ),
                "standard_deviation": (
                    standard_deviation
                ),
            },
        )

    # ========================================================
    # IQR
    # ========================================================

    def detect_iqr(
        self,
        value: float,
        values: Iterable[float],
        feature: str = "value",
    ) -> AnomalyResult:
        """
        Detect an anomaly using the interquartile range.
        """

        values_list = list(
            values
        )

        if len(
            values_list
        ) < self.config.minimum_samples:
            return AnomalyResult(
                feature=feature,
                value=value,
                is_anomaly=False,
                score=0.0,
                severity=AnomalySeverity.NORMAL,
                method=AnomalyMethod.IQR,
                expected_value=(
                    _mean(
                        values_list
                    )
                    if values_list
                    else None
                ),
                message=(
                    "Insufficient historical samples "
                    "for IQR detection."
                ),
            )

        q1 = _percentile(
            values_list,
            25.0,
        )

        q3 = _percentile(
            values_list,
            75.0,
        )

        iqr = q3 - q1

        lower_bound = (
            q1
            - self.config.iqr_multiplier
            * iqr
        )

        upper_bound = (
            q3
            + self.config.iqr_multiplier
            * iqr
        )

        is_anomaly = (
            value < lower_bound
            or value > upper_bound
        )

        if iqr <= 0.0:
            distance = 0.0

            if value < lower_bound:
                distance = (
                    lower_bound
                    - value
                )

            elif value > upper_bound:
                distance = (
                    value
                    - upper_bound
                )

            score = (
                1.0
                if distance > 0.0
                else 0.0
            )

        else:
            distance = max(
                0.0,
                lower_bound - value,
                value - upper_bound,
            )

            score = _clamp(
                distance
                / (
                    2.0
                    * iqr
                )
            )

            if is_anomaly:
                score = max(
                    score,
                    0.5,
                )

        severity = self._severity_from_score(
            score
        )

        if is_anomaly:
            message = (
                f"{feature} lies outside the "
                "interquartile range."
            )
        else:
            message = (
                f"{feature} lies within the "
                "interquartile range."
            )

        return AnomalyResult(
            feature=feature,
            value=value,
            is_anomaly=is_anomaly,
            score=score,
            severity=severity,
            method=AnomalyMethod.IQR,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            expected_value=_mean(
                values_list
            ),
            message=message,
            metadata={
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "sample_count": len(
                    values_list
                ),
            },
        )

    # ========================================================
    # ROLLING DETECTION
    # ========================================================

    def detect_rolling(
        self,
        value: float,
        history: Iterable[float],
        feature: str = "value",
    ) -> AnomalyResult:
        """
        Detect an anomaly against a rolling historical window.
        """

        history_list = list(
            history
        )

        if len(
            history_list
        ) < self.config.minimum_samples:
            return AnomalyResult(
                feature=feature,
                value=value,
                is_anomaly=False,
                score=0.0,
                severity=AnomalySeverity.NORMAL,
                method=AnomalyMethod.ROLLING,
                expected_value=(
                    _mean(
                        history_list
                    )
                    if history_list
                    else None
                ),
                message=(
                    "Insufficient historical samples "
                    "for rolling detection."
                ),
            )

        window = history_list[
            -self.config.rolling_window_size :
        ]

        result = self.detect_z_score(
            value,
            window,
            feature=feature,
        )

        result.method = (
            AnomalyMethod.ROLLING
        )

        result.message = (
            result.message
            + " Rolling-window analysis was used."
        )

        result.metadata[
            "window_size"
        ] = len(
            window
        )

        return result

    # ========================================================
    # COMBINED DETECTION
    # ========================================================

    def detect(
        self,
        value: Any,
        values: Iterable[Any],
        feature: str = "value",
        method: AnomalyMethod = AnomalyMethod.COMBINED,
    ) -> AnomalyResult:
        """
        Detect an anomaly using the selected method.
        """

        numeric_value = _to_float(
            value
        )

        if numeric_value is None:
            return AnomalyResult(
                feature=feature,
                value=0.0,
                is_anomaly=True,
                score=1.0,
                severity=AnomalySeverity.CRITICAL,
                method=method,
                message=(
                    f"{feature} contains a non-numeric "
                    "or non-finite value."
                ),
            )

        numeric_values = [
            numeric
            for item in values
            if (
                numeric := _to_float(
                    item
                )
            )
            is not None
        ]

        if method == AnomalyMethod.Z_SCORE:
            return self.detect_z_score(
                numeric_value,
                numeric_values,
                feature,
            )

        if method == AnomalyMethod.IQR:
            return self.detect_iqr(
                numeric_value,
                numeric_values,
                feature,
            )

        if method == AnomalyMethod.ROLLING:
            return self.detect_rolling(
                numeric_value,
                numeric_values,
                feature,
            )

        return self.detect_combined(
            numeric_value,
            numeric_values,
            feature,
        )

    def detect_combined(
        self,
        value: float,
        values: Iterable[float],
        feature: str = "value",
    ) -> AnomalyResult:
        """
        Combine z-score and IQR detection.

        A value is considered anomalous when either method finds
        strong evidence of an outlier.
        """

        values_list = list(
            values
        )

        z_result = self.detect_z_score(
            value,
            values_list,
            feature,
        )

        iqr_result = self.detect_iqr(
            value,
            values_list,
            feature,
        )

        score = max(
            z_result.score,
            iqr_result.score,
        )

        is_anomaly = (
            z_result.is_anomaly
            or iqr_result.is_anomaly
        )

        severity = self._severity_from_score(
            score
        )

        if is_anomaly:
            message = (
                f"{feature} was identified as an "
                "anomaly by combined statistical analysis."
            )
        else:
            message = (
                f"{feature} is within the expected "
                "statistical range."
            )

        return AnomalyResult(
            feature=feature,
            value=value,
            is_anomaly=is_anomaly,
            score=score,
            severity=severity,
            method=AnomalyMethod.COMBINED,
            z_score=z_result.z_score,
            lower_bound=z_result.lower_bound,
            upper_bound=z_result.upper_bound,
            expected_value=z_result.expected_value,
            message=message,
            metadata={
                "z_score_result": (
                    z_result.to_dict()
                ),
                "iqr_result": (
                    iqr_result.to_dict()
                ),
            },
        )

    # ========================================================
    # FEATURE-SPECIFIC DETECTION
    # ========================================================

    def detect_features(
        self,
        record: Mapping[str, Any],
        history: Mapping[str, Iterable[Any]],
        features: Iterable[str] | None = None,
        method: AnomalyMethod = AnomalyMethod.COMBINED,
    ) -> list[AnomalyResult]:
        """
        Detect anomalies across multiple features.

        ``history`` should contain historical values for each
        feature.
        """

        if features is None:
            features = [
                key
                for key, value in record.items()
                if _to_float(value) is not None
            ]

        results: list[AnomalyResult] = []

        for feature in features:
            if feature not in record:
                continue

            value = _to_float(
                record[feature]
            )

            if value is None:
                results.append(
                    AnomalyResult(
                        feature=feature,
                        value=0.0,
                        is_anomaly=True,
                        score=1.0,
                        severity=(
                            AnomalySeverity.CRITICAL
                        ),
                        method=method,
                        message=(
                            f"{feature} contains an "
                            "invalid numerical value."
                        ),
                    )
                )

                continue

            historical_values = history.get(
                feature,
                [],
            )

            results.append(
                self.detect(
                    value,
                    historical_values,
                    feature=feature,
                    method=method,
                )
            )

        return results

    # ========================================================
    # RECORD DETECTION
    # ========================================================

    def detect_record(
        self,
        record: Mapping[str, Any],
        history: Mapping[str, Iterable[Any]],
        record_index: int = 0,
        features: Iterable[str] | None = None,
        method: AnomalyMethod = AnomalyMethod.COMBINED,
    ) -> RecordAnomalyResult:
        """
        Detect anomalies in one telemetry record.
        """

        timestamp = record.get(
            "timestamp"
        )

        results = self.detect_features(
            record,
            history,
            features=features,
            method=method,
        )

        anomalous_results = [
            result
            for result in results
            if result.is_anomaly
        ]

        if anomalous_results:
            overall_score = max(
                result.score
                for result in anomalous_results
            )

        else:
            overall_score = 0.0

        severity = self._severity_from_score(
            overall_score
        )

        return RecordAnomalyResult(
            record_index=record_index,
            timestamp=timestamp,
            is_anomaly=bool(
                anomalous_results
            ),
            overall_score=overall_score,
            severity=severity,
            anomalies=anomalous_results,
            metadata={
                "features_checked": len(
                    results
                )
            },
        )

    # ========================================================
    # DATASET DETECTION
    # ========================================================

    def detect_dataset(
        self,
        records: Iterable[Mapping[str, Any]],
        features: Iterable[str] | None = None,
        method: AnomalyMethod = AnomalyMethod.COMBINED,
    ) -> DetectionReport:
        """
        Detect anomalies across an entire dataset.

        Historical values are automatically constructed from
        previous records, so each record is compared against the
        available historical observations.
        """

        record_list = list(
            records
        )

        report = DetectionReport(
            total_records=len(
                record_list
            )
        )

        if not record_list:
            return report

        # ----------------------------------------------------
        # Determine features.
        # ----------------------------------------------------

        if features is None:
            feature_set: set[str] = set()

            for record in record_list:
                for key, value in record.items():
                    if _to_float(value) is not None:
                        feature_set.add(
                            str(key)
                        )

            features_list = sorted(
                feature_set
            )

        else:
            features_list = [
                str(feature)
                for feature in features
            ]

        # ----------------------------------------------------
        # Build historical values progressively.
        # ----------------------------------------------------

        history: dict[
            str,
            list[float],
        ] = {
            feature: []
            for feature in features_list
        }

        for index, record in enumerate(
            record_list
        ):
            record_history = {
                feature: list(
                    history.get(
                        feature,
                        [],
                    )
                )
                for feature in features_list
            }

            result = self.detect_record(
                record,
                record_history,
                record_index=index,
                features=features_list,
                method=method,
            )

            report.results.append(
                result
            )

            if result.is_anomaly:
                report.anomalous_records += 1

                report.total_anomalies += (
                    result.anomaly_count
                )

            else:
                report.normal_records += 1

            # Add current observations to history only after
            # detection, so the current value does not contaminate
            # its own baseline.
            for feature in features_list:
                if feature not in record:
                    continue

                value = _to_float(
                    record[feature]
                )

                if value is None:
                    continue

                history[
                    feature
                ].append(
                    value
                )

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        report.feature_statistics = (
            self.calculate_feature_statistics(
                record_list,
                features_list,
            )
        )

        return report

    # ========================================================
    # STATISTICS
    # ========================================================

    def calculate_feature_statistics(
        self,
        records: Iterable[Mapping[str, Any]],
        features: Iterable[str],
    ) -> dict[
        str,
        dict[str, float],
    ]:
        """
        Calculate basic statistics for selected features.
        """

        record_list = list(
            records
        )

        statistics_result: dict[
            str,
            dict[str, float],
        ] = {}

        for feature in features:
            values: list[float] = []

            for record in record_list:
                if feature not in record:
                    continue

                value = _to_float(
                    record[feature]
                )

                if value is not None:
                    values.append(
                        value
                    )

            if not values:
                continue

            statistics_result[
                feature
            ] = {
                "count": float(
                    len(values)
                ),
                "mean": _mean(
                    values
                ),
                "minimum": min(
                    values
                ),
                "maximum": max(
                    values
                ),
                "standard_deviation": (
                    _standard_deviation(
                        values
                    )
                ),
                "q1": _percentile(
                    values,
                    25.0,
                ),
                "median": _percentile(
                    values,
                    50.0,
                ),
                "q3": _percentile(
                    values,
                    75.0,
                ),
            }

        return statistics_result

    # ========================================================
    # SCORING
    # ========================================================

    def _score_from_z_score(
        self,
        absolute_z_score: float,
    ) -> float:
        """
        Convert absolute z-score into a 0-1 anomaly score.
        """

        threshold = (
            self.config.z_score_threshold
        )

        if absolute_z_score <= threshold:
            return _clamp(
                absolute_z_score
                / max(
                    threshold,
                    0.1,
                )
                * 0.5
            )

        excess = (
            absolute_z_score
            - threshold
        )

        scale = max(
            self.config.critical_z_score_threshold
            - threshold,
            0.1,
        )

        return _clamp(
            0.5
            + (
                excess
                / scale
            )
            * 0.5
        )

    def _severity_from_score(
        self,
        score: float,
    ) -> AnomalySeverity:
        """
        Convert an anomaly score to severity.
        """

        score = _clamp(
            score
        )

        if score >= (
            self.config.critical_score_threshold
        ):
            return AnomalySeverity.CRITICAL

        if score >= (
            self.config.high_score_threshold
        ):
            return AnomalySeverity.HIGH

        if score >= (
            self.config.medium_score_threshold
        ):
            return AnomalySeverity.MEDIUM

        if score >= (
            self.config.low_score_threshold
        ):
            return AnomalySeverity.LOW

        return AnomalySeverity.NORMAL


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def detect_anomaly(
    value: Any,
    values: Iterable[Any],
    feature: str = "value",
    method: AnomalyMethod = AnomalyMethod.COMBINED,
    config: AnomalyConfig | None = None,
) -> AnomalyResult:
    """
    Convenience function for detecting one anomaly.
    """

    detector = AnomalyDetector(
        config=config
    )

    return detector.detect(
        value=value,
        values=values,
        feature=feature,
        method=method,
    )


def detect_dataset_anomalies(
    records: Iterable[Mapping[str, Any]],
    features: Iterable[str] | None = None,
    method: AnomalyMethod = AnomalyMethod.COMBINED,
    config: AnomalyConfig | None = None,
) -> DetectionReport:
    """
    Convenience function for detecting anomalies in a dataset.
    """

    detector = AnomalyDetector(
        config=config
    )

    return detector.detect_dataset(
        records=records,
        features=features,
        method=method,
    )


def calculate_z_score(
    value: float,
    values: Iterable[float],
) -> float:
    """
    Convenience function for calculating a z-score.
    """

    detector = AnomalyDetector()

    return detector.calculate_z_score(
        value,
        values,
    )


# ============================================================
# COMMON GRID FEATURE HELPERS
# ============================================================


def detect_grid_anomalies(
    records: Iterable[Mapping[str, Any]],
    config: AnomalyConfig | None = None,
) -> DetectionReport:
    """
    Detect anomalies in common electrical-grid measurements.

    Supported fields include:

    - voltage
    - voltage_kv
    - current
    - current_a
    - frequency_hz
    - demand_mw
    - generation_mw
    - active_power_mw
    - reactive_power_mvar
    - temperature_c
    - power_factor
    """

    grid_features = (
        "voltage",
        "voltage_kv",
        "current",
        "current_a",
        "frequency_hz",
        "demand_mw",
        "generation_mw",
        "active_power_mw",
        "reactive_power_mvar",
        "temperature_c",
        "power_factor",
    )

    detector = AnomalyDetector(
        config=config
    )

    return detector.detect_dataset(
        records,
        features=grid_features,
        method=AnomalyMethod.COMBINED,
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "AnomalyMethod",
    "AnomalySeverity",
    "AnomalyConfig",
    "AnomalyResult",
    "RecordAnomalyResult",
    "DetectionReport",
    "AnomalyDetector",
    "detect_anomaly",
    "detect_dataset_anomalies",
    "calculate_z_score",
    "detect_grid_anomalies",
]