"""
Blackout Oracle - Data Quality Module.

Provides data-quality checks for grid telemetry, weather data,
historical observations, and other normalized ingestion records.

The quality layer is responsible for:

- Checking required fields
- Detecting missing values
- Detecting invalid numeric values
- Detecting physically unreasonable values
- Detecting duplicate timestamps
- Detecting timestamp ordering problems
- Detecting stale data
- Calculating a quality score
- Producing a structured quality report

This module does not modify the source data and does not send
commands to grid equipment.

Only Python standard-library modules are used.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_SOURCE = "unknown"

DEFAULT_STALE_THRESHOLD_SECONDS = 300

DEFAULT_DUPLICATE_THRESHOLD = 1

DEFAULT_MIN_FREQUENCY_HZ = 40.0
DEFAULT_MAX_FREQUENCY_HZ = 70.0

DEFAULT_MIN_POWER_FACTOR = 0.0
DEFAULT_MAX_POWER_FACTOR = 1.0

DEFAULT_MAX_REASONABLE_VOLTAGE_KV = 1500.0

DEFAULT_MAX_REASONABLE_CURRENT_A = 500000.0

DEFAULT_MAX_REASONABLE_POWER_MW = 100000.0

DEFAULT_MAX_REASONABLE_TEMPERATURE_C = 150.0


# ============================================================
# ENUMS
# ============================================================


class QualityLevel(str, Enum):
    """
    Overall quality classification.
    """

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INVALID = "invalid"


class QualityIssueType(str, Enum):
    """
    Types of data-quality issues.
    """

    MISSING = "missing"
    INVALID = "invalid"
    OUT_OF_RANGE = "out_of_range"
    DUPLICATE = "duplicate"
    OUT_OF_ORDER = "out_of_order"
    STALE = "stale"
    NON_FINITE = "non_finite"
    INCONSISTENT = "inconsistent"


# ============================================================
# DATA CLASSES
# ============================================================


@dataclass
class QualityIssue:
    """
    Represents one data-quality issue.
    """

    issue_type: QualityIssueType

    message: str

    field: str | None = None

    record_index: int | None = None

    severity: str = "warning"

    value: Any = None

    details: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert the issue into a dictionary.
        """
        return {
            "issue_type": self.issue_type.value,
            "message": self.message,
            "field": self.field,
            "record_index": self.record_index,
            "severity": self.severity,
            "value": self.value,
            "details": dict(
                self.details
            ),
        }


@dataclass
class QualityReport:
    """
    Complete data-quality report.
    """

    source: str = DEFAULT_SOURCE

    total_records: int = 0

    valid_records: int = 0

    invalid_records: int = 0

    missing_value_count: int = 0

    invalid_value_count: int = 0

    out_of_range_count: int = 0

    duplicate_count: int = 0

    out_of_order_count: int = 0

    stale_count: int = 0

    non_finite_count: int = 0

    inconsistent_count: int = 0

    quality_score: float = 0.0

    quality_level: QualityLevel = (
        QualityLevel.INVALID
    )

    issues: list[QualityIssue] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    generated_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    @property
    def has_issues(
        self,
    ) -> bool:
        """
        Return True when any quality issue exists.
        """
        return bool(
            self.issues
        )

    @property
    def is_acceptable(
        self,
    ) -> bool:
        """
        Return True when quality is at least fair.
        """
        return self.quality_level in {
            QualityLevel.EXCELLENT,
            QualityLevel.GOOD,
            QualityLevel.FAIR,
        }

    def add_issue(
        self,
        issue: QualityIssue,
    ) -> None:
        """
        Add an issue and update its corresponding counter.
        """
        self.issues.append(
            issue
        )

        if issue.issue_type == QualityIssueType.MISSING:
            self.missing_value_count += 1

        elif issue.issue_type == QualityIssueType.INVALID:
            self.invalid_value_count += 1

        elif issue.issue_type == QualityIssueType.OUT_OF_RANGE:
            self.out_of_range_count += 1

        elif issue.issue_type == QualityIssueType.DUPLICATE:
            self.duplicate_count += 1

        elif issue.issue_type == QualityIssueType.OUT_OF_ORDER:
            self.out_of_order_count += 1

        elif issue.issue_type == QualityIssueType.STALE:
            self.stale_count += 1

        elif issue.issue_type == QualityIssueType.NON_FINITE:
            self.non_finite_count += 1

        elif issue.issue_type == QualityIssueType.INCONSISTENT:
            self.inconsistent_count += 1

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert the report into a JSON-compatible dictionary.
        """
        return {
            "source": self.source,
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "missing_value_count": (
                self.missing_value_count
            ),
            "invalid_value_count": (
                self.invalid_value_count
            ),
            "out_of_range_count": (
                self.out_of_range_count
            ),
            "duplicate_count": self.duplicate_count,
            "out_of_order_count": (
                self.out_of_order_count
            ),
            "stale_count": self.stale_count,
            "non_finite_count": (
                self.non_finite_count
            ),
            "inconsistent_count": (
                self.inconsistent_count
            ),
            "quality_score": self.quality_score,
            "quality_level": (
                self.quality_level.value
            ),
            "has_issues": self.has_issues,
            "is_acceptable": self.is_acceptable,
            "issues": [
                issue.to_dict()
                for issue in self.issues
            ],
            "metadata": dict(
                self.metadata
            ),
            "generated_at": (
                self.generated_at.isoformat()
            ),
        }


@dataclass
class QualityConfig:
    """
    Configuration for data-quality checks.
    """

    required_fields: tuple[str, ...] = (
        "timestamp",
    )

    stale_threshold_seconds: int = (
        DEFAULT_STALE_THRESHOLD_SECONDS
    )

    min_frequency_hz: float = (
        DEFAULT_MIN_FREQUENCY_HZ
    )

    max_frequency_hz: float = (
        DEFAULT_MAX_FREQUENCY_HZ
    )

    min_power_factor: float = (
        DEFAULT_MIN_POWER_FACTOR
    )

    max_power_factor: float = (
        DEFAULT_MAX_POWER_FACTOR
    )

    max_reasonable_voltage_kv: float = (
        DEFAULT_MAX_REASONABLE_VOLTAGE_KV
    )

    max_reasonable_current_a: float = (
        DEFAULT_MAX_REASONABLE_CURRENT_A
    )

    max_reasonable_power_mw: float = (
        DEFAULT_MAX_REASONABLE_POWER_MW
    )

    max_reasonable_temperature_c: float = (
        DEFAULT_MAX_REASONABLE_TEMPERATURE_C
    )

    detect_duplicates: bool = True

    detect_ordering: bool = True

    detect_stale_data: bool = True

    check_physical_ranges: bool = True

    def __post_init__(
        self,
    ) -> None:
        """
        Normalize configuration values.
        """
        self.stale_threshold_seconds = max(
            0,
            int(
                self.stale_threshold_seconds
            ),
        )

        self.min_frequency_hz = float(
            self.min_frequency_hz
        )

        self.max_frequency_hz = float(
            self.max_frequency_hz
        )

        self.min_power_factor = float(
            self.min_power_factor
        )

        self.max_power_factor = float(
            self.max_power_factor
        )

        self.max_reasonable_voltage_kv = max(
            0.0,
            float(
                self.max_reasonable_voltage_kv
            ),
        )

        self.max_reasonable_current_a = max(
            0.0,
            float(
                self.max_reasonable_current_a
            ),
        )

        self.max_reasonable_power_mw = max(
            0.0,
            float(
                self.max_reasonable_power_mw
            ),
        )

        self.max_reasonable_temperature_c = (
            float(
                self.max_reasonable_temperature_c
            )
        )


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def utc_now() -> datetime:
    """
    Return the current timezone-aware UTC timestamp.
    """
    return datetime.now(
        timezone.utc
    )


def _normalize_key(
    key: Any,
) -> str:
    """
    Normalize a field name.
    """
    return (
        str(
            key
        )
        .strip()
        .lower()
        .replace(
            "-",
            "_",
        )
        .replace(
            " ",
            "_",
        )
    )


def _normalize_mapping(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Normalize the keys of a record.
    """
    return {
        _normalize_key(key): value
        for key, value in record.items()
    }


def _parse_timestamp(
    value: Any,
) -> datetime | None:
    """
    Convert a timestamp into a timezone-aware UTC datetime.
    """
    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        timestamp = value

    elif isinstance(
        value,
        (int, float),
    ):
        numeric = float(
            value
        )

        if abs(numeric) > 10_000_000_000:
            numeric /= 1000.0

        try:
            timestamp = datetime.fromtimestamp(
                numeric,
                tz=timezone.utc,
            )
        except (
            OverflowError,
            OSError,
            ValueError,
        ):
            return None

    else:
        text = str(
            value
        ).strip()

        if not text:
            return None

        if text.endswith(
            "Z"
        ):
            text = (
                text[:-1]
                + "+00:00"
            )

        try:
            timestamp = datetime.fromisoformat(
                text
            )
        except ValueError:
            formats = (
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%d-%m-%Y %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
                "%Y-%m-%d",
                "%d-%m-%Y",
                "%d/%m/%Y",
            )

            timestamp = None

            for fmt in formats:
                try:
                    timestamp = datetime.strptime(
                        text,
                        fmt,
                    )
                    break
                except ValueError:
                    continue

            if timestamp is None:
                return None

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(
            tzinfo=timezone.utc
        )

    return timestamp.astimezone(
        timezone.utc
    )


def _numeric_value(
    value: Any,
) -> float | None:
    """
    Convert a value to float when possible.
    """
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

    return result


# ============================================================
# DATA QUALITY CHECKER
# ============================================================


class DataQualityChecker:
    """
    Performs data-quality checks on normalized records.
    """

    def __init__(
        self,
        config: QualityConfig | None = None,
        source: str = DEFAULT_SOURCE,
    ) -> None:
        """
        Initialize the quality checker.
        """
        self.config = (
            config
            if config is not None
            else QualityConfig()
        )

        self.source = str(
            source
        )

    # ========================================================
    # SINGLE RECORD
    # ========================================================

    def check_record(
        self,
        record: Mapping[str, Any],
        record_index: int | None = None,
    ) -> list[QualityIssue]:
        """
        Check a single record for quality problems.
        """
        if not isinstance(
            record,
            Mapping,
        ):
            return [
                QualityIssue(
                    issue_type=(
                        QualityIssueType.INVALID
                    ),
                    message=(
                        "Record must be a mapping."
                    ),
                    record_index=record_index,
                    severity="error",
                    value=record,
                )
            ]

        data = _normalize_mapping(
            record
        )

        issues: list[QualityIssue] = []

        # ----------------------------------------------------
        # Required fields
        # ----------------------------------------------------

        for required_field in self.config.required_fields:
            field_name = _normalize_key(
                required_field
            )

            if field_name not in data:
                issues.append(
                    QualityIssue(
                        issue_type=(
                            QualityIssueType.MISSING
                        ),
                        message=(
                            f"Required field "
                            f"'{field_name}' is missing."
                        ),
                        field=field_name,
                        record_index=record_index,
                        severity="error",
                    )
                )

                continue

            value = data[
                field_name
            ]

            if value is None or (
                isinstance(
                    value,
                    str,
                )
                and not value.strip()
            ):
                issues.append(
                    QualityIssue(
                        issue_type=(
                            QualityIssueType.MISSING
                        ),
                        message=(
                            f"Required field "
                            f"'{field_name}' is empty."
                        ),
                        field=field_name,
                        record_index=record_index,
                        severity="error",
                        value=value,
                    )
                )

        # ----------------------------------------------------
        # Timestamp
        # ----------------------------------------------------

        if "timestamp" in data:
            timestamp = _parse_timestamp(
                data["timestamp"]
            )

            if timestamp is None:
                issues.append(
                    QualityIssue(
                        issue_type=(
                            QualityIssueType.INVALID
                        ),
                        message=(
                            "Timestamp is invalid."
                        ),
                        field="timestamp",
                        record_index=record_index,
                        severity="error",
                        value=data["timestamp"],
                    )
                )

        # ----------------------------------------------------
        # Numeric fields
        # ----------------------------------------------------

        numeric_fields = (
            "demand_mw",
            "generation_mw",
            "available_power_mw",
            "voltage",
            "voltage_kv",
            "current",
            "current_a",
            "frequency_hz",
            "temperature_c",
            "power_factor",
            "active_power_mw",
            "reactive_power_mvar",
            "renewable_generation_mw",
            "wind_generation_mw",
            "solar_generation_mw",
            "hydro_generation_mw",
            "thermal_generation_mw",
            "exchange_mw",
            "shortage_mw",
            "surplus_mw",
        )

        for field_name in numeric_fields:
            if field_name not in data:
                continue

            value = data[
                field_name
            ]

            if value is None:
                continue

            numeric = _numeric_value(
                value
            )

            if numeric is None:
                issues.append(
                    QualityIssue(
                        issue_type=(
                            QualityIssueType.INVALID
                        ),
                        message=(
                            f"Field '{field_name}' "
                            "must be numeric."
                        ),
                        field=field_name,
                        record_index=record_index,
                        severity="error",
                        value=value,
                    )
                )

                continue

            if not math.isfinite(
                numeric
            ):
                issues.append(
                    QualityIssue(
                        issue_type=(
                            QualityIssueType.NON_FINITE
                        ),
                        message=(
                            f"Field '{field_name}' "
                            "contains a non-finite value."
                        ),
                        field=field_name,
                        record_index=record_index,
                        severity="error",
                        value=value,
                    )
                )

        # ----------------------------------------------------
        # Physical ranges
        # ----------------------------------------------------

        if self.config.check_physical_ranges:
            self._check_physical_ranges(
                data,
                record_index,
                issues,
            )

        # ----------------------------------------------------
        # Internal consistency
        # ----------------------------------------------------

        self._check_consistency(
            data,
            record_index,
            issues,
        )

        return issues

    # ========================================================
    # PHYSICAL RANGE CHECKS
    # ========================================================

    def _check_physical_ranges(
        self,
        data: Mapping[str, Any],
        record_index: int | None,
        issues: list[QualityIssue],
    ) -> None:
        """
        Check for physically unreasonable values.
        """

        # ----------------------------------------------------
        # Frequency
        # ----------------------------------------------------

        if "frequency_hz" in data:
            value = _numeric_value(
                data["frequency_hz"]
            )

            if (
                value is not None
                and (
                    value
                    < self.config.min_frequency_hz
                    or value
                    > self.config.max_frequency_hz
                )
            ):
                issues.append(
                    QualityIssue(
                        issue_type=(
                            QualityIssueType.OUT_OF_RANGE
                        ),
                        message=(
                            "Grid frequency is outside "
                            "the configured quality range."
                        ),
                        field="frequency_hz",
                        record_index=record_index,
                        severity="warning",
                        value=value,
                        details={
                            "minimum": (
                                self.config.min_frequency_hz
                            ),
                            "maximum": (
                                self.config.max_frequency_hz
                            ),
                        },
                    )
                )

        # ----------------------------------------------------
        # Power factor
        # ----------------------------------------------------

        if "power_factor" in data:
            value = _numeric_value(
                data["power_factor"]
            )

            if (
                value is not None
                and (
                    value
                    < self.config.min_power_factor
                    or value
                    > self.config.max_power_factor
                )
            ):
                issues.append(
                    QualityIssue(
                        issue_type=(
                            QualityIssueType.OUT_OF_RANGE
                        ),
                        message=(
                            "Power factor is outside "
                            "the configured range."
                        ),
                        field="power_factor",
                        record_index=record_index,
                        severity="warning",
                        value=value,
                    )
                )

        # ----------------------------------------------------
        # Voltage
        # ----------------------------------------------------

        voltage_field = None

        if "voltage_kv" in data:
            voltage_field = "voltage_kv"

        elif "voltage" in data:
            voltage_field = "voltage"

        if voltage_field is not None:
            value = _numeric_value(
                data[voltage_field]
            )

            if (
                value is not None
                and (
                    value < 0.0
                    or value
                    > self.config.max_reasonable_voltage_kv
                )
            ):
                issues.append(
                    QualityIssue(
                        issue_type=(
                            QualityIssueType.OUT_OF_RANGE
                        ),
                        message=(
                            "Voltage is outside "
                            "the configured physical range."
                        ),
                        field=voltage_field,
                        record_index=record_index,
                        severity="warning",
                        value=value,
                    )
                )

        # ----------------------------------------------------
        # Current
        # ----------------------------------------------------

        current_field = None

        if "current_a" in data:
            current_field = "current_a"

        elif "current" in data:
            current_field = "current"

        if current_field is not None:
            value = _numeric_value(
                data[current_field]
            )

            if (
                value is not None
                and (
                    value < 0.0
                    or value
                    > self.config.max_reasonable_current_a
                )
            ):
                issues.append(
                    QualityIssue(
                        issue_type=(
                            QualityIssueType.OUT_OF_RANGE
                        ),
                        message=(
                            "Current is outside "
                            "the configured physical range."
                        ),
                        field=current_field,
                        record_index=record_index,
                        severity="warning",
                        value=value,
                    )
                )

        # ----------------------------------------------------
        # Power
        # ----------------------------------------------------

        power_fields = (
            "demand_mw",
            "generation_mw",
            "available_power_mw",
            "active_power_mw",
            "reactive_power_mvar",
        )

        for field_name in power_fields:
            if field_name not in data:
                continue

            value = _numeric_value(
                data[field_name]
            )

            if value is None:
                continue

            if (
                value < 0.0
                or value
                > self.config.max_reasonable_power_mw
            ):
                issues.append(
                    QualityIssue(
                        issue_type=(
                            QualityIssueType.OUT_OF_RANGE
                        ),
                        message=(
                            f"Field '{field_name}' "
                            "is outside the configured "
                            "physical range."
                        ),
                        field=field_name,
                        record_index=record_index,
                        severity="warning",
                        value=value,
                    )
                )

        # ----------------------------------------------------
        # Temperature
        # ----------------------------------------------------

        if "temperature_c" in data:
            value = _numeric_value(
                data["temperature_c"]
            )

            if (
                value is not None
                and (
                    value < -100.0
                    or value
                    > self.config.max_reasonable_temperature_c
                )
            ):
                issues.append(
                    QualityIssue(
                        issue_type=(
                            QualityIssueType.OUT_OF_RANGE
                        ),
                        message=(
                            "Temperature is outside "
                            "the configured physical range."
                        ),
                        field="temperature_c",
                        record_index=record_index,
                        severity="warning",
                        value=value,
                    )
                )

    # ========================================================
    # CONSISTENCY CHECKS
    # ========================================================

    def _check_consistency(
        self,
        data: Mapping[str, Any],
        record_index: int | None,
        issues: list[QualityIssue],
    ) -> None:
        """
        Check relationships between related measurements.
        """

        demand = _numeric_value(
            data.get(
                "demand_mw"
            )
        )

        generation = _numeric_value(
            data.get(
                "generation_mw"
            )
        )

        available = _numeric_value(
            data.get(
                "available_power_mw"
            )
        )

        # Available power should normally not be dramatically
        # lower than generation when both are reported.
        if (
            available is not None
            and generation is not None
            and generation > available
        ):
            issues.append(
                QualityIssue(
                    issue_type=(
                        QualityIssueType.INCONSISTENT
                    ),
                    message=(
                        "Generation exceeds reported "
                        "available power."
                    ),
                    field="generation_mw",
                    record_index=record_index,
                    severity="warning",
                    value=generation,
                    details={
                        "available_power_mw": available
                    },
                )
            )

        # A negative generation-demand balance is not inherently
        # a quality problem, so it is intentionally NOT flagged.
        #
        # Demand can legitimately exceed local generation when
        # power is imported from elsewhere.

        if (
            demand is not None
            and demand < 0.0
        ):
            issues.append(
                QualityIssue(
                    issue_type=(
                        QualityIssueType.OUT_OF_RANGE
                    ),
                    message=(
                        "Demand cannot be negative."
                    ),
                    field="demand_mw",
                    record_index=record_index,
                    severity="error",
                    value=demand,
                )
            )

    # ========================================================
    # BATCH CHECK
    # ========================================================

    def check_records(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        reference_time: datetime | None = None,
    ) -> QualityReport:
        """
        Run all quality checks on a collection of records.
        """
        record_list = list(
            records
        )

        report = QualityReport(
            source=self.source,
            total_records=len(
                record_list
            ),
        )

        if not record_list:
            report.quality_score = 0.0
            report.quality_level = (
                QualityLevel.INVALID
            )
            return report

        normalized_records: list[
            dict[str, Any]
        ] = []

        for index, record in enumerate(
            record_list,
            start=1,
        ):
            if not isinstance(
                record,
                Mapping,
            ):
                report.invalid_records += 1

                issues = self.check_record(
                    record,
                    record_index=index,
                )

                for issue in issues:
                    report.add_issue(
                        issue
                    )

                continue

            normalized = _normalize_mapping(
                record
            )

            normalized_records.append(
                normalized
            )

            issues = self.check_record(
                normalized,
                record_index=index,
            )

            if issues:
                report.invalid_records += 1
            else:
                report.valid_records += 1

            for issue in issues:
                report.add_issue(
                    issue
                )

        # ----------------------------------------------------
        # Duplicate timestamps
        # ----------------------------------------------------

        if self.config.detect_duplicates:
            self._check_duplicates(
                normalized_records,
                report,
            )

        # ----------------------------------------------------
        # Timestamp ordering
        # ----------------------------------------------------

        if self.config.detect_ordering:
            self._check_ordering(
                normalized_records,
                report,
            )

        # ----------------------------------------------------
        # Stale data
        # ----------------------------------------------------

        if self.config.detect_stale_data:
            self._check_stale(
                normalized_records,
                report,
                reference_time,
            )

        # ----------------------------------------------------
        # Score
        # ----------------------------------------------------

        report.quality_score = (
            self.calculate_score(
                report
            )
        )

        report.quality_level = (
            self.classify_score(
                report.quality_score
            )
        )

        return report

    # ========================================================
    # DUPLICATES
    # ========================================================

    def _check_duplicates(
        self,
        records: list[dict[str, Any]],
        report: QualityReport,
    ) -> None:
        """
        Detect duplicate timestamps.

        If asset_id exists, duplicates are evaluated per asset.
        """
        seen: dict[
            tuple[str | None, str],
            int,
        ] = {}

        for index, record in enumerate(
            records,
            start=1,
        ):
            timestamp = _parse_timestamp(
                record.get(
                    "timestamp"
                )
            )

            if timestamp is None:
                continue

            asset_id = record.get(
                "asset_id"
            )

            key = (
                str(asset_id)
                if asset_id is not None
                else None,
                timestamp.isoformat(),
            )

            if key in seen:
                report.add_issue(
                    QualityIssue(
                        issue_type=(
                            QualityIssueType.DUPLICATE
                        ),
                        message=(
                            "Duplicate timestamp detected."
                        ),
                        field="timestamp",
                        record_index=index,
                        severity="warning",
                        value=timestamp.isoformat(),
                        details={
                            "first_record_index": (
                                seen[key]
                            )
                        },
                    )
                )

            else:
                seen[key] = index

    # ========================================================
    # ORDERING
    # ========================================================

    def _check_ordering(
        self,
        records: list[dict[str, Any]],
        report: QualityReport,
    ) -> None:
        """
        Detect timestamps that move backwards.
        """
        previous_timestamp: datetime | None = None

        for index, record in enumerate(
            records,
            start=1,
        ):
            timestamp = _parse_timestamp(
                record.get(
                    "timestamp"
                )
            )

            if timestamp is None:
                continue

            if (
                previous_timestamp is not None
                and timestamp
                < previous_timestamp
            ):
                report.add_issue(
                    QualityIssue(
                        issue_type=(
                            QualityIssueType.OUT_OF_ORDER
                        ),
                        message=(
                            "Record timestamp is earlier "
                            "than the previous record."
                        ),
                        field="timestamp",
                        record_index=index,
                        severity="warning",
                        value=timestamp.isoformat(),
                        details={
                            "previous_timestamp": (
                                previous_timestamp.isoformat()
                            )
                        },
                    )
                )

            previous_timestamp = timestamp

    # ========================================================
    # STALE DATA
    # ========================================================

    def _check_stale(
        self,
        records: list[dict[str, Any]],
        report: QualityReport,
        reference_time: datetime | None,
    ) -> None:
        """
        Detect records older than the configured stale threshold.
        """
        if not records:
            return

        if reference_time is None:
            reference = utc_now()
        else:
            reference = reference_time

            if reference.tzinfo is None:
                reference = reference.replace(
                    tzinfo=timezone.utc
                )

            reference = reference.astimezone(
                timezone.utc
            )

        threshold = timedelta(
            seconds=self.config.stale_threshold_seconds
        )

        for index, record in enumerate(
            records,
            start=1,
        ):
            timestamp = _parse_timestamp(
                record.get(
                    "timestamp"
                )
            )

            if timestamp is None:
                continue

            age = (
                reference
                - timestamp
            )

            # Future timestamps should not be classified as
            # stale.
            if age < timedelta(0):
                continue

            if age > threshold:
                report.add_issue(
                    QualityIssue(
                        issue_type=(
                            QualityIssueType.STALE
                        ),
                        message=(
                            "Record is older than the "
                            "configured stale-data threshold."
                        ),
                        field="timestamp",
                        record_index=index,
                        severity="warning",
                        value=timestamp.isoformat(),
                        details={
                            "age_seconds": (
                                age.total_seconds()
                            ),
                            "threshold_seconds": (
                                self.config
                                .stale_threshold_seconds
                            ),
                        },
                    )
                )

    # ========================================================
    # SCORE
    # ========================================================

    def calculate_score(
        self,
        report: QualityReport,
    ) -> float:
        """
        Calculate a 0-100 quality score.

        The score considers:

        - Missing values
        - Invalid values
        - Out-of-range values
        - Duplicate records
        - Ordering problems
        - Stale data
        - Non-finite values
        - Inconsistencies
        """
        if report.total_records <= 0:
            return 0.0

        total = float(
            report.total_records
        )

        missing_penalty = (
            report.missing_value_count
            / total
            * 20.0
        )

        invalid_penalty = (
            report.invalid_value_count
            / total
            * 30.0
        )

        range_penalty = (
            report.out_of_range_count
            / total
            * 20.0
        )

        duplicate_penalty = (
            report.duplicate_count
            / total
            * 10.0
        )

        ordering_penalty = (
            report.out_of_order_count
            / total
            * 5.0
        )

        stale_penalty = (
            report.stale_count
            / total
            * 5.0
        )

        non_finite_penalty = (
            report.non_finite_count
            / total
            * 10.0
        )

        inconsistency_penalty = (
            report.inconsistent_count
            / total
            * 10.0
        )

        total_penalty = (
            missing_penalty
            + invalid_penalty
            + range_penalty
            + duplicate_penalty
            + ordering_penalty
            + stale_penalty
            + non_finite_penalty
            + inconsistency_penalty
        )

        score = max(
            0.0,
            100.0
            - total_penalty,
        )

        return round(
            score,
            2,
        )

    @staticmethod
    def classify_score(
        score: float,
    ) -> QualityLevel:
        """
        Convert a numeric quality score into a quality level.
        """
        if score >= 90.0:
            return QualityLevel.EXCELLENT

        if score >= 75.0:
            return QualityLevel.GOOD

        if score >= 60.0:
            return QualityLevel.FAIR

        if score > 0.0:
            return QualityLevel.POOR

        return QualityLevel.INVALID

    # ========================================================
    # MISSING VALUE ANALYSIS
    # ========================================================

    def missing_values(
        self,
        records: Iterable[Mapping[str, Any]],
    ) -> dict[str, int]:
        """
        Count missing values by field.
        """
        counts: Counter[str] = Counter()

        for record in records:
            if not isinstance(
                record,
                Mapping,
            ):
                continue

            for key, value in record.items():
                field_name = _normalize_key(
                    key
                )

                if value is None:
                    counts[
                        field_name
                    ] += 1

                elif (
                    isinstance(
                        value,
                        str,
                    )
                    and not value.strip()
                ):
                    counts[
                        field_name
                    ] += 1

        return dict(
            counts
        )

    # ========================================================
    # FIELD COMPLETENESS
    # ========================================================

    def field_completeness(
        self,
        records: Iterable[Mapping[str, Any]],
    ) -> dict[str, float]:
        """
        Calculate completeness percentage for each field.
        """
        record_list = [
            record
            for record in records
            if isinstance(
                record,
                Mapping,
            )
        ]

        if not record_list:
            return {}

        fields: set[str] = set()

        for record in record_list:
            fields.update(
                _normalize_key(key)
                for key in record.keys()
            )

        completeness: dict[
            str,
            float,
        ] = {}

        total = len(
            record_list
        )

        for field_name in sorted(
            fields
        ):
            present = 0

            for record in record_list:
                if field_name not in record:
                    continue

                value = record[
                    field_name
                ]

                if value is None:
                    continue

                if (
                    isinstance(
                        value,
                        str,
                    )
                    and not value.strip()
                ):
                    continue

                present += 1

            completeness[
                field_name
            ] = round(
                present
                / total
                * 100.0,
                2,
            )

        return completeness


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def check_data_quality(
    records: Iterable[Mapping[str, Any]],
    *,
    source: str = DEFAULT_SOURCE,
    config: QualityConfig | None = None,
    reference_time: datetime | None = None,
) -> QualityReport:
    """
    Run data-quality checks on records.
    """
    checker = DataQualityChecker(
        config=config,
        source=source,
    )

    return checker.check_records(
        records,
        reference_time=reference_time,
    )


def calculate_quality_score(
    records: Iterable[Mapping[str, Any]],
    *,
    source: str = DEFAULT_SOURCE,
    config: QualityConfig | None = None,
) -> float:
    """
    Calculate only the quality score.
    """
    report = check_data_quality(
        records,
        source=source,
        config=config,
    )

    return report.quality_score


def get_quality_level(
    score: float,
) -> QualityLevel:
    """
    Convert a quality score to a quality level.
    """
    return DataQualityChecker.classify_score(
        float(
            score
        )
    )


def get_missing_value_counts(
    records: Iterable[Mapping[str, Any]],
) -> dict[str, int]:
    """
    Return missing-value counts by field.
    """
    checker = DataQualityChecker()

    return checker.missing_values(
        records
    )


def get_field_completeness(
    records: Iterable[Mapping[str, Any]],
) -> dict[str, float]:
    """
    Return field completeness percentages.
    """
    checker = DataQualityChecker()

    return checker.field_completeness(
        records
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "QualityLevel",
    "QualityIssueType",
    "QualityIssue",
    "QualityReport",
    "QualityConfig",
    "DataQualityChecker",
    "check_data_quality",
    "calculate_quality_score",
    "get_quality_level",
    "get_missing_value_counts",
    "get_field_completeness",
]