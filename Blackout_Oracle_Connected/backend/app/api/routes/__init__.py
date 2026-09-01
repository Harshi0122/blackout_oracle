"""
Blackout Oracle - API Routes Package.

This package contains the HTTP API route modules used by the backend.

Routes are intentionally separated by responsibility so that the API can
grow without putting all endpoints into a single file.

Expected route groups include:

- Health and system status
- Grid information
- Telemetry
- Weather
- Risk assessment
- Incidents
- Predictions
- Simulations
- AI agent operations
- Alerts

Route modules should contain HTTP/API concerns only. Business logic should
remain in the appropriate service layer.
"""

__all__: list[str] = []