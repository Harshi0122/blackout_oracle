import { useEffect, useRef, useState } from 'react';
import type { GridData, WeatherData } from '../lib/types';

interface Props {
  doNothing: { weather: WeatherData; grid: GridData };
  withAi: { weather: WeatherData; grid: GridData };
  className?: string;
}

// Before/after comparison slider — left half shows do-nothing scenario
// (rising cascade risk, more red nodes), right shows AI intervention.

export function BeforeAfter({ doNothing, withAi, className }: Props) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 1000, h: 420 });
  const [pos, setPos] = useState(50);
  const drag = useRef(false);

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

  const onPointerMove = (e: PointerEvent) => {
    if (!drag.current) return;
    const el = wrapRef.current!;
    const r = el.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width) * 100;
    setPos(Math.max(2, Math.min(98, x)));
  };
  useEffect(() => {
    const up = () => (drag.current = false);
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', up);
    return () => {
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', up);
    };
  }, []);

  const PAD = 40;
  const mapX = (x: number) => PAD + x * (size.w - PAD * 2);
  const mapY = (y: number) => PAD + y * (size.h - PAD * 2);

  const STATUS_COLORS: Record<string, string> = {
    green: '#10b981', yellow: '#facc15', orange: '#fb923c', red: '#ef4444',
  };

  const renderSide = (grid: GridData, _weather: WeatherData, risk: number) => {
    return grid.nodes.map((n) => {
      const cx = mapX(n.x), cy = mapY(n.y);
      const c = STATUS_COLORS[n.status];
      const r = n.kind === 'substation' ? 16 : n.kind === 'critical' || n.kind === 'hospital' ? 13 : 10;
      return (
        <g key={n.id}>
          {n.status === 'red' && (
            <circle cx={cx} cy={cy} r={r + 6} fill="none" stroke={c} strokeOpacity="0.7">
              <animate attributeName="r" from={r + 4} to={r + 22} dur="1.8s" repeatCount="indefinite" />
              <animate attributeName="stroke-opacity" from="0.7" to="0" dur="1.8s" repeatCount="indefinite" />
            </circle>
          )}
          <circle cx={cx} cy={cy} r={r} fill={c} fillOpacity={0.28} stroke={c} strokeWidth={2} />
        </g>
      );
    });
  };

  const renderEdges = (grid: GridData) =>
    grid.edges.map((e) => {
      const from = grid.nodes.find((n) => n.id === e.from)!;
      const to = grid.nodes.find((n) => n.id === e.to)!;
      const x1 = mapX(from.x), y1 = mapY(from.y);
      const x2 = mapX(to.x), y2 = mapY(to.y);
      const mx = (x1 + x2) / 2;
      const my = (y1 + y2) / 2 - 12;
      const path = `M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`;
      const stress = to.status === 'red' || from.status === 'red';
      return (
        <path
          key={e.id}
          d={path}
          stroke={stress ? 'rgba(239,68,68,0.4)' : 'rgba(56,189,248,0.18)'}
          strokeWidth={1 + e.load * 1.6}
          fill="none"
        />
      );
    });

  return (
    <div className={`space-y-2 ${className ?? ''}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 rounded bg-rose-500/15 border border-rose-400/30 text-[10px] tracking-[0.22em] font-display text-rose-300">DO NOTHING</span>
          <span className="text-[10px] tracking-[0.22em] font-display text-slate-500">—</span>
          <span className="px-2 py-0.5 rounded bg-emerald-500/15 border border-emerald-400/30 text-[10px] tracking-[0.22em] font-display text-emerald-300">AI INTERVENTION</span>
        </div>
        <div className="flex items-center gap-3 text-[10px] font-mono text-slate-400">
          <span>CASCADE <span className="text-rose-300">{Math.round(doNothing.grid.cascadeRisk * 100)}%</span></span>
          <span>→</span>
          <span><span className="text-emerald-300">{Math.round(withAi.grid.cascadeRisk * 100)}%</span></span>
          <span>·</span>
          <span>STABILITY <span className="text-rose-300">{Math.round(doNothing.grid.stability)}%</span> → <span className="text-emerald-300">{Math.round(withAi.grid.stability)}%</span></span>
        </div>
      </div>

      <div ref={wrapRef} className="relative w-full overflow-hidden rounded-lg select-none" style={{ height: 420 }}>
        {/* BEFORE (full bg) */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#1c0a14] to-[#02030a]">
          <div className="absolute inset-0 bg-grid-dense opacity-20" style={{ filter: 'hue-rotate(330deg)' }} />
          <svg viewBox={`0 0 ${size.w} ${size.h}`} width="100%" height="100%" preserveAspectRatio="none">
            {renderEdges(doNothing.grid)}
            {renderSide(doNothing.grid, doNothing.weather, doNothing.grid.cascadeRisk)}
          </svg>
          <div className="absolute bottom-3 left-3 text-[10px] font-display tracking-[0.22em] text-rose-300/80">
            RAIN · {doNothing.weather.rainfall.toFixed(0)} mm/hr · WIND · {doNothing.weather.windSpeed.toFixed(0)} km/h
          </div>
        </div>

        {/* AFTER overlay (clipped) */}
        <div
          className="absolute inset-0 bg-gradient-to-b from-[#06121e] to-[#02030a]"
          style={{ clipPath: `inset(0 0 0 ${pos}%)` }}
        >
          <div className="absolute inset-0 bg-grid-dense opacity-30" />
          <svg viewBox={`0 0 ${size.w} ${size.h}`} width="100%" height="100%" preserveAspectRatio="none">
            {renderEdges(withAi.grid)}
            {renderSide(withAi.grid, withAi.weather, withAi.grid.cascadeRisk)}
          </svg>
          <div className="absolute bottom-3 right-3 text-[10px] font-display tracking-[0.22em] text-emerald-300/80">
            RAIN · {withAi.weather.rainfall.toFixed(0)} mm/hr · BATTERY · 48 MW INJECTED
          </div>
        </div>

        {/* Slider handle */}
        <div
          className="absolute top-0 bottom-0 w-[2px] bg-cyan-300"
          style={{ left: `${pos}%`, boxShadow: '0 0 14px rgba(34,211,238,0.8)' }}
        >
          <button
            onPointerDown={() => (drag.current = true)}
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-cyan-300 text-slate-900 flex items-center justify-center font-bold text-lg shadow-[0_0_20px_rgba(34,211,238,0.9)] cursor-grab"
            aria-label="Drag to compare"
          >
            ⇆
          </button>
        </div>

        {/* Side labels */}
        <div className="absolute top-3 left-3 px-2 py-1 rounded bg-black/50 backdrop-blur-sm border border-rose-400/30 text-rose-200 text-[10px] tracking-[0.22em] font-display">
          BEFORE
        </div>
        <div className="absolute top-3 right-3 px-2 py-1 rounded bg-black/50 backdrop-blur-sm border border-emerald-400/30 text-emerald-200 text-[10px] tracking-[0.22em] font-display">
          AFTER
        </div>
      </div>
    </div>
  );
}