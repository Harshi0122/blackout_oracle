"""
Blackout Oracle - FastAPI application entry point.

This module creates and configures the FastAPI application,
registers API routers, and exposes health/status endpoints.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __app_name__, __version__


# ============================================================
# APPLICATION STATE
# ============================================================


_startup_time: datetime | None = None


# ============================================================
# LIFESPAN
# ============================================================


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    """
    Application startup/shutdown lifecycle.
    """

    global _startup_time

    _startup_time = datetime.now(timezone.utc)

    # Local-only data keeps the separately supplied dashboard useful as soon
    # as the API is started. Production ingestion can replace these stores.
    from app.demo_data import seed_demo_data
    seed_demo_data()

    app.state.started_at = _startup_time
    app.state.ready = True

    yield

    app.state.ready = False


# ============================================================
# APPLICATION
# ============================================================


app = FastAPI(
    title=__app_name__,
    version=__version__,
    description=(
        "AI-powered electrical-grid monitoring, "
        "anomaly detection, blackout-risk prediction, "
        "and grid simulation platform."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ============================================================
# CORS
# ============================================================


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTER REGISTRATION
# ============================================================


def _register_routers() -> None:
    """
    Register application routers.

    Imports are performed lazily so that a failure in an optional
    feature does not prevent the core FastAPI application from
    being imported.
    """

    router_paths = [
        (
            "app.api.routes.assets",
            "router",
        ),
        (
            "app.api.routes.alerts",
            "router",
        ),
        (
            "app.api.routes.incidents",
            "router",
        ),
        (
            "app.api.routes.risk",
            "router",
        ),
        (
            "app.api.routes.simulations",
            "router",
        ),
        (
            "app.api.routes.telemetry",
            "router",
        ),
        (
            "app.api.routes.weather",
            "router",
        ),
        (
            "app.api.routes.recommendations",
            "router",
        ),
    ]

    for module_name, router_name in router_paths:
        try:
            module = __import__(
                module_name,
                fromlist=[router_name],
            )

            router = getattr(
                module,
                router_name,
                None,
            )

            if router is not None:
                app.include_router(
                    router
                )

        except ModuleNotFoundError:
            # Some route modules may not exist yet while the
            # backend is being developed. Keep the application
            # bootable instead of failing at import time.
            continue


_register_routers()


# ============================================================
# ROOT
# ============================================================


@app.get(
    "/",
    tags=["system"],
)
async def root() -> dict[str, Any]:
    """
    Return basic API information.
    """

    return {
        "name": __app_name__,
        "version": __version__,
        "status": "online",
        "message": (
            "Blackout Oracle backend is running."
        ),
        "docs": "/docs",
    }


# ============================================================
# HEALTH
# ============================================================


@app.get(
    "/health",
    tags=["system"],
)
async def health() -> dict[str, Any]:
    """
    Basic health check.

    This endpoint should remain lightweight and should not depend
    on external services.
    """

    return {
        "status": "healthy",
        "service": __app_name__,
        "version": __version__,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
    }


# ============================================================
# READINESS
# ============================================================


@app.get(
    "/ready",
    tags=["system"],
)
async def readiness() -> dict[str, Any]:
    """
    Readiness endpoint.

    Returns whether the application has completed startup.
    """

    ready = bool(
        getattr(
            app.state,
            "ready",
            False,
        )
    )

    return {
        "ready": ready,
        "status": (
            "ready"
            if ready
            else "starting"
        ),
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
    }


# ============================================================
# VERSION
# ============================================================


@app.get(
    "/version",
    tags=["system"],
)
async def version() -> dict[str, str]:
    """
    Return backend version information.
    """

    return {
        "name": __app_name__,
        "version": __version__,
    }


# ============================================================
# ERROR HANDLING
# ============================================================


@app.get(
    "/health/live",
    tags=["system"],
)
async def liveness() -> dict[str, str]:
    """
    Kubernetes/Docker-style liveness endpoint.
    """

    return {
        "status": "alive"
    }


# ============================================================
# DEVELOPMENT ENTRY POINT
# ============================================================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
