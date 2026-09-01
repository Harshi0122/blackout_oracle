import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, AlertTriangle, ArrowDown, Battery, Brain, ChevronDown, ChevronUp, CloudRain, Cpu, Droplets, Gauge, Lightbulb, Sparkles, Thermometer, Wind } from 'lucide-react';
import type { BackendSnapshot } from '../lib/types';
import { WeatherFX } from './WeatherFX';
import { SmartGrid } from './SmartGrid';
import { CascadeRisk } from './CascadeRisk';
import { WeatherViz } from './WeatherViz';
import { TimelineScrubber } from './TimelineScrubber';
import { CascadeSim } from './CascadeSim';
import { InterventionPanel } from './InterventionPanel';
import { BeforeAfter } from './BeforeAfter';
import { DigitalTwin, type TwinConfig } from './DigitalTwin';
import { CriticalAlert } from './CriticalAlert';
import { Panel } from './Panel';
import { Live } from './Live';
import { NumberAnim } from './NumberAnim';
import { store } from '../lib/store';
import { HudNav, type ViewKey } from './HudNav';
import { SimulationRunner } from './SimulationRunner';

interface Props {
  data: BackendSnapshot;
  operatorId: string;
  onRefresh: () => void;
}

export function CommandCenter({ data, operatorId, onRefresh }: Props) {
  const [view, setView] = useState<ViewKey>('command');
  const [focusedNode, setFocusedNode] = useState<string | null>(null);
  const [scrubMin, setScrubMin] = useState(0);
  const [showLeftPanel, setShowLeftPanel] = useState(true);
  const [showRightPanel, setShowRightPanel] = useState(true);

  // ── Subscriptions to global intervention state ──
  const [, force] = useState(0);
  useEffect(() => store.subscribe(() => force((x) => x + 1)), []);

  // ── Derived "scenario" — apply timeline scrub offsets ──
  const activeInterventions = store.get().activeInterventions;
  const effectiveData = useMemo(() => {
    // Apply scrub: interpolate predictions into a grid snapshot
    const pred = data.predictions.reduce((acc, p) => (p.offsetMin <= scrubMin ? p : acc), data.predictions[0]);
    if (!pred) return data;

    const nodes = data.grid.nodes.map((n) => ({
      ...n,
      status: pred.nodeStatuses[n.id] ?? n.status,
      utilization: Math.min(1, n.utilization + pred.gridStress * 0.15 * (scrubMin / 60)),
    }));
    const edges = data.grid.edges.map((e) => {
      const fromN = nodes.find((n) => n.id === e.from)!;
      const toN = nodes.find((n) => n.id === e.to)!;
      return { ...e, load: Math.min(1, (fromN.utilization + toN.utilization) / 2) };
    });

    const cascadeRisk = Math.min(1, pred.cascadeProbability);
    const stability = Math.max(20, 100 - pred.gridStress * 65 - cascadeRisk * 25);

    return {
      ...data,
      grid: { ...data.grid, nodes, edges, cascadeRisk, stability },
      weather: { ...data.weather, rainfall: pred.rainfall, windSpeed: pred.windSpeed, temperature: pred.temperature },
    };
  }, [data, scrubMin]);

  // ── "What if" grid for digital twin ──
  const [twinConfig, setTwinConfig] = useState<TwinConfig>({
    rainfall: 50, wind: 35, temp: 20, demand: 60, solar: 30, windGen: 70, battery: 60, substationFailed: null,
  });

  const twinGrid = useMemo(() => {
    const stress = Math.min(1, twinConfig.rainfall / 100 * 0.5 + twinConfig.wind / 80 * 0.25 + (twinConfig.demand / 100) * 0.25);
    const nodes = data.grid.nodes.map((n) => {
      let utilization = n.utilization;
      let status = n.status;
      const isHub = ['substation', 'hospital', 'critical'].includes(n.kind);
      const isFailed = twinConfig.substationFailed === n.id;
      if (isHub) {
        utilization = Math.min(1, n.utilization + stress * 0.45);
        if (isFailed) { utilization = 1; status = 'red'; }
        else if (utilization > 0.9) status = 'red';
        else if (utilization > 0.75) status = 'orange';
        else if (utilization > 0.6) status = 'yellow';
        else status = 'green';
      }
      if (n.kind === 'solar') utilization = Math.min(1, twinConfig.solar / 100);
      if (n.kind === 'wind') utilization = Math.min(1, twinConfig.windGen / 100);
      return { ...n, utilization, status, load: utilization * n.capacity };
    });
    return {
      ...data.grid,
      nodes,
      cascadeRisk: Math.min(1, 0.15 + stress * 0.65 + (twinConfig.substationFailed ? 0.25 : 0)),
      stability: Math.max(20, 100 - stress * 65 - (twinConfig.substationFailed ? 30 : 0)),
    };
  }, [data.grid, twinConfig]);

  // ── "Do nothing" scenario for before/after ──
  const doNothing = useMemo(() => {
    const stress = Math.min(1, data.weather.rainfall / 100 * 0.5 + data.weather.windSpeed / 80 * 0.25);
    const nodes = data.grid.nodes.map((n) => {
      const isHub = ['substation', 'hospital', 'critical'].includes(n.kind);
      let utilization = n.utilization;
      let status = n.status;
      if (isHub) {
        utilization = Math.min(1, n.utilization + stress * 0.4);
        if (utilization > 0.9) status = 'red';
        else if (utilization > 0.75) status = 'orange';
      }
      return { ...n, utilization, status, load: utilization * n.capacity };
    });
    return {
      weather: data.weather,
      grid: {
        ...data.grid,
        nodes,
        cascadeRisk: Math.min(1, data.grid.cascadeRisk + 0.15),
        stability: Math.max(20, data.grid.stability - 18),
      },
    };
  }, [data]);

  const criticalAlert = data.alerts.find((a) => a.level === 'critical');

  return (
    <div className="absolute inset-0 flex flex-col">
      {/* Top HUD bar */}
      <header className="relative z-20 flex items-center justify-between px-5 py-2.5 border-b border-cyan-400/10 bg-black/40 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center font-bold text-slate-900">B</div>
          <div className="leading-tight">
            <div className="text-[11px] font-display tracking-[0.32em] text-cyan-300">BLACKOUT ORACLE</div>
            <div className="text-[10px] font-mono text-slate-400">CLIMATE GRID COMMAND CENTER · v2.4</div>
          </div>
        </div>
        <HudNav active={view} onChange={setView} />
        <div className="flex items-center gap-3">
          <AIMeter confidence={data.aiConfidence} />
          <Live />
          <button
            onClick={() => store.set({ view: 'landing' })}
            className="px-2.5 py-1 rounded text-[10px] tracking-[0.2em] font-display text-cyan-300 border border-cyan-400/30 hover:bg-cyan-500/10 transition"
          >
            EXIT
          </button>
        </div>
      </header>

      {/* Main grid layout */}
      <div className="flex-1 flex min-h-0">
        {/* Left panel */}
        <AnimatePresence initial={false}>
          {showLeftPanel && (
            <motion.aside
              initial={{ x: -340, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -340, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 200, damping: 28 }}
              className="w-[340px] shrink-0 border-r border-cyan-400/10 bg-black/40 backdrop-blur-md p-3 space-y-3 overflow-y-auto"
            >
              <Panel title="LIVE ENVIRONMENT" subtitle="Backend weather feed" icon={<CloudRain size={14} />}>
                <WeatherViz weather={data.weather} />
              </Panel>

              <Panel title="CASCADE RISK" subtitle="AI aggregate" icon={<Gauge size={14} />} accent={effectiveData.grid.cascadeRisk > 0.6 ? 'red' : effectiveData.grid.cascadeRisk > 0.4 ? 'amber' : 'cyan'}>
                <CascadeRisk risk={effectiveData.grid.cascadeRisk} stability={effectiveData.grid.stability} />
                <div className="mt-3 text-[11px] font-mono text-slate-400 leading-snug">
                  Probability that <span className="text-rose-300">SUB-A</span> overload cascades into{' '}
                  <span className="text-rose-300">HOSP</span> or <span className="text-rose-300">CRIT</span> within 17 min.
                </div>
              </Panel>

              <Panel title="AI RATIONALE" subtitle="Why we're intervening" icon={<Brain size={14} />} accent="cyan">
                <ul className="space-y-2">
                  {data.rationale.map((r, i) => (
                    <li key={i} className="flex gap-2 text-[11px] text-slate-300">
                      <span className="text-cyan-400 font-mono mt-0.5">{String(i + 1).padStart(2, '0')}</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </Panel>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Center content */}
        <main className="flex-1 relative min-w-0">
          {/* Background weather FX layer */}
          <WeatherFX weather={data.weather} intensity={view === 'before-after' ? 0.5 : 1} />

          {/* Panel toggles */}
          <div className="absolute top-3 left-3 z-20 flex flex-col gap-1.5">
            <PanelToggle on={showLeftPanel} onClick={() => setShowLeftPanel((v) => !v)} direction="left" />
            <PanelToggle on={showRightPanel} onClick={() => setShowRightPanel((v) => !v)} direction="right" />
          </div>

          {/* View body */}
          <AnimatePresence mode="wait">
            <motion.div
              key={view}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.35 }}
              className="absolute inset-0 p-4"
            >
              {view === 'command' && <CommandView data={effectiveData} focusedNode={focusedNode} onFocusNode={setFocusedNode} scrubMin={scrubMin} setScrubMin={setScrubMin} />}
              {view === 'cascade' && <CascadeView data={data} />}
              {view === 'digital-twin' && <TwinView data={effectiveData} twinGrid={twinGrid} twinConfig={twinConfig} setTwinConfig={setTwinConfig} />}
              {view === 'interventions' && <InterventionsView data={data} operatorId={operatorId} onRefresh={onRefresh} />}
              {view === 'before-after' && <BeforeAfterView data={data} doNothing={doNothing} />}
            </motion.div>
          </AnimatePresence>
        </main>

        {/* Right panel */}
        <AnimatePresence initial={false}>
          {showRightPanel && (
            <motion.aside
              initial={{ x: 340, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 340, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 200, damping: 28 }}
              className="w-[340px] shrink-0 border-l border-cyan-400/10 bg-black/40 backdrop-blur-md p-3 space-y-3 overflow-y-auto"
            >
              <Panel title="GRID TELEMETRY" subtitle="Real-time aggregate" icon={<Activity size={14} />} accent="cyan">
                <div className="grid grid-cols-2 gap-2">
                  <Metric icon={<Activity size={12} />} label="STABILITY" value={`${Math.round(effectiveData.grid.stability)}%`} color={effectiveData.grid.stability < 60 ? 'text-rose-300' : 'text-cyan-300'} />
                  <Metric icon={<Gauge size={12} />} label="CASCADE" value={`${Math.round(effectiveData.grid.cascadeRisk * 100)}%`} color={effectiveData.grid.cascadeRisk > 0.6 ? 'text-rose-300' : 'text-amber-300'} />
                  <Metric icon={<Cpu size={12} />} label="FREQUENCY" value={`${effectiveData.grid.frequency.toFixed(2)} Hz`} color="text-cyan-300" />
                  <Metric icon={<Lightbulb size={12} />} label="VOLTAGE" value={`${effectiveData.grid.voltage.toFixed(0)} kV`} color="text-cyan-300" />
                  <Metric icon={<Sparkles size={12} />} label="RENEWABLES" value={`${Math.round(effectiveData.grid.renewablesShare * 100)}%`} color="text-emerald-300" />
                  <Metric icon={<Battery size={12} />} label="DEMAND" value={`${Math.round(effectiveData.grid.totalLoad)} MW`} color="text-amber-300" />
                </div>
              </Panel>

              <Panel title="ALERTS" subtitle="Active warnings" icon={<AlertTriangle size={14} />} accent="red">
                <div className="space-y-2">
                  {data.alerts.map((a) => (
                    <div key={a.id} className={`rounded-md p-2.5 border ${
                      a.level === 'critical' ? 'bg-rose-500/10 border-rose-400/30' : 'bg-amber-500/10 border-amber-400/30'
                    }`}>
                      <div className="flex items-center gap-2">
                        <AlertTriangle size={12} className={a.level === 'critical' ? 'text-rose-300' : 'text-amber-300'} />
                        <span className={`text-[10px] tracking-[0.22em] font-display ${a.level === 'critical' ? 'text-rose-300' : 'text-amber-300'}`}>
                          {a.level.toUpperCase()}
                        </span>
                      </div>
                      <div className="text-xs text-white font-display mt-1">{a.title}</div>
                      <div className="text-[11px] text-slate-300 mt-0.5">{a.subtitle}</div>
                    </div>
                  ))}
                </div>
              </Panel>

              <Panel title="AI INTERVENTIONS" subtitle="Suggested actions" icon={<Sparkles size={14} />} accent="green">
                <div className="space-y-2">
                  {data.interventions.map((intv) => {
                    const isOn = activeInterventions.has(intv.type);
                    return (
                      <div key={intv.id} className={`rounded-md p-2 border transition ${
                        isOn ? 'border-emerald-400/40 bg-emerald-500/5' : 'border-cyan-400/15 bg-black/30'
                      }`}>
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-display text-white truncate">{intv.title}</div>
                            <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                              E {Math.round(intv.effectiveness * 100)}% · C {Math.round(intv.cost * 100)}%
                            </div>
                          </div>
                          <button
                            onClick={() => store.toggleIntervention(intv.type)}
                            className={`shrink-0 px-2 py-0.5 rounded text-[9px] font-display tracking-widest transition ${
                              isOn
                                ? 'bg-emerald-500/30 text-emerald-200 border border-emerald-400/40'
                                : 'bg-cyan-500/10 text-cyan-200 border border-cyan-400/30 hover:bg-cyan-500/20'
                            }`}
                          >
                            {isOn ? 'ON' : 'OFF'}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Panel>
            </motion.aside>
          )}
        </AnimatePresence>
      </div>

      {/* Cinematic critical alert */}
      {criticalAlert && <CriticalAlert alert={criticalAlert} grid={data.grid} operatorId={operatorId} onMutated={onRefresh} />}
    </div>
  );
}

// ─── Sub-views ─────────────────────────────────────────────────────────────

function CommandView({ data, focusedNode, onFocusNode, scrubMin, setScrubMin }: any) {
  return (
    <div className="h-full flex flex-col gap-3">
      {/* Top: timeline + key metrics */}
      <div className="glass hud-bracket rounded-lg p-3">
        <TimelineScrubber predictions={data.predictions} scrubMin={scrubMin} onScrub={setScrubMin} />
      </div>
      {/* Bottom: split — grid + status */}
      <div className="flex-1 grid grid-cols-12 gap-3 min-h-0">
        <div className="col-span-9 glass hud-bracket rounded-lg relative overflow-hidden">
          <div className="absolute top-3 left-3 z-10 flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-cyan-500/15 border border-cyan-400/30 text-[10px] tracking-[0.22em] font-display text-cyan-300">SMART GRID · LIVE DIGITAL TWIN</span>
            <span className="text-[10px] font-mono text-slate-400">{data.grid.nodes.length} NODES · {data.grid.edges.length} LINKS</span>
          </div>
          <div className="absolute top-3 right-3 z-10 text-[10px] font-mono text-cyan-300/80">
            FOCUS · <span className="text-cyan-200">{focusedNode ?? '—'}</span>
          </div>
          <SmartGrid data={data.grid} onFocusNode={onFocusNode} focusedNodeId={focusedNode} />
        </div>

        <div className="col-span-3 space-y-3 overflow-y-auto">
          <Panel title="STRESS DISTRIBUTION" subtitle="Utilization by tier" icon={<Gauge size={14} />} accent="amber">
            <StressBars grid={data.grid} />
          </Panel>
          <Panel title="GENERATION MIX" subtitle="Live generation" icon={<Sparkles size={14} />} accent="green">
            <GenerationMix grid={data.grid} />
          </Panel>
        </div>
      </div>
    </div>
  );
}

function CascadeView({ data }: any) {
  return (
    <div className="h-full grid grid-cols-12 gap-3">
      <div className="col-span-7 glass hud-bracket rounded-lg relative overflow-hidden">
        <div className="absolute top-3 left-3 z-10 px-2 py-0.5 rounded bg-rose-500/15 border border-rose-400/30 text-[10px] tracking-[0.22em] font-display text-rose-300">CASCADE PROPAGATION SIM</div>
        <SmartGrid data={data.grid} />
      </div>
      <div className="col-span-5 glass hud-bracket rounded-lg overflow-hidden">
        <CascadeSim grid={data.grid} steps={data.cascadeSteps} />
      </div>
    </div>
  );
}

function TwinView({ data, twinGrid, twinConfig, setTwinConfig }: any) {
  return (
    <div className="h-full grid grid-cols-12 gap-3">
      <div className="col-span-4 space-y-3 overflow-y-auto">
        <DigitalTwin config={twinConfig} onChange={setTwinConfig} />
        <SimulationRunner config={twinConfig} />
        <Panel title="SIM RESULT" subtitle="Realtime readouts" icon={<Gauge size={14} />}>
          <div className="space-y-2 text-xs font-mono">
            <Readout label="CASCADE RISK" value={`${(twinGrid.cascadeRisk * 100).toFixed(0)}%`} color={twinGrid.cascadeRisk > 0.6 ? 'text-rose-300' : 'text-cyan-300'} />
            <Readout label="GRID STABILITY" value={`${twinGrid.stability.toFixed(0)}%`} color={twinGrid.stability < 50 ? 'text-rose-300' : 'text-emerald-300'} />
            <Readout label="CRITICAL NODES" value={twinGrid.nodes.filter((n: any) => n.status === 'red').length.toString()} color="text-rose-300" />
            <Readout label="WARN NODES" value={twinGrid.nodes.filter((n: any) => n.status === 'orange' || n.status === 'yellow').length.toString()} color="text-amber-300" />
          </div>
        </Panel>
      </div>
      <div className="col-span-8 glass hud-bracket rounded-lg relative overflow-hidden">
        <div className="absolute top-3 left-3 z-10 px-2 py-0.5 rounded bg-cyan-500/15 border border-cyan-400/30 text-[10px] tracking-[0.22em] font-display text-cyan-300">DIGITAL TWIN · LIVE</div>
        <SmartGrid data={twinGrid} />
      </div>
    </div>
  );
}

function InterventionsView({ data, operatorId, onRefresh }: any) {
  return (
    <div className="h-full overflow-y-auto">
      <InterventionPanel interventions={data.interventions} baseGrid={data.grid} operatorId={operatorId} onMutated={onRefresh} />
    </div>
  );
}

function BeforeAfterView({ data, doNothing }: any) {
  // "with AI" applies the active interventions
  const active = store.get().activeInterventions;
  const withAi = useMemo(() => {
    const nodes = data.grid.nodes.map((n: any) => {
      const intv = data.interventions.find((i: any) => active.has(i.type) && i.affectedNodes.includes(n.id));
      if (!intv) return n;
      const order = ['red', 'orange', 'yellow', 'green'];
      const idx = order.indexOf(n.status);
      const newStatus = idx > 0 ? order[idx - 1] : n.status;
      return { ...n, status: newStatus, utilization: Math.max(0, n.utilization - 0.15) };
    });
    return {
      weather: data.weather,
      grid: {
        ...data.grid,
        nodes,
        cascadeRisk: Math.max(0.05, data.grid.cascadeRisk - 0.32),
        stability: Math.min(99, data.grid.stability + 18),
      },
    };
  }, [data, active]);
  return <BeforeAfter doNothing={doNothing} withAi={withAi} />;
}

// ─── Small widgets ─────────────────────────────────────────────────────────

function Metric({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  return (
    <div className="bg-black/30 border border-cyan-400/10 rounded-md p-2">
      <div className="flex items-center gap-1.5 text-[9px] tracking-[0.18em] font-display text-slate-400">
        <span className="text-cyan-300">{icon}</span>{label}
      </div>
      <div className={`font-mono text-base font-semibold mt-1 ${color}`}>{value}</div>
    </div>
  );
}

function Readout({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="flex items-center justify-between border-b border-cyan-400/10 pb-1.5">
      <span className="text-slate-400">{label}</span>
      <span className={`font-semibold ${color}`}>{value}</span>
    </div>
  );
}

function StressBars({ grid }: any) {
  const sorted = [...grid.nodes].sort((a, b) => b.utilization - a.utilization);
  const STATUS_COLORS: Record<string, string> = {
    green: '#10b981', yellow: '#facc15', orange: '#fb923c', red: '#ef4444',
  };
  return (
    <div className="space-y-1.5">
      {sorted.slice(0, 8).map((n: any) => (
        <div key={n.id} className="space-y-0.5">
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-slate-300 font-display tracking-wide">{n.name}</span>
            <span className="font-mono" style={{ color: STATUS_COLORS[n.status] }}>
              {(n.utilization * 100).toFixed(0)}%
            </span>
          </div>
          <div className="h-1.5 rounded bg-slate-800 overflow-hidden">
            <div
              className="h-full transition-all duration-700"
              style={{
                width: `${n.utilization * 100}%`,
                background: STATUS_COLORS[n.status],
                boxShadow: `0 0 8px ${STATUS_COLORS[n.status]}`,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function GenerationMix({ grid }: any) {
  const types = ['generator', 'solar', 'wind', 'battery'];
  const labels: Record<string, string> = { generator: 'GAS', solar: 'SOLAR', wind: 'WIND', battery: 'BATTERY' };
  const colors: Record<string, string> = { generator: '#3b82f6', solar: '#facc15', wind: '#22d3ee', battery: '#10b981' };
  const mix = types.map((t) => ({
    type: t,
    label: labels[t],
    color: colors[t],
    mw: grid.nodes.filter((n: any) => n.kind === t).reduce((s: number, n: any) => s + n.load, 0),
  }));
  const total = mix.reduce((s, m) => s + m.mw, 0) || 1;
  return (
    <div className="space-y-2">
      {mix.map((m) => (
        <div key={m.type}>
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-slate-400 font-display tracking-widest">{m.label}</span>
            <span className="font-mono text-cyan-200">{m.mw.toFixed(0)} MW · {((m.mw / total) * 100).toFixed(0)}%</span>
          </div>
          <div className="h-1.5 rounded bg-slate-800 overflow-hidden mt-0.5">
            <div className="h-full" style={{ width: `${(m.mw / total) * 100}%`, background: m.color, boxShadow: `0 0 8px ${m.color}` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function AIMeter({ confidence }: { confidence: number }) {
  return (
    <div className="flex items-center gap-2 px-2.5 py-1 rounded border border-cyan-400/20 bg-cyan-500/5">
      <Sparkles size={12} className="text-cyan-300" />
      <div>
        <div className="text-[9px] tracking-widest text-cyan-300/80 font-display">AGENT</div>
        <div className="text-[10px] font-mono text-cyan-100 leading-none">
          <NumberAnim value={confidence * 100} unit="%" /> <span className="text-cyan-300/70">conf</span>
        </div>
      </div>
    </div>
  );
}

function PanelToggle({ on, onClick, direction }: { on: boolean; onClick: () => void; direction: 'left' | 'right' }) {
  return (
    <button
      onClick={onClick}
      className="glass w-7 h-7 rounded-md flex items-center justify-center text-cyan-300 hover:bg-cyan-500/15 transition"
      aria-label={`Toggle ${direction} panel`}
    >
      {direction === 'left' ? (on ? <ChevronDown size={14} className="-rotate-90" /> : <ChevronUp size={14} className="rotate-90" />) : (on ? <ChevronDown size={14} className="rotate-90" /> : <ChevronUp size={14} className="-rotate-90" />)}
    </button>
  );
}