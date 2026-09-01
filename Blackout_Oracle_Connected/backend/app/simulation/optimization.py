"""
Blackout Oracle - Simulation Optimization.

Provides deterministic optimization utilities for selecting
contingency scenarios, prioritizing grid interventions, and
finding low-risk operational alternatives.

The optimizer is intentionally solver-agnostic. A production
deployment can plug in an external OPF/SCOPF solver while this
module continues to provide the application-level optimization
interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable, Sequence

from app.simulation.base import (
    SimulationResult,
    SimulationSeverity,
    SimulationState,
)
from app.simulation.contingency import (
    ContingencyCase,
    ContingencyResult,
    ContingencySimulator,
)


# ============================================================
# ENUMS
# ============================================================


class OptimizationObjective(str, Enum):
    """Optimization objectives supported by the service."""

    MINIMIZE_RISK = "minimize_risk"
    MINIMIZE_LOAD_LOSS = "minimize_load_loss"
    MINIMIZE_OVERLOAD = "minimize_overload"
    MINIMIZE_FAILURES = "minimize_failures"
    MAXIMIZE_SECURITY = "maximize_security"
    BALANCED = "balanced"


class OptimizationStatus(str, Enum):
    """Lifecycle state of an optimization request."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INFEASIBLE = "infeasible"


# ============================================================
# OPTIMIZATION CONSTRAINT
# ============================================================


@dataclass
class OptimizationConstraint:
    """
    Constraint applied during candidate evaluation.
    """

    name: str

    maximum: float | None = None

    minimum: float | None = None

    weight: float = 1.0

    hard: bool = True

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def check(
        self,
        value: float,
    ) -> bool:
        """Return whether a value satisfies this constraint."""

        value = float(value)

        if (
            self.minimum is not None
            and value < float(self.minimum)
        ):
            return False

        if (
            self.maximum is not None
            and value > float(self.maximum)
        ):
            return False

        return True

    def violation(
        self,
        value: float,
    ) -> float:
        """
        Return normalized constraint violation.

        Zero means no violation.
        """

        value = float(value)

        violation = 0.0

        if (
            self.minimum is not None
            and value < float(self.minimum)
        ):
            denominator = max(
                abs(float(self.minimum)),
                1.0,
            )

            violation = max(
                violation,
                (
                    float(self.minimum)
                    - value
                )
                / denominator,
            )

        if (
            self.maximum is not None
            and value > float(self.maximum)
        ):
            denominator = max(
                abs(float(self.maximum)),
                1.0,
            )

            violation = max(
                violation,
                (
                    value
                    - float(self.maximum)
                )
                / denominator,
            )

        return violation

    def to_dict(self) -> dict[str, Any]:
        """Serialize the constraint."""

        return {
            "name": self.name,
            "maximum": self.maximum,
            "minimum": self.minimum,
            "weight": self.weight,
            "hard": self.hard,
            "metadata": dict(self.metadata),
        }


# ============================================================
# CANDIDATE
# ============================================================


@dataclass
class OptimizationCandidate:
    """
    Candidate operational state or contingency result.
    """

    candidate_id: str

    actions: list[dict[str, Any]] = field(
        default_factory=list
    )

    risk_score: float = 0.0

    load_loss_mw: float = 0.0

    generation_loss_mw: float = 0.0

    overloaded_assets: int = 0

    failed_assets: int = 0

    affected_assets: int = 0

    blackout_probability: float | None = None

    security_margin: float = 100.0

    objective_value: float = 0.0

    feasible: bool = True

    constraint_violations: dict[str, float] = field(
        default_factory=dict
    )

    simulation: SimulationResult | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def calculate_security_margin(
        self,
    ) -> float:
        """Calculate a simple 0-100 security margin."""

        risk_component = max(
            0.0,
            min(
                100.0,
                self.risk_score,
            ),
        )

        overload_component = min(
            30.0,
            self.overloaded_assets * 5.0,
        )

        failure_component = min(
            30.0,
            self.failed_assets * 8.0,
        )

        load_component = min(
            20.0,
            max(
                0.0,
                self.load_loss_mw,
            )
            / 10.0,
        )

        self.security_margin = max(
            0.0,
            min(
                100.0,
                100.0
                - (
                    risk_component * 0.5
                    + overload_component
                    + failure_component
                    + load_component
                ),
            ),
        )

        return self.security_margin

    def to_dict(self) -> dict[str, Any]:
        """Serialize the candidate."""

        return {
            "candidate_id": self.candidate_id,
            "actions": list(self.actions),
            "risk_score": self.risk_score,
            "load_loss_mw": self.load_loss_mw,
            "generation_loss_mw": self.generation_loss_mw,
            "overloaded_assets": self.overloaded_assets,
            "failed_assets": self.failed_assets,
            "affected_assets": self.affected_assets,
            "blackout_probability": self.blackout_probability,
            "security_margin": self.security_margin,
            "objective_value": self.objective_value,
            "feasible": self.feasible,
            "constraint_violations": dict(
                self.constraint_violations
            ),
            "metadata": dict(self.metadata),
        }


# ============================================================
# OPTIMIZATION RESULT
# ============================================================


@dataclass
class OptimizationResult:
    """
    Complete result of an optimization operation.
    """

    status: OptimizationStatus

    objective: OptimizationObjective

    best_candidate: OptimizationCandidate | None = None

    candidates: list[OptimizationCandidate] = field(
        default_factory=list
    )

    iterations: int = 0

    execution_time_seconds: float = 0.0

    message: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def feasible_candidates(
        self,
    ) -> list[OptimizationCandidate]:
        """Return candidates satisfying all hard constraints."""

        return [
            candidate
            for candidate in self.candidates
            if candidate.feasible
        ]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the optimization result."""

        return {
            "status": self.status.value,
            "objective": self.objective.value,
            "best_candidate": (
                self.best_candidate.to_dict()
                if self.best_candidate is not None
                else None
            ),
            "candidates": [
                candidate.to_dict()
                for candidate in self.candidates
            ],
            "iterations": self.iterations,
            "execution_time_seconds": (
                self.execution_time_seconds
            ),
            "message": self.message,
            "metadata": dict(self.metadata),
        }


# ============================================================
# OBJECTIVE FUNCTIONS
# ============================================================


class ObjectiveFunctions:
    """
    Standard objective functions used by the optimizer.
    """

    @staticmethod
    def minimize_risk(
        candidate: OptimizationCandidate,
    ) -> float:
        return candidate.risk_score

    @staticmethod
    def minimize_load_loss(
        candidate: OptimizationCandidate,
    ) -> float:
        return max(
            0.0,
            candidate.load_loss_mw,
        )

    @staticmethod
    def minimize_overload(
        candidate: OptimizationCandidate,
    ) -> float:
        return float(
            candidate.overloaded_assets
        )

    @staticmethod
    def minimize_failures(
        candidate: OptimizationCandidate,
    ) -> float:
        return float(
            candidate.failed_assets
        )

    @staticmethod
    def maximize_security(
        candidate: OptimizationCandidate,
    ) -> float:
        # Optimizers minimize by convention.
        return -candidate.security_margin

    @staticmethod
    def balanced(
        candidate: OptimizationCandidate,
    ) -> float:
        """
        Weighted multi-objective score.

        Lower is better.
        """

        return (
            candidate.risk_score * 0.45
            + min(
                100.0,
                max(
                    0.0,
                    candidate.load_loss_mw,
                ),
            )
            * 0.20
            + min(
                100.0,
                candidate.overloaded_assets * 10.0,
            )
            * 0.15
            + min(
                100.0,
                candidate.failed_assets * 10.0,
            )
            * 0.10
            + (
                100.0
                - candidate.security_margin
            )
            * 0.10
        )

    @classmethod
    def get(
        cls,
        objective: OptimizationObjective,
    ) -> Callable[
        [OptimizationCandidate],
        float,
    ]:
        """Return the objective function for an objective type."""

        functions = {
            OptimizationObjective.MINIMIZE_RISK:
                cls.minimize_risk,
            OptimizationObjective.MINIMIZE_LOAD_LOSS:
                cls.minimize_load_loss,
            OptimizationObjective.MINIMIZE_OVERLOAD:
                cls.minimize_overload,
            OptimizationObjective.MINIMIZE_FAILURES:
                cls.minimize_failures,
            OptimizationObjective.MAXIMIZE_SECURITY:
                cls.maximize_security,
            OptimizationObjective.BALANCED:
                cls.balanced,
        }

        return functions[
            objective
        ]


# ============================================================
# OPTIMIZER
# ============================================================


class SimulationOptimizer:
    """
    General-purpose optimizer for simulation candidates.

    The default implementation is deterministic and performs
    exhaustive evaluation over the candidate collection.

    For large optimization spaces, a more sophisticated solver
    can be supplied through the evaluator interface.
    """

    def __init__(
        self,
        *,
        objective: OptimizationObjective = (
            OptimizationObjective.BALANCED
        ),
        constraints: Iterable[
            OptimizationConstraint
        ] | None = None,
    ) -> None:
        self.objective = objective

        self.constraints = list(
            constraints or []
        )

        self.objective_function = (
            ObjectiveFunctions.get(
                objective
            )
        )

    # ========================================================
    # CONSTRAINT EVALUATION
    # ========================================================

    def evaluate_constraints(
        self,
        candidate: OptimizationCandidate,
    ) -> bool:
        """
        Evaluate all configured constraints.

        Hard constraint violations make the candidate infeasible.
        """

        candidate.constraint_violations.clear()

        hard_violation = False

        values = self._candidate_constraint_values(
            candidate
        )

        for constraint in self.constraints:
            if constraint.name not in values:
                continue

            value = values[
                constraint.name
            ]

            violation = constraint.violation(
                value
            )

            if violation > 0.0:
                candidate.constraint_violations[
                    constraint.name
                ] = violation

                if constraint.hard:
                    hard_violation = True

        candidate.feasible = not hard_violation

        return candidate.feasible

    @staticmethod
    def _candidate_constraint_values(
        candidate: OptimizationCandidate,
    ) -> dict[str, float]:
        """Map common constraint names to candidate values."""

        return {
            "risk_score": candidate.risk_score,
            "load_loss_mw": candidate.load_loss_mw,
            "generation_loss_mw": (
                candidate.generation_loss_mw
            ),
            "overloaded_assets": float(
                candidate.overloaded_assets
            ),
            "failed_assets": float(
                candidate.failed_assets
            ),
            "affected_assets": float(
                candidate.affected_assets
            ),
            "security_margin": candidate.security_margin,
            "blackout_probability": (
                candidate.blackout_probability
                if candidate.blackout_probability
                is not None
                else 0.0
            ),
        }

    # ========================================================
    # CANDIDATE EVALUATION
    # ========================================================

    def evaluate_candidate(
        self,
        candidate: OptimizationCandidate,
    ) -> OptimizationCandidate:
        """
        Calculate objective value and constraint status.
        """

        candidate.calculate_security_margin()

        self.evaluate_constraints(
            candidate
        )

        candidate.objective_value = (
            self.objective_function(
                candidate
            )
        )

        # Penalize infeasible candidates so they cannot win.
        if not candidate.feasible:
            candidate.objective_value += 1_000_000.0

        return candidate

    # ========================================================
    # OPTIMIZE
    # ========================================================

    def optimize(
        self,
        candidates: Iterable[OptimizationCandidate],
    ) -> OptimizationResult:
        """
        Select the best candidate according to the configured
        objective and constraints.
        """

        candidates = list(
            candidates
        )

        if not candidates:
            return OptimizationResult(
                status=OptimizationStatus.INFEASIBLE,
                objective=self.objective,
                message=(
                    "No optimization candidates were provided."
                ),
            )

        evaluated = [
            self.evaluate_candidate(
                candidate
            )
            for candidate in candidates
        ]

        feasible = [
            candidate
            for candidate in evaluated
            if candidate.feasible
        ]

        if not feasible:
            return OptimizationResult(
                status=OptimizationStatus.INFEASIBLE,
                objective=self.objective,
                candidates=evaluated,
                iterations=len(evaluated),
                message=(
                    "No candidate satisfies all hard constraints."
                ),
            )

        best = min(
            feasible,
            key=lambda candidate: (
                candidate.objective_value,
                candidate.risk_score,
                candidate.load_loss_mw,
                candidate.failed_assets,
            ),
        )

        return OptimizationResult(
            status=OptimizationStatus.COMPLETED,
            objective=self.objective,
            best_candidate=best,
            candidates=evaluated,
            iterations=len(evaluated),
            message=(
                "Optimization completed successfully."
            ),
        )


# ============================================================
# CONTINGENCY OPTIMIZER
# ============================================================


class ContingencyOptimizer:
    """
    Optimization layer built around the contingency simulator.

    It evaluates multiple contingency cases and ranks them by
    security impact.
    """

    def __init__(
        self,
        simulator: ContingencySimulator | None = None,
        *,
        objective: OptimizationObjective = (
            OptimizationObjective.BALANCED
        ),
        constraints: Iterable[
            OptimizationConstraint
        ] | None = None,
    ) -> None:
        self.simulator = (
            simulator
            if simulator is not None
            else ContingencySimulator()
        )

        self.optimizer = SimulationOptimizer(
            objective=objective,
            constraints=constraints,
        )

    # ========================================================
    # CONVERT RESULT
    # ========================================================

    @staticmethod
    def result_to_candidate(
        result: ContingencyResult,
        *,
        candidate_id: str | None = None,
    ) -> OptimizationCandidate:
        """
        Convert a contingency result into an optimization candidate.
        """

        candidate_id = (
            candidate_id
            or result.case.name
        )

        candidate = OptimizationCandidate(
            candidate_id=candidate_id,
            actions=[
                {
                    "type": "contingency",
                    "asset_ids": list(
                        result.case.asset_ids
                    ),
                }
            ],
            risk_score=result.risk_score,
            load_loss_mw=result.load_lost_mw,
            generation_loss_mw=(
                result.generation_lost_mw
            ),
            overloaded_assets=len(
                result.overloaded_assets
            ),
            failed_assets=len(
                result.failed_assets
            ),
            affected_assets=(
                len(result.failed_assets)
                + len(result.overloaded_assets)
                + len(result.islanded_assets)
            ),
            blackout_probability=(
                1.0
                if result.blackout_detected
                else None
            ),
            simulation=result.simulation,
            metadata={
                "case": result.case.to_dict(),
                "severity": result.severity.value,
                "blackout_detected": (
                    result.blackout_detected
                ),
                "cascade_detected": (
                    result.cascade_detected
                ),
                "cascade_depth": (
                    result.cascade_depth
                ),
                "customers_affected": (
                    result.customers_affected
                ),
            },
        )

        candidate.calculate_security_margin()

        return candidate

    # ========================================================
    # OPTIMIZE CASES
    # ========================================================

    def optimize_cases(
        self,
        state: SimulationState,
        cases: Iterable[ContingencyCase],
    ) -> OptimizationResult:
        """
        Run and optimize a collection of contingency cases.
        """

        results: list[
            ContingencyResult
        ] = []

        for case in cases:
            result = self.simulator.run_contingency(
                state,
                case,
            )

            results.append(
                result
            )

        candidates = [
            self.result_to_candidate(
                result
            )
            for result in results
        ]

        return self.optimizer.optimize(
            candidates
        )

    # ========================================================
    # RANK CASES
    # ========================================================

    def rank_cases(
        self,
        state: SimulationState,
        cases: Iterable[ContingencyCase],
    ) -> list[ContingencyResult]:
        """
        Rank contingency cases from highest to lowest operational
        impact.
        """

        results = [
            self.simulator.run_contingency(
                state,
                case,
            )
            for case in cases
        ]

        results.sort(
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
                result.load_lost_mw,
            ),
            reverse=True,
        )

        return results

    # ========================================================
    # CRITICAL CASE
    # ========================================================

    def worst_case(
        self,
        state: SimulationState,
        cases: Iterable[ContingencyCase],
    ) -> ContingencyResult | None:
        """
        Return the highest-risk contingency.
        """

        ranked = self.rank_cases(
            state,
            cases,
        )

        if not ranked:
            return None

        return ranked[0]


# ============================================================
# DISPATCH OPTIMIZATION
# ============================================================


@dataclass
class DispatchAction:
    """
    A candidate operational action.

    Examples include generator redispatch, load shedding,
    transformer tap adjustment, or line switching.
    """

    action_type: str

    asset_id: int | None = None

    value: float | None = None

    unit: str | None = None

    cost: float = 0.0

    risk_reduction: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the dispatch action."""

        return {
            "action_type": self.action_type,
            "asset_id": self.asset_id,
            "value": self.value,
            "unit": self.unit,
            "cost": self.cost,
            "risk_reduction": self.risk_reduction,
            "metadata": dict(self.metadata),
        }


@dataclass
class DispatchOptimizationResult:
    """
    Result of dispatch-action optimization.
    """

    status: OptimizationStatus

    selected_actions: list[DispatchAction] = field(
        default_factory=list
    )

    baseline_risk: float = 0.0

    optimized_risk: float = 0.0

    risk_reduction: float = 0.0

    total_cost: float = 0.0

    message: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the dispatch result."""

        return {
            "status": self.status.value,
            "selected_actions": [
                action.to_dict()
                for action in self.selected_actions
            ],
            "baseline_risk": self.baseline_risk,
            "optimized_risk": self.optimized_risk,
            "risk_reduction": self.risk_reduction,
            "total_cost": self.total_cost,
            "message": self.message,
            "metadata": dict(self.metadata),
        }


class DispatchOptimizer:
    """
    Deterministic greedy optimizer for operational actions.

    Actions are selected according to risk reduction per unit cost.
    """

    def optimize(
        self,
        baseline_risk: float,
        actions: Iterable[DispatchAction],
        *,
        maximum_cost: float | None = None,
        target_risk: float | None = None,
    ) -> DispatchOptimizationResult:
        """
        Select actions that provide the greatest estimated risk
        reduction while respecting an optional cost limit.
        """

        baseline_risk = max(
            0.0,
            min(
                100.0,
                float(baseline_risk),
            ),
        )

        if maximum_cost is not None:
            maximum_cost = max(
                0.0,
                float(maximum_cost),
            )

        if target_risk is not None:
            target_risk = max(
                0.0,
                min(
                    100.0,
                    float(target_risk),
                ),
            )

        available = [
            action
            for action in actions
            if action.risk_reduction > 0.0
            and action.cost >= 0.0
        ]

        available.sort(
            key=lambda action: (
                action.risk_reduction
                / max(
                    action.cost,
                    0.000001,
                ),
                action.risk_reduction,
            ),
            reverse=True,
        )

        selected: list[
            DispatchAction
        ] = []

        current_risk = baseline_risk
        total_cost = 0.0

        for action in available:
            if (
                maximum_cost is not None
                and total_cost
                + action.cost
                > maximum_cost
            ):
                continue

            reduction = min(
                current_risk,
                float(
                    action.risk_reduction
                ),
            )

            if reduction <= 0.0:
                continue

            selected.append(
                action
            )

            total_cost += action.cost

            current_risk = max(
                0.0,
                current_risk - reduction,
            )

            if (
                target_risk is not None
                and current_risk <= target_risk
            ):
                break

        return DispatchOptimizationResult(
            status=OptimizationStatus.COMPLETED,
            selected_actions=selected,
            baseline_risk=baseline_risk,
            optimized_risk=current_risk,
            risk_reduction=(
                baseline_risk
                - current_risk
            ),
            total_cost=total_cost,
            message=(
                "Dispatch optimization completed."
            ),
        )


# ============================================================
# SECURITY MARGIN OPTIMIZATION
# ============================================================


class SecurityMarginOptimizer:
    """
    Utility for selecting the safest candidate based on security
    margin while considering operational cost.
    """

    @staticmethod
    def optimize(
        candidates: Iterable[OptimizationCandidate],
        *,
        minimum_security_margin: float = 50.0,
        maximum_risk: float = 75.0,
    ) -> OptimizationResult:
        """
        Select the candidate with the highest security margin that
        remains within the risk threshold.
        """

        candidates = list(
            candidates
        )

        constraints = [
            OptimizationConstraint(
                name="security_margin",
                minimum=minimum_security_margin,
                hard=True,
            ),
            OptimizationConstraint(
                name="risk_score",
                maximum=maximum_risk,
                hard=True,
            ),
        ]

        optimizer = SimulationOptimizer(
            objective=(
                OptimizationObjective.MAXIMIZE_SECURITY
            ),
            constraints=constraints,
        )

        return optimizer.optimize(
            candidates
        )


# ============================================================
# ACTION GENERATORS
# ============================================================


def generate_load_shedding_actions(
    *,
    load_asset_ids: Iterable[int],
    step_mw: float = 5.0,
    maximum_mw: float = 50.0,
    cost_per_mw: float = 1.0,
) -> list[DispatchAction]:
    """
    Generate candidate load-shedding actions.

    These actions are candidates for optimization only; they do not
    directly modify the physical grid.
    """

    step_mw = max(
        0.1,
        float(step_mw),
    )

    maximum_mw = max(
        step_mw,
        float(maximum_mw),
    )

    cost_per_mw = max(
        0.0,
        float(cost_per_mw),
    )

    actions: list[
        DispatchAction
    ] = []

    for asset_id in load_asset_ids:
        amount = step_mw

        while amount <= maximum_mw:
            actions.append(
                DispatchAction(
                    action_type="load_shedding",
                    asset_id=int(asset_id),
                    value=amount,
                    unit="MW",
                    cost=(
                        amount
                        * cost_per_mw
                    ),
                    metadata={
                        "generated": True,
                    },
                )
            )

            amount += step_mw

    return actions


def generate_generator_redispatch_actions(
    *,
    generator_ids: Iterable[int],
    step_mw: float = 5.0,
    maximum_mw: float = 50.0,
    cost_per_mw: float = 1.0,
) -> list[DispatchAction]:
    """
    Generate candidate generator-redispatch actions.
    """

    step_mw = max(
        0.1,
        float(step_mw),
    )

    maximum_mw = max(
        step_mw,
        float(maximum_mw),
    )

    cost_per_mw = max(
        0.0,
        float(cost_per_mw),
    )

    actions: list[
        DispatchAction
    ] = []

    for asset_id in generator_ids:
        amount = step_mw

        while amount <= maximum_mw:
            actions.append(
                DispatchAction(
                    action_type="generator_redispatch",
                    asset_id=int(asset_id),
                    value=amount,
                    unit="MW",
                    cost=(
                        amount
                        * cost_per_mw
                    ),
                    metadata={
                        "generated": True,
                    },
                )
            )

            amount += step_mw

    return actions


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def optimize_candidates(
    candidates: Sequence[OptimizationCandidate],
    *,
    objective: OptimizationObjective = (
        OptimizationObjective.BALANCED
    ),
    constraints: Iterable[
        OptimizationConstraint
    ] | None = None,
) -> OptimizationResult:
    """
    Convenience wrapper around SimulationOptimizer.
    """

    optimizer = SimulationOptimizer(
        objective=objective,
        constraints=constraints,
    )

    return optimizer.optimize(
        candidates
    )


def optimize_contingencies(
    state: SimulationState,
    cases: Iterable[ContingencyCase],
    *,
    simulator: ContingencySimulator | None = None,
    objective: OptimizationObjective = (
        OptimizationObjective.BALANCED
    ),
    constraints: Iterable[
        OptimizationConstraint
    ] | None = None,
) -> OptimizationResult:
    """
    Convenience wrapper for contingency optimization.
    """

    optimizer = ContingencyOptimizer(
        simulator=simulator,
        objective=objective,
        constraints=constraints,
    )

    return optimizer.optimize_cases(
        state,
        cases,
    )


__all__ = [
    "OptimizationObjective",
    "OptimizationStatus",
    "OptimizationConstraint",
    "OptimizationCandidate",
    "OptimizationResult",
    "ObjectiveFunctions",
    "SimulationOptimizer",
    "ContingencyOptimizer",
    "DispatchAction",
    "DispatchOptimizationResult",
    "DispatchOptimizer",
    "SecurityMarginOptimizer",
    "generate_load_shedding_actions",
    "generate_generator_redispatch_actions",
    "optimize_candidates",
    "optimize_contingencies",
]