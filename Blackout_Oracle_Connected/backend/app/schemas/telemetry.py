"""
Blackout Oracle - Telemetry Schemas.

Pydantic schemas for electrical-grid telemetry, measurements,
quality indicators, historical observations, and telemetry
queries.

These schemas are independent of SQLAlchemy models and are
intended for use by ingestion, API, ML, risk, and analytics
layers.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# ENUMS
# ============================================================


class TelemetryType(str, Enum):
    """Types of electrical telemetry measurements."""

    VOLTAGE = "voltage"
    CURRENT = "current"
    FREQUENCY = "frequency"
    ACTIVE_POWER = "active_power"
    REACTIVE_POWER = "reactive_power"
    APPARENT_POWER = "apparent_power"
    POWER_FACTOR = "power_factor"
    ENERGY = "energy"
    TEMPERATURE = "temperature"
    LOADING = "loading"
    STATUS = "status"
    BREAKER_STATE = "breaker_state"
    OTHER = "other"


class TelemetryQuality(str, Enum):
    """Quality classification of a telemetry observation."""

    GOOD = "good"
    UNCERTAIN = "uncertain"
    SUSPECT = "suspect"
    BAD = "bad"
    MISSING = "missing"
    STALE = "stale"


class TelemetrySource(str, Enum):
    """Source of telemetry data."""

    SCADA = "scada"
    PMU = "pmu"
    SMART_METER = "smart_meter"
    IOT = "iot"
    SLDC = "sldc"
    TANGEDCO = "tangedco"
    SYNTHETIC = "synthetic"
    HISTORICAL = "historical"
    MANUAL = "manual"
    OTHER = "other"


class AggregationType(str, Enum):
    """Aggregation operations for telemetry queries."""

    RAW = "raw"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    SUM = "sum"
    MEDIAN = "median"
    STDDEV = "stddev"


# ============================================================
# TELEMETRY VALUE
# ============================================================


class TelemetryValue(BaseModel):
    """
    A single telemetry measurement value.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    value: float | None = Field(
        default=None,
        description="Measured numeric value.",
    )

    unit: str | None = Field(
        default=None,
        max_length=50,
        description="Engineering unit of the measurement.",
    )

    quality: TelemetryQuality = Field(
        default=TelemetryQuality.GOOD,
        description="Quality of the measurement.",
    )

    quality_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Normalized data-quality score.",
    )


# ============================================================
# BASE TELEMETRY
# ============================================================


class TelemetryBase(BaseModel):
    """
    Common fields shared by telemetry schemas.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    asset_id: int = Field(
        ...,
        ge=1,
        description="Identifier of the asset producing the measurement.",
    )

    telemetry_type: TelemetryType = Field(
        ...,
        description="Type of telemetry measurement.",
    )

    timestamp: datetime = Field(
        ...,
        description="Measurement timestamp.",
    )

    value: float | None = Field(
        default=None,
        description="Measured value.",
    )

    unit: str | None = Field(
        default=None,
        max_length=50,
        description="Engineering unit.",
    )

    quality: TelemetryQuality = Field(
        default=TelemetryQuality.GOOD,
    )

    quality_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    source: TelemetrySource = Field(
        default=TelemetrySource.SCADA,
        description="Origin of the telemetry measurement.",
    )

    source_id: str | None = Field(
        default=None,
        max_length=255,
        description="Identifier assigned by the source system.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# TELEMETRY CREATE
# ============================================================


class TelemetryCreate(TelemetryBase):
    """
    Schema used when inserting a telemetry measurement.
    """

    pass


# ============================================================
# TELEMETRY UPDATE
# ============================================================


class TelemetryUpdate(BaseModel):
    """
    Schema used for updating a telemetry record.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    value: float | None = None

    unit: str | None = Field(
        default=None,
        max_length=50,
    )

    quality: TelemetryQuality | None = None

    quality_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    metadata: dict[str, Any] | None = None


# ============================================================
# TELEMETRY RESPONSE
# ============================================================


class TelemetryResponse(TelemetryBase):
    """
    API response representing a stored telemetry measurement.
    """

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        extra="forbid",
    )

    id: int = Field(
        ...,
        ge=1,
    )

    created_at: datetime | None = None

    updated_at: datetime | None = None


# ============================================================
# BATCH TELEMETRY
# ============================================================


class TelemetryBatchCreate(BaseModel):
    """
    Schema for inserting multiple telemetry observations.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    measurements: list[TelemetryCreate] = Field(
        ...,
        min_length=1,
        max_length=10000,
    )

    source: TelemetrySource | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class TelemetryBatchResponse(BaseModel):
    """
    Result of a batch telemetry ingestion operation.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    total: int = Field(
        default=0,
        ge=0,
    )

    accepted: int = Field(
        default=0,
        ge=0,
    )

    rejected: int = Field(
        default=0,
        ge=0,
    )

    duplicate: int = Field(
        default=0,
        ge=0,
    )

    records: list[TelemetryResponse] = Field(
        default_factory=list,
    )

    errors: list[str] = Field(
        default_factory=list,
    )

    processed_at: datetime


# ============================================================
# TELEMETRY QUERY
# ============================================================


class TelemetryQuery(BaseModel):
    """
    Query parameters for retrieving telemetry observations.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    asset_id: int | None = Field(
        default=None,
        ge=1,
    )

    asset_ids: list[int] = Field(
        default_factory=list,
    )

    telemetry_type: TelemetryType | None = None

    telemetry_types: list[TelemetryType] = Field(
        default_factory=list,
    )

    source: TelemetrySource | None = None

    quality: TelemetryQuality | None = None

    start_time: datetime

    end_time: datetime

    aggregation: AggregationType = AggregationType.RAW

    interval_seconds: int | None = Field(
        default=None,
        gt=0,
    )

    limit: int = Field(
        default=1000,
        ge=1,
        le=10000,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# TELEMETRY FILTER
# ============================================================


class TelemetryFilter(BaseModel):
    """
    Filtering options for telemetry repositories and services.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    asset_id: int | None = Field(
        default=None,
        ge=1,
    )

    telemetry_type: TelemetryType | None = None

    source: TelemetrySource | None = None

    quality: TelemetryQuality | None = None

    min_value: float | None = None

    max_value: float | None = None

    start_time: datetime | None = None

    end_time: datetime | None = None

    limit: int = Field(
        default=1000,
        ge=1,
        le=10000,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# TELEMETRY POINT
# ============================================================


class TelemetryPoint(BaseModel):
    """
    Lightweight time-series telemetry point.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    timestamp: datetime

    value: float | None = None

    quality: TelemetryQuality = TelemetryQuality.GOOD


# ============================================================
# TELEMETRY SERIES
# ============================================================


class TelemetrySeries(BaseModel):
    """
    Time-series representation of telemetry for one asset and
    measurement type.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    asset_id: int = Field(
        ...,
        ge=1,
    )

    telemetry_type: TelemetryType

    unit: str | None = Field(
        default=None,
        max_length=50,
    )

    points: list[TelemetryPoint] = Field(
        default_factory=list,
    )

    start_time: datetime | None = None

    end_time: datetime | None = None

    count: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# AGGREGATED TELEMETRY
# ============================================================


class TelemetryAggregate(BaseModel):
    """
    Aggregated telemetry statistics over a time interval.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    asset_id: int = Field(
        ...,
        ge=1,
    )

    telemetry_type: TelemetryType

    aggregation: AggregationType

    value: float | None = None

    minimum: float | None = None

    maximum: float | None = None

    average: float | None = None

    median: float | None = None

    standard_deviation: float | None = Field(
        default=None,
        ge=0.0,
    )

    count: int = Field(
        default=0,
        ge=0,
    )

    valid_count: int = Field(
        default=0,
        ge=0,
    )

    start_time: datetime

    end_time: datetime

    unit: str | None = None


# ============================================================
# ELECTRICAL TELEMETRY
# ============================================================


class ElectricalTelemetry(BaseModel):
    """
    Common electrical measurements associated with a grid asset.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    asset_id: int = Field(
        ...,
        ge=1,
    )

    timestamp: datetime

    voltage_kv: float | None = Field(
        default=None,
        ge=0.0,
    )

    current_a: float | None = Field(
        default=None,
        ge=0.0,
    )

    active_power_mw: float | None = None

    reactive_power_mvar: float | None = None

    apparent_power_mva: float | None = Field(
        default=None,
        ge=0.0,
    )

    frequency_hz: float | None = Field(
        default=None,
        gt=0.0,
    )

    power_factor: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
    )

    loading_percent: float | None = Field(
        default=None,
        ge=0.0,
    )

    temperature_c: float | None = None

    quality: TelemetryQuality = TelemetryQuality.GOOD

    source: TelemetrySource = TelemetrySource.SCADA

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# TELEMETRY QUALITY
# ============================================================


class TelemetryQualityReport(BaseModel):
    """
    Quality assessment for a telemetry data set.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    asset_id: int | None = Field(
        default=None,
        ge=1,
    )

    telemetry_type: TelemetryType | None = None

    total_records: int = Field(
        default=0,
        ge=0,
    )

    valid_records: int = Field(
        default=0,
        ge=0,
    )

    invalid_records: int = Field(
        default=0,
        ge=0,
    )

    missing_records: int = Field(
        default=0,
        ge=0,
    )

    stale_records: int = Field(
        default=0,
        ge=0,
    )

    duplicate_records: int = Field(
        default=0,
        ge=0,
    )

    completeness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    validity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    quality_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    assessed_at: datetime


# ============================================================
# TELEMETRY STATUS
# ============================================================


class TelemetryStatus(BaseModel):
    """
    Latest telemetry status for an asset.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    asset_id: int = Field(
        ...,
        ge=1,
    )

    last_timestamp: datetime | None = None

    last_value: float | None = None

    telemetry_type: TelemetryType

    quality: TelemetryQuality

    source: TelemetrySource

    is_stale: bool = False

    age_seconds: float | None = Field(
        default=None,
        ge=0.0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# TELEMETRY LIST RESPONSE
# ============================================================


class TelemetryListResponse(BaseModel):
    """
    Paginated telemetry response.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[TelemetryResponse] = Field(
        default_factory=list,
    )

    total: int = Field(
        default=0,
        ge=0,
    )

    limit: int = Field(
        default=1000,
        ge=1,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# TELEMETRY EVENT
# ============================================================


class TelemetryEvent(BaseModel):
    """
    Event representation for telemetry ingestion and processing.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    asset_id: int = Field(
        ...,
        ge=1,
    )

    telemetry_type: TelemetryType

    timestamp: datetime

    value: float | None = None

    quality: TelemetryQuality = TelemetryQuality.GOOD

    source: TelemetrySource

    event_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "TelemetryType",
    "TelemetryQuality",
    "TelemetrySource",
    "AggregationType",
    "TelemetryValue",
    "TelemetryBase",
    "TelemetryCreate",
    "TelemetryUpdate",
    "TelemetryResponse",
    "TelemetryBatchCreate",
    "TelemetryBatchResponse",
    "TelemetryQuery",
    "TelemetryFilter",
    "TelemetryPoint",
    "TelemetrySeries",
    "TelemetryAggregate",
    "ElectricalTelemetry",
    "TelemetryQualityReport",
    "TelemetryStatus",
    "TelemetryListResponse",
    "TelemetryEvent",
]