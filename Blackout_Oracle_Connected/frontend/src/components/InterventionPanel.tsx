import { useEffect, useRef, useState } from 'react';
import type { GridData, Intervention, NodeStatus } from '../lib/types';
import { Battery, Car, Shuffle, ZapOff, Check, ArrowRight } from 'lucide-react';
import { store } from '../lib/store';
import { approveRecommendation, rejectRecommendation, markRecommendationExecuted } from '../api/recommendations';

interface Props {
  interventions: Intervention[];
  baseGrid: GridData;
  className?: string;
  operatorId?: string;
  onMutated?: () => void;
}

// AI intervention visualization: shows the interventions proposed by the
// agentic backend, and animates the BEFORE vs AFTER state of the grid.

const TYPE_ICONS = {
  battery: Battery,
  ev_demand: Car,
  reroute: Shuffle,
  loadshed: ZapOff,
};

export function InterventionPanel({ interventions, baseGrid, className, operatorId = '', onMutated }: Props) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 1000, h: 380 });
  const [applied, setApplied] = useState<Record<string, boolean>>({});
  const active = store.get().activeInterventions;
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

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

  const toggle = (type: Intervention['type']) => {
    store.toggleIntervention(type);
  };


  const review = async (intv: Intervention, action: 'approve' | 'reject' | 'executed') => {
    if (!intv.recommendationId) return;
    if (!operatorId.trim()) {
      setActionError('Enter a development operator identity before recommendation actions.');
      return;
    }
    setActionError(null);
    setBusyId(`${intv.recommendationId}:${action}`);
    try {
      const payload = { reviewer_id: operatorId.trim() };
      if (action === 'approve') await approveRecommendation(intv.recommendationId, payload);
      else if (action === 'reject') await rejectRecommendation(intv.recommendationId, payload);
      else await markRecommendationExecuted(intv.recommendationId, payload);
      onMutated?.();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Recommendation action failed.');
    } finally {
      setBusyId(null);
    }
  };

  const PAD = 40;
  const mapX = (x: number) => PAD + x * (size.w - PAD * 2);
  const mapY = (y: number) => PAD + y * (size.h - PAD * 2);

  // Simulate AFTER: lower utilization + improved status on affected nodes.
  const afterNodes = baseGrid.nodes.map((n) => {
    const intv = interventions.find((i) => active.has(i.type) && i.affectedNodes.includes(n.id));
    if (!intv) return n;
    const order: NodeStatus[] = ['red', 'orange', 'yellow', 'green'];
    const idx = order.indexOf(n.status);
    const newStatus = idx > 0 ? order[idx - 1] : n.status;
    return { ...n, status: newStatus, utilization: Math.max(0, n.utilization - 0.15), cascadeContribution: Math.max(0, n.cascadeContribution - 0.2) };
  });
  const afterNodeMap = new Map(afterNodes.map((n) => [n.id, n]));

  const STATUS_COLORS: Record<string, string> = {
    green: '#10b981', yellow: '#facc15', orange: '#fb923c', red: '#ef4444',
  };

  return (
    <div className={`space-y-3 ${className ?? ''}`}>
      <div ref={wrapRef} className="relative w-full h-[380px] overflow-hidden rounded-lg">
        <div className="absolute inset-0 bg-gradient-to-b from-[#050b1a] to-[#02030a]" />
        <div className="absolute inset-0 bg-grid opacity-30" />

        <svg viewBox={`0 0 ${size.w} ${size.h}`} width="100%" height="100%">
          <defs>
            <filter id="ip-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="4" />
              <feMerge>
                <feMergeNode />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <linearGradient id="ip-flow" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="rgba(34,211,238,0)" />
              <stop offset="50%" stopColor="rgba(34,211,238,1)" />
              <stop offset="100%" stopColor="rgba(34,211,238,0)" />
            </linearGradient>
          </defs>

          {/* Edges base */}
          {baseGrid.edges.map((e) => {
            const from = baseGrid.nodes.find((n) => n.id === e.from)!;
            const to = baseGrid.nodes.find((n) => n.id === e.to)!;
            const x1 = mapX(from.x), y1 = mapY(from.y);
            const x2 = mapX(to.x), y2 = mapY(to.y);
            const mx = (x1 + x2) / 2;
            const my = (y1 + y2) / 2 - 14;
            const path = `M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`;
            return (
              <path
                key={e.id}
                d={path}
                stroke="rgba(56,189,248,0.18)"
                strokeWidth={1.4 + e.load * 1.4}
                fill="none"
              />
            );
          })}

          {/* Intervention flow overlays */}
          {interventions.map((intv) => {
            if (!active.has(intv.type)) return null;
            return intv.flows.map((f, i) => {
              const from = baseGrid.nodes.find((n) => n.id === f.from);
              const to = baseGrid.nodes.find((n) => n.id === f.to);
              if (!from || !to) return null;
              const x1 = mapX(from.x), y1 = mapY(from.y);
              const x2 = mapX(to.x), y2 = mapY(to.y);
              return (
                <g key={`${intv.id}-${i}`}>
                  <line
                    x1={x1} y1={y1} x2={x2} y2={y2}
                    stroke="#10b981"
                    strokeWidth={5}
                    strokeLinecap="round"
                    strokeOpacity={0.7}
                    filter="url(#ip-glow)"
                  >
                    <animate attributeName="stroke-opacity" values="0.3;0.9;0.3" dur="1.6s" repeatCount="indefinite" />
                  </line>
                  {Array.from({ length: 4 }).map((_, j) => (
                    <circle r={3.5} fill="#6ee7b7" filter="url(#ip-glow)">
                      <animateMotion
                        path={`M ${x1} ${y1} L ${x2} ${y2}`}
                        dur="1.2s"
                        repeatCount="indefinite"
                        begin={`${j * 0.3}s`}
                      />
                    </circle>
                  ))}
                </g>
              );
            });
          })}

          {/* Nodes (after state) */}
          {afterNodes.map((n) => {
            const cx = mapX(n.x), cy = mapY(n.y);
            const c = STATUS_COLORS[n.status];
            const base = baseGrid.nodes.find((x) => x.id === n.id)!;
            const improved = base.status !== n.status;
            const r = n.kind === 'substation' ? 16 : n.kind === 'critical' || n.kind === 'hospital' ? 13 : 10;
            return (
              <g key={n.id}>
                {improved && (
                  <circle cx={cx} cy={cy} r={r + 8} fill="none" stroke="#10b981" strokeOpacity="0.7">
                    <animate attributeName="r" from={r + 4} to={r + 18} dur="1.6s" repeatCount="indefinite" />
                    <animate attributeName="stroke-opacity" from="0.7" to="0" dur="1.6s" repeatCount="indefinite" />
                  </circle>
                )}
                <circle cx={cx} cy={cy} r={r} fill={c} fillOpacity={0.25} stroke={c} strokeWidth={2} />
                <text x={cx} y={cy - r - 6} textAnchor="middle" fill="#e2e8f0" fontSize={9} fontFamily="var(--font-display), sans-serif" letterSpacing="1">
                  {n.name}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Caption */}
        <div className="absolute top-3 left-3 flex items-center gap-2">
          <div className="px-2 py-0.5 rounded bg-emerald-500/15 border border-emerald-400/30 text-[10px] tracking-[0.22em] font-display text-emerald-300">
            AFTER AI INTERVENTION
          </div>
          {active.size > 0 && (
            <div className="text-[10px] font-mono text-emerald-300/80">
              {active.size} INTERVENTION{active.size !== 1 ? 'S' : ''} ACTIVE
            </div>
          )}
        </div>
      </div>

      {/* Intervention cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
        {interventions.map((intv) => {
          const Icon = TYPE_ICONS[intv.type];
          const isOn = active.has(intv.type);
          return (
            <div
              key={intv.id}
              className={`glass-soft rounded-md p-3 transition-all ${
                isOn ? 'border-emerald-400/40 bg-emerald-500/5' : ''
              }`}
            >
              <div className="flex items-start gap-3">
                <div className={`w-9 h-9 rounded-md flex items-center justify-center shrink-0 ${
                  isOn ? 'bg-emerald-500/20 text-emerald-300' : 'bg-cyan-500/10 text-cyan-300'
                }`}>
                  <Icon size={18} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <div className="text-sm font-display text-white">{intv.title}</div>
                    {intv.recommended && (
                      <span className="text-[9px] tracking-widest px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-400/30">
                        RECOMMENDED
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-slate-300/80 mt-1 leading-snug">{intv.description}</div>
                  <div className="mt-2 flex items-center gap-3 text-[10px] font-mono text-slate-400">
                    <span>EFFECT <span className="text-emerald-300">{Math.round(intv.effectiveness * 100)}%</span></span>
                    <span>COST <span className="text-amber-300">{Math.round(intv.cost * 100)}%</span></span>
                    <span className="ml-auto text-[9px] tracking-widest text-slate-500 font-display">{intv.reasonCode}</span>
                  </div>
                </div>
                <button
                  onClick={() => toggle(intv.type)}
                  className={`shrink-0 px-3 py-1.5 rounded-md text-[10px] font-display tracking-[0.2em] transition flex items-center gap-1.5 ${
                    isOn
                      ? 'bg-emerald-500/20 text-emerald-200 border border-emerald-400/40 hover:bg-emerald-500/30'
                      : 'bg-cyan-500/10 text-cyan-200 border border-cyan-400/30 hover:bg-cyan-500/20'
                  }`}
                >
                  {isOn ? <><Check size={12} /> ACTIVE</> : <>DEPLOY <ArrowRight size={12} /></>}
                </button>
                {intv.recommendationId && (
                  <div className="flex flex-col gap-1">
                    {['generated', 'pending_review'].includes(intv.recommendationStatus ?? '') && (
                      <button disabled={busyId === `${intv.recommendationId}:approve`} onClick={() => void review(intv, 'approve')} className="px-2 py-1 rounded bg-emerald-500/10 border border-emerald-400/25 text-[9px] text-emerald-200 disabled:opacity-50">APPROVE</button>
                    )}
                    {!['executed', 'expired', 'superseded'].includes(intv.recommendationStatus ?? '') && (
                      <button disabled={busyId === `${intv.recommendationId}:reject`} onClick={() => void review(intv, 'reject')} className="px-2 py-1 rounded bg-rose-500/10 border border-rose-400/25 text-[9px] text-rose-200 disabled:opacity-50">REJECT</button>
                    )}
                    {intv.recommendationStatus === 'approved' && (
                      <button disabled={busyId === `${intv.recommendationId}:executed`} onClick={() => void review(intv, 'executed')} className="px-2 py-1 rounded bg-cyan-500/10 border border-cyan-400/25 text-[9px] text-cyan-200 disabled:opacity-50">MARK EXECUTED</button>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}