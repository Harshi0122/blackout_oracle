"""
Blackout Oracle - TANGEDCO Public Data Adapter.

Provides utilities for consuming publicly available Tamil Nadu
Generation and Distribution Corporation Limited (TANGEDCO) /
Tamil Nadu electricity-system data and converting it into a
normalized internal representation.

The adapter is designed for public data sources such as:

- System demand
- Power generation
- Renewable generation
- Thermal generation
- Hydro generation
- Solar generation
- Wind generation
- Grid frequency
- Power availability
- Power shortage / deficit
- Power exchange

Different public portals can expose different field names and
response formats. Therefore, this adapter accepts multiple
common aliases and normalizes them into a single structure.

Supported input:

- Python dictionaries
- JSON objects
- JSON arrays
- JSON responses containing data/records/items/results
- CSV text
- CSV files
- Public HTTP/HTTPS JSON endpoints
- Public HTTP/HTTPS CSV endpoints

This adapter only reads and normalizes public information.
It does not send commands to electrical equipment and does not
control the power grid.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_SOURCE = "tangedco_public"

DEFAULT_TIMEOUT_SECONDS = 15

SUPPORTED_EXTENSIONS = {
    ".csv",
    ".json",
}

TIMESTAMP_FIELDS = (
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

REGION_FIELDS = (
    "region_id",
    "region",
    "region_name",
    "state",
    "state_name",
    "area",
    "zone",
)

ASSET_FIELDS = (
    "asset_id",
    "asset",
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

DEMAND_FIELDS = (
    "demand",
    "load",
    "system_demand",
    "total_demand",
    "demand_mw",
    "load_mw",
    "peak_demand",
    "peak_demand_mw",
)

GENERATION_FIELDS = (
    "generation",
    "total_generation",
    "generation_mw",
    "power_generation",
    "gen_mw",
    "total_generation_mw",
)

AVAILABLE_POWER_FIELDS = (
    "availability",
    "available_power",
    "power_availability",
    "available_capacity",
    "availability_mw",
    "available_power_mw",
)

FREQUENCY_FIELDS = (
    "frequency",
    "grid_frequency",
    "freq",
    "frequency_hz",
    "grid_frequency_hz",
)

RENEWABLE_FIELDS = (
    "renewable_generation",
    "renewable",
    "renewable_mw",
    "renewable_generation_mw",
    "re_generation",
)

THERMAL_FIELDS = (
    "thermal_generation",
    "thermal",
    "thermal_mw",
    "thermal_generation_mw",
)

HYDRO_FIELDS = (
    "hydro_generation",
    "hydro",
    "hydro_mw",
    "hydro_generation_mw",
)

SOLAR_FIELDS = (
    "solar_generation",
    "solar",
    "solar_mw",
    "solar_generation_mw",
)

WIND_FIELDS = (
    "wind_generation",
    "wind",
    "wind_mw",
    "wind_generation_mw",
)

EXCHANGE_FIELDS = (
    "exchange",
    "power_exchange",
    "interchange",
    "net_exchange",
    "exchange_mw",
    "interstate_exchange",
)

SHORTAGE_FIELDS = (
    "shortage",
    "deficit",
    "shortage_mw",
    "deficit_mw",
    "power_shortage",
    "power_deficit",
)

SURPLUS_FIELDS = (
    "surplus",
    "surplus_mw",
    "power_surplus",
)

POWER_FACTOR_FIELDS = (
    "power_factor",
    "pf",
)

UNIT_FIELDS = (
    "unit",
    "units",
)

RECORD_CONTAINER_FIELDS = (
    "data",
    "records",
    "items",
    "results",
    "observations",
    "response",
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def _normalize_key(
    key: Any,
) -> str:
    """
    Normalize an incoming field name.

    Examples:

        "System Demand" -> "system_demand"
        "Demand-MW" -> "demand_mw"
        "Power Availability" -> "power_availability"
    """
    value = str(
        key
    ).strip().lower()

    value = value.replace(
        "-",
        "_",
    )

    value = value.replace(
        " ",
        "_",
    )

    value = value.replace(
        "/",
        "_",
    )

    return value


def _normalize_mapping(
    data: Mapping[str, Any],
) -> dict[str, Any]:
    """Normalize all keys in a mapping."""
    return {
        _normalize_key(key): value
        for key, value in data.items()
    }


def _first_present(
    data: Mapping[str, Any],
    fields: Iterable[str],
) -> Any:
    """
    Return the first non-empty value found in the mapping.
    """
    for field_name in fields:
        if field_name not in data:
            continue

        value = data[field_name]

        if value is None:
            continue

        if isinstance(
            value,
            str,
        ) and not value.strip():
            continue

        return value

    return None


def _safe_float(
    value: Any,
) -> float | None:
    """
    Safely convert a value to float.

    Handles values such as:

        123.4
        "123.4"
        "1,234.5"
        "123.4 MW"
    """
    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return None

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
        return None

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

    numeric = ""
    decimal_seen = False

    for character in text:
        if character.isdigit():
            numeric += character
            continue

        if character == "." and not decimal_seen:
            numeric += character
            decimal_seen = True
            continue

        if (
            character in {
                "+",
                "-",
            }
            and not numeric
        ):
            numeric += character
            continue

        break

    try:
        return float(
            numeric
        )
    except ValueError:
        return None


def _parse_timestamp(
    value: Any,
) -> datetime | None:
    """
    Parse a timestamp into a timezone-aware UTC datetime.

    Supports:

    - datetime objects
    - ISO-8601 strings
    - strings ending in Z
    """
    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc
            )

        return value.astimezone(
            timezone.utc
        )

    text = str(
        value
    ).strip()

    if not text:
        return None

    if text.endswith(
        "Z"
    ):
        text = (
            text[:-1]
            + "+00:00"
        )

    try:
        parsed = datetime.fromisoformat(
            text
        )
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )

    return parsed.astimezone(
        timezone.utc
    )


def _extract_records(
    payload: Any,
) -> list[dict[str, Any]]:
    """
    Extract record dictionaries from common public API
    response structures.
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

    normalized = _normalize_mapping(
        payload
    )

    for container_name in RECORD_CONTAINER_FIELDS:
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
            nested = _extract_records(
                container
            )

            if nested:
                return nested

    return [
        dict(payload)
    ]


# ============================================================
# DATA STRUCTURES
# ============================================================


@dataclass
class TANGEDCORecord:
    """
    Normalized public TANGEDCO electricity-system observation.

    Measurements are optional because different public sources
    may publish different subsets of information.
    """

    timestamp: datetime

    region_id: str | None = None
    asset_id: str | None = None

    demand_mw: float | None = None
    generation_mw: float | None = None
    available_power_mw: float | None = None

    frequency_hz: float | None = None

    renewable_generation_mw: float | None = None
    thermal_generation_mw: float | None = None
    hydro_generation_mw: float | None = None
    solar_generation_mw: float | None = None
    wind_generation_mw: float | None = None

    exchange_mw: float | None = None

    shortage_mw: float | None = None
    surplus_mw: float | None = None

    power_factor: float | None = None

    unit: str | None = None

    source: str = DEFAULT_SOURCE

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Convert the record into a JSON-compatible dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "region_id": self.region_id,
            "asset_id": self.asset_id,
            "demand_mw": self.demand_mw,
            "generation_mw": self.generation_mw,
            "available_power_mw": (
                self.available_power_mw
            ),
            "frequency_hz": self.frequency_hz,
            "renewable_generation_mw": (
                self.renewable_generation_mw
            ),
            "thermal_generation_mw": (
                self.thermal_generation_mw
            ),
            "hydro_generation_mw": (
                self.hydro_generation_mw
            ),
            "solar_generation_mw": (
                self.solar_generation_mw
            ),
            "wind_generation_mw": (
                self.wind_generation_mw
            ),
            "exchange_mw": self.exchange_mw,
            "shortage_mw": self.shortage_mw,
            "surplus_mw": self.surplus_mw,
            "power_factor": self.power_factor,
            "unit": self.unit,
            "source": self.source,
            "metadata": dict(
                self.metadata
            ),
        }


@dataclass
class TANGEDCOLoadResult:
    """
    Result returned by a TANGEDCO data-loading operation.
    """

    records: list[TANGEDCORecord] = field(
        default_factory=list
    )

    source: str = DEFAULT_SOURCE

    total_records: int = 0
    valid_records: int = 0
    skipped_records: int = 0

    errors: list[str] = field(
        default_factory=list
    )

    loaded_at: datetime = field(
        default_factory=_utc_now
    )

    @property
    def success(self) -> bool:
        """Return True when records loaded without errors."""
        return (
            self.valid_records > 0
            and not self.errors
        )

    @property
    def has_records(self) -> bool:
        """Return True when records are available."""
        return bool(
            self.records
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Convert the load result into a dictionary."""
        return {
            "source": self.source,
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "skipped_records": self.skipped_records,
            "record_count": len(
                self.records
            ),
            "success": self.success,
            "has_records": self.has_records,
            "errors": list(
                self.errors
            ),
            "loaded_at": self.loaded_at.isoformat(),
        }


# ============================================================
# TANGEDCO PUBLIC ADAPTER
# ============================================================


class TANGEDCOPublicAdapter:
    """
    Adapter for publicly available TANGEDCO electricity data.

    The adapter is portal-agnostic and supports several common
    field aliases because public electricity data sources may
    change their exact column names.
    """

    def __init__(
        self,
        source_name: str = DEFAULT_SOURCE,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize the adapter."""
        self.source_name = source_name

        self.timeout = max(
            1,
            int(timeout),
        )

    # ========================================================
    # HTTP
    # ========================================================

    def fetch(
        self,
        url: str,
        headers: Mapping[str, str] | None = None,
    ) -> str:
        """
        Fetch text from a public HTTP/HTTPS endpoint.

        The endpoint must be publicly accessible and the caller
        must be authorized to access it.
        """
        request_headers = {
            "Accept": (
                "application/json,text/csv,"
                "text/plain;q=0.9,*/*;q=0.8"
            ),
            "User-Agent": (
                "Blackout-Oracle/1.0"
            ),
        }

        if headers is not None:
            request_headers.update(
                {
                    str(key): str(value)
                    for key, value in headers.items()
                }
            )

        request = Request(
            url,
            headers=request_headers,
            method="GET",
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                raw_data = response.read()

        except HTTPError as exc:
            raise RuntimeError(
                "TANGEDCO endpoint returned "
                f"HTTP {exc.code}: {exc.reason}"
            ) from exc

        except URLError as exc:
            raise RuntimeError(
                "Unable to reach TANGEDCO endpoint: "
                f"{exc.reason}"
            ) from exc

        except TimeoutError as exc:
            raise RuntimeError(
                "TANGEDCO request timed out."
            ) from exc

        try:
            return raw_data.decode(
                "utf-8-sig"
            )
        except UnicodeDecodeError as exc:
            raise RuntimeError(
                "TANGEDCO endpoint returned unsupported "
                "text encoding."
            ) from exc

    def fetch_json(
        self,
        url: str,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """Fetch and decode JSON from a public endpoint."""
        text = self.fetch(
            url,
            headers=headers,
        )

        try:
            return json.loads(
                text
            )
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "TANGEDCO endpoint did not return valid JSON."
            ) from exc

    # ========================================================
    # JSON NORMALIZATION
    # ========================================================

    def normalize_json(
        self,
        payload: Any,
    ) -> TANGEDCOLoadResult:
        """Normalize a JSON-compatible TANGEDCO payload."""
        result = TANGEDCOLoadResult(
            source=self.source_name
        )

        raw_records = _extract_records(
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
                record = self.normalize_record(
                    raw_record
                )

                result.records.append(
                    record
                )

                result.valid_records += 1

            except (
                TypeError,
                ValueError,
            ) as exc:
                result.skipped_records += 1

                result.errors.append(
                    f"Record {index}: {exc}"
                )

        return result

    # ========================================================
    # CSV NORMALIZATION
    # ========================================================

    def normalize_csv(
        self,
        csv_text: str,
    ) -> TANGEDCOLoadResult:
        """Normalize CSV text containing TANGEDCO observations."""
        result = TANGEDCOLoadResult(
            source=self.source_name
        )

        reader = csv.DictReader(
            io.StringIO(
                csv_text
            )
        )

        if reader.fieldnames is None:
            result.errors.append(
                "CSV data does not contain a header row."
            )

            return result

        for index, row in enumerate(
            reader,
            start=1,
        ):
            result.total_records += 1

            try:
                record = self.normalize_record(
                    row
                )

                result.records.append(
                    record
                )

                result.valid_records += 1

            except (
                TypeError,
                ValueError,
            ) as exc:
                result.skipped_records += 1

                result.errors.append(
                    f"Record {index}: {exc}"
                )

        return result

    # ========================================================
    # FILE LOADING
    # ========================================================

    def load_file(
        self,
        file_path: str | Path,
    ) -> TANGEDCOLoadResult:
        """Load and normalize a local CSV or JSON file."""
        path = Path(
            file_path
        )

        result = TANGEDCOLoadResult(
            source=self.source_name
        )

        if not path.exists():
            result.errors.append(
                f"File does not exist: {path}"
            )

            return result

        if not path.is_file():
            result.errors.append(
                f"Path is not a file: {path}"
            )

            return result

        extension = (
            path.suffix.lower()
        )

        if extension not in SUPPORTED_EXTENSIONS:
            result.errors.append(
                "Unsupported file format: "
                f"{extension}. "
                "Supported formats are CSV and JSON."
            )

            return result

        try:
            text = path.read_text(
                encoding="utf-8-sig"
            )
        except (
            OSError,
            UnicodeError,
        ) as exc:
            result.errors.append(
                f"Unable to read {path}: {exc}"
            )

            return result

        if extension == ".csv":
            return self.normalize_csv(
                text
            )

        try:
            payload = json.loads(
                text
            )
        except json.JSONDecodeError as exc:
            result.errors.append(
                f"Invalid JSON in {path}: {exc}"
            )

            return result

        return self.normalize_json(
            payload
        )

    # ========================================================
    # RECORD NORMALIZATION
    # ========================================================

    def normalize_record(
        self,
        raw_record: Mapping[str, Any],
    ) -> TANGEDCORecord:
        """
        Normalize one TANGEDCO public-data observation.
        """
        if not isinstance(
            raw_record,
            Mapping,
        ):
            raise TypeError(
                "TANGEDCO record must be a mapping."
            )

        record = _normalize_mapping(
            raw_record
        )

        timestamp_value = _first_present(
            record,
            TIMESTAMP_FIELDS,
        )

        timestamp = _parse_timestamp(
            timestamp_value
        )

        if timestamp is None:
            raise ValueError(
                "TANGEDCO record does not contain "
                "a valid timestamp."
            )

        region_value = _first_present(
            record,
            REGION_FIELDS,
        )

        asset_value = _first_present(
            record,
            ASSET_FIELDS,
        )

        demand = _safe_float(
            _first_present(
                record,
                DEMAND_FIELDS,
            )
        )

        generation = _safe_float(
            _first_present(
                record,
                GENERATION_FIELDS,
            )
        )

        available_power = _safe_float(
            _first_present(
                record,
                AVAILABLE_POWER_FIELDS,
            )
        )

        frequency = _safe_float(
            _first_present(
                record,
                FREQUENCY_FIELDS,
            )
        )

        renewable = _safe_float(
            _first_present(
                record,
                RENEWABLE_FIELDS,
            )
        )

        thermal = _safe_float(
            _first_present(
                record,
                THERMAL_FIELDS,
            )
        )

        hydro = _safe_float(
            _first_present(
                record,
                HYDRO_FIELDS,
            )
        )

        solar = _safe_float(
            _first_present(
                record,
                SOLAR_FIELDS,
            )
        )

        wind = _safe_float(
            _first_present(
                record,
                WIND_FIELDS,
            )
        )

        exchange = _safe_float(
            _first_present(
                record,
                EXCHANGE_FIELDS,
            )
        )

        shortage = _safe_float(
            _first_present(
                record,
                SHORTAGE_FIELDS,
            )
        )

        surplus = _safe_float(
            _first_present(
                record,
                SURPLUS_FIELDS,
            )
        )

        power_factor = _safe_float(
            _first_present(
                record,
                POWER_FACTOR_FIELDS,
            )
        )

        unit_value = _first_present(
            record,
            UNIT_FIELDS,
        )

        known_fields: set[str] = set()

        for fields in (
            TIMESTAMP_FIELDS,
            REGION_FIELDS,
            ASSET_FIELDS,
            DEMAND_FIELDS,
            GENERATION_FIELDS,
            AVAILABLE_POWER_FIELDS,
            FREQUENCY_FIELDS,
            RENEWABLE_FIELDS,
            THERMAL_FIELDS,
            HYDRO_FIELDS,
            SOLAR_FIELDS,
            WIND_FIELDS,
            EXCHANGE_FIELDS,
            SHORTAGE_FIELDS,
            SURPLUS_FIELDS,
            POWER_FACTOR_FIELDS,
            UNIT_FIELDS,
        ):
            known_fields.update(
                fields
            )

        metadata = {
            key: value
            for key, value in record.items()
            if key not in known_fields
        }

        return TANGEDCORecord(
            timestamp=timestamp,
            region_id=(
                str(region_value)
                if region_value is not None
                else None
            ),
            asset_id=(
                str(asset_value)
                if asset_value is not None
                else None
            ),
            demand_mw=demand,
            generation_mw=generation,
            available_power_mw=available_power,
            frequency_hz=frequency,
            renewable_generation_mw=renewable,
            thermal_generation_mw=thermal,
            hydro_generation_mw=hydro,
            solar_generation_mw=solar,
            wind_generation_mw=wind,
            exchange_mw=exchange,
            shortage_mw=shortage,
            surplus_mw=surplus,
            power_factor=power_factor,
            unit=(
                str(unit_value)
                if unit_value is not None
                else None
            ),
            source=self.source_name,
            metadata=metadata,
        )

    # ========================================================
    # REMOTE NORMALIZATION
    # ========================================================

    def fetch_and_normalize_json(
        self,
        url: str,
        headers: Mapping[str, str] | None = None,
    ) -> TANGEDCOLoadResult:
        """Fetch JSON and normalize it."""
        payload = self.fetch_json(
            url,
            headers=headers,
        )

        return self.normalize_json(
            payload
        )

    def fetch_and_normalize_csv(
        self,
        url: str,
        headers: Mapping[str, str] | None = None,
    ) -> TANGEDCOLoadResult:
        """Fetch CSV and normalize it."""
        text = self.fetch(
            url,
            headers=headers,
        )

        return self.normalize_csv(
            text
        )

    # ========================================================
    # FILTERING
    # ========================================================

    def filter_by_region(
        self,
        records: Iterable[TANGEDCORecord],
        region_id: str,
    ) -> list[TANGEDCORecord]:
        """Filter records by region."""
        normalized = str(
            region_id
        ).strip().lower()

        return [
            record
            for record in records
            if (
                record.region_id is not None
                and record.region_id.strip().lower()
                == normalized
            )
        ]

    def filter_by_asset(
        self,
        records: Iterable[TANGEDCORecord],
        asset_id: str,
    ) -> list[TANGEDCORecord]:
        """Filter records by asset."""
        normalized = str(
            asset_id
        ).strip().lower()

        return [
            record
            for record in records
            if (
                record.asset_id is not None
                and record.asset_id.strip().lower()
                == normalized
            )
        ]

    def filter_by_time_range(
        self,
        records: Iterable[TANGEDCORecord],
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[TANGEDCORecord]:
        """Filter records by an inclusive timestamp range."""
        normalized_start = (
            _parse_timestamp(start)
            if start is not None
            else None
        )

        normalized_end = (
            _parse_timestamp(end)
            if end is not None
            else None
        )

        filtered: list[TANGEDCORecord] = []

        for record in records:
            if (
                normalized_start is not None
                and record.timestamp
                < normalized_start
            ):
                continue

            if (
                normalized_end is not None
                and record.timestamp
                > normalized_end
            ):
                continue

            filtered.append(
                record
            )

        return filtered

    # ========================================================
    # SORTING
    # ========================================================

    def sort_by_timestamp(
        self,
        records: Iterable[TANGEDCORecord],
        descending: bool = False,
    ) -> list[TANGEDCORecord]:
        """Sort records by timestamp."""
        return sorted(
            records,
            key=lambda record: record.timestamp,
            reverse=descending,
        )

    # ========================================================
    # GRID ANALYSIS
    # ========================================================

    def calculate_generation_demand_balance(
        self,
        record: TANGEDCORecord,
    ) -> float | None:
        """
        Calculate generation minus demand.

        Positive:
            generation exceeds demand.

        Negative:
            demand exceeds generation.

        This is an analytical value only.
        """
        if (
            record.generation_mw is None
            or record.demand_mw is None
        ):
            return None

        return (
            record.generation_mw
            - record.demand_mw
        )

    def calculate_available_margin(
        self,
        record: TANGEDCORecord,
    ) -> float | None:
        """
        Calculate available-power margin relative to demand.
        """
        if (
            record.available_power_mw is None
            or record.demand_mw is None
        ):
            return None

        if record.demand_mw <= 0.0:
            return None

        return (
            record.available_power_mw
            - record.demand_mw
        )

    def calculate_renewable_share(
        self,
        record: TANGEDCORecord,
    ) -> float | None:
        """
        Calculate renewable generation as a fraction of total
        generation.
        """
        if (
            record.renewable_generation_mw
            is None
            or record.generation_mw is None
        ):
            return None

        if record.generation_mw <= 0.0:
            return None

        return max(
            0.0,
            min(
                1.0,
                record.renewable_generation_mw
                / record.generation_mw,
            ),
        )

    # ========================================================
    # BASIC STATISTICS
    # ========================================================

    def statistics(
        self,
        records: Iterable[TANGEDCORecord],
    ) -> dict[str, float | int | None]:
        """
        Calculate basic statistics for TANGEDCO observations.
        """
        record_list = list(
            records
        )

        demands = [
            record.demand_mw
            for record in record_list
            if record.demand_mw is not None
        ]

        generations = [
            record.generation_mw
            for record in record_list
            if record.generation_mw is not None
        ]

        frequencies = [
            record.frequency_hz
            for record in record_list
            if record.frequency_hz is not None
        ]

        available = [
            record.available_power_mw
            for record in record_list
            if record.available_power_mw is not None
        ]

        def average(
            values: list[float],
        ) -> float | None:
            if not values:
                return None

            return (
                sum(values)
                / len(values)
            )

        return {
            "record_count": len(
                record_list
            ),
            "average_demand_mw": average(
                demands
            ),
            "maximum_demand_mw": (
                max(demands)
                if demands
                else None
            ),
            "average_generation_mw": average(
                generations
            ),
            "maximum_generation_mw": (
                max(generations)
                if generations
                else None
            ),
            "average_available_power_mw": average(
                available
            ),
            "average_frequency_hz": average(
                frequencies
            ),
            "minimum_frequency_hz": (
                min(frequencies)
                if frequencies
                else None
            ),
            "maximum_frequency_hz": (
                max(frequencies)
                if frequencies
                else None
            ),
        }

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_record(
        self,
        record: TANGEDCORecord,
    ) -> list[str]:
        """Validate a normalized TANGEDCO record."""
        errors: list[str] = []

        if (
            record.timestamp.tzinfo
            is None
        ):
            errors.append(
                "Timestamp is timezone-naive."
            )

        non_negative_fields = {
            "demand_mw": record.demand_mw,
            "generation_mw": record.generation_mw,
            "available_power_mw": (
                record.available_power_mw
            ),
            "renewable_generation_mw": (
                record.renewable_generation_mw
            ),
            "thermal_generation_mw": (
                record.thermal_generation_mw
            ),
            "hydro_generation_mw": (
                record.hydro_generation_mw
            ),
            "solar_generation_mw": (
                record.solar_generation_mw
            ),
            "wind_generation_mw": (
                record.wind_generation_mw
            ),
        }

        for name, value in non_negative_fields.items():
            if value is not None and value < 0.0:
                errors.append(
                    f"{name} cannot be negative."
                )

        if (
            record.frequency_hz is not None
            and not (
                40.0
                <= record.frequency_hz
                <= 70.0
            )
        ):
            errors.append(
                "Frequency is outside the supported "
                "validation range of 40-70 Hz."
            )

        if (
            record.power_factor is not None
            and not (
                0.0
                <= record.power_factor
                <= 1.0
            )
        ):
            errors.append(
                "Power factor must be between 0 and 1."
            )

        return errors

    def validate_records(
        self,
        records: Iterable[TANGEDCORecord],
    ) -> list[str]:
        """Validate multiple records."""
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
        records: Iterable[TANGEDCORecord],
    ) -> list[dict[str, Any]]:
        """Convert records into dictionaries."""
        return [
            record.to_dict()
            for record in records
        ]


# ============================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================


def normalize_tangedco_data(
    payload: Any,
) -> TANGEDCOLoadResult:
    """
    Normalize an already-fetched TANGEDCO JSON payload.
    """
    adapter = TANGEDCOPublicAdapter()

    return adapter.normalize_json(
        payload
    )


def normalize_tangedco_csv(
    csv_text: str,
) -> TANGEDCOLoadResult:
    """Normalize TANGEDCO CSV text."""
    adapter = TANGEDCOPublicAdapter()

    return adapter.normalize_csv(
        csv_text
    )


def load_tangedco_file(
    file_path: str | Path,
) -> TANGEDCOLoadResult:
    """Load and normalize a local TANGEDCO CSV or JSON file."""
    adapter = TANGEDCOPublicAdapter()

    return adapter.load_file(
        file_path
    )


def fetch_tangedco_json(
    url: str,
    headers: Mapping[str, str] | None = None,
) -> TANGEDCOLoadResult:
    """Fetch and normalize JSON from a public endpoint."""
    adapter = TANGEDCOPublicAdapter()

    return adapter.fetch_and_normalize_json(
        url,
        headers=headers,
    )


def fetch_tangedco_csv(
    url: str,
    headers: Mapping[str, str] | None = None,
) -> TANGEDCOLoadResult:
    """Fetch and normalize CSV from a public endpoint."""
    adapter = TANGEDCOPublicAdapter()

    return adapter.fetch_and_normalize_csv(
        url,
        headers=headers,
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "TANGEDCORecord",
    "TANGEDCOLoadResult",
    "TANGEDCOPublicAdapter",
    "normalize_tangedco_data",
    "normalize_tangedco_csv",
    "load_tangedco_file",
    "fetch_tangedco_json",
    "fetch_tangedco_csv",
]