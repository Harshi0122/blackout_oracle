"""
Blackout Oracle - Scenario Database Model.

Represents hypothetical electrical-grid conditions used for simulation,
contingency analysis, and mitigation planning.

A scenario can represent:

- A generator failure
- A transformer failure
- A substation outage
- A feeder outage
- A transmission-line failure
- A demand surge
- A generation shortage
- Extreme weather conditions
- Multiple simultaneous failures
- A potential cascading failure
- A proposed mitigation strategy

Scenarios are used by the simulation engine to answer questions such
as:

    "What happens if this generator fails?"

    "What happens if this feeder becomes unavailable?"

    "What happens if demand increases by 15%?"

    "Does this mitigation strategy reduce blackout risk?"

IMPORTANT
---------

A scenario is a hypothetical analytical state.

It does NOT represent a real electrical-grid command and does NOT
directly control physical grid equipment.
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


class ScenarioType:
    """
    Type of hypothetical scenario.
    """

    BASELINE = "baseline"

    ASSET_FAILURE = "asset_failure"
    SUBSTATION_FAILURE = "substation_failure"
    TRANSFORMER_FAILURE = "transformer_failure"
    FEEDER_FAILURE = "feeder_failure"
    TRANSMISSION_FAILURE = "transmission_failure"
    GENERATOR_FAILURE = "generator_failure"

    DEMAND_SURGE = "demand_surge"
    GENERATION_SHORTAGE = "generation_shortage"

    VOLTAGE_DISTURBANCE = "voltage_disturbance"
    FREQUENCY_DISTURBANCE = "frequency_disturbance"

    WEATHER_EVENT = "weather_event"
    FLOOD_EVENT = "flood_event"
    STORM_EVENT = "storm_event"
    EXTREME_HEAT = "extreme_heat"

    MULTIPLE_FAILURE = "multiple_failure"
    CASCADING_FAILURE = "cascading_failure"

    MITIGATION = "mitigation"
    CUSTOM = "custom"


class ScenarioStatus:
    """
    Lifecycle state of a scenario.
    """

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScenarioSource:
    """
    Component that created the scenario.
    """

    RISK_ENGINE = "risk_engine"
    PREDICTION_ENGINE = "prediction_engine"
    AI_AGENT = "ai_agent"
    SIMULATION_ENGINE = "simulation_engine"
    OPERATOR = "operator"
    AUTOMATED_RULE = "automated_rule"
    API = "api"
    OTHER = "other"


class ScenarioOutcome:
    """
    High-level result of a simulation scenario.
    """

    UNKNOWN = "unknown"
    STABLE = "stable"
    DEGRADED = "degraded"
    UNSTABLE = "unstable"
    BLACKOUT = "blackout"
    CASCADING_FAILURE = "cascading_failure"
    MITIGATION_SUCCESS = "mitigation_success"
    MITIGATION_FAILURE = "mitigation_failure"


# ============================================================
# SCENARIO MODEL
# ============================================================


class Scenario(Base):
    """
    SQLAlchemy model representing a hypothetical grid scenario.
    """

    __tablename__ = "scenarios"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: (
            f"SCN-{uuid4().hex[:12].upper()}"
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

    scenario_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=ScenarioStatus.CREATED,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ScenarioSource.OTHER,
        index=True,
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

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
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
    # BASELINE GRID CONDITIONS
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
    # SCENARIO CHANGES
    # ========================================================

    demand_change_mw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    demand_change_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    generation_change_mw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    generation_change_percent: Mapped[float] = mapped_column(
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

    # ========================================================
    # FAILURE PARAMETERS
    # ========================================================

    failure_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    forced_outage: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    number_of_failed_assets: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failed_assets_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # WEATHER PARAMETERS
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
    # MITIGATION PARAMETERS
    # ========================================================

    mitigation_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    mitigation_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    mitigation_actions_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # SIMULATION PARAMETERS
    # ========================================================

    simulation_method: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    simulation_engine: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    simulation_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    simulation_duration_seconds: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # SIMULATION RESULTS
    # ========================================================

    outcome: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ScenarioOutcome.UNKNOWN,
        index=True,
    )

    result_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    blackout_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    cascade_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    resulting_demand_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    resulting_generation_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    resulting_reserve_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    resulting_load_loss_mw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    resulting_generation_loss_mw: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    resulting_voltage_min_kv: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    resulting_voltage_max_kv: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    resulting_frequency_min_hz: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    resulting_frequency_max_hz: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    maximum_loading_percent: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # IMPACT
    # ========================================================

    affected_assets_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    affected_regions_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    estimated_customers_affected: Mapped[
        int | None
    ] = mapped_column(
        Integer,
        nullable=True,
    )

    estimated_load_lost_mw: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # SIMULATION VALIDATION
    # ========================================================

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

    validation_passed: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
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

    # ========================================================
    # RELATED RECORDS
    # ========================================================

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

    parameters_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    results_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    metadata_json: Mapped[str | None] = mapped_column(
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
            "ix_scenarios_region_type",
            "region_id",
            "scenario_type",
        ),
        Index(
            "ix_scenarios_region_created",
            "region_id",
            "created_at",
        ),
        Index(
            "ix_scenarios_status",
            "status",
            "created_at",
        ),
        Index(
            "ix_scenarios_outcome",
            "outcome",
            "status",
        ),
        Index(
            "ix_scenarios_asset",
            "asset_id",
        ),
        Index(
            "ix_scenarios_prediction",
            "prediction_id",
        ),
        Index(
            "ix_scenarios_recommendation",
            "recommendation_id",
        ),
        Index(
            "ix_scenarios_blackout_cascade",
            "blackout_probability",
            "cascade_probability",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "<Scenario("
            f"id='{self.id}', "
            f"name='{self.name}', "
            f"type='{self.scenario_type}', "
            f"status='{self.status}', "
            f"outcome='{self.outcome}'"
            ")>"
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Scenario",
    "ScenarioType",
    "ScenarioStatus",
    "ScenarioSource",
    "ScenarioOutcome",
]