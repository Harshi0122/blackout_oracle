"""
Blackout Oracle - Network Feature Engineering.

Provides deterministic network-level feature calculations for
power-grid topology and connectivity analysis.

These features are used by:

- Risk scoring
- Cascading-failure analysis
- Blackout prediction
- Network resilience analysis
- Simulation
- AI investigation

This module does not directly control grid equipment.
It only calculates analytical features from supplied network
data.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Iterable, Sequence
from typing import Any


# ============================================================
# CONSTANTS
# ============================================================

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


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """
    Safely convert a value to int.
    """
    try:
        return int(value)

    except (TypeError, ValueError):
        return default


def _normalize_node(
    node: Any,
) -> str:
    """
    Convert a node identifier to a normalized string.
    """
    return str(node)


# ============================================================
# GRAPH CONSTRUCTION
# ============================================================


def build_adjacency(
    nodes: Iterable[Any],
    edges: Iterable[Sequence[Any]],
) -> dict[str, set[str]]:
    """
    Build an undirected adjacency representation.

    Args:
        nodes:
            Iterable containing node identifiers.

        edges:
            Iterable of two-element sequences:
            (node_a, node_b).

    Returns:
        Dictionary mapping each node to its neighbors.
    """
    adjacency: dict[str, set[str]] = {}

    for node in nodes:
        normalized = _normalize_node(node)
        adjacency.setdefault(
            normalized,
            set(),
        )

    for edge in edges:
        if len(edge) < 2:
            continue

        node_a = _normalize_node(edge[0])
        node_b = _normalize_node(edge[1])

        adjacency.setdefault(
            node_a,
            set(),
        )

        adjacency.setdefault(
            node_b,
            set(),
        )

        if node_a == node_b:
            continue

        adjacency[node_a].add(node_b)
        adjacency[node_b].add(node_a)

    return adjacency


# ============================================================
# BASIC NETWORK METRICS
# ============================================================


def node_count(
    adjacency: dict[str, set[str]],
) -> int:
    """
    Return the number of nodes in the network.
    """
    return len(adjacency)


def edge_count(
    adjacency: dict[str, set[str]],
) -> int:
    """
    Return the number of undirected edges.
    """
    return sum(
        len(neighbors)
        for neighbors in adjacency.values()
    ) // 2


def node_degree(
    adjacency: dict[str, set[str]],
    node: Any,
) -> int:
    """
    Return the degree of a node.
    """
    normalized = _normalize_node(node)

    return len(
        adjacency.get(
            normalized,
            set(),
        )
    )


def degree_statistics(
    adjacency: dict[str, set[str]],
) -> dict[str, float]:
    """
    Calculate basic network degree statistics.
    """
    if not adjacency:
        return {
            "minimum_degree": 0.0,
            "maximum_degree": 0.0,
            "average_degree": 0.0,
            "isolated_node_count": 0.0,
        }

    degrees = [
        len(neighbors)
        for neighbors in adjacency.values()
    ]

    isolated = sum(
        degree == 0
        for degree in degrees
    )

    return {
        "minimum_degree": float(
            min(degrees)
        ),
        "maximum_degree": float(
            max(degrees)
        ),
        "average_degree": (
            sum(degrees)
            / len(degrees)
        ),
        "isolated_node_count": float(
            isolated
        ),
    }


# ============================================================
# CONNECTIVITY
# ============================================================


def reachable_nodes(
    adjacency: dict[str, set[str]],
    start_node: Any,
) -> set[str]:
    """
    Return all nodes reachable from a starting node.

    Uses breadth-first traversal.
    """
    start = _normalize_node(
        start_node
    )

    if start not in adjacency:
        return set()

    visited: set[str] = {start}
    queue: deque[str] = deque([start])

    while queue:
        current = queue.popleft()

        for neighbor in adjacency.get(
            current,
            set(),
        ):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return visited


def is_connected(
    adjacency: dict[str, set[str]],
) -> bool:
    """
    Determine whether the entire network is connected.

    An empty network is considered disconnected for
    analytical purposes.
    """
    if not adjacency:
        return False

    start = next(iter(adjacency))

    return len(
        reachable_nodes(
            adjacency,
            start,
        )
    ) == len(adjacency)


def connected_components(
    adjacency: dict[str, set[str]],
) -> list[set[str]]:
    """
    Find all connected components in the network.

    Returns:
        List of node sets, one set per component.
    """
    remaining = set(
        adjacency.keys()
    )

    components: list[set[str]] = []

    while remaining:
        start = next(iter(remaining))

        component = reachable_nodes(
            adjacency,
            start,
        )

        components.append(component)

        remaining -= component

    return components


def component_count(
    adjacency: dict[str, set[str]],
) -> int:
    """
    Return the number of connected components.
    """
    return len(
        connected_components(adjacency)
    )


def largest_component_ratio(
    adjacency: dict[str, set[str]],
) -> float:
    """
    Calculate the fraction of nodes contained in the
    largest connected component.

    Returns:
        Value between 0.0 and 1.0.
    """
    total = len(adjacency)

    if total == 0:
        return 0.0

    components = connected_components(
        adjacency
    )

    largest = max(
        (
            len(component)
            for component in components
        ),
        default=0,
    )

    return largest / total


# ============================================================
# ISOLATION
# ============================================================


def isolated_nodes(
    adjacency: dict[str, set[str]],
) -> list[str]:
    """
    Return nodes with no network connections.
    """
    return [
        node
        for node, neighbors in adjacency.items()
        if not neighbors
    ]


def isolation_ratio(
    adjacency: dict[str, set[str]],
) -> float:
    """
    Calculate the fraction of isolated nodes.
    """
    if not adjacency:
        return 0.0

    return (
        len(isolated_nodes(adjacency))
        / len(adjacency)
    )


# ============================================================
# NETWORK DENSITY
# ============================================================


def network_density(
    adjacency: dict[str, set[str]],
) -> float:
    """
    Calculate undirected network density.

    Density is:

        2E / (N(N-1))

    Returns:
        Value between 0.0 and 1.0.
    """
    nodes = len(adjacency)

    if nodes < 2:
        return 0.0

    edges = edge_count(
        adjacency
    )

    return (
        2.0 * edges
    ) / (
        nodes * (nodes - 1)
    )


# ============================================================
# PATH ANALYSIS
# ============================================================


def shortest_path_length(
    adjacency: dict[str, set[str]],
    start_node: Any,
    target_node: Any,
) -> int | None:
    """
    Calculate the shortest number of edges between
    two nodes.

    Returns:
        Number of edges, or None if no path exists.
    """
    start = _normalize_node(
        start_node
    )

    target = _normalize_node(
        target_node
    )

    if start not in adjacency:
        return None

    if target not in adjacency:
        return None

    if start == target:
        return 0

    queue: deque[tuple[str, int]] = deque(
        [(start, 0)]
    )

    visited: set[str] = {start}

    while queue:
        current, distance = queue.popleft()

        for neighbor in adjacency.get(
            current,
            set(),
        ):
            if neighbor == target:
                return distance + 1

            if neighbor not in visited:
                visited.add(neighbor)

                queue.append(
                    (
                        neighbor,
                        distance + 1,
                    )
                )

    return None


def average_shortest_path_length(
    adjacency: dict[str, set[str]],
) -> float:
    """
    Calculate the average shortest path length among
    reachable node pairs.

    For disconnected networks, unreachable pairs are
    excluded from the average.
    """
    nodes = list(
        adjacency.keys()
    )

    if len(nodes) < 2:
        return 0.0

    total_distance = 0.0
    pair_count = 0

    for index, source in enumerate(nodes):
        queue: deque[tuple[str, int]] = deque(
            [(source, 0)]
        )

        visited: set[str] = {
            source
        }

        while queue:
            current, distance = queue.popleft()

            for neighbor in adjacency.get(
                current,
                set(),
            ):
                if neighbor in visited:
                    continue

                visited.add(neighbor)

                queue.append(
                    (
                        neighbor,
                        distance + 1,
                    )
                )

                if neighbor in nodes[index + 1:]:
                    total_distance += (
                        distance + 1
                    )

                    pair_count += 1

    if pair_count == 0:
        return 0.0

    return (
        total_distance
        / pair_count
    )


# ============================================================
# BRIDGE / SINGLE-POINT ANALYSIS
# ============================================================


def _find_bridges(
    adjacency: dict[str, set[str]],
) -> list[tuple[str, str]]:
    """
    Find bridge edges using depth-first traversal.

    A bridge is an edge whose removal increases the
    number of connected components.
    """
    discovery_time: dict[str, int] = {}
    low_link: dict[str, int] = {}

    parent: dict[str, str | None] = {}

    bridges: list[tuple[str, str]] = []

    counter = 0

    def visit(node: str) -> None:
        nonlocal counter

        counter += 1

        discovery_time[node] = counter
        low_link[node] = counter

        for neighbor in adjacency.get(
            node,
            set(),
        ):
            if neighbor not in discovery_time:
                parent[neighbor] = node

                visit(neighbor)

                low_link[node] = min(
                    low_link[node],
                    low_link[neighbor],
                )

                if (
                    low_link[neighbor]
                    > discovery_time[node]
                ):
                    bridges.append(
                        (
                            node,
                            neighbor,
                        )
                    )

            elif neighbor != parent.get(node):
                low_link[node] = min(
                    low_link[node],
                    discovery_time[neighbor],
                )

    for node in adjacency:
        if node not in discovery_time:
            parent[node] = None
            visit(node)

    return bridges


def bridge_count(
    adjacency: dict[str, set[str]],
) -> int:
    """
    Return the number of bridge edges.
    """
    return len(
        _find_bridges(adjacency)
    )


def bridge_ratio(
    adjacency: dict[str, set[str]],
) -> float:
    """
    Calculate the fraction of edges that are bridges.

    Returns:
        Value between 0.0 and 1.0.
    """
    edges = edge_count(
        adjacency
    )

    if edges == 0:
        return 0.0

    return (
        bridge_count(adjacency)
        / edges
    )


# ============================================================
# LOAD-BASED NETWORK FEATURES
# ============================================================


def overloaded_asset_ratio(
    loading_percentages: Sequence[Any],
    threshold_percent: float = 100.0,
) -> float:
    """
    Calculate the fraction of assets operating above
    the specified loading threshold.
    """
    values = [
        _safe_float(value)
        for value in loading_percentages
    ]

    if not values:
        return 0.0

    threshold = _safe_float(
        threshold_percent,
        100.0,
    )

    overloaded = sum(
        value >= threshold
        for value in values
    )

    return overloaded / len(values)


def high_loading_ratio(
    loading_percentages: Sequence[Any],
    threshold_percent: float = 80.0,
) -> float:
    """
    Calculate the fraction of assets operating above
    a high-loading threshold.
    """
    return overloaded_asset_ratio(
        loading_percentages,
        threshold_percent,
    )


def average_loading(
    loading_percentages: Sequence[Any],
) -> float:
    """
    Calculate average network asset loading.
    """
    if not loading_percentages:
        return 0.0

    values = [
        _safe_float(value)
        for value in loading_percentages
    ]

    return (
        sum(values)
        / len(values)
    )


def maximum_loading(
    loading_percentages: Sequence[Any],
) -> float:
    """
    Return the highest observed network loading.
    """
    if not loading_percentages:
        return 0.0

    return max(
        _safe_float(value)
        for value in loading_percentages
    )


# ============================================================
# CAPACITY FEATURES
# ============================================================


def total_capacity(
    capacities: Sequence[Any],
) -> float:
    """
    Calculate total available capacity.
    """
    return sum(
        max(
            0.0,
            _safe_float(value),
        )
        for value in capacities
    )


def capacity_utilization(
    current_load: float,
    total_capacity_value: float,
) -> float:
    """
    Calculate network capacity utilization.

    Returns:
        Percentage from 0 upward.
    """
    load = max(
        0.0,
        _safe_float(current_load),
    )

    capacity = _safe_float(
        total_capacity_value
    )

    if capacity <= EPSILON:
        return 0.0

    return (
        load / capacity
    ) * 100.0


def reserve_margin(
    available_capacity: float,
    current_load: float,
) -> float:
    """
    Calculate reserve margin as a percentage.

    Reserve margin:

        (capacity - load) / load * 100
    """
    capacity = _safe_float(
        available_capacity
    )

    load = max(
        0.0,
        _safe_float(current_load),
    )

    if load <= EPSILON:
        return 0.0

    return (
        (capacity - load)
        / load
    ) * 100.0


# ============================================================
# CONTINGENCY FEATURES
# ============================================================


def network_after_edge_removal(
    adjacency: dict[str, set[str]],
    edge: Sequence[Any],
) -> dict[str, set[str]]:
    """
    Create a copy of the network with one edge removed.

    This is an analytical contingency operation only.
    It does not modify the original adjacency dictionary.
    """
    result = {
        node: set(neighbors)
        for node, neighbors in adjacency.items()
    }

    if len(edge) < 2:
        return result

    node_a = _normalize_node(
        edge[0]
    )

    node_b = _normalize_node(
        edge[1]
    )

    if node_a in result:
        result[node_a].discard(
            node_b
        )

    if node_b in result:
        result[node_b].discard(
            node_a
        )

    return result


def edge_contingency_component_count(
    adjacency: dict[str, set[str]],
    edge: Sequence[Any],
) -> int:
    """
    Calculate the number of connected components after
    analytically removing one edge.
    """
    modified = network_after_edge_removal(
        adjacency,
        edge,
    )

    return component_count(
        modified
    )


def edge_is_critical(
    adjacency: dict[str, set[str]],
    edge: Sequence[Any],
) -> bool:
    """
    Determine whether removing an edge disconnects the
    network.

    Returns:
        True when the edge increases the component count.
    """
    before = component_count(
        adjacency
    )

    after = edge_contingency_component_count(
        adjacency,
        edge,
    )

    return after > before


def critical_edge_ratio(
    adjacency: dict[str, set[str]],
) -> float:
    """
    Calculate the fraction of network edges that are
    critical bridges.
    """
    return bridge_ratio(
        adjacency
    )


# ============================================================
# REDUNDANCY
# ============================================================


def network_redundancy_score(
    adjacency: dict[str, set[str]],
) -> float:
    """
    Estimate network structural redundancy.

    The score combines:

    - Network density
    - Largest-component ratio
    - Low bridge dependence

    Returns:
        Value between 0.0 and 1.0.

    This is an analytical feature, not a formal
    power-system reliability index.
    """
    density = network_density(
        adjacency
    )

    connectivity = largest_component_ratio(
        adjacency
    )

    bridge_dependence = bridge_ratio(
        adjacency
    )

    redundancy = (
        density * 0.35
        + connectivity * 0.45
        + (
            1.0 - bridge_dependence
        ) * 0.20
    )

    return max(
        0.0,
        min(
            1.0,
            redundancy,
        ),
    )


def network_fragility_score(
    adjacency: dict[str, set[str]],
) -> float:
    """
    Estimate structural network fragility.

    Higher values indicate:

    - More disconnected structure
    - Greater bridge dependence
    - More isolated nodes
    """
    connectivity_loss = (
        1.0
        - largest_component_ratio(
            adjacency
        )
    )

    bridge_dependence = bridge_ratio(
        adjacency
    )

    isolation = isolation_ratio(
        adjacency
    )

    fragility = (
        connectivity_loss * 0.45
        + bridge_dependence * 0.35
        + isolation * 0.20
    )

    return max(
        0.0,
        min(
            1.0,
            fragility,
        ),
    )


# ============================================================
# NETWORK RISK FEATURES
# ============================================================


def network_stress_score(
    average_loading_percent: float,
    overloaded_ratio: float,
    fragility_score: float,
    reserve_margin_percent: float,
) -> float:
    """
    Combine network-level stress indicators.

    Returns:
        Value between 0.0 and 1.0.

    This is a feature-engineering score and should not be
    used as a protection or control threshold.
    """
    average_loading = max(
        0.0,
        _safe_float(
            average_loading_percent
        ),
    )

    overload_ratio = max(
        0.0,
        min(
            1.0,
            _safe_float(
                overloaded_ratio
            ),
        ),
    )

    fragility = max(
        0.0,
        min(
            1.0,
            _safe_float(
                fragility_score
            ),
        ),
    )

    reserve_margin_value = _safe_float(
        reserve_margin_percent
    )

    loading_stress = min(
        1.0,
        average_loading / 100.0,
    )

    if reserve_margin_value <= 0.0:
        reserve_stress = 1.0
    else:
        reserve_stress = max(
            0.0,
            min(
                1.0,
                1.0
                - (
                    reserve_margin_value
                    / 100.0
                ),
            ),
        )

    score = (
        loading_stress * 0.30
        + overload_ratio * 0.30
        + fragility * 0.25
        + reserve_stress * 0.15
    )

    return max(
        0.0,
        min(
            1.0,
            score,
        ),
    )


# ============================================================
# COMPLETE NETWORK FEATURE EXTRACTION
# ============================================================


def extract_network_features(
    nodes: Iterable[Any],
    edges: Iterable[Sequence[Any]],
    loading_percentages: Sequence[Any] | None = None,
    current_load: float | None = None,
    available_capacity: float | None = None,
    overload_threshold_percent: float = 100.0,
    high_loading_threshold_percent: float = 80.0,
) -> dict[str, float | bool | int]:
    """
    Extract a standardized network feature set.

    Args:
        nodes:
            Network node identifiers.

        edges:
            Network edges represented as pairs.

        loading_percentages:
            Optional asset loading percentages.

        current_load:
            Optional current network load.

        available_capacity:
            Optional available generation/network capacity.

        overload_threshold_percent:
            Threshold used to identify overloaded assets.

        high_loading_threshold_percent:
            Threshold used to identify highly loaded assets.

    Returns:
        Dictionary containing network-level analytical features.
    """
    adjacency = build_adjacency(
        nodes,
        edges,
    )

    degree = degree_statistics(
        adjacency
    )

    components = component_count(
        adjacency
    )

    largest_component = (
        largest_component_ratio(
            adjacency
        )
    )

    isolated = isolation_ratio(
        adjacency
    )

    density = network_density(
        adjacency
    )

    bridges = bridge_count(
        adjacency
    )

    bridge_fraction = bridge_ratio(
        adjacency
    )

    redundancy = network_redundancy_score(
        adjacency
    )

    fragility = network_fragility_score(
        adjacency
    )

    if loading_percentages:
        avg_loading = average_loading(
            loading_percentages
        )

        max_load = maximum_loading(
            loading_percentages
        )

        overloaded = overloaded_asset_ratio(
            loading_percentages,
            overload_threshold_percent,
        )

        high_loading = high_loading_ratio(
            loading_percentages,
            high_loading_threshold_percent,
        )
    else:
        avg_loading = 0.0
        max_load = 0.0
        overloaded = 0.0
        high_loading = 0.0

    if (
        current_load is not None
        and available_capacity is not None
    ):
        utilization = capacity_utilization(
            current_load,
            available_capacity,
        )

        margin = reserve_margin(
            available_capacity,
            current_load,
        )
    else:
        utilization = 0.0
        margin = 0.0

    stress = network_stress_score(
        average_loading_percent=avg_loading,
        overloaded_ratio=overloaded,
        fragility_score=fragility,
        reserve_margin_percent=margin,
    )

    return {
        "node_count": node_count(
            adjacency
        ),
        "edge_count": edge_count(
            adjacency
        ),
        "component_count": components,
        "largest_component_ratio": largest_component,
        "isolated_node_ratio": isolated,
        "network_density": density,
        "minimum_degree": degree[
            "minimum_degree"
        ],
        "maximum_degree": degree[
            "maximum_degree"
        ],
        "average_degree": degree[
            "average_degree"
        ],
        "bridge_count": bridges,
        "bridge_ratio": bridge_fraction,
        "network_redundancy_score": redundancy,
        "network_fragility_score": fragility,
        "average_loading_percent": avg_loading,
        "maximum_loading_percent": max_load,
        "overloaded_asset_ratio": overloaded,
        "high_loading_asset_ratio": high_loading,
        "capacity_utilization_percent": utilization,
        "reserve_margin_percent": margin,
        "network_stress_score": stress,
        "network_is_connected": is_connected(
            adjacency
        ),
    }


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "build_adjacency",
    "node_count",
    "edge_count",
    "node_degree",
    "degree_statistics",
    "reachable_nodes",
    "is_connected",
    "connected_components",
    "component_count",
    "largest_component_ratio",
    "isolated_nodes",
    "isolation_ratio",
    "network_density",
    "shortest_path_length",
    "average_shortest_path_length",
    "bridge_count",
    "bridge_ratio",
    "overloaded_asset_ratio",
    "high_loading_ratio",
    "average_loading",
    "maximum_loading",
    "total_capacity",
    "capacity_utilization",
    "reserve_margin",
    "network_after_edge_removal",
    "edge_contingency_component_count",
    "edge_is_critical",
    "critical_edge_ratio",
    "network_redundancy_score",
    "network_fragility_score",
    "network_stress_score",
    "extract_network_features",
]