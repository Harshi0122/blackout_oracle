"""
Blackout Oracle - Synthetic Grid Data Adapter.

Generates synthetic electrical-grid telemetry for:

- Development
- Testing
- Demonstrations
- Risk-engine testing
- Simulation workflows
- API testing
- ML pipeline prototyping

The generated data is synthetic and must not be interpreted as
real measurements from an electrical grid.

This module does not connect to physical equipment and does not
issue control commands.
"""

from __future__ import annotations

import math
import random
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_FREQUENCY_HZ = 50.0
DEFAULT_VOLTAGE_KV = 110.0
DEFAULT_POWER_FACTOR = 0.95

MIN_FREQUENCY_HZ = 49.0
MAX_FREQUENCY_HZ = 51.0

MIN_POWER_FACTOR = 0.80
MAX_POWER_FACTOR = 1.00

DEFAULT_INTERVAL_SECONDS = 60

DEFAULT_SEED = 42


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def _clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """Clamp a numeric value to a specified range."""
    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Safely convert a value to float."""
    try:
        return float(
            value
        )
    except (
        TypeError,
        ValueError,
    ):
        return default


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """Safely convert a value to int."""
    try:
        return int(
            value
        )
    except (
        TypeError,
        ValueError,
    ):
        return default


# ============================================================
# DATA STRUCTURES
# ============================================================


@dataclass
class SyntheticGridRecord:
    """
    Represents one synthetic grid telemetry observation.
    """

    timestamp: datetime

    asset_id: str
    asset_type: str = "substation"
    region_id: str | None = None

    voltage_kv: float = DEFAULT_VOLTAGE_KV
    current_a: float = 0.0

    active_power_mw: float = 0.0
    reactive_power_mvar: float = 0.0

    frequency_hz: float = DEFAULT_FREQUENCY_HZ
    power_factor: float = DEFAULT_POWER_FACTOR

    loading_percent: float = 0.0

    temperature_c: float | None = None

    source: str = "synthetic_grid"

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Convert the record to a JSON-compatible dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "asset_id": self.asset_id,
            "asset_type": self.asset_type,
            "region_id": self.region_id,
            "voltage_kv": self.voltage_kv,
            "current_a": self.current_a,
            "active_power_mw": self.active_power_mw,
            "reactive_power_mvar": (
                self.reactive_power_mvar
            ),
            "frequency_hz": self.frequency_hz,
            "power_factor": self.power_factor,
            "loading_percent": (
                self.loading_percent
            ),
            "temperature_c": self.temperature_c,
            "source": self.source,
            "metadata": dict(
                self.metadata
            ),
        }


@dataclass
class SyntheticGenerationConfig:
    """
    Configuration for synthetic telemetry generation.
    """

    asset_id: str

    asset_type: str = "substation"

    region_id: str | None = None

    nominal_voltage_kv: float = DEFAULT_VOLTAGE_KV

    nominal_power_mw: float = 100.0

    nominal_frequency_hz: float = (
        DEFAULT_FREQUENCY_HZ
    )

    nominal_temperature_c: float = 30.0

    noise_level: float = 1.0

    seed: int | None = DEFAULT_SEED

    def __post_init__(self) -> None:
        """Normalize configuration values."""
        self.asset_id = str(
            self.asset_id
        )

        self.asset_type = str(
            self.asset_type
        )

        if self.region_id is not None:
            self.region_id = str(
                self.region_id
            )

        self.nominal_voltage_kv = max(
            0.0,
            _safe_float(
                self.nominal_voltage_kv,
                DEFAULT_VOLTAGE_KV,
            ),
        )

        self.nominal_power_mw = max(
            0.0,
            _safe_float(
                self.nominal_power_mw,
                100.0,
            ),
        )

        self.nominal_frequency_hz = max(
            0.0,
            _safe_float(
                self.nominal_frequency_hz,
                DEFAULT_FREQUENCY_HZ,
            ),
        )

        self.nominal_temperature_c = (
            _safe_float(
                self.nominal_temperature_c,
                30.0,
            )
        )

        self.noise_level = max(
            0.0,
            _safe_float(
                self.noise_level,
                1.0,
            ),
        )


@dataclass
class SyntheticLoadResult:
    """
    Result returned after generating synthetic telemetry.
    """

    records: list[SyntheticGridRecord] = field(
        default_factory=list
    )

    asset_id: str | None = None

    start_time: datetime | None = None
    end_time: datetime | None = None

    interval_seconds: int = DEFAULT_INTERVAL_SECONDS

    seed: int | None = None

    generated_at: datetime = field(
        default_factory=_utc_now
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Convert the generation result to a dictionary."""
        return {
            "asset_id": self.asset_id,
            "start_time": (
                self.start_time.isoformat()
                if self.start_time
                else None
            ),
            "end_time": (
                self.end_time.isoformat()
                if self.end_time
                else None
            ),
            "interval_seconds": (
                self.interval_seconds
            ),
            "seed": self.seed,
            "record_count": len(
                self.records
            ),
            "generated_at": (
                self.generated_at.isoformat()
            ),
        }


# ============================================================
# SYNTHETIC GRID ADAPTER
# ============================================================


class SyntheticGridAdapter:
    """
    Generates synthetic grid telemetry.

    The generator models smooth daily variation plus controlled
    random noise. It can also inject synthetic abnormal
    conditions for testing risk and incident detection.
    """

    def __init__(
        self,
        config: SyntheticGenerationConfig | None = None,
        seed: int | None = DEFAULT_SEED,
    ) -> None:
        """Initialize the synthetic grid adapter."""
        self.config = (
            config
            if config is not None
            else SyntheticGenerationConfig(
                asset_id="SYNTHETIC_SUB_001"
            )
        )

        if seed is None:
            seed = self.config.seed

        self.seed = seed

        self.random = random.Random(
            seed
        )

    # ========================================================
    # TIME
    # ========================================================

    def normalize_start_time(
        self,
        start_time: datetime | None,
    ) -> datetime:
        """Return a timezone-aware UTC start time."""
        if start_time is None:
            return _utc_now()

        if start_time.tzinfo is None:
            return start_time.replace(
                tzinfo=timezone.utc
            )

        return start_time.astimezone(
            timezone.utc
        )

    # ========================================================
    # NORMAL TELEMETRY
    # ========================================================

    def generate_record(
        self,
        timestamp: datetime,
        load_factor: float = 1.0,
    ) -> SyntheticGridRecord:
        """
        Generate one normal synthetic telemetry record.
        """
        load_factor = _clamp(
            _safe_float(
                load_factor,
                1.0,
            ),
            0.0,
            1.5,
        )

        noise = self.config.noise_level

        # Smooth load variation.
        load_wave = (
            0.10
            * math.sin(
                timestamp.hour
                / 24.0
                * 2.0
                * math.pi
            )
        )

        power_mw = (
            self.config.nominal_power_mw
            * load_factor
            * (
                1.0
                + load_wave
            )
        )

        power_mw += self.random.gauss(
            0.0,
            noise,
        )

        power_mw = max(
            0.0,
            power_mw,
        )

        # Voltage variation.
        voltage_variation = (
            self.random.gauss(
                0.0,
                0.25 * noise,
            )
        )

        voltage_kv = (
            self.config.nominal_voltage_kv
            + voltage_variation
        )

        voltage_kv = max(
            0.0,
            voltage_kv,
        )

        # Frequency remains close to nominal.
        frequency = (
            self.config.nominal_frequency_hz
            + self.random.gauss(
                0.0,
                0.01 * noise,
            )
        )

        # Power factor.
        power_factor = _clamp(
            DEFAULT_POWER_FACTOR
            + self.random.gauss(
                0.0,
                0.005 * noise,
            ),
            MIN_POWER_FACTOR,
            MAX_POWER_FACTOR,
        )

        # Approximate current using:
        #
        #     P = V * I * PF
        #
        # For the synthetic model, this is only an approximate
        # analytical relationship.
        current_a = 0.0

        if voltage_kv > 0.0:
            current_a = (
                power_mw
                * 1000.0
                / (
                    voltage_kv
                    * power_factor
                )
            )

        reactive_power = (
            power_mw
            * math.tan(
                math.acos(
                    _clamp(
                        power_factor,
                        0.01,
                        1.0,
                    )
                )
            )
        )

        loading_percent = _clamp(
            load_factor
            * 100.0,
            0.0,
            150.0,
        )

        temperature = (
            self.config.nominal_temperature_c
            + self.random.gauss(
                0.0,
                0.5 * noise,
            )
        )

        return SyntheticGridRecord(
            timestamp=timestamp,
            asset_id=self.config.asset_id,
            asset_type=self.config.asset_type,
            region_id=self.config.region_id,
            voltage_kv=voltage_kv,
            current_a=max(
                0.0,
                current_a,
            ),
            active_power_mw=power_mw,
            reactive_power_mvar=max(
                0.0,
                reactive_power,
            ),
            frequency_hz=frequency,
            power_factor=power_factor,
            loading_percent=loading_percent,
            temperature_c=temperature,
            source="synthetic_grid",
            metadata={
                "synthetic": True,
                "generation_mode": "normal",
            },
        )

    # ========================================================
    # GENERATE TIME SERIES
    # ========================================================

    def generate(
        self,
        count: int,
        start_time: datetime | None = None,
        interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
        load_factor: float = 1.0,
    ) -> SyntheticLoadResult:
        """
        Generate a synthetic telemetry time series.

        Args:
            count:
                Number of records to generate.

            start_time:
                Starting timestamp.

            interval_seconds:
                Time between records.

            load_factor:
                Base loading factor.
        """
        count = max(
            0,
            _safe_int(
                count
            ),
        )

        interval_seconds = max(
            1,
            _safe_int(
                interval_seconds,
                DEFAULT_INTERVAL_SECONDS,
            ),
        )

        start = self.normalize_start_time(
            start_time
        )

        records: list[SyntheticGridRecord] = []

        for index in range(
            count
        ):
            timestamp = (
                start
                + timedelta(
                    seconds=(
                        index
                        * interval_seconds
                    )
                )
            )

            record = self.generate_record(
                timestamp,
                load_factor=load_factor,
            )

            records.append(
                record
            )

        end_time = (
            records[-1].timestamp
            if records
            else None
        )

        return SyntheticLoadResult(
            records=records,
            asset_id=self.config.asset_id,
            start_time=(
                records[0].timestamp
                if records
                else None
            ),
            end_time=end_time,
            interval_seconds=interval_seconds,
            seed=self.seed,
        )

    # ========================================================
    # MULTI-ASSET GENERATION
    # ========================================================

    def generate_for_assets(
        self,
        configs: Sequence[SyntheticGenerationConfig],
        count: int,
        start_time: datetime | None = None,
        interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    ) -> list[SyntheticLoadResult]:
        """
        Generate synthetic telemetry for multiple assets.
        """
        results: list[SyntheticLoadResult] = []

        for config in configs:
            adapter = SyntheticGridAdapter(
                config=config,
                seed=self.seed,
            )

            results.append(
                adapter.generate(
                    count=count,
                    start_time=start_time,
                    interval_seconds=interval_seconds,
                )
            )

        return results

    # ========================================================
    # ABNORMAL CONDITIONS
    # ========================================================

    def generate_overload(
        self,
        count: int,
        start_time: datetime | None = None,
        interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
        loading_percent: float = 120.0,
    ) -> SyntheticLoadResult:
        """
        Generate synthetic overloaded-grid telemetry.
        """
        loading_percent = max(
            0.0,
            _safe_float(
                loading_percent,
                120.0,
            ),
        )

        load_factor = (
            loading_percent
            / 100.0
        )

        result = self.generate(
            count=count,
            start_time=start_time,
            interval_seconds=interval_seconds,
            load_factor=load_factor,
        )

        for record in result.records:
            record.loading_percent = (
                loading_percent
            )

            record.metadata[
                "generation_mode"
            ] = "overload"

            record.metadata[
                "synthetic_anomaly"
            ] = "overload"

        return result

    def generate_voltage_anomaly(
        self,
        count: int,
        start_time: datetime | None = None,
        interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
        voltage_multiplier: float = 0.85,
    ) -> SyntheticLoadResult:
        """
        Generate synthetic voltage-anomaly telemetry.
        """
        multiplier = max(
            0.1,
            _safe_float(
                voltage_multiplier,
                0.85,
            ),
        )

        result = self.generate(
            count=count,
            start_time=start_time,
            interval_seconds=interval_seconds,
        )

        for record in result.records:
            record.voltage_kv *= multiplier

            record.metadata[
                "generation_mode"
            ] = "voltage_anomaly"

            record.metadata[
                "synthetic_anomaly"
            ] = "voltage_anomaly"

        return result

    def generate_frequency_anomaly(
        self,
        count: int,
        start_time: datetime | None = None,
        interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
        frequency_hz: float = 49.2,
    ) -> SyntheticLoadResult:
        """
        Generate synthetic frequency-anomaly telemetry.
        """
        frequency = _safe_float(
            frequency_hz,
            49.2,
        )

        result = self.generate(
            count=count,
            start_time=start_time,
            interval_seconds=interval_seconds,
        )

        for record in result.records:
            record.frequency_hz = frequency

            record.metadata[
                "generation_mode"
            ] = "frequency_anomaly"

            record.metadata[
                "synthetic_anomaly"
            ] = "frequency_anomaly"

        return result

    def generate_thermal_stress(
        self,
        count: int,
        start_time: datetime | None = None,
        interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
        temperature_c: float = 60.0,
    ) -> SyntheticLoadResult:
        """
        Generate synthetic thermal-stress telemetry.
        """
        temperature = _safe_float(
            temperature_c,
            60.0,
        )

        result = self.generate(
            count=count,
            start_time=start_time,
            interval_seconds=interval_seconds,
        )

        for record in result.records:
            record.temperature_c = (
                temperature
            )

            record.metadata[
                "generation_mode"
            ] = "thermal_stress"

            record.metadata[
                "synthetic_anomaly"
            ] = "thermal_stress"

        return result

    # ========================================================
    # MIXED ANOMALY GENERATION
    # ========================================================

    def generate_scenario(
        self,
        count: int,
        scenario: str = "normal",
        start_time: datetime | None = None,
        interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    ) -> SyntheticLoadResult:
        """
        Generate telemetry for a named synthetic scenario.

        Supported scenarios:

            normal
            overload
            voltage_anomaly
            frequency_anomaly
            thermal_stress
        """
        normalized = str(
            scenario
        ).strip().lower()

        if normalized == "normal":
            return self.generate(
                count=count,
                start_time=start_time,
                interval_seconds=interval_seconds,
            )

        if normalized == "overload":
            return self.generate_overload(
                count=count,
                start_time=start_time,
                interval_seconds=interval_seconds,
            )

        if normalized == "voltage_anomaly":
            return self.generate_voltage_anomaly(
                count=count,
                start_time=start_time,
                interval_seconds=interval_seconds,
            )

        if normalized == "frequency_anomaly":
            return self.generate_frequency_anomaly(
                count=count,
                start_time=start_time,
                interval_seconds=interval_seconds,
            )

        if normalized == "thermal_stress":
            return self.generate_thermal_stress(
                count=count,
                start_time=start_time,
                interval_seconds=interval_seconds,
            )

        raise ValueError(
            "Unsupported synthetic scenario: "
            f"{scenario}"
        )

    # ========================================================
    # STATISTICS
    # ========================================================

    def statistics(
        self,
        records: Iterable[SyntheticGridRecord],
    ) -> dict[str, float | int | None]:
        """
        Calculate basic telemetry statistics.
        """
        values = list(
            records
        )

        if not values:
            return {
                "record_count": 0,
                "average_voltage_kv": None,
                "average_current_a": None,
                "average_active_power_mw": None,
                "average_frequency_hz": None,
                "average_loading_percent": None,
                "maximum_loading_percent": None,
            }

        voltage = [
            record.voltage_kv
            for record in values
        ]

        current = [
            record.current_a
            for record in values
        ]

        power = [
            record.active_power_mw
            for record in values
        ]

        frequency = [
            record.frequency_hz
            for record in values
        ]

        loading = [
            record.loading_percent
            for record in values
        ]

        return {
            "record_count": len(
                values
            ),
            "average_voltage_kv": (
                sum(voltage)
                / len(voltage)
            ),
            "average_current_a": (
                sum(current)
                / len(current)
            ),
            "average_active_power_mw": (
                sum(power)
                / len(power)
            ),
            "average_frequency_hz": (
                sum(frequency)
                / len(frequency)
            ),
            "average_loading_percent": (
                sum(loading)
                / len(loading)
            ),
            "maximum_loading_percent": max(
                loading
            ),
        }

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_record(
        self,
        record: SyntheticGridRecord,
    ) -> list[str]:
        """
        Validate one synthetic telemetry record.
        """
        errors: list[str] = []

        if not record.asset_id.strip():
            errors.append(
                "Asset ID cannot be empty."
            )

        if (
            record.timestamp.tzinfo
            is None
        ):
            errors.append(
                "Timestamp must be timezone-aware."
            )

        if record.voltage_kv < 0.0:
            errors.append(
                "Voltage cannot be negative."
            )

        if record.current_a < 0.0:
            errors.append(
                "Current cannot be negative."
            )

        if record.active_power_mw < 0.0:
            errors.append(
                "Active power cannot be negative."
            )

        if record.reactive_power_mvar < 0.0:
            errors.append(
                "Reactive power cannot be negative."
            )

        if not (
            0.0
            <= record.power_factor
            <= 1.0
        ):
            errors.append(
                "Power factor must be between 0 and 1."
            )

        if record.loading_percent < 0.0:
            errors.append(
                "Loading percentage cannot be negative."
            )

        return errors

    def validate_records(
        self,
        records: Iterable[SyntheticGridRecord],
    ) -> list[str]:
        """Validate multiple synthetic records."""
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
    # SERIALIZATION
    # ========================================================

    def records_to_dict(
        self,
        records: Iterable[SyntheticGridRecord],
    ) -> list[dict[str, Any]]:
        """Convert records into dictionaries."""
        return [
            record.to_dict()
            for record in records
        ]


# ============================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================


def generate_synthetic_grid(
    count: int,
    asset_id: str = "SYNTHETIC_SUB_001",
    asset_type: str = "substation",
    region_id: str | None = None,
    start_time: datetime | None = None,
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    seed: int | None = DEFAULT_SEED,
) -> SyntheticLoadResult:
    """
    Generate normal synthetic grid telemetry.
    """
    config = SyntheticGenerationConfig(
        asset_id=asset_id,
        asset_type=asset_type,
        region_id=region_id,
        seed=seed,
    )

    adapter = SyntheticGridAdapter(
        config=config,
        seed=seed,
    )

    return adapter.generate(
        count=count,
        start_time=start_time,
        interval_seconds=interval_seconds,
    )


def generate_synthetic_scenario(
    count: int,
    scenario: str = "normal",
    asset_id: str = "SYNTHETIC_SUB_001",
    asset_type: str = "substation",
    region_id: str | None = None,
    start_time: datetime | None = None,
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    seed: int | None = DEFAULT_SEED,
) -> SyntheticLoadResult:
    """
    Generate synthetic telemetry for a specified scenario.
    """
    config = SyntheticGenerationConfig(
        asset_id=asset_id,
        asset_type=asset_type,
        region_id=region_id,
        seed=seed,
    )

    adapter = SyntheticGridAdapter(
        config=config,
        seed=seed,
    )

    return adapter.generate_scenario(
        count=count,
        scenario=scenario,
        start_time=start_time,
        interval_seconds=interval_seconds,
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "SyntheticGridRecord",
    "SyntheticGenerationConfig",
    "SyntheticLoadResult",
    "SyntheticGridAdapter",
    "generate_synthetic_grid",
    "generate_synthetic_scenario",
]