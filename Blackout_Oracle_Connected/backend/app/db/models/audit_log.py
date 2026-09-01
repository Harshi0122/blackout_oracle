"""
Blackout Oracle - Audit Log Database Model.

Stores an immutable audit trail of important events occurring inside
the Blackout Oracle platform.

Audit records may include:

- User authentication events
- Authorization events
- AI-agent decisions
- Risk assessments
- Simulation executions
- Recommendations
- Human approvals
- Alert creation and resolution
- Telemetry ingestion events
- Configuration changes
- External service events

IMPORTANT
---------

Audit logs are for accountability and traceability.

They do NOT provide direct control over electrical-grid infrastructure.

Sensitive information such as API keys, passwords, access tokens, and
other secrets must never be stored in audit records.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# ============================================================
# ENUMS
# ============================================================


class AuditEventType(str, Enum):
    """
    Categories of events recorded by the audit system.
    """

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"

    USER_ACTION = "user_action"

    TELEMETRY = "telemetry"
    WEATHER = "weather"

    RISK_ASSESSMENT = "risk_assessment"

    SIMULATION = "simulation"

    AGENT_ACTION = "agent_action"
    AGENT_DECISION = "agent_decision"

    RECOMMENDATION = "recommendation"

    HUMAN_APPROVAL = "human_approval"

    ALERT = "alert"
    INCIDENT = "incident"

    CONFIGURATION = "configuration"

    SYSTEM = "system"

    EXTERNAL_SERVICE = "external_service"

    SECURITY = "security"


class AuditEventStatus(str, Enum):
    """
    Result of the audited event.
    """

    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
    WARNING = "warning"
    PENDING = "pending"


class AuditSeverity(str, Enum):
    """
    Severity associated with an audit event.
    """

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# AUDIT LOG MODEL
# ============================================================


class AuditLog(Base):
    """
    Immutable audit record for Blackout Oracle.
    """

    __tablename__ = "audit_logs"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"AUD-{uuid4().hex[:12].upper()}"
        ),
    )

    # ========================================================
    # EVENT INFORMATION
    # ========================================================

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    event_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AuditEventStatus.SUCCESS.value,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AuditSeverity.INFO.value,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ========================================================
    # ACTOR INFORMATION
    # ========================================================

    actor_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    actor_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    actor_role: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # ========================================================
    # RESOURCE INFORMATION
    # ========================================================

    resource_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    resource_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    # ========================================================
    # RELATED GRID ASSET
    # ========================================================

    asset_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    region_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # ========================================================
    # CORRELATION
    # ========================================================

    request_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    correlation_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    incident_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    simulation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    recommendation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    alert_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # ========================================================
    # AI INFORMATION
    # ========================================================

    agent_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ========================================================
    # DECISION / VERIFICATION
    # ========================================================

    decision: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    verification_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    approval_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    approved_by: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    # ========================================================
    # NETWORK INFORMATION
    # ========================================================

    source_ip: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # ========================================================
    # EVENT DATA
    # ========================================================

    details_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # TIMESTAMP
    # ========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        index=True,
    )

    # ========================================================
    # DATABASE INDEXES
    # ========================================================

    __table_args__ = (
        Index(
            "ix_audit_logs_actor_created",
            "actor_id",
            "created_at",
        ),
        Index(
            "ix_audit_logs_resource_created",
            "resource_type",
            "resource_id",
            "created_at",
        ),
        Index(
            "ix_audit_logs_event_created",
            "event_type",
            "created_at",
        ),
        Index(
            "ix_audit_logs_region_created",
            "region_id",
            "created_at",
        ),
        Index(
            "ix_audit_logs_correlation",
            "correlation_id",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<AuditLog("
            f"id='{self.id}', "
            f"event_type='{self.event_type}', "
            f"action='{self.action}', "
            f"status='{self.event_status}'"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "AuditLog",
    "AuditEventType",
    "AuditEventStatus",
    "AuditSeverity",
]