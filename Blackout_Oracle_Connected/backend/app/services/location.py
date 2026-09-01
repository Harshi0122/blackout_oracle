"""
Blackout Oracle - Location Service.

Application-level service for geographic operations involving grid
assets, substations, regions, and weather locations.

The service provides coordinate validation, distance calculations,
nearest-asset lookup, bounding-box queries, and location summaries.
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Any, Iterable


class LocationService:
    """
    Service for geographic and location-related grid operations.
    """

    EARTH_RADIUS_KM = 6371.0088

    # ========================================================
    # COORDINATE VALIDATION
    # ========================================================

    @classmethod
    def validate_coordinates(
        cls,
        latitude: float,
        longitude: float,
    ) -> bool:
        """
        Return True when latitude and longitude are valid.
        """

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            return False

        return (
            -90.0 <= latitude <= 90.0
            and -180.0 <= longitude <= 180.0
        )

    @classmethod
    def require_valid_coordinates(
        cls,
        latitude: float,
        longitude: float,
    ) -> tuple[float, float]:
        """
        Validate coordinates and return normalized floats.

        Raises:
            ValueError: If coordinates are invalid.
        """

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Latitude and longitude must be numeric."
            ) from exc

        if not cls.validate_coordinates(
            latitude,
            longitude,
        ):
            raise ValueError(
                "Invalid coordinates. Latitude must be "
                "between -90 and 90 and longitude must be "
                "between -180 and 180."
            )

        return latitude, longitude

    # ========================================================
    # DISTANCE
    # ========================================================

    @classmethod
    def distance_km(
        cls,
        latitude_a: float,
        longitude_a: float,
        latitude_b: float,
        longitude_b: float,
    ) -> float:
        """
        Calculate great-circle distance between two coordinates.

        Returns:
            Distance in kilometres.
        """

        latitude_a, longitude_a = cls.require_valid_coordinates(
            latitude_a,
            longitude_a,
        )

        latitude_b, longitude_b = cls.require_valid_coordinates(
            latitude_b,
            longitude_b,
        )

        lat1 = radians(latitude_a)
        lat2 = radians(latitude_b)

        delta_lat = radians(
            latitude_b - latitude_a
        )

        delta_lon = radians(
            longitude_b - longitude_a
        )

        haversine = (
            sin(delta_lat / 2.0) ** 2
            + cos(lat1)
            * cos(lat2)
            * sin(delta_lon / 2.0) ** 2
        )

        haversine = max(
            0.0,
            min(
                1.0,
                haversine,
            ),
        )

        return (
            2.0
            * cls.EARTH_RADIUS_KM
            * asin(sqrt(haversine))
        )

    @classmethod
    def distance_meters(
        cls,
        latitude_a: float,
        longitude_a: float,
        latitude_b: float,
        longitude_b: float,
    ) -> float:
        """
        Calculate distance between two coordinates in metres.
        """

        return cls.distance_km(
            latitude_a,
            longitude_a,
            latitude_b,
            longitude_b,
        ) * 1000.0

    # ========================================================
    # ASSET COORDINATES
    # ========================================================

    @staticmethod
    def get_coordinates(
        obj: Any,
    ) -> tuple[float, float] | None:
        """
        Extract latitude and longitude from an object.

        Supports objects with attributes as well as dictionaries.
        """

        if isinstance(obj, dict):
            latitude = obj.get("latitude")
            longitude = obj.get("longitude")
        else:
            latitude = getattr(
                obj,
                "latitude",
                None,
            )

            longitude = getattr(
                obj,
                "longitude",
                None,
            )

        if latitude is None or longitude is None:
            return None

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            return None

        if not LocationService.validate_coordinates(
            latitude,
            longitude,
        ):
            return None

        return latitude, longitude

    # ========================================================
    # DISTANCE BETWEEN OBJECTS
    # ========================================================

    @classmethod
    def distance_between(
        cls,
        object_a: Any,
        object_b: Any,
    ) -> float:
        """
        Calculate distance between two location-aware objects.

        Returns:
            Distance in kilometres.

        Raises:
            ValueError: If either object has no valid coordinates.
        """

        coordinates_a = cls.get_coordinates(object_a)
        coordinates_b = cls.get_coordinates(object_b)

        if coordinates_a is None:
            raise ValueError(
                "First object does not contain valid coordinates."
            )

        if coordinates_b is None:
            raise ValueError(
                "Second object does not contain valid coordinates."
            )

        return cls.distance_km(
            coordinates_a[0],
            coordinates_a[1],
            coordinates_b[0],
            coordinates_b[1],
        )

    # ========================================================
    # BOUNDING BOX
    # ========================================================

    @classmethod
    def bounding_box(
        cls,
        latitude: float,
        longitude: float,
        radius_km: float,
    ) -> dict[str, float]:
        """
        Calculate an approximate geographic bounding box around
        a coordinate.

        The box is useful for efficiently pre-filtering assets
        before performing exact Haversine distance calculations.
        """

        latitude, longitude = cls.require_valid_coordinates(
            latitude,
            longitude,
        )

        radius_km = float(radius_km)

        if radius_km < 0:
            raise ValueError(
                "Radius must be greater than or equal to zero."
            )

        latitude_delta = radius_km / 111.32

        longitude_scale = max(
            cos(radians(latitude)),
            1e-12,
        )

        longitude_delta = (
            radius_km
            / (
                111.32
                * longitude_scale
            )
        )

        min_latitude = max(
            -90.0,
            latitude - latitude_delta,
        )

        max_latitude = min(
            90.0,
            latitude + latitude_delta,
        )

        min_longitude = max(
            -180.0,
            longitude - longitude_delta,
        )

        max_longitude = min(
            180.0,
            longitude + longitude_delta,
        )

        return {
            "min_latitude": min_latitude,
            "max_latitude": max_latitude,
            "min_longitude": min_longitude,
            "max_longitude": max_longitude,
        }

    @classmethod
    def within_radius(
        cls,
        obj: Any,
        latitude: float,
        longitude: float,
        radius_km: float,
    ) -> bool:
        """
        Determine whether an object lies within a radius of a point.
        """

        coordinates = cls.get_coordinates(obj)

        if coordinates is None:
            return False

        distance = cls.distance_km(
            latitude,
            longitude,
            coordinates[0],
            coordinates[1],
        )

        return distance <= float(radius_km)

    # ========================================================
    # NEAREST OBJECT
    # ========================================================

    @classmethod
    def nearest(
        cls,
        objects: Iterable[Any],
        latitude: float,
        longitude: float,
        *,
        max_distance_km: float | None = None,
    ) -> tuple[Any, float] | None:
        """
        Find the nearest location-aware object.

        Returns:
            A tuple of (object, distance_km), or None when no valid
            object is available.
        """

        latitude, longitude = cls.require_valid_coordinates(
            latitude,
            longitude,
        )

        if (
            max_distance_km is not None
            and float(max_distance_km) < 0
        ):
            raise ValueError(
                "max_distance_km must be non-negative."
            )

        nearest_object: Any | None = None
        nearest_distance: float | None = None

        for obj in objects:
            coordinates = cls.get_coordinates(obj)

            if coordinates is None:
                continue

            distance = cls.distance_km(
                latitude,
                longitude,
                coordinates[0],
                coordinates[1],
            )

            if (
                max_distance_km is not None
                and distance > float(max_distance_km)
            ):
                continue

            if (
                nearest_distance is None
                or distance < nearest_distance
            ):
                nearest_object = obj
                nearest_distance = distance

        if nearest_object is None:
            return None

        return nearest_object, float(nearest_distance)

    # ========================================================
    # OBJECTS WITHIN RADIUS
    # ========================================================

    @classmethod
    def objects_within_radius(
        cls,
        objects: Iterable[Any],
        latitude: float,
        longitude: float,
        radius_km: float,
    ) -> list[tuple[Any, float]]:
        """
        Return all objects within a specified radius.

        Results are sorted by distance from nearest to farthest.
        """

        latitude, longitude = cls.require_valid_coordinates(
            latitude,
            longitude,
        )

        radius_km = float(radius_km)

        if radius_km < 0:
            raise ValueError(
                "radius_km must be non-negative."
            )

        results: list[tuple[Any, float]] = []

        for obj in objects:
            coordinates = cls.get_coordinates(obj)

            if coordinates is None:
                continue

            distance = cls.distance_km(
                latitude,
                longitude,
                coordinates[0],
                coordinates[1],
            )

            if distance <= radius_km:
                results.append(
                    (
                        obj,
                        distance,
                    )
                )

        results.sort(
            key=lambda item: item[1]
        )

        return results

    # ========================================================
    # REGION FILTERING
    # ========================================================

    @staticmethod
    def _get_value(
        obj: Any,
        field: str,
    ) -> Any:
        """
        Read a field from either a dictionary or an object.
        """

        if isinstance(obj, dict):
            return obj.get(field)

        return getattr(
            obj,
            field,
            None,
        )

    @classmethod
    def filter_by_region(
        cls,
        objects: Iterable[Any],
        region: str,
    ) -> list[Any]:
        """
        Filter objects by region name.
        """

        if not region:
            return list(objects)

        target = region.strip().casefold()

        return [
            obj
            for obj in objects
            if str(
                cls._get_value(
                    obj,
                    "region",
                )
                or ""
            ).strip().casefold()
            == target
        ]

    @classmethod
    def filter_by_state(
        cls,
        objects: Iterable[Any],
        state: str,
    ) -> list[Any]:
        """
        Filter objects by state.
        """

        if not state:
            return list(objects)

        target = state.strip().casefold()

        return [
            obj
            for obj in objects
            if str(
                cls._get_value(
                    obj,
                    "state",
                )
                or ""
            ).strip().casefold()
            == target
        ]

    @classmethod
    def filter_by_district(
        cls,
        objects: Iterable[Any],
        district: str,
    ) -> list[Any]:
        """
        Filter objects by district.
        """

        if not district:
            return list(objects)

        target = district.strip().casefold()

        return [
            obj
            for obj in objects
            if str(
                cls._get_value(
                    obj,
                    "district",
                )
                or ""
            ).strip().casefold()
            == target
        ]

    # ========================================================
    # GEOLOCATION SUMMARY
    # ========================================================

    @classmethod
    def summarize_location(
        cls,
        obj: Any,
    ) -> dict[str, Any]:
        """
        Return a normalized geographic summary for an object.
        """

        coordinates = cls.get_coordinates(obj)

        summary: dict[str, Any] = {
            "latitude": None,
            "longitude": None,
            "region": cls._get_value(
                obj,
                "region",
            ),
            "state": cls._get_value(
                obj,
                "state",
            ),
            "district": cls._get_value(
                obj,
                "district",
            ),
            "city": cls._get_value(
                obj,
                "city",
            ),
        }

        if coordinates is not None:
            summary["latitude"] = coordinates[0]
            summary["longitude"] = coordinates[1]

        return summary

    # ========================================================
    # CLUSTER CENTROID
    # ========================================================

    @classmethod
    def centroid(
        cls,
        objects: Iterable[Any],
    ) -> tuple[float, float] | None:
        """
        Calculate the arithmetic geographic centroid of objects.

        Returns:
            (latitude, longitude), or None if no valid coordinates
            are available.
        """

        coordinates = [
            cls.get_coordinates(obj)
            for obj in objects
        ]

        valid = [
            coordinate
            for coordinate in coordinates
            if coordinate is not None
        ]

        if not valid:
            return None

        latitude = sum(
            coordinate[0]
            for coordinate in valid
        ) / len(valid)

        longitude = sum(
            coordinate[1]
            for coordinate in valid
        ) / len(valid)

        return latitude, longitude

    # ========================================================
    # GRID LOCATION LOOKUP
    # ========================================================

    @classmethod
    def locate_asset(
        cls,
        objects: Iterable[Any],
        *,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Find nearby grid assets and return normalized location
        information together with their distances.
        """

        if limit < 1:
            raise ValueError(
                "limit must be at least 1."
            )

        nearby = cls.objects_within_radius(
            objects,
            latitude,
            longitude,
            radius_km,
        )

        results: list[dict[str, Any]] = []

        for obj, distance in nearby[:limit]:
            asset_id = cls._get_value(
                obj,
                "id",
            )

            asset_type = cls._get_value(
                obj,
                "asset_type",
            )

            results.append(
                {
                    "asset_id": asset_id,
                    "asset_type": asset_type,
                    "distance_km": round(
                        distance,
                        6,
                    ),
                    "latitude": cls.get_coordinates(
                        obj
                    )[0],
                    "longitude": cls.get_coordinates(
                        obj
                    )[1],
                    "region": cls._get_value(
                        obj,
                        "region",
                    ),
                    "state": cls._get_value(
                        obj,
                        "state",
                    ),
                    "district": cls._get_value(
                        obj,
                        "district",
                    ),
                }
            )

        return results


__all__ = [
    "LocationService",
]