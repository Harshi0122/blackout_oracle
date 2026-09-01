"""
Blackout Oracle - Training Dataset Utilities.

Provides dependency-free utilities for preparing, validating,
splitting, and transforming datasets used by the ML components
of Blackout Oracle.

Supported capabilities:

- Dataset representation
- Feature / target separation
- Numeric feature extraction
- Missing-value handling
- Dataset validation
- Train / validation / test splitting
- Binary target preparation
- Regression target preparation
- Feature normalization
- Dataset summaries
- Batch conversion to dictionaries

This module intentionally avoids pandas, NumPy, and scikit-learn
so that the backend can use it without introducing additional
ML dependencies.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence


# ============================================================
# CONSTANTS
# ============================================================

EPSILON = 1e-12

DEFAULT_TRAIN_RATIO = 0.70
DEFAULT_VALIDATION_RATIO = 0.15
DEFAULT_TEST_RATIO = 0.15


# ============================================================
# DATASET TYPES
# ============================================================


@dataclass
class Dataset:
    """
    Generic tabular dataset.

    Each row is represented as a dictionary:

        {
            "frequency_hz": 49.8,
            "load_mw": 9200,
            "voltage": 0.97,
            "risk": 1,
        }
    """

    rows: list[dict[str, Any]] = field(
        default_factory=list
    )

    feature_names: list[str] = field(
        default_factory=list
    )

    target_name: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def size(self) -> int:
        """Return the number of rows."""

        return len(self.rows)

    @property
    def is_empty(self) -> bool:
        """Return True when the dataset has no rows."""

        return not self.rows

    def to_dict(self) -> dict[str, Any]:
        """Convert the dataset to a dictionary."""

        return {
            "rows": [
                dict(row)
                for row in self.rows
            ],
            "feature_names": list(
                self.feature_names
            ),
            "target_name": self.target_name,
            "metadata": dict(
                self.metadata
            ),
        }


@dataclass
class DatasetSplit:
    """
    Train / validation / test dataset split.
    """

    train: Dataset

    validation: Dataset

    test: Dataset

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert the split into a dictionary."""

        return {
            "train": self.train.to_dict(),
            "validation": self.validation.to_dict(),
            "test": self.test.to_dict(),
            "metadata": dict(
                self.metadata
            ),
        }


@dataclass
class FeatureScaler:
    """
    Min-max feature scaler.

    Values are transformed approximately into:

        0.0 <= value <= 1.0

    Constant features are mapped to 0.0.
    """

    minimums: dict[str, float] = field(
        default_factory=dict
    )

    maximums: dict[str, float] = field(
        default_factory=dict
    )

    def transform_value(
        self,
        feature_name: str,
        value: Any,
    ) -> float:
        """Scale one feature value."""

        numeric = _to_float(
            value,
            feature_name,
        )

        if feature_name not in self.minimums:
            raise KeyError(
                f"Unknown feature: {feature_name}"
            )

        minimum = self.minimums[
            feature_name
        ]

        maximum = self.maximums[
            feature_name
        ]

        if abs(
            maximum - minimum
        ) <= EPSILON:
            return 0.0

        return _clamp(
            (
                numeric - minimum
            )
            / (
                maximum - minimum
            )
        )

    def transform_row(
        self,
        row: Mapping[str, Any],
        feature_names: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Scale numeric features in one row."""

        names = (
            list(feature_names)
            if feature_names is not None
            else list(self.minimums.keys())
        )

        result = dict(row)

        for name in names:
            if name in row:
                result[name] = (
                    self.transform_value(
                        name,
                        row[name],
                    )
                )

        return result

    def transform_dataset(
        self,
        dataset: Dataset,
    ) -> Dataset:
        """Scale all configured features in a dataset."""

        return Dataset(
            rows=[
                self.transform_row(
                    row,
                    dataset.feature_names,
                )
                for row in dataset.rows
            ],
            feature_names=list(
                dataset.feature_names
            ),
            target_name=dataset.target_name,
            metadata={
                **dataset.metadata,
                "scaled": True,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert scaler information to a dictionary."""

        return {
            "minimums": dict(
                self.minimums
            ),
            "maximums": dict(
                self.maximums
            ),
        }


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def _to_float(
    value: Any,
    field_name: str = "value",
) -> float:
    """Convert a value to a finite float."""

    try:
        numeric = float(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            f"{field_name} must be numeric."
        ) from exc

    if not math.isfinite(
        numeric
    ):
        raise ValueError(
            f"{field_name} must be finite."
        )

    return numeric


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    """Clamp a value to a range."""

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def _validate_ratio(
    value: float,
    name: str,
) -> float:
    """Validate a split ratio."""

    try:
        numeric = float(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            f"{name} must be numeric."
        ) from exc

    if not 0.0 <= numeric <= 1.0:
        raise ValueError(
            f"{name} must be between 0 and 1."
        )

    return numeric


def _validate_rows(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Validate and copy dataset rows."""

    result: list[
        dict[str, Any]
    ] = []

    for index, row in enumerate(
        rows
    ):
        if not isinstance(
            row,
            Mapping,
        ):
            raise TypeError(
                f"Dataset row {index} must be a mapping."
            )

        result.append(
            dict(row)
        )

    return result


# ============================================================
# DATASET CREATION
# ============================================================


def create_dataset(
    rows: Iterable[Mapping[str, Any]],
    *,
    feature_names: Sequence[str] | None = None,
    target_name: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> Dataset:
    """
    Create a Dataset from an iterable of mappings.

    If feature_names are omitted, they are inferred from the
    first row.
    """

    validated_rows = _validate_rows(
        rows
    )

    if feature_names is None:
        if validated_rows:
            inferred = list(
                validated_rows[0].keys()
            )

            if target_name in inferred:
                inferred.remove(
                    target_name
                )

            feature_list = inferred

        else:
            feature_list = []

    else:
        feature_list = list(
            feature_names
        )

    return Dataset(
        rows=validated_rows,
        feature_names=feature_list,
        target_name=target_name,
        metadata=dict(
            metadata
            or {}
        ),
    )


# ============================================================
# FEATURE / TARGET EXTRACTION
# ============================================================


def extract_features(
    dataset: Dataset,
) -> list[list[float]]:
    """
    Extract feature values as a list of numeric rows.
    """

    if not dataset.feature_names:
        return [
            []
            for _ in dataset.rows
        ]

    result: list[
        list[float]
    ] = []

    for row_index, row in enumerate(
        dataset.rows
    ):
        values: list[
            float
        ] = []

        for feature_name in dataset.feature_names:
            if feature_name not in row:
                raise KeyError(
                    f"Missing feature "
                    f"'{feature_name}' "
                    f"in row {row_index}."
                )

            values.append(
                _to_float(
                    row[feature_name],
                    feature_name,
                )
            )

        result.append(
            values
        )

    return result


def extract_target(
    dataset: Dataset,
) -> list[Any]:
    """
    Extract the target column from a dataset.
    """

    if not dataset.target_name:
        raise ValueError(
            "Dataset does not define a target_name."
        )

    target_name = dataset.target_name

    result: list[Any] = []

    for row_index, row in enumerate(
        dataset.rows
    ):
        if target_name not in row:
            raise KeyError(
                f"Missing target "
                f"'{target_name}' "
                f"in row {row_index}."
            )

        result.append(
            row[target_name]
        )

    return result


# ============================================================
# FEATURE NAME INFERENCE
# ============================================================


def infer_numeric_features(
    rows: Iterable[Mapping[str, Any]],
    *,
    exclude: Iterable[str] | None = None,
) -> list[str]:
    """
    Infer feature names whose available values are numeric.
    """

    validated_rows = _validate_rows(
        rows
    )

    if not validated_rows:
        return []

    excluded = set(
        exclude
        or []
    )

    candidate_names = set(
        validated_rows[0].keys()
    )

    candidate_names -= excluded

    numeric_features: list[
        str
    ] = []

    for name in candidate_names:
        numeric = True

        for row in validated_rows:
            if name not in row:
                continue

            try:
                value = float(
                    row[name]
                )
            except (
                TypeError,
                ValueError,
            ):
                numeric = False
                break

            if not math.isfinite(
                value
            ):
                numeric = False
                break

        if numeric:
            numeric_features.append(
                name
            )

    return sorted(
        numeric_features
    )


# ============================================================
# DATASET VALIDATION
# ============================================================


def validate_dataset(
    dataset: Dataset,
    *,
    require_numeric_features: bool = True,
    require_target: bool = False,
) -> list[str]:
    """
    Validate a dataset.

    Returns a list of validation errors.

    An empty list means the dataset is valid.
    """

    errors: list[str] = []

    if not isinstance(
        dataset,
        Dataset,
    ):
        return [
            "dataset must be a Dataset instance."
        ]

    if not dataset.rows:
        errors.append(
            "Dataset contains no rows."
        )
        return errors

    if require_target and not dataset.target_name:
        errors.append(
            "Dataset target_name is required."
        )

    for feature_name in dataset.feature_names:
        for index, row in enumerate(
            dataset.rows
        ):
            if feature_name not in row:
                errors.append(
                    f"Row {index} is missing "
                    f"feature '{feature_name}'."
                )
                continue

            if require_numeric_features:
                try:
                    _to_float(
                        row[feature_name],
                        feature_name,
                    )
                except ValueError as exc:
                    errors.append(
                        f"Row {index}: {exc}"
                    )

    if dataset.target_name:
        for index, row in enumerate(
            dataset.rows
        ):
            if dataset.target_name not in row:
                errors.append(
                    f"Row {index} is missing "
                    f"target '{dataset.target_name}'."
                )

    return errors


def is_valid_dataset(
    dataset: Dataset,
    *,
    require_numeric_features: bool = True,
    require_target: bool = False,
) -> bool:
    """Return True when the dataset passes validation."""

    return not validate_dataset(
        dataset,
        require_numeric_features=require_numeric_features,
        require_target=require_target,
    )


# ============================================================
# MISSING VALUE HANDLING
# ============================================================


def fill_missing_values(
    dataset: Dataset,
    *,
    strategy: str = "mean",
    value: float = 0.0,
) -> Dataset:
    """
    Fill missing or non-numeric feature values.

    Supported strategies:

        "mean"
        "median"
        "zero"
        "value"
        "forward"

    The target column is not modified.
    """

    if strategy not in {
        "mean",
        "median",
        "zero",
        "value",
        "forward",
    }:
        raise ValueError(
            "Unsupported missing-value strategy: "
            f"{strategy}"
        )

    rows = [
        dict(row)
        for row in dataset.rows
    ]

    statistics: dict[
        str,
        float,
    ] = {}

    for feature_name in dataset.feature_names:
        numeric_values: list[
            float
        ] = []

        for row in rows:
            if feature_name not in row:
                continue

            try:
                numeric = float(
                    row[feature_name]
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            if math.isfinite(
                numeric
            ):
                numeric_values.append(
                    numeric
                )

        if numeric_values:
            if strategy == "mean":
                statistics[
                    feature_name
                ] = (
                    sum(numeric_values)
                    / len(numeric_values)
                )

            elif strategy == "median":
                sorted_values = sorted(
                    numeric_values
                )

                middle = len(
                    sorted_values
                ) // 2

                if len(
                    sorted_values
                ) % 2 == 0:
                    statistics[
                        feature_name
                    ] = (
                        sorted_values[
                            middle - 1
                        ]
                        + sorted_values[
                            middle
                        ]
                    ) / 2.0

                else:
                    statistics[
                        feature_name
                    ] = sorted_values[
                        middle
                    ]

            elif strategy == "zero":
                statistics[
                    feature_name
                ] = 0.0

            elif strategy == "value":
                statistics[
                    feature_name
                ] = float(value)

            elif strategy == "forward":
                statistics[
                    feature_name
                ] = numeric_values[0]

        else:
            statistics[
                feature_name
            ] = (
                0.0
                if strategy != "value"
                else float(value)
            )

    previous_values: dict[
        str,
        float,
    ] = {}

    for row in rows:
        for feature_name in dataset.feature_names:
            raw_value = row.get(
                feature_name
            )

            try:
                numeric = float(
                    raw_value
                )

                valid = math.isfinite(
                    numeric
                )

            except (
                TypeError,
                ValueError,
            ):
                valid = False
                numeric = 0.0

            if valid:
                previous_values[
                    feature_name
                ] = numeric

                continue

            if strategy == "forward":
                replacement = previous_values.get(
                    feature_name,
                    statistics[
                        feature_name
                    ],
                )

            else:
                replacement = statistics[
                    feature_name
                ]

            row[
                feature_name
            ] = replacement

    return Dataset(
        rows=rows,
        feature_names=list(
            dataset.feature_names
        ),
        target_name=dataset.target_name,
        metadata={
            **dataset.metadata,
            "missing_values_filled": True,
            "missing_value_strategy": strategy,
        },
    )


# ============================================================
# TRAIN / VALIDATION / TEST SPLIT
# ============================================================


def split_dataset(
    dataset: Dataset,
    *,
    train_ratio: float = DEFAULT_TRAIN_RATIO,
    validation_ratio: float = DEFAULT_VALIDATION_RATIO,
    test_ratio: float = DEFAULT_TEST_RATIO,
    shuffle: bool = True,
    random_seed: int | None = 42,
) -> DatasetSplit:
    """
    Split a dataset into train, validation, and test sets.
    """

    train_ratio = _validate_ratio(
        train_ratio,
        "train_ratio",
    )

    validation_ratio = _validate_ratio(
        validation_ratio,
        "validation_ratio",
    )

    test_ratio = _validate_ratio(
        test_ratio,
        "test_ratio",
    )

    total_ratio = (
        train_ratio
        + validation_ratio
        + test_ratio
    )

    if abs(
        total_ratio - 1.0
    ) > 1e-9:
        raise ValueError(
            "train_ratio + validation_ratio + "
            "test_ratio must equal 1."
        )

    rows = [
        dict(row)
        for row in dataset.rows
    ]

    if shuffle:
        generator = random.Random(
            random_seed
        )

        generator.shuffle(
            rows
        )

    total = len(rows)

    train_count = int(
        total
        * train_ratio
    )

    validation_count = int(
        total
        * validation_ratio
    )

    train_rows = rows[
        :train_count
    ]

    validation_rows = rows[
        train_count:
        train_count
        + validation_count
    ]

    test_rows = rows[
        train_count
        + validation_count:
    ]

    def make_subset(
        subset_rows: list[dict[str, Any]],
        subset_name: str,
    ) -> Dataset:
        return Dataset(
            rows=subset_rows,
            feature_names=list(
                dataset.feature_names
            ),
            target_name=dataset.target_name,
            metadata={
                **dataset.metadata,
                "split": subset_name,
            },
        )

    return DatasetSplit(
        train=make_subset(
            train_rows,
            "train",
        ),
        validation=make_subset(
            validation_rows,
            "validation",
        ),
        test=make_subset(
            test_rows,
            "test",
        ),
        metadata={
            "train_ratio": train_ratio,
            "validation_ratio": validation_ratio,
            "test_ratio": test_ratio,
            "shuffle": shuffle,
            "random_seed": random_seed,
            "total_rows": total,
        },
    )


# ============================================================
# FEATURE SCALING
# ============================================================


def fit_scaler(
    dataset: Dataset,
) -> FeatureScaler:
    """
    Fit a min-max scaler using a dataset.

    The scaler should normally be fitted on the training set
    only, then applied to validation/test data.
    """

    minimums: dict[
        str,
        float,
    ] = {}

    maximums: dict[
        str,
        float,
    ] = {}

    for feature_name in dataset.feature_names:
        values: list[
            float
        ] = []

        for row in dataset.rows:
            if feature_name not in row:
                continue

            values.append(
                _to_float(
                    row[feature_name],
                    feature_name,
                )
            )

        if not values:
            raise ValueError(
                f"No numeric values found for "
                f"feature '{feature_name}'."
            )

        minimums[
            feature_name
        ] = min(values)

        maximums[
            feature_name
        ] = max(values)

    return FeatureScaler(
        minimums=minimums,
        maximums=maximums,
    )


def scale_dataset(
    dataset: Dataset,
    scaler: FeatureScaler | None = None,
) -> tuple[
    Dataset,
    FeatureScaler,
]:
    """
    Scale a dataset using a supplied scaler or fit a new one.
    """

    active_scaler = (
        scaler
        if scaler is not None
        else fit_scaler(dataset)
    )

    return (
        active_scaler.transform_dataset(
            dataset
        ),
        active_scaler,
    )


# ============================================================
# BINARY TARGET PREPARATION
# ============================================================


def prepare_binary_target(
    dataset: Dataset,
    *,
    positive_values: Iterable[Any] = (1, True, "1", "true", "True"),
) -> Dataset:
    """
    Convert the dataset target into 0/1 labels.

    Values in positive_values become 1.
    All other values become 0.
    """

    if not dataset.target_name:
        raise ValueError(
            "Dataset target_name is required."
        )

    positive_set = {
        str(value).lower()
        for value in positive_values
    }

    rows: list[
        dict[str, Any]
    ] = []

    for row in dataset.rows:
        new_row = dict(
            row
        )

        target_value = new_row[
            dataset.target_name
        ]

        is_positive = (
            str(
                target_value
            ).lower()
            in positive_set
        )

        new_row[
            dataset.target_name
        ] = int(
            is_positive
        )

        rows.append(
            new_row
        )

    return Dataset(
        rows=rows,
        feature_names=list(
            dataset.feature_names
        ),
        target_name=dataset.target_name,
        metadata={
            **dataset.metadata,
            "target_type": "binary",
        },
    )


# ============================================================
# REGRESSION TARGET PREPARATION
# ============================================================


def prepare_numeric_target(
    dataset: Dataset,
) -> Dataset:
    """
    Convert the target column into finite floating-point values.
    """

    if not dataset.target_name:
        raise ValueError(
            "Dataset target_name is required."
        )

    target_name = dataset.target_name

    rows: list[
        dict[str, Any]
    ] = []

    for index, row in enumerate(
        dataset.rows
    ):
        new_row = dict(
            row
        )

        new_row[
            target_name
        ] = _to_float(
            row[target_name],
            f"target at row {index}",
        )

        rows.append(
            new_row
        )

    return Dataset(
        rows=rows,
        feature_names=list(
            dataset.feature_names
        ),
        target_name=target_name,
        metadata={
            **dataset.metadata,
            "target_type": "numeric",
        },
    )


# ============================================================
# DATASET SUMMARY
# ============================================================


def dataset_summary(
    dataset: Dataset,
) -> dict[str, Any]:
    """
    Generate descriptive statistics for numeric features.
    """

    summary: dict[
        str,
        Any,
    ] = {
        "row_count": dataset.size,
        "feature_count": len(
            dataset.feature_names
        ),
        "feature_names": list(
            dataset.feature_names
        ),
        "target_name": dataset.target_name,
        "features": {},
    }

    for feature_name in dataset.feature_names:
        values: list[
            float
        ] = []

        missing = 0

        for row in dataset.rows:
            if feature_name not in row:
                missing += 1
                continue

            try:
                numeric = float(
                    row[feature_name]
                )
            except (
                TypeError,
                ValueError,
            ):
                missing += 1
                continue

            if not math.isfinite(
                numeric
            ):
                missing += 1
                continue

            values.append(
                numeric
            )

        if values:
            mean = (
                sum(values)
                / len(values)
            )

            variance = (
                sum(
                    (
                        value
                        - mean
                    )
                    ** 2
                    for value in values
                )
                / len(values)
            )

            summary[
                "features"
            ][feature_name] = {
                "count": len(values),
                "missing": missing,
                "minimum": min(values),
                "maximum": max(values),
                "mean": mean,
                "standard_deviation": math.sqrt(
                    variance
                ),
            }

        else:
            summary[
                "features"
            ][feature_name] = {
                "count": 0,
                "missing": missing,
                "minimum": None,
                "maximum": None,
                "mean": None,
                "standard_deviation": None,
            }

    return summary


# ============================================================
# DATASET SHUFFLING
# ============================================================


def shuffle_dataset(
    dataset: Dataset,
    *,
    random_seed: int | None = 42,
) -> Dataset:
    """
    Return a shuffled copy of the dataset.
    """

    rows = [
        dict(row)
        for row in dataset.rows
    ]

    generator = random.Random(
        random_seed
    )

    generator.shuffle(
        rows
    )

    return Dataset(
        rows=rows,
        feature_names=list(
            dataset.feature_names
        ),
        target_name=dataset.target_name,
        metadata={
            **dataset.metadata,
            "shuffled": True,
            "random_seed": random_seed,
        },
    )


# ============================================================
# DATASET LIMITING
# ============================================================


def limit_dataset(
    dataset: Dataset,
    max_rows: int,
) -> Dataset:
    """
    Return a copy containing at most max_rows rows.
    """

    if max_rows < 0:
        raise ValueError(
            "max_rows cannot be negative."
        )

    return Dataset(
        rows=[
            dict(row)
            for row in dataset.rows[
                :max_rows
            ]
        ],
        feature_names=list(
            dataset.feature_names
        ),
        target_name=dataset.target_name,
        metadata={
            **dataset.metadata,
            "limited": True,
            "max_rows": max_rows,
        },
    )


# ============================================================
# DATASET CONCATENATION
# ============================================================


def concatenate_datasets(
    datasets: Iterable[Dataset],
) -> Dataset:
    """
    Concatenate multiple compatible datasets.
    """

    dataset_list = list(
        datasets
    )

    if not dataset_list:
        return Dataset()

    first = dataset_list[0]

    feature_names = list(
        first.feature_names
    )

    target_name = first.target_name

    rows: list[
        dict[str, Any]
    ] = []

    for index, dataset in enumerate(
        dataset_list
    ):
        if (
            dataset.feature_names
            != feature_names
        ):
            raise ValueError(
                f"Dataset {index} has "
                "different feature names."
            )

        if dataset.target_name != target_name:
            raise ValueError(
                f"Dataset {index} has "
                "a different target name."
            )

        rows.extend(
            dict(row)
            for row in dataset.rows
        )

    return Dataset(
        rows=rows,
        feature_names=feature_names,
        target_name=target_name,
        metadata={
            "source_dataset_count": len(
                dataset_list
            ),
        },
    )


# ============================================================
# CONVERSION UTILITIES
# ============================================================


def rows_to_feature_target(
    rows: Iterable[Mapping[str, Any]],
    feature_names: Sequence[str],
    target_name: str,
) -> tuple[
    list[list[float]],
    list[Any],
]:
    """
    Convert raw rows directly into feature and target arrays.
    """

    dataset = create_dataset(
        rows,
        feature_names=feature_names,
        target_name=target_name,
    )

    return (
        extract_features(
            dataset
        ),
        extract_target(
            dataset
        ),
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Dataset",
    "DatasetSplit",
    "FeatureScaler",
    "create_dataset",
    "extract_features",
    "extract_target",
    "infer_numeric_features",
    "validate_dataset",
    "is_valid_dataset",
    "fill_missing_values",
    "split_dataset",
    "fit_scaler",
    "scale_dataset",
    "prepare_binary_target",
    "prepare_numeric_target",
    "dataset_summary",
    "shuffle_dataset",
    "limit_dataset",
    "concatenate_datasets",
    "rows_to_feature_target",
]