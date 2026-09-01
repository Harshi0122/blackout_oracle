"""
Blackout Oracle - Simulation Verification.

Provides validation and consistency checks for simulation inputs,
outputs, and digital-twin states.

The verification layer is intentionally deterministic and
solver-agnostic. It can be used before and after simulations to
catch invalid values, inconsistent states, and physically
suspicious results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Any, Iterable

from app.simulation.base import (
    SimulationResult,
    SimulationState,
)


# ============================================================
# ENUMS
# ============================================================


class VerificationSeverity(str, Enum):
    """Severity of a verification finding."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class VerificationStatus(str, Enum):
    """Overall verification status."""

    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"


# ============================================================
# FINDING
# ============================================================


@dataclass
class VerificationFinding:
    """
    A single verification finding.
    """

    code: str

    message: str

    severity: VerificationSeverity = (
        VerificationSeverity.WARNING
    )

    field: str | None = None

    asset_id: int | None = None

    expected: Any = None

    actual: Any = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def is_error(self) -> bool:
        """Return whether the finding represents an error."""

        return self.severity in {
            VerificationSeverity.ERROR,
            VerificationSeverity.CRITICAL,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize the finding."""

        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "field": self.field,
            "asset_id": self.asset_id,
            "expected": self.expected,
            "actual": self.actual,
            "metadata": dict(self.metadata),
        }


# ============================================================
# VERIFICATION RESULT
# ============================================================


@dataclass
class VerificationResult:
    """
    Result of a verification operation.
    """

    status: VerificationStatus

    findings: list[VerificationFinding] = field(
        default_factory=list
    )

    checks_performed: int = 0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def passed(self) -> bool:
        """Return True if no errors were found."""

        return self.status != VerificationStatus.FAILED

    @property
    def has_warnings(self) -> bool:
        """Return whether warnings were found."""

        return any(
            finding.severity
            == VerificationSeverity.WARNING
            for finding in self.findings
        )

    @property
    def errors(self) -> list[VerificationFinding]:
        """Return error and critical findings."""

        return [
            finding
            for finding in self.findings
            if finding.is_error
        ]

    @property
    def warnings(self) -> list[VerificationFinding]:
        """Return warning findings."""

        return [
            finding
            for finding in self.findings
            if finding.severity
            == VerificationSeverity.WARNING
        ]

    def add(
        self,
        finding: VerificationFinding,
    ) -> None:
        """Add a finding."""

        self.findings.append(
            finding
        )

    def finalize(self) -> "VerificationResult":
        """Calculate the final verification status."""

        if any(
            finding.is_error
            for finding in self.findings
        ):
            self.status = VerificationStatus.FAILED

        elif any(
            finding.severity
            == VerificationSeverity.WARNING
            for finding in self.findings
        ):
            self.status = (
                VerificationStatus.PASSED_WITH_WARNINGS
            )

        else:
            self.status = VerificationStatus.PASSED

        return self

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result."""

        return {
            "status": self.status.value,
            "passed": self.passed,
            "has_warnings": self.has_warnings,
            "checks_performed": self.checks_performed,
            "finding_count": len(
                self.findings
            ),
            "error_count": len(
                self.errors
            ),
            "warning_count": len(
                self.warnings
            ),
            "findings": [
                finding.to_dict()
                for finding in self.findings
            ],
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# VERIFICATION CONFIG
# ============================================================


@dataclass
class VerificationConfig:
    """
    Thresholds used by the verification engine.
    """

    voltage_min_pu: float = 0.90

    voltage_max_pu: float = 1.10

    voltage_critical_min_pu: float = 0.80

    voltage_critical_max_pu: float = 1.20

    frequency_min_hz: float = 49.0

    frequency_max_hz: float = 51.0

    frequency_critical_min_hz: float = 48.0

    frequency_critical_max_hz: float = 52.0

    loading_warning_percent: float = 80.0

    loading_max_percent: float = 100.0

    loading_critical_percent: float = 120.0

    maximum_negative_generation_mw: float = 0.001

    allow_isolated_assets: bool = True

    require_timestamp: bool = True

    require_finite_values: bool = True

    check_power_balance: bool = True

    power_balance_tolerance_mw: float = 5.0

    fail_on_critical: bool = True

    fail_on_error: bool = True

    def __post_init__(self) -> None:
        self.voltage_min_pu = float(
            self.voltage_min_pu
        )

        self.voltage_max_pu = float(
            self.voltage_max_pu
        )

        self.voltage_critical_min_pu = float(
            self.voltage_critical_min_pu
        )

        self.voltage_critical_max_pu = float(
            self.voltage_critical_max_pu
        )

        self.frequency_min_hz = float(
            self.frequency_min_hz
        )

        self.frequency_max_hz = float(
            self.frequency_max_hz
        )

        self.frequency_critical_min_hz = float(
            self.frequency_critical_min_hz
        )

        self.frequency_critical_max_hz = float(
            self.frequency_critical_max_hz
        )

        self.loading_warning_percent = max(
            0.0,
            float(
                self.loading_warning_percent
            ),
        )

        self.loading_max_percent = max(
            self.loading_warning_percent,
            float(
                self.loading_max_percent
            ),
        )

        self.loading_critical_percent = max(
            self.loading_max_percent,
            float(
                self.loading_critical_percent
            ),
        )

        self.power_balance_tolerance_mw = max(
            0.0,
            float(
                self.power_balance_tolerance_mw
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the configuration."""

        return {
            "voltage_min_pu": self.voltage_min_pu,
            "voltage_max_pu": self.voltage_max_pu,
            "voltage_critical_min_pu": (
                self.voltage_critical_min_pu
            ),
            "voltage_critical_max_pu": (
                self.voltage_critical_max_pu
            ),
            "frequency_min_hz": self.frequency_min_hz,
            "frequency_max_hz": self.frequency_max_hz,
            "frequency_critical_min_hz": (
                self.frequency_critical_min_hz
            ),
            "frequency_critical_max_hz": (
                self.frequency_critical_max_hz
            ),
            "loading_warning_percent": (
                self.loading_warning_percent
            ),
            "loading_max_percent": (
                self.loading_max_percent
            ),
            "loading_critical_percent": (
                self.loading_critical_percent
            ),
            "maximum_negative_generation_mw": (
                self.maximum_negative_generation_mw
            ),
            "allow_isolated_assets": (
                self.allow_isolated_assets
            ),
            "require_timestamp": (
                self.require_timestamp
            ),
            "require_finite_values": (
                self.require_finite_values
            ),
            "check_power_balance": (
                self.check_power_balance
            ),
            "power_balance_tolerance_mw": (
                self.power_balance_tolerance_mw
            ),
            "fail_on_critical": self.fail_on_critical,
            "fail_on_error": self.fail_on_error,
        }


# ============================================================
# STATE VERIFIER
# ============================================================


class SimulationVerifier:
    """
    Deterministic verifier for SimulationState objects.
    """

    def __init__(
        self,
        config: VerificationConfig | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else VerificationConfig()
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def verify_state(
        self,
        state: SimulationState,
    ) -> VerificationResult:
        """
        Verify a SimulationState.

        Checks:

        - timestamp validity,
        - finite numeric values,
        - asset-key consistency,
        - voltage limits,
        - frequency limits,
        - loading limits,
        - failed/overloaded consistency,
        - power balance,
        - metadata consistency.
        """

        result = VerificationResult(
            status=VerificationStatus.PASSED
        )

        self._check_timestamp(
            state,
            result,
        )

        self._check_numeric_values(
            state,
            result,
        )

        self._check_asset_consistency(
            state,
            result,
        )

        self._check_voltage(
            state,
            result,
        )

        self._check_frequency(
            state,
            result,
        )

        self._check_loading(
            state,
            result,
        )

        self._check_status_sets(
            state,
            result,
        )

        if self.config.check_power_balance:
            self._check_power_balance(
                state,
                result,
            )

        self._check_metadata(
            state,
            result,
        )

        result.checks_performed = (
            len(result.findings)
        )

        result.metadata[
            "verification_type"
        ] = "simulation_state"

        result.metadata[
            "config"
        ] = self.config.to_dict()

        return result.finalize()

    # ========================================================
    # TIMESTAMP
    # ========================================================

    def _check_timestamp(
        self,
        state: SimulationState,
        result: VerificationResult,
    ) -> None:
        """Verify simulation timestamp."""

        if not self.config.require_timestamp:
            return

        if state.timestamp is None:
            result.add(
                VerificationFinding(
                    code="MISSING_TIMESTAMP",
                    message=(
                        "Simulation state has no timestamp."
                    ),
                    severity=VerificationSeverity.ERROR,
                    field="timestamp",
                )
            )
            return

        if not hasattr(
            state.timestamp,
            "tzinfo",
        ):
            result.add(
                VerificationFinding(
                    code="INVALID_TIMESTAMP",
                    message=(
                        "Simulation timestamp is not a valid "
                        "datetime object."
                    ),
                    severity=VerificationSeverity.ERROR,
                    field="timestamp",
                    actual=state.timestamp,
                )
            )

    # ========================================================
    # NUMERIC VALUES
    # ========================================================

    def _check_numeric_values(
        self,
        state: SimulationState,
        result: VerificationResult,
    ) -> None:
        """Check for NaN and infinite values."""

        if not self.config.require_finite_values:
            return

        numeric_maps = {
            "loading": state.loading,
            "voltage": state.voltage,
            "frequency": state.frequency,
            "active_power": state.active_power,
            "reactive_power": state.reactive_power,
        }

        for field_name, values in numeric_maps.items():
            for asset_id, value in values.items():
                if value is None:
                    continue

                try:
                    finite = isfinite(
                        float(value)
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    finite = False

                if not finite:
                    result.add(
                        VerificationFinding(
                            code="NON_FINITE_VALUE",
                            message=(
                                f"{field_name} contains a "
                                "non-finite value."
                            ),
                            severity=VerificationSeverity.ERROR,
                            field=field_name,
                            asset_id=int(asset_id),
                            actual=value,
                        )
                    )

    # ========================================================
    # ASSET CONSISTENCY
    # ========================================================

    def _check_asset_consistency(
        self,
        state: SimulationState,
        result: VerificationResult,
    ) -> None:
        """Check consistency between state dictionaries."""

        all_maps = [
            state.asset_status,
            state.loading,
            state.voltage,
            state.frequency,
            state.active_power,
            state.reactive_power,
        ]

        known_ids: set[int] = set()

        for mapping in all_maps:
            known_ids.update(
                int(asset_id)
                for asset_id in mapping.keys()
            )

        known_ids.update(
            int(asset_id)
            for asset_id in state.failed_assets
        )

        known_ids.update(
            int(asset_id)
            for asset_id in state.overloaded_assets
        )

        known_ids.update(
            int(asset_id)
            for asset_id in state.islanded_assets
        )

        if not known_ids:
            result.add(
                VerificationFinding(
                    code="EMPTY_STATE",
                    message=(
                        "Simulation state contains no asset "
                        "information."
                    ),
                    severity=VerificationSeverity.WARNING,
                )
            )

    # ========================================================
    # VOLTAGE
    # ========================================================

    def _check_voltage(
        self,
        state: SimulationState,
        result: VerificationResult,
    ) -> None:
        """Verify voltage levels."""

        for asset_id, value in state.voltage.items():
            if value is None:
                continue

            try:
                voltage = float(
                    value
                )
            except (
                TypeError,
                ValueError,
            ):
                result.add(
                    VerificationFinding(
                        code="INVALID_VOLTAGE",
                        message=(
                            "Voltage is not numeric."
                        ),
                        severity=VerificationSeverity.ERROR,
                        field="voltage",
                        asset_id=int(asset_id),
                        actual=value,
                    )
                )
                continue

            if (
                voltage
                < self.config.voltage_critical_min_pu
                or voltage
                > self.config.voltage_critical_max_pu
            ):
                result.add(
                    VerificationFinding(
                        code="CRITICAL_VOLTAGE",
                        message=(
                            f"Voltage {voltage:.4f} pu is "
                            "outside the critical operating range."
                        ),
                        severity=VerificationSeverity.CRITICAL,
                        field="voltage",
                        asset_id=int(asset_id),
                        expected=(
                            self.config.voltage_critical_min_pu,
                            self.config.voltage_critical_max_pu,
                        ),
                        actual=voltage,
                    )
                )

            elif (
                voltage
                < self.config.voltage_min_pu
                or voltage
                > self.config.voltage_max_pu
            ):
                result.add(
                    VerificationFinding(
                        code="VOLTAGE_LIMIT",
                        message=(
                            f"Voltage {voltage:.4f} pu is "
                            "outside the normal operating range."
                        ),
                        severity=VerificationSeverity.WARNING,
                        field="voltage",
                        asset_id=int(asset_id),
                        expected=(
                            self.config.voltage_min_pu,
                            self.config.voltage_max_pu,
                        ),
                        actual=voltage,
                    )
                )

    # ========================================================
    # FREQUENCY
    # ========================================================

    def _check_frequency(
        self,
        state: SimulationState,
        result: VerificationResult,
    ) -> None:
        """Verify system frequency."""

        for asset_id, value in state.frequency.items():
            if value is None:
                continue

            try:
                frequency = float(
                    value
                )
            except (
                TypeError,
                ValueError,
            ):
                result.add(
                    VerificationFinding(
                        code="INVALID_FREQUENCY",
                        message=(
                            "Frequency is not numeric."
                        ),
                        severity=VerificationSeverity.ERROR,
                        field="frequency",
                        asset_id=int(asset_id),
                        actual=value,
                    )
                )
                continue

            if (
                frequency
                < self.config.frequency_critical_min_hz
                or frequency
                > self.config.frequency_critical_max_hz
            ):
                result.add(
                    VerificationFinding(
                        code="CRITICAL_FREQUENCY",
                        message=(
                            f"Frequency {frequency:.3f} Hz "
                            "is outside the critical range."
                        ),
                        severity=VerificationSeverity.CRITICAL,
                        field="frequency",
                        asset_id=int(asset_id),
                        expected=(
                            self.config.frequency_critical_min_hz,
                            self.config.frequency_critical_max_hz,
                        ),
                        actual=frequency,
                    )
                )

            elif (
                frequency
                < self.config.frequency_min_hz
                or frequency
                > self.config.frequency_max_hz
            ):
                result.add(
                    VerificationFinding(
                        code="FREQUENCY_LIMIT",
                        message=(
                            f"Frequency {frequency:.3f} Hz "
                            "is outside the normal operating range."
                        ),
                        severity=VerificationSeverity.WARNING,
                        field="frequency",
                        asset_id=int(asset_id),
                        expected=(
                            self.config.frequency_min_hz,
                            self.config.frequency_max_hz,
                        ),
                        actual=frequency,
                    )
                )

    # ========================================================
    # LOADING
    # ========================================================

    def _check_loading(
        self,
        state: SimulationState,
        result: VerificationResult,
    ) -> None:
        """Verify asset loading."""

        for asset_id, value in state.loading.items():
            if value is None:
                continue

            try:
                loading = float(
                    value
                )
            except (
                TypeError,
                ValueError,
            ):
                result.add(
                    VerificationFinding(
                        code="INVALID_LOADING",
                        message=(
                            "Loading value is not numeric."
                        ),
                        severity=VerificationSeverity.ERROR,
                        field="loading",
                        asset_id=int(asset_id),
                        actual=value,
                    )
                )
                continue

            if loading < 0.0:
                result.add(
                    VerificationFinding(
                        code="NEGATIVE_LOADING",
                        message=(
                            "Asset loading cannot be negative."
                        ),
                        severity=VerificationSeverity.ERROR,
                        field="loading",
                        asset_id=int(asset_id),
                        expected=">= 0",
                        actual=loading,
                    )
                )
                continue

            if (
                loading
                >= self.config.loading_critical_percent
            ):
                result.add(
                    VerificationFinding(
                        code="CRITICAL_OVERLOAD",
                        message=(
                            f"Loading {loading:.2f}% exceeds "
                            "the critical threshold."
                        ),
                        severity=VerificationSeverity.CRITICAL,
                        field="loading",
                        asset_id=int(asset_id),
                        expected=(
                            f"< {self.config.loading_critical_percent}%"
                        ),
                        actual=loading,
                    )
                )

            elif (
                loading
                > self.config.loading_max_percent
            ):
                result.add(
                    VerificationFinding(
                        code="OVERLOAD",
                        message=(
                            f"Loading {loading:.2f}% exceeds "
                            "the permitted maximum."
                        ),
                        severity=VerificationSeverity.ERROR,
                        field="loading",
                        asset_id=int(asset_id),
                        expected=(
                            f"<= {self.config.loading_max_percent}%"
                        ),
                        actual=loading,
                    )
                )

            elif (
                loading
                >= self.config.loading_warning_percent
            ):
                result.add(
                    VerificationFinding(
                        code="HIGH_LOADING",
                        message=(
                            f"Loading {loading:.2f}% is "
                            "approaching the operational limit."
                        ),
                        severity=VerificationSeverity.WARNING,
                        field="loading",
                        asset_id=int(asset_id),
                        actual=loading,
                    )
                )

    # ========================================================
    # STATUS SETS
    # ========================================================

    def _check_status_sets(
        self,
        state: SimulationState,
        result: VerificationResult,
    ) -> None:
        """Verify failed and overloaded asset sets."""

        for asset_id in state.failed_assets:
            if asset_id not in state.asset_status:
                result.add(
                    VerificationFinding(
                        code="FAILED_ASSET_MISSING_STATUS",
                        message=(
                            "Asset is marked failed but has "
                            "no corresponding status entry."
                        ),
                        severity=VerificationSeverity.WARNING,
                        asset_id=int(asset_id),
                    )
                )

        for asset_id in state.overloaded_assets:
            loading = state.loading.get(
                asset_id
            )

            if loading is None:
                result.add(
                    VerificationFinding(
                        code="OVERLOADED_ASSET_MISSING_LOADING",
                        message=(
                            "Asset is marked overloaded but "
                            "has no loading measurement."
                        ),
                        severity=VerificationSeverity.WARNING,
                        asset_id=int(asset_id),
                    )
                )

            elif (
                float(loading)
                < self.config.loading_max_percent
            ):
                result.add(
                    VerificationFinding(
                        code="OVERLOAD_FLAG_INCONSISTENT",
                        message=(
                            "Asset is marked overloaded but "
                            "its loading is below the overload limit."
                        ),
                        severity=VerificationSeverity.WARNING,
                        asset_id=int(asset_id),
                        expected=(
                            f">= {self.config.loading_max_percent}%"
                        ),
                        actual=loading,
                    )
                )

        if not self.config.allow_isolated_assets:
            for asset_id in state.islanded_assets:
                result.add(
                    VerificationFinding(
                        code="ISLANDED_ASSET",
                        message=(
                            "Islanded assets are not allowed "
                            "by the verification configuration."
                        ),
                        severity=VerificationSeverity.ERROR,
                        asset_id=int(asset_id),
                    )
                )

    # ========================================================
    # POWER BALANCE
    # ========================================================

    def _check_power_balance(
        self,
        state: SimulationState,
        result: VerificationResult,
    ) -> None:
        """
        Check aggregate active-power balance when enough information
        is available.

        The calculation is intentionally conservative because
        SimulationState does not necessarily distinguish generators
        from loads. If explicit totals are supplied in metadata,
        they are preferred.
        """

        metadata = state.metadata

        generation = self._metadata_number(
            metadata,
            (
                "generation_mw",
                "total_generation_mw",
                "generated_mw",
            ),
        )

        load = self._metadata_number(
            metadata,
            (
                "load_mw",
                "total_load_mw",
                "demand_mw",
            ),
        )

        if (
            generation is None
            or load is None
        ):
            return

        if generation < 0.0:
            result.add(
                VerificationFinding(
                    code="NEGATIVE_GENERATION",
                    message=(
                        "Reported generation is negative."
                    ),
                    severity=VerificationSeverity.ERROR,
                    field="generation_mw",
                    actual=generation,
                )
            )

        if load < 0.0:
            result.add(
                VerificationFinding(
                    code="NEGATIVE_LOAD",
                    message=(
                        "Reported load is negative."
                    ),
                    severity=VerificationSeverity.ERROR,
                    field="load_mw",
                    actual=load,
                )
            )

        balance = generation - load

        # A perfect zero is not expected in a real grid because
        # losses and measurement tolerances exist.
        if abs(balance) > self.config.power_balance_tolerance_mw:
            result.add(
                VerificationFinding(
                    code="POWER_IMBALANCE",
                    message=(
                        "Generation and load totals differ "
                        "beyond the configured tolerance."
                    ),
                    severity=VerificationSeverity.WARNING,
                    field="power_balance_mw",
                    expected=(
                        f"<= ±{self.config.power_balance_tolerance_mw}"
                    ),
                    actual=balance,
                    metadata={
                        "generation_mw": generation,
                        "load_mw": load,
                    },
                )
            )

    @staticmethod
    def _metadata_number(
        metadata: dict[str, Any],
        keys: tuple[str, ...],
    ) -> float | None:
        """Return the first usable numeric metadata value."""

        for key in keys:
            if key not in metadata:
                continue

            try:
                value = float(
                    metadata[key]
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            if isfinite(value):
                return value

        return None

    # ========================================================
    # METADATA
    # ========================================================

    def _check_metadata(
        self,
        state: SimulationState,
        result: VerificationResult,
    ) -> None:
        """Check known metadata fields."""

        converged = state.metadata.get(
            "pandapower_converged"
        )

        if converged is False:
            result.add(
                VerificationFinding(
                    code="POWER_FLOW_NOT_CONVERGED",
                    message=(
                        "The power-flow solver did not converge."
                    ),
                    severity=VerificationSeverity.CRITICAL,
                    field="pandapower_converged",
                    expected=True,
                    actual=False,
                )
            )

        risk_score = state.metadata.get(
            "risk_score"
        )

        if risk_score is not None:
            try:
                risk = float(
                    risk_score
                )

                if (
                    not isfinite(risk)
                    or risk < 0.0
                    or risk > 100.0
                ):
                    result.add(
                        VerificationFinding(
                            code="INVALID_RISK_SCORE",
                            message=(
                                "Risk score must be a finite "
                                "value between 0 and 100."
                            ),
                            severity=VerificationSeverity.ERROR,
                            field="risk_score",
                            expected="0..100",
                            actual=risk_score,
                        )
                    )

            except (
                TypeError,
                ValueError,
            ):
                result.add(
                    VerificationFinding(
                        code="INVALID_RISK_SCORE",
                        message=(
                            "Risk score is not numeric."
                        ),
                        severity=VerificationSeverity.ERROR,
                        field="risk_score",
                        actual=risk_score,
                    )
                )


# ============================================================
# RESULT VERIFIER
# ============================================================


class SimulationResultVerifier:
    """
    Verifier for complete SimulationResult objects.
    """

    def __init__(
        self,
        state_verifier: SimulationVerifier | None = None,
    ) -> None:
        self.state_verifier = (
            state_verifier
            if state_verifier is not None
            else SimulationVerifier()
        )

    def verify(
        self,
        result: SimulationResult,
    ) -> VerificationResult:
        """
        Verify a complete simulation result.
        """

        verification = VerificationResult(
            status=VerificationStatus.PASSED
        )

        final_state = getattr(
            result,
            "final_state",
            None,
        )

        if final_state is None:
            verification.add(
                VerificationFinding(
                    code="MISSING_FINAL_STATE",
                    message=(
                        "Simulation result does not contain "
                        "a final state."
                    ),
                    severity=VerificationSeverity.ERROR,
                    field="final_state",
                )
            )

        else:
            state_result = (
                self.state_verifier.verify_state(
                    final_state
                )
            )

            verification.findings.extend(
                state_result.findings
            )

            verification.checks_performed += (
                state_result.checks_performed
            )

        self._check_result_metadata(
            result,
            verification,
        )

        self._check_result_consistency(
            result,
            verification,
        )

        verification.metadata[
            "verification_type"
        ] = "simulation_result"

        return verification.finalize()

    # ========================================================
    # RESULT METADATA
    # ========================================================

    def _check_result_metadata(
        self,
        result: SimulationResult,
        verification: VerificationResult,
    ) -> None:
        """Verify common SimulationResult fields."""

        simulation_id = getattr(
            result,
            "simulation_id",
            None,
        )

        if simulation_id is None:
            verification.add(
                VerificationFinding(
                    code="MISSING_SIMULATION_ID",
                    message=(
                        "Simulation result has no simulation ID."
                    ),
                    severity=VerificationSeverity.WARNING,
                    field="simulation_id",
                )
            )

        status = getattr(
            result,
            "status",
            None,
        )

        if status is None:
            verification.add(
                VerificationFinding(
                    code="MISSING_SIMULATION_STATUS",
                    message=(
                        "Simulation result has no status."
                    ),
                    severity=VerificationSeverity.WARNING,
                    field="status",
                )
            )

    # ========================================================
    # CONSISTENCY
    # ========================================================

    def _check_result_consistency(
        self,
        result: SimulationResult,
        verification: VerificationResult,
    ) -> None:
        """Check consistency between result flags and final state."""

        final_state = getattr(
            result,
            "final_state",
            None,
        )

        if final_state is None:
            return

        blackout_detected = getattr(
            result,
            "blackout_detected",
            None,
        )

        if blackout_detected is True:
            if (
                not final_state.failed_assets
                and not final_state.islanded_assets
                and not final_state.overloaded_assets
            ):
                verification.add(
                    VerificationFinding(
                        code="BLACKOUT_FLAG_INCONSISTENT",
                        message=(
                            "Result reports a blackout but "
                            "the final state contains no failed, "
                            "islanded, or overloaded assets."
                        ),
                        severity=VerificationSeverity.WARNING,
                    )
                )

        cascade_detected = getattr(
            result,
            "cascade_detected",
            None,
        )

        if cascade_detected is True:
            if len(
                final_state.failed_assets
            ) < 2:
                verification.add(
                    VerificationFinding(
                        code="CASCADE_FLAG_INCONSISTENT",
                        message=(
                            "Result reports a cascade but fewer "
                            "than two failed assets are present."
                        ),
                        severity=VerificationSeverity.WARNING,
                    )
                )


# ============================================================
# COMPARISON VERIFIER
# ============================================================


@dataclass
class StateComparison:
    """
    Comparison between two simulation states.
    """

    changed_assets: list[int] = field(
        default_factory=list
    )

    newly_failed: list[int] = field(
        default_factory=list
    )

    restored_assets: list[int] = field(
        default_factory=list
    )

    newly_overloaded: list[int] = field(
        default_factory=list
    )

    relieved_assets: list[int] = field(
        default_factory=list
    )

    voltage_changes: dict[int, float] = field(
        default_factory=dict
    )

    loading_changes: dict[int, float] = field(
        default_factory=dict
    )

    frequency_changes: dict[int, float] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the comparison."""

        return {
            "changed_assets": list(
                self.changed_assets
            ),
            "newly_failed": list(
                self.newly_failed
            ),
            "restored_assets": list(
                self.restored_assets
            ),
            "newly_overloaded": list(
                self.newly_overloaded
            ),
            "relieved_assets": list(
                self.relieved_assets
            ),
            "voltage_changes": dict(
                self.voltage_changes
            ),
            "loading_changes": dict(
                self.loading_changes
            ),
            "frequency_changes": dict(
                self.frequency_changes
            ),
            "metadata": dict(
                self.metadata
            ),
        }


class StateComparator:
    """
    Compare two SimulationState objects.
    """

    def compare(
        self,
        previous: SimulationState,
        current: SimulationState,
        *,
        tolerance: float = 1e-6,
    ) -> StateComparison:
        """Compare state changes."""

        tolerance = max(
            0.0,
            float(tolerance),
        )

        comparison = StateComparison()

        all_asset_ids = set(
            int(asset_id)
            for asset_id in previous.asset_status.keys()
        )

        all_asset_ids.update(
            int(asset_id)
            for asset_id in current.asset_status.keys()
        )

        all_asset_ids.update(
            int(asset_id)
            for asset_id in previous.loading.keys()
        )

        all_asset_ids.update(
            int(asset_id)
            for asset_id in current.loading.keys()
        )

        all_asset_ids.update(
            int(asset_id)
            for asset_id in previous.voltage.keys()
        )

        all_asset_ids.update(
            int(asset_id)
            for asset_id in current.voltage.keys()
        )

        previous_failed = set(
            int(asset_id)
            for asset_id in previous.failed_assets
        )

        current_failed = set(
            int(asset_id)
            for asset_id in current.failed_assets
        )

        previous_overloaded = set(
            int(asset_id)
            for asset_id in previous.overloaded_assets
        )

        current_overloaded = set(
            int(asset_id)
            for asset_id in current.overloaded_assets
        )

        comparison.newly_failed = sorted(
            current_failed
            - previous_failed
        )

        comparison.restored_assets = sorted(
            previous_failed
            - current_failed
        )

        comparison.newly_overloaded = sorted(
            current_overloaded
            - previous_overloaded
        )

        comparison.relieved_assets = sorted(
            previous_overloaded
            - current_overloaded
        )

        for asset_id in all_asset_ids:
            changed = False

            voltage_changed = (
                self._difference(
                    previous.voltage.get(
                        asset_id
                    ),
                    current.voltage.get(
                        asset_id
                    ),
                    tolerance,
                )
            )

            if voltage_changed:
                changed = True

                comparison.voltage_changes[
                    asset_id
                ] = (
                    self._safe_float(
                        current.voltage.get(
                            asset_id
                        )
                    )
                    - self._safe_float(
                        previous.voltage.get(
                            asset_id
                        )
                    )
                )

            loading_changed = (
                self._difference(
                    previous.loading.get(
                        asset_id
                    ),
                    current.loading.get(
                        asset_id
                    ),
                    tolerance,
                )
            )

            if loading_changed:
                changed = True

                comparison.loading_changes[
                    asset_id
                ] = (
                    self._safe_float(
                        current.loading.get(
                            asset_id
                        )
                    )
                    - self._safe_float(
                        previous.loading.get(
                            asset_id
                        )
                    )
                )

            frequency_changed = (
                self._difference(
                    previous.frequency.get(
                        asset_id
                    ),
                    current.frequency.get(
                        asset_id
                    ),
                    tolerance,
                )
            )

            if frequency_changed:
                changed = True

                comparison.frequency_changes[
                    asset_id
                ] = (
                    self._safe_float(
                        current.frequency.get(
                            asset_id
                        )
                    )
                    - self._safe_float(
                        previous.frequency.get(
                            asset_id
                        )
                    )
                )

            if asset_id in (
                current_failed
                ^ previous_failed
            ):
                changed = True

            if asset_id in (
                current_overloaded
                ^ previous_overloaded
            ):
                changed = True

            if changed:
                comparison.changed_assets.append(
                    asset_id
                )

        comparison.changed_assets = sorted(
            set(
                comparison.changed_assets
            )
        )

        comparison.metadata[
            "previous_timestamp"
        ] = (
            previous.timestamp.isoformat()
            if previous.timestamp is not None
            else None
        )

        comparison.metadata[
            "current_timestamp"
        ] = (
            current.timestamp.isoformat()
            if current.timestamp is not None
            else None
        )

        return comparison

    @staticmethod
    def _difference(
        first: Any,
        second: Any,
        tolerance: float,
    ) -> bool:
        """Return whether two numeric values differ materially."""

        if first is None and second is None:
            return False

        if first is None or second is None:
            return True

        try:
            return abs(
                float(first)
                - float(second)
            ) > tolerance
        except (
            TypeError,
            ValueError,
        ):
            return first != second

    @staticmethod
    def _safe_float(
        value: Any,
    ) -> float:
        """Convert a value to float safely."""

        if value is None:
            return 0.0

        try:
            return float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def verify_state(
    state: SimulationState,
    *,
    config: VerificationConfig | None = None,
) -> VerificationResult:
    """
    Verify a SimulationState.
    """

    verifier = SimulationVerifier(
        config=config
    )

    return verifier.verify_state(
        state
    )


def verify_result(
    result: SimulationResult,
    *,
    config: VerificationConfig | None = None,
) -> VerificationResult:
    """
    Verify a SimulationResult.
    """

    state_verifier = SimulationVerifier(
        config=config
    )

    verifier = SimulationResultVerifier(
        state_verifier=state_verifier
    )

    return verifier.verify(
        result
    )


def compare_states(
    previous: SimulationState,
    current: SimulationState,
    *,
    tolerance: float = 1e-6,
) -> StateComparison:
    """
    Compare two SimulationState objects.
    """

    comparator = StateComparator()

    return comparator.compare(
        previous,
        current,
        tolerance=tolerance,
    )


def is_state_valid(
    state: SimulationState,
    *,
    config: VerificationConfig | None = None,
) -> bool:
    """
    Return True when the state passes verification.
    """

    result = verify_state(
        state,
        config=config,
    )

    return result.passed


__all__ = [
    "VerificationSeverity",
    "VerificationStatus",
    "VerificationFinding",
    "VerificationResult",
    "VerificationConfig",
    "SimulationVerifier",
    "SimulationResultVerifier",
    "StateComparison",
    "StateComparator",
    "verify_state",
    "verify_result",
    "compare_states",
    "is_state_valid",
]