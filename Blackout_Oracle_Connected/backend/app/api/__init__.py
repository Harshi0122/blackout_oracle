"""
Blackout Oracle - API Package.

Contains the FastAPI HTTP API layer for:

- Health checks
- Grid assets
- Telemetry
- Weather
- Risk assessments
- Incidents
- Simulations
- AI recommendations

The API layer should remain separate from the business logic,
data-access, AI-agent, and simulation layers.
"""

from . import routes

__all__ = [
    "routes",
]