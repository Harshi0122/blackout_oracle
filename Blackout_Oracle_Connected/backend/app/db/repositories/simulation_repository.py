"""
Blackout Oracle - Simulation Repository.

Provides database operations for the Simulation model.

The repository layer keeps database access separate from:

- API routes
- AI agents
- Risk engines
- Prediction services
- Scenario management
- Recommendation services
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.simulation import Simulation


class SimulationRepository:
    """
    Repository for Simulation database operations.
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

    def create(
        self,
        simulation: Simulation,
    ) -> Simulation:
        """
        Add a new simulation to the database.

        Args:
            simulation: Simulation model instance.

        Returns:
            The persisted Simulation instance.
        """
        self.db.add(simulation)
        self.db.commit()
        self.db.refresh(simulation)

        return simulation

    # ========================================================
    # GET BY ID
    # ========================================================

    def get_by_id(
        self,
        simulation_id: str,
    ) -> Simulation | None:
        """
        Retrieve a simulation by its primary key.

        Args:
            simulation_id: Simulation ID.

        Returns:
            Simulation if found, otherwise None.
        """
        statement = select(Simulation).where(
            Simulation.id == simulation_id
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
    ) -> list[Simulation]:
        """
        Retrieve simulations with pagination.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            List of simulations.
        """
        statement = (
            select(Simulation)
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.created_at.desc()
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
    ) -> list[Simulation]:
        """
        Retrieve simulations with a specific status.

        Args:
            status: Simulation status.
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            List of matching simulations.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.status == status
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET RUNNING SIMULATIONS
    # ========================================================

    def get_running(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Simulation]:
        """
        Retrieve simulations that are currently running.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.status == "running"
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.started_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET COMPLETED SIMULATIONS
    # ========================================================

    def get_completed(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Simulation]:
        """
        Retrieve completed simulations.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.status == "completed"
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.completed_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET FAILED SIMULATIONS
    # ========================================================

    def get_failed(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Simulation]:
        """
        Retrieve failed simulations.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.status == "failed"
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.created_at.desc()
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
        simulation_type: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Simulation]:
        """
        Retrieve simulations of a specific type.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.simulation_type
                == simulation_type
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.created_at.desc()
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
    ) -> list[Simulation]:
        """
        Retrieve simulations belonging to a region.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.region_id == region_id
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BY SCENARIO
    # ========================================================

    def get_by_scenario(
        self,
        scenario_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Simulation]:
        """
        Retrieve simulations generated from a scenario.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.scenario_id
                == scenario_id
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BY PREDICTION
    # ========================================================

    def get_by_prediction(
        self,
        prediction_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Simulation]:
        """
        Retrieve simulations associated with a prediction.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.prediction_id
                == prediction_id
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BY RECOMMENDATION
    # ========================================================

    def get_by_recommendation(
        self,
        recommendation_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Simulation]:
        """
        Retrieve simulations associated with a recommendation.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.recommendation_id
                == recommendation_id
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.created_at.desc()
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
    ) -> list[Simulation]:
        """
        Retrieve simulations involving an asset.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.asset_id == asset_id
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BLACKOUT SIMULATIONS
    # ========================================================

    def get_blackout_simulations(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Simulation]:
        """
        Retrieve simulations that resulted in a blackout.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.blackout_detected.is_(True)
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET CASCADE SIMULATIONS
    # ========================================================

    def get_cascade_simulations(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Simulation]:
        """
        Retrieve simulations in which a cascading failure
        was detected.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.cascade_detected.is_(True)
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.cascade_depth.desc(),
                Simulation.created_at.desc(),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET UNSTABLE SIMULATIONS
    # ========================================================

    def get_unstable_simulations(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Simulation]:
        """
        Retrieve simulations that produced unstable
        or blackout-related outcomes.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.outcome.in_(
                    [
                        "unstable",
                        "blackout",
                        "partial_blackout",
                        "cascading_failure",
                    ]
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET MITIGATION SIMULATIONS
    # ========================================================

    def get_mitigation_simulations(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Simulation]:
        """
        Retrieve simulations where mitigation was applied.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.mitigation_applied.is_(True)
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET SUCCESSFUL MITIGATIONS
    # ========================================================

    def get_successful_mitigations(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Simulation]:
        """
        Retrieve simulations where the mitigation
        strategy was successful.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.mitigation_applied.is_(True),
                Simulation.mitigation_successful.is_(True),
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.risk_reduction_percent.desc(),
                Simulation.created_at.desc(),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET PENDING VALIDATION
    # ========================================================

    def get_pending_validation(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Simulation]:
        """
        Retrieve simulations awaiting validation.
        """
        statement = (
            select(Simulation)
            .where(
                Simulation.validation_completed.is_(False),
                Simulation.validation_required.is_(True),
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Simulation.created_at.asc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # START SIMULATION
    # ========================================================

    def start(
        self,
        simulation: Simulation,
    ) -> Simulation:
        """
        Mark a simulation as running.

        Args:
            simulation: Simulation model instance.

        Returns:
            Updated simulation.
        """
        simulation.status = "running"
        simulation.started_at = datetime.now(
            timezone.utc
        )

        self.db.commit()
        self.db.refresh(simulation)

        return simulation

    # ========================================================
    # COMPLETE SIMULATION
    # ========================================================

    def complete(
        self,
        simulation: Simulation,
        results: dict[str, Any] | None = None,
    ) -> Simulation:
        """
        Mark a simulation as completed.

        Args:
            simulation: Simulation model instance.
            results: Optional dictionary containing result fields.

        Returns:
            Updated simulation.
        """
        simulation.status = "completed"
        simulation.completed_at = datetime.now(
            timezone.utc
        )

        if results:
            for field, value in results.items():
                if hasattr(simulation, field):
                    setattr(
                        simulation,
                        field,
                        value,
                    )

        self.db.commit()
        self.db.refresh(simulation)

        return simulation

    # ========================================================
    # FAIL SIMULATION
    # ========================================================

    def fail(
        self,
        simulation: Simulation,
        error_message: str,
    ) -> Simulation:
        """
        Mark a simulation as failed.

        Args:
            simulation: Simulation model instance.
            error_message: Reason for failure.

        Returns:
            Updated simulation.
        """
        simulation.status = "failed"
        simulation.error_message = error_message
        simulation.completed_at = datetime.now(
            timezone.utc
        )

        self.db.commit()
        self.db.refresh(simulation)

        return simulation

    # ========================================================
    # CANCEL SIMULATION
    # ========================================================

    def cancel(
        self,
        simulation: Simulation,
    ) -> Simulation:
        """
        Mark a simulation as cancelled.
        """
        simulation.status = "cancelled"
        simulation.completed_at = datetime.now(
            timezone.utc
        )

        self.db.commit()
        self.db.refresh(simulation)

        return simulation

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        simulation: Simulation,
        values: dict[str, Any],
    ) -> Simulation:
        """
        Update an existing simulation.

        Args:
            simulation: Simulation model instance.
            values: Fields to update.

        Returns:
            Updated Simulation instance.
        """
        for field, value in values.items():
            if hasattr(simulation, field):
                setattr(
                    simulation,
                    field,
                    value,
                )

        self.db.commit()
        self.db.refresh(simulation)

        return simulation

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        simulation: Simulation,
    ) -> None:
        """
        Delete a simulation from the database.
        """
        self.db.delete(simulation)
        self.db.commit()

    # ========================================================
    # EXISTS
    # ========================================================

    def exists(
        self,
        simulation_id: str,
    ) -> bool:
        """
        Check whether a simulation exists.
        """
        statement = select(Simulation.id).where(
            Simulation.id == simulation_id
        )

        return (
            self.db.scalar(statement) is not None
        )

    # ========================================================
    # COUNT
    # ========================================================

    def count(self) -> int:
        """
        Return the total number of simulations.
        """
        statement = select(
            func.count(Simulation.id)
        )

        return int(
            self.db.scalar(statement) or 0
        )

    # ========================================================
    # COUNT BY STATUS
    # ========================================================

    def count_by_status(
        self,
        status: str,
    ) -> int:
        """
        Return the number of simulations with a
        particular status.
        """
        statement = select(
            func.count(Simulation.id)
        ).where(
            Simulation.status == status
        )

        return int(
            self.db.scalar(statement) or 0
        )

    # ========================================================
    # COUNT BLACKOUTS
    # ========================================================

    def count_blackouts(self) -> int:
        """
        Return the number of simulations that detected
        a blackout.
        """
        statement = select(
            func.count(Simulation.id)
        ).where(
            Simulation.blackout_detected.is_(True)
        )

        return int(
            self.db.scalar(statement) or 0
        )

    # ========================================================
    # COUNT CASCADES
    # ========================================================

    def count_cascades(self) -> int:
        """
        Return the number of simulations that detected
        cascading failure.
        """
        statement = select(
            func.count(Simulation.id)
        ).where(
            Simulation.cascade_detected.is_(True)
        )

        return int(
            self.db.scalar(statement) or 0
        )