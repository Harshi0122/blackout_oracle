"""
Blackout Oracle - Digital Twin Simulation.

Provides a lightweight digital-twin layer for representing the
current electrical-grid state and running what-if simulations
against a copy of that state.

This module intentionally stays independent of any specific
power-system solver. A solver can be attached through the
``solver`` interface when higher-fidelity simulation is required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

from app.simulation.base import (
    SimulationConfig,
    SimulationEvent,
    SimulationMetrics,
    SimulationResult,
    SimulationSeverity,
    SimulationState,
    SimulationStatus,
    SimulationType,
)
from app.simulation.contingency import (
    ContingencyCase,
    ContingencyResult,
    ContingencySimulator,
)


# ============================================================
# DIGITAL-TWIN ASSET
# ============================================================


@dataclass
class TwinAsset:
    """
    Representation of a physical grid asset inside the digital twin.
    """

    asset_id: int

    asset_type: str

    name: str | None = None

    latitude: float | None = None

    longitude: float | None = None

    rated_power_mw: float | None = None

    rated_voltage_kv: float | None = None

    status: str = "active"

    loading_percent: float = 0.0

    voltage_pu: float | None = None

    frequency_hz: float | None = None

    active_power_mw: float = 0.0

    reactive_power_mvar: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def copy(self) -> "TwinAsset":
        """Return an independent copy of the asset."""

        return TwinAsset(
            asset_id=self.asset_id,
            asset_type=self.asset_type,
            name=self.name,
            latitude=self.latitude,
            longitude=self.longitude,
            rated_power_mw=self.rated_power_mw,
            rated_voltage_kv=self.rated_voltage_kv,
            status=self.status,
            loading_percent=self.loading_percent,
            voltage_pu=self.voltage_pu,
            frequency_hz=self.frequency_hz,
            active_power_mw=self.active_power_mw,
            reactive_power_mvar=self.reactive_power_mvar,
            metadata=dict(self.metadata),
        )

    @property
    def is_online(self) -> bool:
        """Return whether the asset is currently online."""

        return self.status.lower() in {
            "active",
            "online",
            "connected",
            "in_service",
            "in-service",
        }

    @property
    def is_failed(self) -> bool:
        """Return whether the asset has failed."""

        return self.status.lower() in {
            "failed",
            "offline",
            "outage",
            "tripped",
            "disconnected",
        }

    @property
    def is_overloaded(self) -> bool:
        """Return whether the asset exceeds its loading limit."""

        return self.loading_percent >= 100.0

    def fail(self) -> None:
        """Take the asset out of service."""

        self.status = "failed"

    def restore(self) -> None:
        """Restore the asset to service."""

        self.status = "active"

    def to_dict(self) -> dict[str, Any]:
        """Convert the asset to a dictionary."""

        return {
            "asset_id": self.asset_id,
            "asset_type": self.asset_type,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "rated_power_mw": self.rated_power_mw,
            "rated_voltage_kv": self.rated_voltage_kv,
            "status": self.status,
            "loading_percent": self.loading_percent,
            "voltage_pu": self.voltage_pu,
            "frequency_hz": self.frequency_hz,
            "active_power_mw": self.active_power_mw,
            "reactive_power_mvar": self.reactive_power_mvar,
            "metadata": dict(self.metadata),
        }


# ============================================================
# DIGITAL-TWIN SNAPSHOT
# ============================================================


@dataclass
class TwinSnapshot:
    """
    Point-in-time snapshot of the digital twin.
    """

    timestamp: datetime

    assets: dict[int, TwinAsset] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    source: str | None = None

    version: str | None = None

    def copy(self) -> "TwinSnapshot":
        """Return an independent copy."""

        return TwinSnapshot(
            timestamp=self.timestamp,
            assets={
                asset_id: asset.copy()
                for asset_id, asset in self.assets.items()
            },
            metadata=dict(self.metadata),
            source=self.source,
            version=self.version,
        )

    def get_asset(
        self,
        asset_id: int,
    ) -> TwinAsset | None:
        """Return an asset by ID."""

        return self.assets.get(
            int(asset_id)
        )

    def add_asset(
        self,
        asset: TwinAsset,
    ) -> None:
        """Add or replace an asset."""

        self.assets[
            int(asset.asset_id)
        ] = asset

    def remove_asset(
        self,
        asset_id: int,
    ) -> TwinAsset | None:
        """Remove an asset and return it."""

        return self.assets.pop(
            int(asset_id),
            None,
        )

    def online_assets(self) -> list[TwinAsset]:
        """Return all currently online assets."""

        return [
            asset
            for asset in self.assets.values()
            if asset.is_online
        ]

    def failed_assets(self) -> list[TwinAsset]:
        """Return all failed assets."""

        return [
            asset
            for asset in self.assets.values()
            if asset.is_failed
        ]

    def overloaded_assets(self) -> list[TwinAsset]:
        """Return all overloaded assets."""

        return [
            asset
            for asset in self.assets.values()
            if asset.is_overloaded
        ]

    def to_simulation_state(self) -> SimulationState:
        """
        Convert the digital-twin snapshot into the generic
        SimulationState representation.
        """

        state = SimulationState(
            timestamp=self.timestamp
        )

        for asset_id, asset in self.assets.items():
            state.asset_status[
                asset_id
            ] = asset.status

            state.loading[
                asset_id
            ] = asset.loading_percent

            if asset.voltage_pu is not None:
                state.voltage[
                    asset_id
                ] = asset.voltage_pu

            if asset.frequency_hz is not None:
                state.frequency[
                    asset_id
                ] = asset.frequency_hz

            state.active_power[
                asset_id
            ] = asset.active_power_mw

            state.reactive_power[
                asset_id
            ] = asset.reactive_power_mvar

            if asset.is_failed:
                state.failed_assets.add(
                    asset_id
                )

            if asset.is_overloaded:
                state.overloaded_assets.add(
                    asset_id
                )

        state.metadata.update(
            self.metadata
        )

        state.metadata[
            "twin_source"
        ] = self.source

        state.metadata[
            "twin_version"
        ] = self.version

        return state

    @classmethod
    def from_simulation_state(
        cls,
        state: SimulationState,
        *,
        existing_assets: dict[int, TwinAsset] | None = None,
        source: str | None = None,
        version: str | None = None,
    ) -> "TwinSnapshot":
        """
        Build a twin snapshot from a SimulationState.

        Existing asset metadata is retained whenever an asset with
        the same ID already exists.
        """

        existing_assets = (
            existing_assets or {}
        )

        assets: dict[int, TwinAsset] = {}

        asset_ids = set(
            state.asset_status.keys()
        )

        asset_ids.update(
            state.loading.keys()
        )

        asset_ids.update(
            state.voltage.keys()
        )

        asset_ids.update(
            state.frequency.keys()
        )

        asset_ids.update(
            state.active_power.keys()
        )

        for asset_id in asset_ids:
            previous = existing_assets.get(
                asset_id
            )

            status = state.asset_status.get(
                asset_id,
                (
                    "failed"
                    if asset_id
                    in state.failed_assets
                    else "active"
                ),
            )

            asset = (
                previous.copy()
                if previous is not None
                else TwinAsset(
                    asset_id=int(asset_id),
                    asset_type="unknown",
                )
            )

            asset.status = str(
                status
            )

            if asset_id in state.failed_assets:
                asset.status = "failed"

            asset.loading_percent = float(
                state.loading.get(
                    asset_id,
                    asset.loading_percent,
                )
            )

            if asset_id in state.voltage:
                asset.voltage_pu = float(
                    state.voltage[
                        asset_id
                    ]
                )

            if asset_id in state.frequency:
                asset.frequency_hz = float(
                    state.frequency[
                        asset_id
                    ]
                )

            asset.active_power_mw = float(
                state.active_power.get(
                    asset_id,
                    asset.active_power_mw,
                )
            )

            asset.reactive_power_mvar = float(
                state.reactive_power.get(
                    asset_id,
                    asset.reactive_power_mvar,
                )
            )

            assets[
                int(asset_id)
            ] = asset

        return cls(
            timestamp=state.timestamp,
            assets=assets,
            metadata=dict(
                state.metadata
            ),
            source=source,
            version=version,
        )


# ============================================================
# DIGITAL-TWIN CHANGE
# ============================================================


@dataclass
class TwinChange:
    """
    Describes a change made to the digital twin.
    """

    asset_id: int

    field: str

    old_value: Any

    new_value: Any

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the change to a dictionary."""

        return {
            "asset_id": self.asset_id,
            "field": self.field,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
        }


# ============================================================
# DIGITAL-TWIN STATE
# ============================================================


@dataclass
class DigitalTwinState:
    """
    Runtime state maintained by the digital twin.
    """

    snapshot: TwinSnapshot

    previous_snapshot: TwinSnapshot | None = None

    changes: list[TwinChange] = field(
        default_factory=list
    )

    synchronized_at: datetime | None = None

    sync_source: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def copy(self) -> "DigitalTwinState":
        """Return an independent copy."""

        return DigitalTwinState(
            snapshot=self.snapshot.copy(),
            previous_snapshot=(
                self.previous_snapshot.copy()
                if self.previous_snapshot is not None
                else None
            ),
            changes=list(
                self.changes
            ),
            synchronized_at=self.synchronized_at,
            sync_source=self.sync_source,
            metadata=dict(
                self.metadata
            ),
        )


# ============================================================
# DIGITAL TWIN
# ============================================================


class DigitalTwin:
    """
    Main digital-twin interface.

    The twin maintains a normalized representation of grid assets
    and provides controlled operations for:

    - synchronization with incoming state,
    - asset updates,
    - failure injection,
    - restoration,
    - what-if simulation,
    - contingency analysis,
    - state comparison.
    """

    def __init__(
        self,
        assets: Iterable[TwinAsset] | None = None,
        *,
        source: str | None = None,
        version: str | None = None,
    ) -> None:
        now = datetime.now(
            timezone.utc
        )

        asset_map = {
            int(asset.asset_id): asset.copy()
            for asset in (
                assets or []
            )
        }

        self.state = DigitalTwinState(
            snapshot=TwinSnapshot(
                timestamp=now,
                assets=asset_map,
                source=source,
                version=version,
            )
        )

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def assets(self) -> dict[int, TwinAsset]:
        """Return the current asset map."""

        return self.state.snapshot.assets

    @property
    def timestamp(self) -> datetime:
        """Return the current twin timestamp."""

        return self.state.snapshot.timestamp

    @property
    def version(self) -> str | None:
        """Return the current twin version."""

        return self.state.snapshot.version

    # ========================================================
    # ASSET MANAGEMENT
    # ========================================================

    def add_asset(
        self,
        asset: TwinAsset,
    ) -> None:
        """Add an asset to the twin."""

        self.state.snapshot.add_asset(
            asset.copy()
        )

    def get_asset(
        self,
        asset_id: int,
    ) -> TwinAsset | None:
        """Retrieve an asset."""

        return self.state.snapshot.get_asset(
            asset_id
        )

    def update_asset(
        self,
        asset_id: int,
        *,
        reason: str | None = None,
        **updates: Any,
    ) -> TwinAsset:
        """
        Update selected fields of an asset.

        Raises:
            KeyError: If the asset does not exist.
            AttributeError: If an invalid field is supplied.
        """

        asset = self.get_asset(
            asset_id
        )

        if asset is None:
            raise KeyError(
                f"Asset {asset_id} does not exist in the digital twin."
            )

        allowed_fields = {
            "asset_type",
            "name",
            "latitude",
            "longitude",
            "rated_power_mw",
            "rated_voltage_kv",
            "status",
            "loading_percent",
            "voltage_pu",
            "frequency_hz",
            "active_power_mw",
            "reactive_power_mvar",
            "metadata",
        }

        self.state.previous_snapshot = (
            self.state.snapshot.copy()
        )

        for field_name, new_value in updates.items():
            if field_name not in allowed_fields:
                raise AttributeError(
                    f"Unsupported twin asset field: {field_name}"
                )

            old_value = getattr(
                asset,
                field_name,
            )

            if field_name == "metadata":
                new_value = dict(
                    new_value or {}
                )

            setattr(
                asset,
                field_name,
                new_value,
            )

            self.state.changes.append(
                TwinChange(
                    asset_id=int(asset_id),
                    field=field_name,
                    old_value=old_value,
                    new_value=new_value,
                    reason=reason,
                )
            )

        self.state.snapshot.timestamp = (
            datetime.now(
                timezone.utc
            )
        )

        return asset

    # ========================================================
    # FAILURE / RESTORATION
    # ========================================================

    def fail_asset(
        self,
        asset_id: int,
        *,
        reason: str = "manual_failure",
    ) -> TwinAsset:
        """Inject an asset failure into the twin."""

        return self.update_asset(
            asset_id,
            status="failed",
            reason=reason,
        )

    def restore_asset(
        self,
        asset_id: int,
        *,
        reason: str = "manual_restoration",
    ) -> TwinAsset:
        """Restore an asset in the twin."""

        return self.update_asset(
            asset_id,
            status="active",
            reason=reason,
        )

    def set_loading(
        self,
        asset_id: int,
        loading_percent: float,
        *,
        reason: str = "telemetry_update",
    ) -> TwinAsset:
        """Update asset loading."""

        return self.update_asset(
            asset_id,
            loading_percent=max(
                0.0,
                float(loading_percent),
            ),
            reason=reason,
        )

    def set_voltage(
        self,
        asset_id: int,
        voltage_pu: float,
        *,
        reason: str = "telemetry_update",
    ) -> TwinAsset:
        """Update asset voltage."""

        return self.update_asset(
            asset_id,
            voltage_pu=float(
                voltage_pu
            ),
            reason=reason,
        )

    # ========================================================
    # SYNCHRONIZATION
    # ========================================================

    def synchronize(
        self,
        state: SimulationState,
        *,
        source: str | None = None,
        version: str | None = None,
        preserve_unknown_assets: bool = True,
    ) -> TwinSnapshot:
        """
        Synchronize the digital twin with a new SimulationState.

        Existing asset metadata such as name, type, coordinates, and
        ratings is preserved where possible.
        """

        previous = self.state.snapshot.copy()

        updated = TwinSnapshot.from_simulation_state(
            state,
            existing_assets=self.assets,
            source=source,
            version=version,
        )

        if preserve_unknown_assets:
            for asset_id, asset in self.assets.items():
                if asset_id not in updated.assets:
                    updated.assets[
                        asset_id
                    ] = asset.copy()

        self.state.previous_snapshot = previous
        self.state.snapshot = updated
        self.state.synchronized_at = (
            datetime.now(
                timezone.utc
            )
        )
        self.state.sync_source = source

        return updated

    def synchronize_assets(
        self,
        assets: Iterable[TwinAsset],
        *,
        source: str | None = None,
        version: str | None = None,
    ) -> TwinSnapshot:
        """
        Synchronize using a collection of TwinAsset objects.
        """

        previous = self.state.snapshot.copy()

        asset_map = {
            int(asset.asset_id): asset.copy()
            for asset in assets
        }

        self.state.previous_snapshot = previous

        self.state.snapshot = TwinSnapshot(
            timestamp=datetime.now(
                timezone.utc
            ),
            assets=asset_map,
            source=source,
            version=version,
        )

        self.state.synchronized_at = (
            datetime.now(
                timezone.utc
            )
        )

        self.state.sync_source = source

        return self.state.snapshot

    # ========================================================
    # SNAPSHOTS
    # ========================================================

    def snapshot(self) -> TwinSnapshot:
        """Return an immutable-style copy of the current state."""

        return self.state.snapshot.copy()

    def restore_snapshot(
        self,
        snapshot: TwinSnapshot,
        *,
        reason: str = "snapshot_restore",
    ) -> None:
        """Restore the twin from a snapshot."""

        self.state.previous_snapshot = (
            self.state.snapshot.copy()
        )

        self.state.snapshot = snapshot.copy()

        self.state.metadata[
            "last_restore_reason"
        ] = reason

    # ========================================================
    # SIMULATION STATE
    # ========================================================

    def to_simulation_state(
        self,
    ) -> SimulationState:
        """Convert the current twin into a simulation state."""

        return self.state.snapshot.to_simulation_state()

    # ========================================================
    # WHAT-IF SIMULATION
    # ========================================================

    def simulate(
        self,
        *,
        events: Iterable[SimulationEvent] | None = None,
        config: SimulationConfig | None = None,
        simulator: Any | None = None,
    ) -> SimulationResult:
        """
        Run a what-if simulation against a copy of the current twin.

        The real digital twin is not modified.
        """

        simulation_state = (
            self.to_simulation_state()
        )

        simulation_events = list(
            events or []
        )

        if simulator is None:
            simulator = ContingencySimulator(
                config=config
            )

        return simulator.run(
            simulation_state,
            simulation_events,
        )

    # ========================================================
    # CONTINGENCY SIMULATION
    # ========================================================

    def simulate_contingency(
        self,
        case: ContingencyCase,
        *,
        config: SimulationConfig | None = None,
        simulator: ContingencySimulator | None = None,
    ) -> ContingencyResult:
        """
        Run a contingency against a copy of the current twin.
        """

        if simulator is None:
            simulator = ContingencySimulator(
                config=config
            )

        return simulator.run_contingency(
            self.to_simulation_state(),
            case,
        )

    def run_n_minus_one(
        self,
        *,
        asset_ids: Iterable[int] | None = None,
        config: SimulationConfig | None = None,
    ) -> list[ContingencyResult]:
        """
        Run N-1 contingency analysis for the current twin.
        """

        simulator = ContingencySimulator(
            config=config
        )

        state = self.to_simulation_state()

        if asset_ids is None:
            asset_ids = self.assets.keys()

        return simulator.run_n_minus_one(
            state,
            asset_ids,
        )

    # ========================================================
    # STATE COMPARISON
    # ========================================================

    def compare(
        self,
        snapshot: TwinSnapshot,
    ) -> list[TwinChange]:
        """
        Compare the current twin against another snapshot.

        Returns the changes required to transform the supplied
        snapshot into the current state.
        """

        changes: list[TwinChange] = []

        all_asset_ids = set(
            self.assets.keys()
        )

        all_asset_ids.update(
            snapshot.assets.keys()
        )

        fields = (
            "status",
            "loading_percent",
            "voltage_pu",
            "frequency_hz",
            "active_power_mw",
            "reactive_power_mvar",
        )

        for asset_id in sorted(
            all_asset_ids
        ):
            current = self.assets.get(
                asset_id
            )

            previous = snapshot.assets.get(
                asset_id
            )

            if current is None:
                changes.append(
                    TwinChange(
                        asset_id=asset_id,
                        field="asset",
                        old_value=(
                            previous.to_dict()
                            if previous is not None
                            else None
                        ),
                        new_value=None,
                        reason="asset_removed",
                    )
                )
                continue

            if previous is None:
                changes.append(
                    TwinChange(
                        asset_id=asset_id,
                        field="asset",
                        old_value=None,
                        new_value=current.to_dict(),
                        reason="asset_added",
                    )
                )
                continue

            for field_name in fields:
                old_value = getattr(
                    previous,
                    field_name,
                )

                new_value = getattr(
                    current,
                    field_name,
                )

                if old_value != new_value:
                    changes.append(
                        TwinChange(
                            asset_id=asset_id,
                            field=field_name,
                            old_value=old_value,
                            new_value=new_value,
                            reason="state_change",
                        )
                    )

        return changes

    # ========================================================
    # HEALTH
    # ========================================================

    def health_summary(
        self,
    ) -> dict[str, Any]:
        """
        Return a compact health summary of the twin.
        """

        assets = list(
            self.assets.values()
        )

        failed = [
            asset
            for asset in assets
            if asset.is_failed
        ]

        overloaded = [
            asset
            for asset in assets
            if asset.is_overloaded
        ]

        online = [
            asset
            for asset in assets
            if asset.is_online
        ]

        voltage_values = [
            asset.voltage_pu
            for asset in assets
            if asset.voltage_pu is not None
        ]

        frequency_values = [
            asset.frequency_hz
            for asset in assets
            if asset.frequency_hz is not None
        ]

        loading_values = [
            asset.loading_percent
            for asset in assets
        ]

        return {
            "timestamp": self.timestamp.isoformat(),
            "asset_count": len(assets),
            "online_assets": len(online),
            "failed_assets": len(failed),
            "overloaded_assets": len(overloaded),
            "minimum_voltage_pu": (
                min(voltage_values)
                if voltage_values
                else None
            ),
            "maximum_voltage_pu": (
                max(voltage_values)
                if voltage_values
                else None
            ),
            "minimum_frequency_hz": (
                min(frequency_values)
                if frequency_values
                else None
            ),
            "maximum_frequency_hz": (
                max(frequency_values)
                if frequency_values
                else None
            ),
            "maximum_loading_percent": (
                max(loading_values)
                if loading_values
                else 0.0
            ),
            "synchronized_at": (
                self.state.synchronized_at.isoformat()
                if self.state.synchronized_at is not None
                else None
            ),
            "sync_source": self.state.sync_source,
            "version": self.version,
        }

    # ========================================================
    # RISK ESTIMATION
    # ========================================================

    def estimate_risk(
        self,
    ) -> float:
        """
        Estimate current twin risk on a 0-100 scale.

        This is a lightweight deterministic health score. The full
        Blackout Oracle risk engine should be used for production
        risk assessment.
        """

        assets = list(
            self.assets.values()
        )

        if not assets:
            return 0.0

        failed_score = min(
            35.0,
            sum(
                1.0
                for asset in assets
                if asset.is_failed
            )
            / len(assets)
            * 100.0,
        )

        overloaded_score = min(
            25.0,
            sum(
                1.0
                for asset in assets
                if asset.is_overloaded
            )
            / len(assets)
            * 100.0,
        )

        voltage_penalty = 0.0

        for asset in assets:
            if asset.voltage_pu is None:
                continue

            if asset.voltage_pu < 0.90:
                voltage_penalty += min(
                    5.0,
                    (0.90 - asset.voltage_pu)
                    * 100.0,
                )

            elif asset.voltage_pu > 1.10:
                voltage_penalty += min(
                    5.0,
                    (asset.voltage_pu - 1.10)
                    * 100.0,
                )

        voltage_penalty = min(
            20.0,
            voltage_penalty,
        )

        frequency_penalty = 0.0

        for asset in assets:
            if asset.frequency_hz is None:
                continue

            if asset.frequency_hz < 49.0:
                frequency_penalty += min(
                    5.0,
                    (49.0 - asset.frequency_hz)
                    * 5.0,
                )

            elif asset.frequency_hz > 51.0:
                frequency_penalty += min(
                    5.0,
                    (asset.frequency_hz - 51.0)
                    * 5.0,
                )

        frequency_penalty = min(
            20.0,
            frequency_penalty,
        )

        return max(
            0.0,
            min(
                100.0,
                failed_score
                + overloaded_score
                + voltage_penalty
                + frequency_penalty,
            ),
        )

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(self) -> dict[str, Any]:
        """Serialize the complete digital twin."""

        return {
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "source": self.state.snapshot.source,
            "assets": [
                asset.to_dict()
                for asset in self.assets.values()
            ],
            "health": self.health_summary(),
            "estimated_risk_score": self.estimate_risk(),
            "metadata": dict(
                self.state.snapshot.metadata
            ),
        }


# ============================================================
# DIGITAL-TWIN BUILDER
# ============================================================


class DigitalTwinBuilder:
    """
    Fluent builder for constructing a DigitalTwin.
    """

    def __init__(self) -> None:
        self._assets: list[TwinAsset] = []
        self._source: str | None = None
        self._version: str | None = None

    def asset(
        self,
        asset: TwinAsset,
    ) -> "DigitalTwinBuilder":
        """Add an asset."""

        self._assets.append(
            asset
        )

        return self

    def source(
        self,
        source: str,
    ) -> "DigitalTwinBuilder":
        """Set the data source."""

        self._source = source

        return self

    def version(
        self,
        version: str,
    ) -> "DigitalTwinBuilder":
        """Set the twin version."""

        self._version = version

        return self

    def build(self) -> DigitalTwin:
        """Build the digital twin."""

        return DigitalTwin(
            assets=self._assets,
            source=self._source,
            version=self._version,
        )


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def build_twin_from_state(
    state: SimulationState,
    *,
    source: str | None = None,
    version: str | None = None,
) -> DigitalTwin:
    """
    Create a DigitalTwin from a SimulationState.
    """

    snapshot = TwinSnapshot.from_simulation_state(
        state,
        source=source,
        version=version,
    )

    twin = DigitalTwin(
        source=source,
        version=version,
    )

    twin.restore_snapshot(
        snapshot,
        reason="state_initialization",
    )

    return twin


def create_failure_event(
    asset_id: int,
    *,
    timestamp: datetime | None = None,
    severity: SimulationSeverity = (
        SimulationSeverity.HIGH
    ),
    reason: str = "digital_twin_failure",
) -> SimulationEvent:
    """
    Create a standard digital-twin asset-failure event.
    """

    return SimulationEvent(
        event_type="asset_failure",
        asset_id=int(asset_id),
        timestamp=timestamp,
        severity=severity,
        description=reason,
    )


def create_restoration_event(
    asset_id: int,
    *,
    timestamp: datetime | None = None,
) -> SimulationEvent:
    """
    Create a standard asset-restoration event.
    """

    return SimulationEvent(
        event_type="asset_restoration",
        asset_id=int(asset_id),
        timestamp=timestamp,
        severity=SimulationSeverity.LOW,
        description=(
            f"Restoration of asset {asset_id}."
        ),
    )


__all__ = [
    "TwinAsset",
    "TwinSnapshot",
    "TwinChange",
    "DigitalTwinState",
    "DigitalTwin",
    "DigitalTwinBuilder",
    "build_twin_from_state",
    "create_failure_event",
    "create_restoration_event",
]