"""
Blackout Oracle - Grid Graph Utilities.

Provides deterministic graph operations for representing and
analyzing electrical-grid topology.

This module is intentionally independent of the database layer.
It works with nodes and edges supplied by the caller.

Used for:

- Grid topology construction
- Connectivity analysis
- Path finding
- Island detection
- Contingency analysis
- Critical asset analysis
- Cascading-failure analysis

This module performs analytical operations only.
It does not issue commands to physical grid equipment.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any


# ============================================================
# DATA STRUCTURES
# ============================================================


@dataclass
class GridNode:
    """
    Represents a node in the electrical-grid graph.

    Examples of nodes:

        - Bus
        - Substation
        - Generator
        - Load
        - Transformer terminal
    """

    node_id: str
    node_type: str = "unknown"
    name: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class GridEdge:
    """
    Represents a connection between two grid nodes.

    Examples of edges:

        - Transmission line
        - Feeder
        - Transformer connection
        - Bus connection
    """

    edge_id: str
    source: str
    target: str
    edge_type: str = "unknown"
    weight: float = 1.0
    capacity: float | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# GRID GRAPH
# ============================================================


class GridGraph:
    """
    Lightweight undirected graph representation of a power grid.

    The graph stores:

        - Nodes
        - Edges
        - Adjacency relationships

    It does not perform electrical power-flow calculations.
    Electrical calculations belong in the appropriate electrical
    analysis layer.
    """

    def __init__(
        self,
        nodes: Iterable[GridNode] | None = None,
        edges: Iterable[GridEdge] | None = None,
    ) -> None:
        """
        Initialize a grid graph.
        """
        self.nodes: dict[str, GridNode] = {}

        self.edges: dict[str, GridEdge] = {}

        self.adjacency: dict[str, set[str]] = {}

        if nodes is not None:
            for node in nodes:
                self.add_node(node)

        if edges is not None:
            for edge in edges:
                self.add_edge(edge)

    # ========================================================
    # NODE OPERATIONS
    # ========================================================

    def add_node(
        self,
        node: GridNode,
    ) -> None:
        """
        Add or replace a node.
        """
        node_id = str(
            node.node_id
        )

        node.node_id = node_id

        self.nodes[node_id] = node

        self.adjacency.setdefault(
            node_id,
            set(),
        )

    def add_node_data(
        self,
        node_id: Any,
        node_type: str = "unknown",
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GridNode:
        """
        Convenience method for creating and adding a node.
        """
        node = GridNode(
            node_id=str(node_id),
            node_type=node_type,
            name=name,
            metadata=dict(
                metadata or {}
            ),
        )

        self.add_node(node)

        return node

    def remove_node(
        self,
        node_id: Any,
    ) -> bool:
        """
        Remove a node and all edges connected to it.

        Returns:
            True if the node existed.
        """
        normalized = str(
            node_id
        )

        if normalized not in self.nodes:
            return False

        connected_edges = [
            edge_id
            for edge_id, edge in self.edges.items()
            if (
                edge.source == normalized
                or edge.target == normalized
            )
        ]

        for edge_id in connected_edges:
            self.remove_edge(edge_id)

        self.nodes.pop(
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

    def has_node(
        self,
        node_id: Any,
    ) -> bool:
        """
        Check whether a node exists.
        """
        return str(
            node_id
        ) in self.nodes

    def get_node(
        self,
        node_id: Any,
    ) -> GridNode | None:
        """
        Retrieve a node.
        """
        return self.nodes.get(
            str(node_id)
        )

    # ========================================================
    # EDGE OPERATIONS
    # ========================================================

    def add_edge(
        self,
        edge: GridEdge,
    ) -> None:
        """
        Add an edge.

        Missing endpoint nodes are automatically created as
        generic nodes.
        """
        edge_id = str(
            edge.edge_id
        )

        edge.edge_id = edge_id

        source = str(
            edge.source
        )

        target = str(
            edge.target
        )

        edge.source = source
        edge.target = target

        if source not in self.nodes:
            self.add_node_data(
                source
            )

        if target not in self.nodes:
            self.add_node_data(
                target
            )

        self.edges[edge_id] = edge

        self.adjacency.setdefault(
            source,
            set(),
        )

        self.adjacency.setdefault(
            target,
            set(),
        )

        if source != target:
            self.adjacency[source].add(
                target
            )

            self.adjacency[target].add(
                source
            )

    def add_edge_data(
        self,
        edge_id: Any,
        source: Any,
        target: Any,
        edge_type: str = "unknown",
        weight: float = 1.0,
        capacity: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GridEdge:
        """
        Convenience method for creating and adding an edge.
        """
        edge = GridEdge(
            edge_id=str(edge_id),
            source=str(source),
            target=str(target),
            edge_type=edge_type,
            weight=float(weight),
            capacity=capacity,
            metadata=dict(
                metadata or {}
            ),
        )

        self.add_edge(edge)

        return edge

    def remove_edge(
        self,
        edge_id: Any,
    ) -> bool:
        """
        Remove an edge.

        Returns:
            True if the edge existed.
        """
        normalized = str(
            edge_id
        )

        edge = self.edges.pop(
            normalized,
            None,
        )

        if edge is None:
            return False

        if edge.source in self.adjacency:
            self.adjacency[
                edge.source
            ].discard(
                edge.target
            )

        if edge.target in self.adjacency:
            self.adjacency[
                edge.target
            ].discard(
                edge.source
            )

        return True

    def has_edge(
        self,
        edge_id: Any,
    ) -> bool:
        """
        Check whether an edge exists.
        """
        return str(
            edge_id
        ) in self.edges

    def get_edge(
        self,
        edge_id: Any,
    ) -> GridEdge | None:
        """
        Retrieve an edge.
        """
        return self.edges.get(
            str(edge_id)
        )

    # ========================================================
    # GRAPH INFORMATION
    # ========================================================

    def node_count(self) -> int:
        """
        Return the number of nodes.
        """
        return len(
            self.nodes
        )

    def edge_count(self) -> int:
        """
        Return the number of edges.
        """
        return len(
            self.edges
        )

    def degree(
        self,
        node_id: Any,
    ) -> int:
        """
        Return the number of neighboring nodes.
        """
        return len(
            self.adjacency.get(
                str(node_id),
                set(),
            )
        )

    def neighbors(
        self,
        node_id: Any,
    ) -> set[str]:
        """
        Return neighboring node identifiers.

        A copy is returned so callers cannot accidentally
        modify the graph.
        """
        return set(
            self.adjacency.get(
                str(node_id),
                set(),
            )
        )

    def edges_for_node(
        self,
        node_id: Any,
    ) -> list[GridEdge]:
        """
        Return all edges connected to a node.
        """
        normalized = str(
            node_id
        )

        return [
            edge
            for edge in self.edges.values()
            if (
                edge.source == normalized
                or edge.target == normalized
            )
        ]

    # ========================================================
    # TRAVERSAL
    # ========================================================

    def reachable_nodes(
        self,
        start_node: Any,
    ) -> set[str]:
        """
        Return all nodes reachable from a starting node.
        """
        start = str(
            start_node
        )

        if start not in self.nodes:
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
                if neighbor not in visited:
                    visited.add(
                        neighbor
                    )

                    queue.append(
                        neighbor
                    )

        return visited

    def is_connected(self) -> bool:
        """
        Determine whether the graph is fully connected.

        An empty graph is considered disconnected.
        """
        if not self.nodes:
            return False

        start = next(
            iter(self.nodes)
        )

        return (
            len(
                self.reachable_nodes(
                    start
                )
            )
            == len(self.nodes)
        )

    # ========================================================
    # COMPONENTS
    # ========================================================

    def connected_components(
        self,
    ) -> list[set[str]]:
        """
        Return all connected components.
        """
        remaining = set(
            self.nodes.keys()
        )

        components: list[set[str]] = []

        while remaining:
            start = next(
                iter(remaining)
            )

            component = (
                self.reachable_nodes(
                    start
                )
            )

            components.append(
                component
            )

            remaining -= component

        return components

    def component_count(self) -> int:
        """
        Return the number of connected components.
        """
        return len(
            self.connected_components()
        )

    def largest_component_size(
        self,
    ) -> int:
        """
        Return the number of nodes in the largest component.
        """
        components = (
            self.connected_components()
        )

        if not components:
            return 0

        return max(
            len(component)
            for component in components
        )

    def largest_component_ratio(
        self,
    ) -> float:
        """
        Return the fraction of all nodes contained in the
        largest connected component.
        """
        if not self.nodes:
            return 0.0

        return (
            self.largest_component_size()
            / len(self.nodes)
        )

    # ========================================================
    # PATH FINDING
    # ========================================================

    def shortest_path(
        self,
        start_node: Any,
        target_node: Any,
    ) -> list[str] | None:
        """
        Find a shortest path between two nodes.

        Returns:
            List of node IDs including start and target,
            or None if no path exists.
        """
        start = str(
            start_node
        )

        target = str(
            target_node
        )

        if (
            start not in self.nodes
            or target not in self.nodes
        ):
            return None

        if start == target:
            return [start]

        queue: deque[str] = deque(
            [start]
        )

        parent: dict[str, str | None] = {
            start: None
        }

        while queue:
            current = queue.popleft()

            for neighbor in self.adjacency.get(
                current,
                set(),
            ):
                if neighbor in parent:
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
        start_node: Any,
        target_node: Any,
    ) -> int | None:
        """
        Return the number of edges in the shortest path.
        """
        path = self.shortest_path(
            start_node,
            target_node,
        )

        if path is None:
            return None

        return max(
            0,
            len(path) - 1,
        )

    # ========================================================
    # EDGE PATH LOOKUP
    # ========================================================

    def edge_between(
        self,
        source: Any,
        target: Any,
    ) -> GridEdge | None:
        """
        Find an edge connecting two nodes.

        Because this is an undirected graph, either orientation
        is accepted.
        """
        source_id = str(
            source
        )

        target_id = str(
            target
        )

        for edge in self.edges.values():
            if (
                (
                    edge.source == source_id
                    and edge.target == target_id
                )
                or (
                    edge.source == target_id
                    and edge.target == source_id
                )
            ):
                return edge

        return None

    def path_edges(
        self,
        path: Sequence[Any],
    ) -> list[GridEdge]:
        """
        Convert a node path into its corresponding graph edges.

        Missing connections are skipped.
        """
        if len(path) < 2:
            return []

        result: list[GridEdge] = []

        for index in range(
            len(path) - 1
        ):
            edge = self.edge_between(
                path[index],
                path[index + 1],
            )

            if edge is not None:
                result.append(
                    edge
                )

        return result

    # ========================================================
    # GRAPH COPY / CONTINGENCY
    # ========================================================

    def copy(self) -> GridGraph:
        """
        Create an independent copy of the graph.
        """
        copied = GridGraph()

        for node in self.nodes.values():
            copied.add_node(
                GridNode(
                    node_id=node.node_id,
                    node_type=node.node_type,
                    name=node.name,
                    metadata=dict(
                        node.metadata
                    ),
                )
            )

        for edge in self.edges.values():
            copied.add_edge(
                GridEdge(
                    edge_id=edge.edge_id,
                    source=edge.source,
                    target=edge.target,
                    edge_type=edge.edge_type,
                    weight=edge.weight,
                    capacity=edge.capacity,
                    metadata=dict(
                        edge.metadata
                    ),
                )
            )

        return copied

    def without_edge(
        self,
        edge_id: Any,
    ) -> GridGraph:
        """
        Return a copy of the graph with one edge removed.

        The original graph remains unchanged.
        """
        copied = self.copy()

        copied.remove_edge(
            edge_id
        )

        return copied

    def without_node(
        self,
        node_id: Any,
    ) -> GridGraph:
        """
        Return a copy of the graph with one node removed.

        The original graph remains unchanged.
        """
        copied = self.copy()

        copied.remove_node(
            node_id
        )

        return copied

    # ========================================================
    # BRIDGE ANALYSIS
    # ========================================================

    def bridge_edges(self) -> list[GridEdge]:
        """
        Find graph edges whose removal disconnects part of
        their connected component.

        Uses Tarjan's bridge-finding algorithm.
        """
        discovery: dict[str, int] = {}

        low: dict[str, int] = {}

        parent: dict[str, str | None] = {}

        bridges: list[str] = []

        counter = 0

        def visit(
            node: str,
        ) -> None:
            nonlocal counter

            counter += 1

            discovery[node] = counter
            low[node] = counter

            for neighbor in self.adjacency.get(
                node,
                set(),
            ):
                if neighbor not in discovery:
                    parent[neighbor] = node

                    visit(
                        neighbor
                    )

                    low[node] = min(
                        low[node],
                        low[neighbor],
                    )

                    if (
                        low[neighbor]
                        > discovery[node]
                    ):
                        edge = self.edge_between(
                            node,
                            neighbor,
                        )

                        if edge is not None:
                            bridges.append(
                                edge.edge_id
                            )

                elif (
                    neighbor
                    != parent.get(node)
                ):
                    low[node] = min(
                        low[node],
                        discovery[neighbor],
                    )

        for node in self.nodes:
            if node not in discovery:
                parent[node] = None

                visit(
                    node
                )

        return [
            self.edges[edge_id]
            for edge_id in bridges
            if edge_id in self.edges
        ]

    def bridge_count(self) -> int:
        """
        Return the number of bridge edges.
        """
        return len(
            self.bridge_edges()
        )

    # ========================================================
    # CRITICAL NODE ANALYSIS
    # ========================================================

    def articulation_nodes(self) -> list[str]:
        """
        Find articulation nodes.

        An articulation node is a node whose removal increases
        the number of connected components within its relevant
        component.

        Uses Tarjan's articulation-point algorithm.
        """
        discovery: dict[str, int] = {}

        low: dict[str, int] = {}

        parent: dict[str, str | None] = {}

        articulation: set[str] = set()

        counter = 0

        def visit(
            node: str,
        ) -> None:
            nonlocal counter

            counter += 1

            discovery[node] = counter
            low[node] = counter

            children = 0

            for neighbor in self.adjacency.get(
                node,
                set(),
            ):
                if neighbor not in discovery:
                    parent[neighbor] = node

                    children += 1

                    visit(
                        neighbor
                    )

                    low[node] = min(
                        low[node],
                        low[neighbor],
                    )

                    current_parent = parent.get(
                        node
                    )

                    if (
                        current_parent is None
                        and children > 1
                    ):
                        articulation.add(
                            node
                        )

                    if (
                        current_parent is not None
                        and low[neighbor]
                        >= discovery[node]
                    ):
                        articulation.add(
                            node
                        )

                elif (
                    neighbor
                    != parent.get(node)
                ):
                    low[node] = min(
                        low[node],
                        discovery[neighbor],
                    )

        for node in self.nodes:
            if node not in discovery:
                parent[node] = None

                visit(
                    node
                )

        return sorted(
            articulation
        )

    def articulation_count(self) -> int:
        """
        Return the number of articulation nodes.
        """
        return len(
            self.articulation_nodes()
        )

    # ========================================================
    # NETWORK METRICS
    # ========================================================

    def average_degree(self) -> float:
        """
        Calculate average node degree.
        """
        if not self.nodes:
            return 0.0

        return (
            sum(
                self.degree(node_id)
                for node_id in self.nodes
            )
            / len(self.nodes)
        )

    def density(self) -> float:
        """
        Calculate undirected graph density.

        Density:

            2E / N(N-1)
        """
        node_total = self.node_count()

        if node_total < 2:
            return 0.0

        return (
            2.0 * self.edge_count()
        ) / (
            node_total
            * (node_total - 1)
        )

    def isolated_nodes(self) -> list[str]:
        """
        Return nodes with no connections.
        """
        return [
            node_id
            for node_id in self.nodes
            if self.degree(node_id) == 0
        ]

    def isolation_ratio(self) -> float:
        """
        Calculate the fraction of isolated nodes.
        """
        if not self.nodes:
            return 0.0

        return (
            len(
                self.isolated_nodes()
            )
            / len(self.nodes)
        )

    # ========================================================
    # CONTINGENCY ANALYSIS
    # ========================================================

    def edge_contingency(
        self,
        edge_id: Any,
    ) -> dict[str, Any]:
        """
        Analyze the structural effect of removing one edge.

        Returns:
            A dictionary containing before/after connectivity
            information.
        """
        original_components = (
            self.component_count()
        )

        original_largest = (
            self.largest_component_size()
        )

        modified = self.without_edge(
            edge_id
        )

        modified_components = (
            modified.component_count()
        )

        modified_largest = (
            modified.largest_component_size()
        )

        return {
            "edge_id": str(edge_id),
            "original_component_count": original_components,
            "modified_component_count": modified_components,
            "component_count_change": (
                modified_components
                - original_components
            ),
            "original_largest_component_size": original_largest,
            "modified_largest_component_size": modified_largest,
            "largest_component_loss": (
                original_largest
                - modified_largest
            ),
            "is_critical": (
                modified_components
                > original_components
            ),
        }

    def node_contingency(
        self,
        node_id: Any,
    ) -> dict[str, Any]:
        """
        Analyze the structural effect of removing one node.
        """
        original_components = (
            self.component_count()
        )

        original_largest = (
            self.largest_component_size()
        )

        modified = self.without_node(
            node_id
        )

        modified_components = (
            modified.component_count()
        )

        modified_largest = (
            modified.largest_component_size()
        )

        return {
            "node_id": str(node_id),
            "original_component_count": original_components,
            "modified_component_count": modified_components,
            "component_count_change": (
                modified_components
                - original_components
            ),
            "original_largest_component_size": original_largest,
            "modified_largest_component_size": modified_largest,
            "largest_component_loss": (
                original_largest
                - modified_largest
            ),
            "is_critical": (
                modified_components
                > original_components
            ),
        }

    # ========================================================
    # CRITICALITY
    # ========================================================

    def node_criticality(
        self,
        node_id: Any,
    ) -> float:
        """
        Estimate structural criticality of a node.

        Factors:

            - Node degree
            - Articulation status
            - Component connectivity

        Returns:
            Value between 0.0 and 1.0.

        This is an analytical ranking feature and not a
        protection-system threshold.
        """
        normalized = str(
            node_id
        )

        if normalized not in self.nodes:
            return 0.0

        maximum_degree = max(
            (
                self.degree(
                    current
                )
                for current in self.nodes
            ),
            default=0,
        )

        if maximum_degree > 0:
            degree_score = (
                self.degree(
                    normalized
                )
                / maximum_degree
            )
        else:
            degree_score = 0.0

        articulation_score = (
            1.0
            if normalized
            in set(
                self.articulation_nodes()
            )
            else 0.0
        )

        component_score = (
            len(
                self.reachable_nodes(
                    normalized
                )
            )
            / max(
                1,
                self.node_count(),
            )
        )

        return max(
            0.0,
            min(
                1.0,
                (
                    degree_score * 0.30
                    + articulation_score * 0.40
                    + component_score * 0.30
                ),
            ),
        )

    def edge_criticality(
        self,
        edge_id: Any,
    ) -> float:
        """
        Estimate structural criticality of an edge.

        Bridge edges receive the highest structural score.
        """
        edge = self.get_edge(
            edge_id
        )

        if edge is None:
            return 0.0

        contingency = self.edge_contingency(
            edge_id
        )

        component_change = max(
            0,
            int(
                contingency[
                    "component_count_change"
                ]
            ),
        )

        largest_component_loss = max(
            0,
            int(
                contingency[
                    "largest_component_loss"
                ]
            ),
        )

        if self.node_count() > 0:
            component_loss_score = (
                largest_component_loss
                / self.node_count()
            )
        else:
            component_loss_score = 0.0

        bridge_score = (
            1.0
            if component_change > 0
            else 0.0
        )

        return max(
            0.0,
            min(
                1.0,
                (
                    bridge_score * 0.70
                    + component_loss_score * 0.30
                ),
            ),
        )

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the graph into a JSON-compatible dictionary.
        """
        return {
            "nodes": [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "name": node.name,
                    "metadata": dict(
                        node.metadata
                    ),
                }
                for node in self.nodes.values()
            ],
            "edges": [
                {
                    "edge_id": edge.edge_id,
                    "source": edge.source,
                    "target": edge.target,
                    "edge_type": edge.edge_type,
                    "weight": edge.weight,
                    "capacity": edge.capacity,
                    "metadata": dict(
                        edge.metadata
                    ),
                }
                for edge in self.edges.values()
            ],
        }


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def create_grid_graph(
    nodes: Iterable[dict[str, Any]] | None = None,
    edges: Iterable[dict[str, Any]] | None = None,
) -> GridGraph:
    """
    Create a GridGraph from dictionaries.

    Example node:

        {
            "id": "BUS_1",
            "type": "bus",
            "name": "Main Bus"
        }

    Example edge:

        {
            "id": "LINE_1",
            "source": "BUS_1",
            "target": "BUS_2",
            "type": "transmission_line"
        }
    """
    graph = GridGraph()

    for item in nodes or []:
        node_id = item.get(
            "node_id",
            item.get(
                "id"
            ),
        )

        if node_id is None:
            continue

        graph.add_node_data(
            node_id=node_id,
            node_type=item.get(
                "node_type",
                item.get(
                    "type",
                    "unknown",
                ),
            ),
            name=item.get(
                "name"
            ),
            metadata=item.get(
                "metadata",
                {},
            ),
        )

    for item in edges or []:
        edge_id = item.get(
            "edge_id",
            item.get(
                "id"
            ),
        )

        source = item.get(
            "source"
        )

        target = item.get(
            "target"
        )

        if (
            edge_id is None
            or source is None
            or target is None
        ):
            continue

        graph.add_edge_data(
            edge_id=edge_id,
            source=source,
            target=target,
            edge_type=item.get(
                "edge_type",
                item.get(
                    "type",
                    "unknown",
                ),
            ),
            weight=item.get(
                "weight",
                1.0,
            ),
            capacity=item.get(
                "capacity"
            ),
            metadata=item.get(
                "metadata",
                {},
            ),
        )

    return graph


def graph_from_edges(
    edges: Iterable[Sequence[Any]],
) -> GridGraph:
    """
    Create a simple graph from edge tuples.

    Each edge must contain:

        (source, target)

    Edge IDs are automatically generated.
    """
    graph = GridGraph()

    for index, edge in enumerate(edges):
        if len(edge) < 2:
            continue

        source = str(
            edge[0]
        )

        target = str(
            edge[1]
        )

        graph.add_edge_data(
            edge_id=f"EDGE_{index + 1}",
            source=source,
            target=target,
        )

    return graph


def graph_connectivity_score(
    graph: GridGraph,
) -> float:
    """
    Calculate a simple normalized connectivity score.

    The score combines:

        - Largest connected component
        - Low isolation
        - Low fragmentation

    Returns:
        Value between 0.0 and 1.0.
    """
    if graph.node_count() == 0:
        return 0.0

    largest_component = (
        graph.largest_component_ratio()
    )

    isolation = (
        graph.isolation_ratio()
    )

    if graph.component_count() <= 1:
        fragmentation = 1.0
    else:
        fragmentation = 1.0 / (
            graph.component_count()
        )

    score = (
        largest_component * 0.50
        + (
            1.0 - isolation
        ) * 0.25
        + fragmentation * 0.25
    )

    return max(
        0.0,
        min(
            1.0,
            score,
        ),
    )


def graph_fragility_score(
    graph: GridGraph,
) -> float:
    """
    Calculate a simple structural fragility score.

    Higher values indicate greater structural vulnerability.

    Factors:

        - Network fragmentation
        - Bridge dependence
        - Articulation-node dependence
        - Isolated nodes
    """
    if graph.node_count() == 0:
        return 0.0

    fragmentation = max(
        0.0,
        1.0
        - graph.largest_component_ratio(),
    )

    if graph.edge_count() > 0:
        bridge_ratio = (
            graph.bridge_count()
            / graph.edge_count()
        )
    else:
        bridge_ratio = 0.0

    articulation_ratio = (
        graph.articulation_count()
        / graph.node_count()
    )

    isolation = (
        graph.isolation_ratio()
    )

    score = (
        fragmentation * 0.35
        + bridge_ratio * 0.30
        + articulation_ratio * 0.20
        + isolation * 0.15
    )

    return max(
        0.0,
        min(
            1.0,
            score,
        ),
    )


def graph_summary(
    graph: GridGraph,
) -> dict[str, Any]:
    """
    Return a compact summary of graph structure.
    """
    return {
        "node_count": graph.node_count(),
        "edge_count": graph.edge_count(),
        "component_count": graph.component_count(),
        "largest_component_size": (
            graph.largest_component_size()
        ),
        "largest_component_ratio": (
            graph.largest_component_ratio()
        ),
        "average_degree": (
            graph.average_degree()
        ),
        "network_density": (
            graph.density()
        ),
        "isolated_node_count": len(
            graph.isolated_nodes()
        ),
        "bridge_count": (
            graph.bridge_count()
        ),
        "articulation_node_count": (
            graph.articulation_count()
        ),
        "connectivity_score": (
            graph_connectivity_score(
                graph
            )
        ),
        "fragility_score": (
            graph_fragility_score(
                graph
            )
        ),
        "is_connected": (
            graph.is_connected()
        ),
    }


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "GridNode",
    "GridEdge",
    "GridGraph",
    "create_grid_graph",
    "graph_from_edges",
    "graph_connectivity_score",
    "graph_fragility_score",
    "graph_summary",
]