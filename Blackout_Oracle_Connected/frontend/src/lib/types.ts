// Type definitions for the BLACKOUT ORACLE data model.
// This mirrors what a backend agentic-AI service would emit.

export type WeatherMode = 'clear' | 'rain' | 'storm' | 'heat' | 'flood';

export interface WeatherData {
  mode: WeatherMode;
  rainfall: number; // mm/hr
  windSpeed: number; // km/h
  temperature: number; // C
  humidity: number; // %
  lightningRate: number; // strikes / min
  floodLevel: number; // 0..1
  cloudCover: number; // 0..1
  pressure: number; // hPa
  visibility: number; // km
}

export type NodeStatus = 'green' | 'yellow' | 'orange' | 'red';

export type NodeKind =
  | 'generator'
  | 'solar'
  | 'wind'
  | 'battery'
  | 'substation'
  | 'industrial'
  | 'residential'
  | 'hospital'
  | 'critical';

export interface GridNode {
  id: string;
  name: string;
  kind: NodeKind;
  x: number; // 0..1 normalized
  y: number;
  status: NodeStatus;
  utilization: number; // 0..1
  load: number; // MW
  capacity: number; // MW
  cascadeContribution: number; // 0..1
  priority: number; // 1=low, 3=critical
}

export interface GridEdge {
  id: string;
  from: string;
  to: string;
  active: boolean;
  load: number; // 0..1
  flow: number; // -1..1, direction sign
}

export interface GridData {
  nodes: GridNode[];
  edges: GridEdge[];
  totalLoad: number; // MW
  totalGeneration: number; // MW
  frequency: number; // Hz
  voltage: number; // kV
  cascadeRisk: number; // 0..1
  stability: number; // 0..100
  renewablesShare: number; // 0..1
}

export type InterventionType = 'battery' | 'ev_demand' | 'reroute' | 'loadshed';

export interface Intervention {
  id: string;
  type: InterventionType;
  title: string;
  description: string;
  effectiveness: number; // 0..1
  cost: number; // 0..1
  active: boolean;
  flows: { from: string; to: string; amount: number }[];
  affectedNodes: string[];
  recommended: boolean;
  reasonCode: string;
  recommendationId?: string;
  recommendationStatus?: string;
  verificationStatus?: string | null;
}

export interface CascadeStep {
  t: number; // seconds offset
  nodeId: string;
  status: NodeStatus;
  message: string;
}

export interface Alert {
  id: string;
  level: 'critical' | 'warning' | 'info';
  title: string;
  subtitle: string;
  nodeId?: string;
  cascadeWindowMin?: number;
  timestamp: number;
}

export interface PredictionPoint {
  label: string; // 'NOW', '+5m', ...
  offsetMin: number;
  rainfall: number;
  windSpeed: number;
  temperature: number;
  demand: number;
  solarGen: number;
  windGen: number;
  batterySoC: number;
  gridStress: number;
  cascadeProbability: number;
  nodeStatuses: Record<string, NodeStatus>;
}

export interface BackendSnapshot {
  timestamp: number;
  weather: WeatherData;
  grid: GridData;
  interventions: Intervention[];
  cascadeSteps: CascadeStep[];
  alerts: Alert[];
  predictions: PredictionPoint[];
  aiConfidence: number; // 0..1
  rationale: string[];
  recommendationsRaw?: Array<Record<string, unknown>>;
  incidentsRaw?: Array<Record<string, unknown>>;
}