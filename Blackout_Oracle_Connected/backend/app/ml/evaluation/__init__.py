"""
Blackout Oracle - ML Evaluation Package.

Utilities for evaluating, validating, and comparing the
machine-learning and risk-scoring components used by
Blackout Oracle.

Evaluation may include:

- Prediction accuracy
- Classification metrics
- Risk-score quality
- Probability calibration
- Confusion matrices
- Precision and recall
- False-positive / false-negative analysis
- Model comparison
- Prediction stability
- Threshold analysis

The package initialization is intentionally lightweight to
avoid circular imports between the ML, grid, incident, and
database layers.

Concrete evaluation utilities should be imported explicitly
where required.
"""

__all__ = []