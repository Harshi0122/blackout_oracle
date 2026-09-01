"""
Blackout Oracle - Grid Asset API Routes.

This module exposes HTTP endpoints for viewing and managing the logical
representation of electrical-grid assets.

Supported asset categories include:

- Substations
- Transformers
- Feeders
- Transmission lines
- Generators
- Loads
- Buses

IMPORTANT
---------

These endpoints operate on Blackout Oracle's internal grid representation.

They do NOT:

- Control real electrical equipment.
- Operate breakers.
- Modify SCADA.
- Change real substation settings.
- Send commands to utility infrastructure.

The initial implementation uses an in-memory development store.
It will later be replaced by PostgreSQL/PostGIS persistence.
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
    prefix="/assets",
    tags=["Grid Assets"],
)


# ============================================================
# ENUMS
# ============================================================


class AssetType(str, Enum):
    """Supported Blackout Oracle grid asset types."""

    SUBSTATION = "substation"
    TRANSFORMER = "transformer"
    FEEDER = "feeder"
    TRANSMISSION_LINE = "transmission_line"
    GENERATOR = "generator"
    SOLAR = "solar"
    WIND = "wind"
    BATTERY = "battery"
    LOAD = "load"
    INDUSTRIAL = "industrial"
    RESIDENTIAL = "residential"
    HOSPITAL = "hospital"
    CRITICAL = "critical"
    BUS = "bus"


class AssetStatus(str, Enum):
    """Logical operational status of an asset."""

    UNKNOWN = "unknown"
    NORMAL = "normal"
    DEGRADED = "degraded"
    WARNING = "warning"
    FAILED = "failed"
    OFFLINE = "offline"


class DataSourceType(str, Enum):
    """Source classification for asset information."""

    SYNTHETIC = "synthetic"
    PUBLIC = "public"
    AUTHORIZED_TELEMETRY = "authorized_telemetry"
    HISTORICAL = "historical"
    MANUAL = "manual"


# ============================================================
# SCHEMAS
# ============================================================


class GeoPoint(BaseModel):
    """Geographical location of an asset."""

    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
    )


class AssetCreate(BaseModel):
    """Request model for creating a grid asset."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    asset_type: AssetType

    region_id: str | None = Field(
        default=None,
        max_length=100,
    )

    region_name: str | None = Field(
        default=None,
        max_length=200,
    )

    parent_asset_id: str | None = Field(
        default=None,
        max_length=100,
    )

    location: GeoPoint | None = None

    rated_capacity_mw: float | None = Field(
        default=None,
        ge=0,
    )

    voltage_kv: float | None = Field(
        default=None,
        ge=0,
    )

    status: AssetStatus = AssetStatus.UNKNOWN

    source: DataSourceType = DataSourceType.SYNTHETIC

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class AssetUpdate(BaseModel):
    """Request model for updating internal asset metadata."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    region_id: str | None = None

    region_name: str | None = None

    parent_asset_id: str | None = None

    location: GeoPoint | None = None

    rated_capacity_mw: float | None = Field(
        default=None,
        ge=0,
    )

    voltage_kv: float | None = Field(
        default=None,
        ge=0,
    )

    status: AssetStatus | None = None

    metadata: dict[str, Any] | None = None


class AssetResponse(BaseModel):
    """Response model representing a grid asset."""

    id: str

    name: str

    asset_type: AssetType

    region_id: str | None = None
    region_name: str | None = None

    parent_asset_id: str | None = None

    location: GeoPoint | None = None

    rated_capacity_mw: float | None = None

    voltage_kv: float | None = None

    status: AssetStatus

    source: DataSourceType

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    created_at: datetime
    updated_at: datetime


class AssetStatusResponse(BaseModel):
    """Current status information for an asset."""

    asset_id: str

    status: AssetStatus

    timestamp: datetime

    source: DataSourceType

    telemetry_available: bool

    telemetry_age_seconds: float | None = None

    latest_measurements: dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# DEVELOPMENT STORE
# ============================================================

# Temporary in-memory storage.
#
# This will later be replaced by PostgreSQL/PostGIS repositories.

_ASSETS: dict[str, AssetResponse] = {}


# ============================================================
# CREATE ASSET
# ============================================================


@router.post(
    "",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_asset(
    asset: AssetCreate,
) -> AssetResponse:
    """
    Create an asset in Blackout Oracle's internal grid model.

    This creates only an internal representation.

    It does NOT create or modify a real-world electrical asset.
    """

    asset_id = (
        f"AST-{uuid4().hex[:12].upper()}"
    )

    now = datetime.now(timezone.utc)

    response = AssetResponse(
        id=asset_id,
        name=asset.name,
        asset_type=asset.asset_type,
        region_id=asset.region_id,
        region_name=asset.region_name,
        parent_asset_id=asset.parent_asset_id,
        location=asset.location,
        rated_capacity_mw=asset.rated_capacity_mw,
        voltage_kv=asset.voltage_kv,
        status=asset.status,
        source=asset.source,
        metadata=asset.metadata,
        created_at=now,
        updated_at=now,
    )

    _ASSETS[asset_id] = response

    return response


# ============================================================
# LIST ASSETS
# ============================================================


@router.get(
    "",
    response_model=list[AssetResponse],
)
async def list_assets(
    asset_type: AssetType | None = Query(
        default=None,
        description="Filter by asset type.",
    ),
    region_id: str | None = Query(
        default=None,
        description="Filter by region.",
    ),
    asset_status: AssetStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by asset status.",
    ),
    source: DataSourceType | None = Query(
        default=None,
        description="Filter by data source.",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of assets to return.",
    ),
) -> list[AssetResponse]:
    """
    List grid assets using optional filters.
    """

    assets = list(
        _ASSETS.values()
    )

    if asset_type is not None:
        assets = [
            asset
            for asset in assets
            if asset.asset_type == asset_type
        ]

    if region_id is not None:
        assets = [
            asset
            for asset in assets
            if asset.region_id == region_id
        ]

    if asset_status is not None:
        assets = [
            asset
            for asset in assets
            if asset.status == asset_status
        ]

    if source is not None:
        assets = [
            asset
            for asset in assets
            if asset.source == source
        ]

    assets.sort(
        key=lambda asset: asset.name.lower()
    )

    return assets[:limit]


# ============================================================
# GET ASSET
# ============================================================


@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
)
async def get_asset(
    asset_id: str,
) -> AssetResponse:
    """
    Retrieve one grid asset.
    """

    asset = _ASSETS.get(
        asset_id
    )

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Asset '{asset_id}' was not found."
            ),
        )

    return asset


# ============================================================
# UPDATE ASSET
# ============================================================


@router.patch(
    "/{asset_id}",
    response_model=AssetResponse,
)
async def update_asset(
    asset_id: str,
    update: AssetUpdate,
) -> AssetResponse:
    """
    Update the internal representation of a grid asset.

    This modifies only Blackout Oracle's internal data.

    It does NOT modify any real electrical infrastructure.
    """

    asset = _ASSETS.get(
        asset_id
    )

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Asset '{asset_id}' was not found."
            ),
        )

    update_data = update.model_dump(
        exclude_unset=True
    )

    for field_name, value in update_data.items():
        setattr(
            asset,
            field_name,
            value,
        )

    asset.updated_at = (
        datetime.now(timezone.utc)
    )

    return asset


# ============================================================
# DELETE ASSET
# ============================================================


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_asset(
    asset_id: str,
) -> None:
    """
    Delete an asset from the internal grid model.

    This does NOT delete or disable a real-world asset.
    """

    if asset_id not in _ASSETS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Asset '{asset_id}' was not found."
            ),
        )

    del _ASSETS[asset_id]


# ============================================================
# ASSET STATUS
# ============================================================


@router.get(
    "/{asset_id}/status",
    response_model=AssetStatusResponse,
)
async def get_asset_status(
    asset_id: str,
) -> AssetStatusResponse:
    """
    Retrieve the latest known status for an asset.

    Telemetry integration will be connected later.
    """

    asset = _ASSETS.get(
        asset_id
    )

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Asset '{asset_id}' was not found."
            ),
        )

    return AssetStatusResponse(
        asset_id=asset.id,
        status=asset.status,
        timestamp=asset.updated_at,
        source=asset.source,
        telemetry_available=False,
        telemetry_age_seconds=None,
        latest_measurements={},
    )


# ============================================================
# ASSET TELEMETRY SUMMARY
# ============================================================


@router.get(
    "/{asset_id}/telemetry",
    response_model=dict[str, Any],
)
async def get_asset_telemetry(
    asset_id: str,
) -> dict[str, Any]:
    """
    Return the latest telemetry associated with an asset.

    This is currently a placeholder for the telemetry service.

    Future implementation will retrieve data from the normalized telemetry
    pipeline rather than directly accessing utility systems.
    """

    asset = _ASSETS.get(
        asset_id
    )

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Asset '{asset_id}' was not found."
            ),
        )

    return {
        "asset_id": asset.id,
        "asset_name": asset.name,
        "status": "not_implemented",
        "telemetry_available": False,
        "latest_measurements": {},
        "message": (
            "Telemetry service has not been connected yet."
        ),
    }


# ============================================================
# ASSET SUMMARY
# ============================================================


@router.get(
    "/summary/counts",
    response_model=dict[str, int],
)
async def asset_summary() -> dict[str, int]:
    """
    Return counts of assets by type and status.
    """

    summary: dict[str, int] = {
        "total": len(_ASSETS),
    }

    for asset_type in AssetType:
        summary[
            asset_type.value
        ] = 0

    for asset_status in AssetStatus:
        summary[
            asset_status.value
        ] = 0

    for asset in _ASSETS.values():
        summary[
            asset.asset_type.value
        ] += 1

        summary[
            asset.status.value
        ] += 1

    return summary


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "router",
    "AssetType",
    "AssetStatus",
    "DataSourceType",
    "GeoPoint",
    "AssetCreate",
    "AssetUpdate",
    "AssetResponse",
    "AssetStatusResponse",
]