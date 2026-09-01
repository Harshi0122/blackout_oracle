import { useEffect, useRef, useState } from 'react';
import type { BackendSnapshot, Intervention, NodeKind, NodeStatus, Alert } from './types';
import { emptySnapshot } from './emptyState';
import { getOracleSnapshot } from '../api/blackoutOracle';
import type { ActiveLocation } from './useLocation';

export interface LiveMeta {
  connected: boolean;
  partial: boolean;
  source: 'api' | 'unavailable';
  lastUpdated: number;
  error?: string;
}
export interface LiveDataResult {
  data: BackendSnapshot;
  meta: LiveMeta;
  refresh: () => void;
}

const toNodeStatus = (value: unknown): NodeStatus => {
  const status = String(value ?? '').toLowerCase();
  if (['failed', 'offline', 'red', 'critical'].includes(status)) return 'red';
  if (['warning', 'orange'].includes(status)) return 'orange';
  if (['degraded', 'yellow'].includes(status)) return 'yellow';
  return 'green';
};

const toNodeKind = (value: unknown): NodeKind => {
  const type = String(value ?? '').toLowerCase();
  if (type.includes('solar')) return 'solar';
  if (type.includes('wind')) return 'wind';
  if (type.includes('battery')) return 'battery';
  if (type.includes('generator') || type.includes('generation')) return 'generator';
  if (type.includes('hospital')) return 'hospital';
  if (type.includes('substation') || type.includes('transformer')) return 'substation';
  if (type.includes('industrial')) return 'industrial';
  if (type.includes('residential')) return 'residential';
  return 'critical';
};

const numberOr = (value: unknown, fallback = 0) =>
  typeof value === 'number' && Number.isFinite(value) ? value : fallback;

function recommendationType(title: string): Intervention['type'] {
  const value = title.toLowerCase();
  if (value.includes('battery')) return 'battery';
  if (value.includes('ev') || value.includes('demand')) return 'ev_demand';
  if (value.includes('reroute') || value.includes('route')) return 'reroute';
  return 'loadshed';
}

function adapt(raw: Awaited<ReturnType<typeof getOracleSnapshot>>): BackendSnapshot {
  const base = emptySnapshot();
  const assets = Array.isArray(raw.assets) ? raw.assets : [];
  const nodes = assets.map((asset: any, index: number) => {
    const metadata = asset.metadata && typeof asset.metadata === 'object' ? asset.metadata : {};
    return {
      id: String(asset.id),
      name: String(asset.name ?? `Asset ${index + 1}`),
      kind: toNodeKind(asset.asset_type),
      x: asset.location?.longitude != null
        ? Math.max(0.06, Math.min(0.94, (Number(asset.location.longitude) + 180) / 360))
        : 0.1 + (index % 6) * 0.16,
      y: asset.location?.latitude != null
        ? Math.max(0.08, Math.min(0.92, (90 - Number(asset.location.latitude)) / 180))
        : 0.12 + Math.floor(index / 6) * 0.18,
      status: toNodeStatus(asset.status),
      utilization: Math.max(0, Math.min(1, numberOr(metadata.utilization, 0))),
      load: numberOr(metadata.load_mw, 0),
      capacity: numberOr(asset.rated_capacity_mw, 0),
      cascadeContribution: numberOr(metadata.cascade_contribution, 0),
      priority: ['hospital', 'critical'].includes(toNodeKind(asset.asset_type)) ? 3 : 2,
    };
  });

  // Build edges from asset metadata.edges (deduplicated by edge id)
  const edgeMap = new Map<string, { id: string; from: string; to: string; active: boolean; load: number; flow: number }>();
  for (const asset of assets) {
    const metadata = asset.metadata && typeof asset.metadata === 'object' ? asset.metadata : {};
    const edges = Array.isArray((metadata as any).edges) ? (metadata as any).edges : [];
    for (const e of edges) {
      if (e && typeof e === 'object' && e.id && !edgeMap.has(e.id)) {
        edgeMap.set(e.id, {
          id: String(e.id),
          from: String(e.from),
          to: String(e.to),
          active: true,
          load: Math.max(0, Math.min(1, numberOr(e.load, 0.5))),
          flow: numberOr(e.flow, 1),
        });
      }
    }
  }
  const edges = Array.from(edgeMap.values());

  const risk = raw.riskLatest ?? raw.riskSummary;
  const riskScore = numberOr((risk as any)?.risk_score ?? (risk as any)?.current_score, 0);
  const cascadeProbability = numberOr((risk as any)?.cascade_probability, riskScore / 100);
  const weather = raw.weather as any;
  const rainfall = numberOr(weather?.rainfall_rate_mm_per_hour ?? weather?.rainfall_mm, 0);
  const floodRaw = numberOr(weather?.flood_risk, 0);
  const floodLevel = floodRaw > 1 ? floodRaw / 100 : floodRaw;
  const temperature = numberOr(weather?.temperature_c, 0);
  const mode = weather?.storm_detected || weather?.lightning_detected ? 'storm'
    : floodLevel > 0.6 ? 'flood'
    : rainfall > 0 ? 'rain'
    : temperature > 36 ? 'heat'
    : 'clear';

  const alerts: Alert[] = (raw.alerts as any[]).map((alert): Alert => {
  const backendLevel = String(alert.level ?? '').toLowerCase();

  const level: Alert['level'] =
    backendLevel === 'red' || backendLevel === 'black'
      ? 'critical'
      : backendLevel === 'orange' || backendLevel === 'yellow'
        ? 'warning'
        : 'info';

  return {
    id: String(alert.id),
    level,
    title: String(alert.title ?? 'Grid Alert'),
    subtitle: String(alert.message ?? ''),
    nodeId: Array.isArray(alert.affected_assets)
      ? String(alert.affected_assets[0])
      : undefined,
    cascadeWindowMin: alert.warning_horizon_minutes ?? undefined,
    timestamp: alert.created_at
      ? new Date(alert.created_at).getTime()
      : Date.now(),
  };
});

  const interventions: Intervention[] = (raw.recommendations as any[]).map((recommendation) => {
    const before = numberOr(recommendation.risk_before, 0);
    const after = numberOr(recommendation.risk_after, before);
    const effectiveness = before > 0 ? Math.max(0, Math.min(1, (before - after) / before)) : 0;
    const rationale = Array.isArray(recommendation.rationale)
      ? recommendation.rationale.join(' ')
      : String(recommendation.rationale ?? recommendation.explanation ?? '');
    return {
      id: `recommendation:${String(recommendation.id)}`,
      recommendationId: String(recommendation.id),
      recommendationStatus: String(recommendation.status ?? ''),
      verificationStatus: recommendation.verification_status ?? null,
      type: recommendationType(String(recommendation.title ?? '')),
      title: String(recommendation.title ?? 'Recommendation'),
      description: String(recommendation.explanation ?? rationale),
      effectiveness,
      cost: 0,
      active: false,
      flows: [],
      affectedNodes: [],
      recommended: true,
      reasonCode: rationale,
    };
  });

  const rationale = (raw.recommendations as any[])
    .flatMap((recommendation) => {
      const value = recommendation.rationale ?? recommendation.explanation;
      return Array.isArray(value) ? value : [value];
    })
    .filter((value): value is string => typeof value === 'string' && value.trim().length > 0)
    .slice(0, 6);

  return {
    ...base,
    timestamp: Date.now(),
    weather: {
      ...base.weather,
      mode,
      rainfall,
      windSpeed: numberOr(weather?.wind_speed_kmh, 0),
      temperature,
      humidity: numberOr(weather?.humidity_percent, 0),
      lightningRate: weather?.lightning_detected ? 1 : 0,
      floodLevel,
      cloudCover: weather?.storm_detected ? 1 : 0,
      pressure: numberOr(weather?.pressure_hpa, 0),
      visibility: numberOr(weather?.visibility_km, 0),
    },
    grid: {
      ...base.grid,
      nodes,
      edges,
      totalLoad: numberOr((raw.telemetry as any)?.total_load_mw, 0),
      totalGeneration: numberOr((raw.telemetry as any)?.total_generation_mw, 0),
      frequency: numberOr((raw.telemetry as any)?.frequency_hz, 0),
      voltage: numberOr((raw.telemetry as any)?.voltage_kv, 0),
      cascadeRisk: Math.max(0, Math.min(1, cascadeProbability)),
      stability: Math.max(0, Math.min(100, 100 - riskScore)),
      renewablesShare: (() => {
        const genNodes = nodes.filter((n) => ['generator', 'solar', 'wind', 'battery'].includes(n.kind));
        const totalGen = genNodes.reduce((s, n) => s + n.load, 0);
        const renGen = genNodes.filter((n) => ['solar', 'wind'].includes(n.kind)).reduce((s, n) => s + n.load, 0);
        return totalGen > 0 ? Math.min(1, renGen / totalGen) : 0;
      })(),
    },
    alerts,
    interventions,
    aiConfidence: Math.max(0, Math.min(1, numberOr((risk as any)?.confidence, 0) / 100)),
    rationale,
    recommendationsRaw: raw.recommendations as Array<Record<string, unknown>>,
    incidentsRaw: raw.incidents as Array<Record<string, unknown>>,
  };
}

export function useLiveData(
  location: ActiveLocation,
  intervalMs = Number(import.meta.env.VITE_POLL_INTERVAL_MS || 5000),
): LiveDataResult {
  const [data, setData] = useState<BackendSnapshot>(() => emptySnapshot());
  const [meta, setMeta] = useState<LiveMeta>({
    connected: false,
    partial: false,
    source: 'unavailable',
    lastUpdated: Date.now(),
  });
  const [refreshKey, setRefreshKey] = useState(0);
  const inFlight = useRef(false);

  useEffect(() => {
    let alive = true;
    let controller: AbortController | undefined;

    const load = async () => {
      if (inFlight.current) return;
      inFlight.current = true;
      controller = new AbortController();
      try {
        const raw = await getOracleSnapshot(location, controller.signal);
        if (!alive) return;
        const healthStatus = String((raw.health as any)?.status ?? '').toLowerCase();
        const connected = healthStatus === 'healthy' || healthStatus === 'online';
        setData(adapt(raw));
        setMeta({
          connected,
          partial: raw.failed > 0,
          source: connected ? 'api' : 'unavailable',
          lastUpdated: Date.now(),
          error: raw.failed ? `${raw.failed} backend request(s) unavailable` : undefined,
        });
      } catch (error) {
        if (alive && (error as Error).name !== 'AbortError') {
          setData(emptySnapshot());
          setMeta({
            connected: false,
            partial: false,
            source: 'unavailable',
            lastUpdated: Date.now(),
            error: error instanceof Error ? error.message : 'Backend unavailable',
          });
        }
      } finally {
        inFlight.current = false;
      }
    };

    void load();
    const interval = window.setInterval(() => { void load(); }, Math.max(2000, intervalMs));
    return () => {
      alive = false;
      controller?.abort();
      window.clearInterval(interval);
    };
  }, [intervalMs, refreshKey, location.latitude, location.longitude]);

  return { data, meta, refresh: () => setRefreshKey((value) => value + 1) };
}
