"""
Blackout Oracle - Data Normalizer.

Provides common utilities for converting raw data from different
ingestion sources into consistent, application-friendly
dictionaries.

This module is intentionally independent of:
- Database models
- FastAPI
- SQLAlchemy
- Machine-learning libraries
- External APIs

That keeps the ingestion layer easy to test and prevents
circular-import problems.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any


# ============================================================
# CONSTANTS
# ============================================================

TIMESTAMP_ALIASES = (
    "timestamp",
    "datetime",
    "date_time",
    "time",
    "date",
    "recorded_at",
    "observed_at",
    "observation_time",
    "valid_time",
)

ASSET_ID_ALIASES = (
    "asset_id",
    "asset",
    "asset_name",
    "station",
    "station_id",
    "station_name",
    "substation",
    "substation_id",
    "substation_name",
    "plant",
    "plant_id",
    "plant_name",
)

REGION_ALIASES = (
    "region_id",
    "region",
    "region_name",
    "state",
    "state_name",
    "area",
    "zone",
)

DEMAND_ALIASES = (
    "demand",
    "load",
    "system_demand",
    "total_demand",
    "demand_mw",
    "load_mw",
)

GENERATION_ALIASES = (
    "generation",
    "total_generation",
    "generation_mw",
    "power_generation",
    "gen_mw",
)

VOLTAGE_ALIASES = (
    "voltage",
    "voltage_kv",
    "voltage_v",
    "bus_voltage",
)

CURRENT_ALIASES = (
    "current",
    "current_a",
    "current_amp",
    "amperage",
)

FREQUENCY_ALIASES = (
    "frequency",
    "frequency_hz",
    "grid_frequency",
    "grid_frequency_hz",
    "freq",
)

TEMPERATURE_ALIASES = (
    "temperature",
    "temperature_c",
    "temp",
    "temp_c",
)

POWER_FACTOR_ALIASES = (
    "power_factor",
    "pf",
)

REACTIVE_POWER_ALIASES = (
    "reactive_power",
    "reactive_power_mvar",
    "q_mvar",
)

ACTIVE_POWER_ALIASES = (
    "active_power",
    "active_power_mw",
    "real_power",
    "real_power_mw",
)

RENEWABLE_ALIASES = (
    "renewable",
    "renewable_generation",
    "renewable_generation_mw",
    "renewable_mw",
)

WIND_ALIASES = (
    "wind",
    "wind_generation",
    "wind_generation_mw",
    "wind_mw",
)

SOLAR_ALIASES = (
    "solar",
    "solar_generation",
    "solar_generation_mw",
    "solar_mw",
)

HYDRO_ALIASES = (
    "hydro",
    "hydro_generation",
    "hydro_generation_mw",
    "hydro_mw",
)

THERMAL_ALIASES = (
    "thermal",
    "thermal_generation",
    "thermal_generation_mw",
    "thermal_mw",
)

EXCHANGE_ALIASES = (
    "exchange",
    "power_exchange",
    "interchange",
    "net_exchange",
    "exchange_mw",
)

SHORTAGE_ALIASES = (
    "shortage",
    "deficit",
    "shortage_mw",
    "deficit_mw",
)

SURPLUS_ALIASES = (
    "surplus",
    "surplus_mw",
)

UNIT_ALIASES = (
    "unit",
    "units",
)

# Common containers returned by public APIs.
RECORD_CONTAINER_ALIASES = (
    "data",
    "records",
    "items",
    "results",
    "observations",
    "response",
)


# ============================================================
# BASIC HELPERS
# ============================================================


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(
        timezone.utc
    )


def normalize_key(
    key: Any,
) -> str:
    """
    Convert a raw field name into snake_case.

    Examples:
        "System Demand" -> "system_demand"
        "Voltage-kV" -> "voltage_kv"
        "Grid/Frequency" -> "grid_frequency"
    """
    value = str(
        key
    ).strip().lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "_",
        value,
    )

    value = re.sub(
        r"_+",
        "_",
        value,
    )

    return value.strip(
        "_"
    )


def normalize_mapping(
    data: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Normalize every key in a mapping.
    """
    return {
        normalize_key(key): value
        for key, value in data.items()
    }


def first_present(
    data: Mapping[str, Any],
    aliases: Iterable[str],
) -> Any:
    """
    Return the first non-empty value matching the supplied
    aliases.
    """
    for alias in aliases:
        normalized_alias = normalize_key(
            alias
        )

        if normalized_alias not in data:
            continue

        value = data[
            normalized_alias
        ]

        if value is None:
            continue

        if isinstance(
            value,
            str,
        ) and not value.strip():
            continue

        return value

    return None


# ============================================================
# VALUE CONVERSION
# ============================================================


def to_float(
    value: Any,
    default: float | None = None,
) -> float | None:
    """
    Convert a value into a float.

    Handles common values such as:

        123
        123.45
        "123.45"
        "1,234.50"
        "123.45 MW"
    """
    if value is None:
        return default

    if isinstance(
        value,
        bool,
    ):
        return default

    if isinstance(
        value,
        (int, float),
    ):
        return float(
            value
        )

    text = str(
        value
    ).strip()

    if not text:
        return default

    text = text.replace(
        ",",
        "",
    )

    try:
        return float(
            text
        )
    except ValueError:
        pass

    match = re.search(
        r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)",
        text,
    )

    if match is None:
        return default

    try:
        return float(
            match.group(
                0
            )
        )
    except ValueError:
        return default


def to_int(
    value: Any,
    default: int | None = None,
) -> int | None:
    """
    Convert a value into an integer.
    """
    if value is None:
        return default

    if isinstance(
        value,
        bool,
    ):
        return default

    try:
        return int(
            value
        )
    except (
        TypeError,
        ValueError,
    ):
        numeric = to_float(
            value
        )

        if numeric is None:
            return default

        return int(
            numeric
        )


def to_bool(
    value: Any,
    default: bool = False,
) -> bool:
    """
    Convert common boolean representations into bool.
    """
    if isinstance(
        value,
        bool,
    ):
        return value

    if value is None:
        return default

    if isinstance(
        value,
        (int, float),
    ):
        return bool(
            value
        )

    text = str(
        value
    ).strip().lower()

    if text in {
        "true",
        "1",
        "yes",
        "y",
        "on",
        "active",
        "enabled",
    }:
        return True

    if text in {
        "false",
        "0",
        "no",
        "n",
        "off",
        "inactive",
        "disabled",
    }:
        return False

    return default


def clean_string(
    value: Any,
    default: str | None = None,
) -> str | None:
    """
    Convert a value into a cleaned string.
    """
    if value is None:
        return default

    text = str(
        value
    ).strip()

    if not text:
        return default

    return text


# ============================================================
# TIMESTAMP NORMALIZATION
# ============================================================


def parse_timestamp(
    value: Any,
    default: datetime | None = None,
) -> datetime | None:
    """
    Convert a timestamp into a timezone-aware UTC datetime.

    Supports:
    - datetime objects
    - ISO-8601 strings
    - timestamps ending in Z
    - Unix timestamps in seconds
    - Unix timestamps in milliseconds
    """
    if value is None:
        return default

    if isinstance(
        value,
        datetime,
    ):
        result = value

    elif isinstance(
        value,
        (int, float),
    ):
        numeric = float(
            value
        )

        # Detect millisecond Unix timestamps.
        if abs(numeric) > 10_000_000_000:
            numeric /= 1000.0

        try:
            result = datetime.fromtimestamp(
                numeric,
                tz=timezone.utc,
            )
        except (
            OverflowError,
            OSError,
            ValueError,
        ):
            return default

    else:
        text = str(
            value
        ).strip()

        if not text:
            return default

        if text.endswith(
            "Z"
        ):
            text = (
                text[:-1]
                + "+00:00"
            )

        try:
            result = datetime.fromisoformat(
                text
            )
        except ValueError:
            # Support a few common public-data formats.
            formats = (
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%d-%m-%Y %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
                "%Y-%m-%d",
                "%d-%m-%Y",
                "%d/%m/%Y",
            )

            result = None

            for fmt in formats:
                try:
                    result = datetime.strptime(
                        text,
                        fmt,
                    )
                    break
                except ValueError:
                    continue

            if result is None:
                return default

    if result.tzinfo is None:
        result = result.replace(
            tzinfo=timezone.utc
        )

    return result.astimezone(
        timezone.utc
    )


# ============================================================
# RECORD EXTRACTION
# ============================================================


def extract_records(
    payload: Any,
) -> list[dict[str, Any]]:
    """
    Extract record dictionaries from common API response
    structures.

    Examples supported:

        [{"a": 1}, {"a": 2}]

        {"data": [{"a": 1}]}

        {"records": [{"a": 1}]}

        {"response": {"items": [{"a": 1}]}}
    """
    if isinstance(
        payload,
        list,
    ):
        return [
            dict(item)
            for item in payload
            if isinstance(
                item,
                Mapping,
            )
        ]

    if not isinstance(
        payload,
        Mapping,
    ):
        return []

    normalized = normalize_mapping(
        payload
    )

    for container_name in RECORD_CONTAINER_ALIASES:
        container = normalized.get(
            container_name
        )

        if isinstance(
            container,
            list,
        ):
            return [
                dict(item)
                for item in container
                if isinstance(
                    item,
                    Mapping,
                )
            ]

        if isinstance(
            container,
            Mapping,
        ):
            nested = extract_records(
                container
            )

            if nested:
                return nested

    return [
        dict(payload)
    ]


# ============================================================
# GENERIC RECORD NORMALIZER
# ============================================================


def normalize_record(
    raw_record: Mapping[str, Any],
    *,
    source: str = "unknown",
) -> dict[str, Any]:
    """
    Normalize one raw grid/weather/telemetry record.

    Unknown fields are preserved inside ``metadata`` so source-
    specific information is not silently discarded.
    """
    if not isinstance(
        raw_record,
        Mapping,
    ):
        raise TypeError(
            "Raw record must be a mapping."
        )

    data = normalize_mapping(
        raw_record
    )

    timestamp_value = first_present(
        data,
        TIMESTAMP_ALIASES,
    )

    timestamp = parse_timestamp(
        timestamp_value
    )

    if timestamp is None:
        raise ValueError(
            "Record does not contain a valid timestamp."
        )

    asset_id = clean_string(
        first_present(
            data,
            ASSET_ID_ALIASES,
        )
    )

    region_id = clean_string(
        first_present(
            data,
            REGION_ALIASES,
        )
    )

    demand_mw = to_float(
        first_present(
            data,
            DEMAND_ALIASES,
        )
    )

    generation_mw = to_float(
        first_present(
            data,
            GENERATION_ALIASES,
        )
    )

    voltage = to_float(
        first_present(
            data,
            VOLTAGE_ALIASES,
        )
    )

    current = to_float(
        first_present(
            data,
            CURRENT_ALIASES,
        )
    )

    frequency = to_float(
        first_present(
            data,
            FREQUENCY_ALIASES,
        )
    )

    temperature = to_float(
        first_present(
            data,
            TEMPERATURE_ALIASES,
        )
    )

    power_factor = to_float(
        first_present(
            data,
            POWER_FACTOR_ALIASES,
        )
    )

    active_power = to_float(
        first_present(
            data,
            ACTIVE_POWER_ALIASES,
        )
    )

    reactive_power = to_float(
        first_present(
            data,
            REACTIVE_POWER_ALIASES,
        )
    )

    renewable_generation = to_float(
        first_present(
            data,
            RENEWABLE_ALIASES,
        )
    )

    wind_generation = to_float(
        first_present(
            data,
            WIND_ALIASES,
        )
    )

    solar_generation = to_float(
        first_present(
            data,
            SOLAR_ALIASES,
        )
    )

    hydro_generation = to_float(
        first_present(
            data,
            HYDRO_ALIASES,
        )
    )

    thermal_generation = to_float(
        first_present(
            data,
            THERMAL_ALIASES,
        )
    )

    exchange_mw = to_float(
        first_present(
            data,
            EXCHANGE_ALIASES,
        )
    )

    shortage_mw = to_float(
        first_present(
            data,
            SHORTAGE_ALIASES,
        )
    )

    surplus_mw = to_float(
        first_present(
            data,
            SURPLUS_ALIASES,
        )
    )

    unit = clean_string(
        first_present(
            data,
            UNIT_ALIASES,
        )
    )

    known_fields: set[str] = set()

    alias_groups = (
        TIMESTAMP_ALIASES,
        ASSET_ID_ALIASES,
        REGION_ALIASES,
        DEMAND_ALIASES,
        GENERATION_ALIASES,
        VOLTAGE_ALIASES,
        CURRENT_ALIASES,
        FREQUENCY_ALIASES,
        TEMPERATURE_ALIASES,
        POWER_FACTOR_ALIASES,
        ACTIVE_POWER_ALIASES,
        REACTIVE_POWER_ALIASES,
        RENEWABLE_ALIASES,
        WIND_ALIASES,
        SOLAR_ALIASES,
        HYDRO_ALIASES,
        THERMAL_ALIASES,
        EXCHANGE_ALIASES,
        SHORTAGE_ALIASES,
        SURPLUS_ALIASES,
        UNIT_ALIASES,
    )

    for aliases in alias_groups:
        for alias in aliases:
            known_fields.add(
                normalize_key(
                    alias
                )
            )

    metadata = {
        key: value
        for key, value in data.items()
        if key not in known_fields
    }

    return {
        "timestamp": timestamp.isoformat(),
        "asset_id": asset_id,
        "region_id": region_id,
        "demand_mw": demand_mw,
        "generation_mw": generation_mw,
        "voltage": voltage,
        "current": current,
        "frequency_hz": frequency,
        "temperature_c": temperature,
        "power_factor": power_factor,
        "active_power_mw": active_power,
        "reactive_power_mvar": reactive_power,
        "renewable_generation_mw": (
            renewable_generation
        ),
        "wind_generation_mw": (
            wind_generation
        ),
        "solar_generation_mw": (
            solar_generation
        ),
        "hydro_generation_mw": (
            hydro_generation
        ),
        "thermal_generation_mw": (
            thermal_generation
        ),
        "exchange_mw": exchange_mw,
        "shortage_mw": shortage_mw,
        "surplus_mw": surplus_mw,
        "unit": unit,
        "source": source,
        "metadata": metadata,
    }


# ============================================================
# NORMALIZATION CLASS
# ============================================================


class DataNormalizer:
    """
    Central normalizer used by the ingestion layer.

    This class provides a consistent interface for normalizing
    individual records and complete datasets.
    """

    def __init__(
        self,
        source: str = "unknown",
    ) -> None:
        """Initialize the normalizer."""
        self.source = str(
            source
        )

    def normalize(
        self,
        raw_record: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Normalize one record.
        """
        return normalize_record(
            raw_record,
            source=self.source,
        )

    def normalize_many(
        self,
        raw_records: Iterable[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Normalize multiple records.

        Invalid records raise an exception rather than being
        silently discarded.
        """
        normalized: list[dict[str, Any]] = []

        for record in raw_records:
            normalized.append(
                self.normalize(
                    record
                )
            )

        return normalized

    def normalize_payload(
        self,
        payload: Any,
    ) -> list[dict[str, Any]]:
        """
        Extract and normalize records from a complete API
        payload.
        """
        records = extract_records(
            payload
        )

        return self.normalize_many(
            records
        )

    def try_normalize_many(
        self,
        raw_records: Iterable[Mapping[str, Any]],
    ) -> tuple[
        list[dict[str, Any]],
        list[str],
    ]:
        """
        Normalize multiple records while collecting errors.

        Returns:

            (
                successful_records,
                error_messages,
            )
        """
        normalized: list[dict[str, Any]] = []
        errors: list[str] = []

        for index, record in enumerate(
            raw_records,
            start=1,
        ):
            try:
                normalized.append(
                    self.normalize(
                        record
                    )
                )

            except (
                TypeError,
                ValueError,
            ) as exc:
                errors.append(
                    f"Record {index}: {exc}"
                )

        return (
            normalized,
            errors,
        )


# ============================================================
# VALIDATION
# ============================================================


def validate_normalized_record(
    record: Mapping[str, Any],
) -> list[str]:
    """
    Validate a normalized record.

    The rules are intentionally conservative because different
    sources can legitimately omit certain measurements.
    """
    errors: list[str] = []

    timestamp = record.get(
        "timestamp"
    )

    if not timestamp:
        errors.append(
            "Missing timestamp."
        )

    numeric_fields = (
        "demand_mw",
        "generation_mw",
        "active_power_mw",
        "reactive_power_mvar",
        "renewable_generation_mw",
        "wind_generation_mw",
        "solar_generation_mw",
        "hydro_generation_mw",
        "thermal_generation_mw",
    )

    for field_name in numeric_fields:
        value = record.get(
            field_name
        )

        if value is not None:
            numeric = to_float(
                value
            )

            if numeric is None:
                errors.append(
                    f"{field_name} must be numeric."
                )

            elif numeric < 0.0:
                errors.append(
                    f"{field_name} cannot be negative."
                )

    frequency = to_float(
        record.get(
            "frequency_hz"
        )
    )

    if frequency is not None and not (
        40.0
        <= frequency
        <= 70.0
    ):
        errors.append(
            "frequency_hz is outside the "
            "40-70 Hz validation range."
        )

    power_factor = to_float(
        record.get(
            "power_factor"
        )
    )

    if power_factor is not None and not (
        0.0
        <= power_factor
        <= 1.0
    ):
        errors.append(
            "power_factor must be between 0 and 1."
        )

    return errors


def validate_records(
    records: Iterable[Mapping[str, Any]],
) -> list[str]:
    """
    Validate multiple normalized records.
    """
    errors: list[str] = []

    for index, record in enumerate(
        records,
        start=1,
    ):
        record_errors = (
            validate_normalized_record(
                record
            )
        )

        for error in record_errors:
            errors.append(
                f"Record {index}: {error}"
            )

    return errors


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "TIMESTAMP_ALIASES",
    "ASSET_ID_ALIASES",
    "REGION_ALIASES",
    "DEMAND_ALIASES",
    "GENERATION_ALIASES",
    "VOLTAGE_ALIASES",
    "CURRENT_ALIASES",
    "FREQUENCY_ALIASES",
    "TEMPERATURE_ALIASES",
    "POWER_FACTOR_ALIASES",
    "REACTIVE_POWER_ALIASES",
    "ACTIVE_POWER_ALIASES",
    "RENEWABLE_ALIASES",
    "WIND_ALIASES",
    "SOLAR_ALIASES",
    "HYDRO_ALIASES",
    "THERMAL_ALIASES",
    "EXCHANGE_ALIASES",
    "SHORTAGE_ALIASES",
    "SURPLUS_ALIASES",
    "UNIT_ALIASES",
    "utc_now",
    "normalize_key",
    "normalize_mapping",
    "first_present",
    "to_float",
    "to_int",
    "to_bool",
    "clean_string",
    "parse_timestamp",
    "extract_records",
    "normalize_record",
    "DataNormalizer",
    "validate_normalized_record",
    "validate_records",
]