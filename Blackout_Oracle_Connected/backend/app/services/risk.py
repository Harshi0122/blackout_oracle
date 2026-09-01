"""
Blackout Oracle - Risk Service.

Application-level service for calculating, retrieving, and
summarizing electrical-grid risk.

This service coordinates the risk engine, ML risk models,
grid telemetry, and persistence layers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.risk.engine import RiskEngine
from app.risk.scoring import RiskScorer
from app.risk.calibration import RiskCalibrator
from app.schemas.risk import (
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    RiskFactor,
    RiskLevel,
    RiskSummaryResponse,
    RiskTrend,
    RiskTrendPoint,
)


class RiskService:
    """
    High-level service for Blackout Oracle risk operations.

    The service is deliberately tolerant of different implementations
    of the lower-level risk engine so that the application remains
    usable while individual components evolve.
    """

    def __init__(
        self,
        engine: RiskEngine | None = None,
        scorer: RiskScorer | None = None,
        calibrator: RiskCalibrator | None = None,
    ) -> None:
        self.engine = (
            engine
            if engine is not None
            else RiskEngine()
        )

        self.scorer = (
            scorer
            if scorer is not None
            else RiskScorer()
        )

        self.calibrator = (
            calibrator
            if calibrator is not None
            else RiskCalibrator()
        )

    # ========================================================
    # BASIC RISK LEVEL
    # ========================================================

    @staticmethod
    def level_from_score(
        score: float,
    ) -> RiskLevel:
        """
        Convert a 0-100 risk score into a categorical level.
        """

        score = max(
            0.0,
            min(
                100.0,
                float(score),
            ),
        )

        if score >= 90.0:
            return RiskLevel.CRITICAL

        if score >= 75.0:
            return RiskLevel.HIGH

        if score >= 50.0:
            return RiskLevel.MEDIUM

        if score >= 25.0:
            return RiskLevel.LOW

        return RiskLevel.VERY_LOW

    # ========================================================
    # SCORE NORMALIZATION
    # ========================================================

    @staticmethod
    def _clamp_score(
        value: float | None,
    ) -> float:
        """
        Clamp a risk score to the valid 0-100 range.
        """

        if value is None:
            return 0.0

        try:
            value = float(value)
        except (TypeError, ValueError):
            return 0.0

        return max(
            0.0,
            min(
                100.0,
                value,
            ),
        )

    @staticmethod
    def _clamp_probability(
        value: float | None,
    ) -> float | None:
        """
        Clamp a probability to the valid 0-1 range.
        """

        if value is None:
            return None

        try:
            value = float(value)
        except (TypeError, ValueError):
            return None

        return max(
            0.0,
            min(
                1.0,
                value,
            ),
        )

    # ========================================================
    # COMPONENT SCORE
    # ========================================================

    def calculate_component_score(
        self,
        *,
        values: dict[str, float | None],
        weights: dict[str, float] | None = None,
    ) -> float:
        """
        Calculate a weighted risk score from individual components.

        Values are expected to use a 0-100 scale.
        """

        if not values:
            return 0.0

        normalized = {
            name: self._clamp_score(value)
            for name, value in values.items()
            if value is not None
        }

        if not normalized:
            return 0.0

        if weights is None:
            weight = 1.0 / len(normalized)

            weights = {
                name: weight
                for name in normalized
            }

        total_weight = sum(
            max(
                0.0,
                float(weights.get(name, 0.0)),
            )
            for name in normalized
        )

        if total_weight <= 0.0:
            return sum(
                normalized.values()
            ) / len(normalized)

        score = sum(
            normalized[name]
            * max(
                0.0,
                float(weights.get(name, 0.0)),
            )
            for name in normalized
        ) / total_weight

        return self._clamp_score(score)

    # ========================================================
    # FACTORS
    # ========================================================

    def build_factors(
        self,
        values: dict[str, float | None],
        weights: dict[str, float] | None = None,
    ) -> list[RiskFactor]:
        """
        Build structured risk-factor objects from component scores.
        """

        normalized = {
            name: self._clamp_score(value)
            for name, value in values.items()
            if value is not None
        }

        if not normalized:
            return []

        if weights is None:
            equal_weight = 1.0 / len(normalized)

            weights = {
                name: equal_weight
                for name in normalized
            }

        positive_weights = {
            name: max(
                0.0,
                float(weights.get(name, 0.0)),
            )
            for name in normalized
        }

        total_weight = sum(
            positive_weights.values()
        )

        if total_weight <= 0:
            total_weight = 1.0

        factors: list[RiskFactor] = []

        for name, score in normalized.items():
            weight = (
                positive_weights[name]
                / total_weight
            )

            contribution = (
                score * weight
            )

            factors.append(
                RiskFactor(
                    name=name,
                    score=score,
                    weight=weight,
                    contribution=contribution,
                    severity=self.level_from_score(
                        score
                    ),
                    explanation=(
                        f"{name} contributed "
                        f"{contribution:.2f} points "
                        f"to the overall risk score."
                    ),
                )
            )

        factors.sort(
            key=lambda factor: factor.contribution,
            reverse=True,
        )

        return factors

    # ========================================================
    # ENGINE EXECUTION
    # ========================================================

    def _run_engine(
        self,
        values: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """
        Execute the configured risk engine.

        Several common engine interfaces are supported.
        """

        payload = dict(values)

        if metadata:
            payload["metadata"] = metadata

        methods = (
            "calculate",
            "assess",
            "evaluate",
            "predict",
            "score",
        )

        for method_name in methods:
            method = getattr(
                self.engine,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:
                return method(payload)
            except TypeError:
                try:
                    return method(**payload)
                except TypeError:
                    continue

        return None

    # ========================================================
    # EXTRACT ENGINE RESULT
    # ========================================================

    @staticmethod
    def _extract_value(
        result: Any,
        *names: str,
        default: Any = None,
    ) -> Any:
        """
        Extract a value from either a dictionary or an object.
        """

        if result is None:
            return default

        if isinstance(result, dict):
            for name in names:
                if name in result:
                    return result[name]

            return default

        for name in names:
            value = getattr(
                result,
                name,
                None,
            )

            if value is not None:
                return value

        return default

    # ========================================================
    # ASSESS RISK
    # ========================================================

    def assess(
        self,
        request: RiskAssessmentRequest,
    ) -> RiskAssessmentResponse:
        """
        Perform a complete grid-risk assessment.
        """

        values = {
            "electrical": request.electrical_score,
            "asset": request.asset_score,
            "weather": request.weather_score,
            "anomaly": request.anomaly_score,
            "blackout": request.blackout_score,
            "cascade": request.cascade_score,
            "forecast": request.forecast_score,
        }

        values = {
            key: value
            for key, value in values.items()
            if value is not None
        }

        engine_result = self._run_engine(
            values,
            request.metadata,
        )

        engine_score = self._extract_value(
            engine_result,
            "score",
            "risk_score",
            "overall_score",
        )

        if engine_score is None:
            score = self.calculate_component_score(
                values=values,
            )
        else:
            score = self._clamp_score(
                engine_score
            )

        probability = self._clamp_probability(
            self._extract_value(
                engine_result,
                "probability",
                "risk_probability",
            )
        )

        confidence = self._clamp_probability(
            self._extract_value(
                engine_result,
                "confidence",
            )
        )

        if confidence is None:
            confidence = self._estimate_confidence(
                values
            )

        trend_value = self._extract_value(
            engine_result,
            "trend",
            default=RiskTrend.UNKNOWN,
        )

        try:
            trend = RiskTrend(
                str(trend_value)
            )
        except ValueError:
            trend = RiskTrend.UNKNOWN

        weights = {
            "electrical": 0.25,
            "asset": 0.20,
            "weather": 0.10,
            "anomaly": 0.15,
            "blackout": 0.15,
            "cascade": 0.10,
            "forecast": 0.05,
        }

        factors = self.build_factors(
            values,
            weights,
        )

        level = self.level_from_score(
            score
        )

        now = datetime.now(
            timezone.utc
        )

        recommendations = self._build_recommendations(
            score=score,
            level=level,
            factors=factors,
        )

        return RiskAssessmentResponse(
            id=None,
            risk_type="overall",
            score=score,
            level=level,
            probability=probability,
            confidence=confidence,
            trend=trend,
            region=request.region,
            substation_id=request.substation_id,
            transformer_id=request.transformer_id,
            transmission_line_id=(
                request.transmission_line_id
            ),
            asset_id=request.asset_id,
            alert_required=score >= 75.0,
            critical=score >= 90.0,
            factors=factors,
            metadata=request.metadata,
            assessed_at=now,
            valid_until=None,
            engine=self.engine.__class__.__name__,
            engine_version=None,
            recommendations=recommendations,
        )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    @staticmethod
    def _estimate_confidence(
        values: dict[str, float],
    ) -> float:
        """
        Estimate confidence from the amount of available
        component information.
        """

        if not values:
            return 0.0

        coverage = min(
            1.0,
            len(values) / 7.0,
        )

        return round(
            0.4 + (0.6 * coverage),
            4,
        )

    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    @staticmethod
    def _build_recommendations(
        *,
        score: float,
        level: RiskLevel,
        factors: list[RiskFactor],
    ) -> list[str]:
        """
        Produce deterministic operator-facing recommendations.
        """

        recommendations: list[str] = []

        if level == RiskLevel.CRITICAL:
            recommendations.append(
                "Immediate operator review is recommended."
            )
            recommendations.append(
                "Evaluate active contingencies and "
                "potential cascading-failure paths."
            )

        elif level == RiskLevel.HIGH:
            recommendations.append(
                "Increase grid monitoring and perform "
                "operator review."
            )
            recommendations.append(
                "Evaluate vulnerable assets and available "
                "contingency actions."
            )

        elif level == RiskLevel.MEDIUM:
            recommendations.append(
                "Continue enhanced monitoring of the "
                "affected grid area."
            )

        elif level == RiskLevel.LOW:
            recommendations.append(
                "Continue normal monitoring and review "
                "the leading risk factors."
            )

        else:
            recommendations.append(
                "No immediate elevated-risk action is indicated."
            )

        if factors:
            leading_factor = factors[0]

            if leading_factor.score >= 75.0:
                recommendations.append(
                    "Investigate the leading risk factor: "
                    f"{leading_factor.name}."
                )

        if score >= 90.0:
            recommendations.append(
                "Run a contingency or cascade simulation "
                "before making major operational changes."
            )

        return recommendations

    # ========================================================
    # COMPONENT ASSESSMENTS
    # ========================================================

    def assess_electrical(
        self,
        score: float,
        *,
        confidence: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RiskAssessmentResponse:
        """
        Create an electrical-risk assessment.
        """

        request = RiskAssessmentRequest(
            electrical_score=score,
            metadata=metadata or {},
        )

        response = self.assess(
            request
        )

        response.risk_type = "electrical"

        if confidence is not None:
            response.confidence = (
                self._clamp_probability(
                    confidence
                )
                or 0.0
            )

        return response

    def assess_asset(
        self,
        score: float,
        *,
        asset_id: int | None = None,
        confidence: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RiskAssessmentResponse:
        """
        Create an asset-risk assessment.
        """

        request = RiskAssessmentRequest(
            asset_score=score,
            asset_id=asset_id,
            metadata=metadata or {},
        )

        response = self.assess(
            request
        )

        response.risk_type = "asset"

        if confidence is not None:
            response.confidence = (
                self._clamp_probability(
                    confidence
                )
                or 0.0
            )

        return response

    def assess_weather(
        self,
        score: float,
        *,
        region: str | None = None,
        confidence: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RiskAssessmentResponse:
        """
        Create a weather-risk assessment.
        """

        request = RiskAssessmentRequest(
            weather_score=score,
            region=region,
            metadata=metadata or {},
        )

        response = self.assess(
            request
        )

        response.risk_type = "weather"

        if confidence is not None:
            response.confidence = (
                self._clamp_probability(
                    confidence
                )
                or 0.0
            )

        return response

    # ========================================================
    # SUMMARY
    # ========================================================

    def summarize(
        self,
        *,
        electrical_score: float | None = None,
        asset_score: float | None = None,
        weather_score: float | None = None,
        anomaly_score: float | None = None,
        blackout_score: float | None = None,
        cascade_score: float | None = None,
        forecast_score: float | None = None,
        active_alerts: int = 0,
        active_incidents: int = 0,
        critical_assets: int = 0,
    ) -> RiskSummaryResponse:
        """
        Build a high-level grid-risk summary.
        """

        values = {
            "electrical": electrical_score,
            "asset": asset_score,
            "weather": weather_score,
            "anomaly": anomaly_score,
            "blackout": blackout_score,
            "cascade": cascade_score,
            "forecast": forecast_score,
        }

        available = {
            key: value
            for key, value in values.items()
            if value is not None
        }

        weights = {
            "electrical": 0.25,
            "asset": 0.20,
            "weather": 0.10,
            "anomaly": 0.15,
            "blackout": 0.15,
            "cascade": 0.10,
            "forecast": 0.05,
        }

        score = self.calculate_component_score(
            values=available,
            weights=weights,
        )

        confidence = self._estimate_confidence(
            available
        )

        return RiskSummaryResponse(
            overall_score=score,
            overall_level=self.level_from_score(
                score
            ),
            overall_probability=None,
            confidence=confidence,
            trend=RiskTrend.UNKNOWN,
            electrical_score=(
                self._clamp_score(electrical_score)
                if electrical_score is not None
                else None
            ),
            asset_score=(
                self._clamp_score(asset_score)
                if asset_score is not None
                else None
            ),
            weather_score=(
                self._clamp_score(weather_score)
                if weather_score is not None
                else None
            ),
            anomaly_score=(
                self._clamp_score(anomaly_score)
                if anomaly_score is not None
                else None
            ),
            blackout_score=(
                self._clamp_score(blackout_score)
                if blackout_score is not None
                else None
            ),
            cascade_score=(
                self._clamp_score(cascade_score)
                if cascade_score is not None
                else None
            ),
            forecast_score=(
                self._clamp_score(forecast_score)
                if forecast_score is not None
                else None
            ),
            active_alerts=max(
                0,
                int(active_alerts),
            ),
            active_incidents=max(
                0,
                int(active_incidents),
            ),
            critical_assets=max(
                0,
                int(critical_assets),
            ),
            assessed_at=datetime.now(
                timezone.utc
            ),
            metadata={},
        )

    # ========================================================
    # TREND
    # ========================================================

    @staticmethod
    def calculate_trend(
        current_score: float,
        previous_score: float | None,
        *,
        tolerance: float = 2.0,
    ) -> RiskTrend:
        """
        Determine risk direction from two scores.
        """

        current_score = max(
            0.0,
            min(
                100.0,
                float(current_score),
            ),
        )

        if previous_score is None:
            return RiskTrend.UNKNOWN

        previous_score = max(
            0.0,
            min(
                100.0,
                float(previous_score),
            ),
        )

        change = (
            current_score
            - previous_score
        )

        if change > tolerance:
            return RiskTrend.WORSENING

        if change < -tolerance:
            return RiskTrend.IMPROVING

        return RiskTrend.STABLE

    def build_trend(
        self,
        scores: list[tuple[datetime, float]],
        *,
        risk_type: str = "overall",
    ) -> dict[str, Any]:
        """
        Build a lightweight risk trend representation.
        """

        if not scores:
            return {
                "risk_type": risk_type,
                "current_score": 0.0,
                "previous_score": None,
                "trend": RiskTrend.UNKNOWN,
                "change": None,
                "points": [],
            }

        ordered = sorted(
            scores,
            key=lambda item: item[0],
        )

        current_timestamp, current_score = ordered[-1]

        previous_score = (
            ordered[-2][1]
            if len(ordered) >= 2
            else None
        )

        trend = self.calculate_trend(
            current_score,
            previous_score,
        )

        points = [
            RiskTrendPoint(
                timestamp=timestamp,
                score=self._clamp_score(score),
                level=self.level_from_score(
                    score
                ),
                probability=None,
            )
            for timestamp, score in ordered
        ]

        return {
            "risk_type": risk_type,
            "current_score": self._clamp_score(
                current_score
            ),
            "previous_score": (
                self._clamp_score(previous_score)
                if previous_score is not None
                else None
            ),
            "trend": trend,
            "change": (
                self._clamp_score(current_score)
                - self._clamp_score(previous_score)
                if previous_score is not None
                else None
            ),
            "points": points,
            "timestamp": current_timestamp,
        }

    # ========================================================
    # MODEL SCORING HELPERS
    # ========================================================

    def score_prediction(
        self,
        probability: float,
        *,
        impact: float = 1.0,
    ) -> float:
        """
        Convert predicted probability and impact into a 0-100
        risk score.
        """

        probability = max(
            0.0,
            min(
                1.0,
                float(probability),
            ),
        )

        impact = max(
            0.0,
            min(
                1.0,
                float(impact),
            ),
        )

        raw_score = (
            probability
            * impact
            * 100.0
        )

        return self._clamp_score(
            raw_score
        )

    def calibrate_probability(
        self,
        probability: float,
    ) -> float:
        """
        Calibrate a model probability using the configured
        calibration component when supported.
        """

        probability = max(
            0.0,
            min(
                1.0,
                float(probability),
            ),
        )

        methods = (
            "calibrate",
            "transform",
            "predict",
        )

        for method_name in methods:
            method = getattr(
                self.calibrator,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:
                result = method(
                    probability
                )

                if isinstance(
                    result,
                    (int, float),
                ):
                    return max(
                        0.0,
                        min(
                            1.0,
                            float(result),
                        ),
                    )

                extracted = self._extract_value(
                    result,
                    "probability",
                    "calibrated_probability",
                    "value",
                )

                if extracted is not None:
                    return max(
                        0.0,
                        min(
                            1.0,
                            float(extracted),
                        ),
                    )

            except (TypeError, ValueError):
                continue

        return probability


__all__ = [
    "RiskService",
]