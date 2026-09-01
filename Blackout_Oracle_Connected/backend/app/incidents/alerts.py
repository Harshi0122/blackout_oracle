"""
Blackout Oracle - Incident Alert Utilities.

Provides deterministic utilities for creating, evaluating,
deduplicating, prioritizing, and summarizing alerts associated
with grid incidents.

This module is independent of the database layer and can be used
by API routes, incident detection, risk analysis, telemetry
processing, simulation workflows, and the AI agent.

This module does not directly control physical grid equipment.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ============================================================
# CONSTANTS
# ============================================================

VALID_SEVERITIES = {
    "info",
    "low",
    "medium",
    "high",
    "critical",
}

VALID_STATUSES = {
    "open",
    "acknowledged",
    "resolved",
    "dismissed",
}

SEVERITY_RANK = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


# ============================================================
# HELPERS
# ============================================================


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def _normalize_severity(
    severity: str,
) -> str:
    """Normalize an alert severity."""
    normalized = str(
        severity
    ).strip().lower()

    if normalized not in VALID_SEVERITIES:
        return "info"

    return normalized


def _normalize_status(
    status: str,
) -> str:
    """Normalize an alert status."""
    normalized = str(
        status
    ).strip().lower()

    if normalized not in VALID_STATUSES:
        return "open"

    return normalized


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# ALERT DATA STRUCTURE
# ============================================================


@dataclass
class IncidentAlert:
    """In-memory representation of an incident alert."""

    alert_id: str
    title: str
    message: str

    severity: str = "info"
    status: str = "open"

    incident_id: str | None = None
    asset_id: str | None = None
    region_id: str | None = None

    alert_type: str = "incident"
    source: str = "system"

    confidence: float = 0.0

    created_at: datetime = field(
        default_factory=_utc_now
    )

    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """Normalize alert fields after initialization."""
        self.alert_id = str(
            self.alert_id
        )

        self.title = str(
            self.title
        )

        self.message = str(
            self.message
        )

        self.severity = _normalize_severity(
            self.severity
        )

        self.status = _normalize_status(
            self.status
        )

        self.confidence = max(
            0.0,
            min(
                1.0,
                _safe_float(
                    self.confidence
                ),
            ),
        )

    @property
    def severity_rank(self) -> int:
        """Return the numeric severity ranking."""
        return SEVERITY_RANK[
            self.severity
        ]

    @property
    def is_active(self) -> bool:
        """Return True when the alert is currently active."""
        return self.status in {
            "open",
            "acknowledged",
        }

    @property
    def is_resolved(self) -> bool:
        """Return True when the alert is resolved."""
        return self.status == "resolved"

    def acknowledge(self) -> None:
        """Mark the alert as acknowledged."""
        if self.status == "resolved":
            return

        self.status = "acknowledged"

        if self.acknowledged_at is None:
            self.acknowledged_at = _utc_now()

    def resolve(self) -> None:
        """Mark the alert as resolved."""
        self.status = "resolved"

        if self.resolved_at is None:
            self.resolved_at = _utc_now()

    def dismiss(self) -> None:
        """Mark the alert as dismissed."""
        self.status = "dismissed"

        if self.resolved_at is None:
            self.resolved_at = _utc_now()

    def to_dict(self) -> dict[str, Any]:
        """Convert the alert into a JSON-compatible dictionary."""
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "status": self.status,
            "incident_id": self.incident_id,
            "asset_id": self.asset_id,
            "region_id": self.region_id,
            "alert_type": self.alert_type,
            "source": self.source,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "acknowledged_at": (
                self.acknowledged_at.isoformat()
                if self.acknowledged_at
                else None
            ),
            "resolved_at": (
                self.resolved_at.isoformat()
                if self.resolved_at
                else None
            ),
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# ALERT CREATION
# ============================================================


def create_alert(
    alert_id: Any,
    title: str,
    message: str,
    severity: str = "info",
    incident_id: Any | None = None,
    asset_id: Any | None = None,
    region_id: Any | None = None,
    alert_type: str = "incident",
    source: str = "system",
    confidence: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> IncidentAlert:
    """Create a new incident alert."""
    return IncidentAlert(
        alert_id=str(
            alert_id
        ),
        title=title,
        message=message,
        severity=severity,
        incident_id=(
            str(incident_id)
            if incident_id is not None
            else None
        ),
        asset_id=(
            str(asset_id)
            if asset_id is not None
            else None
        ),
        region_id=(
            str(region_id)
            if region_id is not None
            else None
        ),
        alert_type=alert_type,
        source=source,
        confidence=confidence,
        metadata=dict(
            metadata or {}
        ),
    )


# ============================================================
# SEVERITY
# ============================================================


def severity_from_risk_score(
    risk_score: float,
) -> str:
    """
    Convert a normalized risk score into alert severity.

    < 0.25 -> info
    < 0.50 -> low
    < 0.75 -> medium
    < 0.90 -> high
    >= 0.90 -> critical
    """
    score = max(
        0.0,
        min(
            1.0,
            _safe_float(
                risk_score
            ),
        ),
    )

    if score < 0.25:
        return "info"

    if score < 0.50:
        return "low"

    if score < 0.75:
        return "medium"

    if score < 0.90:
        return "high"

    return "critical"


def severity_from_loading(
    loading_percent: float,
) -> str:
    """Determine alert severity from asset loading."""
    loading = max(
        0.0,
        _safe_float(
            loading_percent
        ),
    )

    if loading < 70.0:
        return "info"

    if loading < 85.0:
        return "low"

    if loading < 100.0:
        return "medium"

    if loading < 120.0:
        return "high"

    return "critical"


def severity_from_probability(
    probability: float,
) -> str:
    """Determine severity from a normalized probability."""
    value = max(
        0.0,
        min(
            1.0,
            _safe_float(
                probability
            ),
        ),
    )

    if value < 0.25:
        return "info"

    if value < 0.50:
        return "low"

    if value < 0.75:
        return "medium"

    if value < 0.90:
        return "high"

    return "critical"


# ============================================================
# PRIORITY
# ============================================================


def calculate_alert_priority(
    severity: str,
    confidence: float = 1.0,
    asset_criticality: float = 0.0,
    affected_load_mw: float = 0.0,
) -> float:
    """
    Calculate a normalized alert priority.

    Severity          40%
    Confidence        20%
    Asset criticality 25%
    Affected load     15%
    """
    normalized_severity = _normalize_severity(
        severity
    )

    severity_score = (
        SEVERITY_RANK[
            normalized_severity
        ]
        / 4.0
    )

    confidence_score = max(
        0.0,
        min(
            1.0,
            _safe_float(
                confidence
            ),
        ),
    )

    criticality_score = max(
        0.0,
        min(
            1.0,
            _safe_float(
                asset_criticality
            ),
        ),
    )

    load_score = max(
        0.0,
        min(
            1.0,
            _safe_float(
                affected_load_mw
            )
            / 1000.0,
        ),
    )

    return (
        severity_score * 0.40
        + confidence_score * 0.20
        + criticality_score * 0.25
        + load_score * 0.15
    )


def alert_priority_level(
    priority: float,
) -> str:
    """Convert an alert priority score into a priority level."""
    value = max(
        0.0,
        min(
            1.0,
            _safe_float(
                priority
            ),
        ),
    )

    if value < 0.25:
        return "low"

    if value < 0.50:
        return "normal"

    if value < 0.75:
        return "high"

    return "urgent"


# ============================================================
# DEDUPLICATION
# ============================================================


def alert_fingerprint(
    alert: IncidentAlert,
) -> str:
    """Generate a deterministic fingerprint for an alert."""
    parts = (
        alert.alert_type,
        alert.incident_id or "",
        alert.asset_id or "",
        alert.region_id or "",
        alert.title.strip().lower(),
        alert.message.strip().lower(),
    )

    return "|".join(
        parts
    )


def alerts_are_similar(
    first: IncidentAlert,
    second: IncidentAlert,
) -> bool:
    """Determine whether two alerts represent the same condition."""
    return (
        alert_fingerprint(first)
        == alert_fingerprint(second)
    )


def deduplicate_alerts(
    alerts: Iterable[IncidentAlert],
) -> list[IncidentAlert]:
    """Remove duplicate alerts while preserving order."""
    unique: list[IncidentAlert] = []

    fingerprints: set[str] = set()

    for alert in alerts:
        fingerprint = alert_fingerprint(
            alert
        )

        if fingerprint in fingerprints:
            continue

        fingerprints.add(
            fingerprint
        )

        unique.append(
            alert
        )

    return unique


# ============================================================
# FILTERING
# ============================================================


def filter_alerts_by_severity(
    alerts: Iterable[IncidentAlert],
    minimum_severity: str,
) -> list[IncidentAlert]:
    """Return alerts at or above the requested severity."""
    severity = _normalize_severity(
        minimum_severity
    )

    minimum_rank = SEVERITY_RANK[
        severity
    ]

    return [
        alert
        for alert in alerts
        if alert.severity_rank
        >= minimum_rank
    ]


def filter_active_alerts(
    alerts: Iterable[IncidentAlert],
) -> list[IncidentAlert]:
    """Return only active alerts."""
    return [
        alert
        for alert in alerts
        if alert.is_active
    ]


def filter_alerts_for_incident(
    alerts: Iterable[IncidentAlert],
    incident_id: Any,
) -> list[IncidentAlert]:
    """Return alerts associated with an incident."""
    normalized = str(
        incident_id
    )

    return [
        alert
        for alert in alerts
        if alert.incident_id
        == normalized
    ]


def filter_alerts_for_asset(
    alerts: Iterable[IncidentAlert],
    asset_id: Any,
) -> list[IncidentAlert]:
    """Return alerts associated with an asset."""
    normalized = str(
        asset_id
    )

    return [
        alert
        for alert in alerts
        if alert.asset_id
        == normalized
    ]


# ============================================================
# SORTING
# ============================================================


def sort_alerts_by_priority(
    alerts: Iterable[IncidentAlert],
    descending: bool = True,
) -> list[IncidentAlert]:
    """Sort alerts by severity and confidence."""
    return sorted(
        alerts,
        key=lambda alert: (
            alert.severity_rank,
            alert.confidence,
        ),
        reverse=descending,
    )


def sort_alerts_by_time(
    alerts: Iterable[IncidentAlert],
    descending: bool = True,
) -> list[IncidentAlert]:
    """Sort alerts by creation time."""
    return sorted(
        alerts,
        key=lambda alert: alert.created_at,
        reverse=descending,
    )


# ============================================================
# ESCALATION
# ============================================================


def should_escalate_alert(
    alert: IncidentAlert,
    risk_score: float | None = None,
    loading_percent: float | None = None,
    asset_criticality: float | None = None,
) -> bool:
    """
    Determine whether an alert should be escalated.

    This function only determines analytical escalation.
    It does not send notifications or execute controls.
    """
    if alert.severity in {
        "high",
        "critical",
    }:
        return True

    if (
        risk_score is not None
        and _safe_float(
            risk_score
        ) >= 0.75
    ):
        return True

    if (
        loading_percent is not None
        and _safe_float(
            loading_percent
        ) >= 100.0
    ):
        return True

    if (
        asset_criticality is not None
        and _safe_float(
            asset_criticality
        ) >= 0.80
    ):
        return True

    return False


def escalate_alert(
    alert: IncidentAlert,
) -> IncidentAlert:
    """Return a copy of the alert with one-level higher severity."""
    severity_order = (
        "info",
        "low",
        "medium",
        "high",
        "critical",
    )

    current_index = severity_order.index(
        alert.severity
    )

    next_index = min(
        current_index + 1,
        len(severity_order) - 1,
    )

    return IncidentAlert(
        alert_id=alert.alert_id,
        title=alert.title,
        message=alert.message,
        severity=severity_order[
            next_index
        ],
        status=alert.status,
        incident_id=alert.incident_id,
        asset_id=alert.asset_id,
        region_id=alert.region_id,
        alert_type=alert.alert_type,
        source=alert.source,
        confidence=alert.confidence,
        created_at=alert.created_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
        metadata=dict(
            alert.metadata
        ),
    )


# ============================================================
# CORRELATION
# ============================================================


def correlate_alerts(
    alerts: Iterable[IncidentAlert],
) -> dict[str, list[IncidentAlert]]:
    """Group alerts by incident ID."""
    groups: dict[
        str,
        list[IncidentAlert],
    ] = {}

    for alert in alerts:
        key = (
            alert.incident_id
            or "unassigned"
        )

        groups.setdefault(
            key,
            [],
        ).append(
            alert
        )

    return groups


def correlate_by_asset(
    alerts: Iterable[IncidentAlert],
) -> dict[str, list[IncidentAlert]]:
    """Group alerts by asset ID."""
    groups: dict[
        str,
        list[IncidentAlert],
    ] = {}

    for alert in alerts:
        key = (
            alert.asset_id
            or "unassigned"
        )

        groups.setdefault(
            key,
            [],
        ).append(
            alert
        )

    return groups


# ============================================================
# SUMMARY
# ============================================================


def alert_summary(
    alerts: Iterable[IncidentAlert],
) -> dict[str, Any]:
    """Generate a summary of a collection of alerts."""
    alert_list = list(
        alerts
    )

    severity_counts = {
        severity: 0
        for severity in VALID_SEVERITIES
    }

    status_counts = {
        status: 0
        for status in VALID_STATUSES
    }

    for alert in alert_list:
        severity_counts[
            alert.severity
        ] += 1

        status_counts[
            alert.status
        ] += 1

    active_count = sum(
        alert.is_active
        for alert in alert_list
    )

    highest_severity = "info"

    if alert_list:
        highest = max(
            alert_list,
            key=lambda alert: alert.severity_rank,
        )

        highest_severity = (
            highest.severity
        )

    average_confidence = (
        sum(
            alert.confidence
            for alert in alert_list
        )
        / len(alert_list)
        if alert_list
        else 0.0
    )

    return {
        "total_alerts": len(
            alert_list
        ),
        "active_alerts": active_count,
        "severity_counts": severity_counts,
        "status_counts": status_counts,
        "highest_severity": highest_severity,
        "average_confidence": average_confidence,
    }


# ============================================================
# ALERT GENERATORS
# ============================================================


def generate_risk_alert(
    alert_id: Any,
    risk_score: float,
    asset_id: Any | None = None,
    incident_id: Any | None = None,
    region_id: Any | None = None,
    confidence: float = 1.0,
) -> IncidentAlert:
    """Generate an alert from a normalized risk score."""
    severity = severity_from_risk_score(
        risk_score
    )

    normalized_score = max(
        0.0,
        min(
            1.0,
            _safe_float(
                risk_score
            ),
        ),
    )

    score_percent = (
        normalized_score
        * 100.0
    )

    return create_alert(
        alert_id=alert_id,
        title="Grid risk detected",
        message=(
            f"Current analytical risk score "
            f"is {score_percent:.1f}%."
        ),
        severity=severity,
        incident_id=incident_id,
        asset_id=asset_id,
        region_id=region_id,
        alert_type="risk",
        source="risk_engine",
        confidence=confidence,
        metadata={
            "risk_score": normalized_score,
        },
    )


def generate_overload_alert(
    alert_id: Any,
    loading_percent: float,
    asset_id: Any | None = None,
    incident_id: Any | None = None,
    region_id: Any | None = None,
) -> IncidentAlert:
    """Generate an alert from an asset loading condition."""
    severity = severity_from_loading(
        loading_percent
    )

    loading = max(
        0.0,
        _safe_float(
            loading_percent
        ),
    )

    return create_alert(
        alert_id=alert_id,
        title="Grid asset loading condition",
        message=(
            f"Observed loading is "
            f"{loading:.1f}%."
        ),
        severity=severity,
        incident_id=incident_id,
        asset_id=asset_id,
        region_id=region_id,
        alert_type="overload",
        source="telemetry",
        confidence=1.0,
        metadata={
            "loading_percent": loading,
        },
    )


def generate_prediction_alert(
    alert_id: Any,
    probability: float,
    event_type: str = "grid event",
    asset_id: Any | None = None,
    incident_id: Any | None = None,
    region_id: Any | None = None,
    confidence: float | None = None,
) -> IncidentAlert:
    """Generate an alert from predictive model output."""
    normalized_probability = max(
        0.0,
        min(
            1.0,
            _safe_float(
                probability
            ),
        ),
    )

    severity = severity_from_probability(
        normalized_probability
    )

    probability_percent = (
        normalized_probability
        * 100.0
    )

    return create_alert(
        alert_id=alert_id,
        title=f"Potential {event_type} detected",
        message=(
            f"Predictive analysis estimates a "
            f"{probability_percent:.1f}% probability "
            f"of the specified event."
        ),
        severity=severity,
        incident_id=incident_id,
        asset_id=asset_id,
        region_id=region_id,
        alert_type="prediction",
        source="prediction_engine",
        confidence=(
            normalized_probability
            if confidence is None
            else confidence
        ),
        metadata={
            "probability": normalized_probability,
            "event_type": event_type,
        },
    )


# ============================================================
# BATCH PROCESSING
# ============================================================


def process_alerts(
    alerts: Iterable[IncidentAlert],
    minimum_severity: str = "info",
    active_only: bool = False,
    deduplicate: bool = True,
) -> list[IncidentAlert]:
    """
    Process alerts through filtering, deduplication,
    and priority sorting.
    """
    processed = list(
        alerts
    )

    if active_only:
        processed = filter_active_alerts(
            processed
        )

    processed = filter_alerts_by_severity(
        processed,
        minimum_severity,
    )

    if deduplicate:
        processed = deduplicate_alerts(
            processed
        )

    return sort_alerts_by_priority(
        processed
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "IncidentAlert",
    "create_alert",
    "severity_from_risk_score",
    "severity_from_loading",
    "severity_from_probability",
    "calculate_alert_priority",
    "alert_priority_level",
    "alert_fingerprint",
    "alerts_are_similar",
    "deduplicate_alerts",
    "filter_alerts_by_severity",
    "filter_active_alerts",
    "filter_alerts_for_incident",
    "filter_alerts_for_asset",
    "sort_alerts_by_priority",
    "sort_alerts_by_time",
    "should_escalate_alert",
    "escalate_alert",
    "correlate_alerts",
    "correlate_by_asset",
    "alert_summary",
    "generate_risk_alert",
    "generate_overload_alert",
    "generate_prediction_alert",
    "process_alerts",
]