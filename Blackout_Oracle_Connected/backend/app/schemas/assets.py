"""
Blackout Oracle - Asset Schemas.

Pydantic schemas for electrical-grid assets such as substations,
transformers, transmission lines, and other monitored equipment.

These schemas define the API/application data contract and are
kept separate from the SQLAlchemy database models.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# ENUMS
# ============================================================


class AssetType(str, Enum):
    """Supported electrical-grid asset types."""

    SUBSTATION = "substation"
    TRANSFORMER = "transformer"
    TRANSMISSION_LINE = "transmission_line"
    GENERATOR = "generator"
    BUS = "bus"
    BREAKER = "breaker"
    SWITCH = "switch"
    CAPACITOR = "capacitor"
    REACTOR = "reactor"
    OTHER = "other"


class AssetStatus(str, Enum):
    """Operational state of a grid asset."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    FAULT = "fault"
    RETIRED = "retired"
    UNKNOWN = "unknown"


class AssetHealthStatus(str, Enum):
    """Health classification of an asset."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


# ============================================================
# BASE ASSET
# ============================================================


class AssetBase(BaseModel):
    """
    Common fields shared by all asset schemas.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable asset name.",
    )

    asset_type: AssetType = Field(
        ...,
        description="Type of electrical-grid asset.",
    )

    status: AssetStatus = Field(
        default=AssetStatus.ACTIVE,
        description="Current operational status.",
    )

    region: str | None = Field(
        default=None,
        max_length=255,
        description="Geographical or operational region.",
    )

    state: str | None = Field(
        default=None,
        max_length=100,
        description="State or administrative area.",
    )

    district: str | None = Field(
        default=None,
        max_length=100,
        description="District containing the asset.",
    )

    latitude: float | None = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Asset latitude.",
    )

    longitude: float | None = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Asset longitude.",
    )

    voltage_level_kv: float | None = Field(
        default=None,
        gt=0.0,
        description="Nominal voltage level in kV.",
    )

    capacity_mva: float | None = Field(
        default=None,
        gt=0.0,
        description="Rated capacity in MVA.",
    )

    health_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Asset health score from 0 to 100.",
    )

    health_status: AssetHealthStatus = Field(
        default=AssetHealthStatus.UNKNOWN,
        description="Current asset health classification.",
    )

    installation_date: datetime | None = Field(
        default=None,
        description="Asset installation date.",
    )

    last_maintenance_at: datetime | None = Field(
        default=None,
        description="Most recent maintenance timestamp.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional asset metadata.",
    )


# ============================================================
# ASSET CREATE
# ============================================================


class AssetCreate(AssetBase):
    """
    Schema used when creating a new generic asset.
    """

    external_id: str | None = Field(
        default=None,
        max_length=255,
        description="External identifier from the grid operator.",
    )


# ============================================================
# ASSET UPDATE
# ============================================================


class AssetUpdate(BaseModel):
    """
    Schema used for partial updates to an asset.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    status: AssetStatus | None = None

    region: str | None = Field(
        default=None,
        max_length=255,
    )

    state: str | None = Field(
        default=None,
        max_length=100,
    )

    district: str | None = Field(
        default=None,
        max_length=100,
    )

    latitude: float | None = Field(
        default=None,
        ge=-90.0,
        le=90.0,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180.0,
        le=180.0,
    )

    voltage_level_kv: float | None = Field(
        default=None,
        gt=0.0,
    )

    capacity_mva: float | None = Field(
        default=None,
        gt=0.0,
    )

    health_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    health_status: AssetHealthStatus | None = None

    last_maintenance_at: datetime | None = None

    metadata: dict[str, Any] | None = None


# ============================================================
# ASSET RESPONSE
# ============================================================


class AssetResponse(AssetBase):
    """
    API response representing a stored asset.
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

    external_id: str | None = None

    created_at: datetime

    updated_at: datetime


# ============================================================
# SUBSTATION
# ============================================================


class SubstationBase(AssetBase):
    """
    Fields specific to electrical substations.
    """

    asset_type: AssetType = Field(
        default=AssetType.SUBSTATION,
    )

    substation_code: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique substation code.",
    )

    operator: str | None = Field(
        default=None,
        max_length=255,
        description="Grid operator responsible for the substation.",
    )

    bus_count: int | None = Field(
        default=None,
        ge=0,
        description="Number of buses.",
    )

    transformer_count: int | None = Field(
        default=None,
        ge=0,
        description="Number of transformers.",
    )

    criticality_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Grid criticality score from 0 to 100.",
    )


class SubstationCreate(SubstationBase):
    """Schema for creating a substation."""

    external_id: str | None = Field(
        default=None,
        max_length=255,
    )


class SubstationUpdate(BaseModel):
    """Schema for partially updating a substation."""

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    status: AssetStatus | None = None

    region: str | None = Field(
        default=None,
        max_length=255,
    )

    latitude: float | None = Field(
        default=None,
        ge=-90.0,
        le=90.0,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180.0,
        le=180.0,
    )

    operator: str | None = Field(
        default=None,
        max_length=255,
    )

    bus_count: int | None = Field(
        default=None,
        ge=0,
    )

    transformer_count: int | None = Field(
        default=None,
        ge=0,
    )

    criticality_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    health_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    health_status: AssetHealthStatus | None = None

    metadata: dict[str, Any] | None = None


class SubstationResponse(SubstationBase):
    """API response representing a stored substation."""

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        extra="forbid",
    )

    id: int = Field(
        ...,
        ge=1,
    )

    external_id: str | None = None

    created_at: datetime

    updated_at: datetime


# ============================================================
# TRANSFORMER
# ============================================================


class TransformerBase(AssetBase):
    """
    Fields specific to power transformers.
    """

    asset_type: AssetType = Field(
        default=AssetType.TRANSFORMER,
    )

    transformer_code: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique transformer identifier.",
    )

    substation_id: int | None = Field(
        default=None,
        ge=1,
        description="Parent substation identifier.",
    )

    primary_voltage_kv: float | None = Field(
        default=None,
        gt=0.0,
        description="Primary-side voltage in kV.",
    )

    secondary_voltage_kv: float | None = Field(
        default=None,
        gt=0.0,
        description="Secondary-side voltage in kV.",
    )

    rated_power_mva: float | None = Field(
        default=None,
        gt=0.0,
        description="Transformer rated power in MVA.",
    )

    loading_percent: float | None = Field(
        default=None,
        ge=0.0,
        description="Current transformer loading percentage.",
    )

    winding_temperature_c: float | None = Field(
        default=None,
        description="Winding temperature in degrees Celsius.",
    )


class TransformerCreate(TransformerBase):
    """Schema for creating a transformer."""

    external_id: str | None = Field(
        default=None,
        max_length=255,
    )


class TransformerUpdate(BaseModel):
    """Schema for partially updating a transformer."""

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    status: AssetStatus | None = None

    substation_id: int | None = Field(
        default=None,
        ge=1,
    )

    primary_voltage_kv: float | None = Field(
        default=None,
        gt=0.0,
    )

    secondary_voltage_kv: float | None = Field(
        default=None,
        gt=0.0,
    )

    rated_power_mva: float | None = Field(
        default=None,
        gt=0.0,
    )

    loading_percent: float | None = Field(
        default=None,
        ge=0.0,
    )

    winding_temperature_c: float | None = None

    health_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    health_status: AssetHealthStatus | None = None

    metadata: dict[str, Any] | None = None


class TransformerResponse(TransformerBase):
    """API response representing a stored transformer."""

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        extra="forbid",
    )

    id: int = Field(
        ...,
        ge=1,
    )

    external_id: str | None = None

    created_at: datetime

    updated_at: datetime


# ============================================================
# TRANSMISSION LINE
# ============================================================


class TransmissionLineBase(AssetBase):
    """
    Fields specific to transmission lines.
    """

    asset_type: AssetType = Field(
        default=AssetType.TRANSMISSION_LINE,
    )

    line_code: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique transmission-line identifier.",
    )

    from_substation_id: int | None = Field(
        default=None,
        ge=1,
        description="Originating substation identifier.",
    )

    to_substation_id: int | None = Field(
        default=None,
        ge=1,
        description="Receiving substation identifier.",
    )

    length_km: float | None = Field(
        default=None,
        gt=0.0,
        description="Transmission-line length in kilometres.",
    )

    thermal_limit_mva: float | None = Field(
        default=None,
        gt=0.0,
        description="Thermal operating limit in MVA.",
    )

    current_loading_percent: float | None = Field(
        default=None,
        ge=0.0,
        description="Current line loading percentage.",
    )

    conductor_type: str | None = Field(
        default=None,
        max_length=100,
        description="Conductor type.",
    )


class TransmissionLineCreate(TransmissionLineBase):
    """Schema for creating a transmission line."""

    external_id: str | None = Field(
        default=None,
        max_length=255,
    )


class TransmissionLineUpdate(BaseModel):
    """Schema for partially updating a transmission line."""

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    status: AssetStatus | None = None

    from_substation_id: int | None = Field(
        default=None,
        ge=1,
    )

    to_substation_id: int | None = Field(
        default=None,
        ge=1,
    )

    length_km: float | None = Field(
        default=None,
        gt=0.0,
    )

    thermal_limit_mva: float | None = Field(
        default=None,
        gt=0.0,
    )

    current_loading_percent: float | None = Field(
        default=None,
        ge=0.0,
    )

    conductor_type: str | None = Field(
        default=None,
        max_length=100,
    )

    health_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    health_status: AssetHealthStatus | None = None

    metadata: dict[str, Any] | None = None


class TransmissionLineResponse(TransmissionLineBase):
    """API response representing a stored transmission line."""

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        extra="forbid",
    )

    id: int = Field(
        ...,
        ge=1,
    )

    external_id: str | None = None

    created_at: datetime

    updated_at: datetime


# ============================================================
# ASSET FILTER
# ============================================================


class AssetFilter(BaseModel):
    """
    Filters for querying grid assets.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    asset_type: AssetType | None = None

    status: AssetStatus | None = None

    health_status: AssetHealthStatus | None = None

    region: str | None = Field(
        default=None,
        max_length=255,
    )

    state: str | None = Field(
        default=None,
        max_length=100,
    )

    district: str | None = Field(
        default=None,
        max_length=100,
    )

    min_health_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    max_health_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    min_voltage_level_kv: float | None = Field(
        default=None,
        gt=0.0,
    )

    max_voltage_level_kv: float | None = Field(
        default=None,
        gt=0.0,
    )

    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# ASSET LIST RESPONSE
# ============================================================


class AssetListResponse(BaseModel):
    """
    Paginated asset response.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[AssetResponse] = Field(
        default_factory=list,
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


# ============================================================
# ASSET HEALTH
# ============================================================


class AssetHealthResponse(BaseModel):
    """
    Current health assessment for an asset.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    asset_id: int = Field(
        ...,
        ge=1,
    )

    health_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
    )

    health_status: AssetHealthStatus

    failure_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    assessed_at: datetime

    factors: dict[str, float] = Field(
        default_factory=dict,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "AssetType",
    "AssetStatus",
    "AssetHealthStatus",
    "AssetBase",
    "AssetCreate",
    "AssetUpdate",
    "AssetResponse",
    "SubstationBase",
    "SubstationCreate",
    "SubstationUpdate",
    "SubstationResponse",
    "TransformerBase",
    "TransformerCreate",
    "TransformerUpdate",
    "TransformerResponse",
    "TransmissionLineBase",
    "TransmissionLineCreate",
    "TransmissionLineUpdate",
    "TransmissionLineResponse",
    "AssetFilter",
    "AssetListResponse",
    "AssetHealthResponse",
]