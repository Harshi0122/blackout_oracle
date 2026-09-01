"""
Blackout Oracle - Asset Failure Prediction Package.

This package contains components for estimating the probability
of failure or abnormal operation of electrical-grid assets.

Supported asset categories may include:

- Transformers
- Generators
- Feeders
- Transmission lines
- Substations
- Buses
- Other monitored grid assets

The package is intentionally kept lightweight at initialization
time to avoid circular imports and unnecessary dependencies.

Concrete prediction and service modules should be imported
explicitly by the application when required.
"""

__all__ = []