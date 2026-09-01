"""
Blackout Oracle - Machine Learning Package.

This package contains the machine-learning components used by
Blackout Oracle for grid monitoring, prediction, anomaly
detection, forecasting, asset-failure prediction, blackout-risk
assessment, and cascading-failure analysis.

Available ML modules:

    anamoly/
        Anomaly detection and anomaly-analysis services.

    asset_failure/
        Asset failure prediction models and services.

    blackout_risk/
        Blackout-risk prediction models and services.

    cascade/
        Cascading-failure risk models and services.

    evaluation/
        Model evaluation metrics and validation utilities.

    forecasting/
        Load, generation, and grid-metric forecasting.

    training/
        Dataset preparation and training utilities.

The package initialization is intentionally lightweight.
Submodules should be imported explicitly to avoid unnecessary
startup costs and circular dependencies.
"""

__all__ = [
    "anamoly",
    "asset_failure",
    "blackout_risk",
    "cascade",
    "evaluation",
    "forecasting",
    "training",
]