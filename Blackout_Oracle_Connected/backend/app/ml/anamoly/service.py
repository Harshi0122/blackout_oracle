"""
Blackout Oracle - Anomaly Detection Service.

Provides the application-level service responsible for running
anomaly detection on electrical-grid telemetry.

Responsibilities:

- Prepare historical observations
- Run anomaly detection
- Analyze individual telemetry records
- Analyze batches of records
- Produce structured anomaly summaries
- Identify the most important anomalous measurements

This service does not directly access the database, external APIs,
or grid-control systems.

The service uses the statistical detector from:

    app.ml.anamoly.detector
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from app.ml.anamoly.detector import (
    AnomalyConfig,
    AnomalyDetector,
    AnomalyMethod,
    AnomalyResult,
    AnomalySeverity,
    DetectionReport,
    RecordAnomalyResult,
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_FEATURES: tuple[str, ...] = (
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

DEFAULT_METHOD = AnomalyMethod.COMBINED

DEFAULT_TOP_ANOMALIES = 10


# ============================================================
# SERVICE RESULT
# ============================================================


@dataclass
class AnomalyServiceResult:
    """
    Application-level result returned by the anomaly service.
    """

    success: bool = True

    message: str = ""

    report: DetectionReport | None = None

    important_anomalies: list[RecordAnomalyResult] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def anomaly_count(self) -> int:
        """Return the number of anomalous records."""

        if self.report is None:
            return 0

        return self.report.anomalous_records

    @property
    def total_records(self) -> int:
        """Return the number of processed records."""

        if self.report is None:
            return 0

        return self.report.total_records

    @property
    def anomaly_rate(self) -> float:
        """Return the fraction of anomalous records."""

        if self.report is None:
            return 0.0

        return self.report.anomaly_rate

    def to_dict(self) -> dict[str, Any]:
        """Convert the service result into a dictionary."""

        return {
            "success": self.success,
            "message": self.message,
            "total_records": self.total_records,
            "anomaly_count": self.anomaly_count,
            "anomaly_rate": self.anomaly_rate,
            "report": (
                self.report.to_dict()
                if self.report is not None
                else None
            ),
            "important_anomalies": [
                anomaly.to_dict()
                for anomaly in self.important_anomalies
            ],
            "metadata": dict(self.metadata),
        }


# ============================================================
# SERVICE
# ============================================================


class AnomalyDetectionService:
    """
    High-level anomaly detection service.

    This class provides a stable application interface around the
    lower-level AnomalyDetector.

    Other parts of Blackout Oracle should preferably use this
    service instead of directly implementing anomaly-detection
    logic.
    """

    def __init__(
        self,
        detector: AnomalyDetector | None = None,
        config: AnomalyConfig | None = None,
    ) -> None:
        """
        Initialize the anomaly detection service.
        """

        if detector is not None:
            self.detector = detector

        else:
            self.detector = AnomalyDetector(
                config=config
            )

    # ========================================================
    # SINGLE VALUE
    # ========================================================

    def analyze_value(
        self,
        value: Any,
        historical_values: Iterable[Any],
        *,
        feature: str = "value",
        method: AnomalyMethod = DEFAULT_METHOD,
    ) -> AnomalyResult:
        """
        Analyze one measurement against historical values.
        """

        return self.detector.detect(
            value=value,
            values=historical_values,
            feature=feature,
            method=method,
        )

    # ========================================================
    # SINGLE RECORD
    # ========================================================

    def analyze_record(
        self,
        record: Mapping[str, Any],
        history: Mapping[str, Iterable[Any]],
        *,
        record_index: int = 0,
        features: Iterable[str] | None = None,
        method: AnomalyMethod = DEFAULT_METHOD,
    ) -> RecordAnomalyResult:
        """
        Analyze one telemetry record.

        ``history`` contains historical values for each feature.
        """

        selected_features = (
            tuple(features)
            if features is not None
            else DEFAULT_FEATURES
        )

        return self.detector.detect_record(
            record=record,
            history=history,
            record_index=record_index,
            features=selected_features,
            method=method,
        )

    # ========================================================
    # DATASET
    # ========================================================

    def analyze_dataset(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        features: Iterable[str] | None = None,
        method: AnomalyMethod = DEFAULT_METHOD,
        top_n: int = DEFAULT_TOP_ANOMALIES,
    ) -> AnomalyServiceResult:
        """
        Analyze a complete telemetry dataset.
        """

        record_list = list(
            records
        )

        selected_features = (
            tuple(features)
            if features is not None
            else DEFAULT_FEATURES
        )

        try:
            report = self.detector.detect_dataset(
                records=record_list,
                features=selected_features,
                method=method,
            )

        except Exception as exc:
            return AnomalyServiceResult(
                success=False,
                message=(
                    "Anomaly detection failed."
                ),
                metadata={
                    "error": str(exc),
                    "exception_type": type(
                        exc
                    ).__name__,
                },
            )

        important = self.get_important_anomalies(
            report,
            top_n=top_n,
        )

        return AnomalyServiceResult(
            success=True,
            message=(
                "Anomaly detection completed successfully."
            ),
            report=report,
            important_anomalies=important,
            metadata={
                "features": list(
                    selected_features
                ),
                "method": method.value,
            },
        )

    # ========================================================
    # GRID TELEMETRY
    # ========================================================

    def analyze_grid_telemetry(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        top_n: int = DEFAULT_TOP_ANOMALIES,
    ) -> AnomalyServiceResult:
        """
        Analyze common electrical-grid telemetry fields.

        This is the preferred method for normal Blackout Oracle
        grid telemetry.
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

        return self.analyze_dataset(
            records,
            features=grid_features,
            method=AnomalyMethod.COMBINED,
            top_n=top_n,
        )

    # ========================================================
    # FEATURE ANALYSIS
    # ========================================================

    def analyze_feature(
        self,
        records: Iterable[Mapping[str, Any]],
        feature: str,
        *,
        method: AnomalyMethod = DEFAULT_METHOD,
        top_n: int = DEFAULT_TOP_ANOMALIES,
    ) -> AnomalyServiceResult:
        """
        Analyze one specific feature across a dataset.
        """

        return self.analyze_dataset(
            records,
            features=(feature,),
            method=method,
            top_n=top_n,
        )

    # ========================================================
    # IMPORTANT ANOMALIES
    # ========================================================

    @staticmethod
    def get_important_anomalies(
        report: DetectionReport,
        *,
        top_n: int = DEFAULT_TOP_ANOMALIES,
    ) -> list[RecordAnomalyResult]:
        """
        Return the most significant anomalous records.

        Records are ranked by overall anomaly score.
        """

        top_n = max(
            0,
            int(top_n),
        )

        anomalies = [
            result
            for result in report.results
            if result.is_anomaly
        ]

        anomalies.sort(
            key=lambda result: (
                result.overall_score,
                result.anomaly_count,
            ),
            reverse=True,
        )

        return anomalies[
            :top_n
        ]

    # ========================================================
    # CRITICAL ANOMALIES
    # ========================================================

    @staticmethod
    def get_critical_anomalies(
        report: DetectionReport,
    ) -> list[RecordAnomalyResult]:
        """
        Return only critical anomalies.
        """

        return [
            result
            for result in report.results
            if result.severity
            == AnomalySeverity.CRITICAL
        ]

    # ========================================================
    # HIGH-SEVERITY ANOMALIES
    # ========================================================

    @staticmethod
    def get_high_priority_anomalies(
        report: DetectionReport,
    ) -> list[RecordAnomalyResult]:
        """
        Return high and critical anomalies.
        """

        priority_levels = {
            AnomalySeverity.HIGH,
            AnomalySeverity.CRITICAL,
        }

        return [
            result
            for result in report.results
            if result.severity
            in priority_levels
        ]

    # ========================================================
    # FEATURE SUMMARY
    # ========================================================

    @staticmethod
    def summarize_features(
        report: DetectionReport,
    ) -> dict[str, dict[str, Any]]:
        """
        Summarize anomaly activity by feature.
        """

        summary: dict[
            str,
            dict[str, Any],
        ] = {}

        for result in report.results:
            for anomaly in result.anomalies:
                feature = anomaly.feature

                if feature not in summary:
                    summary[feature] = {
                        "anomaly_count": 0,
                        "maximum_score": 0.0,
                        "maximum_severity": (
                            AnomalySeverity.NORMAL.value
                        ),
                    }

                summary[
                    feature
                ]["anomaly_count"] += 1

                summary[
                    feature
                ]["maximum_score"] = max(
                    summary[
                        feature
                    ]["maximum_score"],
                    anomaly.score,
                )

                current_severity = (
                    summary[
                        feature
                    ]["maximum_severity"]
                )

                if self_severity_rank(
                    anomaly.severity
                ) > self_severity_rank(
                    AnomalySeverity(
                        current_severity
                    )
                ):
                    summary[
                        feature
                    ]["maximum_severity"] = (
                        anomaly.severity.value
                    )

        return summary

    # ========================================================
    # SEVERITY SUMMARY
    # ========================================================

    @staticmethod
    def summarize_severity(
        report: DetectionReport,
    ) -> dict[str, int]:
        """
        Count anomalous records by severity.
        """

        summary = {
            AnomalySeverity.NORMAL.value: 0,
            AnomalySeverity.LOW.value: 0,
            AnomalySeverity.MEDIUM.value: 0,
            AnomalySeverity.HIGH.value: 0,
            AnomalySeverity.CRITICAL.value: 0,
        }

        for result in report.results:
            severity = result.severity.value

            if severity in summary:
                summary[
                    severity
                ] += 1

        return summary

    # ========================================================
    # ALERT CANDIDATES
    # ========================================================

    @staticmethod
    def get_alert_candidates(
        report: DetectionReport,
        *,
        minimum_severity: AnomalySeverity = AnomalySeverity.HIGH,
    ) -> list[RecordAnomalyResult]:
        """
        Return anomalies that may warrant incident/alert
        processing.

        This method does NOT create an alert itself. It only
        identifies candidates for the incident-management layer.
        """

        minimum_rank = self_severity_rank(
            minimum_severity
        )

        return [
            result
            for result in report.results
            if (
                result.is_anomaly
                and self_severity_rank(
                    result.severity
                )
                >= minimum_rank
            )
        ]

    # ========================================================
    # HEALTH SUMMARY
    # ========================================================

    @staticmethod
    def health_summary(
        report: DetectionReport,
    ) -> dict[str, Any]:
        """
        Produce a compact health summary for dashboards.
        """

        critical_count = len(
            AnomalyDetectionService.get_critical_anomalies(
                report
            )
        )

        high_count = len(
            AnomalyDetectionService.get_high_priority_anomalies(
                report
            )
        )

        if critical_count > 0:
            status = "critical"

        elif high_count > 0:
            status = "warning"

        elif report.anomalous_records > 0:
            status = "attention"

        else:
            status = "normal"

        return {
            "status": status,
            "total_records": report.total_records,
            "anomalous_records": (
                report.anomalous_records
            ),
            "normal_records": (
                report.normal_records
            ),
            "total_anomalies": (
                report.total_anomalies
            ),
            "anomaly_rate": (
                report.anomaly_rate
            ),
            "critical_anomalies": (
                critical_count
            ),
            "high_priority_anomalies": (
                high_count
            ),
        }


# ============================================================
# SEVERITY HELPERS
# ============================================================


def self_severity_rank(
    severity: AnomalySeverity,
) -> int:
    """
    Return a numeric rank for anomaly severity.
    """

    ranks = {
        AnomalySeverity.NORMAL: 0,
        AnomalySeverity.LOW: 1,
        AnomalySeverity.MEDIUM: 2,
        AnomalySeverity.HIGH: 3,
        AnomalySeverity.CRITICAL: 4,
    }

    return ranks.get(
        severity,
        0,
    )


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def analyze_anomalies(
    records: Iterable[Mapping[str, Any]],
    *,
    features: Iterable[str] | None = None,
    method: AnomalyMethod = DEFAULT_METHOD,
    config: AnomalyConfig | None = None,
    top_n: int = DEFAULT_TOP_ANOMALIES,
) -> AnomalyServiceResult:
    """
    Convenience function for dataset anomaly analysis.
    """

    service = AnomalyDetectionService(
        config=config
    )

    return service.analyze_dataset(
        records,
        features=features,
        method=method,
        top_n=top_n,
    )


def analyze_grid_telemetry(
    records: Iterable[Mapping[str, Any]],
    *,
    config: AnomalyConfig | None = None,
    top_n: int = DEFAULT_TOP_ANOMALIES,
) -> AnomalyServiceResult:
    """
    Convenience function for grid telemetry analysis.
    """

    service = AnomalyDetectionService(
        config=config
    )

    return service.analyze_grid_telemetry(
        records,
        top_n=top_n,
    )


def get_alert_candidates(
    report: DetectionReport,
    *,
    minimum_severity: AnomalySeverity = AnomalySeverity.HIGH,
) -> list[RecordAnomalyResult]:
    """
    Convenience function for obtaining alert candidates.
    """

    return AnomalyDetectionService.get_alert_candidates(
        report,
        minimum_severity=minimum_severity,
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "AnomalyServiceResult",
    "AnomalyDetectionService",
    "analyze_anomalies",
    "analyze_grid_telemetry",
    "get_alert_candidates",
]