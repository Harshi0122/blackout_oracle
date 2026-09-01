import { useEffect, useRef, useState } from 'react';
import { Pause, Play, RotateCcw, Activity, AlertTriangle } from 'lucide-react';
import type { CascadeStep, GridData } from '../lib/types';
import { TOPOLOGY } from '../lib/mockBackend';

interface Props {
  grid: GridData;
  steps: CascadeStep[];
  className?: string;
}

// Cascade failure animation with play/pause/reset/simulate.
export function CascadeSim({ grid, steps, className }: Props) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 1000, h: 380 });
  const [playing, setPlaying] = useState(false);
  const [t, setT] = useState(0); // seconds since start of sim
  const [completed, setCompleted] = useState(false);
  const tRef = useRef(0);
  const lastRef = useRef(performance.now());
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    setSize({ w: r.width, h: r.height });
    const ro = new ResizeObserver(() => {
      const rr = el.getBoundingClientRect();
      setSize({ w: rr.width, h: rr.height });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (!playing) return;
    lastRef.current = performance.now();
    const tick = (now: number) => {
      const dt = (now - lastRef.current) / 1000;
      lastRef.current = now;
      tRef.current += dt;
      const maxT = steps[steps.length - 1]?.t ?? 18;
      if (tRef.current >= maxT) {
        tRef.current = maxT;
        setT(maxT);
        setPlaying(false);
        setCompleted(true);
        return;
      }
      setT(tRef.current);
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [playing, steps]);

  const reset = () => {
    setPlaying(false);
    tRef.current = 0;
    setT(0);
    setCompleted(false);
  };

  const PAD = 36;
  const mapX = (x: number) => PAD + x * (size.w - PAD * 2);
  const mapY = (y: number) => PAD + y * (size.h - PAD * 2);

  // Identify which step is currently "firing"
  const activeStepIdx = steps.findIndex((s, i) => {
    const next = steps[i + 1];
    return t >= s.t && (!next || t < next.t);
  });

  const STATUS_COLORS: Record<string, string> = {
    green: '#10b981', yellow: '#facc15', orange: '#fb923c', red: '#ef4444',
  };

  // Build a sequential chain for visualization
  const trail = steps.map((s) => s.nodeId);
  const trailNodes = trail.map((id) => grid.nodes.find((n) => n.id === id)!).filter(Boolean);

  return (
    <div className={`relative overflow-hidden rounded-lg ${className ?? ''}`}>
      {/* Cinematic background */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#050b1a] via-[#0a1428] to-[#02030a]" />
      <div className="absolute inset-0 bg-grid-dense opacity-30" />

      {/* Controls */}
      <div className="relative flex items-center gap-2 px-4 pt-3">
        <button
          onClick={() => setPlaying((p) => !p)}
          disabled={completed}
          className="glass px-3 py-1.5 rounded-md flex items-center gap-2 hover:bg-cyan-500/10 transition text-cyan-200 text-xs font-display tracking-widest disabled:opacity-40"
        >
          {playing ? <Pause size={14} /> : <Play size={14} />}
          {playing ? 'PAUSE' : completed ? 'COMPLETE' : 'PLAY'}
        </button>
        <button
          onClick={reset}
          className="glass px-3 py-1.5 rounded-md flex items-center gap-2 hover:bg-cyan-500/10 transition text-cyan-200 text-xs font-display tracking-widest"
        >
          <RotateCcw size={14} /> RESET
        </button>
        <button
          onClick={() => { reset(); setPlaying(true); }}
          className="glass px-3 py-1.5 rounded-md flex items-center gap-2 bg-rose-500/10 hover:bg-rose-500/20 transition text-rose-200 text-xs font-display tracking-widest border-rose-400/30"
        >
          <AlertTriangle size={14} /> SIMULATE
        </button>
        <div className="ml-auto flex items-center gap-2 text-[10px] font-display tracking-[0.22em] text-cyan-300/80">
          <Activity size={12} className="text-rose-400 live-dot" />
          T+ {t.toFixed(1)}s
        </div>
      </div>

      {/* Canvas */}
      <div ref={wrapRef} className="relative w-full h-[380px] mt-2">
        <svg viewBox={`0 0 ${size.w} ${size.h}`} width="100%" height="100%">
          <defs>
            <filter id="cs-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="4" />
              <feMerge>
                <feMergeNode />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <linearGradient id="surge" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="rgba(251,146,60,0)" />
              <stop offset="50%" stopColor="rgba(251,146,60,1)" />
              <stop offset="100%" stopColor="rgba(239,68,68,1)" />
            </linearGradient>
          </defs>

          {/* Trail edges */}
          {trailNodes.slice(0, -1).map((n, i) => {
            const m = trailNodes[i + 1];
            const step = steps[i];
            const lit = t >= step.t;
            const x1 = mapX(n.x), y1 = mapY(n.y);
            const x2 = mapX(m.x), y2 = mapY(m.y);
            return (
              <g key={i}>
                <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="rgba(56,189,248,0.12)" strokeWidth={6} />
                {lit && (
                  <line
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke="url(#surge)"
                    strokeWidth={5}
                    strokeLinecap="round"
                    filter="url(#cs-glow)"
                  />
                )}
                {/* surge particle */}
                {lit && (
                  <circle r={5} fill="#fda4af" filter="url(#cs-glow)">
                    <animate attributeName="cx" from={x1} to={x2} dur="1.4s" repeatCount="indefinite" begin={`${i * 0.3}s`} />
                    <animate attributeName="cy" from={y1} to={y2} dur="1.4s" repeatCount="indefinite" begin={`${i * 0.3}s`} />
                  </circle>
                )}
              </g>
            );
          })}

          {/* Trail nodes */}
          {trailNodes.map((n, i) => {
            const step = steps[i];
            const active = t >= step.t;
            const cx = mapX(n.x), cy = mapY(n.y);
            const c = STATUS_COLORS[step.status];
            return (
              <g key={n.id}>
                {active && (
                  <circle cx={cx} cy={cy} r={28} fill="none" stroke={c} strokeOpacity="0.6">
                    <animate attributeName="r" from="14" to="44" dur="1.6s" repeatCount="indefinite" />
                    <animate attributeName="stroke-opacity" from="0.7" to="0" dur="1.6s" repeatCount="indefinite" />
                  </circle>
                )}
                <circle cx={cx} cy={cy} r={18} fill={c} fillOpacity={active ? 0.3 : 0.15} stroke={c} strokeWidth={2} filter={active ? 'url(#cs-glow)' : ''} />
                <text x={cx} y={cy + 4} textAnchor="middle" fill="#fff" fontSize={14} fontFamily="system-ui" fontWeight="700">
                  {i + 1}
                </text>
                <text x={cx} y={cy + 38} textAnchor="middle" fill="#e2e8f0" fontSize={10} fontFamily="var(--font-display), sans-serif" letterSpacing="1">
                  {n.name}
                </text>
              </g>
            );
          })}

          {/* Top label */}
          <g>
            <rect x={size.w / 2 - 120} y={8} width={240} height={26} rx="4" fill="rgba(244,63,94,0.12)" stroke="rgba(244,63,94,0.5)" />
            <text x={size.w / 2} y={25} textAnchor="middle" fill="#fda4af" fontSize={11} fontFamily="var(--font-display), sans-serif" letterSpacing="3">
              CASCADE PROPAGATION
            </text>
          </g>
        </svg>
      </div>

      {/* Timeline strip */}
      <div className="relative px-4 pb-3">
        <div className="relative h-2 bg-slate-800/60 rounded-full overflow-hidden">
          <div
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-amber-400 via-orange-500 to-rose-500"
            style={{
              width: `${(t / (steps[steps.length - 1]?.t ?? 18)) * 100}%`,
              boxShadow: '0 0 12px rgba(244,63,94,0.6)',
            }}
          />
        </div>
        <div className="flex justify-between mt-2 text-[9px] font-display tracking-widest text-slate-400">
          {steps.map((s, i) => (
            <span key={i} style={{ color: t >= s.t ? '#fda4af' : undefined }}>
              {s.t.toFixed(0)}s
            </span>
          ))}
        </div>
      </div>

      {/* Active step description */}
      <div className="relative px-4 pb-4">
        <div className="glass-soft rounded-md p-3 flex items-start gap-3">
          <div className={`w-1 self-stretch rounded-full ${
            activeStepIdx === -1 ? 'bg-cyan-400' : 'bg-rose-400'
          }`} />
          <div>
            <div className="text-[10px] tracking-[0.22em] font-display text-cyan-300/80">
              {activeStepIdx === -1 ? 'STATUS' : `STEP ${activeStepIdx + 1}`}
            </div>
            <div className="text-sm text-white font-display mt-0.5">
              {activeStepIdx === -1 ? 'Awaiting simulation start' : steps[activeStepIdx]?.message}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}