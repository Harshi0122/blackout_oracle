"""
Blackout Oracle - Simulation Scenarios.

Defines reusable grid-failure and what-if scenarios that can be
executed by the simulation layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from app.simulation.base import (
    SimulationEvent,
    SimulationSeverity,
    SimulationState,
    SimulationType,
)
from app.simulation.contingency import (
    ContingencyCase,
)


# ============================================================
# SCENARIO TYPES
# ============================================================


class ScenarioType:
    """Standard scenario type names."""

    ASSET_FAILURE = "asset_failure"
    LINE_OUTAGE = "line_outage"
    TRANSFORMER_OUTAGE = "transformer_outage"
    GENERATOR_TRIP = "generator_trip"
    LOAD_SURGE = "load_surge"
    LOAD_SHEDDING = "load_shedding"
    VOLTAGE_DROP = "voltage_drop"
    FREQUENCY_DROP = "frequency_drop"
    CASCADE = "cascade"
    BLACKOUT = "blackout"
    N_MINUS_ONE = "n_minus_one"
    N_MINUS_K = "n_minus_k"
    EXTREME_WEATHER = "extreme_weather"
    CUSTOM = "custom"


# ============================================================
# SCENARIO
# ============================================================


@dataclass
class SimulationScenario:
    """
    A complete simulation scenario.

    A scenario contains the events to inject into the grid,
    optional parameter overrides, and metadata describing the
    purpose of the simulation.
    """

    scenario_id: str

    name: str

    scenario_type: str = ScenarioType.CUSTOM

    description: str | None = None

    events: list[SimulationEvent] = field(
        default_factory=list
    )

    parameters: dict[str, Any] = field(
        default_factory=dict
    )

    severity: SimulationSeverity = (
        SimulationSeverity.MEDIUM
    )

    probability: float | None = None

    enabled: bool = True

    tags: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if self.probability is not None:
            self.probability = max(
                0.0,
                min(
                    1.0,
                    float(self.probability),
                ),
            )

        self.tags = list(
            dict.fromkeys(
                str(tag)
                for tag in self.tags
            )
        )

    @property
    def event_count(self) -> int:
        """Return the number of events in the scenario."""

        return len(
            self.events
        )

    @property
    def asset_ids(self) -> list[int]:
        """Return all asset IDs referenced by the scenario."""

        return list(
            dict.fromkeys(
                int(event.asset_id)
                for event in self.events
                if event.asset_id is not None
            )
        )

    def add_event(
        self,
        event: SimulationEvent,
    ) -> None:
        """Add an event to the scenario."""

        self.events.append(
            event
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the scenario."""

        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "scenario_type": self.scenario_type,
            "description": self.description,
            "events": [
                event.to_dict()
                for event in self.events
            ],
            "parameters": dict(
                self.parameters
            ),
            "severity": self.severity.value,
            "probability": self.probability,
            "enabled": self.enabled,
            "tags": list(self.tags),
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# SCENARIO RESULT
# ============================================================


@dataclass
class ScenarioResult:
    """
    Result of executing a simulation scenario.
    """

    scenario: SimulationScenario

    success: bool

    risk_score: float = 0.0

    blackout_detected: bool = False

    cascade_detected: bool = False

    failed_assets: list[int] = field(
        default_factory=list
    )

    overloaded_assets: list[int] = field(
        default_factory=list
    )

    affected_assets: list[int] = field(
        default_factory=list
    )

    load_lost_mw: float = 0.0

    generation_lost_mw: float = 0.0

    minimum_voltage_pu: float | None = None

    maximum_voltage_pu: float | None = None

    minimum_frequency_hz: float | None = None

    maximum_frequency_hz: float | None = None

    simulation_id: str | None = None

    error: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the scenario result."""

        return {
            "scenario": self.scenario.to_dict(),
            "success": self.success,
            "risk_score": self.risk_score,
            "blackout_detected": (
                self.blackout_detected
            ),
            "cascade_detected": (
                self.cascade_detected
            ),
            "failed_assets": list(
                self.failed_assets
            ),
            "overloaded_assets": list(
                self.overloaded_assets
            ),
            "affected_assets": list(
                self.affected_assets
            ),
            "load_lost_mw": self.load_lost_mw,
            "generation_lost_mw": (
                self.generation_lost_mw
            ),
            "minimum_voltage_pu": (
                self.minimum_voltage_pu
            ),
            "maximum_voltage_pu": (
                self.maximum_voltage_pu
            ),
            "minimum_frequency_hz": (
                self.minimum_frequency_hz
            ),
            "maximum_frequency_hz": (
                self.maximum_frequency_hz
            ),
            "simulation_id": self.simulation_id,
            "error": self.error,
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# SCENARIO FACTORY
# ============================================================


class ScenarioFactory:
    """
    Factory for creating common Blackout Oracle scenarios.
    """

    @staticmethod
    def asset_failure(
        asset_id: int,
        *,
        scenario_id: str | None = None,
        name: str | None = None,
        severity: SimulationSeverity = (
            SimulationSeverity.HIGH
        ),
        description: str | None = None,
        probability: float | None = None,
    ) -> SimulationScenario:
        """Create an individual asset-failure scenario."""

        asset_id = int(
            asset_id
        )

        return SimulationScenario(
            scenario_id=(
                scenario_id
                or f"asset-failure-{asset_id}"
            ),
            name=(
                name
                or f"Failure of asset {asset_id}"
            ),
            scenario_type=(
                ScenarioType.ASSET_FAILURE
            ),
            description=(
                description
                or (
                    f"Simulate failure of asset "
                    f"{asset_id}."
                )
            ),
            severity=severity,
            probability=probability,
            events=[
                SimulationEvent(
                    event_type="asset_failure",
                    asset_id=asset_id,
                    severity=severity,
                    description=(
                        f"Failure of asset {asset_id}."
                    ),
                )
            ],
        )

    @staticmethod
    def line_outage(
        line_id: int,
        *,
        scenario_id: str | None = None,
        name: str | None = None,
        probability: float | None = None,
    ) -> SimulationScenario:
        """Create a transmission-line outage scenario."""

        line_id = int(
            line_id
        )

        return SimulationScenario(
            scenario_id=(
                scenario_id
                or f"line-outage-{line_id}"
            ),
            name=(
                name
                or f"Line outage {line_id}"
            ),
            scenario_type=(
                ScenarioType.LINE_OUTAGE
            ),
            description=(
                f"Simulate outage of line {line_id}."
            ),
            severity=SimulationSeverity.HIGH,
            probability=probability,
            events=[
                SimulationEvent(
                    event_type="line_outage",
                    asset_id=line_id,
                    severity=SimulationSeverity.HIGH,
                    description=(
                        f"Outage of line {line_id}."
                    ),
                )
            ],
        )

    @staticmethod
    def transformer_outage(
        transformer_id: int,
        *,
        scenario_id: str | None = None,
        name: str | None = None,
        probability: float | None = None,
    ) -> SimulationScenario:
        """Create a transformer-outage scenario."""

        transformer_id = int(
            transformer_id
        )

        return SimulationScenario(
            scenario_id=(
                scenario_id
                or (
                    f"transformer-outage-"
                    f"{transformer_id}"
                )
            ),
            name=(
                name
                or (
                    f"Transformer outage "
                    f"{transformer_id}"
                )
            ),
            scenario_type=(
                ScenarioType.TRANSFORMER_OUTAGE
            ),
            description=(
                f"Simulate outage of transformer "
                f"{transformer_id}."
            ),
            severity=SimulationSeverity.HIGH,
            probability=probability,
            events=[
                SimulationEvent(
                    event_type="transformer_outage",
                    asset_id=transformer_id,
                    severity=SimulationSeverity.HIGH,
                    description=(
                        f"Outage of transformer "
                        f"{transformer_id}."
                    ),
                )
            ],
        )

    @staticmethod
    def generator_trip(
        generator_id: int,
        *,
        power_mw: float | None = None,
        scenario_id: str | None = None,
        probability: float | None = None,
    ) -> SimulationScenario:
        """Create a generator-trip scenario."""

        generator_id = int(
            generator_id
        )

        parameters: dict[str, Any] = {}

        if power_mw is not None:
            parameters[
                "generation_lost_mw"
            ] = max(
                0.0,
                float(power_mw),
            )

        return SimulationScenario(
            scenario_id=(
                scenario_id
                or f"generator-trip-{generator_id}"
            ),
            name=(
                f"Generator trip {generator_id}"
            ),
            scenario_type=(
                ScenarioType.GENERATOR_TRIP
            ),
            description=(
                f"Simulate trip of generator "
                f"{generator_id}."
            ),
            severity=SimulationSeverity.HIGH,
            probability=probability,
            parameters=parameters,
            events=[
                SimulationEvent(
                    event_type="generator_trip",
                    asset_id=generator_id,
                    severity=SimulationSeverity.HIGH,
                    parameters=parameters,
                    description=(
                        f"Trip of generator "
                        f"{generator_id}."
                    ),
                )
            ],
        )

    @staticmethod
    def load_surge(
        load_id: int,
        *,
        multiplier: float = 1.20,
        scenario_id: str | None = None,
        severity: SimulationSeverity = (
            SimulationSeverity.MEDIUM
        ),
    ) -> SimulationScenario:
        """Create a load-surge scenario."""

        multiplier = max(
            0.0,
            float(multiplier),
        )

        return SimulationScenario(
            scenario_id=(
                scenario_id
                or f"load-surge-{load_id}"
            ),
            name=(
                f"Load surge at {load_id}"
            ),
            scenario_type=(
                ScenarioType.LOAD_SURGE
            ),
            severity=severity,
            parameters={
                "load_multiplier": multiplier,
            },
            events=[
                SimulationEvent(
                    event_type="load_surge",
                    asset_id=int(load_id),
                    severity=severity,
                    parameters={
                        "load_multiplier": multiplier,
                    },
                    description=(
                        f"Increase load at asset "
                        f"{load_id} by a multiplier "
                        f"of {multiplier:.2f}."
                    ),
                )
            ],
        )

    @staticmethod
    def voltage_drop(
        asset_id: int,
        *,
        voltage_pu: float = 0.85,
        scenario_id: str | None = None,
    ) -> SimulationScenario:
        """Create a voltage-disturbance scenario."""

        voltage_pu = float(
            voltage_pu
        )

        return SimulationScenario(
            scenario_id=(
                scenario_id
                or f"voltage-drop-{asset_id}"
            ),
            name=(
                f"Voltage drop at {asset_id}"
            ),
            scenario_type=(
                ScenarioType.VOLTAGE_DROP
            ),
            severity=SimulationSeverity.HIGH,
            parameters={
                "voltage_pu": voltage_pu,
            },
            events=[
                SimulationEvent(
                    event_type="voltage_drop",
                    asset_id=int(asset_id),
                    severity=SimulationSeverity.HIGH,
                    parameters={
                        "voltage_pu": voltage_pu,
                    },
                    description=(
                        f"Reduce voltage at asset "
                        f"{asset_id} to "
                        f"{voltage_pu:.3f} pu."
                    ),
                )
            ],
        )

    @staticmethod
    def frequency_drop(
        asset_id: int | None = None,
        *,
        frequency_hz: float = 49.0,
        scenario_id: str | None = None,
    ) -> SimulationScenario:
        """Create a frequency-disturbance scenario."""

        frequency_hz = float(
            frequency_hz
        )

        return SimulationScenario(
            scenario_id=(
                scenario_id
                or "frequency-drop"
            ),
            name=(
                "System frequency drop"
            ),
            scenario_type=(
                ScenarioType.FREQUENCY_DROP
            ),
            severity=SimulationSeverity.HIGH,
            parameters={
                "frequency_hz": frequency_hz,
            },
            events=[
                SimulationEvent(
                    event_type="frequency_drop",
                    asset_id=(
                        int(asset_id)
                        if asset_id is not None
                        else None
                    ),
                    severity=SimulationSeverity.HIGH,
                    parameters={
                        "frequency_hz": frequency_hz,
                    },
                    description=(
                        "Simulate a system frequency "
                        f"of {frequency_hz:.2f} Hz."
                    ),
                )
            ],
        )

    @staticmethod
    def cascade(
        asset_ids: Iterable[int],
        *,
        scenario_id: str | None = None,
        name: str | None = None,
    ) -> SimulationScenario:
        """Create a multi-asset cascading-failure scenario."""

        ids = list(
            dict.fromkeys(
                int(asset_id)
                for asset_id in asset_ids
            )
        )

        if not ids:
            raise ValueError(
                "At least one asset ID is required."
            )

        events = [
            SimulationEvent(
                event_type="cascade_failure",
                asset_id=asset_id,
                severity=SimulationSeverity.CRITICAL,
                description=(
                    f"Cascade failure of asset "
                    f"{asset_id}."
                ),
            )
            for asset_id in ids
        ]

        return SimulationScenario(
            scenario_id=(
                scenario_id
                or "cascade-"
                + "-".join(
                    map(
                        str,
                        ids,
                    )
                )
            ),
            name=(
                name
                or "Cascading failure scenario"
            ),
            scenario_type=(
                ScenarioType.CASCADE
            ),
            severity=SimulationSeverity.CRITICAL,
            events=events,
            parameters={
                "cascade": True,
                "asset_count": len(ids),
            },
        )

    @staticmethod
    def blackout(
        *,
        scenario_id: str = "blackout",
        name: str = "System blackout",
    ) -> SimulationScenario:
        """Create an explicit blackout scenario."""

        return SimulationScenario(
            scenario_id=scenario_id,
            name=name,
            scenario_type=(
                ScenarioType.BLACKOUT
            ),
            severity=SimulationSeverity.CRITICAL,
            description=(
                "Simulate a complete grid blackout."
            ),
            parameters={
                "blackout": True,
            },
            events=[
                SimulationEvent(
                    event_type="blackout",
                    severity=SimulationSeverity.CRITICAL,
                    description=(
                        "Simulated system blackout."
                    ),
                )
            ],
        )

    @staticmethod
    def n_minus_one(
        asset_id: int,
        *,
        scenario_id: str | None = None,
    ) -> SimulationScenario:
        """Create an N-1 scenario."""

        case = ContingencyCase(
            name=(
                f"N-1 outage of asset {asset_id}"
            ),
            asset_ids=[
                int(asset_id)
            ],
            description=(
                "Single asset N-1 contingency."
            ),
        )

        return SimulationScenario(
            scenario_id=(
                scenario_id
                or f"n-1-{asset_id}"
            ),
            name=case.name,
            scenario_type=(
                ScenarioType.N_MINUS_ONE
            ),
            severity=SimulationSeverity.HIGH,
            parameters={
                "contingency": case.to_dict(),
            },
            events=[
                SimulationEvent(
                    event_type="n_minus_one_outage",
                    asset_id=int(asset_id),
                    severity=SimulationSeverity.HIGH,
                    description=(
                        f"N-1 outage of asset "
                        f"{asset_id}."
                    ),
                )
            ],
        )

    @staticmethod
    def n_minus_k(
        asset_ids: Iterable[int],
        *,
        scenario_id: str | None = None,
        name: str | None = None,
    ) -> SimulationScenario:
        """Create an N-k scenario."""

        ids = list(
            dict.fromkeys(
                int(asset_id)
                for asset_id in asset_ids
            )
        )

        if not ids:
            raise ValueError(
                "At least one asset ID is required."
            )

        case = ContingencyCase(
            name=(
                name
                or (
                    f"N-{len(ids)} contingency"
                )
            ),
            asset_ids=ids,
            description=(
                "Multiple simultaneous asset "
                "outage contingency."
            ),
        )

        events = [
            SimulationEvent(
                event_type="n_minus_k_outage",
                asset_id=asset_id,
                severity=SimulationSeverity.CRITICAL,
                description=(
                    f"N-k outage of asset "
                    f"{asset_id}."
                ),
            )
            for asset_id in ids
        ]

        return SimulationScenario(
            scenario_id=(
                scenario_id
                or (
                    f"n-{len(ids)}-"
                    + "-".join(
                        map(
                            str,
                            ids,
                        )
                    )
                )
            ),
            name=case.name,
            scenario_type=(
                ScenarioType.N_MINUS_K
            ),
            severity=SimulationSeverity.CRITICAL,
            events=events,
            parameters={
                "contingency": case.to_dict(),
            },
        )

    @staticmethod
    def extreme_weather(
        asset_ids: Iterable[int],
        *,
        weather_type: str = "storm",
        severity: SimulationSeverity = (
            SimulationSeverity.HIGH
        ),
        scenario_id: str | None = None,
    ) -> SimulationScenario:
        """Create an extreme-weather scenario."""

        ids = list(
            dict.fromkeys(
                int(asset_id)
                for asset_id in asset_ids
            )
        )

        events = [
            SimulationEvent(
                event_type="extreme_weather",
                asset_id=asset_id,
                severity=severity,
                parameters={
                    "weather_type": weather_type,
                },
                description=(
                    f"{weather_type} impact on "
                    f"asset {asset_id}."
                ),
            )
            for asset_id in ids
        ]

        return SimulationScenario(
            scenario_id=(
                scenario_id
                or f"weather-{weather_type}"
            ),
            name=(
                f"Extreme weather: "
                f"{weather_type}"
            ),
            scenario_type=(
                ScenarioType.EXTREME_WEATHER
            ),
            severity=severity,
            events=events,
            parameters={
                "weather_type": weather_type,
                "asset_count": len(ids),
            },
        )


# ============================================================
# SCENARIO LIBRARY
# ============================================================


class ScenarioLibrary:
    """
    In-memory registry of reusable simulation scenarios.
    """

    def __init__(
        self,
        scenarios: Iterable[
            SimulationScenario
        ] | None = None,
    ) -> None:
        self._scenarios: dict[
            str,
            SimulationScenario,
        ] = {}

        for scenario in (
            scenarios or []
        ):
            self.register(
                scenario
            )

    def register(
        self,
        scenario: SimulationScenario,
        *,
        overwrite: bool = True,
    ) -> SimulationScenario:
        """Register a scenario."""

        if (
            not overwrite
            and scenario.scenario_id
            in self._scenarios
        ):
            raise ValueError(
                "Scenario already exists: "
                f"{scenario.scenario_id}"
            )

        self._scenarios[
            scenario.scenario_id
        ] = scenario

        return scenario

    def get(
        self,
        scenario_id: str,
    ) -> SimulationScenario | None:
        """Retrieve a scenario."""

        return self._scenarios.get(
            scenario_id
        )

    def require(
        self,
        scenario_id: str,
    ) -> SimulationScenario:
        """Retrieve a scenario or raise KeyError."""

        scenario = self.get(
            scenario_id
        )

        if scenario is None:
            raise KeyError(
                f"Unknown simulation scenario: "
                f"{scenario_id}"
            )

        return scenario

    def remove(
        self,
        scenario_id: str,
    ) -> SimulationScenario | None:
        """Remove a scenario."""

        return self._scenarios.pop(
            scenario_id,
            None,
        )

    def clear(self) -> None:
        """Remove all scenarios."""

        self._scenarios.clear()

    def all(
        self,
    ) -> list[SimulationScenario]:
        """Return all registered scenarios."""

        return list(
            self._scenarios.values()
        )

    def enabled(
        self,
    ) -> list[SimulationScenario]:
        """Return enabled scenarios only."""

        return [
            scenario
            for scenario
            in self._scenarios.values()
            if scenario.enabled
        ]

    def by_type(
        self,
        scenario_type: str,
    ) -> list[SimulationScenario]:
        """Return scenarios matching a type."""

        return [
            scenario
            for scenario
            in self._scenarios.values()
            if scenario.scenario_type
            == scenario_type
        ]

    def by_tag(
        self,
        tag: str,
    ) -> list[SimulationScenario]:
        """Return scenarios containing a tag."""

        return [
            scenario
            for scenario
            in self._scenarios.values()
            if tag in scenario.tags
        ]

    def __len__(self) -> int:
        return len(
            self._scenarios
        )


# ============================================================
# SCENARIO RUNNER
# ============================================================


class ScenarioRunner:
    """
    Executes scenarios using a compatible simulation callable.

    The runner accepts a callable instead of depending directly on
    a specific simulation engine. This keeps scenario definitions
    independent from pandapower or other solver implementations.
    """

    def __init__(
        self,
        simulator: Any,
    ) -> None:
        self.simulator = simulator

    def run(
        self,
        state: SimulationState,
        scenario: SimulationScenario,
    ) -> ScenarioResult:
        """
        Execute a scenario.
        """

        if not scenario.enabled:
            return ScenarioResult(
                scenario=scenario,
                success=False,
                error=(
                    "Scenario is disabled."
                ),
            )

        try:
            simulation_result = self._execute(
                state,
                scenario,
            )

            return self._build_result(
                scenario,
                simulation_result,
            )

        except Exception as exc:
            return ScenarioResult(
                scenario=scenario,
                success=False,
                error=str(exc),
            )

    def run_many(
        self,
        state: SimulationState,
        scenarios: Iterable[
            SimulationScenario
        ],
    ) -> list[ScenarioResult]:
        """Run multiple scenarios."""

        return [
            self.run(
                state,
                scenario,
            )
            for scenario in scenarios
        ]

    def _execute(
        self,
        state: SimulationState,
        scenario: SimulationScenario,
    ) -> Any:
        """
        Execute a scenario using the supplied simulator.
        """

        # BaseSimulator-style interface.
        if hasattr(
            self.simulator,
            "run",
        ):
            return self.simulator.run(
                state,
                scenario.events,
            )

        # Callable simulator.
        if callable(
            self.simulator
        ):
            return self.simulator(
                state,
                scenario.events,
            )

        raise TypeError(
            "Simulator must expose a run() method "
            "or be callable."
        )

    @staticmethod
    def _build_result(
        scenario: SimulationScenario,
        simulation_result: Any,
    ) -> ScenarioResult:
        """
        Convert a simulation result into ScenarioResult.
        """

        final_state = getattr(
            simulation_result,
            "final_state",
            None,
        )

        metrics = getattr(
            simulation_result,
            "metrics",
            None,
        )

        if final_state is None:
            return ScenarioResult(
                scenario=scenario,
                success=False,
                simulation_id=getattr(
                    simulation_result,
                    "simulation_id",
                    None,
                ),
                error=(
                    getattr(
                        simulation_result,
                        "error",
                        None,
                    )
                    or "Simulation produced no final state."
                ),
            )

        failed_assets = sorted(
            final_state.failed_assets
        )

        overloaded_assets = sorted(
            final_state.overloaded_assets
        )

        islanded_assets = sorted(
            final_state.islanded_assets
        )

        affected_assets = sorted(
            set(
                failed_assets
            )
            | set(
                overloaded_assets
            )
            | set(
                islanded_assets
            )
        )

        risk_score = float(
            getattr(
                metrics,
                "risk_score",
                getattr(
                    simulation_result,
                    "risk_score",
                    0.0,
                ),
            )
            or 0.0
        )

        return ScenarioResult(
            scenario=scenario,
            success=(
                getattr(
                    simulation_result,
                    "is_successful",
                    True,
                )
            ),
            risk_score=risk_score,
            blackout_detected=(
                ScenarioRunner._detect_blackout(
                    simulation_result,
                    final_state,
                )
            ),
            cascade_detected=(
                ScenarioRunner._detect_cascade(
                    simulation_result,
                    final_state,
                )
            ),
            failed_assets=failed_assets,
            overloaded_assets=overloaded_assets,
            affected_assets=affected_assets,
            load_lost_mw=float(
                getattr(
                    metrics,
                    "load_lost_mw",
                    0.0,
                )
                or 0.0
            ),
            generation_lost_mw=float(
                getattr(
                    metrics,
                    "generation_lost_mw",
                    0.0,
                )
                or 0.0
            ),
            minimum_voltage_pu=(
                getattr(
                    metrics,
                    "minimum_voltage_pu",
                    None,
                )
            ),
            maximum_voltage_pu=(
                getattr(
                    metrics,
                    "maximum_voltage_pu",
                    None,
                )
            ),
            minimum_frequency_hz=(
                getattr(
                    metrics,
                    "minimum_frequency_hz",
                    None,
                )
            ),
            maximum_frequency_hz=(
                getattr(
                    metrics,
                    "maximum_frequency_hz",
                    None,
                )
            ),
            simulation_id=getattr(
                simulation_result,
                "simulation_id",
                None,
            ),
            error=getattr(
                simulation_result,
                "error",
                None,
            ),
        )

    @staticmethod
    def _detect_blackout(
        simulation_result: Any,
        final_state: SimulationState,
    ) -> bool:
        """Detect blackout from simulation result/state."""

        metadata = final_state.metadata

        if metadata.get(
            "blackout_detected"
        ):
            return True

        severity = getattr(
            simulation_result,
            "severity",
            None,
        )

        if severity == SimulationSeverity.CRITICAL:
            if not final_state.asset_status:
                return False

            active = sum(
                1
                for status
                in final_state.asset_status.values()
                if str(status).lower()
                in {
                    "active",
                    "online",
                    "connected",
                    "in_service",
                    "in-service",
                }
            )

            return active == 0

        return False

    @staticmethod
    def _detect_cascade(
        simulation_result: Any,
        final_state: SimulationState,
    ) -> bool:
        """Detect whether cascading failure occurred."""

        if final_state.metadata.get(
            "cascade_detected"
        ):
            return True

        events = getattr(
            simulation_result,
            "events",
            [],
        )

        return any(
            "cascade"
            in str(
                getattr(
                    event,
                    "event_type",
                    "",
                )
            ).lower()
            for event in events
        )


# ============================================================
# SCENARIO GENERATORS
# ============================================================


def generate_n_minus_one_scenarios(
    asset_ids: Iterable[int],
) -> list[SimulationScenario]:
    """
    Generate one N-1 scenario for every supplied asset.
    """

    return [
        ScenarioFactory.n_minus_one(
            int(asset_id)
        )
        for asset_id in asset_ids
    ]


def generate_pair_failure_scenarios(
    asset_ids: Iterable[int],
) -> list[SimulationScenario]:
    """
    Generate all unique two-asset failure scenarios.

    This is useful for small N-2 studies. For large grids, avoid
    generating the full combinatorial set.
    """

    ids = list(
        dict.fromkeys(
            int(asset_id)
            for asset_id in asset_ids
        )
    )

    scenarios: list[
        SimulationScenario
    ] = []

    for index, first in enumerate(ids):
        for second in ids[
            index + 1:
        :]:
            scenarios.append(
                ScenarioFactory.n_minus_k(
                    [first, second]
                )
            )

    return scenarios


def generate_cascade_scenarios(
    groups: Iterable[
        Iterable[int]
    ],
) -> list[SimulationScenario]:
    """
    Generate cascading-failure scenarios from asset groups.
    """

    scenarios: list[
        SimulationScenario
    ] = []

    for index, group in enumerate(groups):
        scenarios.append(
            ScenarioFactory.cascade(
                group,
                scenario_id=f"cascade-{index + 1}",
            )
        )

    return scenarios


# ============================================================
# DEFAULT SCENARIO LIBRARY
# ============================================================


def create_default_library(
    *,
    asset_ids: Iterable[int] | None = None,
) -> ScenarioLibrary:
    """
    Create a scenario library.

    If asset IDs are supplied, standard N-1 scenarios are added.
    """

    library = ScenarioLibrary()

    library.register(
        ScenarioFactory.blackout()
    )

    if asset_ids is not None:
        for scenario in generate_n_minus_one_scenarios(
            asset_ids
        ):
            library.register(
                scenario
            )

    return library


__all__ = [
    "ScenarioType",
    "SimulationScenario",
    "ScenarioResult",
    "ScenarioFactory",
    "ScenarioLibrary",
    "ScenarioRunner",
    "generate_n_minus_one_scenarios",
    "generate_pair_failure_scenarios",
    "generate_cascade_scenarios",
    "create_default_library",
]