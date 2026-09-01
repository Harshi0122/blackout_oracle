"""
Blackout Oracle - Grid Service.

Application-level service for querying and coordinating electrical
grid assets, topology, telemetry, and grid health information.

This service acts as a bridge between API/application code and
the lower-level grid and repository layers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.repositories.asset_repository import AssetRepository
from app.db.repositories.telemetry_repository import TelemetryRepository
from app.grid.criticality import calculate_asset_criticality
from app.grid.geography import calculate_distance_km
from app.grid.graph import GridGraph
from app.grid.topology import GridTopology


class GridService:
    """
    Coordinate grid-related application operations.

    The service intentionally keeps database access behind repository
    classes and keeps topology/graph calculations in the grid layer.
    """

    def __init__(
        self,
        db: Session,
        asset_repository: AssetRepository | None = None,
        telemetry_repository: TelemetryRepository | None = None,
        topology: GridTopology | None = None,
        graph: GridGraph | None = None,
    ) -> None:
        self.db = db

        self.asset_repository = (
            asset_repository
            if asset_repository is not None
            else AssetRepository(db)
        )

        self.telemetry_repository = (
            telemetry_repository
            if telemetry_repository is not None
            else TelemetryRepository(db)
        )

        self.topology = topology
        self.graph = graph

    # ========================================================
    # ASSETS
    # ========================================================

    def get_asset(
        self,
        asset_id: int,
    ) -> Any | None:
        """
        Return a single grid asset by ID.
        """

        return self.asset_repository.get(asset_id)

    def list_assets(
        self,
        *,
        asset_type: str | None = None,
        status: str | None = None,
        region: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Any]:
        """
        Return grid assets matching the supplied filters.

        The repository implementation may expose additional filtering
        capabilities; this method keeps the service interface simple.
        """

        filters: dict[str, Any] = {}

        if asset_type is not None:
            filters["asset_type"] = asset_type

        if status is not None:
            filters["status"] = status

        if region is not None:
            filters["region"] = region

        try:
            return self.asset_repository.list(
                filters=filters,
                limit=limit,
                offset=offset,
            )
        except TypeError:
            try:
                return self.asset_repository.list(
                    limit=limit,
                    offset=offset,
                    **filters,
                )
            except TypeError:
                assets = self.asset_repository.list()

                if asset_type is not None:
                    assets = [
                        asset
                        for asset in assets
                        if str(
                            getattr(asset, "asset_type", "")
                        ).lower()
                        == asset_type.lower()
                    ]

                if status is not None:
                    assets = [
                        asset
                        for asset in assets
                        if str(
                            getattr(asset, "status", "")
                        ).lower()
                        == status.lower()
                    ]

                if region is not None:
                    assets = [
                        asset
                        for asset in assets
                        if str(
                            getattr(asset, "region", "")
                        ).lower()
                        == region.lower()
                    ]

                return assets[offset : offset + limit]

    # ========================================================
    # TELEMETRY
    # ========================================================

    def get_latest_telemetry(
        self,
        asset_id: int,
        telemetry_type: str | None = None,
    ) -> Any | None:
        """
        Return the most recent telemetry observation for an asset.
        """

        try:
            if telemetry_type is not None:
                return self.telemetry_repository.get_latest(
                    asset_id=asset_id,
                    telemetry_type=telemetry_type,
                )

            return self.telemetry_repository.get_latest(
                asset_id=asset_id,
            )

        except TypeError:
            try:
                records = self.telemetry_repository.list(
                    asset_id=asset_id,
                    limit=1,
                )
            except TypeError:
                records = self.telemetry_repository.list(
                    asset_id=asset_id,
                )

            if not records:
                return None

            if telemetry_type is not None:
                records = [
                    record
                    for record in records
                    if str(
                        getattr(
                            record,
                            "telemetry_type",
                            "",
                        )
                    ).lower()
                    == telemetry_type.lower()
                ]

            if not records:
                return None

            return max(
                records,
                key=lambda item: getattr(
                    item,
                    "timestamp",
                    datetime.min,
                ),
            )

    def get_telemetry_history(
        self,
        asset_id: int,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        telemetry_type: str | None = None,
        limit: int = 1000,
    ) -> list[Any]:
        """
        Return telemetry history for an asset.
        """

        filters: dict[str, Any] = {
            "asset_id": asset_id,
        }

        if start_time is not None:
            filters["start_time"] = start_time

        if end_time is not None:
            filters["end_time"] = end_time

        if telemetry_type is not None:
            filters["telemetry_type"] = telemetry_type

        try:
            return self.telemetry_repository.list(
                filters=filters,
                limit=limit,
                offset=0,
            )
        except TypeError:
            try:
                return self.telemetry_repository.list(
                    limit=limit,
                    offset=0,
                    **filters,
                )
            except TypeError:
                return self.telemetry_repository.list(
                    asset_id=asset_id,
                    limit=limit,
                )

    # ========================================================
    # ASSET HEALTH
    # ========================================================

    def get_asset_health(
        self,
        asset_id: int,
    ) -> dict[str, Any]:
        """
        Calculate a lightweight current health assessment.

        The method uses the asset's stored health information when
        available and supplements it with the latest telemetry.
        """

        asset = self.get_asset(asset_id)

        if asset is None:
            raise ValueError(
                f"Grid asset {asset_id} was not found."
            )

        health_score = getattr(
            asset,
            "health_score",
            None,
        )

        health_status = getattr(
            asset,
            "health_status",
            None,
        )

        telemetry = self.get_latest_telemetry(asset_id)

        telemetry_value = None

        if telemetry is not None:
            telemetry_value = getattr(
                telemetry,
                "value",
                None,
            )

        if health_score is None:
            health_score = 100.0

            if telemetry is not None:
                quality_score = getattr(
                    telemetry,
                    "quality_score",
                    None,
                )

                if quality_score is not None:
                    health_score = max(
                        0.0,
                        min(
                            100.0,
                            float(quality_score) * 100.0,
                        ),
                    )

        return {
            "asset_id": asset_id,
            "health_score": float(health_score),
            "health_status": (
                str(health_status)
                if health_status is not None
                else "unknown"
            ),
            "latest_telemetry": telemetry_value,
            "telemetry_timestamp": (
                getattr(
                    telemetry,
                    "timestamp",
                    None,
                )
                if telemetry is not None
                else None
            ),
        }

    # ========================================================
    # CRITICALITY
    # ========================================================

    def calculate_criticality(
        self,
        asset_id: int,
        *,
        load_mw: float = 0.0,
        connected_assets: int = 0,
        customers_affected: int = 0,
        redundancy: float = 1.0,
    ) -> float:
        """
        Calculate the operational criticality of an asset.

        Returns a normalized score from 0 to 100.
        """

        asset = self.get_asset(asset_id)

        if asset is None:
            raise ValueError(
                f"Grid asset {asset_id} was not found."
            )

        try:
            return float(
                calculate_asset_criticality(
                    asset=asset,
                    load_mw=load_mw,
                    connected_assets=connected_assets,
                    customers_affected=customers_affected,
                    redundancy=redundancy,
                )
            )
        except TypeError:
            try:
                return float(
                    calculate_asset_criticality(
                        asset,
                        load_mw,
                        connected_assets,
                        customers_affected,
                        redundancy,
                    )
                )
            except TypeError:
                return self._fallback_criticality(
                    asset,
                    load_mw=load_mw,
                    connected_assets=connected_assets,
                    customers_affected=customers_affected,
                    redundancy=redundancy,
                )

    @staticmethod
    def _fallback_criticality(
        asset: Any,
        *,
        load_mw: float,
        connected_assets: int,
        customers_affected: int,
        redundancy: float,
    ) -> float:
        """
        Deterministic fallback criticality calculation.

        This keeps the service functional even if the lower-level
        criticality helper has a different interface.
        """

        asset_type = str(
            getattr(
                asset,
                "asset_type",
                "",
            )
        ).lower()

        type_weight = {
            "substation": 30.0,
            "transformer": 25.0,
            "transmission_line": 25.0,
            "generator": 30.0,
            "bus": 20.0,
        }.get(
            asset_type,
            15.0,
        )

        load_component = min(
            25.0,
            max(
                0.0,
                float(load_mw),
            )
            / 10.0,
        )

        connectivity_component = min(
            20.0,
            max(
                0,
                connected_assets,
            )
            * 2.0,
        )

        customer_component = min(
            20.0,
            max(
                0,
                customers_affected,
            )
            / 5000.0,
        )

        redundancy_factor = max(
            0.0,
            min(
                1.0,
                float(redundancy),
            ),
        )

        redundancy_penalty = (
            1.0 - redundancy_factor
        ) * 10.0

        score = (
            type_weight
            + load_component
            + connectivity_component
            + customer_component
            + redundancy_penalty
        )

        return max(
            0.0,
            min(
                100.0,
                score,
            ),
        )

    # ========================================================
    # GEOGRAPHY
    # ========================================================

    @staticmethod
    def distance_between_assets(
        asset_a: Any,
        asset_b: Any,
    ) -> float:
        """
        Calculate geographical distance between two assets.

        Returns distance in kilometres.
        """

        lat_a = getattr(
            asset_a,
            "latitude",
            None,
        )
        lon_a = getattr(
            asset_a,
            "longitude",
            None,
        )

        lat_b = getattr(
            asset_b,
            "latitude",
            None,
        )
        lon_b = getattr(
            asset_b,
            "longitude",
            None,
        )

        if None in (
            lat_a,
            lon_a,
            lat_b,
            lon_b,
        ):
            raise ValueError(
                "Both assets must have latitude and longitude."
            )

        try:
            return float(
                calculate_distance_km(
                    lat_a,
                    lon_a,
                    lat_b,
                    lon_b,
                )
            )
        except TypeError:
            try:
                return float(
                    calculate_distance_km(
                        (lat_a, lon_a),
                        (lat_b, lon_b),
                    )
                )
            except TypeError:
                return GridService._haversine_distance(
                    float(lat_a),
                    float(lon_a),
                    float(lat_b),
                    float(lon_b),
                )

    @staticmethod
    def _haversine_distance(
        latitude_a: float,
        longitude_a: float,
        latitude_b: float,
        longitude_b: float,
    ) -> float:
        """
        Calculate great-circle distance using the Haversine formula.
        """

        from math import (
            asin,
            cos,
            radians,
            sin,
            sqrt,
        )

        earth_radius_km = 6371.0088

        lat1 = radians(latitude_a)
        lat2 = radians(latitude_b)

        delta_lat = radians(
            latitude_b - latitude_a
        )

        delta_lon = radians(
            longitude_b - longitude_a
        )

        value = (
            sin(delta_lat / 2) ** 2
            + cos(lat1)
            * cos(lat2)
            * sin(delta_lon / 2) ** 2
        )

        value = max(
            0.0,
            min(
                1.0,
                value,
            ),
        )

        return (
            2.0
            * earth_radius_km
            * asin(sqrt(value))
        )

    # ========================================================
    # TOPOLOGY
    # ========================================================

    def get_topology(self) -> GridTopology | None:
        """
        Return the configured grid topology object.
        """

        return self.topology

    def get_graph(self) -> GridGraph | None:
        """
        Return the configured grid graph object.
        """

        return self.graph

    def set_topology(
        self,
        topology: GridTopology,
    ) -> None:
        """
        Replace the active grid topology.
        """

        self.topology = topology

    def set_graph(
        self,
        graph: GridGraph,
    ) -> None:
        """
        Replace the active grid graph.
        """

        self.graph = graph

    # ========================================================
    # GRID SUMMARY
    # ========================================================

    def get_grid_summary(self) -> dict[str, Any]:
        """
        Return a high-level summary of the current grid state.
        """

        assets = self.list_assets(
            limit=10000,
            offset=0,
        )

        summary: dict[str, Any] = {
            "total_assets": len(assets),
            "active_assets": 0,
            "fault_assets": 0,
            "maintenance_assets": 0,
            "unknown_assets": 0,
            "asset_types": {},
        }

        for asset in assets:
            status = str(
                getattr(
                    asset,
                    "status",
                    "unknown",
                )
            ).lower()

            asset_type = str(
                getattr(
                    asset,
                    "asset_type",
                    "unknown",
                )
            ).lower()

            if status == "active":
                summary["active_assets"] += 1
            elif status == "fault":
                summary["fault_assets"] += 1
            elif status == "maintenance":
                summary["maintenance_assets"] += 1
            else:
                summary["unknown_assets"] += 1

            summary["asset_types"][asset_type] = (
                summary["asset_types"].get(
                    asset_type,
                    0,
                )
                + 1
            )

        return summary

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_asset(
        self,
        asset: Any,
    ) -> list[str]:
        """
        Return validation problems for a grid asset.

        An empty list means no obvious structural problems were
        detected by this service.
        """

        errors: list[str] = []

        asset_id = getattr(
            asset,
            "id",
            None,
        )

        if asset_id is None:
            errors.append(
                "Asset is missing an ID."
            )

        latitude = getattr(
            asset,
            "latitude",
            None,
        )

        longitude = getattr(
            asset,
            "longitude",
            None,
        )

        if latitude is not None and not (
            -90.0 <= float(latitude) <= 90.0
        ):
            errors.append(
                "Latitude is outside the valid range."
            )

        if longitude is not None and not (
            -180.0 <= float(longitude) <= 180.0
        ):
            errors.append(
                "Longitude is outside the valid range."
            )

        voltage = getattr(
            asset,
            "voltage_level_kv",
            None,
        )

        if voltage is not None and float(voltage) <= 0:
            errors.append(
                "Voltage level must be greater than zero."
            )

        capacity = getattr(
            asset,
            "capacity_mva",
            None,
        )

        if capacity is not None and float(capacity) <= 0:
            errors.append(
                "Capacity must be greater than zero."
            )

        return errors


__all__ = [
    "GridService",
]