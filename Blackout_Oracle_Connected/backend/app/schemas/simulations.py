"""
Blackout Oracle - Simulation Schemas.

Pydantic schemas for grid simulations, contingency analysis,
cascading-failure scenarios, simulation results, and simulation
lifecycle management.

These schemas are intentionally independent of SQLAlchemy models.
They define the application/API contract for the simulation layer.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# ENUMS
# ============================================================


class SimulationType(str, Enum):
    """Types of simulations supported by Blackout Oracle."""

    POWER_FLOW = "power_flow"
    CONTINGENCY = "contingency"
    CASCADE = "cascade"
    BLACKOUT = "blackout"
    FAILURE = "failure"
    LOAD_FLOW = "load_flow"
    VOLTAGE_STABILITY = "voltage_stability"
    FREQUENCY_STABILITY = "frequency_stability"
    WEATHER_IMPACT = "weather_impact"
    CUSTOM = "custom"


class SimulationStatus(str, Enum):
    """Lifecycle status of a simulation."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class SimulationPriority(str, Enum):
    """Execution priority of a simulation."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class SimulationResultStatus(str, Enum):
    """Overall interpretation of a simulation result."""

    NORMAL = "normal"
    WARNING = "warning"
    UNSAFE = "unsafe"
    CRITICAL = "critical"
    INCONCLUSIVE = "inconclusive"


# ============================================================
# SCENARIO COMPONENTS
# ============================================================


class SimulationAssetChange(BaseModel):
    """
    Describes an asset state change introduced by a simulation.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    asset_id: int = Field(
        ...,
        ge=1,
        description="Asset affected by the scenario.",
    )

    status: str | None = Field(
        default=None,
        max_length=100,
        description="Simulated asset status.",
    )

    loading_percent: float | None = Field(
        default=None,
        ge=0.0,
        description="Simulated loading percentage.",
    )

    voltage_pu: float | None = Field(
        default=None,
        gt=0.0,
        description="Simulated voltage in per-unit.",
    )

    power_mw: float | None = Field(
        default=None,
        description="Simulated active power in MW.",
    )

    reactive_power_mvar: float | None = Field(
        default=None,
        description="Simulated reactive power in MVAr.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class SimulationContingency(BaseModel):
    """
    Represents an outage or contingency introduced into a
    simulation scenario.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    asset_id: int = Field(
        ...,
        ge=1,
    )

    asset_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    forced_outage: bool = True

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# BASE SIMULATION
# ============================================================


class SimulationBase(BaseModel):
    """
    Common fields shared by simulation schemas.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable simulation name.",
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    simulation_type: SimulationType = Field(
        ...,
        description="Simulation algorithm/category.",
    )

    priority: SimulationPriority = Field(
        default=SimulationPriority.NORMAL,
    )

    region: str | None = Field(
        default=None,
        max_length=255,
    )

    substation_id: int | None = Field(
        default=None,
        ge=1,
    )

    asset_id: int | None = Field(
        default=None,
        ge=1,
    )

    duration_seconds: float | None = Field(
        default=None,
        ge=0.0,
        description="Requested simulation duration.",
    )

    timestep_seconds: float | None = Field(
        default=None,
        gt=0.0,
        description="Simulation time step.",
    )

    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Simulation-specific parameters.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# SIMULATION CREATE
# ============================================================


class SimulationCreate(SimulationBase):
    """
    Schema used to create a new simulation.
    """

    contingencies: list[SimulationContingency] = Field(
        default_factory=list,
        description="Contingencies to apply during the simulation.",
    )

    asset_changes: list[SimulationAssetChange] = Field(
        default_factory=list,
        description="Explicit simulated asset changes.",
    )

    requested_by: str | None = Field(
        default=None,
        max_length=255,
    )


# ============================================================
# SIMULATION UPDATE
# ============================================================


class SimulationUpdate(BaseModel):
    """
    Schema used for partial updates to a simulation.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    priority: SimulationPriority | None = None

    status: SimulationStatus | None = None

    parameters: dict[str, Any] | None = None

    metadata: dict[str, Any] | None = None


# ============================================================
# SIMULATION REQUEST
# ============================================================


class SimulationRequest(BaseModel):
    """
    Request payload for executing a simulation.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    simulation_type: SimulationType

    region: str | None = Field(
        default=None,
        max_length=255,
    )

    substation_id: int | None = Field(
        default=None,
        ge=1,
    )

    asset_id: int | None = Field(
        default=None,
        ge=1,
    )

    contingencies: list[SimulationContingency] = Field(
        default_factory=list,
    )

    asset_changes: list[SimulationAssetChange] = Field(
        default_factory=list,
    )

    parameters: dict[str, Any] = Field(
        default_factory=dict,
    )

    duration_seconds: float | None = Field(
        default=None,
        ge=0.0,
    )

    timestep_seconds: float | None = Field(
        default=None,
        gt=0.0,
    )


# ============================================================
# SIMULATION RESPONSE
# ============================================================


class SimulationResponse(SimulationBase):
    """
    API response representing a stored simulation.
    """

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        extra="forbid",
    )

    id: int = Field(
        ...,
        ge=1,
    )

    status: SimulationStatus = SimulationStatus.QUEUED

    requested_by: str | None = None

    created_at: datetime

    started_at: datetime | None = None

    completed_at: datetime | None = None

    failed_at: datetime | None = None

    error_message: str | None = None

    execution_time_seconds: float | None = Field(
        default=None,
        ge=0.0,
    )


# ============================================================
# SIMULATION FILTER
# ============================================================


class SimulationFilter(BaseModel):
    """
    Filters for querying simulations.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    simulation_type: SimulationType | None = None

    status: SimulationStatus | None = None

    priority: SimulationPriority | None = None

    region: str | None = Field(
        default=None,
        max_length=255,
    )

    substation_id: int | None = Field(
        default=None,
        ge=1,
    )

    asset_id: int | None = Field(
        default=None,
        ge=1,
    )

    requested_by: str | None = Field(
        default=None,
        max_length=255,
    )

    start_time: datetime | None = None

    end_time: datetime | None = None

    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# POWER FLOW RESULT
# ============================================================


class BusResult(BaseModel):
    """
    Simulated electrical bus result.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    bus_id: int = Field(
        ...,
        ge=1,
    )

    voltage_pu: float = Field(
        ...,
        gt=0.0,
    )

    voltage_angle_deg: float | None = None

    active_power_mw: float | None = None

    reactive_power_mvar: float | None = None

    within_limits: bool = True


class LineResult(BaseModel):
    """
    Simulated transmission-line result.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    line_id: int = Field(
        ...,
        ge=1,
    )

    power_flow_mw: float | None = None

    reactive_flow_mvar: float | None = None

    loading_percent: float = Field(
        ...,
        ge=0.0,
    )

    current_a: float | None = Field(
        default=None,
        ge=0.0,
    )

    within_limits: bool = True


class TransformerResult(BaseModel):
    """
    Simulated transformer result.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    transformer_id: int = Field(
        ...,
        ge=1,
    )

    loading_percent: float = Field(
        ...,
        ge=0.0,
    )

    voltage_pu: float | None = Field(
        default=None,
        gt=0.0,
    )

    temperature_c: float | None = None

    within_limits: bool = True


# ============================================================
# CASCADE RESULT
# ============================================================


class CascadeEvent(BaseModel):
    """
    One step in a simulated cascading-failure sequence.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    step: int = Field(
        ...,
        ge=0,
    )

    timestamp: datetime | None = None

    asset_id: int = Field(
        ...,
        ge=1,
    )

    asset_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    reason: str | None = Field(
        default=None,
        max_length=2000,
    )

    loading_percent: float | None = Field(
        default=None,
        ge=0.0,
    )

    severity: str | None = Field(
        default=None,
        max_length=50,
    )


class CascadeSimulationResult(BaseModel):
    """
    Result of a cascading-failure simulation.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    cascade_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    affected_assets: list[int] = Field(
        default_factory=list,
    )

    affected_substations: list[int] = Field(
        default_factory=list,
    )

    failed_assets: list[int] = Field(
        default_factory=list,
    )

    propagation_depth: int = Field(
        default=0,
        ge=0,
    )

    total_load_lost_mw: float = Field(
        default=0.0,
        ge=0.0,
    )

    events: list[CascadeEvent] = Field(
        default_factory=list,
    )


# ============================================================
# SIMULATION RESULT
# ============================================================


class SimulationResult(BaseModel):
    """
    Generic result produced by a simulation.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    simulation_id: int = Field(
        ...,
        ge=1,
    )

    status: SimulationResultStatus

    success: bool

    risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    blackout_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    cascade_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    buses: list[BusResult] = Field(
        default_factory=list,
    )

    lines: list[LineResult] = Field(
        default_factory=list,
    )

    transformers: list[TransformerResult] = Field(
        default_factory=list,
    )

    cascade: CascadeSimulationResult | None = None

    warnings: list[str] = Field(
        default_factory=list,
    )

    violations: list[str] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )

    metrics: dict[str, float] = Field(
        default_factory=dict,
    )

    execution_time_seconds: float | None = Field(
        default=None,
        ge=0.0,
    )

    completed_at: datetime | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# SIMULATION SUMMARY
# ============================================================


class SimulationSummary(BaseModel):
    """
    High-level summary of a simulation result.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    simulation_id: int = Field(
        ...,
        ge=1,
    )

    simulation_type: SimulationType

    status: SimulationResultStatus

    risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    blackout_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    cascade_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    affected_assets: int = Field(
        default=0,
        ge=0,
    )

    failed_assets: int = Field(
        default=0,
        ge=0,
    )

    affected_load_mw: float = Field(
        default=0.0,
        ge=0.0,
    )

    violations: int = Field(
        default=0,
        ge=0,
    )

    warnings: int = Field(
        default=0,
        ge=0,
    )

    completed_at: datetime | None = None


# ============================================================
# SIMULATION LIST RESPONSE
# ============================================================


class SimulationListResponse(BaseModel):
    """
    Paginated collection of simulations.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[SimulationResponse] = Field(
        default_factory=list,
    )

    total: int = Field(
        default=0,
        ge=0,
    )

    limit: int = Field(
        default=100,
        ge=1,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# SIMULATION EVENT
# ============================================================


class SimulationEvent(BaseModel):
    """
    Event emitted during simulation lifecycle processing.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    simulation_id: int = Field(
        ...,
        ge=1,
    )

    event_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    status: SimulationStatus

    timestamp: datetime

    message: str | None = Field(
        default=None,
        max_length=5000,
    )

    progress_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# SIMULATION CONFIGURATION
# ============================================================


class SimulationConfiguration(BaseModel):
    """
    Configuration used by a simulation engine.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    solver: str = Field(
        default="default",
        min_length=1,
        max_length=100,
    )

    max_iterations: int = Field(
        default=100,
        ge=1,
    )

    convergence_tolerance: float = Field(
        default=1e-6,
        gt=0.0,
    )

    timestep_seconds: float = Field(
        default=1.0,
        gt=0.0,
    )

    duration_seconds: float = Field(
        default=60.0,
        ge=0.0,
    )

    enable_cascade_analysis: bool = True

    enable_blackout_analysis: bool = True

    parameters: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "SimulationType",
    "SimulationStatus",
    "SimulationPriority",
    "SimulationResultStatus",
    "SimulationAssetChange",
    "SimulationContingency",
    "SimulationBase",
    "SimulationCreate",
    "SimulationUpdate",
    "SimulationRequest",
    "SimulationResponse",
    "SimulationFilter",
    "BusResult",
    "LineResult",
    "TransformerResult",
    "CascadeEvent",
    "CascadeSimulationResult",
    "SimulationResult",
    "SimulationSummary",
    "SimulationListResponse",
    "SimulationEvent",
    "SimulationConfiguration",
]