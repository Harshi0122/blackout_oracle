"""
Blackout Oracle - Incident Repository.

Provides database operations for the Incident model.

The repository layer keeps database access separate from:

- API routes
- AI agents
- Risk engines
- Prediction services
- Simulation services
- Alert processing
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.incident import Incident


class IncidentRepository:
    """
    Repository for Incident database operations.
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize the repository.

        Args:
            db: Active SQLAlchemy database session.
        """
        self.db = db

    # ========================================================
    # CREATE
    # ========================================================

    def create(self, incident: Incident) -> Incident:
        """
        Add a new incident to the database.
        """
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)

        return incident

    # ========================================================
    # GET BY ID
    # ========================================================

    def get_by_id(
        self,
        incident_id: str,
    ) -> Incident | None:
        """
        Retrieve an incident by its primary key.
        """
        statement = select(Incident).where(
            Incident.id == incident_id
        )

        return self.db.scalar(statement)

    # ========================================================
    # GET BY EXTERNAL ID
    # ========================================================

    def get_by_external_id(
        self,
        external_id: str,
    ) -> Incident | None:
        """
        Retrieve an incident using its external ID.
        """
        statement = select(Incident).where(
            Incident.external_id == external_id
        )

        return self.db.scalar(statement)

    # ========================================================
    # GET ALL
    # ========================================================

    def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Incident]:
        """
        Retrieve incidents with pagination.
        """
        statement = (
            select(Incident)
            .offset(skip)
            .limit(limit)
            .order_by(
                Incident.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BY STATUS
    # ========================================================

    def get_by_status(
        self,
        status: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Incident]:
        """
        Retrieve incidents with a specific status.
        """
        statement = (
            select(Incident)
            .where(
                Incident.status == status
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Incident.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET ACTIVE INCIDENTS
    # ========================================================

    def get_active_incidents(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Incident]:
        """
        Retrieve currently active incidents.
        """
        statement = (
            select(Incident)
            .where(
                Incident.is_active.is_(True)
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Incident.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BY REGION
    # ========================================================

    def get_by_region(
        self,
        region_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Incident]:
        """
        Retrieve incidents belonging to a region.
        """
        statement = (
            select(Incident)
            .where(
                Incident.region_id == region_id
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Incident.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BY ASSET
    # ========================================================

    def get_by_asset(
        self,
        asset_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Incident]:
        """
        Retrieve incidents associated with an asset.
        """
        statement = (
            select(Incident)
            .where(
                Incident.asset_id == asset_id
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Incident.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BY TYPE
    # ========================================================

    def get_by_type(
        self,
        incident_type: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Incident]:
        """
        Retrieve incidents of a specific type.
        """
        statement = (
            select(Incident)
            .where(
                Incident.incident_type
                == incident_type
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Incident.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BY SEVERITY
    # ========================================================

    def get_by_severity(
        self,
        severity: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Incident]:
        """
        Retrieve incidents with a specific severity.
        """
        statement = (
            select(Incident)
            .where(
                Incident.severity == severity
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Incident.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET CRITICAL INCIDENTS
    # ========================================================

    def get_critical_incidents(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Incident]:
        """
        Retrieve active critical or emergency incidents.
        """
        statement = (
            select(Incident)
            .where(
                Incident.is_active.is_(True),
                Incident.severity.in_(
                    [
                        "critical",
                        "emergency",
                    ]
                ),
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Incident.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET UNRESOLVED INCIDENTS
    # ========================================================

    def get_unresolved_incidents(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Incident]:
        """
        Retrieve incidents that have not been resolved.
        """
        statement = (
            select(Incident)
            .where(
                Incident.resolved_at.is_(None)
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Incident.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BLACKOUT INCIDENTS
    # ========================================================

    def get_blackout_incidents(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Incident]:
        """
        Retrieve incidents associated with blackouts
        or cascading failures.
        """
        statement = (
            select(Incident)
            .where(
                (
                    Incident.blackout_detected.is_(True)
                )
                | (
                    Incident.cascade_detected.is_(True)
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Incident.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # SEARCH
    # ========================================================

    def search(
        self,
        query: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Incident]:
        """
        Search incidents by title, description,
        or external ID.
        """
        search_text = f"%{query}%"

        statement = (
            select(Incident)
            .where(
                (Incident.title.ilike(search_text))
                | (
                    Incident.description.ilike(
                        search_text
                    )
                )
                | (
                    Incident.external_id.ilike(
                        search_text
                    )
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Incident.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        incident: Incident,
        values: dict[str, Any],
    ) -> Incident:
        """
        Update an existing incident.
        """
        for field, value in values.items():
            if hasattr(incident, field):
                setattr(
                    incident,
                    field,
                    value,
                )

        self.db.commit()
        self.db.refresh(incident)

        return incident

    # ========================================================
    # RESOLVE
    # ========================================================

    def resolve(
        self,
        incident: Incident,
    ) -> Incident:
        """
        Mark an incident as resolved.
        """

        incident.is_active = False
        incident.resolved_at = datetime.now(
            timezone.utc
        )

        self.db.commit()
        self.db.refresh(incident)

        return incident

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        incident: Incident,
    ) -> None:
        """
        Delete an incident from the database.
        """
        self.db.delete(incident)
        self.db.commit()

    # ========================================================
    # EXISTS
    # ========================================================

    def exists(
        self,
        incident_id: str,
    ) -> bool:
        """
        Check whether an incident exists.
        """
        statement = select(Incident.id).where(
            Incident.id == incident_id
        )

        return (
            self.db.scalar(statement) is not None
        )

    # ========================================================
    # COUNT
    # ========================================================

    def count(self) -> int:
        """
        Return the total number of incidents.
        """
        statement = select(
            func.count(Incident.id)
        )

        return int(
            self.db.scalar(statement) or 0
        )

    # ========================================================
    # COUNT ACTIVE
    # ========================================================

    def count_active(self) -> int:
        """
        Return the number of currently active incidents.
        """
        statement = select(
            func.count(Incident.id)
        ).where(
            Incident.is_active.is_(True)
        )

        return int(
            self.db.scalar(statement) or 0
        )