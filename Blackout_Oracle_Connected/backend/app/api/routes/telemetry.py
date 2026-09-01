"""
Blackout Oracle - Telemetry API Routes.

This module exposes API endpoints for receiving, querying, and summarizing
electrical-grid telemetry.

Telemetry may eventually include:

- Voltage
- Current
- Frequency
- Active power
- Reactive power
- Apparent power
- Load
- Generation
- Power factor
- Transformer temperature
- Breaker status
- Feeder status
- Asset health indicators

IMPORTANT
---------

This module is responsible for the API boundary only.

It does NOT:

- Control electrical equipment.
- Operate breakers.
- Modify SCADA.
- Change substation configuration.
- Send commands to real infrastructure.

Telemetry ingestion must use authorized data sources.

For early development this module uses an in-memory store. Production
implementation will use PostgreSQL/TimescaleDB and the telemetry ingestion
pipeline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/telemetry",
    tags=["Telemetry"],
)


# ============================================================
# ENUMS
# ============================================================


class MeasurementType(str, Enum):
    """Supported electrical measurements."""

    VOLTAGE = "voltage"
    CURRENT = "current"
    FREQUENCY = "frequency"
    ACTIVE_POWER = "active_power"
    REACTIVE_POWER = "reactive_power"
    APPARENT_POWER = "apparent_power"
    POWER_FACTOR = "power_factor"
    LOAD = "load"
    GENERATION = "generation"
    TEMPERATURE = "temperature"


class TelemetryQuality(str, Enum):
    """Quality classification for telemetry."""

    GOOD = "good"
    UNCERTAIN = "uncertain"
    BAD = "bad"
    STALE = "stale"
    MISSING = "missing"


class TelemetrySource(str, Enum):
    """Authorized telemetry source categories."""

    SYNTHETIC = "synthetic"
    HISTORICAL = "historical"
    PUBLIC_API = "public_api"
    AUTHORIZED_UTILITY = "authorized_utility"
    MANUAL = "manual"


# ============================================================
# REQUEST SCHEMAS
# ============================================================


class TelemetryPointCreate(BaseModel):
    """
    A single telemetry measurement.

    Example:

        voltage = 230
        unit = kV
        timestamp = current UTC time
    """

    asset_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Grid asset producing the measurement.",
    )

    measurement_type: MeasurementType

    value: float = Field(
        ...,
        description="Numeric measurement value.",
    )

    unit: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Measurement unit.",
    )

    timestamp: datetime = Field(
        ...,
        description="Timestamp of the measurement.",
    )

    quality: TelemetryQuality = (
        TelemetryQuality.GOOD
    )

    source: TelemetrySource = (
        TelemetrySource.SYNTHETIC
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class TelemetryBatchCreate(BaseModel):
    """Request model for submitting multiple telemetry points."""

    measurements: list[TelemetryPointCreate] = Field(
        ...,
        min_length=1,
        max_length=10000,
    )


# ============================================================
# RESPONSE SCHEMAS
# ============================================================


class TelemetryPointResponse(BaseModel):
    """Response representation of a telemetry point."""

    id: str

    asset_id: str

    measurement_type: MeasurementType

    value: float

    unit: str

    timestamp: datetime

    received_at: datetime

    quality: TelemetryQuality

    source: TelemetrySource

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class TelemetryBatchResponse(BaseModel):
    """Response for a telemetry batch ingestion request."""

    accepted: int

    rejected: int

    measurements: list[TelemetryPointResponse]


class TelemetryLatestResponse(BaseModel):
    """Latest telemetry for one asset."""

    asset_id: str

    measurements: dict[str, TelemetryPointResponse]

    latest_timestamp: datetime | None = None


class TelemetryHealthResponse(BaseModel):
    """Telemetry freshness/health information."""

    asset_id: str | None = None

    telemetry_available: bool

    latest_timestamp: datetime | None = None

    age_seconds: float | None = None

    quality: TelemetryQuality

    source: TelemetrySource | None = None


# ============================================================
# DEVELOPMENT STORE
# ============================================================

# Temporary in-memory telemetry storage.
#
# Production:
#
#     Authorized source
#           ↓
#     Ingestion adapter
#           ↓
#     Validation
#           ↓
#     Normalization
#           ↓
#     TimescaleDB
#           ↓
#     Risk/ML pipeline
#
# The API should NOT directly scrape or control utility infrastructure.

_TELEMETRY: list[TelemetryPointResponse] = []


# ============================================================
# VALIDATION HELPERS
# ============================================================


def _validate_timestamp(
    timestamp: datetime,
) -> datetime:
    """
    Normalize a timestamp to timezone-aware UTC.

    Naive timestamps are rejected because time alignment is critical
    for time-series grid analysis.
    """

    if timestamp.tzinfo is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Telemetry timestamp must include timezone information."
            ),
        )

    return timestamp.astimezone(
        timezone.utc
    )


# ============================================================
# INGEST SINGLE TELEMETRY POINT
# ============================================================


@router.post(
    "",
    response_model=TelemetryPointResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_telemetry(
    telemetry: TelemetryPointCreate,
) -> TelemetryPointResponse:
    """
    Ingest one telemetry measurement.

    This endpoint is intended for authorized/internal ingestion clients.

    It does not connect directly to a utility SCADA system.
    """

    timestamp = _validate_timestamp(
        telemetry.timestamp
    )

    received_at = datetime.now(
        timezone.utc
    )

    telemetry_id = (
        f"TEL-{uuid4().hex[:12].upper()}"
    )

    response = TelemetryPointResponse(
        id=telemetry_id,
        asset_id=telemetry.asset_id,
        measurement_type=telemetry.measurement_type,
        value=telemetry.value,
        unit=telemetry.unit,
        timestamp=timestamp,
        received_at=received_at,
        quality=telemetry.quality,
        source=telemetry.source,
        metadata=telemetry.metadata,
    )

    _TELEMETRY.append(
        response
    )

    return response


# ============================================================
# INGEST BATCH
# ============================================================


@router.post(
    "/batch",
    response_model=TelemetryBatchResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_telemetry_batch(
    batch: TelemetryBatchCreate,
) -> TelemetryBatchResponse:
    """
    Ingest multiple telemetry measurements.

    Batch ingestion will be important when the real telemetry pipeline
    begins sending high-frequency measurements.
    """

    accepted: list[TelemetryPointResponse] = []
    rejected = 0

    received_at = datetime.now(
        timezone.utc
    )

    for telemetry in batch.measurements:

        try:
            timestamp = _validate_timestamp(
                telemetry.timestamp
            )

            telemetry_id = (
                f"TEL-{uuid4().hex[:12].upper()}"
            )

            response = TelemetryPointResponse(
                id=telemetry_id,
                asset_id=telemetry.asset_id,
                measurement_type=(
                    telemetry.measurement_type
                ),
                value=telemetry.value,
                unit=telemetry.unit,
                timestamp=timestamp,
                received_at=received_at,
                quality=telemetry.quality,
                source=telemetry.source,
                metadata=telemetry.metadata,
            )

            _TELEMETRY.append(
                response
            )

            accepted.append(
                response
            )

        except HTTPException:
            rejected += 1

    return TelemetryBatchResponse(
        accepted=len(accepted),
        rejected=rejected,
        measurements=accepted,
    )


# ============================================================
# LATEST TELEMETRY
# ============================================================


@router.get(
    "/latest/{asset_id}",
    response_model=TelemetryLatestResponse,
)
async def get_latest_telemetry(
    asset_id: str,
) -> TelemetryLatestResponse:
    """
    Retrieve the latest known measurement of each type for an asset.
    """

    asset_measurements = [
        point
        for point in _TELEMETRY
        if point.asset_id == asset_id
    ]

    if not asset_measurements:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No telemetry found for asset '{asset_id}'."
            ),
        )

    latest: dict[
        str,
        TelemetryPointResponse,
    ] = {}

    for point in asset_measurements:

        key = point.measurement_type.value

        current = latest.get(
            key
        )

        if (
            current is None
            or point.timestamp > current.timestamp
        ):
            latest[key] = point

    timestamps = [
        point.timestamp
        for point in latest.values()
    ]

    latest_timestamp = (
        max(timestamps)
        if timestamps
        else None
    )

    return TelemetryLatestResponse(
        asset_id=asset_id,
        measurements=latest,
        latest_timestamp=latest_timestamp,
    )


# ============================================================
# QUERY TELEMETRY
# ============================================================


@router.get(
    "",
    response_model=list[TelemetryPointResponse],
)
async def query_telemetry(
    asset_id: str | None = Query(
        default=None,
        description="Filter by asset.",
    ),
    measurement_type: MeasurementType | None = Query(
        default=None,
        description="Filter by measurement type.",
    ),
    quality: TelemetryQuality | None = Query(
        default=None,
        description="Filter by telemetry quality.",
    ),
    source: TelemetrySource | None = Query(
        default=None,
        description="Filter by telemetry source.",
    ),
    start_time: datetime | None = Query(
        default=None,
        description="Start of time range.",
    ),
    end_time: datetime | None = Query(
        default=None,
        description="End of time range.",
    ),
    limit: int = Query(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum number of points.",
    ),
) -> list[TelemetryPointResponse]:
    """
    Query telemetry measurements.

    Production implementation will execute this query against
    TimescaleDB rather than the in-memory store.
    """

    telemetry = list(
        _TELEMETRY
    )

    if asset_id is not None:
        telemetry = [
            point
            for point in telemetry
            if point.asset_id == asset_id
        ]

    if measurement_type is not None:
        telemetry = [
            point
            for point in telemetry
            if point.measurement_type
            == measurement_type
        ]

    if quality is not None:
        telemetry = [
            point
            for point in telemetry
            if point.quality == quality
        ]

    if source is not None:
        telemetry = [
            point
            for point in telemetry
            if point.source == source
        ]

    if start_time is not None:

        start_time = _validate_timestamp(
            start_time
        )

        telemetry = [
            point
            for point in telemetry
            if point.timestamp >= start_time
        ]

    if end_time is not None:

        end_time = _validate_timestamp(
            end_time
        )

        telemetry = [
            point
            for point in telemetry
            if point.timestamp <= end_time
        ]

    telemetry.sort(
        key=lambda point: point.timestamp,
        reverse=True,
    )

    return telemetry[:limit]


# ============================================================
# TELEMETRY HEALTH
# ============================================================


@router.get(
    "/health",
    response_model=TelemetryHealthResponse,
)
async def telemetry_health(
    asset_id: str | None = Query(
        default=None,
        description="Optional asset to check.",
    ),
) -> TelemetryHealthResponse:
    """
    Determine telemetry freshness.

    Freshness is critical for Blackout Oracle because an old telemetry
    reading must not be treated as real-time information.
    """

    telemetry = list(
        _TELEMETRY
    )

    if asset_id is not None:
        telemetry = [
            point
            for point in telemetry
            if point.asset_id == asset_id
        ]

    if not telemetry:
        return TelemetryHealthResponse(
            asset_id=asset_id,
            telemetry_available=False,
            latest_timestamp=None,
            age_seconds=None,
            quality=TelemetryQuality.MISSING,
            source=None,
        )

    latest = max(
        telemetry,
        key=lambda point: point.timestamp,
    )

    now = datetime.now(
        timezone.utc
    )

    age_seconds = (
        now - latest.timestamp
    ).total_seconds()

    if age_seconds < 0:
        age_seconds = 0.0

    quality = latest.quality

    if age_seconds > 300:
        quality = TelemetryQuality.STALE

    return TelemetryHealthResponse(
        asset_id=asset_id,
        telemetry_available=True,
        latest_timestamp=latest.timestamp,
        age_seconds=age_seconds,
        quality=quality,
        source=latest.source,
    )


# ============================================================
# TELEMETRY SUMMARY
# ============================================================


@router.get(
    "/summary",
    response_model=dict[str, Any],
)
async def telemetry_summary(
    asset_id: str | None = Query(
        default=None,
    ),
) -> dict[str, Any]:
    """
    Return a telemetry pipeline summary.
    """

    telemetry = list(
        _TELEMETRY
    )

    if asset_id is not None:
        telemetry = [
            point
            for point in telemetry
            if point.asset_id == asset_id
        ]

    if not telemetry:
        return {
            "total_measurements": 0,
            "assets": 0,
            "measurement_types": {},
            "sources": {},
            "total_load_mw": 0.0,
            "total_generation_mw": 0.0,
            "frequency_hz": 50.0,
            "voltage_kv": 230.0,
        }

    assets = {
        point.asset_id
        for point in telemetry
    }

    measurement_counts: dict[
        str,
        int,
    ] = {}

    source_counts: dict[
        str,
        int,
    ] = {}

    for point in telemetry:

        measurement_key = (
            point.measurement_type.value
        )

        measurement_counts[
            measurement_key
        ] = (
            measurement_counts.get(
                measurement_key,
                0,
            )
            + 1
        )

        source_key = point.source.value

        source_counts[
            source_key
        ] = (
            source_counts.get(
                source_key,
                0,
            )
            + 1
        )

    latest_timestamp = max(
        point.timestamp
        for point in telemetry
    )

    # Compute grid-level aggregates from telemetry data.
    # The frontend expects total_load_mw, total_generation_mw,
    # frequency_hz, and voltage_kv for the dashboard summary.
    total_load_mw = 0.0
    total_generation_mw = 0.0
    latest_frequency: float | None = None
    latest_frequency_ts: datetime | None = None
    latest_voltage: float | None = None
    latest_voltage_ts: datetime | None = None

    for point in telemetry:
        mt = point.measurement_type.value
        if mt == "load":
            total_load_mw += point.value
        elif mt == "generation":
            total_generation_mw += point.value
        elif mt == "frequency":
            if (
                latest_frequency_ts is None
                or point.timestamp > latest_frequency_ts
            ):
                latest_frequency = point.value
                latest_frequency_ts = point.timestamp
        elif mt == "voltage":
            if (
                latest_voltage_ts is None
                or point.timestamp > latest_voltage_ts
            ):
                latest_voltage = point.value
                latest_voltage_ts = point.timestamp

    return {
        "total_measurements": len(
            telemetry
        ),
        "assets": len(
            assets
        ),
        "measurement_types": (
            measurement_counts
        ),
        "sources": source_counts,
        "latest_timestamp": (
            latest_timestamp.isoformat()
        ),
        "total_load_mw": round(total_load_mw, 2),
        "total_generation_mw": round(total_generation_mw, 2),
        "frequency_hz": round(latest_frequency, 4) if latest_frequency is not None else 50.0,
        "voltage_kv": round(latest_voltage, 2) if latest_voltage is not None else 230.0,
    }


# ============================================================
# CLEAR DEVELOPMENT DATA
# ============================================================


@router.delete(
    "/development/clear",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_development_telemetry() -> None:
    """
    Clear in-memory telemetry.

    DEVELOPMENT ONLY.

    This endpoint must be removed or disabled before production deployment.
    """

    _TELEMETRY.clear()


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "router",
    "MeasurementType",
    "TelemetryQuality",
    "TelemetrySource",
    "TelemetryPointCreate",
    "TelemetryBatchCreate",
    "TelemetryPointResponse",
    "TelemetryBatchResponse",
    "TelemetryLatestResponse",
    "TelemetryHealthResponse",
]