import { useEffect, useRef, useState } from 'react';
import { Pause, Play, RotateCcw, Zap } from 'lucide-react';
import type { PredictionPoint } from '../lib/types';
import { NumberAnim } from './NumberAnim';

interface Props {
  predictions: PredictionPoint[];
  scrubMin: number; // 0..60
  onScrub: (min: number) => void;
}

// Interactive prediction timeline. The user drags a handle to scrub through
// the next 60 minutes and the rest of the app reacts.

export function TimelineScrubber({ predictions, scrubMin, onScrub }: Props) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [playing, setPlaying] = useState(false);
  const playRef = useRef<number | null>(null);
  const [drag, setDrag] = useState(false);

  useEffect(() => {
    if (!playing) {
      if (playRef.current) cancelAnimationFrame(playRef.current);
      return;
    }
    let last = performance.now();
    const tick = (t: number) => {
      const dt = (t - last) / 1000;
      last = t;
      const next = scrubMin + dt * 4; // 4 minutes/sec
      if (next >= 60) {
        onScrub(60);
        setPlaying(false);
        return;
      }
      onScrub(next);
      playRef.current = requestAnimationFrame(tick);
    };
    playRef.current = requestAnimationFrame(tick);
    return () => {
      if (playRef.current) cancelAnimationFrame(playRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing, scrubMin === 60]);

  const onPointerDown = (e: React.PointerEvent) => {
    setDrag(true);
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    updateFromEvent(e);
  };
  const onPointerMove = (e: React.PointerEvent) => {
    if (!drag) return;
    updateFromEvent(e);
  };
  const onPointerUp = () => setDrag(false);

  const updateFromEvent = (e: React.PointerEvent) => {
    const el = trackRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    onScrub(Math.round(ratio * 60));
  };

  const active = predictions.length > 0 ? predictions.reduce((acc, p) => {
    if (p.offsetMin <= scrubMin) acc = p;
    return acc;
  }, predictions[0]) : { rainfall: 0, gridStress: 0, cascadeProbability: 0, demand: 0 };

  const dots = predictions.map((p) => ({ ...p, x: (p.offsetMin / 60) * 100 }));
  const hasPredictions = predictions.length > 0;

  return (
    <div className="space-y-3">
      {/* Control row */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setPlaying((p) => !p)}
          className="glass px-3 py-1.5 rounded-md flex items-center gap-2 hover:bg-cyan-500/10 transition text-cyan-200 text-xs font-display tracking-widest"
        >
          {playing ? <Pause size={14} /> : <Play size={14} />}
          {playing ? 'PAUSE' : 'PLAY'}
        </button>
        <button
          onClick={() => { onScrub(0); setPlaying(false); }}
          className="glass px-3 py-1.5 rounded-md flex items-center gap-2 hover:bg-cyan-500/10 transition text-cyan-200 text-xs font-display tracking-widest"
        >
          <RotateCcw size={14} /> RESET
        </button>
        <button
          onClick={() => onScrub(Math.min(60, scrubMin + 5))}
          className="glass px-3 py-1.5 rounded-md flex items-center gap-2 hover:bg-cyan-500/10 transition text-cyan-200 text-xs font-display tracking-widest"
        >
          <Zap size={14} /> +5 MIN
        </button>
        <div className="ml-auto text-[10px] font-display tracking-[0.22em] text-cyan-300/80">
          SCRUB · {scrubMin.toFixed(1)} MIN
        </div>
      </div>

      {/* Track */}
      <div
        ref={trackRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        className="relative h-16 select-none cursor-pointer"
        style={{ touchAction: 'none' }}
      >
        {/* bg line */}
        <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-[2px] bg-gradient-to-r from-cyan-400/30 via-blue-500/30 to-rose-500/40 rounded-full" />

        {/* filled */}
        <div
          className="absolute left-0 top-1/2 -translate-y-1/2 h-[2px] rounded-full bg-gradient-to-r from-cyan-300 to-rose-400"
          style={{ width: `${(scrubMin / 60) * 100}%`, boxShadow: '0 0 12px rgba(34,211,238,0.7)' }}
        />

        {/* dots */}
        {dots.map((d) => (
          <div
            key={d.label}
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 flex flex-col items-center"
            style={{ left: `${d.x}%` }}
          >
            <div
              className={`w-3 h-3 rounded-full border-2 ${
                d.offsetMin <= scrubMin ? 'bg-cyan-400 border-cyan-200' : 'bg-slate-700 border-slate-500'
              }`}
              style={{ boxShadow: d.offsetMin <= scrubMin ? '0 0 10px rgba(34,211,238,0.7)' : 'none' }}
            />
            <div className={`text-[9px] font-display tracking-widest mt-2 ${d.offsetMin <= scrubMin ? 'text-cyan-200' : 'text-slate-500'}`}>
              {d.label}
            </div>
          </div>
        ))}

        {/* Handle */}
        <div
          className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 pointer-events-none"
          style={{ left: `${(scrubMin / 60) * 100}%` }}
        >
          <div className="w-4 h-4 rounded-full bg-white shadow-[0_0_14px_rgba(34,211,238,0.9)] border-2 border-cyan-300" />
          <div className="absolute top-5 left-1/2 -translate-x-1/2 text-[10px] font-mono text-cyan-200 whitespace-nowrap">
            {scrubMin.toFixed(1)}m
          </div>
        </div>
      </div>

      {/* Live readout */}
      <div className="grid grid-cols-4 gap-2 text-center">
        <ReadoutCell label="RAINFALL" value={active.rainfall} unit="mm/hr" color="text-cyan-300" />
        <ReadoutCell label="GRID STRESS" value={active.gridStress * 100} unit="%" color="text-amber-300" />
        <ReadoutCell label="CASCADE P" value={active.cascadeProbability * 100} unit="%" color="text-rose-300" />
        <ReadoutCell label="DEMAND" value={active.demand} unit="MW" color="text-emerald-300" />
      </div>
    </div>
  );
}

function ReadoutCell({ label, value, unit, color }: { label: string; value: number; unit: string; color: string }) {
  return (
    <div className="bg-black/30 border border-cyan-400/10 rounded-md py-2">
      <div className="text-[9px] tracking-[0.18em] text-slate-400 font-display">{label}</div>
      <div className={`font-mono text-lg font-semibold ${color}`}>
        <NumberAnim value={value} decimals={0} />
        <span className="text-[9px] ml-1 opacity-70 font-display">{unit}</span>
      </div>
    </div>
  );
}