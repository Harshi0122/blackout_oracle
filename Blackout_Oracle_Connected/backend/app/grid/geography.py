"""
Blackout Oracle - Grid Geography Utilities.

Provides deterministic geographic calculations for power-grid
assets and regions.

Used for:

- Distance calculations
- Geographic proximity analysis
- Asset clustering
- Weather exposure analysis
- Regional risk analysis
- Infrastructure mapping
- Outage impact analysis

This module performs analytical calculations only.
It does not control physical grid equipment.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any


# ============================================================
# CONSTANTS
# ============================================================

EARTH_RADIUS_KM = 6371.0088

EPSILON = 1e-9


# ============================================================
# BASIC HELPERS
# ============================================================


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Safely convert a value to float.

    Invalid, NaN, and infinite values are replaced with
    the supplied default.
    """
    try:
        result = float(value)

        if not math.isfinite(result):
            return default

        return result

    except (TypeError, ValueError):
        return default


def _validate_latitude(
    latitude: float,
) -> float:
    """
    Normalize latitude to the valid geographic range.
    """
    return max(
        -90.0,
        min(
            90.0,
            _safe_float(latitude),
        ),
    )


def _normalize_longitude(
    longitude: float,
) -> float:
    """
    Normalize longitude to the range [-180, 180].
    """
    value = _safe_float(longitude)

    normalized = (
        (value + 180.0)
        % 360.0
    ) - 180.0

    return normalized


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    """
    Clamp a value to a specified range.
    """
    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


# ============================================================
# COORDINATE VALIDATION
# ============================================================


def valid_coordinates(
    latitude: float,
    longitude: float,
) -> bool:
    """
    Determine whether latitude and longitude are valid.

    Returns:
        True if both coordinates are finite and within
        their geographic ranges.
    """
    try:
        lat = float(latitude)
        lon = float(longitude)

        if not (
            math.isfinite(lat)
            and math.isfinite(lon)
        ):
            return False

        return (
            -90.0 <= lat <= 90.0
            and -180.0 <= lon <= 180.0
        )

    except (TypeError, ValueError):
        return False


def normalize_coordinates(
    latitude: float,
    longitude: float,
) -> tuple[float, float]:
    """
    Normalize a coordinate pair.

    Returns:
        Tuple containing normalized latitude and longitude.
    """
    return (
        _validate_latitude(latitude),
        _normalize_longitude(longitude),
    )


# ============================================================
# DISTANCE
# ============================================================


def haversine_distance_km(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """
    Calculate great-circle distance between two coordinates
    using the Haversine formula.

    Returns:
        Distance in kilometers.
    """
    lat1 = math.radians(
        _validate_latitude(latitude_1)
    )

    lat2 = math.radians(
        _validate_latitude(latitude_2)
    )

    lon1 = math.radians(
        _normalize_longitude(longitude_1)
    )

    lon2 = math.radians(
        _normalize_longitude(longitude_2)
    )

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        math.sin(delta_lat / 2.0) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2.0) ** 2
    )

    a = _clamp(
        a,
        0.0,
        1.0,
    )

    central_angle = 2.0 * math.asin(
        math.sqrt(a)
    )

    return (
        EARTH_RADIUS_KM
        * central_angle
    )


def distance_meters(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """
    Calculate geographic distance in meters.
    """
    return (
        haversine_distance_km(
            latitude_1,
            longitude_1,
            latitude_2,
            longitude_2,
        )
        * 1000.0
    )


# ============================================================
# BEARING
# ============================================================


def bearing_degrees(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """
    Calculate the initial bearing from one coordinate to
    another.

    Returns:
        Bearing in degrees clockwise from north.
    """
    lat1 = math.radians(
        _validate_latitude(latitude_1)
    )

    lat2 = math.radians(
        _validate_latitude(latitude_2)
    )

    lon1 = math.radians(
        _normalize_longitude(longitude_1)
    )

    lon2 = math.radians(
        _normalize_longitude(longitude_2)
    )

    delta_lon = lon2 - lon1

    x = (
        math.cos(lat2)
        * math.sin(delta_lon)
    )

    y = (
        math.cos(lat1)
        * math.sin(lat2)
        - math.sin(lat1)
        * math.cos(lat2)
        * math.cos(delta_lon)
    )

    bearing = math.degrees(
        math.atan2(x, y)
    )

    return (
        bearing + 360.0
    ) % 360.0


def bearing_direction(
    bearing: float,
) -> str:
    """
    Convert a bearing into a cardinal/intercardinal direction.

    Returns one of:

        N
        NE
        E
        SE
        S
        SW
        W
        NW
    """
    value = (
        _safe_float(bearing)
        % 360.0
    )

    directions = (
        "N",
        "NE",
        "E",
        "SE",
        "S",
        "SW",
        "W",
        "NW",
    )

    index = int(
        (
            value + 22.5
        )
        // 45.0
    ) % 8

    return directions[index]


# ============================================================
# MIDPOINT
# ============================================================


def geographic_midpoint(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> tuple[float, float]:
    """
    Calculate the geographic midpoint between two coordinates.

    Returns:
        Tuple of (latitude, longitude).
    """
    lat1 = math.radians(
        _validate_latitude(latitude_1)
    )

    lat2 = math.radians(
        _validate_latitude(latitude_2)
    )

    lon1 = math.radians(
        _normalize_longitude(longitude_1)
    )

    lon2 = math.radians(
        _normalize_longitude(longitude_2)
    )

    x1 = math.cos(lat1) * math.cos(lon1)
    y1 = math.cos(lat1) * math.sin(lon1)
    z1 = math.sin(lat1)

    x2 = math.cos(lat2) * math.cos(lon2)
    y2 = math.cos(lat2) * math.sin(lon2)
    z2 = math.sin(lat2)

    x = x1 + x2
    y = y1 + y2
    z = z1 + z2

    longitude = math.atan2(
        y,
        x,
    )

    hypotenuse = math.sqrt(
        x * x
        + y * y
    )

    latitude = math.atan2(
        z,
        hypotenuse,
    )

    return (
        math.degrees(latitude),
        math.degrees(longitude),
    )


# ============================================================
# PROXIMITY
# ============================================================


def within_radius(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
    radius_km: float,
) -> bool:
    """
    Determine whether two coordinates are within a specified
    radius.
    """
    radius = max(
        0.0,
        _safe_float(radius_km),
    )

    return (
        haversine_distance_km(
            latitude_1,
            longitude_1,
            latitude_2,
            longitude_2,
        )
        <= radius
    )


def proximity_score(
    distance_km: float,
    maximum_distance_km: float,
) -> float:
    """
    Convert geographic distance into a proximity score.

    Closer assets receive higher scores.

    Returns:
        Value between 0.0 and 1.0.
    """
    distance = max(
        0.0,
        _safe_float(distance_km),
    )

    maximum = max(
        EPSILON,
        _safe_float(maximum_distance_km),
    )

    return _clamp(
        1.0
        - (
            distance
            / maximum
        )
    )


# ============================================================
# ASSET DISTANCE
# ============================================================


def calculate_asset_distance(
    asset_a: dict[str, Any],
    asset_b: dict[str, Any],
) -> float:
    """
    Calculate the distance between two asset dictionaries.

    Expected keys:

        latitude
        longitude

    Returns:
        Distance in kilometers.
    """
    return haversine_distance_km(
        asset_a.get(
            "latitude",
            0.0,
        ),
        asset_a.get(
            "longitude",
            0.0,
        ),
        asset_b.get(
            "latitude",
            0.0,
        ),
        asset_b.get(
            "longitude",
            0.0,
        ),
    )


# ============================================================
# NEAREST ASSETS
# ============================================================


def find_nearest_assets(
    latitude: float,
    longitude: float,
    assets: Iterable[dict[str, Any]],
    limit: int = 10,
    maximum_distance_km: float | None = None,
) -> list[dict[str, Any]]:
    """
    Find the geographically nearest assets.

    Each asset should contain:

        latitude
        longitude

    Optional:

        id
        name
        asset_type

    Returns:
        New dictionaries containing the original asset fields
        plus distance_km.
    """
    target_latitude = _validate_latitude(
        latitude
    )

    target_longitude = _normalize_longitude(
        longitude
    )

    results: list[dict[str, Any]] = []

    maximum_distance = (
        None
        if maximum_distance_km is None
        else max(
            0.0,
            _safe_float(
                maximum_distance_km
            ),
        )
    )

    for asset in assets:
        asset_latitude = asset.get(
            "latitude"
        )

        asset_longitude = asset.get(
            "longitude"
        )

        if (
            asset_latitude is None
            or asset_longitude is None
        ):
            continue

        if not valid_coordinates(
            asset_latitude,
            asset_longitude,
        ):
            continue

        distance = haversine_distance_km(
            target_latitude,
            target_longitude,
            asset_latitude,
            asset_longitude,
        )

        if (
            maximum_distance is not None
            and distance > maximum_distance
        ):
            continue

        result = dict(asset)

        result["distance_km"] = distance

        results.append(result)

    results.sort(
        key=lambda item: _safe_float(
            item.get(
                "distance_km",
                float("inf"),
            ),
            float("inf"),
        )
    )

    return results[
        :max(
            0,
            int(limit),
        )
    ]


# ============================================================
# ASSET CLUSTERING
# ============================================================


def geographic_cluster(
    assets: Iterable[dict[str, Any]],
    radius_km: float = 5.0,
) -> list[list[dict[str, Any]]]:
    """
    Group geographically close assets into simple clusters.

    This is a lightweight deterministic clustering method.

    Each asset should contain:

        latitude
        longitude

    Assets are assigned to the first existing cluster whose
    representative point lies within the specified radius.
    """
    radius = max(
        0.0,
        _safe_float(
            radius_km,
            5.0,
        ),
    )

    clusters: list[
        list[dict[str, Any]]
    ] = []

    representatives: list[
        tuple[float, float]
    ] = []

    for asset in assets:
        latitude = asset.get(
            "latitude"
        )

        longitude = asset.get(
            "longitude"
        )

        if (
            latitude is None
            or longitude is None
        ):
            continue

        if not valid_coordinates(
            latitude,
            longitude,
        ):
            continue

        assigned = False

        for index, representative in enumerate(
            representatives
        ):
            distance = haversine_distance_km(
                latitude,
                longitude,
                representative[0],
                representative[1],
            )

            if distance <= radius:
                clusters[index].append(
                    dict(asset)
                )

                assigned = True

                break

        if not assigned:
            clusters.append(
                [dict(asset)]
            )

            representatives.append(
                (
                    float(latitude),
                    float(longitude),
                )
            )

    return clusters


# ============================================================
# CENTROID
# ============================================================


def geographic_centroid(
    coordinates: Iterable[tuple[float, float]],
) -> tuple[float, float]:
    """
    Calculate a simple geographic centroid.

    Coordinates should be supplied as:

        (latitude, longitude)

    Returns:
        Tuple of (latitude, longitude).

    For empty input, returns (0.0, 0.0).
    """
    points = [
        (
            _validate_latitude(latitude),
            _normalize_longitude(longitude),
        )
        for latitude, longitude in coordinates
        if valid_coordinates(
            latitude,
            longitude,
        )
    ]

    if not points:
        return (
            0.0,
            0.0,
        )

    x = 0.0
    y = 0.0
    z = 0.0

    for latitude, longitude in points:
        latitude_rad = math.radians(
            latitude
        )

        longitude_rad = math.radians(
            longitude
        )

        x += (
            math.cos(latitude_rad)
            * math.cos(longitude_rad)
        )

        y += (
            math.cos(latitude_rad)
            * math.sin(longitude_rad)
        )

        z += math.sin(
            latitude_rad
        )

    x /= len(points)
    y /= len(points)
    z /= len(points)

    longitude = math.atan2(
        y,
        x,
    )

    horizontal = math.sqrt(
        x * x
        + y * y
    )

    latitude = math.atan2(
        z,
        horizontal,
    )

    return (
        math.degrees(latitude),
        math.degrees(longitude),
    )


def asset_centroid(
    assets: Iterable[dict[str, Any]],
) -> tuple[float, float]:
    """
    Calculate the geographic centroid of a collection of
    assets.
    """
    coordinates = []

    for asset in assets:
        latitude = asset.get(
            "latitude"
        )

        longitude = asset.get(
            "longitude"
        )

        if (
            latitude is None
            or longitude is None
        ):
            continue

        if valid_coordinates(
            latitude,
            longitude,
        ):
            coordinates.append(
                (
                    latitude,
                    longitude,
                )
            )

    return geographic_centroid(
        coordinates
    )


# ============================================================
# REGIONAL COVERAGE
# ============================================================


def assets_within_region_radius(
    center_latitude: float,
    center_longitude: float,
    assets: Iterable[dict[str, Any]],
    radius_km: float,
) -> list[dict[str, Any]]:
    """
    Return all assets within a specified geographic radius.

    Returned dictionaries include distance_km.
    """
    return find_nearest_assets(
        center_latitude,
        center_longitude,
        assets,
        limit=10_000_000,
        maximum_distance_km=radius_km,
    )


def regional_asset_density(
    asset_count: int,
    area_km2: float,
) -> float:
    """
    Calculate asset density per square kilometer.
    """
    count = max(
        0,
        int(asset_count),
    )

    area = _safe_float(
        area_km2
    )

    if area <= EPSILON:
        return 0.0

    return count / area


# ============================================================
# WEATHER EXPOSURE
# ============================================================


def weather_exposure_score(
    asset_latitude: float,
    asset_longitude: float,
    weather_latitude: float,
    weather_longitude: float,
    influence_radius_km: float = 50.0,
) -> float:
    """
    Estimate how geographically exposed an asset is to a
    weather observation.

    Closer weather observations receive higher scores.

    Returns:
        Value between 0.0 and 1.0.
    """
    distance = haversine_distance_km(
        asset_latitude,
        asset_longitude,
        weather_latitude,
        weather_longitude,
    )

    return proximity_score(
        distance,
        influence_radius_km,
    )


def nearest_weather_station_distance(
    asset_latitude: float,
    asset_longitude: float,
    weather_stations: Iterable[dict[str, Any]],
) -> float:
    """
    Find the distance to the nearest weather station.

    Weather station dictionaries should contain:

        latitude
        longitude

    Returns:
        Distance in kilometers.

    If no valid station exists, returns -1.0.
    """
    minimum_distance = float("inf")

    for station in weather_stations:
        latitude = station.get(
            "latitude"
        )

        longitude = station.get(
            "longitude"
        )

        if (
            latitude is None
            or longitude is None
        ):
            continue

        if not valid_coordinates(
            latitude,
            longitude,
        ):
            continue

        distance = haversine_distance_km(
            asset_latitude,
            asset_longitude,
            latitude,
            longitude,
        )

        minimum_distance = min(
            minimum_distance,
            distance,
        )

    if math.isinf(
        minimum_distance
    ):
        return -1.0

    return minimum_distance


# ============================================================
# INFRASTRUCTURE EXPOSURE
# ============================================================


def geographic_risk_exposure(
    asset_latitude: float,
    asset_longitude: float,
    hazard_latitude: float,
    hazard_longitude: float,
    hazard_radius_km: float,
) -> float:
    """
    Calculate geographic exposure of an asset to a hazard
    centered at another coordinate.

    Returns:
        Value between 0.0 and 1.0.
    """
    radius = max(
        EPSILON,
        _safe_float(
            hazard_radius_km
        ),
    )

    distance = haversine_distance_km(
        asset_latitude,
        asset_longitude,
        hazard_latitude,
        hazard_longitude,
    )

    if distance >= radius:
        return 0.0

    return _clamp(
        1.0
        - (
            distance
            / radius
        )
    )


# ============================================================
# COMPLETE GEOGRAPHIC FEATURES
# ============================================================


def extract_geographic_features(
    asset_latitude: float,
    asset_longitude: float,
    reference_latitude: float | None = None,
    reference_longitude: float | None = None,
    nearby_assets: Iterable[dict[str, Any]] | None = None,
    weather_stations: Iterable[dict[str, Any]] | None = None,
    analysis_radius_km: float = 50.0,
) -> dict[str, float | int | bool]:
    """
    Extract a standardized geographic feature set.

    Args:
        asset_latitude:
            Latitude of the target asset.

        asset_longitude:
            Longitude of the target asset.

        reference_latitude:
            Optional reference point latitude.

        reference_longitude:
            Optional reference point longitude.

        nearby_assets:
            Optional collection of nearby grid assets.

        weather_stations:
            Optional weather station collection.

        analysis_radius_km:
            Radius used for proximity analysis.

    Returns:
        Dictionary of geographic features.
    """
    latitude = _validate_latitude(
        asset_latitude
    )

    longitude = _normalize_longitude(
        asset_longitude
    )

    radius = max(
        EPSILON,
        _safe_float(
            analysis_radius_km,
            50.0,
        ),
    )

    # --------------------------------------------------------
    # Reference-point distance
    # --------------------------------------------------------

    if (
        reference_latitude is not None
        and reference_longitude is not None
    ):
        reference_distance = haversine_distance_km(
            latitude,
            longitude,
            reference_latitude,
            reference_longitude,
        )

        reference_proximity = proximity_score(
            reference_distance,
            radius,
        )

    else:
        reference_distance = 0.0
        reference_proximity = 0.0

    # --------------------------------------------------------
    # Nearby assets
    # --------------------------------------------------------

    if nearby_assets is not None:
        nearby = assets_within_region_radius(
            latitude,
            longitude,
            nearby_assets,
            radius,
        )

        nearby_count = len(
            nearby
        )
    else:
        nearby_count = 0

    # --------------------------------------------------------
    # Weather stations
    # --------------------------------------------------------

    if weather_stations is not None:
        weather_distance = nearest_weather_station_distance(
            latitude,
            longitude,
            weather_stations,
        )

        if weather_distance >= 0.0:
            weather_proximity = proximity_score(
                weather_distance,
                radius,
            )
        else:
            weather_proximity = 0.0

    else:
        weather_distance = -1.0
        weather_proximity = 0.0

    # --------------------------------------------------------
    # Final features
    # --------------------------------------------------------

    return {
        "latitude": latitude,
        "longitude": longitude,
        "reference_distance_km": reference_distance,
        "reference_proximity_score": reference_proximity,
        "nearby_asset_count": nearby_count,
        "analysis_radius_km": radius,
        "nearest_weather_station_distance_km": weather_distance,
        "weather_station_proximity_score": weather_proximity,
        "has_nearby_weather_station": (
            weather_distance >= 0.0
        ),
        "valid_coordinates": valid_coordinates(
            latitude,
            longitude,
        ),
    }


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "valid_coordinates",
    "normalize_coordinates",
    "haversine_distance_km",
    "distance_meters",
    "bearing_degrees",
    "bearing_direction",
    "geographic_midpoint",
    "within_radius",
    "proximity_score",
    "calculate_asset_distance",
    "find_nearest_assets",
    "geographic_cluster",
    "geographic_centroid",
    "asset_centroid",
    "assets_within_region_radius",
    "regional_asset_density",
    "weather_exposure_score",
    "nearest_weather_station_distance",
    "geographic_risk_exposure",
    "extract_geographic_features",
]