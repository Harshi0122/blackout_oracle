export type JsonRecord = Record<string, unknown>;

export interface GeoPoint {
  latitude: number;
  longitude: number;
  altitude_m?: number | null;
  metadata?: JsonRecord;
}

export type AssetStatus = 'normal' | 'degraded' | 'warning' | 'failed' | 'offline' | 'unknown';
export interface AssetResponse {
  id: string;
  name: string;
  asset_type: string;
  region_id?: string | null;
  region_name?: string | null;
  parent_asset_id?: string | null;
  location?: GeoPoint | null;
  rated_capacity_mw?: number | null;
  voltage_kv?: number | null;
  status: AssetStatus;
  source: string;
  metadata: JsonRecord;
  created_at: string;
  updated_at: string;
}

export type AlertLevel = 'green' | 'yellow' | 'orange' | 'red' | 'black';
export type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'dismissed';
export interface AlertResponse {
  id: string;
  incident_id?: string | null;
  region_id?: string | null;
  level: AlertLevel;
  status: AlertStatus;
  title: string;
  message: string;
  risk_score?: number | null;
  confidence?: number | null;
  warning_horizon_minutes?: number | null;
  affected_assets?: string[];
  created_at?: string;
  updated_at?: string;
  metadata?: JsonRecord;
}
export interface AlertAcknowledgeRequest { acknowledged_by: string; note?: string | null; }
export interface AlertResolveRequest { resolved_by: string; note?: string | null; }

export interface IncidentResponse {
  id: string;
  title: string;
  description: string;
  incident_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'detected' | 'investigating' | 'predicted' | 'mitigation_pending' | 'human_review' | 'monitoring' | 'resolved' | 'false_positive' | 'failed';
  region_id?: string | null;
  region_name?: string | null;
  affected_asset_ids: string[];
  latitude?: number | null;
  longitude?: number | null;
  risk_score?: number | null;
  confidence?: number | null;
  warning_horizon_minutes?: number | null;
  contributing_factors: string[];
  metadata: JsonRecord;
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
}
export interface IncidentResolveRequest { resolved_by: string; resolution_note?: string | null; resolution_type?: string; }

export interface RiskFactor {
  name: string;
  category: string;
  contribution: number;
  severity: string;
  description: string;
  evidence: JsonRecord;
}
export interface RiskAssessmentResponse {
  id: string;
  region_id?: string | null;
  region_name?: string | null;
  risk_type: string;
  risk_score: number;
  risk_level: 'normal' | 'watch' | 'elevated' | 'high' | 'critical';
  confidence: number;
  blackout_probability?: number | null;
  cascade_probability?: number | null;
  warning_horizon_minutes?: number | null;
  affected_asset_ids: string[];
  risk_factors: RiskFactor[];
  model_name: string;
  model_version: string;
  data_timestamp: string;
  calculated_at: string;
  metadata: JsonRecord;
}
export interface RiskSummaryResponse {
  region_id?: string | null;
  region_name?: string | null;
  current_score: number;
  current_level: string;
  average_score: number;
  maximum_score: number;
  minimum_score: number;
  trend: string;
  observations: number;
  calculated_at: string;
}
export interface RiskAssessmentRequest {
  region_id?: string | null;
  region_name?: string | null;
  asset_ids?: string[];
  telemetry?: JsonRecord;
  weather?: JsonRecord;
  forecast?: JsonRecord;
  historical_context?: JsonRecord;
}

export interface WeatherObservationResponse {
  id: string;
  latitude: number;
  longitude: number;
  location_name?: string | null;
  observed_at: string;
  received_at: string;
  temperature_c?: number | null;
  feels_like_c?: number | null;
  humidity_percent?: number | null;
  rainfall_mm?: number | null;
  rainfall_rate_mm_per_hour?: number | null;
  wind_speed_kmh?: number | null;
  wind_gust_kmh?: number | null;
  pressure_hpa?: number | null;
  visibility_km?: number | null;
  lightning_detected: boolean;
  storm_detected: boolean;
  flood_risk?: number | null;
  weather_severity: 'normal' | 'watch' | 'warning' | 'severe' | 'extreme';
  source: string;
  metadata: JsonRecord;
}
export interface WeatherForecastResponse {
  id: string;
  latitude: number;
  longitude: number;
  location_name?: string | null;
  forecast_time: string;
  generated_at: string;
  temperature_c?: number | null;
  rainfall_probability_percent?: number | null;
  predicted_rainfall_mm?: number | null;
  wind_speed_kmh?: number | null;
  wind_gust_kmh?: number | null;
  storm_probability_percent?: number | null;
  flood_probability_percent?: number | null;
  weather_severity: string;
  source: string;
  metadata: JsonRecord;
}

export interface TelemetryPointResponse {
  id: string;
  asset_id: string;
  measurement_type: string;
  value: number;
  unit: string;
  timestamp: string;
  received_at: string;
  quality: string;
  source: string;
  metadata: JsonRecord;
}
export interface TelemetryLatestResponse {
  asset_id: string;
  measurements: Record<string, TelemetryPointResponse>;
  latest_timestamp?: string | null;
}
export interface TelemetryHealthResponse {
  asset_id?: string | null;
  telemetry_available: boolean;
  latest_timestamp?: string | null;
  age_seconds?: number | null;
  quality: string;
  source?: string | null;
}
export interface TelemetrySummary extends JsonRecord {
  total_measurements?: number;
  assets?: number;
  measurement_types?: Record<string, number>;
  sources?: Record<string, number>;
}

export type RecommendationStatus = 'generated' | 'pending_review' | 'approved' | 'rejected' | 'executed' | 'expired' | 'superseded';
export interface RecommendationResponse {
  id: string;
  incident_id?: string | null;
  scenario_id?: string | null;
  title: string;
  explanation: string;
  rationale: string | string[] | null;
  risk_before?: number | null;
  risk_after?: number | null;
  confidence?: number | null;
  status: RecommendationStatus;
  verification_status?: string | null;
  reviewed_at?: string | null;
  reviewed_by?: string | null;
  review_note?: string | null;
  created_at?: string;
  metadata?: JsonRecord;
}
export interface RecommendationReviewRequest { reviewer_id: string; note?: string | null; }

export type SimulationStatus = 'created' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
export interface ScenarioChange { asset_id: string; parameter: string; value?: unknown; description?: string | null; }
export interface ScenarioCreate {
  name: string;
  description?: string;
  simulation_type?: 'power_flow' | 'time_series' | 'contingency' | 'cascade' | 'voltage_stability' | 'frequency_stability' | 'blackout' | 'custom';
  changes?: ScenarioChange[];
  parameters?: JsonRecord;
  metadata?: JsonRecord;
}
export interface SimulationCreate {
  incident_id?: string | null;
  scenario_id?: string | null;
  scenario?: ScenarioCreate | null;
  simulation_type?: ScenarioCreate['simulation_type'];
  time_horizon_minutes?: number;
  time_step_seconds?: number;
  parameters?: JsonRecord;
}
export interface SimulationResponse {
  id: string;
  incident_id?: string | null;
  scenario_id: string;
  simulation_type: string;
  status: SimulationStatus;
  time_horizon_minutes: number;
  time_step_seconds: number;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  results?: JsonRecord | null;
  summary: JsonRecord;
  warnings: string[];
  errors: string[];
  metadata: JsonRecord;
}
