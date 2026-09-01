"""
Blackout Oracle - Data Ingestion Package.

This package contains the components responsible for collecting,
normalizing, validating, and preparing external and synthetic
grid data for the rest of the application.

Supported ingestion sources include:

- Historical datasets
- IMD weather data
- Public SLDC data
- Public TANGEDCO data
- Synthetic grid telemetry

The ingestion layer should convert different external formats
into consistent internal data structures before passing data to
feature engineering, grid analysis, prediction, and risk
assessment modules.
"""

__all__ = []