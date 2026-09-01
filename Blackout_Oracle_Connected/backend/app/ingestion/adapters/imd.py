"""
Blackout Oracle - IMD Weather Data Adapter.

Provides utilities for consuming and normalizing weather data
obtained from India Meteorological Department (IMD) sources.

The adapter is intentionally independent of:

- FastAPI
- SQLAlchemy
- Database repositories
- Machine-learning frameworks
- Third-party HTTP clients

It accepts already-fetched JSON/dictionary data and can also
optionally fetch JSON from an HTTP endpoint using Python's
standard library.

The normalized output can be consumed by the weather feature
engineering and risk-analysis layers.

This module does not directly control physical grid equipment.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_SOURCE = "imd"

DEFAULT_TIMEOUT_SECONDS = 15

TIMESTAMP_FIELDS = (
    "timestamp",
    "datetime",
    "date_time",
    "time",
    "observation_time",
    "observed_at",
    "valid_time",
)

LOCATION_FIELDS = (
    "location",
    "location_name",
    "station",
    "station_name",
    "city",
)

STATION_ID_FIELDS = (
    "station_id",
    "station_code",
    "stationid",
    "station_code_id",
)

LATITUDE_FIELDS = (
    "latitude",
    "lat",
)

LONGITUDE_FIELDS = (
    "longitude",
    "lon",
    "lng",
)

TEMPERATURE_FIELDS = (
    "temperature",
    "temp",
    "temperature_c",
    "temp_c",
)

HUMIDITY_FIELDS = (
    "humidity",
    "relative_humidity",
    "relativehumidity",
    "rh",
)

WIND_SPEED_FIELDS = (
    "wind_speed",
    "windspeed",
    "wind_speed_kmh",
    "wind_speed_ms",
)

WIND_DIRECTION_FIELDS = (
    "wind_direction",
    "winddirection",
    "wind_dir",
)

PRESSURE_FIELDS = (
    "pressure",
    "surface_pressure",
    "pressure_hpa",
    "mslp",
)

RAINFALL_FIELDS = (
    "rainfall",
    "rain",
    "precipitation",
    "rainfall_mm",
    "precipitation_mm",
)

VISIBILITY_FIELDS = (
    "visibility",
    "visibility_km",
)

CLOUD_FIELDS = (
    "cloud_cover",
    "cloudcover",
    "cloud_percentage",
)

WEATHER_DESCRIPTION_FIELDS = (
    "weather",
    "weather_description",
    "condition",
    "description",
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

        "Station ID" -> "station_id"
        "Wind-Speed" -> "wind_speed"
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

    return value


def _normalize_mapping(
    data: Mapping[str, Any],
) -> dict[str, Any]:
    """Normalize dictionary keys."""
    return {
        _normalize_key(key): value
        for key, value in data.items()
    }


def _first_present(
    data: Mapping[str, Any],
    fields: Iterable[str],
) -> Any:
    """Return the first non-empty field value."""
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
    """Safely convert a value to float."""
    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return None

    try:
        return float(
            str(value).strip()
        )
    except (
        TypeError,
        ValueError,
    ):
        return None


def _parse_timestamp(
    value: Any,
) -> datetime | None:
    """
    Parse a timestamp into a timezone-aware UTC datetime.

    Supports datetime objects and ISO-8601 strings.
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


def _normalize_percentage(
    value: float | None,
) -> float | None:
    """
    Normalize a percentage value to the range 0-100.
    """
    if value is None:
        return None

    return max(
        0.0,
        min(
            100.0,
            value,
        ),
    )


# ============================================================
# DATA STRUCTURES
# ============================================================


@dataclass
class IMDWeatherRecord:
    """
    Normalized weather observation.

    All measurements are optional because different IMD
    observations may contain different fields.
    """

    timestamp: datetime

    station_id: str | None = None
    station_name: str | None = None

    latitude: float | None = None
    longitude: float | None = None

    temperature_c: float | None = None
    humidity_percent: float | None = None

    wind_speed: float | None = None
    wind_direction: float | None = None

    pressure_hpa: float | None = None
    rainfall_mm: float | None = None

    visibility_km: float | None = None
    cloud_cover_percent: float | None = None

    weather_description: str | None = None

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
            "station_id": self.station_id,
            "station_name": self.station_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "temperature_c": self.temperature_c,
            "humidity_percent": self.humidity_percent,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "pressure_hpa": self.pressure_hpa,
            "rainfall_mm": self.rainfall_mm,
            "visibility_km": self.visibility_km,
            "cloud_cover_percent": self.cloud_cover_percent,
            "weather_description": (
                self.weather_description
            ),
            "source": self.source,
            "metadata": dict(
                self.metadata
            ),
        }


@dataclass
class IMDLoadResult:
    """
    Result of an IMD data-loading operation.
    """

    records: list[IMDWeatherRecord] = field(
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
        """Return True when at least one record was loaded."""
        return (
            self.valid_records > 0
            and not self.errors
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Convert the result into a dictionary."""
        return {
            "source": self.source,
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "skipped_records": self.skipped_records,
            "record_count": len(
                self.records
            ),
            "success": self.success,
            "errors": list(
                self.errors
            ),
            "loaded_at": self.loaded_at.isoformat(),
        }


# ============================================================
# IMD ADAPTER
# ============================================================


class IMDWeatherAdapter:
    """
    Adapter for IMD weather observations.

    The adapter accepts data that has already been obtained from
    an IMD endpoint or another IMD-compatible source.

    It can also fetch JSON data from a supplied endpoint using
    urllib from the Python standard library.
    """

    def __init__(
        self,
        source_name: str = DEFAULT_SOURCE,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize the IMD adapter."""
        self.source_name = source_name
        self.timeout = max(
            1,
            int(timeout),
        )

    # ========================================================
    # HTTP FETCHING
    # ========================================================

    def fetch_json(
        self,
        url: str,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """
        Fetch JSON from an HTTP endpoint.

        The URL must point to a source the user is authorized
        to access.
        """
        request_headers = {
            "Accept": "application/json",
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
                f"IMD endpoint returned HTTP "
                f"{exc.code}: {exc.reason}"
            ) from exc

        except URLError as exc:
            raise RuntimeError(
                f"Unable to reach IMD endpoint: "
                f"{exc.reason}"
            ) from exc

        except TimeoutError as exc:
            raise RuntimeError(
                "IMD request timed out."
            ) from exc

        try:
            return json.loads(
                raw_data.decode(
                    "utf-8"
                )
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise RuntimeError(
                "IMD endpoint returned invalid JSON."
            ) from exc

    # ========================================================
    # RECORD EXTRACTION
    # ========================================================

    def extract_records(
        self,
        payload: Any,
    ) -> list[dict[str, Any]]:
        """
        Extract record dictionaries from common JSON structures.

        Supported structures include:

            [
                {...},
                {...}
            ]

        and:

            {
                "data": [
                    {...},
                    {...}
                ]
            }

        The keys "records", "items", "results", and "observations"
        are also recognized.
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

        for container_name in (
            "data",
            "records",
            "items",
            "results",
            "observations",
        ):
            container = payload.get(
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

        # A single observation can also be supplied directly.
        return [
            dict(payload)
        ]

    # ========================================================
    # NORMALIZATION
    # ========================================================

    def normalize_record(
        self,
        raw_record: Mapping[str, Any],
    ) -> IMDWeatherRecord:
        """
        Normalize one raw IMD observation.
        """
        if not isinstance(
            raw_record,
            Mapping,
        ):
            raise TypeError(
                "IMD weather record must be a mapping."
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
                "IMD record does not contain a valid timestamp."
            )

        station_id_value = _first_present(
            record,
            STATION_ID_FIELDS,
        )

        station_name_value = _first_present(
            record,
            LOCATION_FIELDS,
        )

        latitude = _safe_float(
            _first_present(
                record,
                LATITUDE_FIELDS,
            )
        )

        longitude = _safe_float(
            _first_present(
                record,
                LONGITUDE_FIELDS,
            )
        )

        temperature = _safe_float(
            _first_present(
                record,
                TEMPERATURE_FIELDS,
            )
        )

        humidity = _normalize_percentage(
            _safe_float(
                _first_present(
                    record,
                    HUMIDITY_FIELDS,
                )
            )
        )

        wind_speed = _safe_float(
            _first_present(
                record,
                WIND_SPEED_FIELDS,
            )
        )

        wind_direction = _safe_float(
            _first_present(
                record,
                WIND_DIRECTION_FIELDS,
            )
        )

        pressure = _safe_float(
            _first_present(
                record,
                PRESSURE_FIELDS,
            )
        )

        rainfall = _safe_float(
            _first_present(
                record,
                RAINFALL_FIELDS,
            )
        )

        visibility = _safe_float(
            _first_present(
                record,
                VISIBILITY_FIELDS,
            )
        )

        cloud_cover = _normalize_percentage(
            _safe_float(
                _first_present(
                    record,
                    CLOUD_FIELDS,
                )
            )
        )

        weather_description_value = _first_present(
            record,
            WEATHER_DESCRIPTION_FIELDS,
        )

        known_fields = set(
            TIMESTAMP_FIELDS
        )

        known_fields.update(
            LOCATION_FIELDS
        )

        known_fields.update(
            STATION_ID_FIELDS
        )

        known_fields.update(
            LATITUDE_FIELDS
        )

        known_fields.update(
            LONGITUDE_FIELDS
        )

        known_fields.update(
            TEMPERATURE_FIELDS
        )

        known_fields.update(
            HUMIDITY_FIELDS
        )

        known_fields.update(
            WIND_SPEED_FIELDS
        )

        known_fields.update(
            WIND_DIRECTION_FIELDS
        )

        known_fields.update(
            PRESSURE_FIELDS
        )

        known_fields.update(
            RAINFALL_FIELDS
        )

        known_fields.update(
            VISIBILITY_FIELDS
        )

        known_fields.update(
            CLOUD_FIELDS
        )

        known_fields.update(
            WEATHER_DESCRIPTION_FIELDS
        )

        metadata = {
            key: value
            for key, value in record.items()
            if key not in known_fields
        }

        return IMDWeatherRecord(
            timestamp=timestamp,
            station_id=(
                str(station_id_value)
                if station_id_value is not None
                else None
            ),
            station_name=(
                str(station_name_value)
                if station_name_value is not None
                else None
            ),
            latitude=latitude,
            longitude=longitude,
            temperature_c=temperature,
            humidity_percent=humidity,
            wind_speed=wind_speed,
            wind_direction=wind_direction,
            pressure_hpa=pressure,
            rainfall_mm=rainfall,
            visibility_km=visibility,
            cloud_cover_percent=cloud_cover,
            weather_description=(
                str(weather_description_value)
                if weather_description_value is not None
                else None
            ),
            source=self.source_name,
            metadata=metadata,
        )

    # ========================================================
    # PAYLOAD NORMALIZATION
    # ========================================================

    def normalize_payload(
        self,
        payload: Any,
    ) -> IMDLoadResult:
        """
        Normalize an IMD JSON payload.
        """
        result = IMDLoadResult(
            source=self.source_name
        )

        raw_records = self.extract_records(
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
                normalized = self.normalize_record(
                    raw_record
                )

                result.records.append(
                    normalized
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
    # END-TO-END FETCH
    # ========================================================

    def fetch_and_normalize(
        self,
        url: str,
        headers: Mapping[str, str] | None = None,
    ) -> IMDLoadResult:
        """
        Fetch JSON from an endpoint and normalize the result.
        """
        payload = self.fetch_json(
            url,
            headers=headers,
        )

        return self.normalize_payload(
            payload
        )

    # ========================================================
    # FILTERING
    # ========================================================

    def filter_by_station(
        self,
        records: Iterable[IMDWeatherRecord],
        station_id: str,
    ) -> list[IMDWeatherRecord]:
        """Filter records by station ID."""
        normalized = str(
            station_id
        ).strip()

        return [
            record
            for record in records
            if (
                record.station_id is not None
                and record.station_id.strip()
                == normalized
            )
        ]

    def filter_by_location(
        self,
        records: Iterable[IMDWeatherRecord],
        location: str,
    ) -> list[IMDWeatherRecord]:
        """Filter records by station/location name."""
        normalized = str(
            location
        ).strip().lower()

        return [
            record
            for record in records
            if (
                record.station_name is not None
                and record.station_name.strip().lower()
                == normalized
            )
        ]

    def filter_by_time_range(
        self,
        records: Iterable[IMDWeatherRecord],
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[IMDWeatherRecord]:
        """
        Filter records by timestamp.

        Start and end are inclusive.
        """
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

        filtered: list[IMDWeatherRecord] = []

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
        records: Iterable[IMDWeatherRecord],
        descending: bool = False,
    ) -> list[IMDWeatherRecord]:
        """Sort weather records by timestamp."""
        return sorted(
            records,
            key=lambda record: record.timestamp,
            reverse=descending,
        )

    # ========================================================
    # WEATHER RISK FEATURES
    # ========================================================

    def calculate_weather_risk_factors(
        self,
        record: IMDWeatherRecord,
    ) -> dict[str, float]:
        """
        Calculate normalized weather-related risk indicators.

        These values are analytical features for the risk engine.
        They are not protection-system thresholds.

        Returns values in the range 0.0-1.0.
        """
        factors: dict[str, float] = {}

        # High wind risk.
        if record.wind_speed is not None:
            factors["wind_risk"] = max(
                0.0,
                min(
                    1.0,
                    record.wind_speed
                    / 100.0,
                ),
            )
        else:
            factors["wind_risk"] = 0.0

        # Heavy rainfall risk.
        if record.rainfall_mm is not None:
            factors["rainfall_risk"] = max(
                0.0,
                min(
                    1.0,
                    record.rainfall_mm
                    / 100.0,
                ),
            )
        else:
            factors["rainfall_risk"] = 0.0

        # Extreme temperature risk.
        if record.temperature_c is not None:
            temperature_deviation = max(
                0.0,
                abs(
                    record.temperature_c
                    - 25.0
                ),
            )

            factors["temperature_risk"] = max(
                0.0,
                min(
                    1.0,
                    temperature_deviation
                    / 30.0,
                ),
            )
        else:
            factors["temperature_risk"] = 0.0

        # High humidity risk.
        if record.humidity_percent is not None:
            factors["humidity_risk"] = max(
                0.0,
                min(
                    1.0,
                    max(
                        0.0,
                        record.humidity_percent
                        - 70.0,
                    )
                    / 30.0,
                ),
            )
        else:
            factors["humidity_risk"] = 0.0

        return factors

    def calculate_weather_risk_score(
        self,
        record: IMDWeatherRecord,
    ) -> float:
        """
        Calculate an overall normalized weather risk score.

        This is an analytical score intended for downstream
        prediction/risk processing.
        """
        factors = (
            self.calculate_weather_risk_factors(
                record
            )
        )

        return (
            factors["wind_risk"] * 0.35
            + factors["rainfall_risk"] * 0.30
            + factors["temperature_risk"] * 0.20
            + factors["humidity_risk"] * 0.15
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_record(
        self,
        record: IMDWeatherRecord,
    ) -> list[str]:
        """
        Validate a normalized IMD weather record.
        """
        errors: list[str] = []

        if not isinstance(
            record.timestamp,
            datetime,
        ):
            errors.append(
                "Invalid timestamp."
            )

        if (
            record.timestamp.tzinfo
            is None
        ):
            errors.append(
                "Timestamp is timezone-naive."
            )

        if record.latitude is not None:
            if not -90.0 <= record.latitude <= 90.0:
                errors.append(
                    "Latitude must be between -90 and 90."
                )

        if record.longitude is not None:
            if not -180.0 <= record.longitude <= 180.0:
                errors.append(
                    "Longitude must be between -180 and 180."
                )

        if record.humidity_percent is not None:
            if not 0.0 <= record.humidity_percent <= 100.0:
                errors.append(
                    "Humidity must be between 0 and 100."
                )

        if record.cloud_cover_percent is not None:
            if not 0.0 <= record.cloud_cover_percent <= 100.0:
                errors.append(
                    "Cloud cover must be between 0 and 100."
                )

        if record.wind_speed is not None:
            if record.wind_speed < 0.0:
                errors.append(
                    "Wind speed cannot be negative."
                )

        if record.rainfall_mm is not None:
            if record.rainfall_mm < 0.0:
                errors.append(
                    "Rainfall cannot be negative."
                )

        return errors

    def validate_records(
        self,
        records: Iterable[IMDWeatherRecord],
    ) -> list[str]:
        """
        Validate multiple normalized records.
        """
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
        records: Iterable[IMDWeatherRecord],
    ) -> list[dict[str, Any]]:
        """Convert records to dictionaries."""
        return [
            record.to_dict()
            for record in records
        ]


# ============================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================


def normalize_imd_data(
    payload: Any,
) -> IMDLoadResult:
    """
    Normalize an already-fetched IMD JSON payload.
    """
    adapter = IMDWeatherAdapter()

    return adapter.normalize_payload(
        payload
    )


def fetch_imd_data(
    url: str,
    headers: Mapping[str, str] | None = None,
) -> IMDLoadResult:
    """
    Fetch and normalize IMD-compatible JSON data.
    """
    adapter = IMDWeatherAdapter()

    return adapter.fetch_and_normalize(
        url,
        headers=headers,
    )


def calculate_weather_risk(
    record: IMDWeatherRecord,
) -> float:
    """
    Calculate the analytical weather risk score for one record.
    """
    adapter = IMDWeatherAdapter()

    return adapter.calculate_weather_risk_score(
        record
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "SUPPORTED_EXTENSIONS",
    "IMDWeatherRecord",
    "IMDLoadResult",
    "IMDWeatherAdapter",
    "normalize_imd_data",
    "fetch_imd_data",
    "calculate_weather_risk",
]