"""
Blackout Oracle - Simulation API Routes.

This module exposes HTTP endpoints for running and inspecting hypothetical
power-grid simulations.

The simulation layer is a DIGITAL TWIN.

It operates on a software representation of the electrical network and
does not control or modify real-world grid infrastructure.

Typical flow:

    Current Grid State
           |
           v
    Scenario Generation
           |
           v
    Digital Twin
           |
           v
    Power-System Simulation
           |
           v
    Simulation Result
           |
           v
    Verification
           |
           v
    Recommendation

IMPORTANT SAFETY RULES
----------------------

Simulation endpoints must never:

- Connect directly to SCADA control channels.
- Operate breakers.
- Modify real substations.
- Control generators.
- Change real grid settings.
- Execute arbitrary infrastructure commands.

The initial implementation uses an in-memory development store.
The actual pandapower simulation engine will be connected through the
simulation service layer later.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/simulations",
    tags=["Simulations"],
)


# ============================================================
# ENUMS
# ============================================================


class SimulationStatus(str, Enum):
    """Lifecycle status of a simulation."""

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SimulationType(str, Enum):
    """Types of power-system simulations."""

    POWER_FLOW = "power_flow"
    TIME_SERIES = "time_series"
    CONTINGENCY = "contingency"
    CASCADE = "cascade"
    VOLTAGE_STABILITY = "voltage_stability"
    FREQUENCY_STABILITY = "frequency_stability"
    BLACKOUT = "blackout"
    CUSTOM = "custom"


# ============================================================
# SCENARIO SCHEMAS
# ============================================================


class ScenarioChange(BaseModel):
    """
    A hypothetical change applied to the digital twin.

    Examples:

    - Simulate a transmission line outage.
    - Simulate transformer derating.
    - Simulate increased demand.
    - Simulate generator loss.
    - Simulate weather-related asset unavailability.

    These changes apply ONLY to the simulation model.
    """

    asset_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    parameter: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    value: Any = None

    description: str | None = Field(
        default=None,
        max_length=1000,
    )


class ScenarioCreate(BaseModel):
    """Request model for creating a hypothetical scenario."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )

    description: str = Field(
        default="",
        max_length=5000,
    )

    simulation_type: SimulationType = (
        SimulationType.POWER_FLOW
    )

    changes: list[ScenarioChange] = Field(
        default_factory=list,
    )

    parameters: dict[str, Any] = Field(
        default_factory=dict,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class ScenarioResponse(BaseModel):
    """Response model representing a scenario."""

    id: str

    name: str

    description: str

    simulation_type: SimulationType

    changes: list[ScenarioChange]

    parameters: dict[str, Any]

    metadata: dict[str, Any]

    created_at: datetime


# ============================================================
# SIMULATION REQUEST/RESPONSE
# ============================================================


class SimulationCreate(BaseModel):
    """
    Request model for creating a simulation.

    Either an existing scenario_id or an inline scenario may be supplied.
    """

    incident_id: str | None = Field(
        default=None,
        max_length=100,
        description="Associated Blackout Oracle incident.",
    )

    scenario_id: str | None = Field(
        default=None,
        max_length=100,
        description="Existing scenario ID.",
    )

    scenario: ScenarioCreate | None = Field(
        default=None,
        description="Inline scenario definition.",
    )

    simulation_type: SimulationType = (
        SimulationType.POWER_FLOW
    )

    time_horizon_minutes: int = Field(
        default=60,
        ge=1,
        le=10080,
        description="Simulation horizon in minutes.",
    )

    time_step_seconds: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Simulation timestep in seconds.",
    )

    parameters: dict[str, Any] = Field(
        default_factory=dict,
    )


class SimulationResponse(BaseModel):
    """Complete simulation response."""

    id: str

    incident_id: str | None = None

    scenario_id: str

    simulation_type: SimulationType

    status: SimulationStatus

    time_horizon_minutes: int

    time_step_seconds: int

    started_at: datetime | None = None

    completed_at: datetime | None = None

    created_at: datetime

    results: dict[str, Any] | None = None

    summary: dict[str, Any] = Field(
        default_factory=dict
    )

    warnings: list[str] = Field(
        default_factory=list
    )

    errors: list[str] = Field(
        default_factory=list
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# DEVELOPMENT STORES
# ============================================================

# These are temporary development stores.
#
# Production implementation will use the database and simulation service.

_SCENARIOS: dict[str, ScenarioResponse] = {}

_SIMULATIONS: dict[str, SimulationResponse] = {}


# ============================================================
# SCENARIO CREATION
# ============================================================


@router.post(
    "/scenarios",
    response_model=ScenarioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scenario(
    scenario: ScenarioCreate,
) -> ScenarioResponse:
    """
    Create a hypothetical digital-twin scenario.

    This creates only a software scenario.

    It does NOT modify any real-world electrical equipment.
    """

    scenario_id = (
        f"SCN-{uuid4().hex[:12].upper()}"
    )

    now = datetime.now(timezone.utc)

    response = ScenarioResponse(
        id=scenario_id,
        name=scenario.name,
        description=scenario.description,
        simulation_type=scenario.simulation_type,
        changes=scenario.changes,
        parameters=scenario.parameters,
        metadata=scenario.metadata,
        created_at=now,
    )

    _SCENARIOS[
        scenario_id
    ] = response

    return response


# ============================================================
# LIST SCENARIOS
# ============================================================


@router.get(
    "/scenarios",
    response_model=list[ScenarioResponse],
)
async def list_scenarios(
    simulation_type: SimulationType | None = Query(
        default=None,
        description="Filter by simulation type.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
) -> list[ScenarioResponse]:
    """
    List available simulation scenarios.
    """

    scenarios = list(
        _SCENARIOS.values()
    )

    if simulation_type is not None:
        scenarios = [
            scenario
            for scenario in scenarios
            if scenario.simulation_type
            == simulation_type
        ]

    scenarios.sort(
        key=lambda scenario: scenario.created_at,
        reverse=True,
    )

    return scenarios[:limit]


# ============================================================
# GET SCENARIO
# ============================================================


@router.get(
    "/scenarios/{scenario_id}",
    response_model=ScenarioResponse,
)
async def get_scenario(
    scenario_id: str,
) -> ScenarioResponse:
    """
    Retrieve a scenario by ID.
    """

    scenario = _SCENARIOS.get(
        scenario_id
    )

    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Scenario '{scenario_id}' was not found."
            ),
        )

    return scenario


# ============================================================
# CREATE SIMULATION
# ============================================================


@router.post(
    "",
    response_model=SimulationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_simulation(
    request: SimulationCreate,
) -> SimulationResponse:
    """
    Create and execute a digital-twin simulation.

    CURRENT DEVELOPMENT BEHAVIOR:

    The simulation is recorded but the real pandapower engine is not
    connected yet.

    PRODUCTION BEHAVIOR:

        1. Load the approved network model.
        2. Load the relevant baseline state.
        3. Apply hypothetical scenario changes.
        4. Run pandapower calculations.
        5. Evaluate electrical constraints.
        6. Save the simulation results.
        7. Pass the result to the verification service.

    No real infrastructure is modified.
    """

    scenario_id = request.scenario_id

    # --------------------------------------------------------
    # Use existing scenario
    # --------------------------------------------------------

    if scenario_id is not None:

        scenario = _SCENARIOS.get(
            scenario_id
        )

        if scenario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Scenario '{scenario_id}' was not found."
                ),
            )

    # --------------------------------------------------------
    # Create inline scenario
    # --------------------------------------------------------

    elif request.scenario is not None:

        scenario_id = (
            f"SCN-{uuid4().hex[:12].upper()}"
        )

        scenario = ScenarioResponse(
            id=scenario_id,
            name=request.scenario.name,
            description=request.scenario.description,
            simulation_type=request.scenario.simulation_type,
            changes=request.scenario.changes,
            parameters=request.scenario.parameters,
            metadata=request.scenario.metadata,
            created_at=datetime.now(timezone.utc),
        )

        _SCENARIOS[
            scenario_id
        ] = scenario

    else:

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Either scenario_id or scenario must be provided."
            ),
        )

    simulation_id = (
        f"SIM-{uuid4().hex[:12].upper()}"
    )

    now = datetime.now(timezone.utc)

    response = SimulationResponse(
        id=simulation_id,
        incident_id=request.incident_id,
        scenario_id=scenario_id,
        simulation_type=request.simulation_type,
        status=SimulationStatus.CREATED,
        time_horizon_minutes=(
            request.time_horizon_minutes
        ),
        time_step_seconds=(
            request.time_step_seconds
        ),
        created_at=now,
        metadata={
            "development_mode": True,
            "simulation_engine_connected": False,
            "parameters": request.parameters,
        },
    )

    _SIMULATIONS[
        simulation_id
    ] = response

    return response


# ============================================================
# RUN SIMULATION
# ============================================================


@router.post(
    "/{simulation_id}/run",
    response_model=SimulationResponse,
)
async def run_simulation(
    simulation_id: str,
) -> SimulationResponse:
    """
    Run a previously created simulation.

    The actual simulation engine will eventually be called from here.

    The production engine should run entirely against the digital twin.
    """

    simulation = _SIMULATIONS.get(
        simulation_id
    )

    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Simulation '{simulation_id}' was not found."
            ),
        )

    if simulation.status == SimulationStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Simulation is already running.",
        )

    if simulation.status == SimulationStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Simulation has already completed.",
        )

    now = datetime.now(timezone.utc)

    simulation.status = SimulationStatus.RUNNING
    simulation.started_at = now

    # --------------------------------------------------------
    # TODO:
    # Connect to the simulation service here.
    #
    # Example future flow:
    #
    # result = await simulation_service.run(
    #     scenario_id=simulation.scenario_id,
    #     simulation_type=simulation.simulation_type,
    #     horizon=simulation.time_horizon_minutes,
    #     timestep=simulation.time_step_seconds,
    # )
    # --------------------------------------------------------

    simulation.status = SimulationStatus.FAILED
    simulation.completed_at = (
        datetime.now(timezone.utc)
    )

    simulation.errors = [
        (
            "Simulation engine is not connected yet. "
            "No electrical simulation was executed."
        )
    ]

    return simulation


# ============================================================
# GET SIMULATION
# ============================================================


@router.get(
    "/{simulation_id}",
    response_model=SimulationResponse,
)
async def get_simulation(
    simulation_id: str,
) -> SimulationResponse:
    """
    Retrieve a simulation by ID.
    """

    simulation = _SIMULATIONS.get(
        simulation_id
    )

    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Simulation '{simulation_id}' was not found."
            ),
        )

    return simulation


# ============================================================
# LIST SIMULATIONS
# ============================================================


@router.get(
    "",
    response_model=list[SimulationResponse],
)
async def list_simulations(
    incident_id: str | None = Query(
        default=None,
        description="Filter by incident.",
    ),
    simulation_status: SimulationStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by simulation status.",
    ),
    simulation_type: SimulationType | None = Query(
        default=None,
        description="Filter by simulation type.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
) -> list[SimulationResponse]:
    """
    List simulations using optional filters.
    """

    simulations = list(
        _SIMULATIONS.values()
    )

    if incident_id is not None:
        simulations = [
            simulation
            for simulation in simulations
            if simulation.incident_id
            == incident_id
        ]

    if simulation_status is not None:
        simulations = [
            simulation
            for simulation in simulations
            if simulation.status
            == simulation_status
        ]

    if simulation_type is not None:
        simulations = [
            simulation
            for simulation in simulations
            if simulation.simulation_type
            == simulation_type
        ]

    simulations.sort(
        key=lambda simulation: simulation.created_at,
        reverse=True,
    )

    return simulations[:limit]


# ============================================================
# SIMULATION RESULT
# ============================================================


@router.get(
    "/{simulation_id}/result",
    response_model=dict[str, Any],
)
async def get_simulation_result(
    simulation_id: str,
) -> dict[str, Any]:
    """
    Return the detailed simulation result.

    The result will eventually contain electrical metrics such as:

    - Bus voltages
    - Line loading
    - Transformer loading
    - Generator output
    - Power losses
    - Voltage violations
    - Thermal violations
    - Islanding
    - Cascading-failure indicators
    """

    simulation = _SIMULATIONS.get(
        simulation_id
    )

    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Simulation '{simulation_id}' was not found."
            ),
        )

    if simulation.status != SimulationStatus.COMPLETED:
        return {
            "simulation_id": simulation_id,
            "status": simulation.status.value,
            "result": None,
            "message": (
                "Simulation does not have a completed result."
            ),
        }

    return {
        "simulation_id": simulation_id,
        "status": simulation.status.value,
        "result": simulation.results,
        "summary": simulation.summary,
        "warnings": simulation.warnings,
        "errors": simulation.errors,
    }


# ============================================================
# CANCEL SIMULATION
# ============================================================


@router.post(
    "/{simulation_id}/cancel",
    response_model=SimulationResponse,
)
async def cancel_simulation(
    simulation_id: str,
) -> SimulationResponse:
    """
    Cancel a queued/running simulation.

    This affects only the software simulation job.
    """

    simulation = _SIMULATIONS.get(
        simulation_id
    )

    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Simulation '{simulation_id}' was not found."
            ),
        )

    if simulation.status in {
        SimulationStatus.COMPLETED,
        SimulationStatus.FAILED,
        SimulationStatus.CANCELLED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Simulation cannot be cancelled from status "
                f"'{simulation.status.value}'."
            ),
        )

    simulation.status = (
        SimulationStatus.CANCELLED
    )

    simulation.completed_at = (
        datetime.now(timezone.utc)
    )

    return simulation


# ============================================================
# SIMULATION SUMMARY
# ============================================================


@router.get(
    "/summary/counts",
    response_model=dict[str, int],
)
async def simulation_summary() -> dict[str, int]:
    """
    Return simulation counts grouped by status.
    """

    summary: dict[str, int] = {
        "total": len(_SIMULATIONS),
    }

    for simulation_status in SimulationStatus:
        summary[
            simulation_status.value
        ] = 0

    for simulation in _SIMULATIONS.values():
        summary[
            simulation.status.value
        ] += 1

    return summary


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "router",
    "SimulationStatus",
    "SimulationType",
    "ScenarioChange",
    "ScenarioCreate",
    "ScenarioResponse",
    "SimulationCreate",
    "SimulationResponse",
]