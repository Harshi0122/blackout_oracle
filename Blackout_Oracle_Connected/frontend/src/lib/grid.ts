import type { GridNode, GridEdge } from './types';

// Topology of the smart-grid digital twin — laid out as a logical flow
// from generation (left) through substations (middle) to consumers (right).
// Coordinates are normalized 0..1 so the SVG renderer scales cleanly.

export const NODES: GridNode[] = [
  // ── Generation (sources) ──
  { id: 'GEN-N', name: 'NORTH GAS GEN', kind: 'generator', x: 0.08, y: 0.22, status: 'green', utilization: 0.72, load: 145, capacity: 200, cascadeContribution: 0.15, priority: 2 },
  { id: 'GEN-S', name: 'SOUTH GAS GEN', kind: 'generator', x: 0.08, y: 0.62, status: 'green', utilization: 0.65, load: 130, capacity: 200, cascadeContribution: 0.15, priority: 2 },
  { id: 'SOLAR-W', name: 'WEST SOLAR FARM', kind: 'solar', x: 0.14, y: 0.42, status: 'yellow', utilization: 0.30, load: 36, capacity: 120, cascadeContribution: 0.05, priority: 1 },
  { id: 'WIND-N', name: 'OFFSHORE WIND', kind: 'wind', x: 0.10, y: 0.82, status: 'green', utilization: 0.85, load: 102, capacity: 120, cascadeContribution: 0.08, priority: 1 },
  { id: 'BAT-1', name: 'BATTERY BANK A', kind: 'battery', x: 0.22, y: 0.16, status: 'green', utilization: 0.40, load: 48, capacity: 120, cascadeContribution: 0.10, priority: 2 },
  { id: 'BAT-2', name: 'BATTERY BANK B', kind: 'battery', x: 0.22, y: 0.84, status: 'green', utilization: 0.35, load: 42, capacity: 120, cascadeContribution: 0.10, priority: 2 },

  // ── Transmission (substations) ──
  { id: 'SUB-A', name: 'SUBSTATION A', kind: 'substation', x: 0.40, y: 0.25, status: 'orange', utilization: 0.91, load: 91, capacity: 100, cascadeContribution: 0.78, priority: 3 },
  { id: 'SUB-B', name: 'SUBSTATION B', kind: 'substation', x: 0.40, y: 0.50, status: 'yellow', utilization: 0.74, load: 74, capacity: 100, cascadeContribution: 0.42, priority: 3 },
  { id: 'SUB-C', name: 'SUBSTATION C', kind: 'substation', x: 0.40, y: 0.75, status: 'green', utilization: 0.52, load: 52, capacity: 100, cascadeContribution: 0.18, priority: 3 },
  { id: 'SUB-D', name: 'SUBSTATION D', kind: 'substation', x: 0.55, y: 0.38, status: 'yellow', utilization: 0.68, load: 68, capacity: 100, cascadeContribution: 0.32, priority: 3 },

  // ── Distribution (loads) ──
  { id: 'IND-1', name: 'INDUSTRIAL ZONE 1', kind: 'industrial', x: 0.66, y: 0.18, status: 'yellow', utilization: 0.71, load: 71, capacity: 100, cascadeContribution: 0.22, priority: 2 },
  { id: 'IND-2', name: 'INDUSTRIAL ZONE 2', kind: 'industrial', x: 0.66, y: 0.62, status: 'green', utilization: 0.55, load: 55, capacity: 100, cascadeContribution: 0.18, priority: 2 },
  { id: 'RES-1', name: 'RESIDENTIAL NORTH', kind: 'residential', x: 0.78, y: 0.30, status: 'green', utilization: 0.48, load: 48, capacity: 100, cascadeContribution: 0.10, priority: 1 },
  { id: 'RES-2', name: 'RESIDENTIAL SOUTH', kind: 'residential', x: 0.78, y: 0.72, status: 'green', utilization: 0.44, load: 44, capacity: 100, cascadeContribution: 0.08, priority: 1 },
  { id: 'HOSP', name: 'CENTRAL HOSPITAL', kind: 'hospital', x: 0.88, y: 0.42, status: 'orange', utilization: 0.82, load: 41, capacity: 50, cascadeContribution: 0.65, priority: 3 },
  { id: 'CRIT', name: 'EMERGENCY OPS', kind: 'critical', x: 0.88, y: 0.58, status: 'red', utilization: 0.95, load: 28.5, capacity: 30, cascadeContribution: 0.85, priority: 3 },
  { id: 'DATA', name: 'DATA CENTER', kind: 'critical', x: 0.74, y: 0.50, status: 'yellow', utilization: 0.69, load: 69, capacity: 100, cascadeContribution: 0.55, priority: 3 },
];

export const EDGES: GridEdge[] = [
  // Generators → Substations
  { id: 'e1', from: 'GEN-N', to: 'SUB-A', active: true, load: 0.78, flow: 1 },
  { id: 'e2', from: 'GEN-S', to: 'SUB-C', active: true, load: 0.72, flow: 1 },
  { id: 'e3', from: 'SOLAR-W', to: 'SUB-B', active: true, load: 0.32, flow: 1 },
  { id: 'e4', from: 'WIND-N', to: 'SUB-C', active: true, load: 0.68, flow: 1 },
  { id: 'e5', from: 'BAT-1', to: 'SUB-A', active: true, load: 0.45, flow: 1 },
  { id: 'e6', from: 'BAT-2', to: 'SUB-B', active: true, load: 0.40, flow: 1 },

  // Substation interconnect
  { id: 'e7', from: 'SUB-A', to: 'SUB-D', active: true, load: 0.65, flow: 1 },
  { id: 'e8', from: 'SUB-B', to: 'SUB-D', active: true, load: 0.55, flow: -1 },
  { id: 'e9', from: 'SUB-C', to: 'SUB-D', active: true, load: 0.42, flow: 1 },

  // Substations → Loads
  { id: 'e10', from: 'SUB-D', to: 'IND-1', active: true, load: 0.62, flow: 1 },
  { id: 'e11', from: 'SUB-D', to: 'IND-2', active: true, load: 0.48, flow: 1 },
  { id: 'e12', from: 'SUB-D', to: 'RES-1', active: true, load: 0.40, flow: 1 },
  { id: 'e13', from: 'SUB-D', to: 'RES-2', active: true, load: 0.38, flow: 1 },
  { id: 'e14', from: 'SUB-A', to: 'HOSP', active: true, load: 0.82, flow: 1 },
  { id: 'e15', from: 'SUB-B', to: 'DATA', active: true, load: 0.58, flow: 1 },
  { id: 'e16', from: 'SUB-C', to: 'CRIT', active: true, load: 0.88, flow: 1 },
  { id: 'e17', from: 'SUB-B', to: 'RES-1', active: true, load: 0.32, flow: 1 },
  { id: 'e18', from: 'SUB-C', to: 'IND-2', active: true, load: 0.45, flow: 1 },
];