"""
Blackout Oracle - Forecasting Package.

Contains forecasting components used to predict future grid
conditions such as:

- Electrical load
- Power generation
- Demand trends
- Asset measurements
- Grid stress
- Future operating conditions

The package initialization is intentionally lightweight to
avoid circular imports between the forecasting, ML, grid,
database, and ingestion layers.

Concrete forecasting models and services should be imported
explicitly where required.
"""

__all__ = []