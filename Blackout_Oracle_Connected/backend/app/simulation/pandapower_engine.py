"""
Blackout Oracle - pandapower Simulation Engine.

Provides an optional pandapower-backed power-flow engine for the
digital-twin and contingency-simulation layers.

The engine converts the application's generic SimulationState into
a pandapower network, executes a power-flow calculation, and converts
the resulting electrical quantities back into SimulationState.

pandapower is imported lazily so that the rest of the Blackout Oracle
application can still start when the optional dependency is not
installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from app.simulation.base import (
    BaseSimulator,
    SimulationConfig,
    SimulationContext,
    SimulationEvent,
    SimulationSeverity,
    SimulationState,
    SimulationType,
)


# ============================================================
# OPTIONAL DEPENDENCY
# ============================================================


def _load_pandapower() -> Any:
    """
    Lazily import pandapower.

    Raises:
        RuntimeError: If pandapower is not installed.
    """

    try:
        import pandapower as pp

        return pp

    except ImportError as exc:
        raise RuntimeError(
            "pandapower is not installed. "
            "Install it with: pip install pandapower"
        ) from exc


# ============================================================
# CONFIGURATION
# ============================================================


@dataclass
class PandaPowerConfig:
    """
    Configuration for the pandapower engine.
    """

    algorithm: str = "nr"

    calculate_voltage_angles: bool = True

    init: str = "auto"

    enforce_q_lims: bool = True

    tolerance_mva: float = 1e-8

    maximum_iterations: int = 30

    check_connectivity: bool = True

    distributed_slack: bool = False

    numba: bool = False

    recycle: bool = False

    voltage_min_pu: float = 0.90

    voltage_max_pu: float = 1.10

    frequency_min_hz: float = 49.0

    frequency_max_hz: float = 51.0

    loading_limit_percent: float = 100.0

    base_frequency_hz: float = 50.0

    default_voltage_kv: float = 110.0

    default_line_length_km: float = 1.0

    default_line_r_ohm_per_km: float = 0.1

    default_line_x_ohm_per_km: float = 0.1

    default_line_c_nf_per_km: float = 10.0

    default_line_max_i_ka: float = 1.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self.tolerance_mva = max(
            1e-12,
            float(self.tolerance_mva),
        )

        self.maximum_iterations = max(
            1,
            int(self.maximum_iterations),
        )

        self.voltage_min_pu = float(
            self.voltage_min_pu
        )

        self.voltage_max_pu = float(
            self.voltage_max_pu
        )

        self.frequency_min_hz = float(
            self.frequency_min_hz
        )

        self.frequency_max_hz = float(
            self.frequency_max_hz
        )

        self.loading_limit_percent = max(
            0.0,
            float(self.loading_limit_percent),
        )

        self.base_frequency_hz = max(
            0.1,
            float(self.base_frequency_hz),
        )

        self.default_voltage_kv = max(
            0.001,
            float(self.default_voltage_kv),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the configuration."""

        return {
            "algorithm": self.algorithm,
            "calculate_voltage_angles": (
                self.calculate_voltage_angles
            ),
            "init": self.init,
            "enforce_q_lims": self.enforce_q_lims,
            "tolerance_mva": self.tolerance_mva,
            "maximum_iterations": (
                self.maximum_iterations
            ),
            "check_connectivity": (
                self.check_connectivity
            ),
            "distributed_slack": (
                self.distributed_slack
            ),
            "numba": self.numba,
            "recycle": self.recycle,
            "voltage_min_pu": (
                self.voltage_min_pu
            ),
            "voltage_max_pu": (
                self.voltage_max_pu
            ),
            "frequency_min_hz": (
                self.frequency_min_hz
            ),
            "frequency_max_hz": (
                self.frequency_max_hz
            ),
            "loading_limit_percent": (
                self.loading_limit_percent
            ),
            "base_frequency_hz": (
                self.base_frequency_hz
            ),
            "default_voltage_kv": (
                self.default_voltage_kv
            ),
            "metadata": dict(self.metadata),
        }


# ============================================================
# NETWORK DESCRIPTION
# ============================================================


@dataclass
class PandaPowerAsset:
    """
    Description of an asset used to construct a pandapower network.
    """

    asset_id: int

    asset_type: str

    name: str | None = None

    bus_id: int | None = None

    from_bus: int | None = None

    to_bus: int | None = None

    voltage_kv: float | None = None

    active_power_mw: float = 0.0

    reactive_power_mvar: float = 0.0

    rated_power_mw: float | None = None

    length_km: float | None = None

    resistance_ohm_per_km: float | None = None

    reactance_ohm_per_km: float | None = None

    capacitance_nf_per_km: float | None = None

    max_current_ka: float | None = None

    status: str = "active"

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def is_online(self) -> bool:
        """Return whether the asset is in service."""

        return self.status.lower() in {
            "active",
            "online",
            "connected",
            "in_service",
            "in-service",
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize the asset."""

        return {
            "asset_id": self.asset_id,
            "asset_type": self.asset_type,
            "name": self.name,
            "bus_id": self.bus_id,
            "from_bus": self.from_bus,
            "to_bus": self.to_bus,
            "voltage_kv": self.voltage_kv,
            "active_power_mw": self.active_power_mw,
            "reactive_power_mvar": (
                self.reactive_power_mvar
            ),
            "rated_power_mw": self.rated_power_mw,
            "length_km": self.length_km,
            "resistance_ohm_per_km": (
                self.resistance_ohm_per_km
            ),
            "reactance_ohm_per_km": (
                self.reactance_ohm_per_km
            ),
            "capacitance_nf_per_km": (
                self.capacitance_nf_per_km
            ),
            "max_current_ka": (
                self.max_current_ka
            ),
            "status": self.status,
            "metadata": dict(self.metadata),
        }


# ============================================================
# ENGINE
# ============================================================


class PandaPowerEngine:
    """
    Low-level wrapper around pandapower.

    The engine can either receive an already-created pandapower
    network or construct a simple network from PandaPowerAsset
    descriptions.
    """

    def __init__(
        self,
        *,
        config: PandaPowerConfig | None = None,
        network: Any | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else PandaPowerConfig()
        )

        self.network = network

        self._pp: Any | None = None

        self.last_error: str | None = None

        self.last_converged: bool | None = None

    # ========================================================
    # DEPENDENCY
    # ========================================================

    @property
    def pp(self) -> Any:
        """Return the lazily loaded pandapower module."""

        if self._pp is None:
            self._pp = _load_pandapower()

        return self._pp

    # ========================================================
    # NETWORK
    # ========================================================

    def create_network(self) -> Any:
        """Create an empty pandapower network."""

        self.network = self.pp.create_empty_network(
            sn_mva=100.0,
            f_hz=self.config.base_frequency_hz,
        )

        return self.network

    def get_network(self) -> Any:
        """Return the current network, creating one if necessary."""

        if self.network is None:
            return self.create_network()

        return self.network

    # ========================================================
    # BUILD NETWORK
    # ========================================================

    def build_network(
        self,
        assets: Iterable[PandaPowerAsset],
    ) -> Any:
        """
        Construct a pandapower network from generic asset
        descriptions.

        The method supports common asset types:

        - bus
        - load
        - generator / gen
        - external_grid / slack
        - line
        - transformer
        """

        pp = self.pp

        net = pp.create_empty_network(
            sn_mva=100.0,
            f_hz=self.config.base_frequency_hz,
        )

        assets = list(
            assets
        )

        bus_map: dict[int, int] = {}

        # ----------------------------------------------------
        # BUSES
        # ----------------------------------------------------

        bus_assets = [
            asset
            for asset in assets
            if self._is_type(
                asset.asset_type,
                "bus",
                "substation",
                "node",
            )
        ]

        for asset in bus_assets:
            voltage_kv = (
                asset.voltage_kv
                or self.config.default_voltage_kv
            )

            pp_bus_id = pp.create_bus(
                net,
                vn_kv=float(
                    voltage_kv
                ),
                name=(
                    asset.name
                    or f"Bus {asset.asset_id}"
                ),
                in_service=asset.is_online,
            )

            bus_map[
                asset.asset_id
            ] = pp_bus_id

        # ----------------------------------------------------
        # AUTO-CREATE MISSING BUSES
        # ----------------------------------------------------

        for asset in assets:
            referenced_ids = []

            if asset.bus_id is not None:
                referenced_ids.append(
                    asset.bus_id
                )

            if asset.from_bus is not None:
                referenced_ids.append(
                    asset.from_bus
                )

            if asset.to_bus is not None:
                referenced_ids.append(
                    asset.to_bus
                )

            for bus_asset_id in referenced_ids:
                if bus_asset_id in bus_map:
                    continue

                voltage_kv = (
                    asset.voltage_kv
                    or self.config.default_voltage_kv
                )

                pp_bus_id = pp.create_bus(
                    net,
                    vn_kv=float(
                        voltage_kv
                    ),
                    name=(
                        f"Bus {bus_asset_id}"
                    ),
                    in_service=True,
                )

                bus_map[
                    bus_asset_id
                ] = pp_bus_id

        # ----------------------------------------------------
        # EXTERNAL GRIDS
        # ----------------------------------------------------

        for asset in assets:
            if not self._is_type(
                asset.asset_type,
                "external_grid",
                "slack",
                "grid",
            ):
                continue

            bus_id = self._resolve_bus(
                asset,
                bus_map,
            )

            if bus_id is None:
                continue

            pp.create_ext_grid(
                net,
                bus=bus_id,
                vm_pu=self._initial_voltage(
                    asset
                ),
                va_degree=0.0,
                name=(
                    asset.name
                    or f"Grid {asset.asset_id}"
                ),
                in_service=asset.is_online,
            )

        # ----------------------------------------------------
        # GENERATORS
        # ----------------------------------------------------

        for asset in assets:
            if not self._is_type(
                asset.asset_type,
                "generator",
                "gen",
                "generating_unit",
            ):
                continue

            bus_id = self._resolve_bus(
                asset,
                bus_map,
            )

            if bus_id is None:
                continue

            max_p = (
                asset.rated_power_mw
                if asset.rated_power_mw
                is not None
                else max(
                    asset.active_power_mw,
                    0.0,
                )
                + 1000.0
            )

            pp.create_gen(
                net,
                bus=bus_id,
                p_mw=float(
                    asset.active_power_mw
                ),
                vm_pu=self._initial_voltage(
                    asset
                ),
                max_p_mw=float(
                    max_p
                ),
                in_service=asset.is_online,
                name=(
                    asset.name
                    or f"Generator {asset.asset_id}"
                ),
            )

        # ----------------------------------------------------
        # LOADS
        # ----------------------------------------------------

        for asset in assets:
            if not self._is_type(
                asset.asset_type,
                "load",
                "demand",
                "consumer",
                "load_point",
            ):
                continue

            bus_id = self._resolve_bus(
                asset,
                bus_map,
            )

            if bus_id is None:
                continue

            pp.create_load(
                net,
                bus=bus_id,
                p_mw=max(
                    0.0,
                    float(
                        asset.active_power_mw
                    ),
                ),
                q_mvar=float(
                    asset.reactive_power_mvar
                ),
                in_service=asset.is_online,
                name=(
                    asset.name
                    or f"Load {asset.asset_id}"
                ),
            )

        # ----------------------------------------------------
        # LINES
        # ----------------------------------------------------

        for asset in assets:
            if not self._is_type(
                asset.asset_type,
                "line",
                "transmission_line",
                "feeder",
            ):
                continue

            from_bus = self._resolve_bus_id(
                asset.from_bus,
                bus_map,
            )

            to_bus = self._resolve_bus_id(
                asset.to_bus,
                bus_map,
            )

            if (
                from_bus is None
                or to_bus is None
            ):
                continue

            length_km = (
                asset.length_km
                or self.config.default_line_length_km
            )

            r = (
                asset.resistance_ohm_per_km
                or self.config.default_line_r_ohm_per_km
            )

            x = (
                asset.reactance_ohm_per_km
                or self.config.default_line_x_ohm_per_km
            )

            c = (
                asset.capacitance_nf_per_km
                or self.config.default_line_c_nf_per_km
            )

            max_i = (
                asset.max_current_ka
                or self.config.default_line_max_i_ka
            )

            pp.create_line_from_parameters(
                net,
                from_bus=from_bus,
                to_bus=to_bus,
                length_km=float(
                    length_km
                ),
                r_ohm_per_km=float(
                    r
                ),
                x_ohm_per_km=float(
                    x
                ),
                c_nf_per_km=float(
                    c
                ),
                max_i_ka=float(
                    max_i
                ),
                in_service=asset.is_online,
                name=(
                    asset.name
                    or f"Line {asset.asset_id}"
                ),
            )

        # ----------------------------------------------------
        # TRANSFORMERS
        # ----------------------------------------------------

        for asset in assets:
            if not self._is_type(
                asset.asset_type,
                "transformer",
                "trafo",
            ):
                continue

            hv_bus = self._resolve_bus_id(
                asset.from_bus,
                bus_map,
            )

            lv_bus = self._resolve_bus_id(
                asset.to_bus,
                bus_map,
            )

            if (
                hv_bus is None
                or lv_bus is None
            ):
                continue

            hv_kv = (
                asset.metadata.get(
                    "hv_kv"
                )
                or asset.voltage_kv
                or self.config.default_voltage_kv
            )

            lv_kv = (
                asset.metadata.get(
                    "lv_kv"
                )
                or self.config.default_voltage_kv
            )

            sn_mva = (
                asset.rated_power_mw
                or asset.metadata.get(
                    "sn_mva"
                )
                or 100.0
            )

            vk_percent = float(
                asset.metadata.get(
                    "vk_percent",
                    10.0,
                )
            )

            vkr_percent = float(
                asset.metadata.get(
                    "vkr_percent",
                    0.5,
                )
            )

            pfe_kw = float(
                asset.metadata.get(
                    "pfe_kw",
                    0.0,
                )
            )

            i0_percent = float(
                asset.metadata.get(
                    "i0_percent",
                    0.0,
                )
            )

            pp.create_transformer_from_parameters(
                net,
                hv_bus=hv_bus,
                lv_bus=lv_bus,
                sn_mva=float(
                    sn_mva
                ),
                vn_hv_kv=float(
                    hv_kv
                ),
                vn_lv_kv=float(
                    lv_kv
                ),
                vk_percent=vk_percent,
                vkr_percent=vkr_percent,
                pfe_kw=pfe_kw,
                i0_percent=i0_percent,
                in_service=asset.is_online,
                name=(
                    asset.name
                    or f"Transformer {asset.asset_id}"
                ),
            )

        self.network = net

        return net

    # ========================================================
    # POWER FLOW
    # ========================================================

    def run_power_flow(
        self,
        *,
        network: Any | None = None,
    ) -> Any:
        """
        Execute pandapower power flow.

        Returns:
            The solved pandapower network.
        """

        net = (
            network
            if network is not None
            else self.get_network()
        )

        self.last_error = None
        self.last_converged = None

        try:
            self.pp.runpp(
                net,
                algorithm=self.config.algorithm,
                calculate_voltage_angles=(
                    self.config.calculate_voltage_angles
                ),
                init=self.config.init,
                enforce_q_lims=(
                    self.config.enforce_q_lims
                ),
                tolerance_mva=(
                    self.config.tolerance_mva
                ),
                max_iteration=(
                    self.config.maximum_iterations
                ),
                check_connectivity=(
                    self.config.check_connectivity
                ),
                distributed_slack=(
                    self.config.distributed_slack
                ),
                numba=self.config.numba,
                recycle=(
                    self.config.recycle
                    if self.config.recycle
                    else None
                ),
            )

            self.last_converged = bool(
                getattr(
                    net,
                    "converged",
                    True,
                )
            )

            return net

        except Exception as exc:
            self.last_error = str(
                exc
            )
            self.last_converged = False

            raise

    # ========================================================
    # APPLY EVENT
    # ========================================================

    def apply_event(
        self,
        event: SimulationEvent,
        *,
        network: Any | None = None,
    ) -> None:
        """
        Apply an outage/failure event to the pandapower network.

        Asset IDs are expected to be mapped to pandapower indices
        through the ``asset_id`` column where available.
        """

        net = (
            network
            if network is not None
            else self.get_network()
        )

        if event.asset_id is None:
            return

        asset_id = int(
            event.asset_id
        )

        event_type = event.event_type.lower()

        should_fail = any(
            keyword in event_type
            for keyword in (
                "fail",
                "outage",
                "trip",
                "disconnect",
            )
        )

        should_restore = any(
            keyword in event_type
            for keyword in (
                "restore",
                "restoration",
                "reconnect",
            )
        )

        if not (
            should_fail
            or should_restore
        ):
            return

        mapping = self._find_asset_mapping(
            net,
            asset_id,
        )

        for table_name, row_index in mapping:
            table = getattr(
                net,
                table_name,
            )

            if (
                "in_service"
                not in table.columns
            ):
                continue

            table.at[
                row_index,
                "in_service",
            ] = (
                not should_fail
                if should_restore
                else False
            )

    # ========================================================
    # APPLY EVENTS
    # ========================================================

    def apply_events(
        self,
        events: Iterable[SimulationEvent],
        *,
        network: Any | None = None,
    ) -> None:
        """Apply multiple events."""

        for event in events:
            self.apply_event(
                event,
                network=network,
            )

    # ========================================================
    # RESULT EXTRACTION
    # ========================================================

    def to_simulation_state(
        self,
        *,
        network: Any | None = None,
        timestamp: datetime | None = None,
    ) -> SimulationState:
        """
        Convert solved pandapower results to SimulationState.
        """

        net = (
            network
            if network is not None
            else self.get_network()
        )

        timestamp = (
            timestamp
            if timestamp is not None
            else datetime.now(
                timezone.utc
            )
        )

        state = SimulationState(
            timestamp=timestamp
        )

        self._extract_bus_results(
            net,
            state,
        )

        self._extract_line_results(
            net,
            state,
        )

        self._extract_transformer_results(
            net,
            state,
        )

        self._extract_generation_results(
            net,
            state,
        )

        self._extract_load_results(
            net,
            state,
        )

        state.metadata[
            "pandapower_converged"
        ] = bool(
            getattr(
                net,
                "converged",
                self.last_converged
                if self.last_converged is not None
                else False,
            )
        )

        state.metadata[
            "pandapower_algorithm"
        ] = self.config.algorithm

        if self.last_error:
            state.metadata[
                "pandapower_error"
            ] = self.last_error

        return state

    # ========================================================
    # BUS RESULTS
    # ========================================================

    def _extract_bus_results(
        self,
        net: Any,
        state: SimulationState,
    ) -> None:
        """Extract bus voltage results."""

        if not hasattr(
            net,
            "res_bus",
        ):
            return

        if net.res_bus.empty:
            return

        for index, row in net.res_bus.iterrows():
            asset_id = self._asset_id_from_table(
                net,
                "bus",
                index,
            )

            if asset_id is None:
                asset_id = int(
                    index
                )

            vm_pu = self._row_value(
                row,
                "vm_pu",
            )

            if vm_pu is not None:
                state.voltage[
                    asset_id
                ] = vm_pu

            state.asset_status[
                asset_id
            ] = (
                "active"
                if self._table_in_service(
                    net,
                    "bus",
                    index,
                )
                else "offline"
            )

    # ========================================================
    # LINE RESULTS
    # ========================================================

    def _extract_line_results(
        self,
        net: Any,
        state: SimulationState,
    ) -> None:
        """Extract line loading results."""

        if not hasattr(
            net,
            "res_line",
        ):
            return

        if net.res_line.empty:
            return

        for index, row in net.res_line.iterrows():
            asset_id = self._asset_id_from_table(
                net,
                "line",
                index,
            )

            if asset_id is None:
                asset_id = int(
                    index
                )

            loading = self._row_value(
                row,
                "loading_percent",
            )

            if loading is not None:
                state.loading[
                    asset_id
                ] = loading

                if (
                    loading
                    >= self.config.loading_limit_percent
                ):
                    state.overloaded_assets.add(
                        asset_id
                    )

            state.asset_status[
                asset_id
            ] = (
                "active"
                if self._table_in_service(
                    net,
                    "line",
                    index,
                )
                else "failed"
            )

            if (
                not self._table_in_service(
                    net,
                    "line",
                    index,
                )
            ):
                state.failed_assets.add(
                    asset_id
                )

    # ========================================================
    # TRANSFORMER RESULTS
    # ========================================================

    def _extract_transformer_results(
        self,
        net: Any,
        state: SimulationState,
    ) -> None:
        """Extract transformer loading results."""

        if not hasattr(
            net,
            "res_trafo",
        ):
            return

        if net.res_trafo.empty:
            return

        for index, row in net.res_trafo.iterrows():
            asset_id = self._asset_id_from_table(
                net,
                "trafo",
                index,
            )

            if asset_id is None:
                asset_id = int(
                    index
                )

            loading = self._row_value(
                row,
                "loading_percent",
            )

            if loading is not None:
                state.loading[
                    asset_id
                ] = loading

                if (
                    loading
                    >= self.config.loading_limit_percent
                ):
                    state.overloaded_assets.add(
                        asset_id
                    )

            state.asset_status[
                asset_id
            ] = (
                "active"
                if self._table_in_service(
                    net,
                    "trafo",
                    index,
                )
                else "failed"
            )

            if (
                not self._table_in_service(
                    net,
                    "trafo",
                    index,
                )
            ):
                state.failed_assets.add(
                    asset_id
                )

    # ========================================================
    # GENERATION RESULTS
    # ========================================================

    def _extract_generation_results(
        self,
        net: Any,
        state: SimulationState,
    ) -> None:
        """Extract generator active-power results."""

        generation_mw = 0.0

        if hasattr(
            net,
            "res_gen",
        ) and not net.res_gen.empty:
            generation_mw += float(
                net.res_gen[
                    "p_mw"
                ].sum()
            )

        if hasattr(
            net,
            "res_ext_grid",
        ) and not net.res_ext_grid.empty:
            generation_mw += float(
                net.res_ext_grid[
                    "p_mw"
                ].sum()
            )

        state.metadata[
            "generation_mw"
        ] = generation_mw

    # ========================================================
    # LOAD RESULTS
    # ========================================================

    def _extract_load_results(
        self,
        net: Any,
        state: SimulationState,
    ) -> None:
        """Extract load results."""

        if not hasattr(
            net,
            "res_load",
        ):
            return

        if net.res_load.empty:
            return

        total_load = 0.0

        for index, row in net.res_load.iterrows():
            asset_id = self._asset_id_from_table(
                net,
                "load",
                index,
            )

            if asset_id is None:
                asset_id = int(
                    index
                )

            p_mw = self._row_value(
                row,
                "p_mw",
            )

            q_mvar = self._row_value(
                row,
                "q_mvar",
            )

            if p_mw is not None:
                state.active_power[
                    asset_id
                ] = p_mw

                total_load += max(
                    0.0,
                    p_mw,
                )

            if q_mvar is not None:
                state.reactive_power[
                    asset_id
                ] = q_mvar

        state.metadata[
            "load_mw"
        ] = total_load

    # ========================================================
    # FULL SIMULATION
    # ========================================================

    def simulate(
        self,
        *,
        network: Any | None = None,
        events: Iterable[SimulationEvent] | None = None,
        timestamp: datetime | None = None,
    ) -> SimulationState:
        """
        Apply events, run power flow, and return SimulationState.
        """

        net = (
            network
            if network is not None
            else self.get_network()
        )

        events = list(
            events or []
        )

        self.apply_events(
            events,
            network=net,
        )

        self.run_power_flow(
            network=net
        )

        return self.to_simulation_state(
            network=net,
            timestamp=timestamp,
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def diagnostics(
        self,
        *,
        network: Any | None = None,
    ) -> dict[str, Any]:
        """
        Return a compact diagnostic summary.
        """

        net = (
            network
            if network is not None
            else self.get_network()
        )

        summary: dict[str, Any] = {
            "converged": getattr(
                net,
                "converged",
                self.last_converged,
            ),
            "last_error": self.last_error,
            "buses": self._table_length(
                net,
                "bus",
            ),
            "lines": self._table_length(
                net,
                "line",
            ),
            "transformers": self._table_length(
                net,
                "trafo",
            ),
            "loads": self._table_length(
                net,
                "load",
            ),
            "generators": self._table_length(
                net,
                "gen",
            ),
            "external_grids": self._table_length(
                net,
                "ext_grid",
            ),
        }

        if hasattr(
            net,
            "res_bus",
        ) and not net.res_bus.empty:
            summary[
                "minimum_voltage_pu"
            ] = float(
                net.res_bus[
                    "vm_pu"
                ].min()
            )

            summary[
                "maximum_voltage_pu"
            ] = float(
                net.res_bus[
                    "vm_pu"
                ].max()
            )

        if hasattr(
            net,
            "res_line",
        ) and not net.res_line.empty:
            summary[
                "maximum_line_loading_percent"
            ] = float(
                net.res_line[
                    "loading_percent"
                ].max()
            )

        if hasattr(
            net,
            "res_trafo",
        ) and not net.res_trafo.empty:
            summary[
                "maximum_transformer_loading_percent"
            ] = float(
                net.res_trafo[
                    "loading_percent"
                ].max()
            )

        return summary

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _is_type(
        value: str,
        *types: str,
    ) -> bool:
        """Case-insensitive asset-type comparison."""

        normalized = (
            str(value)
            .strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        return normalized in {
            item.lower()
            for item in types
        }

    @staticmethod
    def _initial_voltage(
        asset: PandaPowerAsset,
    ) -> float:
        """
        Extract initial per-unit voltage from metadata.
        """

        value = asset.metadata.get(
            "vm_pu",
            1.0,
        )

        try:
            return float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return 1.0

    @staticmethod
    def _resolve_bus(
        asset: PandaPowerAsset,
        bus_map: dict[int, int],
    ) -> int | None:
        """Resolve an asset's bus reference."""

        if asset.bus_id is not None:
            return bus_map.get(
                int(asset.bus_id)
            )

        if asset.from_bus is not None:
            return bus_map.get(
                int(asset.from_bus)
            )

        return None

    @staticmethod
    def _resolve_bus_id(
        bus_id: int | None,
        bus_map: dict[int, int],
    ) -> int | None:
        """Resolve a generic bus ID."""

        if bus_id is None:
            return None

        return bus_map.get(
            int(bus_id)
        )

    @staticmethod
    def _row_value(
        row: Any,
        column: str,
    ) -> float | None:
        """Safely extract a numeric dataframe value."""

        try:
            value = row[column]
        except (
            KeyError,
            TypeError,
        ):
            return None

        try:
            return float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _table_length(
        net: Any,
        table_name: str,
    ) -> int:
        """Return the row count of a pandapower table."""

        table = getattr(
            net,
            table_name,
            None,
        )

        if table is None:
            return 0

        try:
            return len(table.index)
        except AttributeError:
            return 0

    @staticmethod
    def _table_in_service(
        net: Any,
        table_name: str,
        index: Any,
    ) -> bool:
        """Return an asset's in-service state."""

        table = getattr(
            net,
            table_name,
            None,
        )

        if table is None:
            return True

        if (
            "in_service"
            not in table.columns
        ):
            return True

        try:
            return bool(
                table.at[
                    index,
                    "in_service",
                ]
            )
        except (
            KeyError,
            TypeError,
        ):
            return True

    @staticmethod
    def _asset_id_from_table(
        net: Any,
        table_name: str,
        index: Any,
    ) -> int | None:
        """
        Retrieve application-level asset ID from a pandapower table.

        The preferred column is ``asset_id``. If absent, ``id`` and
        ``source_id`` are also checked.
        """

        table = getattr(
            net,
            table_name,
            None,
        )

        if table is None:
            return None

        for column in (
            "asset_id",
            "source_id",
            "id",
        ):
            if column not in table.columns:
                continue

            try:
                value = table.at[
                    index,
                    column,
                ]
            except (
                KeyError,
                TypeError,
            ):
                continue

            try:
                return int(
                    value
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

        return None

    def _find_asset_mapping(
        self,
        net: Any,
        asset_id: int,
    ) -> list[tuple[str, Any]]:
        """
        Find pandapower rows associated with an application asset ID.
        """

        mappings: list[
            tuple[str, Any]
        ] = []

        for table_name in (
            "bus",
            "line",
            "trafo",
            "load",
            "gen",
            "ext_grid",
            "sgen",
            "shunt",
        ):
            table = getattr(
                net,
                table_name,
                None,
            )

            if table is None:
                continue

            if "asset_id" in table.columns:
                try:
                    matches = table.index[
                        table[
                            "asset_id"
                        ].astype(str)
                        == str(asset_id)
                    ]

                    mappings.extend(
                        (
                            table_name,
                            index,
                        )
                        for index in matches
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

        return mappings


# ============================================================
# SIMULATOR ADAPTER
# ============================================================


class PandaPowerSimulator(BaseSimulator):
    """
    BaseSimulator adapter backed by pandapower.

    This class allows the existing Blackout Oracle simulation
    pipeline to use a real power-flow solver.
    """

    def __init__(
        self,
        config: SimulationConfig | None = None,
        *,
        engine: PandaPowerEngine | None = None,
        assets: Iterable[PandaPowerAsset] | None = None,
    ) -> None:
        if config is None:
            config = SimulationConfig(
                simulation_type=(
                    SimulationType.CUSTOM
                )
            )

        self.engine = (
            engine
            if engine is not None
            else PandaPowerEngine(
                config=PandaPowerConfig(
                    voltage_min_pu=(
                        config.voltage_min_pu
                    ),
                    voltage_max_pu=(
                        config.voltage_max_pu
                    ),
                    frequency_min_hz=(
                        config.frequency_min_hz
                    ),
                    frequency_max_hz=(
                        config.frequency_max_hz
                    ),
                    loading_limit_percent=(
                        config.loading_limit_percent
                    ),
                )
            )
        )

        self.assets = list(
            assets or []
        )

        super().__init__(
            config
        )

        self._network: Any | None = None

    @property
    def simulation_type(
        self,
    ) -> SimulationType:
        """Return the simulation type."""

        return SimulationType.CUSTOM

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def initialize(
        self,
        state: SimulationState,
        events: list[SimulationEvent],
    ) -> SimulationContext:
        """
        Build a pandapower network from configured assets and
        initialize it with the current simulation state.
        """

        if self.assets:
            self._network = self.engine.build_network(
                self.assets
            )
        elif self.engine.network is not None:
            self._network = self.engine.network
        else:
            raise RuntimeError(
                "No pandapower network or asset definitions "
                "were provided."
            )

        self.engine.apply_events(
            events,
            network=self._network,
        )

        context = SimulationContext(
            config=self.config,
            state=state.copy(),
            events=list(events),
        )

        context.metadata[
            "engine"
        ] = "pandapower"

        return context

    # ========================================================
    # STEP
    # ========================================================

    def step(
        self,
        context: SimulationContext,
    ) -> SimulationState:
        """
        Execute one power-flow step.
        """

        if self._network is None:
            raise RuntimeError(
                "pandapower network has not been initialized."
            )

        solved_state = self.engine.simulate(
            network=self._network,
            events=[],
            timestamp=context.state.timestamp,
        )

        context.state = solved_state

        return solved_state

    # ========================================================
    # BLACKOUT DETECTION
    # ========================================================

    def detect_blackout(
        self,
        state: SimulationState,
    ) -> bool:
        """
        Detect blackout using power-flow convergence and
        voltage availability.
        """

        converged = state.metadata.get(
            "pandapower_converged"
        )

        if converged is False:
            return True

        if not state.voltage:
            return False

        valid_voltage = [
            value
            for value in state.voltage.values()
            if value is not None
        ]

        if not valid_voltage:
            return False

        # Treat widespread severe undervoltage as a blackout-like
        # condition for application-level risk analysis.
        below_limit = sum(
            1
            for value in valid_voltage
            if value
            < self.config.voltage_min_pu
        )

        return (
            below_limit
            == len(valid_voltage)
        )

    # ========================================================
    # CASCADE DETECTION
    # ========================================================

    def detect_cascade(
        self,
        state: SimulationState,
    ) -> bool:
        """
        Detect cascade-like conditions from overloads/failures.
        """

        return bool(
            state.overloaded_assets
            and len(
                state.overloaded_assets
            )
            >= max(
                1,
                len(
                    state.asset_status
                )
                // 4,
            )
        )

    # ========================================================
    # METRICS
    # ========================================================

    def calculate_metrics(
        self,
        result: Any,
    ) -> Any:
        """
        Use the base metric calculation and add pandapower-specific
        information.
        """

        metrics = super().calculate_metrics(
            result
        )

        if result.final_state is not None:
            converged = result.final_state.metadata.get(
                "pandapower_converged"
            )

            result.metadata[
                "pandapower_converged"
            ] = converged

            result.metadata[
                "pandapower_algorithm"
            ] = self.engine.config.algorithm

        return metrics


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def create_engine(
    *,
    config: PandaPowerConfig | None = None,
    network: Any | None = None,
) -> PandaPowerEngine:
    """
    Create a PandaPowerEngine.
    """

    return PandaPowerEngine(
        config=config,
        network=network,
    )


def run_power_flow(
    network: Any,
    *,
    config: PandaPowerConfig | None = None,
) -> SimulationState:
    """
    Convenience function for solving an existing pandapower network.
    """

    engine = PandaPowerEngine(
        config=config,
        network=network,
    )

    engine.run_power_flow()

    return engine.to_simulation_state()


def simulate_events(
    network: Any,
    events: Iterable[SimulationEvent],
    *,
    config: PandaPowerConfig | None = None,
) -> SimulationState:
    """
    Convenience function for applying events and solving a network.
    """

    engine = PandaPowerEngine(
        config=config,
        network=network,
    )

    return engine.simulate(
        events=events
    )


__all__ = [
    "PandaPowerConfig",
    "PandaPowerAsset",
    "PandaPowerEngine",
    "PandaPowerSimulator",
    "create_engine",
    "run_power_flow",
    "simulate_events",
]