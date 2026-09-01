"""
Blackout Oracle - ML Training Package.

Contains utilities responsible for training, validating, and
persisting machine-learning models used by Blackout Oracle.

Training components may include:

- Feature preparation
- Dataset preparation
- Model training
- Validation
- Hyperparameter configuration
- Model evaluation
- Model persistence
- Training metadata
- Model versioning

The package initialization is intentionally lightweight to avoid
circular imports between the training, ML, database, ingestion,
and application layers.

Concrete training utilities should be imported explicitly where
required.
"""

__all__ = []