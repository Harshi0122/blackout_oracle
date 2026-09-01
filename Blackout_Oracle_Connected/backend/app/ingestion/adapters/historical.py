"""
Blackout Oracle - Historical Data Adapter.

Loads historical grid data from local CSV and JSON files and
normalizes the records into a common internal representation.

Supported sources:

- CSV files
- JSON files
- JSON arrays
- JSON objects containing a records/data/items list

Typical historical data may contain:

- Telemetry
- Voltage
- Current
- Frequency
- Power generation
- Power consumption
- Loading
- Weather observations
- Asset identifiers
- Timestamps

This adapter only reads and normalizes data.
It does not modify physical grid equipment.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================
# CONSTANTS
# ============================================================

SUPPORTED_EXTENSIONS = {
    ".csv",
    ".json",
}

TIMESTAMP_FIELDS = (
    "timestamp",
    "time",
    "datetime",
    "date_time",
    "recorded_at",
    "observed_at",
    "created_at",
)

ASSET_ID_FIELDS = (
    "asset_id",
    "asset",
    "device_id",
    "equipment_id",
    "sensor_id",
)

VALUE_FIELDS = (
    "value",
    "measurement",
    "reading",
)


# ============================================================
# HELPERS
# ============================================================


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def _normalize_key(
    key: Any,
) -> str:
    """
    Normalize a field name.

    Examples:

        "Asset ID" -> "asset_id"
        "Power-Generated" -> "power_generated"
    """
    value = str(
        key
    ).strip().lower()

    value = value.replace(
        "-",
        "_",
    )

    value = value.replace(
        " ",
        "_",
    )

    return value


def _normalize_record(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize dictionary keys while preserving their values.
    """
    normalized: dict[str, Any] = {}

    for key, value in record.items():
        normalized[
            _normalize_key(key)
        ] = value

    return normalized


def _parse_timestamp(
    value: Any,
) -> datetime | None:
    """
    Parse a timestamp into a timezone-aware datetime.

    Supports:

    - datetime objects
    - ISO-8601 strings
    - strings ending in Z
    """
    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc
            )

        return value.astimezone(
            timezone.utc
        )

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
        parsed = datetime.fromisoformat(
            text
        )
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )

    return parsed.astimezone(
        timezone.utc
    )


def _safe_float(
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
        return float(
            str(value).strip()
        )
    except (
        TypeError,
        ValueError,
    ):
        return None


def _safe_int(
    value: Any,
) -> int | None:
    """Safely convert a value to int."""
    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return None

    try:
        return int(
            str(value).strip()
        )
    except (
        TypeError,
        ValueError,
    ):
        return None


def _first_present(
    record: dict[str, Any],
    fields: tuple[str, ...],
) -> Any:
    """Return the first non-empty value for a set of fields."""
    for field_name in fields:
        if field_name not in record:
            continue

        value = record[field_name]

        if value is None:
            continue

        if isinstance(
            value,
            str,
        ) and not value.strip():
            continue

        return value

    return None


# ============================================================
# DATA STRUCTURES
# ============================================================


@dataclass
class HistoricalRecord:
    """
    Normalized historical grid observation.
    """

    timestamp: datetime

    asset_id: str | None = None
    metric: str | None = None
    value: float | None = None
    unit: str | None = None

    region_id: str | None = None
    source: str = "historical"

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert the record into a JSON-compatible dictionary.
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "asset_id": self.asset_id,
            "metric": self.metric,
            "value": self.value,
            "unit": self.unit,
            "region_id": self.region_id,
            "source": self.source,
            "metadata": dict(
                self.metadata
            ),
        }


@dataclass
class HistoricalLoadResult:
    """
    Result returned after loading historical data.
    """

    records: list[HistoricalRecord] = field(
        default_factory=list
    )

    source_path: str | None = None

    total_rows: int = 0
    valid_rows: int = 0
    skipped_rows: int = 0

    errors: list[str] = field(
        default_factory=list
    )

    loaded_at: datetime = field(
        default_factory=_utc_now
    )

    @property
    def success(self) -> bool:
        """Return True when data loaded without errors."""
        return (
            self.total_rows > 0
            and not self.errors
        )

    @property
    def has_records(self) -> bool:
        """Return True when at least one record was loaded."""
        return bool(
            self.records
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Convert the result to a JSON-compatible dictionary."""
        return {
            "source_path": self.source_path,
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "skipped_rows": self.skipped_rows,
            "record_count": len(
                self.records
            ),
            "success": self.success,
            "has_records": self.has_records,
            "errors": list(
                self.errors
            ),
            "loaded_at": self.loaded_at.isoformat(),
        }


# ============================================================
# HISTORICAL DATA ADAPTER
# ============================================================


class HistoricalDataAdapter:
    """
    Adapter for loading historical grid data.

    The adapter supports CSV and JSON files and converts them
    into HistoricalRecord objects.
    """

    def __init__(
        self,
        source_name: str = "historical",
    ) -> None:
        """
        Initialize the historical data adapter.
        """
        self.source_name = source_name

    # ========================================================
    # FILE LOADING
    # ========================================================

    def load_file(
        self,
        file_path: str | Path,
    ) -> HistoricalLoadResult:
        """
        Load a historical data file.

        Supported formats:

            .csv
            .json
        """
        path = Path(
            file_path
        )

        result = HistoricalLoadResult(
            source_path=str(
                path
            )
        )

        if not path.exists():
            result.errors.append(
                f"File does not exist: {path}"
            )

            return result

        if not path.is_file():
            result.errors.append(
                f"Path is not a file: {path}"
            )

            return result

        extension = (
            path.suffix.lower()
        )

        if extension not in SUPPORTED_EXTENSIONS:
            result.errors.append(
                "Unsupported file format: "
                f"{extension}. "
                "Supported formats are CSV and JSON."
            )

            return result

        try:
            if extension == ".csv":
                raw_records = self._read_csv(
                    path
                )
            else:
                raw_records = self._read_json(
                    path
                )

        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            csv.Error,
        ) as exc:
            result.errors.append(
                f"Failed to read {path}: {exc}"
            )

            return result

        self._process_records(
            raw_records,
            result,
        )

        return result

    # ========================================================
    # CSV
    # ========================================================

    def _read_csv(
        self,
        path: Path,
    ) -> Iterator[dict[str, Any]]:
        """
        Read records from a CSV file.
        """
        with path.open(
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(
                file
            )

            if reader.fieldnames is None:
                raise csv.Error(
                    "CSV file does not contain a header row."
                )

            for row in reader:
                yield dict(
                    row
                )

    # ========================================================
    # JSON
    # ========================================================

    def _read_json(
        self,
        path: Path,
    ) -> Iterator[dict[str, Any]]:
        """
        Read records from a JSON file.

        Supported structures:

            [
                {...},
                {...}
            ]

        or:

            {
                "records": [
                    {...},
                    {...}
                ]
            }

        The keys "data" and "items" are also supported.
        """
        with path.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            payload = json.load(
                file
            )

        if isinstance(
            payload,
            list,
        ):
            for item in payload:
                if isinstance(
                    item,
                    dict,
                ):
                    yield item

            return

        if not isinstance(
            payload,
            dict,
        ):
            raise json.JSONDecodeError(
                "JSON root must be an object or array.",
                "",
                0,
            )

        for container_name in (
            "records",
            "data",
            "items",
        ):
            container = payload.get(
                container_name
            )

            if isinstance(
                container,
                list,
            ):
                for item in container:
                    if isinstance(
                        item,
                        dict,
                    ):
                        yield item

                return

        # Allow a single JSON object to represent one record.
        yield payload

    # ========================================================
    # RECORD PROCESSING
    # ========================================================

    def _process_records(
        self,
        raw_records: Iterable[dict[str, Any]],
        result: HistoricalLoadResult,
    ) -> None:
        """
        Normalize raw records and add them to a load result.
        """
        for index, raw_record in enumerate(
            raw_records,
            start=1,
        ):
            result.total_rows += 1

            try:
                record = self.normalize_record(
                    raw_record
                )

                if record is None:
                    result.skipped_rows += 1

                    continue

                result.records.append(
                    record
                )

                result.valid_rows += 1

            except (
                TypeError,
                ValueError,
            ) as exc:
                result.skipped_rows += 1

                result.errors.append(
                    f"Row {index}: {exc}"
                )

    # ========================================================
    # NORMALIZATION
    # ========================================================

    def normalize_record(
        self,
        raw_record: dict[str, Any],
    ) -> HistoricalRecord | None:
        """
        Convert a raw dictionary into a HistoricalRecord.

        A valid record must contain a recognizable timestamp.
        """
        if not isinstance(
            raw_record,
            dict,
        ):
            raise TypeError(
                "Historical record must be a dictionary."
            )

        record = _normalize_record(
            raw_record
        )

        timestamp_value = _first_present(
            record,
            TIMESTAMP_FIELDS,
        )

        timestamp = _parse_timestamp(
            timestamp_value
        )

        if timestamp is None:
            raise ValueError(
                "Record does not contain a valid timestamp."
            )

        asset_value = _first_present(
            record,
            ASSET_ID_FIELDS,
        )

        metric_value = _first_present(
            record,
            (
                "metric",
                "parameter",
                "measurement_type",
                "signal",
                "variable",
            ),
        )

        value = _first_present(
            record,
            VALUE_FIELDS,
        )

        numeric_value = _safe_float(
            value
        )

        unit_value = _first_present(
            record,
            (
                "unit",
                "units",
            ),
        )

        region_value = _first_present(
            record,
            (
                "region_id",
                "region",
            ),
        )

        known_fields = set(
            TIMESTAMP_FIELDS
        )
        known_fields.update(
            ASSET_ID_FIELDS
        )
        known_fields.update(
            VALUE_FIELDS
        )
        known_fields.update(
            {
                "metric",
                "parameter",
                "measurement_type",
                "signal",
                "variable",
                "unit",
                "units",
                "region_id",
                "region",
            }
        )

        metadata = {
            key: value
            for key, value in record.items()
            if key not in known_fields
        }

        return HistoricalRecord(
            timestamp=timestamp,
            asset_id=(
                str(asset_value)
                if asset_value is not None
                else None
            ),
            metric=(
                str(metric_value)
                if metric_value is not None
                else None
            ),
            value=numeric_value,
            unit=(
                str(unit_value)
                if unit_value is not None
                else None
            ),
            region_id=(
                str(region_value)
                if region_value is not None
                else None
            ),
            source=self.source_name,
            metadata=metadata,
        )

    # ========================================================
    # MULTI-FILE LOADING
    # ========================================================

    def load_files(
        self,
        file_paths: Iterable[str | Path],
    ) -> list[HistoricalLoadResult]:
        """
        Load multiple historical files.
        """
        results: list[HistoricalLoadResult] = []

        for file_path in file_paths:
            results.append(
                self.load_file(
                    file_path
                )
            )

        return results

    def load_directory(
        self,
        directory: str | Path,
        recursive: bool = False,
    ) -> list[HistoricalLoadResult]:
        """
        Load all supported historical files from a directory.
        """
        directory_path = Path(
            directory
        )

        if not directory_path.exists():
            return []

        if not directory_path.is_dir():
            return []

        pattern = (
            "**/*"
            if recursive
            else "*"
        )

        files = [
            path
            for path in directory_path.glob(
                pattern
            )
            if (
                path.is_file()
                and path.suffix.lower()
                in SUPPORTED_EXTENSIONS
            )
        ]

        files.sort()

        return self.load_files(
            files
        )

    # ========================================================
    # RECORD ACCESS
    # ========================================================

    def records_from_result(
        self,
        result: HistoricalLoadResult,
    ) -> list[HistoricalRecord]:
        """
        Return records from a load result.

        A copy of the list is returned.
        """
        return list(
            result.records
        )

    # ========================================================
    # FILTERING
    # ========================================================

    def filter_by_asset(
        self,
        records: Iterable[HistoricalRecord],
        asset_id: Any,
    ) -> list[HistoricalRecord]:
        """
        Filter records by asset ID.
        """
        normalized = str(
            asset_id
        )

        return [
            record
            for record in records
            if record.asset_id
            == normalized
        ]

    def filter_by_region(
        self,
        records: Iterable[HistoricalRecord],
        region_id: Any,
    ) -> list[HistoricalRecord]:
        """
        Filter records by region ID.
        """
        normalized = str(
            region_id
        )

        return [
            record
            for record in records
            if record.region_id
            == normalized
        ]

    def filter_by_metric(
        self,
        records: Iterable[HistoricalRecord],
        metric: str,
    ) -> list[HistoricalRecord]:
        """
        Filter records by metric name.
        """
        normalized = str(
            metric
        ).strip().lower()

        return [
            record
            for record in records
            if (
                record.metric is not None
                and record.metric.strip().lower()
                == normalized
            )
        ]

    def filter_time_range(
        self,
        records: Iterable[HistoricalRecord],
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[HistoricalRecord]:
        """
        Filter records by timestamp.

        Start and end are inclusive.
        """
        normalized_start = (
            _parse_timestamp(start)
            if start is not None
            else None
        )

        normalized_end = (
            _parse_timestamp(end)
            if end is not None
            else None
        )

        filtered: list[HistoricalRecord] = []

        for record in records:
            if (
                normalized_start is not None
                and record.timestamp
                < normalized_start
            ):
                continue

            if (
                normalized_end is not None
                and record.timestamp
                > normalized_end
            ):
                continue

            filtered.append(
                record
            )

        return filtered

    # ========================================================
    # SORTING
    # ========================================================

    def sort_by_timestamp(
        self,
        records: Iterable[HistoricalRecord],
        descending: bool = False,
    ) -> list[HistoricalRecord]:
        """
        Sort records by timestamp.
        """
        return sorted(
            records,
            key=lambda record: record.timestamp,
            reverse=descending,
        )

    # ========================================================
    # NUMERIC EXTRACTION
    # ========================================================

    def numeric_values(
        self,
        records: Iterable[HistoricalRecord],
    ) -> list[float]:
        """
        Extract numeric values from historical records.

        Records without numeric values are ignored.
        """
        values: list[float] = []

        for record in records:
            if record.value is not None:
                values.append(
                    record.value
                )

        return values

    # ========================================================
    # BASIC STATISTICS
    # ========================================================

    def statistics(
        self,
        records: Iterable[HistoricalRecord],
    ) -> dict[str, float | int | None]:
        """
        Calculate basic statistics for numeric records.

        Returns:

            count
            minimum
            maximum
            average
        """
        values = self.numeric_values(
            records
        )

        if not values:
            return {
                "count": 0,
                "minimum": None,
                "maximum": None,
                "average": None,
            }

        return {
            "count": len(
                values
            ),
            "minimum": min(
                values
            ),
            "maximum": max(
                values
            ),
            "average": (
                sum(values)
                / len(values)
            ),
        }

    # ========================================================
    # DATA QUALITY
    # ========================================================

    def validate_records(
        self,
        records: Iterable[HistoricalRecord],
    ) -> list[str]:
        """
        Validate normalized historical records.

        Returns:
            A list of validation errors.
        """
        errors: list[str] = []

        for index, record in enumerate(
            records,
            start=1,
        ):
            if not isinstance(
                record.timestamp,
                datetime,
            ):
                errors.append(
                    f"Record {index} has an invalid timestamp."
                )

            if (
                record.timestamp.tzinfo
                is None
            ):
                errors.append(
                    f"Record {index} timestamp is timezone-naive."
                )

            if (
                record.asset_id is not None
                and not str(
                    record.asset_id
                ).strip()
            ):
                errors.append(
                    f"Record {index} has an empty asset ID."
                )

        return errors

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def records_to_dict(
        self,
        records: Iterable[HistoricalRecord],
    ) -> list[dict[str, Any]]:
        """
        Convert historical records to dictionaries.
        """
        return [
            record.to_dict()
            for record in records
        ]


# ============================================================
# MODULE-LEVEL FUNCTIONS
# ============================================================


def load_historical_file(
    file_path: str | Path,
) -> HistoricalLoadResult:
    """
    Convenience function for loading one historical file.
    """
    adapter = HistoricalDataAdapter()

    return adapter.load_file(
        file_path
    )


def load_historical_directory(
    directory: str | Path,
    recursive: bool = False,
) -> list[HistoricalLoadResult]:
    """
    Convenience function for loading historical files from a
    directory.
    """
    adapter = HistoricalDataAdapter()

    return adapter.load_directory(
        directory,
        recursive=recursive,
    )


def normalize_historical_records(
    records: Iterable[dict[str, Any]],
) -> list[HistoricalRecord]:
    """
    Normalize an iterable of raw historical dictionaries.
    """
    adapter = HistoricalDataAdapter()

    normalized: list[HistoricalRecord] = []

    for record in records:
        normalized_record = (
            adapter.normalize_record(
                record
            )
        )

        if normalized_record is not None:
            normalized.append(
                normalized_record
            )

    return normalized


def historical_statistics(
    records: Iterable[HistoricalRecord],
) -> dict[str, float | int | None]:
    """
    Calculate basic statistics for historical records.
    """
    adapter = HistoricalDataAdapter()

    return adapter.statistics(
        records
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "SUPPORTED_EXTENSIONS",
    "HistoricalRecord",
    "HistoricalLoadResult",
    "HistoricalDataAdapter",
    "load_historical_file",
    "load_historical_directory",
    "normalize_historical_records",
    "historical_statistics",
]