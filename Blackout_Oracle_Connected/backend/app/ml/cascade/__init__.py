"""
Blackout Oracle - Cascade Analysis Package.

This package contains components used to analyze potential
cascading failures across the electrical grid.

Cascade analysis can be used to evaluate:

- Transmission-line overload propagation
- Transformer overload propagation
- Generator trips
- Substation failures
- Network connectivity loss
- Load redistribution
- Cascading-failure risk
- Potential blackout propagation paths

The package initialization is intentionally lightweight to
avoid circular imports between the ML, grid, incident, and
database layers.

Concrete cascade models and services should be imported
explicitly where required.
"""

__all__ = []