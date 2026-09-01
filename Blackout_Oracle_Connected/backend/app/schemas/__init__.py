"""
Blackout Oracle - Application Schemas.

Central package for Pydantic schemas used by the API and
application layers.

Schemas define the structure of data exchanged between:

- API endpoints
- Database repositories
- Grid services
- Ingestion pipelines
- Risk engine
- Incident management
- Simulation services
- ML services

The package initialization is intentionally lightweight.
Individual schema modules should be imported explicitly to
avoid circular dependencies.
"""

__all__ = []