"""
Blackout Oracle - Telemetry Database Model.

Stores raw and normalized electrical-grid telemetry observations.

Telemetry may originate from:

- Substations
- Feeders
- Buses
- Generators
- Loads
- Transformers
- Other monitored grid assets

Telemetry can contain:

- Voltage
- Current
- Frequency
- Active power
- Reactive power
- Apparent power
- Power factor
- Loading
- Energy
- Temperature
- Equipment measurements

The telemetry layer is the primary time-series input for:

- Anomaly detection
- Risk scoring
- Prediction
- Grid-state estimation
- Historical analysis
- Simulation input generation
- AI investigation

IMPORTANT
---------

This model stores measurements.

It does NOT directly control physical electrical-grid equipment.
"""


from __future__ import annotations

from datetime import datetime, timezone
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


class TelemetryType:
    """
    Category of telemetry measurement.
    """

    VOLTAGE = "voltage"
    CURRENT = "current"
    FREQUENCY = "frequency"

    ACTIVE_POWER = "active_power"
    REACTIVE_POWER = "reactive_power"
    APPARENT_POWER = "apparent_power"

    POWER_FACTOR = "power_factor"
    LOADING = "loading"

    ENERGY = "energy"
    TEMPERATURE = "temperature"

    STATUS = "status"
    ALARM = "alarm"

    COMBINED = "combined"
    OTHER = "other"


class TelemetrySource:
    """
    Source of telemetry data.
    """

    SCADA = "scada"
    PMU = "pmu"
    RTU = "rtu"
    SMART_METER = "smart_meter"

    UTILITY_API = "utility_api"
    EXTERNAL_API = "external_api"

    IOT = "iot"
    SENSOR = "sensor"

    SIMULATION = "simulation"
    MANUAL = "manual"

    TEST = "test"
    UNKNOWN = "unknown"


class TelemetryQuality:
    """
    Quality classification of a telemetry observation.
    """

    GOOD = "good"
    WARNING = "warning"
    BAD = "bad"
    STALE = "stale"
    MISSING = "missing"
    ESTIMATED = "estimated"
    SIMULATED = "simulated"
    UNKNOWN = "unknown"


class AssetType:
    """
    Type of grid asset producing the telemetry.
    """

    SUBSTATION = "substation"
    FEEDER = "feeder"
    BUS = "bus"
    GENERATOR = "generator"
    LOAD = "load"
    TRANSFORMER = "transformer"
    TRANSMISSION_LINE = "transmission_line"
    DISTRIBUTION_LINE = "distribution_line"
    OTHER = "other"


# ============================================================
# TELEMETRY MODEL
# ============================================================


class Telemetry(Base):
    """
    SQLAlchemy model representing one telemetry observation.

    Each record represents a measurement received at a particular
    point in time from a particular grid asset.
    """

    __tablename__ = "telemetry"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"TEL-{uuid4().hex[:12].upper()}"
        ),
    )

    # ========================================================
    # SOURCE INFORMATION
    # ========================================================

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=TelemetrySource.UNKNOWN,
        index=True,
    )

    source_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    source_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        index=True,
    )

    # ========================================================
    # MEASUREMENT INFORMATION
    # ========================================================

    telemetry_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default=TelemetryType.COMBINED,
        index=True,
    )

    measurement_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # ========================================================
    # GRID ASSET
    # ========================================================

    asset_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default=AssetType.OTHER,
        index=True,
    )

    asset_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    asset_name: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    external_asset_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    # ========================================================
    # GRID LOCATION
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

    substation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    feeder_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    bus_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    generator_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    load_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # ========================================================
    # GEOGRAPHICAL LOCATION
    # ========================================================

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # ELECTRICAL MEASUREMENTS
    # ========================================================

    voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    current_a: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    frequency_hz: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    active_power_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    reactive_power_mvar: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    apparent_power_mva: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    power_factor: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    loading_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    energy_mwh: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # ENVIRONMENTAL / EQUIPMENT MEASUREMENTS
    # ========================================================

    temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    equipment_temperature_c: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    oil_temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # STATUS / ALARM
    # ========================================================

    status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    alarm_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    alarm_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    alarm_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # QUALITY INFORMATION
    # ========================================================

    quality: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=TelemetryQuality.UNKNOWN,
        index=True,
    )

    quality_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    is_estimated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_simulated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # ========================================================
    # ANOMALY INFORMATION
    # ========================================================

    anomaly_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    anomaly_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    anomaly_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    anomaly_explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # DATA PROCESSING
    # ========================================================

    normalized: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    processed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    processing_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ========================================================
    # CORRELATION
    # ========================================================

    request_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    correlation_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    # ========================================================
    # ADDITIONAL DATA
    # ========================================================

    raw_payload_json: Mapped[str | None] = mapped_column(
        Text,
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
    # DATABASE INDEXES
    # ========================================================

    __table_args__ = (
        Index(
            "ix_telemetry_asset_timestamp",
            "asset_id",
            "source_timestamp",
        ),
        Index(
            "ix_telemetry_region_timestamp",
            "region_id",
            "source_timestamp",
        ),
        Index(
            "ix_telemetry_substation_timestamp",
            "substation_id",
            "source_timestamp",
        ),
        Index(
            "ix_telemetry_feeder_timestamp",
            "feeder_id",
            "source_timestamp",
        ),
        Index(
            "ix_telemetry_type_timestamp",
            "telemetry_type",
            "source_timestamp",
        ),
        Index(
            "ix_telemetry_quality_valid",
            "quality",
            "is_valid",
        ),
        Index(
            "ix_telemetry_anomaly",
            "anomaly_detected",
            "anomaly_score",
        ),
        Index(
            "ix_telemetry_received",
            "received_at",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<Telemetry("
            f"id='{self.id}', "
            f"asset='{self.asset_id}', "
            f"type='{self.telemetry_type}', "
            f"timestamp='{self.source_timestamp}'"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Telemetry",
    "TelemetryType",
    "TelemetrySource",
    "TelemetryQuality",
    "AssetType",
]