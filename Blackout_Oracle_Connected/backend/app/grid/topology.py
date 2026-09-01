"""
Blackout Oracle - Grid Topology Utilities.

Provides deterministic topology-level operations for the
electrical grid.

This module handles:

- Topology construction
- Asset-to-node relationships
- Network connectivity
- Substation / bus / feeder relationships
- Island detection
- Topology validation
- Connectivity analysis
- Topology summaries

This module is analytical only. It does not send commands
to physical grid equipment.
"""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any


# ============================================================
# CONSTANTS
# ============================================================

VALID_ASSET_TYPES = {
    "bus",
    "substation",
    "feeder",
    "generator",
    "load",
    "transformer",
    "transmission_line",
    "switch",
    "unknown",
}


# ============================================================
# DATA STRUCTURES
# ============================================================


@dataclass
class TopologyAsset:
    """
    Represents a grid asset in the topology model.
    """

    asset_id: str
    asset_type: str = "unknown"
    name: str | None = None
    node_id: str | None = None
    parent_id: str | None = None
    region_id: str | None = None
    status: str = "unknown"
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class TopologyConnection:
    """
    Represents a topology connection between two grid assets.
    """

    connection_id: str
    source_id: str
    target_id: str
    connection_type: str = "unknown"
    status: str = "active"
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# TOPOLOGY MODEL
# ============================================================


class GridTopology:
    """
    In-memory representation of electrical-grid topology.

    The topology model stores assets and their connections
    independently from the database layer.

    This allows the risk engine and simulation engine to work
    with a deterministic snapshot of the grid.
    """

    def __init__(
        self,
        assets: Iterable[TopologyAsset] | None = None,
        connections: Iterable[TopologyConnection] | None = None,
    ) -> None:
        """
        Initialize a topology model.
        """
        self.assets: dict[str, TopologyAsset] = {}

        self.connections: dict[
            str,
            TopologyConnection,
        ] = {}

        self.adjacency: dict[
            str,
            set[str],
        ] = defaultdict(set)

        if assets is not None:
            for asset in assets:
                self.add_asset(asset)

        if connections is not None:
            for connection in connections:
                self.add_connection(connection)

    # ========================================================
    # ASSET OPERATIONS
    # ========================================================

    def add_asset(
        self,
        asset: TopologyAsset,
    ) -> None:
        """
        Add or replace a topology asset.
        """
        asset_id = str(
            asset.asset_id
        )

        asset.asset_id = asset_id

        if not asset.asset_type:
            asset.asset_type = "unknown"

        asset.asset_type = (
            str(asset.asset_type)
            .lower()
        )

        self.assets[asset_id] = asset

        self.adjacency.setdefault(
            asset_id,
            set(),
        )

    def add_asset_data(
        self,
        asset_id: Any,
        asset_type: str = "unknown",
        name: str | None = None,
        node_id: str | None = None,
        parent_id: str | None = None,
        region_id: str | None = None,
        status: str = "unknown",
        metadata: dict[str, Any] | None = None,
    ) -> TopologyAsset:
        """
        Convenience method for creating and adding an asset.
        """
        asset = TopologyAsset(
            asset_id=str(asset_id),
            asset_type=asset_type,
            name=name,
            node_id=node_id,
            parent_id=parent_id,
            region_id=region_id,
            status=status,
            metadata=dict(
                metadata or {}
            ),
        )

        self.add_asset(asset)

        return asset

    def remove_asset(
        self,
        asset_id: Any,
    ) -> bool:
        """
        Remove an asset and all connections involving it.

        Returns:
            True if the asset existed.
        """
        normalized = str(
            asset_id
        )

        if normalized not in self.assets:
            return False

        connection_ids = [
            connection_id
            for connection_id, connection
            in self.connections.items()
            if (
                connection.source_id
                == normalized
                or connection.target_id
                == normalized
            )
        ]

        for connection_id in connection_ids:
            self.remove_connection(
                connection_id
            )

        self.assets.pop(
            normalized,
            None,
        )

        self.adjacency.pop(
            normalized,
            None,
        )

        for neighbors in self.adjacency.values():
            neighbors.discard(
                normalized
            )

        return True

    def has_asset(
        self,
        asset_id: Any,
    ) -> bool:
        """
        Check whether an asset exists.
        """
        return str(
            asset_id
        ) in self.assets

    def get_asset(
        self,
        asset_id: Any,
    ) -> TopologyAsset | None:
        """
        Retrieve an asset.
        """
        return self.assets.get(
            str(asset_id)
        )

    def assets_by_type(
        self,
        asset_type: str,
    ) -> list[TopologyAsset]:
        """
        Return all assets of a specific type.
        """
        requested_type = (
            str(asset_type)
            .lower()
        )

        return [
            asset
            for asset in self.assets.values()
            if asset.asset_type
            == requested_type
        ]

    def assets_by_region(
        self,
        region_id: Any,
    ) -> list[TopologyAsset]:
        """
        Return all assets belonging to a region.
        """
        region = str(
            region_id
        )

        return [
            asset
            for asset in self.assets.values()
            if asset.region_id
            == region
        ]

    def assets_by_status(
        self,
        status: str,
    ) -> list[TopologyAsset]:
        """
        Return all assets with a specified operational status.
        """
        requested_status = (
            str(status)
            .lower()
        )

        return [
            asset
            for asset in self.assets.values()
            if str(
                asset.status
            ).lower()
            == requested_status
        ]

    # ========================================================
    # CONNECTION OPERATIONS
    # ========================================================

    def add_connection(
        self,
        connection: TopologyConnection,
    ) -> None:
        """
        Add a topology connection.

        Missing endpoint assets are automatically created as
        generic assets.
        """
        connection_id = str(
            connection.connection_id
        )

        source_id = str(
            connection.source_id
        )

        target_id = str(
            connection.target_id
        )

        connection.connection_id = (
            connection_id
        )

        connection.source_id = source_id
        connection.target_id = target_id

        if source_id not in self.assets:
            self.add_asset_data(
                source_id
            )

        if target_id not in self.assets:
            self.add_asset_data(
                target_id
            )

        self.connections[
            connection_id
        ] = connection

        self.adjacency[
            source_id
        ].add(
            target_id
        )

        self.adjacency[
            target_id
        ].add(
            source_id
        )

    def add_connection_data(
        self,
        connection_id: Any,
        source_id: Any,
        target_id: Any,
        connection_type: str = "unknown",
        status: str = "active",
        metadata: dict[str, Any] | None = None,
    ) -> TopologyConnection:
        """
        Convenience method for creating and adding a connection.
        """
        connection = TopologyConnection(
            connection_id=str(
                connection_id
            ),
            source_id=str(
                source_id
            ),
            target_id=str(
                target_id
            ),
            connection_type=connection_type,
            status=status,
            metadata=dict(
                metadata or {}
            ),
        )

        self.add_connection(
            connection
        )

        return connection

    def remove_connection(
        self,
        connection_id: Any,
    ) -> bool:
        """
        Remove a topology connection.
        """
        normalized = str(
            connection_id
        )

        connection = self.connections.pop(
            normalized,
            None,
        )

        if connection is None:
            return False

        self.adjacency[
            connection.source_id
        ].discard(
            connection.target_id
        )

        self.adjacency[
            connection.target_id
        ].discard(
            connection.source_id
        )

        return True

    def has_connection(
        self,
        connection_id: Any,
    ) -> bool:
        """
        Check whether a connection exists.
        """
        return str(
            connection_id
        ) in self.connections

    def get_connection(
        self,
        connection_id: Any,
    ) -> TopologyConnection | None:
        """
        Retrieve a connection.
        """
        return self.connections.get(
            str(connection_id)
        )

    def connections_for_asset(
        self,
        asset_id: Any,
    ) -> list[TopologyConnection]:
        """
        Return all connections involving an asset.
        """
        normalized = str(
            asset_id
        )

        return [
            connection
            for connection in self.connections.values()
            if (
                connection.source_id
                == normalized
                or connection.target_id
                == normalized
            )
        ]

    # ========================================================
    # BASIC COUNTS
    # ========================================================

    def asset_count(self) -> int:
        """
        Return the number of topology assets.
        """
        return len(
            self.assets
        )

    def connection_count(
        self,
    ) -> int:
        """
        Return the number of topology connections.
        """
        return len(
            self.connections
        )

    # ========================================================
    # NEIGHBOR ANALYSIS
    # ========================================================

    def neighbors(
        self,
        asset_id: Any,
    ) -> set[str]:
        """
        Return neighboring asset IDs.

        A copy is returned to prevent accidental modification
        of the topology.
        """
        return set(
            self.adjacency.get(
                str(asset_id),
                set(),
            )
        )

    def degree(
        self,
        asset_id: Any,
    ) -> int:
        """
        Return the topology degree of an asset.
        """
        return len(
            self.neighbors(
                asset_id
            )
        )

    def connected_asset_count(
        self,
        asset_id: Any,
    ) -> int:
        """
        Return the number of assets directly connected to
        an asset.
        """
        return self.degree(
            asset_id
        )

    # ========================================================
    # TRAVERSAL
    # ========================================================

    def reachable_assets(
        self,
        start_asset_id: Any,
        active_only: bool = True,
    ) -> set[str]:
        """
        Find all assets reachable from a starting asset.

        Args:
            start_asset_id:
                Starting asset identifier.

            active_only:
                When True, inactive connections are ignored.
        """
        start = str(
            start_asset_id
        )

        if start not in self.assets:
            return set()

        visited: set[str] = {
            start
        }

        queue: deque[str] = deque(
            [start]
        )

        while queue:
            current = queue.popleft()

            for neighbor in self.adjacency.get(
                current,
                set(),
            ):
                if neighbor in visited:
                    continue

                if active_only:
                    connection = self.connection_between(
                        current,
                        neighbor,
                    )

                    if (
                        connection is not None
                        and str(
                            connection.status
                        ).lower()
                        not in {
                            "active",
                            "online",
                            "closed",
                            "energized",
                        }
                    ):
                        continue

                visited.add(
                    neighbor
                )

                queue.append(
                    neighbor
                )

        return visited

    # ========================================================
    # CONNECTIVITY
    # ========================================================

    def is_connected(
        self,
        active_only: bool = True,
    ) -> bool:
        """
        Determine whether the complete topology is connected.

        Empty topology is considered disconnected.
        """
        if not self.assets:
            return False

        start = next(
            iter(self.assets)
        )

        reachable = self.reachable_assets(
            start,
            active_only=active_only,
        )

        return len(
            reachable
        ) == len(
            self.assets
        )

    def connected_components(
        self,
        active_only: bool = True,
    ) -> list[set[str]]:
        """
        Find connected topology islands.
        """
        remaining = set(
            self.assets.keys()
        )

        components: list[set[str]] = []

        while remaining:
            start = next(
                iter(remaining)
            )

            component = self.reachable_assets(
                start,
                active_only=active_only,
            )

            components.append(
                component
            )

            remaining -= component

        return components

    def component_count(
        self,
        active_only: bool = True,
    ) -> int:
        """
        Return the number of topology islands.
        """
        return len(
            self.connected_components(
                active_only=active_only
            )
        )

    def largest_component_ratio(
        self,
        active_only: bool = True,
    ) -> float:
        """
        Return the fraction of assets in the largest
        connected component.
        """
        total = self.asset_count()

        if total == 0:
            return 0.0

        components = self.connected_components(
            active_only=active_only
        )

        largest = max(
            (
                len(component)
                for component in components
            ),
            default=0,
        )

        return (
            largest / total
        )

    # ========================================================
    # PATH ANALYSIS
    # ========================================================

    def shortest_path(
        self,
        source_id: Any,
        target_id: Any,
        active_only: bool = True,
    ) -> list[str] | None:
        """
        Find a shortest topology path between two assets.
        """
        source = str(
            source_id
        )

        target = str(
            target_id
        )

        if (
            source not in self.assets
            or target not in self.assets
        ):
            return None

        if source == target:
            return [source]

        queue: deque[str] = deque(
            [source]
        )

        parent: dict[
            str,
            str | None,
        ] = {
            source: None
        }

        while queue:
            current = queue.popleft()

            for neighbor in self.adjacency.get(
                current,
                set(),
            ):
                if neighbor in parent:
                    continue

                if active_only:
                    connection = self.connection_between(
                        current,
                        neighbor,
                    )

                    if (
                        connection is not None
                        and str(
                            connection.status
                        ).lower()
                        not in {
                            "active",
                            "online",
                            "closed",
                            "energized",
                        }
                    ):
                        continue

                parent[neighbor] = current

                if neighbor == target:
                    path: list[str] = []

                    cursor: str | None = target

                    while cursor is not None:
                        path.append(
                            cursor
                        )

                        cursor = parent[
                            cursor
                        ]

                    path.reverse()

                    return path

                queue.append(
                    neighbor
                )

        return None

    def shortest_path_length(
        self,
        source_id: Any,
        target_id: Any,
        active_only: bool = True,
    ) -> int | None:
        """
        Return the number of topology connections in the
        shortest path.
        """
        path = self.shortest_path(
            source_id,
            target_id,
            active_only=active_only,
        )

        if path is None:
            return None

        return max(
            0,
            len(path) - 1,
        )

    # ========================================================
    # CONNECTION LOOKUP
    # ========================================================

    def connection_between(
        self,
        source_id: Any,
        target_id: Any,
    ) -> TopologyConnection | None:
        """
        Find a connection between two assets.
        """
        source = str(
            source_id
        )

        target = str(
            target_id
        )

        for connection in self.connections.values():
            if (
                (
                    connection.source_id
                    == source
                    and connection.target_id
                    == target
                )
                or (
                    connection.source_id
                    == target
                    and connection.target_id
                    == source
                )
            ):
                return connection

        return None

    # ========================================================
    # TOPOLOGY HIERARCHY
    # ========================================================

    def children_of(
        self,
        parent_id: Any,
    ) -> list[TopologyAsset]:
        """
        Return assets whose parent_id matches the supplied ID.
        """
        parent = str(
            parent_id
        )

        return [
            asset
            for asset in self.assets.values()
            if asset.parent_id
            == parent
        ]

    def parent_of(
        self,
        asset_id: Any,
    ) -> TopologyAsset | None:
        """
        Return the parent asset of an asset.
        """
        asset = self.get_asset(
            asset_id
        )

        if (
            asset is None
            or asset.parent_id is None
        ):
            return None

        return self.get_asset(
            asset.parent_id
        )

    def descendants_of(
        self,
        parent_id: Any,
    ) -> list[TopologyAsset]:
        """
        Return all descendants in the parent hierarchy.
        """
        result: list[TopologyAsset] = []

        queue: deque[str] = deque(
            [str(parent_id)]
        )

        visited: set[str] = set()

        while queue:
            current = queue.popleft()

            if current in visited:
                continue

            visited.add(
                current
            )

            children = self.children_of(
                current
            )

            for child in children:
                result.append(
                    child
                )

                queue.append(
                    child.asset_id
                )

        return result

    # ========================================================
    # GRID-SPECIFIC GROUPING
    # ========================================================

    def substations(self) -> list[TopologyAsset]:
        """
        Return all substations.
        """
        return self.assets_by_type(
            "substation"
        )

    def buses(self) -> list[TopologyAsset]:
        """
        Return all buses.
        """
        return self.assets_by_type(
            "bus"
        )

    def feeders(self) -> list[TopologyAsset]:
        """
        Return all feeders.
        """
        return self.assets_by_type(
            "feeder"
        )

    def generators(self) -> list[TopologyAsset]:
        """
        Return all generators.
        """
        return self.assets_by_type(
            "generator"
        )

    def loads(self) -> list[TopologyAsset]:
        """
        Return all loads.
        """
        return self.assets_by_type(
            "load"
        )

    def transformers(self) -> list[TopologyAsset]:
        """
        Return all transformers.
        """
        return self.assets_by_type(
            "transformer"
        )

    def transmission_lines(
        self,
    ) -> list[TopologyAsset]:
        """
        Return all transmission lines.
        """
        return self.assets_by_type(
            "transmission_line"
        )

    # ========================================================
    # SUBSTATION ANALYSIS
    # ========================================================

    def assets_connected_to_substation(
        self,
        substation_id: Any,
    ) -> list[TopologyAsset]:
        """
        Return assets directly connected to a substation.
        """
        substation = str(
            substation_id
        )

        return [
            self.assets[neighbor]
            for neighbor in self.neighbors(
                substation
            )
            if neighbor in self.assets
        ]

    def feeder_count_for_substation(
        self,
        substation_id: Any,
    ) -> int:
        """
        Count directly connected feeders.
        """
        return sum(
            asset.asset_type
            == "feeder"
            for asset
            in self.assets_connected_to_substation(
                substation_id
            )
        )

    def generator_count_for_substation(
        self,
        substation_id: Any,
    ) -> int:
        """
        Count directly connected generators.
        """
        return sum(
            asset.asset_type
            == "generator"
            for asset
            in self.assets_connected_to_substation(
                substation_id
            )
        )

    # ========================================================
    # TOPOLOGY VALIDATION
    # ========================================================

    def validate(
        self,
    ) -> list[str]:
        """
        Validate topology consistency.

        Returns:
            List of validation errors.

        An empty list means no structural validation errors
        were found.
        """
        errors: list[str] = []

        for asset_id, asset in self.assets.items():
            if asset_id != str(
                asset.asset_id
            ):
                errors.append(
                    f"Asset key mismatch: {asset_id}"
                )

            if (
                asset.asset_type
                not in VALID_ASSET_TYPES
            ):
                errors.append(
                    "Unknown asset type "
                    f"'{asset.asset_type}' "
                    f"for asset '{asset_id}'."
                )

            if (
                asset.parent_id is not None
                and asset.parent_id
                not in self.assets
            ):
                errors.append(
                    f"Asset '{asset_id}' references "
                    f"missing parent '{asset.parent_id}'."
                )

        for connection_id, connection in (
            self.connections.items()
        ):
            if (
                connection.source_id
                not in self.assets
            ):
                errors.append(
                    f"Connection '{connection_id}' "
                    f"references missing source "
                    f"'{connection.source_id}'."
                )

            if (
                connection.target_id
                not in self.assets
            ):
                errors.append(
                    f"Connection '{connection_id}' "
                    f"references missing target "
                    f"'{connection.target_id}'."
                )

            if (
                connection.source_id
                == connection.target_id
            ):
                errors.append(
                    f"Connection '{connection_id}' "
                    "connects an asset to itself."
                )

        return errors

    def is_valid(
        self,
    ) -> bool:
        """
        Return True when topology validation succeeds.
        """
        return not self.validate()

    # ========================================================
    # CONTINGENCY
    # ========================================================

    def without_connection(
        self,
        connection_id: Any,
    ) -> GridTopology:
        """
        Return a copy of the topology with one connection
        removed.

        The original topology is not modified.
        """
        copied = self.copy()

        copied.remove_connection(
            connection_id
        )

        return copied

    def without_asset(
        self,
        asset_id: Any,
    ) -> GridTopology:
        """
        Return a copy of the topology with one asset removed.
        """
        copied = self.copy()

        copied.remove_asset(
            asset_id
        )

        return copied

    def connection_contingency(
        self,
        connection_id: Any,
    ) -> dict[str, Any]:
        """
        Analyze the structural effect of removing a connection.
        """
        before = self.component_count()

        before_largest = (
            self.largest_component_ratio()
        )

        modified = self.without_connection(
            connection_id
        )

        after = modified.component_count()

        after_largest = (
            modified.largest_component_ratio()
        )

        return {
            "connection_id": str(
                connection_id
            ),
            "before_component_count": before,
            "after_component_count": after,
            "component_count_change": (
                after - before
            ),
            "before_largest_component_ratio": (
                before_largest
            ),
            "after_largest_component_ratio": (
                after_largest
            ),
            "largest_component_ratio_loss": (
                before_largest
                - after_largest
            ),
            "is_critical": after > before,
        }

    def asset_contingency(
        self,
        asset_id: Any,
    ) -> dict[str, Any]:
        """
        Analyze the structural effect of removing an asset.
        """
        before = self.component_count()

        before_largest = (
            self.largest_component_ratio()
        )

        modified = self.without_asset(
            asset_id
        )

        after = modified.component_count()

        after_largest = (
            modified.largest_component_ratio()
        )

        return {
            "asset_id": str(
                asset_id
            ),
            "before_component_count": before,
            "after_component_count": after,
            "component_count_change": (
                after - before
            ),
            "before_largest_component_ratio": (
                before_largest
            ),
            "after_largest_component_ratio": (
                after_largest
            ),
            "largest_component_ratio_loss": (
                before_largest
                - after_largest
            ),
            "is_critical": after > before,
        }

    # ========================================================
    # COPY
    # ========================================================

    def copy(self) -> GridTopology:
        """
        Create an independent copy of the topology.
        """
        copied = GridTopology()

        for asset in self.assets.values():
            copied.add_asset(
                TopologyAsset(
                    asset_id=asset.asset_id,
                    asset_type=asset.asset_type,
                    name=asset.name,
                    node_id=asset.node_id,
                    parent_id=asset.parent_id,
                    region_id=asset.region_id,
                    status=asset.status,
                    metadata=dict(
                        asset.metadata
                    ),
                )
            )

        for connection in self.connections.values():
            copied.add_connection(
                TopologyConnection(
                    connection_id=(
                        connection.connection_id
                    ),
                    source_id=connection.source_id,
                    target_id=connection.target_id,
                    connection_type=(
                        connection.connection_type
                    ),
                    status=connection.status,
                    metadata=dict(
                        connection.metadata
                    ),
                )
            )

        return copied

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize topology into a JSON-compatible dictionary.
        """
        return {
            "assets": [
                {
                    "asset_id": asset.asset_id,
                    "asset_type": asset.asset_type,
                    "name": asset.name,
                    "node_id": asset.node_id,
                    "parent_id": asset.parent_id,
                    "region_id": asset.region_id,
                    "status": asset.status,
                    "metadata": dict(
                        asset.metadata
                    ),
                }
                for asset in self.assets.values()
            ],
            "connections": [
                {
                    "connection_id": (
                        connection.connection_id
                    ),
                    "source_id": connection.source_id,
                    "target_id": connection.target_id,
                    "connection_type": (
                        connection.connection_type
                    ),
                    "status": connection.status,
                    "metadata": dict(
                        connection.metadata
                    ),
                }
                for connection in self.connections.values()
            ],
        }


# ============================================================
# CONVENIENCE BUILDERS
# ============================================================


def build_topology(
    assets: Iterable[dict[str, Any]] | None = None,
    connections: Iterable[dict[str, Any]] | None = None,
) -> GridTopology:
    """
    Build a GridTopology from dictionaries.

    Example asset:

        {
            "id": "SUB_001",
            "type": "substation",
            "name": "Main Substation",
            "region_id": "REGION_01"
        }

    Example connection:

        {
            "id": "LINE_001",
            "source_id": "SUB_001",
            "target_id": "SUB_002",
            "type": "transmission_line"
        }
    """
    topology = GridTopology()

    for item in assets or []:
        asset_id = item.get(
            "asset_id",
            item.get("id"),
        )

        if asset_id is None:
            continue

        topology.add_asset_data(
            asset_id=asset_id,
            asset_type=item.get(
                "asset_type",
                item.get(
                    "type",
                    "unknown",
                ),
            ),
            name=item.get(
                "name"
            ),
            node_id=item.get(
                "node_id"
            ),
            parent_id=item.get(
                "parent_id"
            ),
            region_id=item.get(
                "region_id"
            ),
            status=item.get(
                "status",
                "unknown",
            ),
            metadata=item.get(
                "metadata",
                {},
            ),
        )

    for item in connections or []:
        connection_id = item.get(
            "connection_id",
            item.get("id"),
        )

        source_id = item.get(
            "source_id",
            item.get("source"),
        )

        target_id = item.get(
            "target_id",
            item.get("target"),
        )

        if (
            connection_id is None
            or source_id is None
            or target_id is None
        ):
            continue

        topology.add_connection_data(
            connection_id=connection_id,
            source_id=source_id,
            target_id=target_id,
            connection_type=item.get(
                "connection_type",
                item.get(
                    "type",
                    "unknown",
                ),
            ),
            status=item.get(
                "status",
                "active",
            ),
            metadata=item.get(
                "metadata",
                {},
            ),
        )

    return topology


def topology_from_edges(
    edges: Iterable[Sequence[Any]],
) -> GridTopology:
    """
    Create a simple topology from edge tuples.

    Each edge must contain:

        (source_id, target_id)

    Connection IDs are generated automatically.
    """
    topology = GridTopology()

    for index, edge in enumerate(
        edges
    ):
        if len(edge) < 2:
            continue

        source_id = str(
            edge[0]
        )

        target_id = str(
            edge[1]
        )

        topology.add_connection_data(
            connection_id=(
                f"CONNECTION_{index + 1}"
            ),
            source_id=source_id,
            target_id=target_id,
        )

    return topology


# ============================================================
# TOPOLOGY METRICS
# ============================================================


def topology_connectivity_score(
    topology: GridTopology,
    active_only: bool = True,
) -> float:
    """
    Calculate a normalized topology connectivity score.

    Higher values indicate a more connected topology.
    """
    if topology.asset_count() == 0:
        return 0.0

    largest_ratio = (
        topology.largest_component_ratio(
            active_only=active_only
        )
    )

    component_count = (
        topology.component_count(
            active_only=active_only
        )
    )

    if component_count <= 1:
        fragmentation_score = 1.0
    else:
        fragmentation_score = 1.0 / component_count

    score = (
        largest_ratio * 0.70
        + fragmentation_score * 0.30
    )

    return max(
        0.0,
        min(
            1.0,
            score,
        ),
    )


def topology_fragility_score(
    topology: GridTopology,
    active_only: bool = True,
) -> float:
    """
    Calculate a normalized structural fragility score.

    Higher values indicate greater structural vulnerability.
    """
    if topology.asset_count() == 0:
        return 0.0

    connectivity_loss = (
        1.0
        - topology.largest_component_ratio(
            active_only=active_only
        )
    )

    component_count = (
        topology.component_count(
            active_only=active_only
        )
    )

    if topology.connection_count() > 0:
        connection_density = (
            topology.connection_count()
            / max(
                1,
                topology.asset_count(),
            )
        )
    else:
        connection_density = 0.0

    isolated_ratio = (
        len(
            [
                asset_id
                for asset_id in topology.assets
                if topology.degree(
                    asset_id
                ) == 0
            ]
        )
        / topology.asset_count()
    )

    fragmentation = min(
        1.0,
        max(
            0.0,
            (
                component_count - 1
            )
            / max(
                1,
                topology.asset_count() - 1,
            ),
        ),
    )

    redundancy_proxy = min(
        1.0,
        connection_density / 2.0,
    )

    score = (
        connectivity_loss * 0.40
        + fragmentation * 0.25
        + isolated_ratio * 0.20
        + (
            1.0
            - redundancy_proxy
        ) * 0.15
    )

    return max(
        0.0,
        min(
            1.0,
            score,
        ),
    )


# ============================================================
# TOPOLOGY SUMMARY
# ============================================================


def topology_summary(
    topology: GridTopology,
    active_only: bool = True,
) -> dict[str, Any]:
    """
    Return a compact topology summary.
    """
    asset_type_counts: dict[
        str,
        int,
    ] = defaultdict(int)

    for asset in topology.assets.values():
        asset_type_counts[
            asset.asset_type
        ] += 1

    return {
        "asset_count": topology.asset_count(),
        "connection_count": (
            topology.connection_count()
        ),
        "component_count": (
            topology.component_count(
                active_only=active_only
            )
        ),
        "largest_component_ratio": (
            topology.largest_component_ratio(
                active_only=active_only
            )
        ),
        "connectivity_score": (
            topology_connectivity_score(
                topology,
                active_only=active_only,
            )
        ),
        "fragility_score": (
            topology_fragility_score(
                topology,
                active_only=active_only,
            )
        ),
        "asset_type_counts": dict(
            asset_type_counts
        ),
        "is_connected": topology.is_connected(
            active_only=active_only
        ),
        "validation_errors": topology.validate(),
        "is_valid": topology.is_valid(),
    }


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "TopologyAsset",
    "TopologyConnection",
    "GridTopology",
    "build_topology",
    "topology_from_edges",
    "topology_connectivity_score",
    "topology_fragility_score",
    "topology_summary",
]