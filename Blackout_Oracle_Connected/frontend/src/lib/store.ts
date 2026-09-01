import type { InterventionType, WeatherMode } from './types';

// Tiny global store for cross-view UI state (active interventions, view mode, etc).
// Lightweight pub/sub — zero external deps.

type Listener = () => void;

interface State {
  view: 'landing' | 'command' | 'digital-twin' | 'cascade' | 'interventions' | 'before-after';
  weatherMode: WeatherMode;
  // active intervention IDs
  activeInterventions: Set<InterventionType>;
  criticalAlertId: string | null;
  scenarioMode: 'live' | 'whatif' | 'do-nothing';
  scrubTimeMin: number; // 0..60
  cameraFocus: string | null; // node id to focus on
}

let state: State = {
  view: 'landing',
  weatherMode: 'storm',
  activeInterventions: new Set(),
  criticalAlertId: 'a1',
  scenarioMode: 'live',
  scrubTimeMin: 0,
  cameraFocus: null,
};

const listeners = new Set<Listener>();

export const store = {
  get(): State {
    return state;
  },
  set(patch: Partial<State>) {
    state = { ...state, ...patch };
    if (patch.activeInterventions) {
      state.activeInterventions = new Set(patch.activeInterventions);
    }
    listeners.forEach((l) => l());
  },
  toggleIntervention(type: InterventionType) {
    const next = new Set(state.activeInterventions);
    if (next.has(type)) next.delete(type);
    else next.add(type);
    state = { ...state, activeInterventions: next };
    listeners.forEach((l) => l());
  },
  subscribe(l: Listener) {
    listeners.add(l);
    return () => {
      listeners.delete(l);
    };
  },
};