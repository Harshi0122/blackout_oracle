import { useEffect, useMemo, useRef, useState } from 'react';
import type { GridData, GridNode } from '../lib/types';
import { TOPOLOGY } from '../lib/mockBackend';
import { Tooltip } from './Tooltip';
import { NumberAnim } from './NumberAnim';

interface Props {
  data: GridData;
  onFocusNode?: (id: string | null) => void;
  focusedNodeId?: string | null;
  showFlow?: boolean;
  compact?: boolean;
}

const STATUS_COLORS: Record<string, { fill: string; stroke: string; glow: string }> = {
  green:  { fill: '#10b981', stroke: '#34d399', glow: 'rgba(16,185,129,0.5)' },
  yellow: { fill: '#facc15', stroke: '#fde047', glow: 'rgba(250,204,21,0.5)' },
  orange: { fill: '#fb923c', stroke: '#fdba74', glow: 'rgba(251,146,60,0.55)' },
  red:    { fill: '#ef4444', stroke: '#fda4af', glow: 'rgba(239,68,68,0.65)' },
};

const KIND_GLYPH: Record<string, string> = {
  generator: '⚙',
  solar: '☀',
  wind: '✸',
  battery: '▮',
  substation: '◈',
  industrial: '◧',
  residential: '◉',
  hospital: '✚',
  critical: '⚐',
};

const KIND_LABEL: Record<string, string> = {
  generator: 'GENERATOR',
  solar: 'SOLAR FARM',
  wind: 'WIND FARM',
  battery: 'BATTERY',
  substation: 'SUBSTATION',
  industrial: 'INDUSTRIAL',
  residential: 'RESIDENTIAL',
  hospital: 'HOSPITAL',
  critical: 'CRITICAL INFRA',
};

// ─── SmartGrid: SVG-based digital twin with interactive nodes and
// animated electricity particles traveling along transmission lines.
export function SmartGrid({ data, onFocusNode, focusedNodeId, showFlow = true, compact }: Props) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 1000, h: 600 });
  const [hover, setHover] = useState<{ id: string; x: number; y: number } | null>(null);

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

  // Map normalized positions to viewbox.
  const PAD = 36;
  const mapX = (x: number) => PAD + x * (size.w - PAD * 2);
  const mapY = (y: number) => PAD + y * (size.h - PAD * 2);

  const nodesById = useMemo(() => {
    const m = new Map<string, GridNode>();
    data.nodes.forEach((n) => m.set(n.id, n));
    return m;
  }, [data]);

  const focused = focusedNodeId ? nodesById.get(focusedNodeId) : null;
  const connectedToFocused = useMemo(() => {
    if (!focused) return new Set<string>();
    const s = new Set<string>();
    data.edges.forEach((e) => {
      if (e.from === focused.id) s.add(e.to);
      if (e.to === focused.id) s.add(e.from);
    });
    return s;
  }, [focused, data.edges]);

  return (
    <div ref={wrapRef} className="absolute inset-0">
      <svg
        viewBox={`0 0 ${size.w} ${size.h}`}
        width="100%"
        height="100%"
        preserveAspectRatio="none"
        className="absolute inset-0"
      >
        <defs>
          {/* Filters */}
          <filter id="glow-strong" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3.5" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="glow-soft" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="1.6" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          {/* Radial backgrounds for substation hubs */}
          <radialGradient id="hub-bg" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(56,189,248,0.18)" />
            <stop offset="100%" stopColor="rgba(56,189,248,0)" />
          </radialGradient>

          {/* Edge gradient that runs along the path */}
          <linearGradient id="edge-flow" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="rgba(34,211,238,0.0)" />
            <stop offset="50%" stopColor="rgba(34,211,238,1)" />
            <stop offset="100%" stopColor="rgba(34,211,238,0.0)" />
          </linearGradient>
          <linearGradient id="edge-flow-warm" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="rgba(251,146,60,0.0)" />
            <stop offset="50%" stopColor="rgba(251,146,60,1)" />
            <stop offset="100%" stopColor="rgba(251,146,60,0.0)" />
          </linearGradient>
          <linearGradient id="edge-flow-red" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="rgba(239,68,68,0.0)" />
            <stop offset="50%" stopColor="rgba(239,68,68,1)" />
            <stop offset="100%" stopColor="rgba(239,68,68,0.0)" />
          </linearGradient>

          {/* Pattern: subtle topo grid */}
          <pattern id="topo-grid" width="60" height="60" patternUnits="userSpaceOnUse">
            <path d="M60 0 L0 0 0 60" fill="none" stroke="rgba(56,189,248,0.06)" strokeWidth="1" />
          </pattern>
        </defs>

        {/* Topology background */}
        <rect width={size.w} height={size.h} fill="url(#topo-grid)" />

        {/* Halo behind the central area */}
        <ellipse cx={size.w * 0.5} cy={size.h * 0.5} rx={size.w * 0.46} ry={size.h * 0.42} fill="url(#hub-bg)" />

        {/* ─── EDGES ─── */}
        <g>
          {data.edges.map((e) => {
            const from = nodesById.get(e.from)!;
            const to = nodesById.get(e.to)!;
            const x1 = mapX(from.x);
            const y1 = mapY(from.y);
            const x2 = mapX(to.x);
            const y2 = mapY(to.y);
            // Curved path
            const mx = (x1 + x2) / 2;
            const my = (y1 + y2) / 2 - 16;
            const path = `M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`;
            const isConnFocused = focused && (e.from === focused.id || e.to === focused.id);
            const colorByStress =
              to.status === 'red' || from.status === 'red'
                ? 'edge-flow-red'
                : to.status === 'orange' || from.status === 'orange'
                ? 'edge-flow-warm'
                : 'edge-flow';
            const opacityBase = focused ? (isConnFocused ? 1 : 0.18) : 0.85;
            const strokeW = 1.2 + e.load * 2.2 + (isConnFocused ? 1.4 : 0);
            return (
              <g key={e.id}>
                <path d={path} stroke="rgba(56,189,248,0.12)" strokeWidth={strokeW + 2} fill="none" />
                {showFlow && (
                  <path
                    d={path}
                    stroke={`url(#${colorByStress})`}
                    strokeWidth={strokeW}
                    fill="none"
                    opacity={opacityBase}
                    className={e.load > 0.65 ? 'flow-dash' : 'flow-dash-slow'}
                    style={{ animationDuration: `${0.6 + (1 - e.load) * 1.4}s` }}
                    filter="url(#glow-soft)"
                  />
                )}
              </g>
            );
          })}
        </g>

        {/* ─── PARTICLES along active edges ─── */}
        {showFlow && (
          <g>
            {data.edges.map((e) => {
              const from = nodesById.get(e.from)!;
              const to = nodesById.get(e.to)!;
              const x1 = mapX(from.x);
              const y1 = mapY(from.y);
              const x2 = mapX(to.x);
              const y2 = mapY(to.y);
              const mx = (x1 + x2) / 2;
              const my = (y1 + y2) / 2 - 16;
              const path = `M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`;
              const isConnFocused = focused && (e.from === focused.id || e.to === focused.id);
              const opacity = focused ? (isConnFocused ? 1 : 0.2) : 0.95;
              // emit N particles per edge proportional to load
              const count = Math.max(1, Math.round(e.load * 4));
              return Array.from({ length: count }).map((_, i) => (
                <circle key={`${e.id}-${i}`} r={1.6 + e.load * 1.6} fill={to.status === 'red' ? '#fda4af' : to.status === 'orange' ? '#fdba74' : '#67e8f9'} opacity={opacity} filter="url(#glow-strong)">
                  <animateMotion
                    dur={`${1.6 + (1 - e.load) * 2.4}s`}
                    repeatCount="indefinite"
                    path={path}
                    begin={`${(i / count) * 1.6}s`}
                  />
                </circle>
              ));
            })}
          </g>
        )}

        {/* ─── NODES ─── */}
        <g>
          {data.nodes.map((n) => {
            const cx = mapX(n.x);
            const cy = mapY(n.y);
            const c = STATUS_COLORS[n.status];
            const isFocused = focused?.id === n.id;
            const isConn = connectedToFocused.has(n.id);
            const dim = focused && !isFocused && !isConn ? 0.35 : 1;
            const r = n.kind === 'substation' ? 18 : n.kind === 'critical' || n.kind === 'hospital' ? 15 : 12;
            return (
              <g
                key={n.id}
                opacity={dim}
                style={{ cursor: 'pointer', transition: 'opacity 0.25s' }}
                onMouseEnter={(ev) => {
                  const rect = (ev.currentTarget.ownerSVGElement?.getBoundingClientRect() ?? { left: 0, top: 0 }) as DOMRect;
                  setHover({ id: n.id, x: rect.left + cx, y: rect.top + cy });
                }}
                onMouseLeave={() => setHover(null)}
                onClick={() => onFocusNode?.(isFocused ? null : n.id)}
              >
                {/* Pulse rings for hubs */}
                {(n.kind === 'substation' || n.kind === 'critical') && (
                  <>
                    <circle cx={cx} cy={cy} r={r + 4} fill="none" stroke={c.stroke} strokeOpacity="0.5">
                      <animate attributeName="r" from={r + 4} to={r + 24} dur="2.2s" repeatCount="indefinite" />
                      <animate attributeName="stroke-opacity" from="0.6" to="0" dur="2.2s" repeatCount="indefinite" />
                    </circle>
                    <circle cx={cx} cy={cy} r={r + 4} fill="none" stroke={c.stroke} strokeOpacity="0.4">
                      <animate attributeName="r" from={r + 4} to={r + 30} dur="2.2s" begin="1.1s" repeatCount="indefinite" />
                      <animate attributeName="stroke-opacity" from="0.5" to="0" dur="2.2s" begin="1.1s" repeatCount="indefinite" />
                    </circle>
                  </>
                )}

                {/* Energy halo glow for status */}
                <circle cx={cx} cy={cy} r={r + 18} fill={c.fill} fillOpacity={n.status === 'red' ? 0.18 : 0.08}>
                  <animate attributeName="fill-opacity" values={`${n.status === 'red' ? 0.18 : 0.06};${n.status === 'red' ? 0.28 : 0.12};${n.status === 'red' ? 0.18 : 0.06}`} dur="2.4s" repeatCount="indefinite" />
                </circle>

                {/* Outer ring */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={r + 3}
                  fill="rgba(15,28,56,0.6)"
                  stroke={c.stroke}
                  strokeWidth={isFocused ? 2.5 : 1.2}
                  strokeOpacity={isFocused ? 1 : 0.7}
                />

                {/* Inner fill */}
                <circle cx={cx} cy={cy} r={r} fill={c.fill} fillOpacity={0.18} stroke={c.fill} strokeWidth={1.6} filter={isFocused ? 'url(#glow-strong)' : 'url(#glow-soft)'} />

                {/* Glyph */}
                <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle" fill="#e2e8f0" fontSize={r * 0.95} fontFamily="system-ui" style={{ pointerEvents: 'none' }}>
                  {KIND_GLYPH[n.kind]}
                </text>

                {/* Capacity arc */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={r + 6}
                  fill="none"
                  stroke="rgba(255,255,255,0.06)"
                  strokeWidth={3}
                />
                <circle
                  cx={cx}
                  cy={cy}
                  r={r + 6}
                  fill="none"
                  stroke={c.fill}
                  strokeWidth={3}
                  strokeLinecap="round"
                  strokeDasharray={`${n.utilization * 2 * Math.PI * (r + 6)} ${2 * Math.PI * (r + 6)}`}
                  transform={`rotate(-90 ${cx} ${cy})`}
                  style={{ transition: 'stroke-dasharray 0.6s ease' }}
                />

                {/* Label */}
                {!compact && (
                  <g transform={`translate(${cx}, ${cy + r + 16})`}>
                    <rect x={-44} y={-8} width={88} height={16} rx={4} fill="rgba(2,6,23,0.7)" stroke="rgba(56,189,248,0.18)" />
                    <text textAnchor="middle" y={3} fill="#e2e8f0" fontSize={9} fontFamily="var(--font-display), sans-serif" letterSpacing="1">
                      {n.name}
                    </text>
                  </g>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      {/* Hover tooltip */}
      <Tooltip visible={!!hover && !!nodesById.get(hover!.id)} x={hover?.x ?? 0} y={hover?.y ?? 0}>
        {hover && (() => {
          const n = nodesById.get(hover.id)!;
          const c = STATUS_COLORS[n.status];
          return (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between gap-3">
                <div className="text-[10px] tracking-[0.18em] text-cyan-200">{KIND_LABEL[n.kind]}</div>
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: c.fill, boxShadow: `0 0 8px ${c.fill}` }} />
              </div>
              <div className="text-sm font-display text-white">{n.name}</div>
              <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] mt-1">
                <span className="text-slate-400">UTILIZATION</span>
                <span className="text-right" style={{ color: c.fill }}>
                  <NumberAnim value={n.utilization * 100} decimals={0} unit="%" />
                </span>
                <span className="text-slate-400">STATUS</span>
                <span className="text-right" style={{ color: c.fill }}>{n.status.toUpperCase()}</span>
                <span className="text-slate-400">LOAD</span>
                <span className="text-right text-cyan-100">
                  <NumberAnim value={n.load} decimals={1} unit="MW" />
                </span>
                <span className="text-slate-400">CAPACITY</span>
                <span className="text-right text-cyan-100">{n.capacity} MW</span>
                <span className="text-slate-400">CASCADE</span>
                <span className="text-right" style={{ color: n.cascadeContribution > 0.6 ? c.fill : '#67e8f9' }}>
                  {n.cascadeContribution > 0.66 ? 'HIGH' : n.cascadeContribution > 0.33 ? 'MODERATE' : 'LOW'}
                </span>
              </div>
              <div className="text-[10px] text-cyan-300/70 pt-1 border-t border-cyan-400/10">CLICK TO TRACE FLOW</div>
            </div>
          );
        })()}
      </Tooltip>
    </div>
  );
}