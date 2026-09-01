"""
Blackout Oracle - Data Ingestion Pipeline.

Coordinates the ingestion process between source adapters and
the rest of the Blackout Oracle application.

Pipeline flow:

    Raw source data
            |
            v
    Source adapter
            |
            v
    Normalization
            |
            v
    Validation
            |
            v
    IngestionResult
            |
            v
    Feature / Risk / Incident layers

The pipeline is intentionally independent of:
- FastAPI
- SQLAlchemy
- Machine-learning libraries
- Specific external data providers

This makes it suitable for development, testing, simulations,
and production integration.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from app.ingestion.base import (
    BaseIngestionAdapter,
    DataSourceType,
    IngestionError,
    IngestionResult,
)
from app.ingestion.normalizer import (
    extract_records,
    normalize_record,
    validate_normalized_record,
)


# ============================================================
# TYPE VARIABLES
# ============================================================

RecordT = TypeVar(
    "RecordT"
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_PIPELINE_NAME = (
    "blackout_oracle_ingestion"
)

DEFAULT_SOURCE = "unknown"


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(
        timezone.utc
    )


# ============================================================
# PIPELINE ERROR
# ============================================================


@dataclass
class PipelineError:
    """
    Represents an error produced by the ingestion pipeline.
    """

    message: str

    stage: str

    source: str = DEFAULT_SOURCE

    record_index: int | None = None

    timestamp: datetime = field(
        default_factory=utc_now
    )

    details: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Convert the error into a dictionary."""
        return {
            "message": self.message,
            "stage": self.stage,
            "source": self.source,
            "record_index": self.record_index,
            "timestamp": self.timestamp.isoformat(),
            "details": dict(
                self.details
            ),
        }


# ============================================================
# PIPELINE RESULT
# ============================================================


@dataclass
class PipelineResult(
    Generic[RecordT]
):
    """
    Result returned by the ingestion pipeline.
    """

    records: list[RecordT] = field(
        default_factory=list
    )

    pipeline_name: str = (
        DEFAULT_PIPELINE_NAME
    )

    source: str = DEFAULT_SOURCE

    source_type: DataSourceType = (
        DataSourceType.UNKNOWN
    )

    total_records: int = 0

    successful_records: int = 0

    failed_records: int = 0

    errors: list[PipelineError] = field(
        default_factory=list
    )

    started_at: datetime | None = None

    completed_at: datetime | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def success(
        self,
    ) -> bool:
        """
        Return True if the pipeline processed at least one
        record without errors.
        """
        return (
            self.successful_records > 0
            and not self.errors
        )

    @property
    def partial_success(
        self,
    ) -> bool:
        """
        Return True if some records succeeded and some failed.
        """
        return (
            self.successful_records > 0
            and self.failed_records > 0
        )

    @property
    def has_records(
        self,
    ) -> bool:
        """Return True if records were produced."""
        return bool(
            self.records
        )

    @property
    def duration_seconds(
        self,
    ) -> float | None:
        """Return pipeline execution duration."""
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
        stage: str,
        record_index: int | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        """Add a pipeline error."""
        self.errors.append(
            PipelineError(
                message=str(
                    message
                ),
                stage=stage,
                source=self.source,
                record_index=record_index,
                details=(
                    dict(details)
                    if details is not None
                    else {}
                ),
            )
        )

    def finalize(
        self,
    ) -> PipelineResult[RecordT]:
        """Finalize the pipeline result."""
        self.completed_at = utc_now()

        self.successful_records = len(
            self.records
        )

        return self

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Convert the pipeline result into a dictionary."""
        return {
            "pipeline_name": self.pipeline_name,
            "source": self.source,
            "source_type": self.source_type.value,
            "total_records": self.total_records,
            "successful_records": (
                self.successful_records
            ),
            "failed_records": self.failed_records,
            "success": self.success,
            "partial_success": (
                self.partial_success
            ),
            "has_records": self.has_records,
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
# PIPELINE CONFIGURATION
# ============================================================


@dataclass
class PipelineConfig:
    """
    Configuration for an ingestion pipeline.
    """

    name: str = DEFAULT_PIPELINE_NAME

    source: str = DEFAULT_SOURCE

    source_type: DataSourceType = (
        DataSourceType.UNKNOWN
    )

    stop_on_error: bool = False

    validate_records: bool = True

    preserve_unknown_fields: bool = True

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# INGESTION PIPELINE
# ============================================================


class IngestionPipeline(
    Generic[RecordT]
):
    """
    Main coordinator for the Blackout Oracle ingestion layer.

    A pipeline can operate in two modes:

    1. Adapter mode:
       Uses a BaseIngestionAdapter to normalize source records.

    2. Generic mode:
       Uses the shared normalizer directly and returns dictionaries.
    """

    def __init__(
        self,
        adapter: BaseIngestionAdapter[RecordT] | None = None,
        config: PipelineConfig | None = None,
    ) -> None:
        """Initialize the ingestion pipeline."""
        self.adapter = adapter

        if config is not None:
            self.config = config

        elif adapter is not None:
            self.config = PipelineConfig(
                name=DEFAULT_PIPELINE_NAME,
                source=adapter.source_name,
                source_type=adapter.source_type,
            )

        else:
            self.config = PipelineConfig()

    # ========================================================
    # ADAPTER MODE
    # ========================================================

    def run(
        self,
        raw_records: Iterable[Mapping[str, Any]],
    ) -> PipelineResult[RecordT]:
        """
        Run the pipeline using the configured adapter.
        """
        if self.adapter is None:
            raise RuntimeError(
                "No ingestion adapter has been configured."
            )

        result = PipelineResult[
            RecordT
        ](
            pipeline_name=self.config.name,
            source=self.config.source,
            source_type=self.config.source_type,
            started_at=utc_now(),
            metadata=dict(
                self.config.metadata
            ),
        )

        records = list(
            raw_records
        )

        result.total_records = len(
            records
        )

        for index, raw_record in enumerate(
            records,
            start=1,
        ):
            try:
                normalized = (
                    self.adapter.normalize_record(
                        raw_record
                    )
                )

                if self.config.validate_records:
                    validation_errors = (
                        self.adapter.validate_record(
                            normalized
                        )
                    )

                    if validation_errors:
                        result.failed_records += 1

                        for error in validation_errors:
                            result.add_error(
                                error,
                                stage="validation",
                                record_index=index,
                            )

                        if self.config.stop_on_error:
                            break

                        continue

                result.records.append(
                    normalized
                )

            except (
                TypeError,
                ValueError,
            ) as exc:
                result.failed_records += 1

                result.add_error(
                    str(exc),
                    stage="normalization",
                    record_index=index,
                )

                if self.config.stop_on_error:
                    break

            except Exception as exc:
                result.failed_records += 1

                result.add_error(
                    str(exc),
                    stage="processing",
                    record_index=index,
                    details={
                        "exception_type": (
                            type(exc).__name__
                        )
                    },
                )

                if self.config.stop_on_error:
                    break

        return result.finalize()

    # ========================================================
    # GENERIC MODE
    # ========================================================

    def run_generic(
        self,
        payload: Any,
        source: str | None = None,
    ) -> PipelineResult[
        dict[str, Any]
    ]:
        """
        Run the pipeline using the shared normalizer instead of
        a source-specific adapter.
        """
        pipeline_source = (
            source
            if source is not None
            else self.config.source
        )

        result = PipelineResult[
            dict[str, Any]
        ](
            pipeline_name=self.config.name,
            source=pipeline_source,
            source_type=self.config.source_type,
            started_at=utc_now(),
            metadata=dict(
                self.config.metadata
            ),
        )

        raw_records = extract_records(
            payload
        )

        result.total_records = len(
            raw_records
        )

        for index, raw_record in enumerate(
            raw_records,
            start=1,
        ):
            try:
                normalized = normalize_record(
                    raw_record,
                    source=pipeline_source,
                )

                if self.config.validate_records:
                    errors = validate_normalized_record(
                        normalized
                    )

                    if errors:
                        result.failed_records += 1

                        for error in errors:
                            result.add_error(
                                error,
                                stage="validation",
                                record_index=index,
                            )

                        if self.config.stop_on_error:
                            break

                        continue

                result.records.append(
                    normalized
                )

            except (
                TypeError,
                ValueError,
            ) as exc:
                result.failed_records += 1

                result.add_error(
                    str(exc),
                    stage="normalization",
                    record_index=index,
                )

                if self.config.stop_on_error:
                    break

            except Exception as exc:
                result.failed_records += 1

                result.add_error(
                    str(exc),
                    stage="processing",
                    record_index=index,
                    details={
                        "exception_type": (
                            type(exc).__name__
                        )
                    },
                )

                if self.config.stop_on_error:
                    break

        return result.finalize()

    # ========================================================
    # SINGLE RECORD
    # ========================================================

    def process_one(
        self,
        raw_record: Mapping[str, Any],
    ) -> RecordT:
        """
        Process exactly one record through the configured
        adapter.
        """
        if self.adapter is None:
            raise RuntimeError(
                "No ingestion adapter has been configured."
            )

        normalized = self.adapter.normalize_record(
            raw_record
        )

        if self.config.validate_records:
            errors = self.adapter.validate_record(
                normalized
            )

            if errors:
                raise ValueError(
                    "; ".join(
                        errors
                    )
                )

        return normalized

    # ========================================================
    # BATCH PROCESSING
    # ========================================================

    def process_batches(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        batch_size: int = 100,
    ) -> list[
        PipelineResult[RecordT]
    ]:
        """
        Process records in batches.

        This is useful when a large historical dataset should
        not be handled as one giant operation.
        """
        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than zero."
            )

        records = list(
            raw_records
        )

        results: list[
            PipelineResult[RecordT]
        ] = []

        for start in range(
            0,
            len(records),
            batch_size,
        ):
            batch = records[
                start : start + batch_size
            ]

            results.append(
                self.run(
                    batch
                )
            )

        return results


# ============================================================
# PIPELINE BUILDER
# ============================================================


class PipelineBuilder(
    Generic[RecordT]
):
    """
    Convenience builder for constructing ingestion pipelines.
    """

    def __init__(self) -> None:
        self._adapter: (
            BaseIngestionAdapter[RecordT]
            | None
        ) = None

        self._config = PipelineConfig()

    def with_adapter(
        self,
        adapter: BaseIngestionAdapter[RecordT],
    ) -> PipelineBuilder[RecordT]:
        """Set the source adapter."""
        self._adapter = adapter

        self._config.source = (
            adapter.source_name
        )

        self._config.source_type = (
            adapter.source_type
        )

        return self

    def with_name(
        self,
        name: str,
    ) -> PipelineBuilder[RecordT]:
        """Set the pipeline name."""
        self._config.name = str(
            name
        )

        return self

    def with_source(
        self,
        source: str,
    ) -> PipelineBuilder[RecordT]:
        """Set the source name."""
        self._config.source = str(
            source
        )

        return self

    def stop_on_error(
        self,
        enabled: bool = True,
    ) -> PipelineBuilder[RecordT]:
        """Configure fail-fast behavior."""
        self._config.stop_on_error = bool(
            enabled
        )

        return self

    def validate(
        self,
        enabled: bool = True,
    ) -> PipelineBuilder[RecordT]:
        """Enable or disable validation."""
        self._config.validate_records = bool(
            enabled
        )

        return self

    def with_metadata(
        self,
        metadata: Mapping[str, Any],
    ) -> PipelineBuilder[RecordT]:
        """Add pipeline metadata."""
        self._config.metadata.update(
            dict(
                metadata
            )
        )

        return self

    def build(
        self,
    ) -> IngestionPipeline[RecordT]:
        """Build the configured pipeline."""
        return IngestionPipeline(
            adapter=self._adapter,
            config=self._config,
        )


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def run_ingestion(
    adapter: BaseIngestionAdapter[RecordT],
    raw_records: Iterable[Mapping[str, Any]],
    *,
    stop_on_error: bool = False,
    validate: bool = True,
) -> PipelineResult[RecordT]:
    """
    Convenience function for running an adapter through the
    ingestion pipeline.
    """
    config = PipelineConfig(
        source=adapter.source_name,
        source_type=adapter.source_type,
        stop_on_error=stop_on_error,
        validate_records=validate,
    )

    pipeline = IngestionPipeline(
        adapter=adapter,
        config=config,
    )

    return pipeline.run(
        raw_records
    )


def run_generic_ingestion(
    payload: Any,
    *,
    source: str = DEFAULT_SOURCE,
    source_type: DataSourceType = DataSourceType.UNKNOWN,
    stop_on_error: bool = False,
    validate: bool = True,
) -> PipelineResult[
    dict[str, Any]
]:
    """
    Convenience function for normalizing generic payloads.
    """
    config = PipelineConfig(
        source=source,
        source_type=source_type,
        stop_on_error=stop_on_error,
        validate_records=validate,
    )

    pipeline = IngestionPipeline(
        config=config
    )

    return pipeline.run_generic(
        payload
    )


# ============================================================
# PIPELINE STATUS HELPERS
# ============================================================


def summarize_result(
    result: PipelineResult[Any],
) -> dict[str, Any]:
    """
    Produce a compact summary of a pipeline result.
    """
    return {
        "pipeline_name": result.pipeline_name,
        "source": result.source,
        "total_records": result.total_records,
        "successful_records": (
            result.successful_records
        ),
        "failed_records": result.failed_records,
        "error_count": len(
            result.errors
        ),
        "success": result.success,
        "partial_success": (
            result.partial_success
        ),
        "duration_seconds": (
            result.duration_seconds
        ),
    }


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "PipelineError",
    "PipelineResult",
    "PipelineConfig",
    "IngestionPipeline",
    "PipelineBuilder",
    "run_ingestion",
    "run_generic_ingestion",
    "summarize_result",
]