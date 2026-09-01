"""
Blackout Oracle - Grid Asset Database Model.

Represents electrical-grid assets monitored by Blackout Oracle.

Supported asset types include:

- Substations
- Transformers
- Transmission lines
- Distribution feeders
- Generators
- Switchgear
- Circuit breakers
- Busbars
- Other grid infrastructure

IMPORTANT
---------

This model stores information about grid infrastructure.

It does NOT provide direct control of physical electrical equipment.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# ============================================================
# ENUMS
# ============================================================


class AssetType(str, Enum):
    """
    Type of electrical-grid asset.
    """

    SUBSTATION = "substation"
    TRANSFORMER = "transformer"
    TRANSMISSION_LINE = "transmission_line"
    DISTRIBUTION_FEEDER = "distribution_feeder"
    GENERATOR = "generator"
    SWITCHGEAR = "switchgear"
    CIRCUIT_BREAKER = "circuit_breaker"
    BUSBAR = "busbar"
    CAPACITOR_BANK = "capacitor_bank"
    REACTOR = "reactor"
    OTHER = "other"


class AssetStatus(str, Enum):
    """
    Current operational status of an asset.
    """

    UNKNOWN = "unknown"
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    FAILED = "failed"


class AssetCriticality(str, Enum):
    """
    Importance of an asset to grid reliability.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# ASSET MODEL
# ============================================================


class Asset(Base):
    """
    SQLAlchemy model representing a monitored grid asset.
    """

    __tablename__ = "assets"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"AST-{uuid4().hex[:12].upper()}"
        ),
    )

    # ========================================================
    # IDENTIFICATION
    # ========================================================

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    asset_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    external_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        unique=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # LOCATION
    # ========================================================

    region_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    region_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    elevation_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # ELECTRICAL CHARACTERISTICS
    # ========================================================

    nominal_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    maximum_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    minimum_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rated_power_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rated_current_a: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # ASSET STATUS
    # ========================================================

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=AssetStatus.UNKNOWN.value,
        index=True,
    )

    criticality: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AssetCriticality.MEDIUM.value,
        index=True,
    )

    is_monitored: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # ========================================================
    # MONITORING INFORMATION
    # ========================================================

    telemetry_source: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    telemetry_asset_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    last_telemetry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ========================================================
    # MAINTENANCE
    # ========================================================

    installation_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    commissioning_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_maintenance_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    next_maintenance_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ========================================================
    # RELIABILITY
    # ========================================================

    failure_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    historical_failure_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    health_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # ENVIRONMENTAL EXPOSURE
    # ========================================================

    flood_exposure_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    storm_exposure_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    temperature_exposure_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # METADATA
    # ========================================================

    owner: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    operator: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        onupdate=lambda: datetime.now(
            timezone.utc
        ),
    )

    # ========================================================
    # INDEXES
    # ========================================================

    __table_args__ = (
        Index(
            "ix_assets_region_type",
            "region_id",
            "asset_type",
        ),
        Index(
            "ix_assets_status_criticality",
            "status",
            "criticality",
        ),
        Index(
            "ix_assets_location",
            "latitude",
            "longitude",
        ),
        Index(
            "ix_assets_monitoring",
            "is_monitored",
            "is_active",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<Asset("
            f"id='{self.id}', "
            f"name='{self.name}', "
            f"type='{self.asset_type}', "
            f"status='{self.status}', "
            f"criticality='{self.criticality}'"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Asset",
    "AssetType",
    "AssetStatus",
    "AssetCriticality",
]