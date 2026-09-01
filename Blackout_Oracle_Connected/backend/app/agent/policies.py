"""
Blackout Oracle - AI Agent Safety and Behavioral Policies.

This module defines the rules that govern what the Blackout Oracle AI agent
is allowed and not allowed to do.

The policies are deliberately deterministic. The LLM must not be allowed
to override these rules.

Blackout Oracle is a decision-support system and must remain human-in-the-loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


# ============================================================
# POLICY ENUMS
# ============================================================


class ActionType(str, Enum):
    """Actions that the Blackout Oracle agent may attempt."""

    OBSERVE = "observe"
    ANALYZE = "analyze"
    PREDICT = "predict"
    INVESTIGATE = "investigate"
    SIMULATE = "simulate"
    VERIFY = "verify"
    RANK = "rank"
    RECOMMEND = "recommend"
    ALERT = "alert"

    # Explicitly represented so they can be rejected by policy.
    CONTROL_GRID = "control_grid"
    MODIFY_SCADA = "modify_scada"
    OPERATE_BREAKER = "operate_breaker"
    MODIFY_SUBSTATION = "modify_substation"


class PolicyDecision(str, Enum):
    """Possible outcomes of a policy evaluation."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_HUMAN_APPROVAL = "require_human_approval"


class RiskLevel(str, Enum):
    """Standard Blackout Oracle risk levels."""

    NORMAL = "normal"
    WATCH = "watch"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# POLICY RESULT
# ============================================================


@dataclass(frozen=True)
class PolicyResult:
    """
    Result of evaluating an agent action against safety policies.

    Attributes:
        decision: Whether the action is allowed, denied, or requires approval.
        reason: Human-readable explanation.
        policy: Policy responsible for the decision.
    """

    decision: PolicyDecision
    reason: str
    policy: str


# ============================================================
# CORE SAFETY POLICY
# ============================================================


class SafetyPolicy:
    """
    Deterministic safety policy for the Blackout Oracle agent.

    The AI agent can:

    - Read permitted data
    - Analyze data
    - Run predictions
    - Run simulations
    - Generate hypothetical scenarios
    - Verify simulated scenarios
    - Rank verified scenarios
    - Generate recommendations
    - Create alerts

    The AI agent cannot:

    - Control real grid equipment
    - Operate breakers
    - Modify SCADA
    - Write to utility control systems
    - Bypass authentication
    - Execute arbitrary infrastructure commands
    """

    # Actions that are always safe within the application.
    ALLOWED_ACTIONS: frozenset[ActionType] = frozenset(
        {
            ActionType.OBSERVE,
            ActionType.ANALYZE,
            ActionType.PREDICT,
            ActionType.INVESTIGATE,
            ActionType.SIMULATE,
            ActionType.VERIFY,
            ActionType.RANK,
            ActionType.RECOMMEND,
            ActionType.ALERT,
        }
    )

    # Actions that are permanently forbidden.
    DENIED_ACTIONS: frozenset[ActionType] = frozenset(
        {
            ActionType.CONTROL_GRID,
            ActionType.MODIFY_SCADA,
            ActionType.OPERATE_BREAKER,
            ActionType.MODIFY_SUBSTATION,
        }
    )

    def evaluate(self, action: ActionType) -> PolicyResult:
        """
        Evaluate whether an agent action is permitted.

        Args:
            action: Action being requested.

        Returns:
            PolicyResult describing the policy decision.
        """

        if action in self.DENIED_ACTIONS:
            return PolicyResult(
                decision=PolicyDecision.DENY,
                reason=(
                    "Blackout Oracle is a read-only decision-support system "
                    "and cannot directly control or modify electrical infrastructure."
                ),
                policy="critical_infrastructure_control",
            )

        if action in self.ALLOWED_ACTIONS:
            return PolicyResult(
                decision=PolicyDecision.ALLOW,
                reason="Action is permitted by the Blackout Oracle safety policy.",
                policy="read_only_analysis",
            )

        return PolicyResult(
            decision=PolicyDecision.DENY,
            reason="Unknown actions are denied by default.",
            policy="default_deny",
        )


# ============================================================
# HUMAN APPROVAL POLICY
# ============================================================


class HumanApprovalPolicy:
    """
    Determines which actions require human review.

    Recommendations that could influence real-world grid operations must
    always remain human-reviewed.

    The current implementation intentionally requires approval for every
    operational recommendation.
    """

    def requires_approval(self, action: ActionType) -> bool:
        """Return whether an action requires human approval."""

        return action in {
            ActionType.RECOMMEND,
            ActionType.ALERT,
        }

    def evaluate(self, action: ActionType) -> PolicyResult:
        """Return the human-approval requirement for an action."""

        if self.requires_approval(action):
            return PolicyResult(
                decision=PolicyDecision.REQUIRE_HUMAN_APPROVAL,
                reason=(
                    "This action may influence operational decision-making "
                    "and requires review by an authorized human operator."
                ),
                policy="human_in_the_loop",
            )

        return PolicyResult(
            decision=PolicyDecision.ALLOW,
            reason="Action does not require operational human approval.",
            policy="human_in_the_loop",
        )


# ============================================================
# SIMULATION POLICY
# ============================================================


class SimulationPolicy:
    """
    Rules governing scenario simulation.

    The agent may generate hypothetical scenarios, but every scenario must
    pass through the simulation and verification layers before becoming a
    recommendation.
    """

    def can_recommend(
        self,
        simulation_result: dict[str, Any] | None,
        verification_result: dict[str, Any] | None,
    ) -> PolicyResult:
        """
        Determine whether a simulated scenario may become a recommendation.
        """

        if simulation_result is None:
            return PolicyResult(
                decision=PolicyDecision.DENY,
                reason="Scenario has not been simulated.",
                policy="simulation_required",
            )

        if verification_result is None:
            return PolicyResult(
                decision=PolicyDecision.DENY,
                reason="Scenario has not been verified.",
                policy="verification_required",
            )

        verification_status = str(
            verification_result.get("status", "")
        ).upper()

        if verification_status not in {
            "VERIFIED",
            "PASSED",
            "SAFE",
        }:
            return PolicyResult(
                decision=PolicyDecision.DENY,
                reason=(
                    "Scenario failed simulation verification and cannot "
                    "be recommended."
                ),
                policy="verification_required",
            )

        return PolicyResult(
            decision=PolicyDecision.REQUIRE_HUMAN_APPROVAL,
            reason=(
                "Scenario passed simulation verification but requires "
                "human approval before operational consideration."
            ),
            policy="verified_scenario_human_review",
        )


# ============================================================
# DATA QUALITY POLICY
# ============================================================


class DataQualityPolicy:
    """
    Prevents unreliable or stale data from being silently treated as current.

    Data quality is especially important for real-time blackout prediction.
    """

    def evaluate(
        self,
        *,
        is_stale: bool = False,
        source_available: bool = True,
        is_simulated: bool = False,
        quality_score: float = 100.0,
    ) -> PolicyResult:
        """
        Evaluate the reliability of an input data source.

        Args:
            is_stale: Whether the data is older than its allowed freshness.
            source_available: Whether the source is currently available.
            is_simulated: Whether the data is synthetic/simulated.
            quality_score: Normalized data-quality score from 0 to 100.
        """

        quality_score = max(0.0, min(100.0, float(quality_score)))

        if not source_available:
            return PolicyResult(
                decision=PolicyDecision.DENY,
                reason="Data source is unavailable.",
                policy="data_availability",
            )

        if is_stale:
            return PolicyResult(
                decision=PolicyDecision.DENY,
                reason="Data is stale and cannot be treated as real-time telemetry.",
                policy="data_freshness",
            )

        if quality_score < 50:
            return PolicyResult(
                decision=PolicyDecision.DENY,
                reason="Data quality is below the minimum acceptable threshold.",
                policy="data_quality",
            )

        if is_simulated:
            return PolicyResult(
                decision=PolicyDecision.ALLOW,
                reason=(
                    "Synthetic data is permitted for simulation and development, "
                    "but must be explicitly identified as simulated."
                ),
                policy="synthetic_data",
            )

        return PolicyResult(
            decision=PolicyDecision.ALLOW,
            reason="Data passed the quality policy.",
            policy="data_quality",
        )


# ============================================================
# CONFIDENCE POLICY
# ============================================================


class ConfidencePolicy:
    """
    Controls how prediction confidence affects recommendations.

    High-risk predictions with low confidence should not be presented as
    certain events.
    """

    MINIMUM_RECOMMENDATION_CONFIDENCE = 60.0
    MINIMUM_CRITICAL_ALERT_CONFIDENCE = 50.0

    def evaluate_recommendation(
        self,
        confidence: float,
    ) -> PolicyResult:
        """Evaluate whether prediction confidence is sufficient."""

        confidence = max(0.0, min(100.0, float(confidence)))

        if confidence < self.MINIMUM_RECOMMENDATION_CONFIDENCE:
            return PolicyResult(
                decision=PolicyDecision.DENY,
                reason=(
                    f"Prediction confidence ({confidence:.1f}%) is below "
                    f"the recommendation threshold "
                    f"({self.MINIMUM_RECOMMENDATION_CONFIDENCE:.1f}%)."
                ),
                policy="recommendation_confidence",
            )

        return PolicyResult(
            decision=PolicyDecision.REQUIRE_HUMAN_APPROVAL,
            reason=(
                f"Prediction confidence ({confidence:.1f}%) is sufficient "
                "for consideration but human approval remains required."
            ),
            policy="recommendation_confidence",
        )

    def evaluate_alert(
        self,
        confidence: float,
    ) -> PolicyResult:
        """Evaluate whether confidence is sufficient for a critical alert."""

        confidence = max(0.0, min(100.0, float(confidence)))

        if confidence < self.MINIMUM_CRITICAL_ALERT_CONFIDENCE:
            return PolicyResult(
                decision=PolicyDecision.DENY,
                reason=(
                    f"Prediction confidence ({confidence:.1f}%) is too low "
                    "for a critical alert."
                ),
                policy="alert_confidence",
            )

        return PolicyResult(
            decision=PolicyDecision.REQUIRE_HUMAN_APPROVAL,
            reason=(
                "Alert may be generated, but operational interpretation "
                "requires human review."
            ),
            policy="alert_confidence",
        )


# ============================================================
# BLACKOUT ORACLE POLICY MANAGER
# ============================================================


class BlackoutOraclePolicy:
    """
    Central policy manager used by the AI agent.

    All agent actions should pass through this class before execution.
    """

    def __init__(self) -> None:
        self.safety = SafetyPolicy()
        self.human_approval = HumanApprovalPolicy()
        self.simulation = SimulationPolicy()
        self.data_quality = DataQualityPolicy()
        self.confidence = ConfidencePolicy()

    # ------------------------------------------------------------------
    # Action Evaluation
    # ------------------------------------------------------------------

    def evaluate_action(self, action: ActionType) -> PolicyResult:
        """
        Evaluate an agent action against the core safety policy.
        """

        return self.safety.evaluate(action)

    # ------------------------------------------------------------------
    # Recommendation Evaluation
    # ------------------------------------------------------------------

    def evaluate_recommendation(
        self,
        *,
        simulation_result: dict[str, Any] | None,
        verification_result: dict[str, Any] | None,
        confidence: float,
    ) -> PolicyResult:
        """
        Determine whether a scenario can become a recommendation.

        Requirements:

        1. Scenario must be simulated.
        2. Scenario must be verified.
        3. Confidence must be sufficient.
        4. Human approval remains mandatory.
        """

        simulation_policy = self.simulation.can_recommend(
            simulation_result,
            verification_result,
        )

        if simulation_policy.decision == PolicyDecision.DENY:
            return simulation_policy

        confidence_policy = self.confidence.evaluate_recommendation(
            confidence
        )

        if confidence_policy.decision == PolicyDecision.DENY:
            return confidence_policy

        return PolicyResult(
            decision=PolicyDecision.REQUIRE_HUMAN_APPROVAL,
            reason=(
                "Scenario passed simulation and confidence checks. "
                "Human approval is still required."
            ),
            policy="recommendation_gate",
        )

    # ------------------------------------------------------------------
    # Alert Evaluation
    # ------------------------------------------------------------------

    def evaluate_alert(
        self,
        *,
        confidence: float,
        risk_level: RiskLevel,
    ) -> PolicyResult:
        """
        Determine whether an alert may be generated.
        """

        confidence_policy = self.confidence.evaluate_alert(confidence)

        if confidence_policy.decision == PolicyDecision.DENY:
            return confidence_policy

        if risk_level in {
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        }:
            return PolicyResult(
                decision=PolicyDecision.REQUIRE_HUMAN_APPROVAL,
                reason=(
                    f"{risk_level.value.upper()} risk detected. "
                    "Alert may be generated, but human review is required."
                ),
                policy="high_risk_alert",
            )

        return PolicyResult(
            decision=PolicyDecision.ALLOW,
            reason="Alert meets the configured risk and confidence requirements.",
            policy="standard_alert",
        )


# ============================================================
# DEFAULT POLICY INSTANCE
# ============================================================

default_policy = BlackoutOraclePolicy()