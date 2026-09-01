"""Small, clearly labelled development dataset for the connected dashboard."""

from __future__ import annotations

from datetime import datetime, timezone


def seed_demo_data() -> None:
    """Populate empty development stores once per API process.

    This is intentionally synthetic and exists only so a fresh local checkout
    renders useful API-backed data.  Production ingestion replaces these stores.
    """
    from app.api.routes import alerts, assets, incidents, recommendations, risk, telemetry, weather

    if assets._ASSETS:
        return

    now = datetime.now(timezone.utc)
    region = {"region_id": "west-sector", "region_name": "West Sector"}

    # ── Grid topology: 17 nodes matching the frontend's SmartGrid layout ──
    # Each asset includes metadata.edges so the frontend can reconstruct
    # the transmission-line topology for the digital twin visualization.

    # Edge definitions (from/to, load 0..1, flow direction)
    _EDGES = [
        {"id": "e1",  "from": "GEN-N",  "to": "SUB-A", "load": 0.78, "flow": 1},
        {"id": "e2",  "from": "GEN-S",  "to": "SUB-C", "load": 0.72, "flow": 1},
        {"id": "e3",  "from": "SOLAR-W","to": "SUB-B", "load": 0.32, "flow": 1},
        {"id": "e4",  "from": "WIND-N", "to": "SUB-C", "load": 0.68, "flow": 1},
        {"id": "e5",  "from": "BAT-1",  "to": "SUB-A", "load": 0.45, "flow": 1},
        {"id": "e6",  "from": "BAT-2",  "to": "SUB-B", "load": 0.40, "flow": 1},
        {"id": "e7",  "from": "SUB-A",  "to": "SUB-D", "load": 0.65, "flow": 1},
        {"id": "e8",  "from": "SUB-B",  "to": "SUB-D", "load": 0.55, "flow": -1},
        {"id": "e9",  "from": "SUB-C",  "to": "SUB-D", "load": 0.42, "flow": 1},
        {"id": "e10", "from": "SUB-D",  "to": "IND-1", "load": 0.62, "flow": 1},
        {"id": "e11", "from": "SUB-D",  "to": "IND-2", "load": 0.48, "flow": 1},
        {"id": "e12", "from": "SUB-D",  "to": "RES-1", "load": 0.40, "flow": 1},
        {"id": "e13", "from": "SUB-D",  "to": "RES-2", "load": 0.38, "flow": 1},
        {"id": "e14", "from": "SUB-A",  "to": "HOSP",  "load": 0.82, "flow": 1},
        {"id": "e15", "from": "SUB-B",  "to": "DATA",  "load": 0.58, "flow": 1},
        {"id": "e16", "from": "SUB-C",  "to": "CRIT",  "load": 0.88, "flow": 1},
        {"id": "e17", "from": "SUB-B",  "to": "RES-1", "load": 0.32, "flow": 1},
        {"id": "e18", "from": "SUB-C",  "to": "IND-2", "load": 0.45, "flow": 1},
    ]

    # Build a per-node edge lookup for metadata
    _node_edges: dict[str, list[dict]] = {}
    for edge in _EDGES:
        _node_edges.setdefault(edge["from"], []).append(edge)
        _node_edges.setdefault(edge["to"], []).append(edge)

    # Asset definitions: (id, name, asset_type, status, capacity_mw, lat, lon, utilization)
    asset_rows = [
        # Generation
        ("GEN-N",   "NORTH GAS GEN",     "generator", "normal",   200, 28.6300, 77.1800, 0.72),
        ("GEN-S",   "SOUTH GAS GEN",     "generator", "normal",   200, 28.5900, 77.1800, 0.65),
        ("SOLAR-W", "WEST SOLAR FARM",   "solar",     "warning",  120, 28.6100, 77.1900, 0.30),
        ("WIND-N",  "OFFSHORE WIND",     "wind",      "normal",   120, 28.6000, 77.1700, 0.85),
        ("BAT-1",   "BATTERY BANK A",    "battery",   "normal",   120, 28.6250, 77.1950, 0.40),
        ("BAT-2",   "BATTERY BANK B",    "battery",   "normal",   120, 28.5950, 77.1950, 0.35),
        # Transmission
        ("SUB-A",   "SUBSTATION A",      "substation","warning",  100, 28.6139, 77.2090, 0.91),
        ("SUB-B",   "SUBSTATION B",      "substation","degraded", 100, 28.6100, 77.2100, 0.74),
        ("SUB-C",   "SUBSTATION C",      "substation","normal",   100, 28.6050, 77.2100, 0.52),
        ("SUB-D",   "SUBSTATION D",      "substation","degraded", 100, 28.6150, 77.2150, 0.68),
        # Distribution
        ("IND-1",   "INDUSTRIAL ZONE 1", "industrial","degraded", 100, 28.6200, 77.2200, 0.71),
        ("IND-2",   "INDUSTRIAL ZONE 2", "industrial","normal",   100, 28.6000, 77.2200, 0.55),
        ("RES-1",   "RESIDENTIAL NORTH", "residential","normal",  100, 28.6180, 77.2250, 0.48),
        ("RES-2",   "RESIDENTIAL SOUTH", "residential","normal",  100, 28.6020, 77.2250, 0.44),
        ("HOSP",    "CENTRAL HOSPITAL",  "hospital",  "warning",   50, 28.6220, 77.2300, 0.82),
        ("CRIT",    "EMERGENCY OPS",     "critical",  "failed",    30, 28.6100, 77.2300, 0.95),
        ("DATA",    "DATA CENTER",       "critical",  "degraded", 100, 28.6120, 77.2220, 0.69),
    ]

    for identifier, name, asset_type, status, capacity, latitude, longitude, utilization in asset_rows:
        connected_edges = _node_edges.get(identifier, [])
        assets._ASSETS[identifier] = assets.AssetResponse(
            id=identifier, name=name, asset_type=asset_type, status=status,
            rated_capacity_mw=capacity,
            location={"latitude": latitude, "longitude": longitude},
            source="synthetic",
            metadata={
                "utilization": utilization,
                "load_mw": round(capacity * utilization, 1),
                "cascade_contribution": round(utilization * 0.85, 2),
                "edges": connected_edges,
            },
            created_at=now, updated_at=now, **region,
        )

    # ── Weather observation ──
    weather._WEATHER_OBSERVATIONS.append(weather.WeatherObservationResponse(
        id="WTH-DEMO-001", latitude=28.6139, longitude=77.2090, location_name="West Sector",
        observed_at=now, received_at=now, temperature_c=21.0, humidity_percent=91.0,
        rainfall_mm=18.4, rainfall_rate_mm_per_hour=64.0, wind_speed_kmh=46.0,
        wind_gust_kmh=70.0, pressure_hpa=1004.0, visibility_km=4.2,
        lightning_detected=True, storm_detected=True, flood_risk=62.0,
        weather_severity="severe", source="synthetic",
    ))

    # ── Risk assessment ──
    assessment = risk.RiskAssessmentResponse(
        id="RSK-DEMO-001", risk_type="cascade", risk_score=78.0, risk_level="high", confidence=86.0,
        blackout_probability=0.42, cascade_probability=0.68, warning_horizon_minutes=17,
        affected_asset_ids=["SUB-A", "HOSP"],
        risk_factors=[{
            "name": "Substation loading", "category": "overload", "contribution": 46.0,
            "severity": "high", "description": "SUB-A is operating near its thermal limit.",
            "evidence": {},
        }],
        model_name="development-demo", model_version="1.0",
        data_timestamp=now, calculated_at=now, **region,
    )
    risk._RISK_ASSESSMENTS[assessment.id] = assessment
    risk._RISK_HISTORY.append(risk.RiskHistoryPoint(
        timestamp=now, risk_score=assessment.risk_score,
        risk_level=assessment.risk_level, confidence=assessment.confidence,
    ))

    # ── Incident ──
    incident = incidents.IncidentResponse(
        id="INC-DEMO-001", title="Substation A overload risk",
        description="Storm conditions are increasing load stress on SUB-A, threatening HOSP and CRIT.",
        incident_type="transformer_overload", severity="high", status="mitigation_pending",
        affected_asset_ids=["SUB-A", "HOSP", "CRIT"], risk_score=78.0, confidence=86.0,
        warning_horizon_minutes=17,
        contributing_factors=["Heavy rain", "High feeder load", "Cascade path active"],
        created_at=now, updated_at=now, **region,
    )
    incidents._INCIDENTS[incident.id] = incident

    # ── Alert ──
    alerts._ALERTS["ALT-DEMO-001"] = alerts.AlertResponse(
        id="ALT-DEMO-001", incident_id=incident.id, level="orange", status="active",
        title="SUBSTATION A OVERLOAD RISK", message="Breaker thermal limit is approaching.",
        risk_score=78.0, confidence=86.0, warning_horizon_minutes=17,
        affected_assets=["SUB-A", "HOSP", "CRIT"], created_at=now, **region,
    )

    # ── Recommendation ──
    recommendation = recommendations.RecommendationResponse(
        id="REC-DEMO-001", incident_id=incident.id, scenario_id="SCN-DEMO-001",
        title="Dispatch battery reserve",
        explanation="Use the battery reserve to reduce Substation A loading.",
        rationale=[
            "Projected cascade probability is elevated.",
            "Battery dispatch lowers estimated loading by 18%.",
        ],
        risk_before=78.0, risk_after=45.0, confidence=82.0,
        verification_status="verified",
        affected_asset_ids=["SUB-A", "HOSP"], status="pending_review",
        requires_human_approval=True, created_at=now,
    )
    recommendations._RECOMMENDATIONS[recommendation.id] = recommendation

    # ── Telemetry ──
    telemetry._TELEMETRY.extend([
        # Load measurements
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-001", asset_id="SUB-A", measurement_type="load", value=164.0,
            unit="MW", timestamp=now, received_at=now, quality="good", source="synthetic"),
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-010", asset_id="HOSP", measurement_type="load", value=41.0,
            unit="MW", timestamp=now, received_at=now, quality="good", source="synthetic"),
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-011", asset_id="SUB-B", measurement_type="load", value=74.0,
            unit="MW", timestamp=now, received_at=now, quality="good", source="synthetic"),
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-012", asset_id="SUB-C", measurement_type="load", value=52.0,
            unit="MW", timestamp=now, received_at=now, quality="good", source="synthetic"),
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-013", asset_id="SUB-D", measurement_type="load", value=68.0,
            unit="MW", timestamp=now, received_at=now, quality="good", source="synthetic"),
        # Generation measurements
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-002", asset_id="GEN-N", measurement_type="generation", value=145.0,
            unit="MW", timestamp=now, received_at=now, quality="good", source="synthetic"),
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-020", asset_id="GEN-S", measurement_type="generation", value=130.0,
            unit="MW", timestamp=now, received_at=now, quality="good", source="synthetic"),
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-021", asset_id="SOLAR-W", measurement_type="generation", value=36.0,
            unit="MW", timestamp=now, received_at=now, quality="good", source="synthetic"),
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-022", asset_id="WIND-N", measurement_type="generation", value=102.0,
            unit="MW", timestamp=now, received_at=now, quality="good", source="synthetic"),
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-023", asset_id="BAT-1", measurement_type="generation", value=48.0,
            unit="MW", timestamp=now, received_at=now, quality="good", source="synthetic"),
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-024", asset_id="BAT-2", measurement_type="generation", value=42.0,
            unit="MW", timestamp=now, received_at=now, quality="good", source="synthetic"),
        # Frequency (slightly depressed under stress)
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-003", asset_id="SUB-A", measurement_type="frequency", value=49.87,
            unit="Hz", timestamp=now, received_at=now, quality="good", source="synthetic"),
        # Voltage (slightly below nominal)
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-004", asset_id="SUB-A", measurement_type="voltage", value=226.4,
            unit="kV", timestamp=now, received_at=now, quality="good", source="synthetic"),
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-025", asset_id="SUB-D", measurement_type="voltage", value=228.1,
            unit="kV", timestamp=now, received_at=now, quality="good", source="synthetic"),
        # Temperature on critical transformer
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-005", asset_id="SUB-A", measurement_type="temperature", value=78.5,
            unit="C", timestamp=now, received_at=now, quality="good", source="synthetic"),
        # Power factor
        telemetry.TelemetryPointResponse(
            id="TEL-DEMO-006", asset_id="SUB-A", measurement_type="power_factor", value=0.91,
            unit="ratio", timestamp=now, received_at=now, quality="good", source="synthetic"),
    ])
