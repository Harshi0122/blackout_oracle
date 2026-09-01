"""
Blackout Oracle - Simulation Base Classes.

Defines the common interfaces and data structures used by the
grid simulation layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ============================================================
# ENUMS
# ============================================================


class SimulationStatus(str, Enum):
    """Lifecycle state of a simulation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SimulationType(str, Enum):
    """Types of simulations supported by Blackout Oracle."""

    CONTINGENCY = "contingency"
    CASCADE = "cascade"
    BLACKOUT = "blackout"
    ASSET_FAILURE = "asset_failure"
    N_MINUS_ONE = "n_minus_one"
    WHAT_IF = "what_if"
    CUSTOM = "custom"


class SimulationSeverity(str, Enum):
    """Severity of a simulated grid event."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# SIMULATION EVENT
# ============================================================


@dataclass
class SimulationEvent:
    """
    Represents an event injected into a simulation.

    Examples include asset failure, line outage, transformer
    overload, generator trip, or bus failure.
    """

    event_type: str
    asset_id: int | None = None

    timestamp: datetime | None = None

    duration_seconds: float | None = None

    severity: SimulationSeverity = SimulationSeverity.MEDIUM

    parameters: dict[str, Any] = field(
        default_factory=dict
    )

    description: str | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(
                timezone.utc
            )

        if self.duration_seconds is not None:
            self.duration_seconds = max(
                0.0,
                float(self.duration_seconds),
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert the event to a serializable dictionary."""

        return {
            "event_type": self.event_type,
            "asset_id": self.asset_id,
            "timestamp": (
                self.timestamp.isoformat()
                if self.timestamp is not None
                else None
            ),
            "duration_seconds": self.duration_seconds,
            "severity": self.severity.value,
            "parameters": dict(self.parameters),
            "description": self.description,
        }


# ============================================================
# SIMULATION STATE
# ============================================================


@dataclass
class SimulationState:
    """
    Represents the electrical-grid state at one point during
    a simulation.
    """

    timestamp: datetime

    voltage: dict[int, float] = field(
        default_factory=dict
    )

    frequency: dict[int, float] = field(
        default_factory=dict
    )

    active_power: dict[int, float] = field(
        default_factory=dict
    )

    reactive_power: dict[int, float] = field(
        default_factory=dict
    )

    loading: dict[int, float] = field(
        default_factory=dict
    )

    asset_status: dict[int, str] = field(
        default_factory=dict
    )

    failed_assets: set[int] = field(
        default_factory=set
    )

    overloaded_assets: set[int] = field(
        default_factory=set
    )

    islanded_assets: set[int] = field(
        default_factory=set
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def copy(self) -> "SimulationState":
        """Return an independent copy of the simulation state."""

        return SimulationState(
            timestamp=self.timestamp,
            voltage=dict(self.voltage),
            frequency=dict(self.frequency),
            active_power=dict(self.active_power),
            reactive_power=dict(self.reactive_power),
            loading=dict(self.loading),
            asset_status=dict(self.asset_status),
            failed_assets=set(self.failed_assets),
            overloaded_assets=set(self.overloaded_assets),
            islanded_assets=set(self.islanded_assets),
            metadata=dict(self.metadata),
        )

    def fail_asset(
        self,
        asset_id: int,
    ) -> None:
        """Mark an asset as failed."""

        self.failed_assets.add(asset_id)

        self.asset_status[
            asset_id
        ] = "failed"

    def restore_asset(
        self,
        asset_id: int,
    ) -> None:
        """Restore an asset from the failed state."""

        self.failed_assets.discard(
            asset_id
        )

        self.asset_status[
            asset_id
        ] = "active"

    def mark_overloaded(
        self,
        asset_id: int,
        overloaded: bool = True,
    ) -> None:
        """Mark or clear an asset overload."""

        if overloaded:
            self.overloaded_assets.add(
                asset_id
            )
        else:
            self.overloaded_assets.discard(
                asset_id
            )

    def is_failed(
        self,
        asset_id: int,
    ) -> bool:
        """Return whether an asset is failed."""

        return asset_id in self.failed_assets

    def is_overloaded(
        self,
        asset_id: int,
    ) -> bool:
        """Return whether an asset is overloaded."""

        return asset_id in self.overloaded_assets

    def to_dict(self) -> dict[str, Any]:
        """Convert state into a serializable dictionary."""

        return {
            "timestamp": self.timestamp.isoformat(),
            "voltage": dict(self.voltage),
            "frequency": dict(self.frequency),
            "active_power": dict(self.active_power),
            "reactive_power": dict(
                self.reactive_power
            ),
            "loading": dict(self.loading),
            "asset_status": dict(
                self.asset_status
            ),
            "failed_assets": list(
                self.failed_assets
            ),
            "overloaded_assets": list(
                self.overloaded_assets
            ),
            "islanded_assets": list(
                self.islanded_assets
            ),
            "metadata": dict(self.metadata),
        }


# ============================================================
# SIMULATION METRICS
# ============================================================


@dataclass
class SimulationMetrics:
    """
    Aggregated metrics describing the result of a simulation.
    """

    total_assets: int = 0

    failed_assets: int = 0

    overloaded_assets: int = 0

    islanded_assets: int = 0

    affected_assets: int = 0

    customers_affected: int = 0

    load_lost_mw: float = 0.0

    generation_lost_mw: float = 0.0

    maximum_loading_percent: float = 0.0

    minimum_voltage_pu: float | None = None

    maximum_voltage_pu: float | None = None

    minimum_frequency_hz: float | None = None

    maximum_frequency_hz: float | None = None

    cascade_depth: int = 0

    cascade_events: int = 0

    blackout_probability: float | None = None

    risk_score: float = 0.0

    def calculate_risk_score(self) -> float:
        """
        Calculate a deterministic simulation risk score.

        The score is normalized to 0-100 and is intended as an
        operational screening metric rather than a physical
        power-system solver output.
        """

        failure_component = min(
            30.0,
            self.failed_assets * 5.0,
        )

        overload_component = min(
            20.0,
            self.overloaded_assets * 3.0,
        )

        island_component = min(
            20.0,
            self.islanded_assets * 8.0,
        )

        load_loss_component = min(
            15.0,
            max(
                0.0,
                self.load_lost_mw,
            )
            / 10.0,
        )

        cascade_component = min(
            15.0,
            self.cascade_depth * 3.0
            + self.cascade_events * 0.5,
        )

        self.risk_score = max(
            0.0,
            min(
                100.0,
                failure_component
                + overload_component
                + island_component
                + load_loss_component
                + cascade_component,
            ),
        )

        return self.risk_score

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics into a serializable dictionary."""

        return {
            "total_assets": self.total_assets,
            "failed_assets": self.failed_assets,
            "overloaded_assets": self.overloaded_assets,
            "islanded_assets": self.islanded_assets,
            "affected_assets": self.affected_assets,
            "customers_affected": self.customers_affected,
            "load_lost_mw": self.load_lost_mw,
            "generation_lost_mw": self.generation_lost_mw,
            "maximum_loading_percent": (
                self.maximum_loading_percent
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
            "cascade_depth": self.cascade_depth,
            "cascade_events": self.cascade_events,
            "blackout_probability": (
                self.blackout_probability
            ),
            "risk_score": self.risk_score,
        }


# ============================================================
# SIMULATION RESULT
# ============================================================


@dataclass
class SimulationResult:
    """
    Complete result produced by a simulation.
    """

    simulation_id: str

    simulation_type: SimulationType

    status: SimulationStatus

    started_at: datetime

    completed_at: datetime | None = None

    initial_state: SimulationState | None = None

    final_state: SimulationState | None = None

    states: list[SimulationState] = field(
        default_factory=list
    )

    events: list[SimulationEvent] = field(
        default_factory=list
    )

    metrics: SimulationMetrics = field(
        default_factory=SimulationMetrics
    )

    severity: SimulationSeverity = (
        SimulationSeverity.NONE
    )

    error: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def duration_seconds(self) -> float | None:
        """Return simulation duration in seconds."""

        if self.completed_at is None:
            return None

        return max(
            0.0,
            (
                self.completed_at
                - self.started_at
            ).total_seconds(),
        )

    @property
    def risk_score(self) -> float:
        """Return the simulation risk score."""

        return self.metrics.risk_score

    @property
    def is_successful(self) -> bool:
        """Return whether the simulation completed successfully."""

        return (
            self.status
            == SimulationStatus.COMPLETED
            and self.error is None
        )

    def finalize(
        self,
        status: SimulationStatus = (
            SimulationStatus.COMPLETED
        ),
    ) -> None:
        """Finalize the simulation result."""

        self.status = status

        if self.completed_at is None:
            self.completed_at = datetime.now(
                timezone.utc
            )

        self.metrics.calculate_risk_score()

        self.severity = self._severity_from_score(
            self.metrics.risk_score
        )

    @staticmethod
    def _severity_from_score(
        score: float,
    ) -> SimulationSeverity:
        """Map risk score to simulation severity."""

        score = max(
            0.0,
            min(
                100.0,
                float(score),
            ),
        )

        if score >= 90.0:
            return SimulationSeverity.CRITICAL

        if score >= 75.0:
            return SimulationSeverity.HIGH

        if score >= 50.0:
            return SimulationSeverity.MEDIUM

        if score >= 25.0:
            return SimulationSeverity.LOW

        return SimulationSeverity.NONE

    def to_dict(self) -> dict[str, Any]:
        """Convert the complete result to a dictionary."""

        return {
            "simulation_id": self.simulation_id,
            "simulation_type": (
                self.simulation_type.value
            ),
            "status": self.status.value,
            "started_at": (
                self.started_at.isoformat()
            ),
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at is not None
                else None
            ),
            "duration_seconds": (
                self.duration_seconds
            ),
            "initial_state": (
                self.initial_state.to_dict()
                if self.initial_state is not None
                else None
            ),
            "final_state": (
                self.final_state.to_dict()
                if self.final_state is not None
                else None
            ),
            "states": [
                state.to_dict()
                for state in self.states
            ],
            "events": [
                event.to_dict()
                for event in self.events
            ],
            "metrics": self.metrics.to_dict(),
            "severity": self.severity.value,
            "error": self.error,
            "metadata": dict(self.metadata),
        }


# ============================================================
# SIMULATION CONFIGURATION
# ============================================================


@dataclass
class SimulationConfig:
    """
    Configuration controlling simulation execution.
    """

    simulation_type: SimulationType = (
        SimulationType.CUSTOM
    )

    time_step_seconds: float = 1.0

    duration_seconds: float = 60.0

    maximum_steps: int = 1000

    stop_on_blackout: bool = True

    stop_on_cascade: bool = False

    cascade_threshold_percent: float = 100.0

    voltage_min_pu: float = 0.90

    voltage_max_pu: float = 1.10

    frequency_min_hz: float = 49.0

    frequency_max_hz: float = 51.0

    loading_limit_percent: float = 100.0

    random_seed: int | None = None

    parameters: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self.time_step_seconds = max(
            0.001,
            float(self.time_step_seconds),
        )

        self.duration_seconds = max(
            0.0,
            float(self.duration_seconds),
        )

        self.maximum_steps = max(
            1,
            int(self.maximum_steps),
        )

        self.cascade_threshold_percent = max(
            0.0,
            float(self.cascade_threshold_percent),
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

    @property
    def expected_steps(self) -> int:
        """Return the expected number of simulation steps."""

        if self.duration_seconds <= 0:
            return 1

        steps = int(
            self.duration_seconds
            / self.time_step_seconds
        )

        return max(
            1,
            min(
                self.maximum_steps,
                steps,
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to a dictionary."""

        return {
            "simulation_type": (
                self.simulation_type.value
            ),
            "time_step_seconds": (
                self.time_step_seconds
            ),
            "duration_seconds": (
                self.duration_seconds
            ),
            "maximum_steps": self.maximum_steps,
            "stop_on_blackout": (
                self.stop_on_blackout
            ),
            "stop_on_cascade": (
                self.stop_on_cascade
            ),
            "cascade_threshold_percent": (
                self.cascade_threshold_percent
            ),
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
            "random_seed": self.random_seed,
            "parameters": dict(self.parameters),
        }


# ============================================================
# SIMULATION CONTEXT
# ============================================================


@dataclass
class SimulationContext:
    """
    Runtime context shared by simulation components.
    """

    config: SimulationConfig

    state: SimulationState

    events: list[SimulationEvent] = field(
        default_factory=list
    )

    step: int = 0

    elapsed_seconds: float = 0.0

    terminated: bool = False

    termination_reason: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def advance(
        self,
        *,
        timestamp: datetime | None = None,
    ) -> None:
        """Advance the simulation by one configured step."""

        self.step += 1

        self.elapsed_seconds += (
            self.config.time_step_seconds
        )

        if timestamp is None:
            timestamp = (
                self.state.timestamp
            )

        self.state.timestamp = timestamp

    def terminate(
        self,
        reason: str,
    ) -> None:
        """Stop the simulation."""

        self.terminated = True
        self.termination_reason = reason


# ============================================================
# ABSTRACT SIMULATOR
# ============================================================


class BaseSimulator(ABC):
    """
    Abstract base class for all grid simulators.

    Concrete simulators should implement `initialize`,
    `step`, and `finalize`.
    """

    def __init__(
        self,
        config: SimulationConfig | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else SimulationConfig()
        )

    @property
    @abstractmethod
    def simulation_type(self) -> SimulationType:
        """Return the simulator's simulation type."""

        raise NotImplementedError

    @abstractmethod
    def initialize(
        self,
        state: SimulationState,
        events: list[SimulationEvent],
    ) -> SimulationContext:
        """
        Initialize a simulation context from the initial state
        and injected events.
        """

        raise NotImplementedError

    @abstractmethod
    def step(
        self,
        context: SimulationContext,
    ) -> SimulationState:
        """
        Execute one simulation step.
        """

        raise NotImplementedError

    def run(
        self,
        state: SimulationState,
        events: list[SimulationEvent] | None = None,
    ) -> SimulationResult:
        """
        Execute the simulation until completion or termination.
        """

        simulation_events = list(
            events or []
        )

        started_at = datetime.now(
            timezone.utc
        )

        result = SimulationResult(
            simulation_id=self._generate_simulation_id(
                started_at
            ),
            simulation_type=self.simulation_type,
            status=SimulationStatus.RUNNING,
            started_at=started_at,
            initial_state=state.copy(),
            events=simulation_events,
        )

        try:
            context = self.initialize(
                state.copy(),
                simulation_events,
            )

            result.states.append(
                context.state.copy()
            )

            for _ in range(
                self.config.expected_steps
            ):
                if context.terminated:
                    break

                self.step(context)

                result.states.append(
                    context.state.copy()
                )

                if self.should_stop(
                    context
                ):
                    break

                context.advance()

            result.final_state = (
                context.state.copy()
            )

            result.metadata.update(
                {
                    "steps": context.step,
                    "elapsed_seconds": (
                        context.elapsed_seconds
                    ),
                    "termination_reason": (
                        context.termination_reason
                    ),
                }
            )

            self.calculate_metrics(
                result
            )

            result.finalize()

        except Exception as exc:
            result.error = str(exc)
            result.finalize(
                SimulationStatus.FAILED
            )

        return result

    def should_stop(
        self,
        context: SimulationContext,
    ) -> bool:
        """
        Determine whether the simulation should terminate.
        """

        state = context.state

        if (
            self.config.stop_on_blackout
            and self.detect_blackout(state)
        ):
            context.terminate(
                "blackout_detected"
            )
            return True

        if (
            self.config.stop_on_cascade
            and self.detect_cascade(state)
        ):
            context.terminate(
                "cascade_detected"
            )
            return True

        if (
            context.elapsed_seconds
            >= self.config.duration_seconds
        ):
            context.terminate(
                "duration_reached"
            )
            return True

        return False

    def detect_blackout(
        self,
        state: SimulationState,
    ) -> bool:
        """
        Detect a basic blackout condition from simulation state.

        Concrete simulators can override this with more sophisticated
        power-system logic.
        """

        if not state.asset_status:
            return False

        active_assets = [
            asset_id
            for asset_id, status
            in state.asset_status.items()
            if str(status).lower()
            in {
                "active",
                "online",
                "connected",
            }
        ]

        return (
            len(active_assets) == 0
            and len(state.asset_status) > 0
        )

    def detect_cascade(
        self,
        state: SimulationState,
    ) -> bool:
        """
        Detect a basic cascading-failure condition.
        """

        if not state.loading:
            return False

        threshold = (
            self.config.cascade_threshold_percent
        )

        return any(
            loading >= threshold
            for loading in state.loading.values()
        )

    def calculate_metrics(
        self,
        result: SimulationResult,
    ) -> SimulationMetrics:
        """
        Calculate aggregate simulation metrics.
        """

        metrics = result.metrics

        final_state = result.final_state

        if final_state is None:
            return metrics

        metrics.failed_assets = len(
            final_state.failed_assets
        )

        metrics.overloaded_assets = len(
            final_state.overloaded_assets
        )

        metrics.islanded_assets = len(
            final_state.islanded_assets
        )

        metrics.affected_assets = len(
            set(final_state.failed_assets)
            | set(final_state.overloaded_assets)
            | set(final_state.islanded_assets)
        )

        if final_state.loading:
            metrics.maximum_loading_percent = max(
                final_state.loading.values()
            )

        if final_state.voltage:
            metrics.minimum_voltage_pu = min(
                final_state.voltage.values()
            )

            metrics.maximum_voltage_pu = max(
                final_state.voltage.values()
            )

        if final_state.frequency:
            metrics.minimum_frequency_hz = min(
                final_state.frequency.values()
            )

            metrics.maximum_frequency_hz = max(
                final_state.frequency.values()
            )

        metrics.cascade_depth = self.calculate_cascade_depth(
            result
        )

        metrics.cascade_events = len(
            [
                event
                for event in result.events
                if "cascade"
                in event.event_type.lower()
            ]
        )

        metrics.calculate_risk_score()

        return metrics

    @staticmethod
    def calculate_cascade_depth(
        result: SimulationResult,
    ) -> int:
        """
        Estimate cascade depth from state transitions.
        """

        if not result.states:
            return 0

        maximum_failed = 0
        depth = 0

        for state in result.states:
            failed = len(
                state.failed_assets
            )

            if failed > maximum_failed:
                maximum_failed = failed
                depth += 1

        return depth

    @staticmethod
    def _generate_simulation_id(
        timestamp: datetime,
    ) -> str:
        """
        Generate a lightweight unique simulation identifier.
        """

        return (
            "sim-"
            + timestamp.strftime(
                "%Y%m%d%H%M%S%f"
            )
        )


# ============================================================
# SIMULATION BUILDER
# ============================================================


class SimulationBuilder:
    """
    Convenience builder for constructing simulation configurations.
    """

    def __init__(self) -> None:
        self._config = SimulationConfig()

    def type(
        self,
        simulation_type: SimulationType,
    ) -> "SimulationBuilder":
        """Set simulation type."""

        self._config.simulation_type = (
            simulation_type
        )
        return self

    def time_step(
        self,
        seconds: float,
    ) -> "SimulationBuilder":
        """Set simulation time step."""

        self._config.time_step_seconds = max(
            0.001,
            float(seconds),
        )
        return self

    def duration(
        self,
        seconds: float,
    ) -> "SimulationBuilder":
        """Set simulation duration."""

        self._config.duration_seconds = max(
            0.0,
            float(seconds),
        )
        return self

    def stop_on_blackout(
        self,
        enabled: bool = True,
    ) -> "SimulationBuilder":
        """Configure blackout termination."""

        self._config.stop_on_blackout = bool(
            enabled
        )
        return self

    def stop_on_cascade(
        self,
        enabled: bool = True,
    ) -> "SimulationBuilder":
        """Configure cascade termination."""

        self._config.stop_on_cascade = bool(
            enabled
        )
        return self

    def parameter(
        self,
        name: str,
        value: Any,
    ) -> "SimulationBuilder":
        """Add a custom simulation parameter."""

        self._config.parameters[
            name
        ] = value

        return self

    def build(self) -> SimulationConfig:
        """Return the constructed configuration."""

        return SimulationConfig(
            simulation_type=(
                self._config.simulation_type
            ),
            time_step_seconds=(
                self._config.time_step_seconds
            ),
            duration_seconds=(
                self._config.duration_seconds
            ),
            maximum_steps=(
                self._config.maximum_steps
            ),
            stop_on_blackout=(
                self._config.stop_on_blackout
            ),
            stop_on_cascade=(
                self._config.stop_on_cascade
            ),
            cascade_threshold_percent=(
                self._config.cascade_threshold_percent
            ),
            voltage_min_pu=(
                self._config.voltage_min_pu
            ),
            voltage_max_pu=(
                self._config.voltage_max_pu
            ),
            frequency_min_hz=(
                self._config.frequency_min_hz
            ),
            frequency_max_hz=(
                self._config.frequency_max_hz
            ),
            loading_limit_percent=(
                self._config.loading_limit_percent
            ),
            random_seed=(
                self._config.random_seed
            ),
            parameters=dict(
                self._config.parameters
            ),
        )


__all__ = [
    "SimulationStatus",
    "SimulationType",
    "SimulationSeverity",
    "SimulationEvent",
    "SimulationState",
    "SimulationMetrics",
    "SimulationResult",
    "SimulationConfig",
    "SimulationContext",
    "BaseSimulator",
    "SimulationBuilder",
]