"""
Blackout Oracle - Asset Repository.

Provides database operations for the Asset model.

The repository layer keeps database access separate from:

- API routes
- AI agents
- Risk engines
- Prediction services
- Simulation services

This makes the application easier to test and maintain.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.asset import Asset


class AssetRepository:
    """
    Repository for Asset database operations.
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

    def create(self, asset: Asset) -> Asset:
        """
        Add a new asset to the database.

        Args:
            asset: Asset model instance.

        Returns:
            The persisted Asset instance.
        """
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)

        return asset

    # ========================================================
    # GET BY ID
    # ========================================================

    def get_by_id(self, asset_id: str) -> Asset | None:
        """
        Retrieve an asset by its primary key.

        Args:
            asset_id: Asset ID.

        Returns:
            Asset if found, otherwise None.
        """
        statement = select(Asset).where(
            Asset.id == asset_id
        )

        return self.db.scalar(statement)

    # ========================================================
    # GET BY CODE
    # ========================================================

    def get_by_code(self, code: str) -> Asset | None:
        """
        Retrieve an asset using its unique code.

        Args:
            code: Asset code.

        Returns:
            Asset if found, otherwise None.
        """
        statement = select(Asset).where(
            Asset.code == code
        )

        return self.db.scalar(statement)

    # ========================================================
    # GET BY EXTERNAL ID
    # ========================================================

    def get_by_external_id(
        self,
        external_id: str,
    ) -> Asset | None:
        """
        Retrieve an asset using its external system ID.

        Args:
            external_id: External asset identifier.

        Returns:
            Asset if found, otherwise None.
        """
        statement = select(Asset).where(
            Asset.external_id == external_id
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
    ) -> list[Asset]:
        """
        Retrieve assets with pagination.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            List of Asset objects.
        """
        statement = (
            select(Asset)
            .offset(skip)
            .limit(limit)
            .order_by(Asset.created_at.desc())
        )

        return list(self.db.scalars(statement).all())

    # ========================================================
    # GET BY REGION
    # ========================================================

    def get_by_region(
        self,
        region_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Asset]:
        """
        Retrieve assets belonging to a region.

        Args:
            region_id: Region ID.
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            List of assets in the region.
        """
        statement = (
            select(Asset)
            .where(Asset.region_id == region_id)
            .offset(skip)
            .limit(limit)
            .order_by(Asset.created_at.desc())
        )

        return list(self.db.scalars(statement).all())

    # ========================================================
    # GET BY TYPE
    # ========================================================

    def get_by_type(
        self,
        asset_type: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Asset]:
        """
        Retrieve assets of a specific type.

        Args:
            asset_type: Asset type.
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            List of matching assets.
        """
        statement = (
            select(Asset)
            .where(Asset.asset_type == asset_type)
            .offset(skip)
            .limit(limit)
            .order_by(Asset.created_at.desc())
        )

        return list(self.db.scalars(statement).all())

    # ========================================================
    # GET BY STATUS
    # ========================================================

    def get_by_status(
        self,
        status: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Asset]:
        """
        Retrieve assets with a specific operational status.

        Args:
            status: Asset status.
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            List of matching assets.
        """
        statement = (
            select(Asset)
            .where(Asset.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(Asset.created_at.desc())
        )

        return list(self.db.scalars(statement).all())

    # ========================================================
    # GET ACTIVE ASSETS
    # ========================================================

    def get_active_assets(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Asset]:
        """
        Retrieve currently active assets.

        Returns:
            List of active assets.
        """
        statement = (
            select(Asset)
            .where(Asset.is_active.is_(True))
            .offset(skip)
            .limit(limit)
            .order_by(Asset.created_at.desc())
        )

        return list(self.db.scalars(statement).all())

    # ========================================================
    # GET MONITORED ASSETS
    # ========================================================

    def get_monitored_assets(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Asset]:
        """
        Retrieve assets currently configured for monitoring.

        Returns:
            List of monitored assets.
        """
        statement = (
            select(Asset)
            .where(Asset.is_monitored.is_(True))
            .offset(skip)
            .limit(limit)
            .order_by(Asset.created_at.desc())
        )

        return list(self.db.scalars(statement).all())

    # ========================================================
    # GET AT-RISK ASSETS
    # ========================================================

    def get_at_risk_assets(
        self,
        minimum_risk_score: float = 70.0,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Asset]:
        """
        Retrieve assets whose risk score is above a threshold.

        Args:
            minimum_risk_score: Minimum risk score.
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            List of high-risk assets.
        """
        statement = (
            select(Asset)
            .where(
                Asset.risk_score.is_not(None),
                Asset.risk_score >= minimum_risk_score,
            )
            .offset(skip)
            .limit(limit)
            .order_by(
                Asset.risk_score.desc()
            )
        )

        return list(self.db.scalars(statement).all())

    # ========================================================
    # GET OVERLOADED ASSETS
    # ========================================================

    def get_overloaded_assets(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Asset]:
        """
        Retrieve assets currently marked as overloaded.

        Returns:
            List of overloaded assets.
        """
        statement = (
            select(Asset)
            .where(Asset.overloaded.is_(True))
            .offset(skip)
            .limit(limit)
            .order_by(
                Asset.loading_percent.desc()
            )
        )

        return list(self.db.scalars(statement).all())

    # ========================================================
    # GET FAULTED ASSETS
    # ========================================================

    def get_faulted_assets(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Asset]:
        """
        Retrieve assets with an active fault.

        Returns:
            List of faulted assets.
        """
        statement = (
            select(Asset)
            .where(Asset.fault_detected.is_(True))
            .offset(skip)
            .limit(limit)
            .order_by(Asset.created_at.desc())
        )

        return list(self.db.scalars(statement).all())

    # ========================================================
    # SEARCH
    # ========================================================

    def search(
        self,
        query: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Asset]:
        """
        Search assets by name, code, or external ID.

        Args:
            query: Search text.
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            Matching assets.
        """
        search_text = f"%{query}%"

        statement = (
            select(Asset)
            .where(
                (Asset.name.ilike(search_text))
                | (Asset.code.ilike(search_text))
                | (
                    Asset.external_id.ilike(
                        search_text
                    )
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(Asset.name.asc())
        )

        return list(self.db.scalars(statement).all())

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        asset: Asset,
        values: dict[str, Any],
    ) -> Asset:
        """
        Update an existing asset.

        Args:
            asset: Asset model instance.
            values: Dictionary containing fields to update.

        Returns:
            Updated Asset instance.
        """
        for field, value in values.items():
            if hasattr(asset, field):
                setattr(asset, field, value)

        self.db.commit()
        self.db.refresh(asset)

        return asset

    # ========================================================
    # DELETE
    # ========================================================

    def delete(self, asset: Asset) -> None:
        """
        Delete an asset from the database.

        Args:
            asset: Asset model instance.
        """
        self.db.delete(asset)
        self.db.commit()

    # ========================================================
    # EXISTS
    # ========================================================

    def exists(self, asset_id: str) -> bool:
        """
        Check whether an asset exists.

        Args:
            asset_id: Asset ID.

        Returns:
            True if the asset exists, otherwise False.
        """
        return self.get_by_id(asset_id) is not None

    # ========================================================
    # COUNT
    # ========================================================

    def count(self) -> int:
        """
        Return the total number of assets.

        Returns:
            Number of assets.
        """
        from sqlalchemy import func

        statement = select(
            func.count(Asset.id)
        )

        return int(self.db.scalar(statement) or 0)