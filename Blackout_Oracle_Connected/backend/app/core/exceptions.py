"""
Blackout Oracle - Application Exceptions.

Centralized custom exceptions used throughout the backend.

The purpose of this module is to provide predictable, structured errors
for:

- API operations
- Grid telemetry
- Weather ingestion
- Risk analysis
- AI-agent operations
- Simulation
- Database operations
- External service integrations

These exceptions represent APPLICATION-LEVEL failures.

They do not execute, authorize, or control any real electrical-grid
operation.
"""

from __future__ import annotations

from typing import Any


# ============================================================
# BASE EXCEPTION
# ============================================================


class BlackoutOracleError(Exception):
    """
    Base exception for all Blackout Oracle application errors.
    """

    error_code: str = "BLACKOUT_ORACLE_ERROR"

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the exception into a serializable representation.
        """

        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# ============================================================
# CONFIGURATION ERRORS
# ============================================================


class ConfigurationError(BlackoutOracleError):
    """
    Raised when application configuration is invalid or incomplete.
    """

    error_code = "CONFIGURATION_ERROR"


class MissingConfigurationError(ConfigurationError):
    """
    Raised when a required configuration value is missing.
    """

    error_code = "MISSING_CONFIGURATION"

    def __init__(
        self,
        setting_name: str,
    ) -> None:
        super().__init__(
            f"Required configuration '{setting_name}' is missing.",
            details={
                "setting": setting_name,
            },
        )


# ============================================================
# DATABASE ERRORS
# ============================================================


class DatabaseError(BlackoutOracleError):
    """
    Base exception for database failures.
    """

    error_code = "DATABASE_ERROR"


class DatabaseConnectionError(DatabaseError):
    """
    Raised when the application cannot connect to the database.
    """

    error_code = "DATABASE_CONNECTION_ERROR"


class DatabaseQueryError(DatabaseError):
    """
    Raised when a database query fails.
    """

    error_code = "DATABASE_QUERY_ERROR"


# ============================================================
# TELEMETRY ERRORS
# ============================================================


class TelemetryError(BlackoutOracleError):
    """
    Base exception for telemetry-related failures.
    """

    error_code = "TELEMETRY_ERROR"


class TelemetryUnavailableError(TelemetryError):
    """
    Raised when telemetry cannot currently be obtained.
    """

    error_code = "TELEMETRY_UNAVAILABLE"


class TelemetryStaleError(TelemetryError):
    """
    Raised when telemetry is too old to safely use for current analysis.
    """

    error_code = "TELEMETRY_STALE"

    def __init__(
        self,
        age_seconds: float,
        threshold_seconds: float,
    ) -> None:
        super().__init__(
            (
                "Telemetry is stale and should not be treated as "
                "current grid state."
            ),
            details={
                "age_seconds": age_seconds,
                "threshold_seconds": threshold_seconds,
            },
        )


class TelemetryValidationError(TelemetryError):
    """
    Raised when incoming telemetry fails validation.
    """

    error_code = "TELEMETRY_VALIDATION_ERROR"


class TelemetrySourceError(TelemetryError):
    """
    Raised when an external telemetry source fails.
    """

    error_code = "TELEMETRY_SOURCE_ERROR"


# ============================================================
# WEATHER ERRORS
# ============================================================


class WeatherError(BlackoutOracleError):
    """
    Base exception for weather-related failures.
    """

    error_code = "WEATHER_ERROR"


class WeatherUnavailableError(WeatherError):
    """
    Raised when weather data cannot be obtained.
    """

    error_code = "WEATHER_UNAVAILABLE"


class WeatherStaleError(WeatherError):
    """
    Raised when weather information is too old for current analysis.
    """

    error_code = "WEATHER_STALE"


class WeatherValidationError(WeatherError):
    """
    Raised when weather data fails validation.
    """

    error_code = "WEATHER_VALIDATION_ERROR"


# ============================================================
# ASSET ERRORS
# ============================================================


class AssetError(BlackoutOracleError):
    """
    Base exception for grid-asset-related failures.
    """

    error_code = "ASSET_ERROR"


class AssetNotFoundError(AssetError):
    """
    Raised when a requested grid asset does not exist.
    """

    error_code = "ASSET_NOT_FOUND"

    def __init__(
        self,
        asset_id: str,
    ) -> None:
        super().__init__(
            f"Grid asset '{asset_id}' was not found.",
            details={
                "asset_id": asset_id,
            },
        )


class AssetValidationError(AssetError):
    """
    Raised when asset information is invalid.
    """

    error_code = "ASSET_VALIDATION_ERROR"


# ============================================================
# INCIDENT ERRORS
# ============================================================


class IncidentError(BlackoutOracleError):
    """
    Base exception for incident-management failures.
    """

    error_code = "INCIDENT_ERROR"


class IncidentNotFoundError(IncidentError):
    """
    Raised when an incident cannot be found.
    """

    error_code = "INCIDENT_NOT_FOUND"

    def __init__(
        self,
        incident_id: str,
    ) -> None:
        super().__init__(
            f"Incident '{incident_id}' was not found.",
            details={
                "incident_id": incident_id,
            },
        )


class InvalidIncidentStateError(IncidentError):
    """
    Raised when an invalid incident state transition is requested.
    """

    error_code = "INVALID_INCIDENT_STATE"


# ============================================================
# RISK ENGINE ERRORS
# ============================================================


class RiskEngineError(BlackoutOracleError):
    """
    Base exception for risk-engine failures.
    """

    error_code = "RISK_ENGINE_ERROR"


class RiskCalculationError(RiskEngineError):
    """
    Raised when risk calculation fails.
    """

    error_code = "RISK_CALCULATION_ERROR"


class InsufficientRiskDataError(RiskEngineError):
    """
    Raised when there is insufficient trustworthy data to calculate risk.
    """

    error_code = "INSUFFICIENT_RISK_DATA"


class RiskModelUnavailableError(RiskEngineError):
    """
    Raised when the configured risk model cannot be loaded or used.
    """

    error_code = "RISK_MODEL_UNAVAILABLE"


# ============================================================
# SIMULATION ERRORS
# ============================================================


class SimulationError(BlackoutOracleError):
    """
    Base exception for digital-twin simulation failures.
    """

    error_code = "SIMULATION_ERROR"


class SimulationNotFoundError(SimulationError):
    """
    Raised when a simulation does not exist.
    """

    error_code = "SIMULATION_NOT_FOUND"

    def __init__(
        self,
        simulation_id: str,
    ) -> None:
        super().__init__(
            f"Simulation '{simulation_id}' was not found.",
            details={
                "simulation_id": simulation_id,
            },
        )


class SimulationValidationError(SimulationError):
    """
    Raised when a simulation scenario is invalid.
    """

    error_code = "SIMULATION_VALIDATION_ERROR"


class SimulationExecutionError(SimulationError):
    """
    Raised when the simulation engine fails.
    """

    error_code = "SIMULATION_EXECUTION_ERROR"


class SimulationTimeoutError(SimulationError):
    """
    Raised when a simulation exceeds its allowed execution time.
    """

    error_code = "SIMULATION_TIMEOUT"


class SimulationConvergenceError(SimulationError):
    """
    Raised when the power-system simulation fails to converge.
    """

    error_code = "SIMULATION_CONVERGENCE_ERROR"


# ============================================================
# VERIFICATION ERRORS
# ============================================================


class VerificationError(BlackoutOracleError):
    """
    Base exception for simulation/recommendation verification failures.
    """

    error_code = "VERIFICATION_ERROR"


class VerificationFailedError(VerificationError):
    """
    Raised when a proposed scenario fails safety or validity verification.
    """

    error_code = "VERIFICATION_FAILED"


class InsufficientVerificationDataError(VerificationError):
    """
    Raised when there is not enough evidence to verify a scenario.
    """

    error_code = "INSUFFICIENT_VERIFICATION_DATA"


# ============================================================
# AI AGENT ERRORS
# ============================================================


class AgentError(BlackoutOracleError):
    """
    Base exception for AI-agent failures.
    """

    error_code = "AGENT_ERROR"


class AgentConfigurationError(AgentError):
    """
    Raised when the AI agent is incorrectly configured.
    """

    error_code = "AGENT_CONFIGURATION_ERROR"


class AgentUnavailableError(AgentError):
    """
    Raised when the AI service is unavailable.
    """

    error_code = "AGENT_UNAVAILABLE"


class AgentExecutionError(AgentError):
    """
    Raised when an agent workflow fails.
    """

    error_code = "AGENT_EXECUTION_ERROR"


class AgentToolError(AgentError):
    """
    Raised when an agent tool fails.
    """

    error_code = "AGENT_TOOL_ERROR"


class AgentSafetyError(AgentError):
    """
    Raised when an agent action violates a configured safety policy.
    """

    error_code = "AGENT_SAFETY_ERROR"


# ============================================================
# GEMINI ERRORS
# ============================================================


class GeminiError(AgentError):
    """
    Base exception for Gemini API failures.
    """

    error_code = "GEMINI_ERROR"


class GeminiAuthenticationError(GeminiError):
    """
    Raised when Gemini authentication fails.
    """

    error_code = "GEMINI_AUTHENTICATION_ERROR"


class GeminiRateLimitError(GeminiError):
    """
    Raised when the Gemini API rate limit is exceeded.
    """

    error_code = "GEMINI_RATE_LIMIT_ERROR"


class GeminiRequestError(GeminiError):
    """
    Raised when a Gemini request fails.
    """

    error_code = "GEMINI_REQUEST_ERROR"


class GeminiResponseError(GeminiError):
    """
    Raised when a Gemini response is invalid or unusable.
    """

    error_code = "GEMINI_RESPONSE_ERROR"


# ============================================================
# RECOMMENDATION ERRORS
# ============================================================


class RecommendationError(BlackoutOracleError):
    """
    Base exception for recommendation-related failures.
    """

    error_code = "RECOMMENDATION_ERROR"


class RecommendationNotFoundError(
    RecommendationError
):
    """
    Raised when a recommendation cannot be found.
    """

    error_code = "RECOMMENDATION_NOT_FOUND"

    def __init__(
        self,
        recommendation_id: str,
    ) -> None:
        super().__init__(
            (
                f"Recommendation '{recommendation_id}' "
                "was not found."
            ),
            details={
                "recommendation_id": recommendation_id,
            },
        )


class RecommendationNotVerifiedError(
    RecommendationError
):
    """
    Raised when a recommendation is based on an unverified scenario.
    """

    error_code = "RECOMMENDATION_NOT_VERIFIED"


class HumanApprovalRequiredError(
    RecommendationError
):
    """
    Raised when human approval is required before proceeding.
    """

    error_code = "HUMAN_APPROVAL_REQUIRED"


class InvalidRecommendationStateError(
    RecommendationError
):
    """
    Raised when an invalid recommendation state transition is attempted.
    """

    error_code = "INVALID_RECOMMENDATION_STATE"


# ============================================================
# ALERT ERRORS
# ============================================================


class AlertError(BlackoutOracleError):
    """
    Base exception for alerting failures.
    """

    error_code = "ALERT_ERROR"


class AlertNotFoundError(AlertError):
    """
    Raised when an alert cannot be found.
    """

    error_code = "ALERT_NOT_FOUND"

    def __init__(
        self,
        alert_id: str,
    ) -> None:
        super().__init__(
            f"Alert '{alert_id}' was not found.",
            details={
                "alert_id": alert_id,
            },
        )


class AlertDeliveryError(AlertError):
    """
    Raised when an alert cannot be delivered.
    """

    error_code = "ALERT_DELIVERY_ERROR"


# ============================================================
# AUTHENTICATION / AUTHORIZATION
# ============================================================


class AuthenticationError(BlackoutOracleError):
    """
    Raised when authentication fails.
    """

    error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(BlackoutOracleError):
    """
    Raised when an authenticated user lacks permission.
    """

    error_code = "AUTHORIZATION_ERROR"


class HumanAuthorizationRequiredError(
    AuthorizationError
):
    """
    Raised when an operation requires authorized human review.
    """

    error_code = "HUMAN_AUTHORIZATION_REQUIRED"


# ============================================================
# EXTERNAL SERVICE ERRORS
# ============================================================


class ExternalServiceError(BlackoutOracleError):
    """
    Base exception for external service failures.
    """

    error_code = "EXTERNAL_SERVICE_ERROR"


class ExternalServiceUnavailableError(
    ExternalServiceError
):
    """
    Raised when an external dependency is unavailable.
    """

    error_code = "EXTERNAL_SERVICE_UNAVAILABLE"


class ExternalServiceTimeoutError(
    ExternalServiceError
):
    """
    Raised when an external dependency times out.
    """

    error_code = "EXTERNAL_SERVICE_TIMEOUT"


# ============================================================
# DATA QUALITY ERRORS
# ============================================================


class DataQualityError(BlackoutOracleError):
    """
    Base exception for data-quality failures.
    """

    error_code = "DATA_QUALITY_ERROR"


class MissingDataError(DataQualityError):
    """
    Raised when required data is missing.
    """

    error_code = "MISSING_DATA"


class InvalidDataError(DataQualityError):
    """
    Raised when received data is invalid.
    """

    error_code = "INVALID_DATA"


class ConflictingDataError(DataQualityError):
    """
    Raised when multiple sources provide conflicting information.
    """

    error_code = "CONFLICTING_DATA"


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    # Base
    "BlackoutOracleError",

    # Configuration
    "ConfigurationError",
    "MissingConfigurationError",

    # Database
    "DatabaseError",
    "DatabaseConnectionError",
    "DatabaseQueryError",

    # Telemetry
    "TelemetryError",
    "TelemetryUnavailableError",
    "TelemetryStaleError",
    "TelemetryValidationError",
    "TelemetrySourceError",

    # Weather
    "WeatherError",
    "WeatherUnavailableError",
    "WeatherStaleError",
    "WeatherValidationError",

    # Assets
    "AssetError",
    "AssetNotFoundError",
    "AssetValidationError",

    # Incidents
    "IncidentError",
    "IncidentNotFoundError",
    "InvalidIncidentStateError",

    # Risk
    "RiskEngineError",
    "RiskCalculationError",
    "InsufficientRiskDataError",
    "RiskModelUnavailableError",

    # Simulation
    "SimulationError",
    "SimulationNotFoundError",
    "SimulationValidationError",
    "SimulationExecutionError",
    "SimulationTimeoutError",
    "SimulationConvergenceError",

    # Verification
    "VerificationError",
    "VerificationFailedError",
    "InsufficientVerificationDataError",

    # AI Agent
    "AgentError",
    "AgentConfigurationError",
    "AgentUnavailableError",
    "AgentExecutionError",
    "AgentToolError",
    "AgentSafetyError",

    # Gemini
    "GeminiError",
    "GeminiAuthenticationError",
    "GeminiRateLimitError",
    "GeminiRequestError",
    "GeminiResponseError",

    # Recommendations
    "RecommendationError",
    "RecommendationNotFoundError",
    "RecommendationNotVerifiedError",
    "HumanApprovalRequiredError",
    "InvalidRecommendationStateError",

    # Alerts
    "AlertError",
    "AlertNotFoundError",
    "AlertDeliveryError",

    # Security
    "AuthenticationError",
    "AuthorizationError",
    "HumanAuthorizationRequiredError",

    # External services
    "ExternalServiceError",
    "ExternalServiceUnavailableError",
    "ExternalServiceTimeoutError",

    # Data quality
    "DataQualityError",
    "MissingDataError",
    "InvalidDataError",
    "ConflictingDataError",
]