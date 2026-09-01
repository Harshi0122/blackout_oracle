"""
Blackout Oracle - Incident Manager.

Provides lifecycle management for grid incidents.

Responsibilities:

- Create incidents
- Track incident state
- Associate incidents with assets
- Attach alerts to incidents
- Update incident severity
- Acknowledge incidents
- Resolve incidents
- Dismiss incidents
- Search and filter incidents
- Generate incident summaries
- Detect active/high-priority incidents

This module is independent of the database layer.
Database persistence can be handled by the repository layer.

This module does not directly control physical grid equipment.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.incidents.alerts import (
    IncidentAlert,
    alert_fingerprint,
    create_alert,
    severity_from_loading,
    severity_from_probability,
    severity_from_risk_score,
)


# ============================================================
# CONSTANTS
# ============================================================

VALID_INCIDENT_STATUSES = {
    "detected",
    "investigating",
    "acknowledged",
    "mitigating",
    "resolved",
    "dismissed",
}

VALID_INCIDENT_TYPES = {
    "unknown",
    "overload",
    "voltage_anomaly",
    "frequency_anomaly",
    "equipment_failure",
    "line_failure",
    "transformer_failure",
    "feeder_failure",
    "generator_failure",
    "substation_failure",
    "weather_event",
    "communication_failure",
    "cascading_failure",
    "power_quality",
    "blackout",
    "prediction",
    "other",
}

SEVERITY_ORDER = (
    "info",
    "low",
    "medium",
    "high",
    "critical",
)

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
    """Normalize an incident severity."""
    value = str(
        severity
    ).strip().lower()

    if value not in SEVERITY_RANK:
        return "info"

    return value


def _normalize_status(
    status: str,
) -> str:
    """Normalize an incident status."""
    value = str(
        status
    ).strip().lower()

    if value not in VALID_INCIDENT_STATUSES:
        return "detected"

    return value


def _normalize_type(
    incident_type: str,
) -> str:
    """Normalize an incident type."""
    value = str(
        incident_type
    ).strip().lower()

    if value not in VALID_INCIDENT_TYPES:
        return "other"

    return value


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
# INCIDENT DATA STRUCTURE
# ============================================================


@dataclass
class Incident:
    """
    In-memory representation of a grid incident.
    """

    incident_id: str
    title: str
    description: str

    incident_type: str = "unknown"
    severity: str = "info"
    status: str = "detected"

    asset_id: str | None = None
    region_id: str | None = None

    source: str = "system"
    confidence: float = 0.0

    detected_at: datetime = field(
        default_factory=_utc_now
    )

    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None

    alerts: list[IncidentAlert] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """Normalize incident fields."""
        self.incident_id = str(
            self.incident_id
        )

        self.title = str(
            self.title
        )

        self.description = str(
            self.description
        )

        self.incident_type = _normalize_type(
            self.incident_type
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
        """Return True when the incident is active."""
        return self.status not in {
            "resolved",
            "dismissed",
        }

    @property
    def is_resolved(self) -> bool:
        """Return True when the incident is resolved."""
        return self.status == "resolved"

    @property
    def alert_count(self) -> int:
        """Return the number of attached alerts."""
        return len(
            self.alerts
        )

    @property
    def active_alert_count(self) -> int:
        """Return the number of active alerts."""
        return sum(
            alert.is_active
            for alert in self.alerts
        )

    def acknowledge(self) -> None:
        """Acknowledge the incident."""
        if self.is_resolved:
            return

        self.status = "acknowledged"

        if self.acknowledged_at is None:
            self.acknowledged_at = _utc_now()

        for alert in self.alerts:
            if alert.is_active:
                alert.acknowledge()

    def start_investigation(self) -> None:
        """Move the incident into investigation."""
        if self.is_resolved:
            return

        self.status = "investigating"

    def start_mitigation(self) -> None:
        """Move the incident into mitigation."""
        if self.is_resolved:
            return

        self.status = "mitigating"

    def resolve(self) -> None:
        """Resolve the incident."""
        self.status = "resolved"

        if self.resolved_at is None:
            self.resolved_at = _utc_now()

        for alert in self.alerts:
            if alert.is_active:
                alert.resolve()

    def dismiss(self) -> None:
        """Dismiss the incident."""
        self.status = "dismissed"

        if self.resolved_at is None:
            self.resolved_at = _utc_now()

        for alert in self.alerts:
            if alert.is_active:
                alert.dismiss()

    def add_alert(
        self,
        alert: IncidentAlert,
    ) -> bool:
        """
        Attach an alert to the incident.

        Returns:
            True when the alert was added.
            False when an equivalent alert already exists.
        """
        for existing in self.alerts:
            if (
                alert_fingerprint(existing)
                == alert_fingerprint(alert)
            ):
                return False

        if alert.incident_id is None:
            alert.incident_id = self.incident_id

        self.alerts.append(
            alert
        )

        if (
            alert.severity_rank
            > self.severity_rank
        ):
            self.severity = alert.severity

        return True

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Convert the incident to a JSON-compatible dictionary."""
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "description": self.description,
            "incident_type": self.incident_type,
            "severity": self.severity,
            "status": self.status,
            "asset_id": self.asset_id,
            "region_id": self.region_id,
            "source": self.source,
            "confidence": self.confidence,
            "detected_at": self.detected_at.isoformat(),
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
            "alert_count": self.alert_count,
            "active_alert_count": (
                self.active_alert_count
            ),
            "alerts": [
                alert.to_dict()
                for alert in self.alerts
            ],
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# INCIDENT CREATION
# ============================================================


def create_incident(
    incident_id: Any,
    title: str,
    description: str,
    incident_type: str = "unknown",
    severity: str = "info",
    status: str = "detected",
    asset_id: Any | None = None,
    region_id: Any | None = None,
    source: str = "system",
    confidence: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> Incident:
    """
    Create a new incident.
    """
    return Incident(
        incident_id=str(
            incident_id
        ),
        title=title,
        description=description,
        incident_type=incident_type,
        severity=severity,
        status=status,
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
        source=source,
        confidence=confidence,
        metadata=dict(
            metadata or {}
        ),
    )


# ============================================================
# INCIDENT MANAGER
# ============================================================


class IncidentManager:
    """
    In-memory incident lifecycle manager.

    This class acts as the coordination layer between incident
    detection and persistence.

    It does not directly depend on SQLAlchemy.
    """

    def __init__(
        self,
        incidents: Iterable[Incident] | None = None,
    ) -> None:
        """Initialize the incident manager."""
        self.incidents: dict[
            str,
            Incident,
        ] = {}

        if incidents is not None:
            for incident in incidents:
                self.add_incident(
                    incident
                )

    # ========================================================
    # BASIC OPERATIONS
    # ========================================================

    def add_incident(
        self,
        incident: Incident,
    ) -> None:
        """Add or replace an incident."""
        incident_id = str(
            incident.incident_id
        )

        incident.incident_id = incident_id

        self.incidents[
            incident_id
        ] = incident

    def create(
        self,
        incident_id: Any,
        title: str,
        description: str,
        incident_type: str = "unknown",
        severity: str = "info",
        asset_id: Any | None = None,
        region_id: Any | None = None,
        source: str = "system",
        confidence: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> Incident:
        """
        Create and register a new incident.
        """
        incident = create_incident(
            incident_id=incident_id,
            title=title,
            description=description,
            incident_type=incident_type,
            severity=severity,
            asset_id=asset_id,
            region_id=region_id,
            source=source,
            confidence=confidence,
            metadata=metadata,
        )

        self.add_incident(
            incident
        )

        return incident

    def remove(
        self,
        incident_id: Any,
    ) -> bool:
        """Remove an incident from the manager."""
        normalized = str(
            incident_id
        )

        if normalized not in self.incidents:
            return False

        del self.incidents[
            normalized
        ]

        return True

    def get(
        self,
        incident_id: Any,
    ) -> Incident | None:
        """Retrieve an incident."""
        return self.incidents.get(
            str(incident_id)
        )

    def exists(
        self,
        incident_id: Any,
    ) -> bool:
        """Check whether an incident exists."""
        return str(
            incident_id
        ) in self.incidents

    def count(self) -> int:
        """Return the number of incidents."""
        return len(
            self.incidents
        )

    # ========================================================
    # ALERT MANAGEMENT
    # ========================================================

    def attach_alert(
        self,
        incident_id: Any,
        alert: IncidentAlert,
    ) -> bool:
        """Attach an alert to an existing incident."""
        incident = self.get(
            incident_id
        )

        if incident is None:
            return False

        return incident.add_alert(
            alert
        )

    def create_alert_for_incident(
        self,
        incident_id: Any,
        alert_id: Any,
        title: str,
        message: str,
        severity: str = "info",
        asset_id: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> IncidentAlert | None:
        """
        Create and attach an alert to an incident.
        """
        incident = self.get(
            incident_id
        )

        if incident is None:
            return None

        alert = create_alert(
            alert_id=alert_id,
            title=title,
            message=message,
            severity=severity,
            incident_id=incident.incident_id,
            asset_id=(
                asset_id
                if asset_id is not None
                else incident.asset_id
            ),
            region_id=incident.region_id,
            alert_type="incident",
            source=incident.source,
            confidence=incident.confidence,
            metadata=metadata,
        )

        if not incident.add_alert(
            alert
        ):
            return None

        return alert

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def acknowledge(
        self,
        incident_id: Any,
    ) -> bool:
        """Acknowledge an incident."""
        incident = self.get(
            incident_id
        )

        if incident is None:
            return False

        incident.acknowledge()

        return True

    def investigate(
        self,
        incident_id: Any,
    ) -> bool:
        """Move an incident into investigation."""
        incident = self.get(
            incident_id
        )

        if incident is None:
            return False

        incident.start_investigation()

        return True

    def mitigate(
        self,
        incident_id: Any,
    ) -> bool:
        """Move an incident into mitigation."""
        incident = self.get(
            incident_id
        )

        if incident is None:
            return False

        incident.start_mitigation()

        return True

    def resolve(
        self,
        incident_id: Any,
    ) -> bool:
        """Resolve an incident."""
        incident = self.get(
            incident_id
        )

        if incident is None:
            return False

        incident.resolve()

        return True

    def dismiss(
        self,
        incident_id: Any,
    ) -> bool:
        """Dismiss an incident."""
        incident = self.get(
            incident_id
        )

        if incident is None:
            return False

        incident.dismiss()

        return True

    # ========================================================
    # SEVERITY
    # ========================================================

    def update_severity(
        self,
        incident_id: Any,
        severity: str,
    ) -> bool:
        """Update the severity of an incident."""
        incident = self.get(
            incident_id
        )

        if incident is None:
            return False

        normalized = _normalize_severity(
            severity
        )

        incident.severity = normalized

        return True

    def escalate(
        self,
        incident_id: Any,
    ) -> bool:
        """
        Increase incident severity by one level.
        """
        incident = self.get(
            incident_id
        )

        if incident is None:
            return False

        current_index = SEVERITY_ORDER.index(
            incident.severity
        )

        next_index = min(
            current_index + 1,
            len(SEVERITY_ORDER) - 1,
        )

        incident.severity = (
            SEVERITY_ORDER[
                next_index
            ]
        )

        return True

    # ========================================================
    # FILTERING
    # ========================================================

    def active_incidents(
        self,
    ) -> list[Incident]:
        """Return all active incidents."""
        return [
            incident
            for incident in self.incidents.values()
            if incident.is_active
        ]

    def resolved_incidents(
        self,
    ) -> list[Incident]:
        """Return all resolved incidents."""
        return [
            incident
            for incident in self.incidents.values()
            if incident.is_resolved
        ]

    def by_severity(
        self,
        minimum_severity: str,
    ) -> list[Incident]:
        """Return incidents at or above a severity."""
        severity = _normalize_severity(
            minimum_severity
        )

        minimum_rank = SEVERITY_RANK[
            severity
        ]

        return [
            incident
            for incident in self.incidents.values()
            if incident.severity_rank
            >= minimum_rank
        ]

    def by_status(
        self,
        status: str,
    ) -> list[Incident]:
        """Return incidents with a specific status."""
        normalized = _normalize_status(
            status
        )

        return [
            incident
            for incident in self.incidents.values()
            if incident.status
            == normalized
        ]

    def by_type(
        self,
        incident_type: str,
    ) -> list[Incident]:
        """Return incidents of a specific type."""
        normalized = _normalize_type(
            incident_type
        )

        return [
            incident
            for incident in self.incidents.values()
            if incident.incident_type
            == normalized
        ]

    def by_asset(
        self,
        asset_id: Any,
    ) -> list[Incident]:
        """Return incidents associated with an asset."""
        normalized = str(
            asset_id
        )

        return [
            incident
            for incident in self.incidents.values()
            if incident.asset_id
            == normalized
        ]

    def by_region(
        self,
        region_id: Any,
    ) -> list[Incident]:
        """Return incidents associated with a region."""
        normalized = str(
            region_id
        )

        return [
            incident
            for incident in self.incidents.values()
            if incident.region_id
            == normalized
        ]

    # ========================================================
    # PRIORITY
    # ========================================================

    def highest_priority(
        self,
    ) -> Incident | None:
        """Return the highest-severity active incident."""
        active = self.active_incidents()

        if not active:
            return None

        return max(
            active,
            key=lambda incident: (
                incident.severity_rank,
                incident.confidence,
                incident.detected_at,
            ),
        )

    def high_priority_incidents(
        self,
    ) -> list[Incident]:
        """Return high and critical active incidents."""
        return [
            incident
            for incident in self.active_incidents()
            if incident.severity
            in {
                "high",
                "critical",
            }
        ]

    def critical_incidents(
        self,
    ) -> list[Incident]:
        """Return active critical incidents."""
        return [
            incident
            for incident in self.active_incidents()
            if incident.severity
            == "critical"
        ]

    # ========================================================
    # DUPLICATE DETECTION
    # ========================================================

    def find_similar(
        self,
        incident: Incident,
    ) -> list[Incident]:
        """
        Find active incidents that appear to represent the
        same underlying condition.
        """
        matches: list[Incident] = []

        for existing in self.active_incidents():
            if existing.incident_id == incident.incident_id:
                continue

            if (
                existing.incident_type
                != incident.incident_type
            ):
                continue

            if (
                existing.asset_id
                != incident.asset_id
            ):
                continue

            if (
                existing.region_id
                != incident.region_id
            ):
                continue

            matches.append(
                existing
            )

        return matches

    # ========================================================
    # ALERT-DRIVEN INCIDENT CREATION
    # ========================================================

    def create_from_alert(
        self,
        incident_id: Any,
        alert: IncidentAlert,
        incident_type: str = "unknown",
        description: str | None = None,
    ) -> Incident:
        """
        Create an incident based on an alert.
        """
        incident = self.create(
            incident_id=incident_id,
            title=alert.title,
            description=(
                description
                if description is not None
                else alert.message
            ),
            incident_type=incident_type,
            severity=alert.severity,
            asset_id=alert.asset_id,
            region_id=alert.region_id,
            source=alert.source,
            confidence=alert.confidence,
        )

        incident.add_alert(
            alert
        )

        return incident

    # ========================================================
    # CONDITION-DRIVEN INCIDENT CREATION
    # ========================================================

    def create_risk_incident(
        self,
        incident_id: Any,
        risk_score: float,
        asset_id: Any | None = None,
        region_id: Any | None = None,
        confidence: float = 1.0,
    ) -> Incident:
        """
        Create an incident from a risk score.
        """
        severity = severity_from_risk_score(
            risk_score
        )

        incident = self.create(
            incident_id=incident_id,
            title="Grid risk incident",
            description=(
                "Risk analysis detected an elevated "
                "grid-risk condition."
            ),
            incident_type="prediction",
            severity=severity,
            asset_id=asset_id,
            region_id=region_id,
            source="risk_engine",
            confidence=confidence,
            metadata={
                "risk_score": max(
                    0.0,
                    min(
                        1.0,
                        _safe_float(
                            risk_score
                        ),
                    ),
                ),
            },
        )

        return incident

    def create_overload_incident(
        self,
        incident_id: Any,
        loading_percent: float,
        asset_id: Any | None = None,
        region_id: Any | None = None,
    ) -> Incident:
        """
        Create an incident from an asset loading condition.
        """
        severity = severity_from_loading(
            loading_percent
        )

        incident = self.create(
            incident_id=incident_id,
            title="Grid asset overload condition",
            description=(
                "Telemetry indicates elevated loading "
                "on a grid asset."
            ),
            incident_type="overload",
            severity=severity,
            asset_id=asset_id,
            region_id=region_id,
            source="telemetry",
            confidence=1.0,
            metadata={
                "loading_percent": max(
                    0.0,
                    _safe_float(
                        loading_percent
                    ),
                ),
            },
        )

        return incident

    def create_prediction_incident(
        self,
        incident_id: Any,
        probability: float,
        event_type: str = "grid event",
        asset_id: Any | None = None,
        region_id: Any | None = None,
    ) -> Incident:
        """
        Create an incident from a predictive model output.

        Prediction output is treated as probabilistic evidence,
        not as certainty.
        """
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

        return self.create(
            incident_id=incident_id,
            title=(
                f"Potential {event_type} detected"
            ),
            description=(
                "Predictive analysis identified a "
                "potential grid event."
            ),
            incident_type="prediction",
            severity=severity,
            asset_id=asset_id,
            region_id=region_id,
            source="prediction_engine",
            confidence=normalized_probability,
            metadata={
                "probability": (
                    normalized_probability
                ),
                "event_type": event_type,
            },
        )

    # ========================================================
    # SORTING
    # ========================================================

    def sort_by_severity(
        self,
        incidents: Iterable[Incident] | None = None,
    ) -> list[Incident]:
        """
        Sort incidents from highest to lowest severity.
        """
        values = list(
            incidents
            if incidents is not None
            else self.incidents.values()
        )

        return sorted(
            values,
            key=lambda incident: (
                incident.severity_rank,
                incident.confidence,
                incident.detected_at,
            ),
            reverse=True,
        )

    def sort_by_time(
        self,
        incidents: Iterable[Incident] | None = None,
        descending: bool = True,
    ) -> list[Incident]:
        """Sort incidents by detection time."""
        values = list(
            incidents
            if incidents is not None
            else self.incidents.values()
        )

        return sorted(
            values,
            key=lambda incident: incident.detected_at,
            reverse=descending,
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    def summary(
        self,
    ) -> dict[str, Any]:
        """Generate an incident-manager summary."""
        all_incidents = list(
            self.incidents.values()
        )

        severity_counts = {
            severity: 0
            for severity in SEVERITY_ORDER
        }

        status_counts = {
            status: 0
            for status in VALID_INCIDENT_STATUSES
        }

        type_counts: dict[
            str,
            int,
        ] = {}

        for incident in all_incidents:
            severity_counts[
                incident.severity
            ] += 1

            status_counts[
                incident.status
            ] += 1

            type_counts[
                incident.incident_type
            ] = (
                type_counts.get(
                    incident.incident_type,
                    0,
                )
                + 1
            )

        active = self.active_incidents()

        return {
            "total_incidents": len(
                all_incidents
            ),
            "active_incidents": len(
                active
            ),
            "resolved_incidents": len(
                self.resolved_incidents()
            ),
            "critical_incidents": len(
                self.critical_incidents()
            ),
            "high_priority_incidents": len(
                self.high_priority_incidents()
            ),
            "severity_counts": severity_counts,
            "status_counts": status_counts,
            "type_counts": type_counts,
        }

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_list(
        self,
    ) -> list[dict[str, Any]]:
        """Return all incidents as dictionaries."""
        return [
            incident.to_dict()
            for incident in self.incidents.values()
        ]

    def active_to_list(
        self,
    ) -> list[dict[str, Any]]:
        """Return active incidents as dictionaries."""
        return [
            incident.to_dict()
            for incident in self.active_incidents()
        ]


# ============================================================
# MODULE-LEVEL HELPERS
# ============================================================


def incident_summary(
    incidents: Iterable[Incident],
) -> dict[str, Any]:
    """
    Generate a summary without creating an IncidentManager.
    """
    manager = IncidentManager(
        incidents
    )

    return manager.summary()


def active_incidents(
    incidents: Iterable[Incident],
) -> list[Incident]:
    """Return active incidents from an iterable."""
    return [
        incident
        for incident in incidents
        if incident.is_active
    ]


def critical_incidents(
    incidents: Iterable[Incident],
) -> list[Incident]:
    """Return critical active incidents."""
    return [
        incident
        for incident in incidents
        if (
            incident.is_active
            and incident.severity
            == "critical"
        )
    ]


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Incident",
    "IncidentManager",
    "create_incident",
    "incident_summary",
    "active_incidents",
    "critical_incidents",
]