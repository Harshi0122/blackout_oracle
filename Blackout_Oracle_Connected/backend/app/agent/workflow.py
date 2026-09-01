"""
Blackout Oracle - AI Agent Workflow.

This module orchestrates the complete Blackout Oracle investigation pipeline.

Workflow:

    CREATED
       ↓
    OBSERVING
       ↓
    DETECTING
       ↓
    ASSESSING
       ↓
    INVESTIGATING
       ↓
    SCENARIO_GENERATION
       ↓
    SIMULATING
       ↓
    VERIFYING
       ↓
    RANKING
       ↓
    RECOMMENDATION_READY
       ↓
    HUMAN_REVIEW

The workflow is intentionally deterministic.

Gemini may assist with reasoning and scenario generation, but it cannot
bypass the workflow, safety policies, simulation, or verification stages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .agent import BlackoutOracleAgent
from .policies import (
    ActionType,
    BlackoutOraclePolicy,
    PolicyDecision,
)
from .state import (
    AgentAction,
    Evidence,
    EvidenceType,
    InvestigationState,
    InvestigationStatus,
    Recommendation,
    RiskAssessment,
    RiskLevel,
    Scenario,
    ScenarioStatus,
    create_investigation_state,
)
from .tools import AgentToolRegistry, ToolResult, create_default_tool_registry


# ============================================================
# WORKFLOW CONFIGURATION
# ============================================================


@dataclass(frozen=True)
class WorkflowConfig:
    """
    Configuration controlling the Blackout Oracle investigation workflow.
    """

    max_scenarios: int = 10

    require_simulation: bool = True
    require_verification: bool = True
    require_human_approval: bool = True

    minimum_recommendation_confidence: float = 60.0

    stop_on_tool_failure: bool = False


# ============================================================
# WORKFLOW RESULT
# ============================================================


@dataclass
class WorkflowResult:
    """
    Final result returned by the investigation workflow.
    """

    success: bool
    state: InvestigationState

    message: str = ""

    @property
    def summary(self) -> dict[str, Any]:
        """Return a compact investigation summary."""

        return self.state.summary()


# ============================================================
# BLACKOUT ORACLE WORKFLOW
# ============================================================


class BlackoutOracleWorkflow:
    """
    Main deterministic workflow for Blackout Oracle.

    Responsibilities:

    - Manage investigation state.
    - Execute approved analytical tools.
    - Enforce workflow ordering.
    - Enforce safety policies.
    - Ensure scenarios are simulated and verified.
    - Produce recommendations only from verified scenarios.
    - Maintain an auditable action history.

    The workflow does not directly interact with real grid infrastructure.
    """

    def __init__(
        self,
        *,
        agent: BlackoutOracleAgent | None = None,
        tool_registry: AgentToolRegistry | None = None,
        policy: BlackoutOraclePolicy | None = None,
        config: WorkflowConfig | None = None,
    ) -> None:
        self.config = config or WorkflowConfig()

        self.tool_registry = (
            tool_registry
            or create_default_tool_registry()
        )

        self.policy = (
            policy
            or BlackoutOraclePolicy()
        )

        self.agent = agent or BlackoutOracleAgent(
            tools=self.tool_registry.list_tools(),
            max_scenarios=self.config.max_scenarios,
        )

    # ========================================================
    # PUBLIC ENTRY POINT
    # ========================================================

    async def run(
        self,
        incident_id: str,
        *,
        region_id: str | None = None,
        region_name: str | None = None,
        initial_context: dict[str, Any] | None = None,
    ) -> WorkflowResult:
        """
        Run a complete Blackout Oracle investigation.

        Args:
            incident_id:
                Unique identifier for the incident.

            region_id:
                Optional grid region identifier.

            region_name:
                Optional human-readable region name.

            initial_context:
                Optional initial incident information.

        Returns:
            WorkflowResult containing the complete investigation state.
        """

        state = create_investigation_state(
            incident_id,
            region_id=region_id,
            region_name=region_name,
            metadata={
                "initial_context": initial_context or {},
            },
        )

        try:
            await self._observe(state)
            await self._detect(state)
            await self._assess(state)
            await self._investigate(state)
            await self._generate_scenarios(state)
            await self._simulate(state)
            await self._verify(state)
            await self._rank(state)
            await self._prepare_recommendation(state)

            if self.config.require_human_approval:
                state.update_status(
                    InvestigationStatus.HUMAN_REVIEW
                )

            return WorkflowResult(
                success=True,
                state=state,
                message="Investigation completed successfully.",
            )

        except Exception as exc:
            state.add_error(str(exc))
            state.update_status(
                InvestigationStatus.FAILED
            )

            return WorkflowResult(
                success=False,
                state=state,
                message=f"Investigation failed: {exc}",
            )

    # ========================================================
    # OBSERVE
    # ========================================================

    async def _observe(
        self,
        state: InvestigationState,
    ) -> None:
        """
        Collect the current grid and environmental state.
        """

        state.update_status(
            InvestigationStatus.OBSERVING
        )

        self._require_action(ActionType.OBSERVE)

        grid_result = await self._execute_tool(
            state,
            "get_grid_state",
            incident_id=state.incident_id,
            region_id=state.region_id,
        )

        if grid_result.success:
            state.grid_state = self._extract_data(
                grid_result
            )

            self._add_evidence(
                state,
                evidence_type=EvidenceType.OBSERVED_FACT,
                source="get_grid_state",
                data=state.grid_state,
            )

        weather_result = await self._execute_tool(
            state,
            "get_weather",
            incident_id=state.incident_id,
            region_id=state.region_id,
        )

        if weather_result.success:
            state.weather_state = self._extract_data(
                weather_result
            )

            self._add_evidence(
                state,
                evidence_type=EvidenceType.OBSERVED_FACT,
                source="get_weather",
                data=state.weather_state,
            )

    # ========================================================
    # DETECT
    # ========================================================

    async def _detect(
        self,
        state: InvestigationState,
    ) -> None:
        """
        Detect abnormal grid behavior.
        """

        state.update_status(
            InvestigationStatus.DETECTING
        )

        self._require_action(ActionType.ANALYZE)

        anomaly_result = await self._execute_tool(
            state,
            "detect_anomalies",
            incident_id=state.incident_id,
        )

        if anomaly_result.success:
            anomaly_data = self._extract_data(
                anomaly_result
            )

            self._add_evidence(
                state,
                evidence_type=EvidenceType.MODEL_PREDICTION,
                source="detect_anomalies",
                data=anomaly_data,
            )

    # ========================================================
    # ASSESS
    # ========================================================

    async def _assess(
        self,
        state: InvestigationState,
    ) -> None:
        """
        Run forecasting and blackout-risk assessment.
        """

        state.update_status(
            InvestigationStatus.ASSESSING
        )

        self._require_action(ActionType.PREDICT)

        forecast_result = await self._execute_tool(
            state,
            "run_load_forecast",
            incident_id=state.incident_id,
            horizon_minutes=60,
        )

        if forecast_result.success:
            forecast_data = self._extract_data(
                forecast_result
            )

            self._add_evidence(
                state,
                evidence_type=EvidenceType.MODEL_PREDICTION,
                source="run_load_forecast",
                data=forecast_data,
            )

        risk_result = await self._execute_tool(
            state,
            "calculate_blackout_risk",
            incident_id=state.incident_id,
        )

        if risk_result.success:
            risk_data = self._extract_data(
                risk_result
            )

            state.risk_assessment = self._build_risk_assessment(
                risk_data
            )

            self._add_evidence(
                state,
                evidence_type=EvidenceType.MODEL_PREDICTION,
                source="calculate_blackout_risk",
                data=risk_data,
                confidence=state.risk_assessment.confidence,
            )

    # ========================================================
    # INVESTIGATE
    # ========================================================

    async def _investigate(
        self,
        state: InvestigationState,
    ) -> None:
        """
        Allow the AI investigation layer to analyze the collected evidence.

        Gemini is used by the agent layer when configured.

        This stage does not permit direct infrastructure control.
        """

        state.update_status(
            InvestigationStatus.INVESTIGATING
        )

        self._require_action(ActionType.INVESTIGATE)

        context = {
            "region_id": state.region_id,
            "region_name": state.region_name,
            "grid_state": state.grid_state,
            "weather_state": state.weather_state,
            "risk_assessment": (
                state.risk_assessment
                and state.risk_assessment.__dict__
            ),
            "evidence": [
                evidence.__dict__
                for evidence in state.evidence
            ],
        }

        # Gemini/LLM investigation will be connected through the agent.
        #
        # We deliberately do not store hidden chain-of-thought.
        #
        # Only structured findings returned by the agent are persisted.

        try:
            result = await self.agent.investigate(
                incident_id=state.incident_id,
                context=context,
            )

            for finding in result.findings:
                if not isinstance(finding, dict):
                    continue

                self._add_evidence(
                    state,
                    evidence_type=EvidenceType.OBSERVED_FACT,
                    source=str(
                        finding.get(
                            "source",
                            "agent_investigation",
                        )
                    ),
                    data=finding,
                )

        except Exception as exc:
            state.add_error(
                f"Agent investigation error: {exc}"
            )

            if self.config.stop_on_tool_failure:
                raise

    # ========================================================
    # SCENARIO GENERATION
    # ========================================================

    async def _generate_scenarios(
        self,
        state: InvestigationState,
    ) -> None:
        """
        Generate hypothetical scenarios for simulation.
        """

        state.update_status(
            InvestigationStatus.SCENARIO_GENERATION
        )

        context = {
            "grid_state": state.grid_state,
            "weather_state": state.weather_state,
            "risk": (
                state.risk_assessment.__dict__
                if state.risk_assessment
                else None
            ),
            "evidence": [
                evidence.__dict__
                for evidence in state.evidence
            ],
            "hypotheses": state.hypotheses,
        }

        result = await self._execute_tool(
            state,
            "generate_scenarios",
            incident_id=state.incident_id,
            context=context,
            max_scenarios=self.config.max_scenarios,
        )

        if not result.success:
            return

        scenarios = self._extract_data(result)

        if not isinstance(scenarios, list):
            return

        for index, scenario_data in enumerate(
            scenarios[: self.config.max_scenarios],
            start=1,
        ):
            if not isinstance(scenario_data, dict):
                continue

            scenario_id = str(
                scenario_data.get(
                    "scenario_id",
                    f"scenario-{index}",
                )
            )

            scenario = Scenario(
                scenario_id=scenario_id,
                name=str(
                    scenario_data.get(
                        "name",
                        f"Scenario {index}",
                    )
                ),
                description=str(
                    scenario_data.get(
                        "description",
                        "",
                    )
                ),
                changes=list(
                    scenario_data.get(
                        "changes",
                        [],
                    )
                ),
            )

            state.add_scenario(scenario)

    # ========================================================
    # SIMULATION
    # ========================================================

    async def _simulate(
        self,
        state: InvestigationState,
    ) -> None:
        """
        Run all candidate scenarios through the digital twin.
        """

        state.update_status(
            InvestigationStatus.SIMULATING
        )

        if not self.config.require_simulation:
            return

        self._require_action(ActionType.SIMULATE)

        for scenario in state.scenarios:
            scenario.status = ScenarioStatus.SIMULATING
            state.touch()

            result = await self._execute_tool(
                state,
                "run_scenario",
                incident_id=state.incident_id,
                scenario={
                    "scenario_id": scenario.scenario_id,
                    "name": scenario.name,
                    "description": scenario.description,
                    "changes": scenario.changes,
                },
            )

            if not result.success:
                scenario.status = ScenarioStatus.FAILED
                state.add_error(
                    f"Simulation failed for "
                    f"{scenario.scenario_id}: "
                    f"{result.error}"
                )
                continue

            scenario.simulation_result = self._extract_data(
                result
            )

            scenario.status = ScenarioStatus.SIMULATED

            self._add_evidence(
                state,
                evidence_type=EvidenceType.SIMULATION_RESULT,
                source="run_scenario",
                data={
                    "scenario_id": scenario.scenario_id,
                    "result": scenario.simulation_result,
                },
                is_simulated=True,
            )

    # ========================================================
    # VERIFICATION
    # ========================================================

    async def _verify(
        self,
        state: InvestigationState,
    ) -> None:
        """
        Verify every simulated scenario.

        Unverified scenarios cannot become recommendations.
        """

        state.update_status(
            InvestigationStatus.VERIFYING
        )

        if not self.config.require_verification:
            return

        self._require_action(ActionType.VERIFY)

        for scenario in state.scenarios:
            if scenario.status != ScenarioStatus.SIMULATED:
                continue

            result = await self._execute_tool(
                state,
                "verify_scenario",
                incident_id=state.incident_id,
                scenario={
                    "scenario_id": scenario.scenario_id,
                    "name": scenario.name,
                    "description": scenario.description,
                    "changes": scenario.changes,
                },
                simulation=scenario.simulation_result,
            )

            if not result.success:
                scenario.status = ScenarioStatus.REJECTED

                state.add_error(
                    f"Verification failed for "
                    f"{scenario.scenario_id}: "
                    f"{result.error}"
                )

                continue

            scenario.verification_result = self._extract_data(
                result
            )

            if self._is_verified(
                scenario.verification_result
            ):
                scenario.status = ScenarioStatus.VERIFIED
            else:
                scenario.status = ScenarioStatus.REJECTED

            self._add_evidence(
                state,
                evidence_type=EvidenceType.SIMULATION_RESULT,
                source="verify_scenario",
                data={
                    "scenario_id": scenario.scenario_id,
                    "verification": scenario.verification_result,
                },
                is_simulated=True,
            )

    # ========================================================
    # RANK
    # ========================================================

    async def _rank(
        self,
        state: InvestigationState,
    ) -> None:
        """
        Rank verified scenarios only.
        """

        state.update_status(
            InvestigationStatus.RANKING
        )

        self._require_action(ActionType.RANK)

        verified = [
            scenario
            for scenario in state.scenarios
            if scenario.status == ScenarioStatus.VERIFIED
        ]

        if not verified:
            return

        scenario_payload = [
            {
                "scenario_id": scenario.scenario_id,
                "name": scenario.name,
                "description": scenario.description,
                "changes": scenario.changes,
                "simulation_result": scenario.simulation_result,
                "verification_result": scenario.verification_result,
            }
            for scenario in verified
        ]

        result = await self._execute_tool(
            state,
            "rank_scenarios",
            incident_id=state.incident_id,
            scenarios=scenario_payload,
        )

        if not result.success:
            state.add_error(
                f"Scenario ranking failed: {result.error}"
            )
            return

        ranking = self._extract_data(result)

        state.metadata["scenario_ranking"] = ranking

    # ========================================================
    # RECOMMENDATION
    # ========================================================

    async def _prepare_recommendation(
        self,
        state: InvestigationState,
    ) -> None:
        """
        Prepare a recommendation only when policy requirements are met.
        """

        verified = [
            scenario
            for scenario in state.scenarios
            if scenario.status == ScenarioStatus.VERIFIED
        ]

        if not verified:
            state.add_error(
                "No verified scenarios are available for recommendation."
            )
            return

        self._require_action(ActionType.RECOMMEND)

        confidence = (
            state.risk_assessment.confidence
            if state.risk_assessment
            else 0.0
        )

        ranking = state.metadata.get(
            "scenario_ranking"
        )

        selected_scenario_id = self._select_ranked_scenario(
            ranking,
            verified,
        )

        if selected_scenario_id is None:
            return

        selected = next(
            (
                scenario
                for scenario in verified
                if scenario.scenario_id == selected_scenario_id
            ),
            None,
        )

        if selected is None:
            return

        policy_result = (
            self.policy.evaluate_recommendation(
                simulation_result=selected.simulation_result,
                verification_result=selected.verification_result,
                confidence=confidence,
            )
        )

        if policy_result.decision == PolicyDecision.DENY:
            state.add_error(
                f"Recommendation rejected by policy: "
                f"{policy_result.reason}"
            )
            return

        recommendation = Recommendation(
            scenario_id=selected.scenario_id,
            title=selected.name,
            explanation=selected.description,
            rationale=[
                "Scenario passed simulation verification.",
                "Scenario was selected from the verified scenario set.",
            ],
            confidence=confidence,
            verification_status="VERIFIED",
            requires_human_approval=True,
        )

        state.set_recommendation(
            recommendation
        )

        state.metadata[
            "recommendation_policy"
        ] = {
            "decision": policy_result.decision.value,
            "reason": policy_result.reason,
            "policy": policy_result.policy,
        }

    # ========================================================
    # TOOL EXECUTION
    # ========================================================

    async def _execute_tool(
        self,
        state: InvestigationState,
        tool_name: str,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Execute an explicitly registered analytical tool.

        Every invocation is recorded in the investigation audit trail.
        """

        tool = self.tool_registry.get(
            tool_name
        )

        result = await tool.execute(
            **kwargs
        )

        state.add_action(
            AgentAction(
                action_id=self._generate_action_id(
                    state,
                    tool_name,
                ),
                action_type="tool_execution",
                tool_name=tool_name,
                input_summary=self._sanitize_for_audit(
                    kwargs
                ),
                output_summary=self._sanitize_for_audit(
                    result.data
                ),
                status=(
                    "completed"
                    if result.success
                    else "failed"
                ),
                error=result.error,
            )
        )

        if not result.success and self.config.stop_on_tool_failure:
            raise RuntimeError(
                f"Tool '{tool_name}' failed: {result.error}"
            )

        return result

    # ========================================================
    # POLICY
    # ========================================================

    def _require_action(
        self,
        action: ActionType,
    ) -> None:
        """
        Enforce the deterministic safety policy.
        """

        result = self.policy.evaluate_action(
            action
        )

        if result.decision == PolicyDecision.DENY:
            raise PermissionError(
                f"Action '{action.value}' denied: "
                f"{result.reason}"
            )

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _extract_data(
        result: ToolResult,
    ) -> Any:
        """Extract data from a successful tool result."""

        return result.data

    @staticmethod
    def _add_evidence(
        state: InvestigationState,
        *,
        evidence_type: EvidenceType,
        source: str,
        data: dict[str, Any] | Any,
        confidence: float | None = None,
        is_simulated: bool = False,
    ) -> None:
        """Add an evidence item to the investigation state."""

        if not isinstance(data, dict):
            data = {
                "value": data
            }

        evidence_id = (
            f"{state.incident_id}-"
            f"evidence-{len(state.evidence) + 1}"
        )

        state.add_evidence(
            Evidence(
                evidence_id=evidence_id,
                evidence_type=evidence_type,
                source=source,
                data=data,
                confidence=confidence,
                is_simulated=is_simulated,
            )
        )

    @staticmethod
    def _build_risk_assessment(
        risk_data: Any,
    ) -> RiskAssessment:
        """Convert risk-engine output into RiskAssessment."""

        if not isinstance(risk_data, dict):
            return RiskAssessment()

        risk_score = float(
            risk_data.get(
                "risk_score",
                0.0,
            )
            or 0.0
        )

        confidence = float(
            risk_data.get(
                "confidence",
                0.0,
            )
            or 0.0
        )

        risk_level_raw = str(
            risk_data.get(
                "risk_level",
                "normal",
            )
        ).lower()

        try:
            risk_level = RiskLevel(
                risk_level_raw
            )
        except ValueError:
            risk_level = (
                BlackoutOracleWorkflow._risk_level_from_score(
                    risk_score
                )
            )

        return RiskAssessment(
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=confidence,
            warning_horizon_minutes=risk_data.get(
                "warning_horizon_minutes"
            ),
            blackout_probability=risk_data.get(
                "blackout_probability"
            ),
            cascade_probability=risk_data.get(
                "cascade_probability"
            ),
            affected_assets=list(
                risk_data.get(
                    "affected_assets",
                    [],
                )
            ),
            contributing_factors=list(
                risk_data.get(
                    "contributing_factors",
                    [],
                )
            ),
        )

    @staticmethod
    def _risk_level_from_score(
        score: float,
    ) -> RiskLevel:
        """Convert a numerical risk score into a risk level."""

        if score >= 95:
            return RiskLevel.CRITICAL

        if score >= 80:
            return RiskLevel.HIGH

        if score >= 60:
            return RiskLevel.ELEVATED

        if score >= 40:
            return RiskLevel.WATCH

        return RiskLevel.NORMAL

    @staticmethod
    def _is_verified(
        verification: Any,
    ) -> bool:
        """Determine whether a verification result passed."""

        if not isinstance(verification, dict):
            return False

        if verification.get("verified") is True:
            return True

        status = str(
            verification.get(
                "status",
                "",
            )
        ).upper()

        return status in {
            "VERIFIED",
            "PASSED",
            "SAFE",
        }

    @staticmethod
    def _select_ranked_scenario(
        ranking: Any,
        verified: list[Scenario],
    ) -> str | None:
        """Select the highest-ranked verified scenario."""

        if isinstance(ranking, dict):
            selected = ranking.get(
                "recommended_scenario"
            )

            if isinstance(selected, str):
                if any(
                    scenario.scenario_id == selected
                    for scenario in verified
                ):
                    return selected

            selected = ranking.get(
                "scenario_id"
            )

            if isinstance(selected, str):
                if any(
                    scenario.scenario_id == selected
                    for scenario in verified
                ):
                    return selected

        # Safe deterministic fallback.
        return verified[0].scenario_id

    @staticmethod
    def _generate_action_id(
        state: InvestigationState,
        tool_name: str,
    ) -> str:
        """Generate a deterministic audit action identifier."""

        return (
            f"{state.incident_id}-"
            f"action-{len(state.actions) + 1}-"
            f"{tool_name}"
        )

    @staticmethod
    def _sanitize_for_audit(
        value: Any,
    ) -> dict[str, Any]:
        """
        Convert tool input/output into a safe audit representation.

        This prevents accidental persistence of extremely large or
        non-serializable objects.
        """

        if value is None:
            return {}

        if isinstance(value, dict):
            sanitized: dict[str, Any] = {}

            for key, item in value.items():
                if key.lower() in {
                    "api_key",
                    "password",
                    "secret",
                    "token",
                    "authorization",
                }:
                    sanitized[key] = "[REDACTED]"
                else:
                    sanitized[key] = item

            return sanitized

        return {
            "value": str(value)
        }


# ============================================================
# WORKFLOW FACTORY
# ============================================================


def create_default_workflow(
    *,
    config: WorkflowConfig | None = None,
) -> BlackoutOracleWorkflow:
    """
    Create a Blackout Oracle workflow using the default safe tools.
    """

    registry = create_default_tool_registry()

    agent = BlackoutOracleAgent(
        tools=registry.list_tools(),
        max_scenarios=(
            config.max_scenarios
            if config
            else 10
        ),
    )

    return BlackoutOracleWorkflow(
        agent=agent,
        tool_registry=registry,
        policy=BlackoutOraclePolicy(),
        config=config,
    )


__all__ = [
    "WorkflowConfig",
    "WorkflowResult",
    "BlackoutOracleWorkflow",
    "create_default_workflow",
]