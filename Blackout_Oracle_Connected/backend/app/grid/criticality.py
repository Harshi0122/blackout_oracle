"""
Blackout Oracle - Grid Criticality Analysis.

Provides deterministic methods for evaluating the criticality
of grid assets and network elements.

Criticality features can be used by:

- Risk scoring
- Contingency analysis
- Blackout prediction
- Cascading-failure analysis
- Grid simulations
- AI investigation

This module performs analytical calculations only.
It does not issue commands to physical grid equipment.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from typing import Any


# ============================================================
# CONSTANTS
# ============================================================

EPSILON = 1e-9

DEFAULT_LOADING_WEIGHT = 0.30
DEFAULT_CONNECTIVITY_WEIGHT = 0.30
DEFAULT_CAPACITY_WEIGHT = 0.20
DEFAULT_OUTAGE_WEIGHT = 0.20


# ============================================================
# BASIC HELPERS
# ============================================================


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Safely convert a value to float.

    Invalid, NaN, and infinite values are replaced by
    the supplied default.
    """
    try:
        result = float(value)

        if not math.isfinite(result):
            return default

        return result

    except (TypeError, ValueError):
        return default


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
        min(maximum, value),
    )


# ============================================================
# LOADING CRITICALITY
# ============================================================


def loading_criticality(
    loading_percent: float,
) -> float:
    """
    Convert asset loading into a normalized criticality score.

    Loading at or below 50% produces low criticality.
    Criticality increases as loading approaches and exceeds
    100%.

    Returns:
        Value between 0.0 and 1.0.
    """
    loading = max(
        0.0,
        _safe_float(loading_percent),
    )

    if loading <= 50.0:
        return 0.0

    if loading >= 100.0:
        return 1.0

    return _clamp(
        (loading - 50.0) / 50.0
    )


def overload_severity(
    loading_percent: float,
) -> float:
    """
    Calculate the severity of an overload condition.

    Returns:
        Value between 0.0 and 1.0.
    """
    loading = max(
        0.0,
        _safe_float(loading_percent),
    )

    if loading <= 100.0:
        return 0.0

    return _clamp(
        (loading - 100.0) / 50.0
    )


# ============================================================
# CONNECTIVITY CRITICALITY
# ============================================================


def connectivity_criticality(
    connected_nodes: int,
    total_nodes: int,
) -> float:
    """
    Estimate criticality based on the number of nodes that
    depend on an asset or network element.

    Args:
        connected_nodes:
            Number of directly or analytically dependent nodes.

        total_nodes:
            Total number of relevant network nodes.

    Returns:
        Value between 0.0 and 1.0.
    """
    connected = max(
        0,
        int(connected_nodes),
    )

    total = max(
        0,
        int(total_nodes),
    )

    if total == 0:
        return 0.0

    return _clamp(
        connected / total
    )


def degree_criticality(
    degree: int,
    maximum_degree: int,
) -> float:
    """
    Estimate node criticality from network degree.

    A higher degree means the node is connected to more
    network elements.

    Returns:
        Value between 0.0 and 1.0.
    """
    current_degree = max(
        0,
        int(degree),
    )

    maximum = max(
        0,
        int(maximum_degree),
    )

    if maximum == 0:
        return 0.0

    return _clamp(
        current_degree / maximum
    )


# ============================================================
# CAPACITY CRITICALITY
# ============================================================


def capacity_criticality(
    capacity: float,
    total_network_capacity: float,
) -> float:
    """
    Estimate how significant an asset's capacity is relative
    to the total network capacity.

    Returns:
        Value between 0.0 and 1.0.
    """
    asset_capacity = max(
        0.0,
        _safe_float(capacity),
    )

    total_capacity = _safe_float(
        total_network_capacity
    )

    if total_capacity <= EPSILON:
        return 0.0

    return _clamp(
        asset_capacity / total_capacity
    )


def capacity_loss_ratio(
    capacity: float,
    total_capacity: float,
) -> float:
    """
    Estimate the percentage of total capacity that would be
    lost if an asset became unavailable.

    Returns:
        Value between 0.0 and 1.0.
    """
    return capacity_criticality(
        capacity,
        total_capacity,
    )


# ============================================================
# OUTAGE HISTORY CRITICALITY
# ============================================================


def outage_frequency_score(
    outage_count: int,
    observation_count: int,
) -> float:
    """
    Estimate historical outage frequency.

    Returns:
        Value between 0.0 and 1.0.
    """
    outages = max(
        0,
        int(outage_count),
    )

    observations = max(
        0,
        int(observation_count),
    )

    if observations == 0:
        return 0.0

    return _clamp(
        outages / observations
    )


def outage_duration_score(
    outage_duration_minutes: float,
    reference_duration_minutes: float = 60.0,
) -> float:
    """
    Convert outage duration into a normalized severity score.

    Returns:
        Value between 0.0 and 1.0.
    """
    duration = max(
        0.0,
        _safe_float(
            outage_duration_minutes
        ),
    )

    reference = max(
        EPSILON,
        _safe_float(
            reference_duration_minutes,
            60.0,
        ),
    )

    return _clamp(
        duration / reference
    )


# ============================================================
# DEPENDENCY CRITICALITY
# ============================================================


def dependent_load_ratio(
    dependent_load_mw: float,
    total_load_mw: float,
) -> float:
    """
    Calculate the fraction of total load dependent on an asset.

    Returns:
        Value between 0.0 and 1.0.
    """
    dependent = max(
        0.0,
        _safe_float(
            dependent_load_mw
        ),
    )

    total = _safe_float(
        total_load_mw
    )

    if total <= EPSILON:
        return 0.0

    return _clamp(
        dependent / total
    )


def customer_dependency_ratio(
    dependent_customers: int,
    total_customers: int,
) -> float:
    """
    Calculate the fraction of customers dependent on an asset.

    Returns:
        Value between 0.0 and 1.0.
    """
    dependent = max(
        0,
        int(dependent_customers),
    )

    total = max(
        0,
        int(total_customers),
    )

    if total == 0:
        return 0.0

    return _clamp(
        dependent / total
    )


# ============================================================
# REDUNDANCY
# ============================================================


def redundancy_score(
    alternative_paths: int,
    maximum_alternative_paths: int = 3,
) -> float:
    """
    Calculate normalized network redundancy.

    More alternative paths generally indicate that the network
    has more structural alternatives if one connection fails.

    Returns:
        Value between 0.0 and 1.0.

    This is an analytical topology feature and is not a formal
    reliability index.
    """
    paths = max(
        0,
        int(alternative_paths),
    )

    maximum = max(
        1,
        int(maximum_alternative_paths),
    )

    return _clamp(
        paths / maximum
    )


def redundancy_criticality(
    alternative_paths: int,
    maximum_alternative_paths: int = 3,
) -> float:
    """
    Convert redundancy into criticality.

    Fewer alternative paths means greater criticality.
    """
    return 1.0 - redundancy_score(
        alternative_paths,
        maximum_alternative_paths,
    )


# ============================================================
# SINGLE-POINT-OF-FAILURE FEATURES
# ============================================================


def single_point_of_failure_score(
    is_single_point_of_failure: bool,
) -> float:
    """
    Convert a single-point-of-failure indicator into a score.
    """
    return 1.0 if is_single_point_of_failure else 0.0


def bridge_criticality(
    is_bridge: bool,
) -> float:
    """
    Convert bridge status into a criticality score.
    """
    return 1.0 if is_bridge else 0.0


# ============================================================
# COMBINED CRITICALITY
# ============================================================


def asset_criticality_score(
    loading_score: float = 0.0,
    connectivity_score: float = 0.0,
    capacity_score: float = 0.0,
    outage_score: float = 0.0,
    dependency_score: float = 0.0,
    redundancy_criticality_score: float = 0.0,
    single_point_score: float = 0.0,
    bridge_score: float = 0.0,
) -> float:
    """
    Calculate an overall asset criticality score.

    The score combines:

        Loading                 20%
        Connectivity            15%
        Capacity                15%
        Historical outages      10%
        Load/customer dependency 15%
        Low redundancy          10%
        Single point of failure 10%
        Bridge status             5%

    Returns:
        Value between 0.0 and 1.0.

    This is an analytical ranking score. It should not be
    interpreted as a protection setting or an automatic
    operational command.
    """
    loading = _clamp(
        _safe_float(
            loading_score
        )
    )

    connectivity = _clamp(
        _safe_float(
            connectivity_score
        )
    )

    capacity = _clamp(
        _safe_float(
            capacity_score
        )
    )

    outage = _clamp(
        _safe_float(
            outage_score
        )
    )

    dependency = _clamp(
        _safe_float(
            dependency_score
        )
    )

    redundancy = _clamp(
        _safe_float(
            redundancy_criticality_score
        )
    )

    single_point = _clamp(
        _safe_float(
            single_point_score
        )
    )

    bridge = _clamp(
        _safe_float(
            bridge_score
        )
    )

    score = (
        loading * 0.20
        + connectivity * 0.15
        + capacity * 0.15
        + outage * 0.10
        + dependency * 0.15
        + redundancy * 0.10
        + single_point * 0.10
        + bridge * 0.05
    )

    return _clamp(score)


# ============================================================
# CRITICALITY CLASSIFICATION
# ============================================================


def criticality_level(
    score: float,
) -> str:
    """
    Convert a criticality score into a human-readable level.

    Returns:

        "low"
        "moderate"
        "high"
        "critical"
    """
    value = _clamp(
        _safe_float(score)
    )

    if value < 0.25:
        return "low"

    if value < 0.50:
        return "moderate"

    if value < 0.75:
        return "high"

    return "critical"


# ============================================================
# NETWORK-LEVEL CRITICALITY
# ============================================================


def network_criticality_score(
    critical_asset_ratio: float,
    overloaded_asset_ratio: float,
    bridge_ratio: float,
    network_fragility: float,
) -> float:
    """
    Calculate a normalized network-level criticality score.

    Args:
        critical_asset_ratio:
            Fraction of assets classified as critical.

        overloaded_asset_ratio:
            Fraction of assets currently overloaded.

        bridge_ratio:
            Fraction of network edges that are bridges.

        network_fragility:
            Structural fragility score.

    Returns:
        Value between 0.0 and 1.0.
    """
    critical_assets = _clamp(
        _safe_float(
            critical_asset_ratio
        )
    )

    overloaded = _clamp(
        _safe_float(
            overloaded_asset_ratio
        )
    )

    bridges = _clamp(
        _safe_float(
            bridge_ratio
        )
    )

    fragility = _clamp(
        _safe_float(
            network_fragility
        )
    )

    score = (
        critical_assets * 0.25
        + overloaded * 0.30
        + bridges * 0.20
        + fragility * 0.25
    )

    return _clamp(score)


# ============================================================
# ASSET RANKING
# ============================================================


def rank_assets_by_criticality(
    assets: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Rank assets by their supplied criticality score.

    Each asset dictionary should contain:

        id
        criticality_score

    Missing scores default to zero.

    The returned list is a new list and does not modify the
    original input.
    """
    asset_list = [
        dict(asset)
        for asset in assets
    ]

    asset_list.sort(
        key=lambda asset: _safe_float(
            asset.get(
                "criticality_score",
                0.0,
            )
        ),
        reverse=True,
    )

    return asset_list


# ============================================================
# COMPLETE ASSET CRITICALITY
# ============================================================


def calculate_asset_criticality(
    *,
    loading_percent: float = 0.0,
    connected_nodes: int = 0,
    total_nodes: int = 0,
    capacity: float = 0.0,
    total_network_capacity: float = 0.0,
    outage_count: int = 0,
    observation_count: int = 0,
    dependent_load_mw: float = 0.0,
    total_load_mw: float = 0.0,
    alternative_paths: int = 0,
    maximum_alternative_paths: int = 3,
    is_single_point_of_failure: bool = False,
    is_bridge: bool = False,
) -> dict[str, float | str | bool]:
    """
    Calculate a complete criticality feature set for an asset.

    Returns:
        Dictionary containing individual criticality features,
        overall score, and criticality level.
    """
    loading_score = loading_criticality(
        loading_percent
    )

    connectivity_score = connectivity_criticality(
        connected_nodes,
        total_nodes,
    )

    capacity_score = capacity_criticality(
        capacity,
        total_network_capacity,
    )

    outage_score = outage_frequency_score(
        outage_count,
        observation_count,
    )

    dependency_score = dependent_load_ratio(
        dependent_load_mw,
        total_load_mw,
    )

    redundancy_score_value = redundancy_criticality(
        alternative_paths,
        maximum_alternative_paths,
    )

    single_point_score = single_point_of_failure_score(
        is_single_point_of_failure
    )

    bridge_score = bridge_criticality(
        is_bridge
    )

    overall_score = asset_criticality_score(
        loading_score=loading_score,
        connectivity_score=connectivity_score,
        capacity_score=capacity_score,
        outage_score=outage_score,
        dependency_score=dependency_score,
        redundancy_criticality_score=redundancy_score_value,
        single_point_score=single_point_score,
        bridge_score=bridge_score,
    )

    return {
        "loading_criticality": loading_score,
        "connectivity_criticality": connectivity_score,
        "capacity_criticality": capacity_score,
        "outage_frequency_score": outage_score,
        "dependency_criticality": dependency_score,
        "redundancy_criticality": redundancy_score_value,
        "single_point_of_failure_score": single_point_score,
        "bridge_criticality": bridge_score,
        "overload_severity": overload_severity(
            loading_percent
        ),
        "capacity_loss_ratio": capacity_loss_ratio(
            capacity,
            total_network_capacity,
        ),
        "criticality_score": overall_score,
        "criticality_level": criticality_level(
            overall_score
        ),
        "is_single_point_of_failure": bool(
            is_single_point_of_failure
        ),
        "is_bridge": bool(
            is_bridge
        ),
    }


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "loading_criticality",
    "overload_severity",
    "connectivity_criticality",
    "degree_criticality",
    "capacity_criticality",
    "capacity_loss_ratio",
    "outage_frequency_score",
    "outage_duration_score",
    "dependent_load_ratio",
    "customer_dependency_ratio",
    "redundancy_score",
    "redundancy_criticality",
    "single_point_of_failure_score",
    "bridge_criticality",
    "asset_criticality_score",
    "criticality_level",
    "network_criticality_score",
    "rank_assets_by_criticality",
    "calculate_asset_criticality",
]