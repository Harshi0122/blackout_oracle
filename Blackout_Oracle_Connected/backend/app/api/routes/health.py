"""
Blackout Oracle - Health Check API Routes.

Provides endpoints used to determine whether the Blackout Oracle backend
and its major dependencies are available.

Health checks are intentionally lightweight. They must not perform expensive
AI inference, power-system simulations, or real-grid operations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel, Field


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


# ============================================================
# ENUMS
# ============================================================


class ServiceStatus(str, Enum):
    """Possible health states of a service."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


# ============================================================
# RESPONSE MODELS
# ============================================================


class ComponentHealth(BaseModel):
    """Health information for one backend component."""

    name: str
    status: ServiceStatus
    message: str | None = None
    latency_ms: float | None = Field(
        default=None,
        ge=0,
    )


class HealthResponse(BaseModel):
    """Complete backend health response."""

    status: ServiceStatus

    service: str

    version: str

    timestamp: datetime

    components: list[ComponentHealth]


class ReadinessResponse(BaseModel):
    """Backend readiness response."""

    ready: bool

    service: str

    timestamp: datetime

    components: list[ComponentHealth]


class LivenessResponse(BaseModel):
    """Backend liveness response."""

    alive: bool

    service: str

    timestamp: datetime


# ============================================================
# CONFIGURATION
# ============================================================

SERVICE_NAME = "blackout-oracle-backend"

# Keep this synchronized with the application version when the project
# eventually gets a centralized version configuration.
SERVICE_VERSION = "0.1.0"


# ============================================================
# COMPONENT CHECKS
# ============================================================


async def check_application() -> ComponentHealth:
    """
    Check whether the application process is functioning.

    This check is intentionally trivial because reaching this function
    already indicates that the FastAPI application is responding.
    """

    return ComponentHealth(
        name="application",
        status=ServiceStatus.HEALTHY,
        message="Application process is responding.",
    )


async def check_database() -> ComponentHealth:
    """
    Check database availability.

    The actual PostgreSQL/TimescaleDB health check will be connected here
    when the database layer is implemented.
    """

    # TODO:
    # Replace this placeholder with an actual database connection check.

    return ComponentHealth(
        name="database",
        status=ServiceStatus.UNKNOWN,
        message="Database health check is not connected yet.",
    )


async def check_telemetry() -> ComponentHealth:
    """
    Check the telemetry ingestion service.

    This will eventually verify that the grid telemetry pipeline is
    receiving sufficiently fresh data.
    """

    # TODO:
    # Connect this to the telemetry/data-ingestion service.

    return ComponentHealth(
        name="telemetry",
        status=ServiceStatus.UNKNOWN,
        message="Telemetry service health check is not connected yet.",
    )


async def check_weather() -> ComponentHealth:
    """
    Check availability of the weather-data service.
    """

    # TODO:
    # Connect this to the weather service.

    return ComponentHealth(
        name="weather",
        status=ServiceStatus.UNKNOWN,
        message="Weather service health check is not connected yet.",
    )


async def check_ai_agent() -> ComponentHealth:
    """
    Check availability of the AI-agent layer.

    This does not perform an actual Gemini inference request.
    """

    # TODO:
    # Check Gemini configuration/client availability here.

    return ComponentHealth(
        name="ai_agent",
        status=ServiceStatus.UNKNOWN,
        message="AI agent health check is not connected yet.",
    )


async def check_simulation_engine() -> ComponentHealth:
    """
    Check availability of the power-system simulation engine.

    The production implementation will verify that the simulation layer
    can initialize correctly without interacting with real infrastructure.
    """

    # TODO:
    # Connect to the pandapower simulation service.

    return ComponentHealth(
        name="simulation_engine",
        status=ServiceStatus.UNKNOWN,
        message="Simulation engine health check is not connected yet.",
    )


# ============================================================
# OVERALL STATUS
# ============================================================


def calculate_overall_status(
    components: list[ComponentHealth],
) -> ServiceStatus:
    """
    Determine overall backend health from component states.

    Rules:

        UNAVAILABLE → UNAVAILABLE
        DEGRADED    → DEGRADED
        UNKNOWN     → DEGRADED
        otherwise   → HEALTHY

    Unknown dependencies prevent the service from being reported as fully
    healthy, which is safer for a monitoring system.
    """

    if any(
        component.status == ServiceStatus.UNAVAILABLE
        for component in components
    ):
        return ServiceStatus.UNAVAILABLE

    if any(
        component.status in {
            ServiceStatus.DEGRADED,
            ServiceStatus.UNKNOWN,
        }
        for component in components
    ):
        return ServiceStatus.DEGRADED

    return ServiceStatus.HEALTHY


async def collect_component_health() -> list[ComponentHealth]:
    """
    Collect health information from all major backend components.
    """

    return [
        await check_application(),
        await check_database(),
        await check_telemetry(),
        await check_weather(),
        await check_ai_agent(),
        await check_simulation_engine(),
    ]


# ============================================================
# LIVENESS
# ============================================================


@router.get(
    "/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
)
async def liveness() -> LivenessResponse:
    """
    Kubernetes/container-style liveness check.

    If this endpoint responds successfully, the API process is alive.

    It deliberately does not check external dependencies.
    """

    return LivenessResponse(
        alive=True,
        service=SERVICE_NAME,
        timestamp=datetime.now(timezone.utc),
    )


# ============================================================
# READINESS
# ============================================================


@router.get(
    "/ready",
    response_model=ReadinessResponse,
)
async def readiness() -> ReadinessResponse:
    """
    Determine whether the backend is ready to serve requests.

    During early development, components marked UNKNOWN cause the service
    to be reported as not fully ready.

    As individual services are implemented, their health checks will become
    meaningful.
    """

    components = await collect_component_health()

    overall_status = calculate_overall_status(
        components
    )

    ready = overall_status == ServiceStatus.HEALTHY

    return ReadinessResponse(
        ready=ready,
        service=SERVICE_NAME,
        timestamp=datetime.now(timezone.utc),
        components=components,
    )


# ============================================================
# FULL HEALTH CHECK
# ============================================================


@router.get(
    "",
    response_model=HealthResponse,
)
async def health_check() -> HealthResponse:
    """
    Return the complete Blackout Oracle backend health status.

    This endpoint is useful for:

    - Development
    - Monitoring
    - Docker
    - Deployment systems
    - CI/CD
    - Future production observability
    """

    components = await collect_component_health()

    overall_status = calculate_overall_status(
        components
    )

    return HealthResponse(
        status=overall_status,
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        timestamp=datetime.now(timezone.utc),
        components=components,
    )


# ============================================================
# SIMPLE HEALTH CHECK
# ============================================================


@router.get(
    "/ping",
    response_model=dict[str, Any],
)
async def ping() -> dict[str, Any]:
    """
    Minimal health endpoint.

    Useful for quickly testing whether FastAPI is responding.
    """

    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "router",
    "ServiceStatus",
    "ComponentHealth",
    "HealthResponse",
    "ReadinessResponse",
    "LivenessResponse",
]