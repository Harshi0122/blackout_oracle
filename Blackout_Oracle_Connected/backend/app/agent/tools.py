"""
Blackout Oracle - AI Agent Tools.

This module defines the tools that the AI agent can use to interact with
Blackout Oracle's analytical backend.

IMPORTANT SAFETY RULES
----------------------

The tools in this module are strictly analytical and read-only.

The agent may:

- Read grid state
- Read weather information
- Read historical data
- Run forecasts
- Detect anomalies
- Calculate risk
- Generate hypothetical scenarios
- Run simulations
- Verify simulations
- Rank verified scenarios
- Generate reports

The agent must NEVER be given tools that directly:

- Control breakers
- Modify substations
- Write to SCADA
- Control generators
- Change real grid configuration
- Execute arbitrary shell commands
- Access unauthorized utility infrastructure

All operational recommendations remain subject to human approval.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


# ============================================================
# TOOL RESULT
# ============================================================


@dataclass
class ToolResult:
    """
    Standard result returned by a Blackout Oracle agent tool.

    Attributes:
        success: Whether the tool completed successfully.
        tool_name: Name of the tool.
        data: Structured result data.
        error: Error message if execution failed.
        metadata: Additional information about the execution.
    """

    success: bool
    tool_name: str

    data: Any = None
    error: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(
        cls,
        tool_name: str,
        data: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Create a successful tool result."""

        return cls(
            success=True,
            tool_name=tool_name,
            data=data,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        tool_name: str,
        error: str,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Create a failed tool result."""

        return cls(
            success=False,
            tool_name=tool_name,
            error=error,
            metadata=metadata or {},
        )


# ============================================================
# BASE TOOL
# ============================================================


class BaseAgentTool(ABC):
    """
    Abstract base class for all Blackout Oracle agent tools.

    Every tool has:

    - A unique name.
    - A description.
    - An input schema.
    - An asynchronous execute() method.

    The tool itself is responsible for calling the appropriate backend
    service. The LLM should never directly access databases or infrastructure.
    """

    name: str
    description: str

    @property
    def input_schema(self) -> dict[str, Any]:
        """
        Return the JSON-compatible input schema for the tool.

        This schema will eventually be provided to Gemini for function/tool
        calling.
        """

        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    @abstractmethod
    async def execute(
        self,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute the tool."""
        raise NotImplementedError


# ============================================================
# FUNCTION-BASED TOOL
# ============================================================


class FunctionTool(BaseAgentTool):
    """
    Adapter for turning an asynchronous Python function into an agent tool.
    """

    def __init__(
        self,
        *,
        name: str,
        description: str,
        function: Callable[..., Awaitable[Any]],
        input_schema: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self._function = function
        self._input_schema = input_schema or {
            "type": "object",
            "properties": {},
            "required": [],
        }

    @property
    def input_schema(self) -> dict[str, Any]:
        """Return the function's JSON input schema."""

        return self._input_schema

    async def execute(
        self,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute the wrapped function."""

        try:
            result = await self._function(**kwargs)

            if isinstance(result, ToolResult):
                return result

            return ToolResult.ok(
                tool_name=self.name,
                data=result,
            )

        except Exception as exc:
            return ToolResult.failure(
                tool_name=self.name,
                error=str(exc),
            )


# ============================================================
# TOOL REGISTRY
# ============================================================


class AgentToolRegistry:
    """
    Registry containing the tools available to the Blackout Oracle agent.

    Only explicitly registered tools are accessible to the agent.

    This creates an allow-list rather than allowing arbitrary function
    execution.
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseAgentTool] = {}

    def register(
        self,
        tool: BaseAgentTool,
    ) -> None:
        """
        Register a tool.

        Raises:
            ValueError: If the tool name is empty or already registered.
        """

        if not tool.name.strip():
            raise ValueError("Tool name cannot be empty.")

        if tool.name in self._tools:
            raise ValueError(
                f"Tool '{tool.name}' is already registered."
            )

        self._tools[tool.name] = tool

    def get(
        self,
        name: str,
    ) -> BaseAgentTool:
        """Retrieve a registered tool."""

        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(
                f"Agent tool '{name}' is not registered."
            ) from exc

    def has(
        self,
        name: str,
    ) -> bool:
        """Return whether a tool is registered."""

        return name in self._tools

    def list_tools(self) -> list[BaseAgentTool]:
        """Return all registered tools."""

        return list(self._tools.values())

    def list_names(self) -> list[str]:
        """Return the names of registered tools."""

        return sorted(self._tools.keys())

    def schemas(self) -> list[dict[str, Any]]:
        """
        Return tool definitions in a model-friendly format.

        This structure can later be converted to Gemini's function/tool
        declaration format.
        """

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self.list_tools()
        ]


# ============================================================
# GRID STATE TOOL
# ============================================================


class GetGridStateTool(BaseAgentTool):
    """Retrieve the current permitted grid state."""

    name = "get_grid_state"

    description = (
        "Retrieve the current grid state for a specified incident or region. "
        "Returns permitted telemetry and asset status. Does not control the grid."
    )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "incident_id": {
                    "type": "string",
                    "description": "Blackout Oracle incident identifier.",
                },
                "region_id": {
                    "type": "string",
                    "description": "Optional grid region identifier.",
                },
            },
            "required": ["incident_id"],
        }

    async def execute(
        self,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Retrieve grid state.

        Backend grid service integration will be connected here.
        """

        incident_id = kwargs.get("incident_id")

        if not incident_id:
            return ToolResult.failure(
                self.name,
                "incident_id is required.",
            )

        return ToolResult.ok(
            self.name,
            data={
                "status": "not_implemented",
                "incident_id": incident_id,
                "message": (
                    "Grid-state service has not been connected yet."
                ),
            },
        )


# ============================================================
# WEATHER TOOL
# ============================================================


class GetWeatherTool(BaseAgentTool):
    """Retrieve current and recent weather conditions."""

    name = "get_weather"

    description = (
        "Retrieve weather and environmental conditions relevant to a grid "
        "region, including rainfall, temperature, wind and flood risk."
    )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "incident_id": {
                    "type": "string",
                },
                "region_id": {
                    "type": "string",
                },
            },
            "required": ["incident_id"],
        }

    async def execute(
        self,
        **kwargs: Any,
    ) -> ToolResult:
        """Retrieve weather information."""

        incident_id = kwargs.get("incident_id")

        if not incident_id:
            return ToolResult.failure(
                self.name,
                "incident_id is required.",
            )

        return ToolResult.ok(
            self.name,
            data={
                "status": "not_implemented",
                "incident_id": incident_id,
            },
        )


# ============================================================
# LOAD FORECAST TOOL
# ============================================================


class RunLoadForecastTool(BaseAgentTool):
    """Run the electrical-load forecasting service."""

    name = "run_load_forecast"

    description = (
        "Forecast future electrical demand using the Blackout Oracle "
        "forecasting service."
    )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "incident_id": {
                    "type": "string",
                },
                "horizon_minutes": {
                    "type": "integer",
                    "minimum": 5,
                    "maximum": 1440,
                },
            },
            "required": ["incident_id"],
        }

    async def execute(
        self,
        **kwargs: Any,
    ) -> ToolResult:
        """Run load forecasting."""

        incident_id = kwargs.get("incident_id")

        if not incident_id:
            return ToolResult.failure(
                self.name,
                "incident_id is required.",
            )

        horizon = kwargs.get("horizon_minutes", 60)

        return ToolResult.ok(
            self.name,
            data={
                "status": "not_implemented",
                "incident_id": incident_id,
                "horizon_minutes": horizon,
            },
        )


# ============================================================
# ANOMALY DETECTION TOOL
# ============================================================


class DetectAnomaliesTool(BaseAgentTool):
    """Detect abnormal grid behavior."""

    name = "detect_anomalies"

    description = (
        "Detect abnormal behavior in grid telemetry using the anomaly "
        "detection service."
    )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "incident_id": {
                    "type": "string",
                },
            },
            "required": ["incident_id"],
        }

    async def execute(
        self,
        **kwargs: Any,
    ) -> ToolResult:
        """Run anomaly detection."""

        incident_id = kwargs.get("incident_id")

        if not incident_id:
            return ToolResult.failure(
                self.name,
                "incident_id is required.",
            )

        return ToolResult.ok(
            self.name,
            data={
                "status": "not_implemented",
                "incident_id": incident_id,
                "anomalies": [],
            },
        )


# ============================================================
# BLACKOUT RISK TOOL
# ============================================================


class CalculateBlackoutRiskTool(BaseAgentTool):
    """Calculate current blackout risk."""

    name = "calculate_blackout_risk"

    description = (
        "Calculate blackout and cascade risk using the Blackout Oracle "
        "risk engine."
    )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "incident_id": {
                    "type": "string",
                },
            },
            "required": ["incident_id"],
        }

    async def execute(
        self,
        **kwargs: Any,
    ) -> ToolResult:
        """Calculate blackout risk."""

        incident_id = kwargs.get("incident_id")

        if not incident_id:
            return ToolResult.failure(
                self.name,
                "incident_id is required.",
            )

        return ToolResult.ok(
            self.name,
            data={
                "status": "not_implemented",
                "incident_id": incident_id,
                "risk_score": None,
                "confidence": None,
            },
        )


# ============================================================
# SCENARIO GENERATION TOOL
# ============================================================


class GenerateScenariosTool(BaseAgentTool):
    """Generate hypothetical grid scenarios."""

    name = "generate_scenarios"

    description = (
        "Generate hypothetical grid scenarios for digital-twin simulation. "
        "Scenarios are not instructions for real infrastructure."
    )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "incident_id": {
                    "type": "string",
                },
                "context": {
                    "type": "object",
                },
                "max_scenarios": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                },
            },
            "required": ["incident_id", "context"],
        }

    async def execute(
        self,
        **kwargs: Any,
    ) -> ToolResult:
        """Generate hypothetical scenarios."""

        incident_id = kwargs.get("incident_id")
        context = kwargs.get("context", {})
        max_scenarios = kwargs.get("max_scenarios", 10)

        if not incident_id:
            return ToolResult.failure(
                self.name,
                "incident_id is required.",
            )

        return ToolResult.ok(
            self.name,
            data=[
                {
                    "scenario_id": "baseline",
                    "name": "Current trajectory",
                    "description": (
                        "Simulate the current grid state without intervention."
                    ),
                    "changes": [],
                    "context": context,
                }
            ][:max_scenarios],
        )


# ============================================================
# SCENARIO SIMULATION TOOL
# ============================================================


class RunScenarioTool(BaseAgentTool):
    """Run a scenario through the digital twin."""

    name = "run_scenario"

    description = (
        "Run a hypothetical grid scenario through the pandapower-based "
        "digital twin. Does not modify the real grid."
    )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "incident_id": {
                    "type": "string",
                },
                "scenario": {
                    "type": "object",
                },
            },
            "required": ["incident_id", "scenario"],
        }

    async def execute(
        self,
        **kwargs: Any,
    ) -> ToolResult:
        """Run a digital-twin simulation."""

        incident_id = kwargs.get("incident_id")
        scenario = kwargs.get("scenario")

        if not incident_id:
            return ToolResult.failure(
                self.name,
                "incident_id is required.",
            )

        if not scenario:
            return ToolResult.failure(
                self.name,
                "scenario is required.",
            )

        return ToolResult.ok(
            self.name,
            data={
                "status": "not_implemented",
                "incident_id": incident_id,
                "scenario_id": scenario.get("scenario_id"),
                "simulation": None,
            },
        )


# ============================================================
# VERIFICATION TOOL
# ============================================================


class VerifyScenarioTool(BaseAgentTool):
    """Verify a simulation result."""

    name = "verify_scenario"

    description = (
        "Verify a simulated grid scenario against configured electrical "
        "and safety constraints."
    )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "incident_id": {
                    "type": "string",
                },
                "scenario": {
                    "type": "object",
                },
                "simulation": {
                    "type": "object",
                },
            },
            "required": [
                "incident_id",
                "scenario",
                "simulation",
            ],
        }

    async def execute(
        self,
        **kwargs: Any,
    ) -> ToolResult:
        """Verify a simulation result."""

        incident_id = kwargs.get("incident_id")
        scenario = kwargs.get("scenario")
        simulation = kwargs.get("simulation")

        if not incident_id:
            return ToolResult.failure(
                self.name,
                "incident_id is required.",
            )

        if not scenario:
            return ToolResult.failure(
                self.name,
                "scenario is required.",
            )

        if simulation is None:
            return ToolResult.failure(
                self.name,
                "simulation result is required.",
            )

        return ToolResult.ok(
            self.name,
            data={
                "status": "not_implemented",
                "verified": False,
                "reason": (
                    "Simulation verification service has not been connected yet."
                ),
            },
        )


# ============================================================
# SCENARIO RANKING TOOL
# ============================================================


class RankScenariosTool(BaseAgentTool):
    """Rank verified scenarios."""

    name = "rank_scenarios"

    description = (
        "Rank scenarios using verified simulation results, risk reduction "
        "and configured optimization criteria."
    )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "incident_id": {
                    "type": "string",
                },
                "scenarios": {
                    "type": "array",
                },
            },
            "required": ["incident_id", "scenarios"],
        }

    async def execute(
        self,
        **kwargs: Any,
    ) -> ToolResult:
        """Rank verified scenarios."""

        incident_id = kwargs.get("incident_id")
        scenarios = kwargs.get("scenarios", [])

        if not incident_id:
            return ToolResult.failure(
                self.name,
                "incident_id is required.",
            )

        if not scenarios:
            return ToolResult.failure(
                self.name,
                "At least one scenario is required.",
            )

        return ToolResult.ok(
            self.name,
            data={
                "status": "not_implemented",
                "incident_id": incident_id,
                "recommended_scenario": None,
                "ranked_scenarios": [],
            },
        )


# ============================================================
# TOOL FACTORY
# ============================================================


def create_default_tool_registry() -> AgentToolRegistry:
    """
    Create the default safe tool registry.

    Only explicitly approved analytical tools are registered.

    No infrastructure-control tools are included.
    """

    registry = AgentToolRegistry()

    registry.register(GetGridStateTool())
    registry.register(GetWeatherTool())
    registry.register(RunLoadForecastTool())
    registry.register(DetectAnomaliesTool())
    registry.register(CalculateBlackoutRiskTool())
    registry.register(GenerateScenariosTool())
    registry.register(RunScenarioTool())
    registry.register(VerifyScenarioTool())
    registry.register(RankScenariosTool())

    return registry


# ============================================================
# DEFAULT REGISTRY
# ============================================================

default_tool_registry = create_default_tool_registry()


__all__ = [
    "ToolResult",
    "BaseAgentTool",
    "FunctionTool",
    "AgentToolRegistry",
    "GetGridStateTool",
    "GetWeatherTool",
    "RunLoadForecastTool",
    "DetectAnomaliesTool",
    "CalculateBlackoutRiskTool",
    "GenerateScenariosTool",
    "RunScenarioTool",
    "VerifyScenarioTool",
    "RankScenariosTool",
    "create_default_tool_registry",
    "default_tool_registry",
]