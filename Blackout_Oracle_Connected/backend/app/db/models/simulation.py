"""
Blackout Oracle - Simulation Database Model.

Stores simulation runs performed by the Blackout Oracle simulation
engine.

A simulation evaluates a hypothetical grid scenario against a baseline
grid state.

Simulations may evaluate:

- Generator failures
- Substation failures
- Transformer failures
- Feeder failures
- Transmission failures
- Demand surges
- Generation shortages
- Voltage instability
- Frequency instability
- Extreme weather
- Flood conditions
- Storm conditions
- Multiple simultaneous failures
- Cascading failures
- Proposed mitigation strategies

The simulation system can be used to determine:

- Whether the grid remains stable
- Whether overloads occur
- Whether voltage limits are violated
- Whether frequency limits are violated
- How much load is lost
- How much generation is lost
- How many customers may be affected
- Whether a mitigation strategy reduces risk

IMPORTANT
---------

This model stores analytical simulation results.

It does NOT directly control physical electrical-grid equipment.
"""


from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# ============================================================
# ENUMS
# ============================================================


class SimulationType:
    """
    Type of simulation being performed.
    """

    CONTINGENCY = "contingency"
    BASELINE = "baseline"
    FAILURE = "failure"
    CASCADING_FAILURE = "cascading_failure"
    BLACKOUT = "blackout"

    LOAD_FLOW = "load_flow"
    POWER_FLOW = "power_flow"

    VOLTAGE_STABILITY = "voltage_stability"
    FREQUENCY_STABILITY = "frequency_stability"
    TRANSIENT_STABILITY = "transient_stability"

    WEATHER_IMPACT = "weather_impact"
    FLOOD_IMPACT = "flood_impact"
    STORM_IMPACT = "storm_impact"

    MITIGATION = "mitigation"
    RECOVERY = "recovery"

    CUSTOM = "custom"


class SimulationStatus:
    """
    Lifecycle state of a simulation run.
    """

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class SimulationOutcome:
    """
    High-level result of a simulation.
    """

    UNKNOWN = "unknown"
    STABLE = "stable"
    DEGRADED = "degraded"
    UNSTABLE = "unstable"

    BLACKOUT = "blackout"
    PARTIAL_BLACKOUT = "partial_blackout"
    CASCADING_FAILURE = "cascading_failure"

    MITIGATION_SUCCESS = "mitigation_success"
    MITIGATION_FAILURE = "mitigation_failure"


class SimulationSource:
    """
    Component that requested the simulation.
    """

    RISK_ENGINE = "risk_engine"
    PREDICTION_ENGINE = "prediction_engine"
    AI_AGENT = "ai_agent"
    RECOMMENDATION_ENGINE = "recommendation_engine"
    OPERATOR = "operator"
    API = "api"
    AUTOMATED_RULE = "automated_rule"
    OTHER = "other"


class SimulationValidationStatus:
    """
    Validation state of simulation results.
    """

    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


# ============================================================
# SIMULATION MODEL
# ============================================================


class Simulation(Base):
    """
    SQLAlchemy model representing an executed grid simulation.
    """

    __tablename__ = "simulations"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"SIM-{uuid4().hex[:12].upper()}"
        ),
    )

    # ========================================================
    # IDENTIFICATION
    # ========================================================

    name: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
        index=True,
    )

    simulation_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=SimulationStatus.CREATED,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default=SimulationSource.OTHER,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # LOCATION
    # ========================================================

    region_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    region_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    # ========================================================
    # TARGET GRID ELEMENT
    # ========================================================

    asset_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    substation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    feeder_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    bus_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    generator_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    load_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # ========================================================
    # RELATED RECORDS
    # ========================================================

    scenario_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    prediction_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    recommendation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    incident_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # ========================================================
    # BASELINE CONDITIONS
    # ========================================================

    baseline_demand_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    baseline_generation_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    baseline_available_generation_mw: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    baseline_reserve_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    baseline_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    baseline_frequency_hz: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    baseline_loading_percent: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # SIMULATION INPUTS
    # ========================================================

    demand_change_mw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    generation_change_mw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    capacity_removed_mw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    capacity_added_mw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    failed_assets_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failed_assets_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # WEATHER INPUTS
    # ========================================================

    weather_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rainfall_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    wind_speed_kmh: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    flood_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    storm_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # SIMULATION ENGINE
    # ========================================================

    engine_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    engine_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    simulation_method: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    solver_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    solver_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ========================================================
    # EXECUTION
    # ========================================================

    execution_time_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    iteration_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    convergence_achieved: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    convergence_error: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # SIMULATION OUTCOME
    # ========================================================

    outcome: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=SimulationOutcome.UNKNOWN,
        index=True,
    )

    result_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # RESULTING GRID CONDITIONS
    # ========================================================

    resulting_demand_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    resulting_generation_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    resulting_available_generation_mw: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    resulting_reserve_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    resulting_load_generation_margin_mw: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # VOLTAGE RESULTS
    # ========================================================

    minimum_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    maximum_voltage_kv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    voltage_violations: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ========================================================
    # FREQUENCY RESULTS
    # ========================================================

    minimum_frequency_hz: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    maximum_frequency_hz: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    frequency_violations: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ========================================================
    # LOADING RESULTS
    # ========================================================

    maximum_loading_percent: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    overloaded_assets_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    critical_overloads_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ========================================================
    # POWER LOSS RESULTS
    # ========================================================

    load_loss_mw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    generation_loss_mw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    transmission_loss_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # CUSTOMER / POPULATION IMPACT
    # ========================================================

    affected_customers: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    affected_population: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    affected_regions_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    affected_assets_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ========================================================
    # BLACKOUT / CASCADE RESULTS
    # ========================================================

    blackout_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    partial_blackout_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    cascade_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    cascade_depth: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    cascade_events_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    blackout_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    cascade_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # STABILITY RESULTS
    # ========================================================

    stability_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    stability_margin: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # MITIGATION RESULTS
    # ========================================================

    mitigation_applied: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    mitigation_successful: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    risk_before_mitigation: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    risk_after_mitigation: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    risk_reduction_percent: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    validation_status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=SimulationValidationStatus.PENDING,
        index=True,
    )

    validation_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    validation_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    validation_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # AI ANALYSIS
    # ========================================================

    ai_analyzed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    ai_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ai_model_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    ai_model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    ai_interpretation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # RAW INPUT / OUTPUT DATA
    # ========================================================

    input_parameters_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    output_results_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    topology_snapshot_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # CORRELATION
    # ========================================================

    request_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    correlation_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    # ========================================================
    # ADDITIONAL DATA
    # ========================================================

    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        index=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        onupdate=lambda: datetime.now(
            timezone.utc
        ),
    )

    # ========================================================
    # DATABASE INDEXES
    # ========================================================

    __table_args__ = (
        Index(
            "ix_simulations_region_type",
            "region_id",
            "simulation_type",
        ),
        Index(
            "ix_simulations_region_created",
            "region_id",
            "created_at",
        ),
        Index(
            "ix_simulations_status",
            "status",
            "created_at",
        ),
        Index(
            "ix_simulations_outcome",
            "outcome",
            "status",
        ),
        Index(
            "ix_simulations_scenario",
            "scenario_id",
        ),
        Index(
            "ix_simulations_prediction",
            "prediction_id",
        ),
        Index(
            "ix_simulations_recommendation",
            "recommendation_id",
        ),
        Index(
            "ix_simulations_blackout_cascade",
            "blackout_detected",
            "cascade_detected",
        ),
        Index(
            "ix_simulations_validation",
            "validation_status",
            "validation_completed",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<Simulation("
            f"id='{self.id}', "
            f"name='{self.name}', "
            f"type='{self.simulation_type}', "
            f"status='{self.status}', "
            f"outcome='{self.outcome}'"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Simulation",
    "SimulationType",
    "SimulationStatus",
    "SimulationOutcome",
    "SimulationSource",
    "SimulationValidationStatus",
]