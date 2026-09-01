"""
Blackout Oracle - ML Model Registry.

Central registry for machine-learning models used by Blackout
Oracle.

The registry provides a lightweight way to:

- Register models
- Retrieve models by name
- Track model versions
- Activate/deactivate models
- Store model metadata
- List registered models
- Select the active model
- Remove models
- Check model availability
- Export registry information

The registry is intentionally dependency-free and does not
persist models to disk or a database by itself. Persistence can
be added later through the training/model-storage layer.

This module is designed to work with the existing ML modules:

    app.ml.anamoly
    app.ml.asset_failure
    app.ml.blackout_risk
    app.ml.cascade
    app.ml.forecasting
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_VERSION = "1.0"

DEFAULT_STATUS = "registered"

VALID_STATUSES = {
    "registered",
    "active",
    "inactive",
    "deprecated",
}


# ============================================================
# HELPERS
# ============================================================


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""

    return datetime.now(
        timezone.utc
    )


def _validate_name(
    name: str,
    field_name: str = "name",
) -> str:
    """Validate a registry name."""

    if not isinstance(
        name,
        str,
    ):
        raise TypeError(
            f"{field_name} must be a string."
        )

    name = name.strip()

    if not name:
        raise ValueError(
            f"{field_name} cannot be empty."
        )

    return name


def _validate_version(
    version: str,
) -> str:
    """Validate a model version."""

    return _validate_name(
        version,
        "version",
    )


# ============================================================
# MODEL ENTRY
# ============================================================


@dataclass
class ModelEntry:
    """
    Metadata and runtime information for one registered model.

    Parameters
    ----------
    name:
        Unique model name.

    model:
        Model object or callable.

    version:
        Model version.

    model_type:
        Type/category of model.

    status:
        Registry status.

    metadata:
        Additional model information.
    """

    name: str

    model: Any

    version: str = DEFAULT_VERSION

    model_type: str = "unknown"

    status: str = DEFAULT_STATUS

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=_utc_now
    )

    updated_at: datetime = field(
        default_factory=_utc_now
    )

    usage_count: int = 0

    def __post_init__(self) -> None:
        """Validate model-entry fields."""

        self.name = _validate_name(
            self.name,
            "name",
        )

        self.version = _validate_version(
            self.version
        )

        self.model_type = _validate_name(
            self.model_type,
            "model_type",
        )

        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid model status: "
                f"{self.status}"
            )

        if self.model is None:
            raise ValueError(
                "model cannot be None."
            )

    @property
    def is_active(self) -> bool:
        """Return whether the model is active."""

        return self.status == "active"

    @property
    def is_available(self) -> bool:
        """Return whether the model can be used."""

        return self.status in {
            "registered",
            "active",
        }

    def mark_active(self) -> None:
        """Mark this model as active."""

        self.status = "active"
        self.updated_at = _utc_now()

    def mark_inactive(self) -> None:
        """Mark this model as inactive."""

        self.status = "inactive"
        self.updated_at = _utc_now()

    def mark_deprecated(self) -> None:
        """Mark this model as deprecated."""

        self.status = "deprecated"
        self.updated_at = _utc_now()

    def increment_usage(self) -> None:
        """Increment the model usage counter."""

        self.usage_count += 1
        self.updated_at = _utc_now()

    def to_dict(
        self,
        include_model: bool = False,
    ) -> dict[str, Any]:
        """
        Convert the model entry into a dictionary.

        By default, the actual model object is not included.
        """

        result: dict[str, Any] = {
            "name": self.name,
            "version": self.version,
            "model_type": self.model_type,
            "status": self.status,
            "is_active": self.is_active,
            "is_available": self.is_available,
            "metadata": dict(
                self.metadata
            ),
            "created_at": (
                self.created_at.isoformat()
            ),
            "updated_at": (
                self.updated_at.isoformat()
            ),
            "usage_count": self.usage_count,
        }

        if include_model:
            result["model"] = self.model

        return result


# ============================================================
# MODEL REGISTRY
# ============================================================


class ModelRegistry:
    """
    In-memory registry for Blackout Oracle ML models.

    Models are identified by:

        model name + version

    Example:

        "cascade_risk" + "1.0"

    Multiple versions of the same model can therefore coexist.
    """

    def __init__(self) -> None:
        """Initialize an empty model registry."""

        self._models: dict[
            str,
            dict[str, ModelEntry],
        ] = {}

        self._active_versions: dict[
            str,
            str,
        ] = {}

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        name: str,
        model: Any,
        *,
        version: str = DEFAULT_VERSION,
        model_type: str = "unknown",
        metadata: dict[str, Any] | None = None,
        activate: bool = False,
        overwrite: bool = False,
    ) -> ModelEntry:
        """
        Register a model.

        Parameters
        ----------
        name:
            Unique model family name.

        model:
            Model instance or callable.

        version:
            Model version.

        model_type:
            Category of the model.

        metadata:
            Additional model metadata.

        activate:
            Whether this version should become active.

        overwrite:
            Whether an existing same-name/version entry can
            be replaced.
        """

        name = _validate_name(
            name
        )

        version = _validate_version(
            version
        )

        if not overwrite and self.exists(
            name,
            version,
        ):
            raise ValueError(
                f"Model '{name}' version "
                f"'{version}' is already registered."
            )

        entry = ModelEntry(
            name=name,
            model=model,
            version=version,
            model_type=model_type,
            metadata=dict(
                metadata
                or {}
            ),
        )

        if name not in self._models:
            self._models[name] = {}

        self._models[name][
            version
        ] = entry

        if activate:
            self.set_active(
                name,
                version,
            )

        return entry

    # ========================================================
    # GET
    # ========================================================

    def get(
        self,
        name: str,
        version: str | None = None,
        *,
        active_only: bool = False,
    ) -> Any:
        """
        Retrieve a registered model.

        If version is omitted, the active version is preferred.

        If no active version exists, the latest registered
        version is returned.
        """

        entry = self.get_entry(
            name,
            version=version,
            active_only=active_only,
        )

        if entry is None:
            raise KeyError(
                self._missing_model_message(
                    name,
                    version,
                )
            )

        entry.increment_usage()

        return entry.model

    # ========================================================
    # GET ENTRY
    # ========================================================

    def get_entry(
        self,
        name: str,
        version: str | None = None,
        *,
        active_only: bool = False,
    ) -> ModelEntry | None:
        """
        Retrieve model metadata without incrementing usage.
        """

        name = _validate_name(
            name
        )

        if name not in self._models:
            return None

        versions = self._models[
            name
        ]

        if version is not None:
            version = _validate_version(
                version
            )

            entry = versions.get(
                version
            )

            if entry is None:
                return None

            if (
                active_only
                and not entry.is_active
            ):
                return None

            return entry

        active_version = (
            self._active_versions.get(
                name
            )
        )

        if active_version is not None:
            entry = versions.get(
                active_version
            )

            if entry is not None:
                if (
                    not active_only
                    or entry.is_active
                ):
                    return entry

        if active_only:
            return None

        if not versions:
            return None

        return self._latest_entry(
            versions
        )

    # ========================================================
    # GET ACTIVE
    # ========================================================

    def get_active(
        self,
        name: str,
    ) -> Any:
        """
        Retrieve the active model for a model family.
        """

        entry = self.get_entry(
            name,
            active_only=True,
        )

        if entry is None:
            raise KeyError(
                f"No active model registered "
                f"for '{name}'."
            )

        entry.increment_usage()

        return entry.model

    # ========================================================
    # GET ACTIVE ENTRY
    # ========================================================

    def get_active_entry(
        self,
        name: str,
    ) -> ModelEntry | None:
        """Return metadata for the active model."""

        return self.get_entry(
            name,
            active_only=True,
        )

    # ========================================================
    # SET ACTIVE
    # ========================================================

    def set_active(
        self,
        name: str,
        version: str,
    ) -> ModelEntry:
        """
        Activate a specific model version.

        Only one version of a model family can be active at a
        time.
        """

        name = _validate_name(
            name
        )

        version = _validate_version(
            version
        )

        if name not in self._models:
            raise KeyError(
                f"Model '{name}' is not registered."
            )

        versions = self._models[
            name
        ]

        if version not in versions:
            raise KeyError(
                f"Model '{name}' version "
                f"'{version}' is not registered."
            )

        for entry in versions.values():
            if entry.is_active:
                entry.mark_inactive()

        entry = versions[
            version
        ]

        entry.mark_active()

        self._active_versions[
            name
        ] = version

        return entry

    # ========================================================
    # DEACTIVATE
    # ========================================================

    def deactivate(
        self,
        name: str,
        version: str | None = None,
    ) -> ModelEntry:
        """
        Deactivate a model version.

        If version is omitted, the active version is deactivated.
        """

        entry = self.get_entry(
            name,
            version=version,
        )

        if entry is None:
            raise KeyError(
                self._missing_model_message(
                    name,
                    version,
                )
            )

        entry.mark_inactive()

        if (
            self._active_versions.get(
                name
            )
            == entry.version
        ):
            del self._active_versions[
                name
            ]

        return entry

    # ========================================================
    # DEPRECATE
    # ========================================================

    def deprecate(
        self,
        name: str,
        version: str,
    ) -> ModelEntry:
        """
        Mark a model version as deprecated.
        """

        entry = self.get_entry(
            name,
            version=version,
        )

        if entry is None:
            raise KeyError(
                self._missing_model_message(
                    name,
                    version,
                )
            )

        entry.mark_deprecated()

        if (
            self._active_versions.get(
                name
            )
            == version
        ):
            del self._active_versions[
                name
            ]

        return entry

    # ========================================================
    # EXISTS
    # ========================================================

    def exists(
        self,
        name: str,
        version: str | None = None,
    ) -> bool:
        """
        Check whether a model is registered.
        """

        name = _validate_name(
            name
        )

        if name not in self._models:
            return False

        if version is None:
            return bool(
                self._models[name]
            )

        version = _validate_version(
            version
        )

        return version in self._models[
            name
        ]

    # ========================================================
    # REMOVE
    # ========================================================

    def remove(
        self,
        name: str,
        version: str | None = None,
    ) -> ModelEntry | list[ModelEntry]:
        """
        Remove a model.

        If version is provided, only that version is removed.

        If version is omitted, all versions of the model family
        are removed.
        """

        name = _validate_name(
            name
        )

        if name not in self._models:
            raise KeyError(
                f"Model '{name}' is not registered."
            )

        versions = self._models[
            name
        ]

        if version is not None:
            version = _validate_version(
                version
            )

            if version not in versions:
                raise KeyError(
                    self._missing_model_message(
                        name,
                        version,
                    )
                )

            entry = versions.pop(
                version
            )

            if (
                self._active_versions.get(
                    name
                )
                == version
            ):
                del self._active_versions[
                    name
                ]

            if not versions:
                del self._models[
                    name
                ]

            return entry

        removed = list(
            versions.values()
        )

        del self._models[
            name
        ]

        self._active_versions.pop(
            name,
            None,
        )

        return removed

    # ========================================================
    # LIST MODELS
    # ========================================================

    def list_models(
        self,
        *,
        model_type: str | None = None,
        status: str | None = None,
    ) -> list[ModelEntry]:
        """
        Return all registered model versions.
        """

        entries: list[
            ModelEntry
        ] = []

        for versions in self._models.values():
            for entry in versions.values():
                if (
                    model_type is not None
                    and entry.model_type
                    != model_type
                ):
                    continue

                if (
                    status is not None
                    and entry.status
                    != status
                ):
                    continue

                entries.append(
                    entry
                )

        return sorted(
            entries,
            key=lambda entry: (
                entry.name,
                entry.created_at,
            ),
        )

    # ========================================================
    # LIST NAMES
    # ========================================================

    def list_names(
        self,
    ) -> list[str]:
        """Return registered model family names."""

        return sorted(
            self._models.keys()
        )

    # ========================================================
    # LIST VERSIONS
    # ========================================================

    def list_versions(
        self,
        name: str,
    ) -> list[str]:
        """Return all registered versions of a model."""

        name = _validate_name(
            name
        )

        if name not in self._models:
            return []

        return sorted(
            self._models[
                name
            ].keys()
        )

    # ========================================================
    # LATEST
    # ========================================================

    def get_latest_entry(
        self,
        name: str,
    ) -> ModelEntry | None:
        """Return the latest registered model version."""

        name = _validate_name(
            name
        )

        versions = self._models.get(
            name
        )

        if not versions:
            return None

        return self._latest_entry(
            versions
        )

    @staticmethod
    def _latest_entry(
        versions: dict[str, ModelEntry],
    ) -> ModelEntry:
        """
        Select the latest entry.

        Creation time is used rather than attempting to parse
        arbitrary version strings.
        """

        return max(
            versions.values(),
            key=lambda entry: entry.created_at,
        )

    # ========================================================
    # MODEL COUNT
    # ========================================================

    def count(
        self,
        name: str | None = None,
    ) -> int:
        """
        Return the number of registered model versions.

        If name is supplied, count only that model family.
        """

        if name is not None:
            name = _validate_name(
                name
            )

            return len(
                self._models.get(
                    name,
                    {},
                )
            )

        return sum(
            len(versions)
            for versions
            in self._models.values()
        )

    # ========================================================
    # ACTIVE MODELS
    # ========================================================

    def active_models(
        self,
    ) -> list[ModelEntry]:
        """Return all currently active models."""

        return self.list_models(
            status="active"
        )

    # ========================================================
    # MODEL TYPES
    # ========================================================

    def model_types(
        self,
    ) -> list[str]:
        """Return unique registered model types."""

        return sorted(
            {
                entry.model_type
                for entry
                in self.list_models()
            }
        )

    # ========================================================
    # UPDATE METADATA
    # ========================================================

    def update_metadata(
        self,
        name: str,
        version: str,
        metadata: dict[str, Any],
    ) -> ModelEntry:
        """
        Update metadata for a registered model.
        """

        entry = self.get_entry(
            name,
            version=version,
        )

        if entry is None:
            raise KeyError(
                self._missing_model_message(
                    name,
                    version,
                )
            )

        entry.metadata.update(
            metadata
        )

        entry.updated_at = _utc_now()

        return entry

    # ========================================================
    # REPLACE MODEL
    # ========================================================

    def replace_model(
        self,
        name: str,
        version: str,
        model: Any,
    ) -> ModelEntry:
        """
        Replace the runtime model object while preserving
        registry metadata.
        """

        if model is None:
            raise ValueError(
                "model cannot be None."
            )

        entry = self.get_entry(
            name,
            version=version,
        )

        if entry is None:
            raise KeyError(
                self._missing_model_message(
                    name,
                    version,
                )
            )

        entry.model = model
        entry.updated_at = _utc_now()

        return entry

    # ========================================================
    # HEALTH CHECK
    # ========================================================

    def health_check(
        self,
    ) -> dict[str, Any]:
        """
        Return registry health information.
        """

        entries = self.list_models()

        active_entries = [
            entry
            for entry in entries
            if entry.is_active
        ]

        unavailable_entries = [
            entry
            for entry in entries
            if not entry.is_available
        ]

        return {
            "healthy": True,
            "model_family_count": len(
                self._models
            ),
            "registered_version_count": len(
                entries
            ),
            "active_model_count": len(
                active_entries
            ),
            "unavailable_model_count": len(
                unavailable_entries
            ),
            "models": [
                {
                    "name": entry.name,
                    "version": entry.version,
                    "status": entry.status,
                }
                for entry in entries
            ],
        }

    # ========================================================
    # EXPORT
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Export registry metadata.

        Actual model objects are intentionally excluded.
        """

        return {
            "model_count": self.count(),
            "model_family_count": len(
                self._models
            ),
            "active_versions": dict(
                self._active_versions
            ),
            "models": [
                entry.to_dict()
                for entry in self.list_models()
            ],
        }

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        """Remove all registered models."""

        self._models.clear()

        self._active_versions.clear()

    # ========================================================
    # INTERNAL ERROR MESSAGE
    # ========================================================

    @staticmethod
    def _missing_model_message(
        name: str,
        version: str | None,
    ) -> str:
        """Build a useful missing-model error."""

        if version is None:
            return (
                f"Model '{name}' is not registered."
            )

        return (
            f"Model '{name}' version "
            f"'{version}' is not registered."
        )


# ============================================================
# GLOBAL REGISTRY
# ============================================================


_registry = ModelRegistry()


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def register_model(
    name: str,
    model: Any,
    *,
    version: str = DEFAULT_VERSION,
    model_type: str = "unknown",
    metadata: dict[str, Any] | None = None,
    activate: bool = False,
    overwrite: bool = False,
) -> ModelEntry:
    """
    Register a model in the global registry.
    """

    return _registry.register(
        name,
        model,
        version=version,
        model_type=model_type,
        metadata=metadata,
        activate=activate,
        overwrite=overwrite,
    )


def get_model(
    name: str,
    version: str | None = None,
) -> Any:
    """
    Retrieve a model from the global registry.
    """

    return _registry.get(
        name,
        version=version,
    )


def get_active_model(
    name: str,
) -> Any:
    """
    Retrieve the active model from the global registry.
    """

    return _registry.get_active(
        name
    )


def get_model_entry(
    name: str,
    version: str | None = None,
) -> ModelEntry | None:
    """
    Retrieve model metadata from the global registry.
    """

    return _registry.get_entry(
        name,
        version=version,
    )


def set_active_model(
    name: str,
    version: str,
) -> ModelEntry:
    """
    Activate a model version in the global registry.
    """

    return _registry.set_active(
        name,
        version,
    )


def deactivate_model(
    name: str,
    version: str | None = None,
) -> ModelEntry:
    """
    Deactivate a model version.
    """

    return _registry.deactivate(
        name,
        version=version,
    )


def remove_model(
    name: str,
    version: str | None = None,
) -> ModelEntry | list[ModelEntry]:
    """
    Remove a model from the global registry.
    """

    return _registry.remove(
        name,
        version=version,
    )


def list_models() -> list[ModelEntry]:
    """
    List all models in the global registry.
    """

    return _registry.list_models()


def registry_health() -> dict[str, Any]:
    """
    Return global registry health information.
    """

    return _registry.health_check()


def get_registry() -> ModelRegistry:
    """
    Return the global model registry instance.

    Useful when application code needs advanced registry
    operations.
    """

    return _registry


# ============================================================
# BLACKOUT ORACLE DEFAULT MODEL NAMES
# ============================================================


ANOMALY_MODEL = "anomaly_detector"

ASSET_FAILURE_MODEL = "asset_failure"

BLACKOUT_RISK_MODEL = "blackout_risk"

CASCADE_MODEL = "cascade_risk"

FORECASTING_MODEL = "grid_forecasting"


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "ModelEntry",
    "ModelRegistry",
    "register_model",
    "get_model",
    "get_active_model",
    "get_model_entry",
    "set_active_model",
    "deactivate_model",
    "remove_model",
    "list_models",
    "registry_health",
    "get_registry",
    "ANOMALY_MODEL",
    "ASSET_FAILURE_MODEL",
    "BLACKOUT_RISK_MODEL",
    "CASCADE_MODEL",
    "FORECASTING_MODEL",
]