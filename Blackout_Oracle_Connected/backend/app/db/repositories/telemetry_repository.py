"""
Blackout Oracle - Telemetry Repository.

Provides database operations for the Telemetry model.

The repository layer keeps database access separate from:

- API routes
- AI agents
- Risk engines
- Prediction services
- Simulation services
- Anomaly detection
- Data-processing services
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.telemetry import Telemetry


class TelemetryRepository:
    """
    Repository for Telemetry database operations.
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
        telemetry: Telemetry,
    ) -> Telemetry:
        """
        Add a telemetry record to the database.

        Args:
            telemetry: Telemetry model instance.

        Returns:
            The persisted telemetry record.
        """
        self.db.add(telemetry)
        self.db.commit()
        self.db.refresh(telemetry)

        return telemetry

    # ========================================================
    # CREATE MANY
    # ========================================================

    def create_many(
        self,
        telemetry_records: list[Telemetry],
    ) -> list[Telemetry]:
        """
        Add multiple telemetry records to the database.

        Args:
            telemetry_records: List of Telemetry instances.

        Returns:
            Persisted telemetry records.
        """
        if not telemetry_records:
            return []

        self.db.add_all(telemetry_records)
        self.db.commit()

        for telemetry in telemetry_records:
            self.db.refresh(telemetry)

        return telemetry_records

    # ========================================================
    # GET BY ID
    # ========================================================

    def get_by_id(
        self,
        telemetry_id: str,
    ) -> Telemetry | None:
        """
        Retrieve telemetry by its primary key.

        Args:
            telemetry_id: Telemetry ID.

        Returns:
            Telemetry record if found, otherwise None.
        """
        statement = select(Telemetry).where(
            Telemetry.id == telemetry_id
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
    ) -> list[Telemetry]:
        """
        Retrieve telemetry records with pagination.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            List of telemetry records.
        """
        statement = (
            select(Telemetry)
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.desc()
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
    ) -> list[Telemetry]:
        """
        Retrieve telemetry belonging to an asset.

        Args:
            asset_id: Asset ID.

        Returns:
            List of telemetry records.
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.asset_id == asset_id
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BY ASSET TYPE
    # ========================================================

    def get_by_asset_type(
        self,
        asset_type: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Telemetry]:
        """
        Retrieve telemetry belonging to a specific
        type of grid asset.

        Args:
            asset_type: Asset type.

        Returns:
            List of telemetry records.
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.asset_type == asset_type
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BY SOURCE
    # ========================================================

    def get_by_source(
        self,
        source: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Telemetry]:
        """
        Retrieve telemetry from a specific data source.

        Args:
            source: Telemetry source.

        Returns:
            List of telemetry records.
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.source == source
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BY SOURCE ID
    # ========================================================

    def get_by_source_id(
        self,
        source_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Telemetry]:
        """
        Retrieve telemetry using the source-system ID.

        Args:
            source_id: Source identifier.

        Returns:
            List of telemetry records.
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.source_id == source_id
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BY TELEMETRY TYPE
    # ========================================================

    def get_by_type(
        self,
        telemetry_type: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Telemetry]:
        """
        Retrieve telemetry of a specific type.

        Args:
            telemetry_type: Telemetry type.

        Returns:
            List of telemetry records.
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.telemetry_type
                == telemetry_type
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BY MEASUREMENT
    # ========================================================

    def get_by_measurement(
        self,
        measurement_name: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Telemetry]:
        """
        Retrieve telemetry for a particular measurement.

        Examples:

        - voltage
        - current
        - active_power
        - reactive_power
        - frequency
        - temperature
        - loading
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.measurement_name
                == measurement_name
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET VALID TELEMETRY
    # ========================================================

    def get_valid(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Telemetry]:
        """
        Retrieve telemetry records marked as valid.
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.is_valid.is_(True)
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET INVALID TELEMETRY
    # ========================================================

    def get_invalid(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Telemetry]:
        """
        Retrieve telemetry records marked as invalid.
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.is_valid.is_(False)
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET ANOMALOUS TELEMETRY
    # ========================================================

    def get_anomalies(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Telemetry]:
        """
        Retrieve telemetry records where an anomaly
        has been detected.
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.anomaly_detected.is_(True)
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET UNPROCESSED TELEMETRY
    # ========================================================

    def get_unprocessed(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Telemetry]:
        """
        Retrieve telemetry records that have not yet
        been processed by the backend.
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.processed.is_(False)
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.asc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET ESTIMATED TELEMETRY
    # ========================================================

    def get_estimated(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Telemetry]:
        """
        Retrieve telemetry values that were estimated
        rather than directly measured.
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.is_estimated.is_(True)
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET SIMULATED TELEMETRY
    # ========================================================

    def get_simulated(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Telemetry]:
        """
        Retrieve telemetry generated by simulations.
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.is_simulated.is_(True)
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET BY QUALITY
    # ========================================================

    def get_by_quality(
        self,
        quality: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Telemetry]:
        """
        Retrieve telemetry with a specific quality level.

        Args:
            quality: Telemetry quality value.

        Returns:
            List of matching telemetry records.
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.quality == quality
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.desc()
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
    ) -> list[Telemetry]:
        """
        Retrieve telemetry belonging to a region.

        Args:
            region_id: Region ID.

        Returns:
            List of telemetry records.
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.region_id == region_id
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET LATEST FOR ASSET
    # ========================================================

    def get_latest_for_asset(
        self,
        asset_id: str,
    ) -> Telemetry | None:
        """
        Retrieve the most recent telemetry record
        for an asset.

        Args:
            asset_id: Asset ID.

        Returns:
            Latest telemetry record, or None.
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.asset_id == asset_id
            )
            .order_by(
                Telemetry.source_timestamp.desc()
            )
            .limit(1)
        )

        return self.db.scalar(statement)

    # ========================================================
    # GET LATEST BY MEASUREMENT
    # ========================================================

    def get_latest_measurement(
        self,
        asset_id: str,
        measurement_name: str,
    ) -> Telemetry | None:
        """
        Retrieve the most recent value for a particular
        measurement belonging to an asset.

        Args:
            asset_id: Asset ID.
            measurement_name: Measurement name.

        Returns:
            Latest matching telemetry record, or None.
        """
        statement = (
            select(Telemetry)
            .where(
                Telemetry.asset_id == asset_id,
                Telemetry.measurement_name
                == measurement_name,
            )
            .order_by(
                Telemetry.source_timestamp.desc()
            )
            .limit(1)
        )

        return self.db.scalar(statement)

    # ========================================================
    # GET TIME RANGE
    # ========================================================

    def get_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        *,
        asset_id: str | None = None,
        skip: int = 0,
        limit: int = 1000,
    ) -> list[Telemetry]:
        """
        Retrieve telemetry within a time range.

        Args:
            start_time: Start of time range.
            end_time: End of time range.
            asset_id: Optional asset filter.
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            Telemetry records within the requested range.
        """
        statement = select(Telemetry).where(
            Telemetry.source_timestamp >= start_time,
            Telemetry.source_timestamp <= end_time,
        )

        if asset_id is not None:
            statement = statement.where(
                Telemetry.asset_id == asset_id
            )

        statement = (
            statement
            .offset(skip)
            .limit(limit)
            .order_by(
                Telemetry.source_timestamp.asc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # GET RECENT TELEMETRY
    # ========================================================

    def get_recent(
        self,
        minutes: int = 15,
        *,
        asset_id: str | None = None,
        limit: int = 1000,
    ) -> list[Telemetry]:
        """
        Retrieve telemetry received during the last
        specified number of minutes.

        Args:
            minutes: Number of minutes to look back.
            asset_id: Optional asset filter.
            limit: Maximum number of records.

        Returns:
            Recent telemetry records.
        """
        from datetime import timedelta

        start_time = (
            datetime.now(timezone.utc)
            - timedelta(minutes=minutes)
        )

        statement = select(Telemetry).where(
            Telemetry.received_at >= start_time
        )

        if asset_id is not None:
            statement = statement.where(
                Telemetry.asset_id == asset_id
            )

        statement = (
            statement
            .limit(limit)
            .order_by(
                Telemetry.received_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ========================================================
    # MARK AS PROCESSED
    # ========================================================

    def mark_processed(
        self,
        telemetry: Telemetry,
    ) -> Telemetry:
        """
        Mark a telemetry record as processed.
        """
        telemetry.processed = True

        self.db.commit()
        self.db.refresh(telemetry)

        return telemetry

    # ========================================================
    # MARK MANY AS PROCESSED
    # ========================================================

    def mark_many_processed(
        self,
        telemetry_records: list[Telemetry],
    ) -> list[Telemetry]:
        """
        Mark multiple telemetry records as processed.
        """
        if not telemetry_records:
            return []

        for telemetry in telemetry_records:
            telemetry.processed = True

        self.db.commit()

        for telemetry in telemetry_records:
            self.db.refresh(telemetry)

        return telemetry_records

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        telemetry: Telemetry,
        values: dict[str, Any],
    ) -> Telemetry:
        """
        Update an existing telemetry record.

        Args:
            telemetry: Telemetry model instance.
            values: Fields to update.

        Returns:
            Updated telemetry record.
        """
        for field, value in values.items():
            if hasattr(telemetry, field):
                setattr(
                    telemetry,
                    field,
                    value,
                )

        self.db.commit()
        self.db.refresh(telemetry)

        return telemetry

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        telemetry: Telemetry,
    ) -> None:
        """
        Delete a telemetry record.
        """
        self.db.delete(telemetry)
        self.db.commit()

    # ========================================================
    # EXISTS
    # ========================================================

    def exists(
        self,
        telemetry_id: str,
    ) -> bool:
        """
        Check whether a telemetry record exists.
        """
        statement = select(
            Telemetry.id
        ).where(
            Telemetry.id == telemetry_id
        )

        return (
            self.db.scalar(statement) is not None
        )

    # ========================================================
    # COUNT
    # ========================================================

    def count(self) -> int:
        """
        Return the total number of telemetry records.
        """
        statement = select(
            func.count(Telemetry.id)
        )

        return int(
            self.db.scalar(statement) or 0
        )

    # ========================================================
    # COUNT ANOMALIES
    # ========================================================

    def count_anomalies(self) -> int:
        """
        Return the number of telemetry records
        containing detected anomalies.
        """
        statement = select(
            func.count(Telemetry.id)
        ).where(
            Telemetry.anomaly_detected.is_(True)
        )

        return int(
            self.db.scalar(statement) or 0
        )

    # ========================================================
    # COUNT UNPROCESSED
    # ========================================================

    def count_unprocessed(self) -> int:
        """
        Return the number of telemetry records waiting
        for processing.
        """
        statement = select(
            func.count(Telemetry.id)
        ).where(
            Telemetry.processed.is_(False)
        )

        return int(
            self.db.scalar(statement) or 0
        )