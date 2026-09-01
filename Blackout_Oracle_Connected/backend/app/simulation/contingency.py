"""
Blackout Oracle - Contingency Simulation.

Provides N-1 / N-k contingency analysis for electrical-grid assets.

The simulator evaluates the effect of intentionally removing one or
more assets from the current grid state and measures resulting
failures, overloads, voltage/frequency violations, and blackout risk.

This module is designed to work with the common simulation interfaces
defined in app.simulation.base.
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
    SimulationMetrics,
    SimulationResult,
    SimulationSeverity,
    SimulationState,
    SimulationStatus,
    SimulationType,
)


# ============================================================
# CONTINGENCY CASE
# ============================================================


@dataclass
class ContingencyCase:
    """
    Describes a single contingency scenario.

    A contingency may represent the outage of one asset or a
    simultaneous outage of multiple assets.
    """

    name: str

    asset_ids: list[int] = field(
        default_factory=list
    )

    description: str | None = None

    probability: float | None = None

    parameters: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        # Remove duplicate asset IDs while preserving order.
        self.asset_ids = list(
            dict.fromkeys(
                int(asset_id)
                for asset_id in self.asset_ids
            )
        )

        if self.probability is not None:
            self.probability = max(
                0.0,
                min(
                    1.0,
                    float(self.probability),
                ),
            )

    @property
    def size(self) -> int:
        """Return the number of assets removed by this contingency."""

        return len(self.asset_ids)

    @property
    def is_n_minus_one(self) -> bool:
        """Return True when this is a single-asset contingency."""

        return self.size == 1

    def to_dict(self) -> dict[str, Any]:
        """Convert the contingency case to a dictionary."""

        return {
            "name": self.name,
            "asset_ids": list(self.asset_ids),
            "description": self.description,
            "probability": self.probability,
            "parameters": dict(self.parameters),
        }


# ============================================================
# CONTINGENCY RESULT
# ============================================================


@dataclass
class ContingencyResult:
    """
    Result of one contingency scenario.
    """

    case: ContingencyCase

    status: SimulationStatus = (
        SimulationStatus.PENDING
    )

    risk_score: float = 0.0

    severity: SimulationSeverity = (
        SimulationSeverity.NONE
    )

    failed_assets: list[int] = field(
        default_factory=list
    )

    overloaded_assets: list[int] = field(
        default_factory=list
    )

    islanded_assets: list[int] = field(
        default_factory=list
    )

    load_lost_mw: float = 0.0

    generation_lost_mw: float = 0.0

    customers_affected: int = 0

    minimum_voltage_pu: float | None = None

    maximum_voltage_pu: float | None = None

    minimum_frequency_hz: float | None = None

    maximum_frequency_hz: float | None = None

    blackout_detected: bool = False

    cascade_detected: bool = False

    cascade_depth: int = 0

    events: list[SimulationEvent] = field(
        default_factory=list
    )

    simulation: SimulationResult | None = None

    error: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def calculate_severity(self) -> SimulationSeverity:
        """Calculate severity from the resulting risk score."""

        score = max(
            0.0,
            min(
                100.0,
                float(self.risk_score),
            ),
        )

        if self.blackout_detected or score >= 90.0:
            self.severity = (
                SimulationSeverity.CRITICAL
            )
        elif self.cascade_detected or score >= 75.0:
            self.severity = (
                SimulationSeverity.HIGH
            )
        elif score >= 50.0:
            self.severity = (
                SimulationSeverity.MEDIUM
            )
        elif score >= 25.0:
            self.severity = (
                SimulationSeverity.LOW
            )
        else:
            self.severity = (
                SimulationSeverity.NONE
            )

        return self.severity

    def to_dict(self) -> dict[str, Any]:
        """Convert the result to a serializable dictionary."""

        return {
            "case": self.case.to_dict(),
            "status": self.status.value,
            "risk_score": self.risk_score,
            "severity": self.severity.value,
            "failed_assets": list(
                self.failed_assets
            ),
            "overloaded_assets": list(
                self.overloaded_assets
            ),
            "islanded_assets": list(
                self.islanded_assets
            ),
            "load_lost_mw": self.load_lost_mw,
            "generation_lost_mw": (
                self.generation_lost_mw
            ),
            "customers_affected": (
                self.customers_affected
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
            "blackout_detected": (
                self.blackout_detected
            ),
            "cascade_detected": (
                self.cascade_detected
            ),
            "cascade_depth": self.cascade_depth,
            "events": [
                event.to_dict()
                for event in self.events
            ],
            "error": self.error,
            "metadata": dict(self.metadata),
        }


# ============================================================
# CONTINGENCY ANALYZER
# ============================================================


class ContingencyAnalyzer:
    """
    Deterministic analyzer for the final state of a contingency.

    This class deliberately does not assume a particular power-flow
    solver. It evaluates the available simulation state and applies
    configurable operational thresholds.
    """

    def __init__(
        self,
        *,
        loading_limit_percent: float = 100.0,
        voltage_min_pu: float = 0.90,
        voltage_max_pu: float = 1.10,
        frequency_min_hz: float = 49.0,
        frequency_max_hz: float = 51.0,
    ) -> None:
        self.loading_limit_percent = float(
            loading_limit_percent
        )

        self.voltage_min_pu = float(
            voltage_min_pu
        )

        self.voltage_max_pu = float(
            voltage_max_pu
        )

        self.frequency_min_hz = float(
            frequency_min_hz
        )

        self.frequency_max_hz = float(
            frequency_max_hz
        )

    def analyze(
        self,
        case: ContingencyCase,
        initial_state: SimulationState,
        final_state: SimulationState,
        *,
        events: list[SimulationEvent] | None = None,
    ) -> ContingencyResult:
        """
        Analyze a completed contingency scenario.
        """

        result = ContingencyResult(
            case=case,
            status=SimulationStatus.COMPLETED,
            events=list(
                events or []
            ),
        )

        result.failed_assets = sorted(
            final_state.failed_assets
        )

        result.overloaded_assets = sorted(
            final_state.overloaded_assets
        )

        result.islanded_assets = sorted(
            final_state.islanded_assets
        )

        result.minimum_voltage_pu = (
            min(
                final_state.voltage.values()
            )
            if final_state.voltage
            else None
        )

        result.maximum_voltage_pu = (
            max(
                final_state.voltage.values()
            )
            if final_state.voltage
            else None
        )

        result.minimum_frequency_hz = (
            min(
                final_state.frequency.values()
            )
            if final_state.frequency
            else None
        )

        result.maximum_frequency_hz = (
            max(
                final_state.frequency.values()
            )
            if final_state.frequency
            else None
        )

        result.blackout_detected = (
            self.detect_blackout(
                final_state
            )
        )

        result.cascade_detected = (
            self.detect_cascade(
                initial_state,
                final_state,
            )
        )

        result.cascade_depth = (
            self.calculate_cascade_depth(
                initial_state,
                final_state,
            )
        )

        result.load_lost_mw = (
            self.calculate_load_loss(
                initial_state,
                final_state,
            )
        )

        result.generation_lost_mw = (
            self.calculate_generation_loss(
                initial_state,
                final_state,
            )
        )

        result.customers_affected = (
            self.calculate_customers_affected(
                final_state
            )
        )

        result.risk_score = (
            self.calculate_risk_score(
                result
            )
        )

        result.calculate_severity()

        return result

    def detect_blackout(
        self,
        state: SimulationState,
    ) -> bool:
        """
        Detect a complete or near-complete loss of grid service.

        A blackout is considered present when there are no active
        assets in a populated asset-status map, or when all modeled
        load-serving assets have failed.
        """

        if not state.asset_status:
            return False

        active_statuses = {
            "active",
            "online",
            "connected",
            "in_service",
            "in-service",
        }

        active_assets = sum(
            1
            for status in state.asset_status.values()
            if str(status).lower()
            in active_statuses
        )

        if active_assets == 0:
            return True

        # If explicit load information exists, determine whether
        # every modeled load-bearing node has effectively failed.
        if state.active_power:
            positive_load_nodes = [
                asset_id
                for asset_id, power
                in state.active_power.items()
                if float(power) > 0.0
            ]

            if positive_load_nodes:
                served = [
                    asset_id
                    for asset_id in positive_load_nodes
                    if asset_id
                    not in state.failed_assets
                ]

                if not served:
                    return True

        return False

    def detect_cascade(
        self,
        initial_state: SimulationState,
        final_state: SimulationState,
    ) -> bool:
        """
        Detect whether failures expanded beyond the injected outage.
        """

        initial_failures = set(
            initial_state.failed_assets
        )

        final_failures = set(
            final_state.failed_assets
        )

        new_failures = (
            final_failures
            - initial_failures
        )

        return bool(
            new_failures
        )

    def calculate_cascade_depth(
        self,
        initial_state: SimulationState,
        final_state: SimulationState,
    ) -> int:
        """
        Estimate cascade depth from newly failed assets.

        The basic state representation does not contain explicit
        parent-child failure relationships, so the depth is estimated
        conservatively from the number of failure waves.
        """

        initial_count = len(
            initial_state.failed_assets
        )

        final_count = len(
            final_state.failed_assets
        )

        if final_count <= initial_count:
            return 0

        additional = (
            final_count
            - initial_count
        )

        if additional <= 0:
            return 0

        return min(
            10,
            additional,
        )

    def calculate_load_loss(
        self,
        initial_state: SimulationState,
        final_state: SimulationState,
    ) -> float:
        """
        Estimate lost active load in MW.

        Positive active-power values are treated as demand/load
        unless explicit metadata indicates otherwise.
        """

        initial_load = sum(
            max(
                0.0,
                float(value),
            )
            for value in initial_state.active_power.values()
        )

        final_load = sum(
            max(
                0.0,
                float(value),
            )
            for value in final_state.active_power.values()
        )

        return max(
            0.0,
            initial_load - final_load,
        )

    def calculate_generation_loss(
        self,
        initial_state: SimulationState,
        final_state: SimulationState,
    ) -> float:
        """
        Estimate generation loss when generation values are supplied
        through state metadata.
        """

        initial_generation = self._metadata_number(
            initial_state,
            "generation_mw",
        )

        final_generation = self._metadata_number(
            final_state,
            "generation_mw",
        )

        if (
            initial_generation is None
            or final_generation is None
        ):
            return 0.0

        return max(
            0.0,
            initial_generation
            - final_generation,
        )

    @staticmethod
    def calculate_customers_affected(
        state: SimulationState,
    ) -> int:
        """
        Extract estimated affected customers from state metadata.
        """

        for key in (
            "customers_affected",
            "affected_customers",
            "customers_lost",
        ):
            value = state.metadata.get(
                key
            )

            if value is not None:
                try:
                    return max(
                        0,
                        int(value),
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    continue

        return 0

    @staticmethod
    def _metadata_number(
        state: SimulationState,
        key: str,
    ) -> float | None:
        """Read a numeric metadata value."""

        value = state.metadata.get(
            key
        )

        if value is None:
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    def calculate_risk_score(
        self,
        result: ContingencyResult,
    ) -> float:
        """
        Calculate a 0-100 contingency risk score.
        """

        score = 0.0

        # Explicitly failed assets.
        score += min(
            30.0,
            len(result.failed_assets) * 8.0,
        )

        # Overloads indicate reduced security margin.
        score += min(
            20.0,
            len(result.overloaded_assets) * 4.0,
        )

        # Islanding can substantially increase risk.
        score += min(
            20.0,
            len(result.islanded_assets) * 6.0,
        )

        # Load loss.
        score += min(
            15.0,
            result.load_lost_mw / 10.0,
        )

        # Voltage violations.
        voltage_penalty = 0.0

        if result.minimum_voltage_pu is not None:
            if (
                result.minimum_voltage_pu
                < self.voltage_min_pu
            ):
                voltage_penalty += min(
                    10.0,
                    (
                        self.voltage_min_pu
                        - result.minimum_voltage_pu
                    )
                    * 100.0,
                )

        if result.maximum_voltage_pu is not None:
            if (
                result.maximum_voltage_pu
                > self.voltage_max_pu
            ):
                voltage_penalty += min(
                    10.0,
                    (
                        result.maximum_voltage_pu
                        - self.voltage_max_pu
                    )
                    * 100.0,
                )

        score += min(
            15.0,
            voltage_penalty,
        )

        # Frequency violations.
        frequency_penalty = 0.0

        if result.minimum_frequency_hz is not None:
            if (
                result.minimum_frequency_hz
                < self.frequency_min_hz
            ):
                frequency_penalty += min(
                    10.0,
                    (
                        self.frequency_min_hz
                        - result.minimum_frequency_hz
                    )
                    * 5.0,
                )

        if result.maximum_frequency_hz is not None:
            if (
                result.maximum_frequency_hz
                > self.frequency_max_hz
            ):
                frequency_penalty += min(
                    10.0,
                    (
                        result.maximum_frequency_hz
                        - self.frequency_max_hz
                    )
                    * 5.0,
                )

        score += min(
            10.0,
            frequency_penalty,
        )

        if result.cascade_detected:
            score += 15.0

        if result.blackout_detected:
            score += 30.0

        return max(
            0.0,
            min(
                100.0,
                score,
            ),
        )


# ============================================================
# CONTINGENCY SIMULATOR
# ============================================================


class ContingencySimulator(BaseSimulator):
    """
    Simulator for N-1, N-k, and custom contingency scenarios.

    This class operates on the generic SimulationState model. It does
    not perform a full AC/DC power-flow solution itself; instead it
    propagates the explicit outage through the available state and
    applies conservative overload/violation detection.
    """

    @property
    def simulation_type(
        self,
    ) -> SimulationType:
        """Return the simulator type."""

        return SimulationType.CONTINGENCY

    def __init__(
        self,
        config: SimulationConfig | None = None,
        *,
        analyzer: ContingencyAnalyzer | None = None,
    ) -> None:
        if config is None:
            config = SimulationConfig(
                simulation_type=(
                    SimulationType.CONTINGENCY
                )
            )
        else:
            config.simulation_type = (
                SimulationType.CONTINGENCY
            )

        super().__init__(
            config
        )

        self.analyzer = (
            analyzer
            if analyzer is not None
            else ContingencyAnalyzer(
                loading_limit_percent=(
                    config.loading_limit_percent
                ),
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
            )
        )

        self._events: list[
            SimulationEvent
        ] = []

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def initialize(
        self,
        state: SimulationState,
        events: list[SimulationEvent],
    ) -> SimulationContext:
        """
        Initialize a contingency simulation.

        All supplied outage events are applied before the first
        simulation step.
        """

        working_state = state.copy()

        self._events = list(
            events
        )

        for event in events:
            if event.asset_id is None:
                continue

            event_type = event.event_type.lower()

            if any(
                keyword in event_type
                for keyword in (
                    "fail",
                    "outage",
                    "trip",
                    "disconnect",
                )
            ):
                working_state.fail_asset(
                    event.asset_id
                )

        context = SimulationContext(
            config=self.config,
            state=working_state,
            events=list(events),
        )

        context.metadata[
            "simulation_type"
        ] = self.simulation_type.value

        context.metadata[
            "contingency_asset_ids"
        ] = [
            event.asset_id
            for event in events
            if event.asset_id is not None
        ]

        return context

    # ========================================================
    # SIMULATION STEP
    # ========================================================

    def step(
        self,
        context: SimulationContext,
    ) -> SimulationState:
        """
        Execute one contingency propagation step.

        Failed assets remain unavailable. Loading is checked against
        the configured threshold and affected assets are marked.
        """

        state = context.state

        self._propagate_failure(
            state
        )

        self._detect_overloads(
            state
        )

        self._detect_voltage_violations(
            state
        )

        self._detect_frequency_violations(
            state
        )

        context.state = state

        return state

    # ========================================================
    # FAILURE PROPAGATION
    # ========================================================

    def _propagate_failure(
        self,
        state: SimulationState,
    ) -> None:
        """
        Apply simple failure propagation based on loading.

        An overloaded asset can fail when its loading substantially
        exceeds the configured limit.
        """

        threshold = max(
            self.config.loading_limit_percent,
            self.config.cascade_threshold_percent,
        )

        for asset_id, loading in list(
            state.loading.items()
        ):
            if asset_id in state.failed_assets:
                continue

            try:
                loading_value = float(
                    loading
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            if loading_value >= (
                threshold * 1.25
            ):
                state.fail_asset(
                    asset_id
                )

    # ========================================================
    # OVERLOAD DETECTION
    # ========================================================

    def _detect_overloads(
        self,
        state: SimulationState,
    ) -> None:
        """
        Mark assets whose loading exceeds the configured limit.
        """

        limit = (
            self.config.loading_limit_percent
        )

        for asset_id, loading in state.loading.items():
            try:
                loading_value = float(
                    loading
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            state.mark_overloaded(
                asset_id,
                loading_value >= limit,
            )

    # ========================================================
    # VOLTAGE VIOLATIONS
    # ========================================================

    def _detect_voltage_violations(
        self,
        state: SimulationState,
    ) -> None:
        """
        Record voltage violations in simulation metadata.
        """

        violations: list[int] = []

        for asset_id, voltage in state.voltage.items():
            try:
                voltage_value = float(
                    voltage
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            if (
                voltage_value
                < self.config.voltage_min_pu
                or voltage_value
                > self.config.voltage_max_pu
            ):
                violations.append(
                    asset_id
                )

        state.metadata[
            "voltage_violations"
        ] = violations

    # ========================================================
    # FREQUENCY VIOLATIONS
    # ========================================================

    def _detect_frequency_violations(
        self,
        state: SimulationState,
    ) -> None:
        """
        Record frequency violations in simulation metadata.
        """

        violations: list[int] = []

        for asset_id, frequency in state.frequency.items():
            try:
                frequency_value = float(
                    frequency
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            if (
                frequency_value
                < self.config.frequency_min_hz
                or frequency_value
                > self.config.frequency_max_hz
            ):
                violations.append(
                    asset_id
                )

        state.metadata[
            "frequency_violations"
        ] = violations

    # ========================================================
    # RUN CONTINGENCY
    # ========================================================

    def run_contingency(
        self,
        state: SimulationState,
        case: ContingencyCase,
    ) -> ContingencyResult:
        """
        Run a single contingency case.
        """

        events = [
            SimulationEvent(
                event_type="asset_outage",
                asset_id=asset_id,
                severity=SimulationSeverity.HIGH,
                description=(
                    f"Contingency outage of asset "
                    f"{asset_id}."
                ),
            )
            for asset_id in case.asset_ids
        ]

        simulation = self.run(
            state,
            events,
        )

        if simulation.final_state is None:
            return ContingencyResult(
                case=case,
                status=simulation.status,
                error=simulation.error,
                simulation=simulation,
            )

        result = self.analyzer.analyze(
            case,
            state,
            simulation.final_state,
            events=events,
        )

        result.simulation = simulation
        result.status = simulation.status
        result.error = simulation.error

        return result

    # ========================================================
    # N-1 ANALYSIS
    # ========================================================

    def run_n_minus_one(
        self,
        state: SimulationState,
        asset_ids: Iterable[int] | None = None,
    ) -> list[ContingencyResult]:
        """
        Run an N-1 contingency study.

        Each supplied asset is removed individually and evaluated.
        """

        if asset_ids is None:
            asset_ids = state.asset_status.keys()

        results: list[
            ContingencyResult
        ] = []

        for asset_id in asset_ids:
            case = ContingencyCase(
                name=f"N-1 outage of asset {asset_id}",
                asset_ids=[int(asset_id)],
                description=(
                    "Single asset outage contingency."
                ),
            )

            results.append(
                self.run_contingency(
                    state,
                    case,
                )
            )

        return results

    # ========================================================
    # N-K ANALYSIS
    # ========================================================

    def run_n_minus_k(
        self,
        state: SimulationState,
        cases: Iterable[ContingencyCase],
    ) -> list[ContingencyResult]:
        """
        Run a collection of N-k contingency scenarios.
        """

        results: list[
            ContingencyResult
        ] = []

        for case in cases:
            if not case.asset_ids:
                continue

            results.append(
                self.run_contingency(
                    state,
                    case,
                )
            )

        return results

    # ========================================================
    # RANKING
    # ========================================================

    @staticmethod
    def rank_results(
        results: Iterable[ContingencyResult],
    ) -> list[ContingencyResult]:
        """
        Rank contingency cases from highest to lowest risk.
        """

        ranked = list(
            results
        )

        ranked.sort(
            key=lambda result: (
                result.risk_score,
                int(
                    result.blackout_detected
                ),
                int(
                    result.cascade_detected
                ),
                len(
                    result.overloaded_assets
                ),
            ),
            reverse=True,
        )

        return ranked

    @staticmethod
    def critical_results(
        results: Iterable[ContingencyResult],
        *,
        threshold: float = 75.0,
    ) -> list[ContingencyResult]:
        """
        Return contingency results above a risk threshold.
        """

        threshold = max(
            0.0,
            min(
                100.0,
                float(threshold),
            ),
        )

        return [
            result
            for result in results
            if (
                result.risk_score >= threshold
                or result.blackout_detected
                or result.cascade_detected
            )
        ]

    # ========================================================
    # SUMMARY
    # ========================================================

    @staticmethod
    def summarize_results(
        results: Iterable[ContingencyResult],
    ) -> dict[str, Any]:
        """
        Generate a summary of a contingency study.
        """

        results = list(
            results
        )

        if not results:
            return {
                "total_cases": 0,
                "critical_cases": 0,
                "high_risk_cases": 0,
                "blackout_cases": 0,
                "cascade_cases": 0,
                "maximum_risk_score": 0.0,
                "average_risk_score": 0.0,
                "most_critical_case": None,
            }

        critical_cases = [
            result
            for result in results
            if result.severity
            == SimulationSeverity.CRITICAL
        ]

        high_risk_cases = [
            result
            for result in results
            if result.risk_score >= 75.0
        ]

        blackout_cases = [
            result
            for result in results
            if result.blackout_detected
        ]

        cascade_cases = [
            result
            for result in results
            if result.cascade_detected
        ]

        highest = max(
            results,
            key=lambda result: result.risk_score,
        )

        average_score = (
            sum(
                result.risk_score
                for result in results
            )
            / len(results)
        )

        return {
            "total_cases": len(results),
            "critical_cases": len(
                critical_cases
            ),
            "high_risk_cases": len(
                high_risk_cases
            ),
            "blackout_cases": len(
                blackout_cases
            ),
            "cascade_cases": len(
                cascade_cases
            ),
            "maximum_risk_score": (
                highest.risk_score
            ),
            "average_risk_score": (
                average_score
            ),
            "most_critical_case": (
                highest.case.to_dict()
            ),
        }


# ============================================================
# CONTINGENCY FACTORY
# ============================================================


def create_n_minus_one_cases(
    asset_ids: Iterable[int],
) -> list[ContingencyCase]:
    """
    Create standard N-1 contingency cases.
    """

    return [
        ContingencyCase(
            name=(
                f"N-1 outage of asset "
                f"{asset_id}"
            ),
            asset_ids=[int(asset_id)],
            description=(
                "Single asset outage."
            ),
        )
        for asset_id in asset_ids
    ]


def create_n_minus_k_case(
    asset_ids: Iterable[int],
    *,
    name: str | None = None,
    description: str | None = None,
) -> ContingencyCase:
    """
    Create a simultaneous N-k contingency case.
    """

    normalized_ids = list(
        dict.fromkeys(
            int(asset_id)
            for asset_id in asset_ids
        )
    )

    if not normalized_ids:
        raise ValueError(
            "At least one asset ID is required."
        )

    return ContingencyCase(
        name=(
            name
            or (
                "N-"
                + str(len(normalized_ids))
                + " contingency: "
                + ",".join(
                    map(
                        str,
                        normalized_ids,
                    )
                )
            )
        ),
        asset_ids=normalized_ids,
        description=description,
    )


__all__ = [
    "ContingencyCase",
    "ContingencyResult",
    "ContingencyAnalyzer",
    "ContingencySimulator",
    "create_n_minus_one_cases",
    "create_n_minus_k_case",
]