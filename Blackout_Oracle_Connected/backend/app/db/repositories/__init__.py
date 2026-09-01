"""
Blackout Oracle - Database Repositories.

Repository package responsible for database access operations.

Repositories provide a clean separation between:

    API / Agent / Services
              │
              ▼
        Repository Layer
              │
              ▼
          SQLAlchemy
              │
              ▼
           Database

This package contains repository implementations for:

- Alerts
- Assets
- Incidents
- Predictions
- Recommendations
- Risk scores
- Scenarios
- Simulations
- Substations
- Telemetry
- Transformers
- Transmission lines
- Weather
"""

# Repository classes will be imported here as they are created.

__all__ = []