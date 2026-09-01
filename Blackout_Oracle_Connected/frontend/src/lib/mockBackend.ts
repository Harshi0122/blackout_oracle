// Simulated backend service that emits realistic weather + grid telemetry.
// In production this would be replaced with WebSocket / SSE feeds from the
// agentic-AI backend; the frontend contract stays the same.

import type {
  BackendSnapshot,
  GridData,
  Intervention,
  NodeStatus,
  PredictionPoint,
  WeatherData,
  WeatherMode,
} from './types';
import { EDGES, NODES } from './grid';

// ─── deterministic-ish PRNG so the simulation is reproducible per session ───
function mulberry32(seed: number) {
  let a = seed >>> 0;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const rand = mulberry32(42);

// ─── weather state machine ───
let weatherMode: WeatherMode = 'storm';
let weatherPhase = 0;

function generateWeather(t: number): WeatherData {
  weatherPhase += 1 / 60;
  const cycle = Math.sin(weatherPhase * 0.18) * 0.5 + 0.5; // 0..1 slow drift
  const pulse = (Math.sin(weatherPhase * 1.2) + 1) / 2; // 0..1 fast pulse

  let rainfall = 0;
  let windSpeed = 0;
  let lightningRate = 0;
  let cloudCover = 0;
  let temperature = 22;
  let humidity = 60;
  let floodLevel = 0;
  let visibility = 20;

  switch (weatherMode) {
    case 'storm': {
      rainfall = 55 + cycle * 35 + pulse * 18;
      windSpeed = 38 + cycle * 18 + pulse * 8;
      lightningRate = cycle > 0.4 ? 4 + pulse * 6 : 1;
      cloudCover = 0.82 + cycle * 0.15;
      temperature = 18 - cycle * 3;
      humidity = 86 + pulse * 8;
      floodLevel = Math.min(1, 0.35 + cycle * 0.45);
      visibility = 4 + pulse * 2;
      break;
    }
    case 'rain': {
      rainfall = 22 + cycle * 14;
      windSpeed = 18 + cycle * 8;
      lightningRate = 0.2;
      cloudCover = 0.7;
      temperature = 21;
      humidity = 78;
      floodLevel = 0.18;
      visibility = 10;
      break;
    }
    case 'heat': {
      rainfall = 0;
      windSpeed = 8 + cycle * 4;
      lightningRate = 0;
      cloudCover = 0.15;
      temperature = 36 + cycle * 4;
      humidity = 42;
      floodLevel = 0.05;
      visibility = 18;
      break;
    }
    case 'flood': {
      rainfall = 28 + cycle * 12;
      windSpeed = 14 + cycle * 6;
      lightningRate = 0.6;
      cloudCover = 0.88;
      temperature = 19;
      humidity = 92;
      floodLevel = 0.65 + cycle * 0.25;
      visibility = 6;
      break;
    }
    case 'clear':
    default: {
      rainfall = 0;
      windSpeed = 6;
      lightningRate = 0;
      cloudCover = 0.2;
      temperature = 24;
      humidity = 50;
      floodLevel = 0.05;
      visibility = 22;
      break;
    }
  }

  // Add tiny noise for liveliness.
  rainfall = Math.max(0, rainfall + (rand() - 0.5) * 4);
  windSpeed = Math.max(0, windSpeed + (rand() - 0.5) * 2);
  temperature += (rand() - 0.5) * 0.4;
  humidity = Math.max(0, Math.min(100, humidity + (rand() - 0.5) * 2));

  return {
    mode: weatherMode,
    rainfall,
    windSpeed,
    temperature,
    humidity,
    lightningRate,
    floodLevel,
    cloudCover,
    pressure: 1005 + cycle * 12,
    visibility,
  };
}

// ─── grid state derived from weather + stress ───
function generateGrid(weather: WeatherData, interventions: Intervention[]): GridData {
  // Stress scales with rainfall and wind. Battery & EV interventions reduce it.
  const interventionReduction = interventions
    .filter((i) => i.active)
    .reduce((acc, i) => acc + i.effectiveness * (1 - i.cost) * 0.25, 0);

  const baseStress = Math.min(
    1,
    weather.rainfall / 100 * 0.55 + weather.windSpeed / 80 * 0.25 + weather.floodLevel * 0.20,
  );
  const stress = Math.max(0, baseStress - interventionReduction);

  const nodes = NODES.map((n) => {
    let utilization = n.utilization;
    let status: NodeStatus = n.status;
    let cascade = n.cascadeContribution;

    // Stress increases load on hubs (substations + critical).
    const isHub = ['substation', 'hospital', 'critical'].includes(n.kind);
    if (isHub) {
      utilization = Math.min(1, n.utilization + stress * 0.35);
      cascade = Math.min(1, n.cascadeContribution + stress * 0.4);
      if (utilization > 0.9) status = 'red';
      else if (utilization > 0.75) status = 'orange';
      else if (utilization > 0.6) status = 'yellow';
      else status = 'green';
    }

    // Solar drops with cloud cover, wind rises with wind speed.
    if (n.kind === 'solar') {
      const gen = Math.max(0.05, 1 - weather.cloudCover * 1.05);
      utilization = Math.min(1, gen * (0.5 + rand() * 0.3));
      status = utilization < 0.2 ? 'yellow' : 'green';
    }
    if (n.kind === 'wind') {
      const gen = Math.min(1, weather.windSpeed / 60);
      utilization = Math.min(1, gen * (0.7 + rand() * 0.25));
      status = utilization > 0.9 ? 'yellow' : 'green';
    }

    // Battery discharges if intervention active.
    if (n.kind === 'battery') {
      const draining = interventions.some((i) => i.active && i.type === 'battery');
      utilization = Math.max(0.05, n.utilization + (draining ? -0.02 : 0.005));
    }

    // Apply intervention-driven status upgrades (RED→GREEN transitions).
    if (interventions.some((i) => i.active && i.affectedNodes.includes(n.id))) {
      const order: NodeStatus[] = ['red', 'orange', 'yellow', 'green'];
      const cur = order.indexOf(status);
      if (cur > 0) status = order[cur - 1];
      utilization = Math.max(0, utilization - 0.15);
      cascade = Math.max(0, cascade - 0.2);
    }

    return {
      ...n,
      utilization,
      status,
      load: utilization * n.capacity,
      cascadeContribution: cascade,
    };
  });

  // Edges: flow tracks from generation → load.
  const activeBatt = interventions.some((i) => i.active && i.type === 'battery');
  const reroute = interventions.some((i) => i.active && i.type === 'reroute');
  const edges = EDGES.map((e) => {
    let load = e.load;
    let active = e.active;
    let flow = e.flow;
    const fromN = nodes.find((n) => n.id === e.from)!;
    const toN = nodes.find((n) => n.id === e.to)!;

    // Load edge scales with utilization of the destination.
    load = Math.min(1, (fromN.utilization + toN.utilization) / 2);
    if (toN.status === 'red') load = Math.min(1, load * 1.2);
    if (toN.status === 'orange') load = Math.min(1, load * 1.05);

    if (activeBatt && (e.from === 'BAT-1' || e.from === 'BAT-2')) {
      load = Math.min(1, load + 0.2);
    }
    if (reroute && (e.id === 'e7' || e.id === 'e9')) {
      load = Math.min(1, load + 0.15);
      flow = 1;
    }
    return { ...e, load, active, flow };
  });

  // Aggregate metrics.
  const totalLoad = nodes.reduce((s, n) => s + n.load, 0);
  const totalGeneration = nodes
    .filter((n) => ['generator', 'solar', 'wind', 'battery'].includes(n.kind))
    .reduce((s, n) => s + n.load, 0);

  const cascadeRisk = Math.min(1, 0.18 + stress * 0.62 + (nodes.find((n) => n.id === 'SUB-A')?.cascadeContribution ?? 0) * 0.2);
  const stability = Math.max(20, 100 - stress * 60 - cascadeRisk * 25);
  const renewablesShare = (() => {
    const ren = nodes
      .filter((n) => ['solar', 'wind'].includes(n.kind))
      .reduce((s, n) => s + n.load, 0);
    return Math.min(1, ren / Math.max(1, totalGeneration));
  })();

  return {
    nodes,
    edges,
    totalLoad,
    totalGeneration,
    frequency: 50 - stress * 0.18,
    voltage: 230 - stress * 4,
    cascadeRisk,
    stability,
    renewablesShare,
  };
}

// ─── interventions ───
function generateInterventions(grid: GridData, weather: WeatherData): Intervention[] {
  const list: Intervention[] = [
    {
      id: 'int-batt',
      type: 'battery',
      title: 'DISPATCH BATTERY BANK A',
      description:
        'Inject 48 MW from Battery Bank A into Substation A to relieve overload and protect Central Hospital.',
      effectiveness: 0.78,
      cost: 0.22,
      active: false,
      flows: [
        { from: 'BAT-1', to: 'SUB-A', amount: 48 },
        { from: 'SUB-A', to: 'HOSP', amount: 32 },
      ],
      affectedNodes: ['BAT-1', 'SUB-A', 'HOSP'],
      recommended: grid.cascadeRisk > 0.5,
      reasonCode: 'CASCADE_OVERLOAD_MITIGATION',
    },
    {
      id: 'int-ev',
      type: 'ev_demand',
      title: 'EV DEMAND RESPONSE',
      description:
        'Curtail 18% of EV charging load across Industrial Zones during peak storm window (-22 MW).',
      effectiveness: 0.42,
      cost: 0.10,
      active: false,
      flows: [{ from: 'IND-1', to: 'IND-2', amount: -22 }],
      affectedNodes: ['IND-1', 'IND-2'],
      recommended: weather.rainfall > 40 && grid.cascadeRisk > 0.4,
      reasonCode: 'PEAK_SHAVING',
    },
    {
      id: 'int-reroute',
      type: 'reroute',
      title: 'REROUTE AROUND SUB-A',
      description:
        'Open breaker 7-A, reroute 60 MW via Substation B → D → Hospital to bypass overheating bus.',
      effectiveness: 0.85,
      cost: 0.35,
      active: false,
      flows: [
        { from: 'SUB-B', to: 'SUB-D', amount: 60 },
        { from: 'SUB-D', to: 'HOSP', amount: 35 },
      ],
      affectedNodes: ['SUB-B', 'SUB-D', 'HOSP', 'SUB-A'],
      recommended: grid.cascadeRisk > 0.55,
      reasonCode: 'TOPOLOGY_PROTECTION',
    },
    {
      id: 'int-shed',
      type: 'loadshed',
      title: 'ROTATING LOAD SHED',
      description:
        'Reduce non-critical Residential North load by 35% for 12 minutes to stabilize frequency.',
      effectiveness: 0.55,
      cost: 0.45,
      active: false,
      flows: [{ from: 'RES-1', to: 'RES-1', amount: -17 }],
      affectedNodes: ['RES-1'],
      recommended: grid.cascadeRisk > 0.75,
      reasonCode: 'FREQUENCY_STABILIZATION',
    },
  ];
  return list;
}

// ─── predictions (NOW → +60m) ───
function generatePredictions(grid: GridData, weather: WeatherData): PredictionPoint[] {
  const labels = [
    { label: 'NOW', offsetMin: 0 },
    { label: '+5 MIN', offsetMin: 5 },
    { label: '+10 MIN', offsetMin: 10 },
    { label: '+15 MIN', offsetMin: 15 },
    { label: '+30 MIN', offsetMin: 30 },
    { label: '+60 MIN', offsetMin: 60 },
  ];

  return labels.map(({ label, offsetMin }, idx) => {
    // Each step ramps weather + stress further (peaks at +30).
    const ramp = Math.min(1.4, idx * 0.18 + 0.05);
    const rainfall = weather.rainfall * ramp + idx * 1.5;
    const windSpeed = weather.windSpeed * (1 + idx * 0.05);
    const temperature = weather.temperature + (idx - 1) * 0.3;
    const demand = (grid.totalLoad / 6) * (1 + idx * 0.04);
    const solarGen = Math.max(8, 36 - idx * 4 - weather.cloudCover * 18);
    const windGen = Math.min(140, grid.totalGeneration * 0.18 * (1 + idx * 0.06));
    const batterySoC = Math.max(10, 80 - idx * 9);
    const gridStress = Math.min(1, grid.cascadeRisk + idx * 0.08);
    const cascadeProbability = Math.min(1, grid.cascadeRisk + idx * 0.06);

    const nodeStatuses: Record<string, NodeStatus> = {};
    grid.nodes.forEach((n) => {
      if (idx === 0) {
        nodeStatuses[n.id] = n.status;
        return;
      }
      const drift = idx * 0.05;
      const u = n.utilization + drift;
      let s: NodeStatus = 'green';
      if (u > 0.9) s = 'red';
      else if (u > 0.75) s = 'orange';
      else if (u > 0.6) s = 'yellow';
      nodeStatuses[n.id] = s;
    });

    return {
      label,
      offsetMin,
      rainfall,
      windSpeed,
      temperature,
      demand,
      solarGen,
      windGen,
      batterySoC,
      gridStress,
      cascadeProbability,
      nodeStatuses,
    };
  });
}

// ─── cascade propagation sequence (used by CascadeSim) ───
function generateCascadeSteps(grid: GridData, weather: WeatherData) {
  const steps: { t: number; nodeId: string; status: NodeStatus; message: string }[] = [];
  const trail = ['SUB-A', 'SUB-D', 'HOSP', 'CRIT'];
  trail.forEach((id, i) => {
    const node = grid.nodes.find((n) => n.id === id);
    if (!node) return;
    const t = i * 4.2;
    let status: NodeStatus = 'yellow';
    if (i === 0) status = 'orange';
    if (i === 1) status = 'orange';
    if (i >= 2) status = 'red';
    const messages = [
      `${node.name} surge detected — load at ${(node.utilization * 100).toFixed(0)}%`,
      `Energy redistributing toward ${node.name}`,
      `${node.name} critical — protective relays opening`,
      `Cascade reaches critical load — initiating AI mitigation`,
    ];
    steps.push({ t, nodeId: id, status, message: messages[i] ?? 'Stress spreading' });
  });
  return steps;
}

// ─── alerts ───
function generateAlerts(grid: GridData, weather: WeatherData) {
  const alerts: import('./types').Alert[] = [
    {
      id: 'a1',
      level: 'critical',
      title: 'SUBSTATION A OVERLOAD RISK',
      subtitle: 'Breaker 7-A approaching thermal limit',
      nodeId: 'SUB-A',
      cascadeWindowMin: 17,
      timestamp: Date.now(),
    },
  ];
  if (weather.rainfall > 50) {
    alerts.push({
      id: 'a2',
      level: 'warning',
      title: 'HEAVY RAINFALL WARNING',
      subtitle: `Storm cell B at ${weather.rainfall.toFixed(0)} mm/hr over west sector`,
      timestamp: Date.now(),
    });
  }
  if (weather.floodLevel > 0.5) {
    alerts.push({
      id: 'a3',
      level: 'warning',
      title: 'FLOOD INFRASTRUCTURE RISK',
      subtitle: 'Substation C secondary access flooded',
      nodeId: 'SUB-C',
      timestamp: Date.now(),
    });
  }
  return alerts;
}

// ─── public API ───
export function setWeatherMode(mode: WeatherMode) {
  weatherMode = mode;
}

export function snapshot(): BackendSnapshot {
  const weather = generateWeather(performance.now());
  const interventions = generateInterventions(
    { cascadeRisk: 0, totalLoad: 600 } as GridData,
    weather,
  );
  const grid = generateGrid(weather, interventions);
  // recompute interventions with real grid state so recommendations make sense
  const realInterventions = generateInterventions(grid, weather);
  const predictions = generatePredictions(grid, weather);
  const cascadeSteps = generateCascadeSteps(grid, weather);
  const alerts = generateAlerts(grid, weather);
  const rationale = [
    'Cascade risk is converging on Substation A — breaker stress sustained > 90s.',
    'Battery dispatch would lower SUB-A utilization by 18% within 90s.',
    'Reroute via SUB-D reduces worst-case cascade probability from 0.78 → 0.31.',
  ];
  return {
    timestamp: Date.now(),
    weather,
    grid,
    interventions: realInterventions,
    cascadeSteps,
    alerts,
    predictions,
    aiConfidence: 0.82 + (rand() - 0.5) * 0.08,
    rationale,
  };
}

// Export the static topology for components that need it directly.
export const TOPOLOGY = { nodes: NODES, edges: EDGES };