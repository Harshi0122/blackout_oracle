"""
Blackout Oracle - Risk Package.

Contains the application-level risk assessment components used
to evaluate the operational risk of the electrical grid.

The risk layer combines information from:

- Grid topology
- Electrical measurements
- Weather conditions
- Historical incidents
- Asset health
- Forecasting
- Anomaly detection
- Blackout-risk prediction
- Cascade-risk prediction

Typical risk outputs include:

- Overall risk score
- Risk level
- Risk contributors
- Asset risk
- Regional risk
- Blackout probability
- Cascade probability
- Recommended actions

The package initialization is intentionally lightweight to avoid
circular imports between the risk, ML, grid, database, incident,
and ingestion layers.

Concrete risk components should be imported explicitly where
required.
"""

__all__ = []