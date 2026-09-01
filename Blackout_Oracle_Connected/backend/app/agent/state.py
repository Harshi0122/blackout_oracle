"""
Blackout Oracle - AI Agent State.

This module defines the state carried throughout an AI-agent investigation.

The state acts as the shared memory between:

    Observation
        ↓
    Detection
        ↓
    Investigation
        ↓
    Prediction
        ↓
    Scenario Generation
        ↓
    Simulation
        ↓
    Verification
        ↓
    Recommendation
        ↓
    Human Review

The state contains data and results, not the agent's private chain-of-thought.
Only auditable inputs, outputs, tool results, decisions, and metadata should
be persisted.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ============================================================
# ENUMS
# ============================================================


class InvestigationStatus(str, Enum):
    """Lifecycle state of an investigation."""

    CREATED = "created"
    OBSERVING = "observing"
    DETECTING = "detecting"
    ASSESSING = "assessing"
    INVESTIGATING = "investigating"
    SCENARIO_GENERATION = "scenario_generation"
    SIMULATING = "simulating"
    VERIFYING = "verifying"
    RANKING = "ranking"
    RECOMMENDATION_READY = "recommendation_ready"
    HUMAN_REVIEW = "human_review"
    RESOLVED = "resolved"
    FAILED = "failed"


class EvidenceType(str, Enum):
    """Classification of evidence collected by the agent."""

    OBSERVED_FACT = "observed_fact"
    MODEL_PREDICTION = "model_prediction"
    HYPOTHESIS = "hypothesis"
    SIMULATION_RESULT = "simulation_result"
    EXTERNAL_REPORT = "external_report"


class ScenarioStatus(str, Enum):
    """Lifecycle state of a simulation scenario."""

    GENERATED = "generated"
    SIMULATING = "simulating"
    SIMULATED = "simulated"
    VERIFIED = "verified"
    REJECTED = "rejected"
    FAILED = "failed"


class RiskLevel(str, Enum):
    """Blackout Oracle risk classification."""

    NORMAL = "normal"
    WATCH = "watch"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# EVIDENCE
# ============================================================


@dataclass
class Evidence:
    """
    Auditable piece of evidence collected during an investigation.

    Examples:

    - Current transformer loading
    - Weather observation
    - Load forecast
    - ML anomaly score
    - Simulation result

    Attributes:
        evidence_id: Unique identifier.
        evidence_type: Classification of the evidence.
        source: Data source or tool that produced it.
        data: Actual structured result.
        timestamp: Time at which the evidence was recorded.
        confidence: Optional confidence associated with the evidence.
        is_simulated: Whether the evidence came from synthetic data.
        metadata: Additional metadata.
    """

    evidence_id: str
    evidence_type: EvidenceType
    source: str
    data: dict[str, Any]
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    confidence: float | None = None
    is_simulated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalize confidence values."""
        if self.confidence is not None:
            self.confidence = max(
                0.0,
                min(100.0, float(self.confidence)),
            )


# ============================================================
# RISK ASSESSMENT
# ============================================================


@dataclass
class RiskAssessment:
    """
    Current blackout-risk assessment.

    Risk and confidence are deliberately separate.

    Example:

        risk_score = 82
        confidence = 54

    means the estimated risk is high but confidence in that estimate
    is relatively low.
    """

    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.NORMAL
    confidence: float = 0.0

    warning_horizon_minutes: float | None = None

    blackout_probability: float | None = None
    cascade_probability: float | None = None

    affected_assets: list[str] = field(default_factory=list)

    contributing_factors: list[str] = field(default_factory=list)

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        """Clamp probability and confidence values."""

        self.risk_score = max(
            0.0,
            min(100.0, float(self.risk_score)),
        )

        self.confidence = max(
            0.0,
            min(100.0, float(self.confidence)),
        )

        if self.blackout_probability is not None:
            self.blackout_probability = max(
                0.0,
                min(1.0, float(self.blackout_probability)),
            )

        if self.cascade_probability is not None:
            self.cascade_probability = max(
                0.0,
                min(1.0, float(self.cascade_probability)),
            )


# ============================================================
# SCENARIO
# ============================================================


@dataclass
class Scenario:
    """
    Hypothetical grid scenario generated for simulation.

    A Scenario represents a proposed change to the digital twin.

    It does NOT represent an instruction to modify the real grid.
    """

    scenario_id: str
    name: str
    description: str

    changes: list[dict[str, Any]] = field(default_factory=list)

    status: ScenarioStatus = ScenarioStatus.GENERATED

    simulation_result: dict[str, Any] | None = None
    verification_result: dict[str, Any] | None = None

    risk_reduction: float | None = None
    expected_impact: float | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    metadata: dict[str, Any] = field(default_factory=dict)


# ============================================================
# RECOMMENDATION
# ============================================================


@dataclass
class Recommendation:
    """
    Auditable recommendation produced after scenario evaluation.

    A recommendation must reference a verified scenario.

    Human approval remains mandatory before any operational decision.
    """

    scenario_id: str

    title: str
    explanation: str

    rationale: list[str] = field(default_factory=list)

    risk_before: float | None = None
    risk_after: float | None = None

    confidence: float = 0.0

    verification_status: str = ""

    requires_human_approval: bool = True

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalize confidence."""
        self.confidence = max(
            0.0,
            min(100.0, float(self.confidence)),
        )


# ============================================================
# AGENT ACTION RECORD
# ============================================================


@dataclass
class AgentAction:
    """
    Auditable record of an action performed by the agent.

    This stores the action and its result, not hidden chain-of-thought.
    """

    action_id: str
    action_type: str

    tool_name: str | None = None

    input_summary: dict[str, Any] = field(default_factory=dict)
    output_summary: dict[str, Any] = field(default_factory=dict)

    status: str = "completed"

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    error: str | None = None


# ============================================================
# INVESTIGATION STATE
# ============================================================


@dataclass
class InvestigationState:
    """
    Complete state of one Blackout Oracle investigation.

    This is the central state object passed between agent workflow stages.

    The state is intentionally explicit and serializable so that an
    investigation can be inspected, resumed, tested, and audited.
    """

    incident_id: str

    status: InvestigationStatus = InvestigationStatus.CREATED

    region_id: str | None = None
    region_name: str | None = None

    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # --------------------------------------------------------
    # Current Grid State
    # --------------------------------------------------------

    grid_state: dict[str, Any] = field(default_factory=dict)

    weather_state: dict[str, Any] = field(default_factory=dict)

    # --------------------------------------------------------
    # Evidence
    # --------------------------------------------------------

    evidence: list[Evidence] = field(default_factory=list)

    # --------------------------------------------------------
    # Risk
    # --------------------------------------------------------

    risk_assessment: RiskAssessment | None = None

    # --------------------------------------------------------
    # Hypotheses
    # --------------------------------------------------------

    hypotheses: list[dict[str, Any]] = field(default_factory=list)

    # --------------------------------------------------------
    # Scenarios
    # --------------------------------------------------------

    scenarios: list[Scenario] = field(default_factory=list)

    # --------------------------------------------------------
    # Recommendation
    # --------------------------------------------------------

    recommendation: Recommendation | None = None

    # --------------------------------------------------------
    # Agent Actions
    # --------------------------------------------------------

    actions: list[AgentAction] = field(default_factory=list)

    # --------------------------------------------------------
    # Errors
    # --------------------------------------------------------

    errors: list[str] = field(default_factory=list)

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    metadata: dict[str, Any] = field(default_factory=dict)

    # ========================================================
    # STATE MANAGEMENT
    # ========================================================

    def update_status(
        self,
        status: InvestigationStatus,
    ) -> None:
        """Update the investigation lifecycle status."""

        self.status = status
        self.touch()

    def touch(self) -> None:
        """Update the state's modification timestamp."""

        self.updated_at = datetime.now(timezone.utc)

    # ========================================================
    # EVIDENCE
    # ========================================================

    def add_evidence(
        self,
        evidence: Evidence,
    ) -> None:
        """Add auditable evidence to the investigation."""

        self.evidence.append(evidence)
        self.touch()

    # ========================================================
    # HYPOTHESES
    # ========================================================

    def add_hypothesis(
        self,
        hypothesis: dict[str, Any],
    ) -> None:
        """Add a root-cause hypothesis."""

        self.hypotheses.append(hypothesis)
        self.touch()

    # ========================================================
    # SCENARIOS
    # ========================================================

    def add_scenario(
        self,
        scenario: Scenario,
    ) -> None:
        """Add a candidate simulation scenario."""

        self.scenarios.append(scenario)
        self.touch()

    def get_scenario(
        self,
        scenario_id: str,
    ) -> Scenario | None:
        """Return a scenario by ID."""

        for scenario in self.scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario

        return None

    def get_verified_scenarios(self) -> list[Scenario]:
        """Return scenarios that passed verification."""

        return [
            scenario
            for scenario in self.scenarios
            if scenario.status == ScenarioStatus.VERIFIED
        ]

    # ========================================================
    # RECOMMENDATION
    # ========================================================

    def set_recommendation(
        self,
        recommendation: Recommendation,
    ) -> None:
        """Set the current recommendation."""

        self.recommendation = recommendation
        self.update_status(
            InvestigationStatus.RECOMMENDATION_READY
        )

    # ========================================================
    # ACTION LOG
    # ========================================================

    def add_action(
        self,
        action: AgentAction,
    ) -> None:
        """Record an auditable agent action."""

        self.actions.append(action)
        self.touch()

    # ========================================================
    # ERRORS
    # ========================================================

    def add_error(
        self,
        error: str,
    ) -> None:
        """Record an investigation error."""

        if error.strip():
            self.errors.append(error.strip())

        self.touch()

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the investigation state to a dictionary.

        Useful for:

        - API responses
        - Logging
        - Persistence
        - Debugging
        - Audit records
        """

        return asdict(self)

    def summary(self) -> dict[str, Any]:
        """
        Return a compact summary of the investigation.

        This is preferable to exposing the entire state in API responses.
        """

        risk = self.risk_assessment

        return {
            "incident_id": self.incident_id,
            "status": self.status.value,
            "region_id": self.region_id,
            "region_name": self.region_name,
            "risk_score": risk.risk_score if risk else None,
            "risk_level": risk.risk_level.value if risk else None,
            "confidence": risk.confidence if risk else None,
            "warning_horizon_minutes": (
                risk.warning_horizon_minutes if risk else None
            ),
            "evidence_count": len(self.evidence),
            "hypothesis_count": len(self.hypotheses),
            "scenario_count": len(self.scenarios),
            "verified_scenario_count": len(
                self.get_verified_scenarios()
            ),
            "has_recommendation": self.recommendation is not None,
            "error_count": len(self.errors),
            "updated_at": self.updated_at.isoformat(),
        }


# ============================================================
# STATE FACTORY
# ============================================================


def create_investigation_state(
    incident_id: str,
    *,
    region_id: str | None = None,
    region_name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> InvestigationState:
    """
    Create a new investigation state.

    Args:
        incident_id: Unique incident identifier.
        region_id: Optional grid region identifier.
        region_name: Optional human-readable region name.
        metadata: Optional investigation metadata.

    Returns:
        Newly initialized InvestigationState.
    """

    if not incident_id.strip():
        raise ValueError("incident_id cannot be empty.")

    return InvestigationState(
        incident_id=incident_id,
        region_id=region_id,
        region_name=region_name,
        metadata=metadata or {},
    )


__all__ = [
    "InvestigationStatus",
    "EvidenceType",
    "ScenarioStatus",
    "RiskLevel",
    "Evidence",
    "RiskAssessment",
    "Scenario",
    "Recommendation",
    "AgentAction",
    "InvestigationState",
    "create_investigation_state",
]