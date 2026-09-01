"""
Blackout Oracle - Ingestion Base Module.

Defines the common interfaces and data structures used by the
Blackout Oracle ingestion layer.

The ingestion pipeline is responsible for:

1. Receiving data from an external or synthetic source.
2. Converting it into a common internal representation.
3. Validating the normalized records.
4. Reporting ingestion errors without crashing the application.

Concrete adapters such as:

- HistoricalDataAdapter
- IMDWeatherAdapter
- SLDCPublicAdapter
- TANGEDCOPublicAdapter
- SyntheticGridAdapter

can build on these common interfaces.

This module does not connect to physical grid equipment and does
not issue grid-control commands.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, TypeVar


# ============================================================
# TYPE VARIABLES
# ============================================================

RecordT = TypeVar(
    "RecordT"
)


# ============================================================
# ENUMS
# ============================================================


class IngestionStatus(str, Enum):
    """
    Status of an ingestion operation.
    """

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    EMPTY = "empty"


class DataSourceType(str, Enum):
    """
    Supported categories of ingestion sources.
    """

    HISTORICAL = "historical"
    IMD = "imd"
    SLDC_PUBLIC = "sldc_public"
    TANGEDCO_PUBLIC = "tangedco_public"
    SYNTHETIC = "synthetic"
    UNKNOWN = "unknown"


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def utc_now() -> datetime:
    """
    Return the current UTC timestamp.
    """
    return datetime.now(
        timezone.utc
    )


# ============================================================
# INGESTION ERROR
# ============================================================


@dataclass
class IngestionError:
    """
    Represents an error encountered while processing input data.
    """

    message: str

    source: str | None = None

    record_index: int | None = None

    field: str | None = None

    error_type: str = "validation_error"

    timestamp: datetime = field(
        default_factory=utc_now
    )

    details: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert the error into a JSON-compatible dictionary.
        """
        return {
            "message": self.message,
            "source": self.source,
            "record_index": self.record_index,
            "field": self.field,
            "error_type": self.error_type,
            "timestamp": self.timestamp.isoformat(),
            "details": dict(
                self.details
            ),
        }


# ============================================================
# INGESTION RESULT
# ============================================================


@dataclass
class IngestionResult(
    Generic[RecordT]
):
    """
    Generic result returned by an ingestion operation.

    The class is deliberately independent of the database and
    API layers so it can be reused throughout the application.
    """

    records: list[RecordT] = field(
        default_factory=list
    )

    source: str = "unknown"

    source_type: DataSourceType = (
        DataSourceType.UNKNOWN
    )

    status: IngestionStatus = (
        IngestionStatus.EMPTY
    )

    total_records: int = 0

    valid_records: int = 0

    skipped_records: int = 0

    errors: list[IngestionError] = field(
        default_factory=list
    )

    started_at: datetime | None = None

    completed_at: datetime | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def record_count(
        self,
    ) -> int:
        """
        Return the number of successfully normalized records.
        """
        return len(
            self.records
        )

    @property
    def has_records(
        self,
    ) -> bool:
        """
        Return True when at least one record exists.
        """
        return bool(
            self.records
        )

    @property
    def has_errors(
        self,
    ) -> bool:
        """
        Return True when at least one ingestion error exists.
        """
        return bool(
            self.errors
        )

    @property
    def success(
        self,
    ) -> bool:
        """
        Return True when ingestion completed successfully.
        """
        return (
            self.status
            == IngestionStatus.SUCCESS
        )

    @property
    def duration_seconds(
        self,
    ) -> float | None:
        """
        Return ingestion duration in seconds.
        """
        if (
            self.started_at is None
            or self.completed_at is None
        ):
            return None

        return (
            self.completed_at
            - self.started_at
        ).total_seconds()

    def add_error(
        self,
        message: str,
        *,
        record_index: int | None = None,
        field: str | None = None,
        error_type: str = "validation_error",
        details: Mapping[str, Any] | None = None,
    ) -> None:
        """
        Add an ingestion error.
        """
        self.errors.append(
            IngestionError(
                message=str(
                    message
                ),
                source=self.source,
                record_index=record_index,
                field=field,
                error_type=error_type,
                details=(
                    dict(details)
                    if details is not None
                    else {}
                ),
            )
        )

    def finalize(
        self,
    ) -> IngestionResult[RecordT]:
        """
        Finalize the result and calculate its status.
        """
        self.completed_at = utc_now()

        self.valid_records = len(
            self.records
        )

        if (
            self.total_records == 0
        ):
            self.status = (
                IngestionStatus.EMPTY
            )

        elif (
            self.valid_records == 0
        ):
            self.status = (
                IngestionStatus.FAILED
            )

        elif self.errors:
            self.status = (
                IngestionStatus.PARTIAL
            )

        else:
            self.status = (
                IngestionStatus.SUCCESS
            )

        return self

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert the result into a JSON-compatible dictionary.
        """
        return {
            "source": self.source,
            "source_type": self.source_type.value,
            "status": self.status.value,
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "skipped_records": self.skipped_records,
            "record_count": self.record_count,
            "has_records": self.has_records,
            "has_errors": self.has_errors,
            "success": self.success,
            "duration_seconds": (
                self.duration_seconds
            ),
            "started_at": (
                self.started_at.isoformat()
                if self.started_at
                else None
            ),
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at
                else None
            ),
            "errors": [
                error.to_dict()
                for error in self.errors
            ],
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# BASE ADAPTER
# ============================================================


class BaseIngestionAdapter(
    ABC,
    Generic[RecordT],
):
    """
    Abstract base class for all Blackout Oracle ingestion
    adapters.

    Concrete adapters should implement:

    - normalize_record()
    - ingest()

    They may additionally implement source-specific loading
    methods such as fetch(), load_file(), or normalize_json().
    """

    source_name: str = "unknown"

    source_type: DataSourceType = (
        DataSourceType.UNKNOWN
    )

    # ========================================================
    # NORMALIZATION
    # ========================================================

    @abstractmethod
    def normalize_record(
        self,
        raw_record: Mapping[str, Any],
    ) -> RecordT:
        """
        Convert one raw record into the adapter's normalized
        record type.
        """
        raise NotImplementedError

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_record(
        self,
        record: RecordT,
    ) -> list[str]:
        """
        Validate one normalized record.

        Concrete adapters can override this method when they need
        source-specific validation rules.

        Returning an empty list means the record is valid.
        """
        return []

    def validate_records(
        self,
        records: Iterable[RecordT],
    ) -> list[str]:
        """
        Validate multiple normalized records.
        """
        errors: list[str] = []

        for index, record in enumerate(
            records,
            start=1,
        ):
            record_errors = self.validate_record(
                record
            )

            for error in record_errors:
                errors.append(
                    f"Record {index}: {error}"
                )

        return errors

    # ========================================================
    # INGESTION
    # ========================================================

    def ingest(
        self,
        raw_records: Iterable[Mapping[str, Any]],
    ) -> IngestionResult[RecordT]:
        """
        Normalize and validate an iterable of raw records.

        Invalid records are skipped and reported rather than
        crashing the entire ingestion operation.
        """
        result = IngestionResult[
            RecordT
        ](
            source=self.source_name,
            source_type=self.source_type,
            started_at=utc_now(),
        )

        for index, raw_record in enumerate(
            raw_records,
            start=1,
        ):
            result.total_records += 1

            try:
                record = self.normalize_record(
                    raw_record
                )

            except (
                TypeError,
                ValueError,
            ) as exc:
                result.skipped_records += 1

                result.add_error(
                    str(exc),
                    record_index=index,
                    error_type="normalization_error",
                )

                continue

            validation_errors = (
                self.validate_record(
                    record
                )
            )

            if validation_errors:
                result.skipped_records += 1

                for error in validation_errors:
                    result.add_error(
                        error,
                        record_index=index,
                        error_type="validation_error",
                    )

                continue

            result.records.append(
                record
            )

        return result.finalize()

    # ========================================================
    # NORMALIZE + VALIDATE ONE RECORD
    # ========================================================

    def process_record(
        self,
        raw_record: Mapping[str, Any],
    ) -> RecordT:
        """
        Normalize and validate one record.

        Raises ValueError when validation fails.
        """
        record = self.normalize_record(
            raw_record
        )

        errors = self.validate_record(
            record
        )

        if errors:
            raise ValueError(
                "; ".join(
                    errors
                )
            )

        return record

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def record_to_dict(
        self,
        record: RecordT,
    ) -> dict[str, Any]:
        """
        Convert a normalized record to a dictionary.

        Adapters whose record classes provide to_dict() can use
        this default implementation.
        """
        to_dict = getattr(
            record,
            "to_dict",
            None,
        )

        if callable(
            to_dict
        ):
            value = to_dict()

            if isinstance(
                value,
                dict,
            ):
                return value

        if isinstance(
            record,
            Mapping,
        ):
            return dict(
                record
            )

        raise TypeError(
            "Record does not provide a compatible to_dict() "
            "method."
        )

    def records_to_dict(
        self,
        records: Iterable[RecordT],
    ) -> list[dict[str, Any]]:
        """
        Convert multiple normalized records into dictionaries.
        """
        return [
            self.record_to_dict(
                record
            )
            for record in records
        ]


# ============================================================
# SIMPLE ADAPTER
# ============================================================


class GenericIngestionAdapter(
    BaseIngestionAdapter[dict[str, Any]]
):
    """
    Generic adapter for already-normalized dictionary records.

    Useful for simple data sources and testing.
    """

    source_name = "generic"

    source_type = (
        DataSourceType.UNKNOWN
    )

    def normalize_record(
        self,
        raw_record: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Copy a mapping into a normal dictionary.
        """
        if not isinstance(
            raw_record,
            Mapping,
        ):
            raise TypeError(
                "Raw record must be a mapping."
            )

        return dict(
            raw_record
        )

    def validate_record(
        self,
        record: dict[str, Any],
    ) -> list[str]:
        """
        Basic dictionary validation.
        """
        if not isinstance(
            record,
            dict,
        ):
            return [
                "Normalized record must be a dictionary."
            ]

        return []


# ============================================================
# UTILITY FUNCTIONS
# ============================================================


def create_ingestion_result(
    source: str = "unknown",
    source_type: DataSourceType = DataSourceType.UNKNOWN,
) -> IngestionResult[Any]:
    """
    Create an empty ingestion result.
    """
    return IngestionResult(
        source=source,
        source_type=source_type,
        started_at=utc_now(),
    )


def ingest_records(
    adapter: BaseIngestionAdapter[RecordT],
    raw_records: Iterable[Mapping[str, Any]],
) -> IngestionResult[RecordT]:
    """
    Convenience function for running an adapter.
    """
    return adapter.ingest(
        raw_records
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "RecordT",
    "IngestionStatus",
    "DataSourceType",
    "IngestionError",
    "IngestionResult",
    "BaseIngestionAdapter",
    "GenericIngestionAdapter",
    "create_ingestion_result",
    "ingest_records",
]