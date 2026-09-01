"""
Blackout Oracle - Common Schemas.

Shared Pydantic schemas used across the API, database,
ingestion, grid, risk, incident, simulation, and ML layers.

This module contains generic structures such as:

- API responses
- Pagination
- Geographic coordinates
- Time ranges
- Health/status information
- Error responses
- Generic identifiers
- Risk summaries
- Timestamped records

The schemas are intentionally independent of SQLAlchemy models
to avoid circular dependencies between application layers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ============================================================
# GENERIC TYPES
# ============================================================

T = TypeVar("T")


# ============================================================
# ENUMS
# ============================================================


class HealthStatus(str, Enum):
    """Generic service health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServiceStatus(str, Enum):
    """Generic application/service status."""

    ONLINE = "online"
    OFFLINE = "offline"
    STARTING = "starting"
    STOPPING = "stopping"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class SortOrder(str, Enum):
    """Sorting direction."""

    ASC = "asc"
    DESC = "desc"


# ============================================================
# TIMESTAMP
# ============================================================


class TimestampMixin(BaseModel):
    """
    Shared timestamp fields for API schemas.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    created_at: datetime | None = None

    updated_at: datetime | None = None


class TimestampedResponse(TimestampMixin):
    """
    Generic response containing a timestamp.
    """

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


# ============================================================
# IDENTIFIER
# ============================================================


class IDResponse(BaseModel):
    """
    Generic object identifier response.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    id: int = Field(
        ...,
        ge=1,
    )


class IdentifierSchema(BaseModel):
    """
    Generic identifier that can optionally carry an external ID.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    id: int | None = Field(
        default=None,
        ge=1,
    )

    external_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )


# ============================================================
# PAGINATION
# ============================================================


class PaginationParams(BaseModel):
    """
    Standard pagination parameters.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of records to return.",
    )

    offset: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip.",
    )


class PaginationMeta(BaseModel):
    """
    Metadata describing a paginated response.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    total: int = Field(
        default=0,
        ge=0,
    )

    limit: int = Field(
        default=100,
        ge=1,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )

    has_next: bool = False

    has_previous: bool = False


class PaginatedResponse(
    BaseModel,
    Generic[T],
):
    """
    Generic paginated API response.

    Example:

        PaginatedResponse[AssetResponse]
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    items: list[T] = Field(
        default_factory=list,
    )

    meta: PaginationMeta


# ============================================================
# SORTING
# ============================================================


class SortParams(BaseModel):
    """
    Standard sorting parameters.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    sort_by: str | None = Field(
        default=None,
        max_length=100,
    )

    sort_order: SortOrder = (
        SortOrder.ASC
    )


# ============================================================
# GEOGRAPHIC DATA
# ============================================================


class Coordinates(BaseModel):
    """
    Geographic coordinates.

    Latitude and longitude use decimal degrees.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
    )

    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
    )


class BoundingBox(BaseModel):
    """
    Geographic bounding box.

    Used for regional grid queries and map-based filtering.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    min_latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
    )

    max_latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
    )

    min_longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
    )

    max_longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
    )


# ============================================================
# TIME RANGE
# ============================================================


class TimeRange(BaseModel):
    """
    Generic time range used by telemetry, historical data,
    incidents, simulations, and analytics.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    start_time: datetime

    end_time: datetime

    def validate_order(self) -> "TimeRange":
        """
        Validate that the end time does not precede the start time.
        """

        if self.end_time < self.start_time:
            raise ValueError(
                "end_time cannot be earlier than start_time."
            )

        return self


class TimeWindow(BaseModel):
    """
    Time window with an optional duration in seconds.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    start_time: datetime

    end_time: datetime | None = None

    duration_seconds: float | None = Field(
        default=None,
        ge=0.0,
    )


# ============================================================
# RANGE
# ============================================================


class NumericRange(BaseModel):
    """
    Generic numeric range.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    minimum: float | None = None

    maximum: float | None = None

    def validate_order(self) -> "NumericRange":
        """Validate numeric range ordering."""

        if (
            self.minimum is not None
            and self.maximum is not None
            and self.maximum < self.minimum
        ):
            raise ValueError(
                "maximum cannot be less than minimum."
            )

        return self


# ============================================================
# HEALTH
# ============================================================


class HealthResponse(BaseModel):
    """
    Generic service health response.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    status: HealthStatus

    service: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    version: str | None = None

    details: dict[str, Any] = Field(
        default_factory=dict,
    )


class ServiceStatusResponse(BaseModel):
    """
    Generic service status response.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    service: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    status: ServiceStatus

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    message: str | None = None

    details: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# ERROR RESPONSES
# ============================================================


class ErrorDetail(BaseModel):
    """
    Detailed API error information.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    field: str | None = None

    message: str

    code: str | None = None

    details: dict[str, Any] = Field(
        default_factory=dict,
    )


class ErrorResponse(BaseModel):
    """
    Standard API error response.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    success: bool = False

    error: str

    message: str

    status_code: int = Field(
        ...,
        ge=400,
        le=599,
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    details: list[ErrorDetail] = Field(
        default_factory=list,
    )

    request_id: str | None = None


# ============================================================
# GENERIC API RESPONSE
# ============================================================


class APIResponse(
    BaseModel,
    Generic[T],
):
    """
    Generic successful API response.

    Example:

        APIResponse[AssetResponse]
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    success: bool = True

    data: T | None = None

    message: str | None = None

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    request_id: str | None = None


# ============================================================
# RISK SUMMARY
# ============================================================


class RiskSummary(BaseModel):
    """
    Generic risk summary shared by risk-related API responses.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
    )

    probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    level: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    alert_required: bool = False

    critical: bool = False

    factors: dict[str, float] = Field(
        default_factory=dict,
    )


# ============================================================
# METRIC
# ============================================================


class MetricValue(BaseModel):
    """
    Generic measured metric.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    value: float

    unit: str | None = Field(
        default=None,
        max_length=50,
    )

    timestamp: datetime | None = None

    quality: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# KEY-VALUE DATA
# ============================================================


class KeyValue(BaseModel):
    """
    Generic key-value structure.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    key: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    value: Any = None


# ============================================================
# OPERATION RESULT
# ============================================================


class OperationResult(BaseModel):
    """
    Generic result for an application operation.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    success: bool

    message: str

    operation: str | None = None

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    data: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# BULK OPERATION
# ============================================================


class BulkOperationResult(BaseModel):
    """
    Result of a bulk application operation.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    success: bool

    total: int = Field(
        default=0,
        ge=0,
    )

    succeeded: int = Field(
        default=0,
        ge=0,
    )

    failed: int = Field(
        default=0,
        ge=0,
    )

    errors: list[ErrorDetail] = Field(
        default_factory=list,
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


# ============================================================
# CONFIDENCE
# ============================================================


class ConfidenceScore(BaseModel):
    """
    Generic confidence value used by ML and risk services.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    source: str | None = Field(
        default=None,
        max_length=255,
    )

    explanation: str | None = Field(
        default=None,
        max_length=2000,
    )


# ============================================================
# PAGINATION HELPER
# ============================================================


def create_pagination_meta(
    total: int,
    limit: int,
    offset: int,
) -> PaginationMeta:
    """
    Create pagination metadata from query parameters.
    """

    total = max(
        0,
        int(total),
    )

    limit = max(
        1,
        int(limit),
    )

    offset = max(
        0,
        int(offset),
    )

    return PaginationMeta(
        total=total,
        limit=limit,
        offset=offset,
        has_next=(
            offset + limit
            < total
        ),
        has_previous=(
            offset > 0
        ),
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "T",
    "HealthStatus",
    "ServiceStatus",
    "SortOrder",
    "TimestampMixin",
    "TimestampedResponse",
    "IDResponse",
    "IdentifierSchema",
    "PaginationParams",
    "PaginationMeta",
    "PaginatedResponse",
    "SortParams",
    "Coordinates",
    "BoundingBox",
    "TimeRange",
    "TimeWindow",
    "NumericRange",
    "HealthResponse",
    "ServiceStatusResponse",
    "ErrorDetail",
    "ErrorResponse",
    "APIResponse",
    "RiskSummary",
    "MetricValue",
    "KeyValue",
    "OperationResult",
    "BulkOperationResult",
    "ConfidenceScore",
    "create_pagination_meta",
]