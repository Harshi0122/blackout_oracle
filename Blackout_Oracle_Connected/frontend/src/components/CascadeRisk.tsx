import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { NumberAnim } from './NumberAnim';

interface Props {
  risk: number; // 0..1
  stability: number; // 0..100
  className?: string;
}

// Big graphical cascade risk: a sweeping radar gauge + concentric ripples
// rather than a flat progress bar.

export function CascadeRisk({ risk, stability, className }: Props) {
  const pct = Math.round(risk * 100);
  const color = useMemo(() => {
    if (risk < 0.25) return { stroke: '#22d3ee', glow: 'rgba(34,211,238,0.5)', label: 'LOW', tag: 'cyan' };
    if (risk < 0.5) return { stroke: '#facc15', glow: 'rgba(250,204,21,0.5)', label: 'MODERATE', tag: 'yellow' };
    if (risk < 0.75) return { stroke: '#fb923c', glow: 'rgba(251,146,60,0.55)', label: 'HIGH', tag: 'orange' };
    return { stroke: '#ef4444', glow: 'rgba(239,68,68,0.65)', label: 'CRITICAL', tag: 'red' };
  }, [risk]);

  // arc length & geometry
  const R = 86;
  const C = 2 * Math.PI * R;
  const half = C / 2;
  const filled = half * risk;
  const sweepDeg = 360 * risk;

  return (
    <div className={`relative ${className ?? ''}`} style={{ aspectRatio: '1 / 1', maxWidth: 280, margin: '0 auto' }}>
      <svg viewBox="0 0 220 220" width="100%" height="100%">
        <defs>
          <linearGradient id="risk-arc" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={color.stroke} stopOpacity="0.4" />
            <stop offset="50%" stopColor={color.stroke} stopOpacity="1" />
            <stop offset="100%" stopColor={color.stroke} stopOpacity="0.4" />
          </linearGradient>
          <radialGradient id="risk-center" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={color.stroke} stopOpacity="0.3" />
            <stop offset="60%" stopColor={color.stroke} stopOpacity="0.06" />
            <stop offset="100%" stopColor={color.stroke} stopOpacity="0" />
          </radialGradient>
          <filter id="risk-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" />
          </filter>
        </defs>

        {/* Concentric ripples */}
        {[1, 2, 3, 4].map((i) => (
          <circle
            key={i}
            cx={110}
            cy={110}
            r={26 + i * 18}
            fill="none"
            stroke={color.stroke}
            strokeOpacity={0.08 + (4 - i) * 0.04}
            strokeWidth={0.6}
          />
        ))}

        {/* Inner disc with gradient */}
        <circle cx={110} cy={110} r={92} fill="url(#risk-center)" />

        {/* Ticks */}
        {Array.from({ length: 48 }).map((_, i) => {
          const a = (i / 48) * Math.PI * 2 - Math.PI / 2;
          const x1 = 110 + Math.cos(a) * 98;
          const y1 = 110 + Math.sin(a) * 98;
          const x2 = 110 + Math.cos(a) * 104;
          const y2 = 110 + Math.sin(a) * 104;
          const major = i % 4 === 0;
          return (
            <line
              key={i}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={i / 48 > risk ? 'rgba(148,163,184,0.35)' : color.stroke}
              strokeWidth={major ? 1.5 : 0.6}
              strokeOpacity={major ? 0.85 : 0.45}
            />
          );
        })}

        {/* Background arc */}
        <circle cx={110} cy={110} r={R} fill="none" stroke="rgba(56,189,248,0.10)" strokeWidth={10} />

        {/* Active arc with glow */}
        <g transform="rotate(-90 110 110)">
          <circle
            cx={110}
            cy={110}
            r={R}
            fill="none"
            stroke="url(#risk-arc)"
            strokeWidth={10}
            strokeLinecap="round"
            strokeDasharray={`${filled} ${half - filled}`}
            style={{ transition: 'stroke-dasharray 0.7s cubic-bezier(0.16,1,0.3,1)' }}
            filter="url(#risk-glow)"
          />
          <circle
            cx={110}
            cy={110}
            r={R}
            fill="none"
            stroke={color.stroke}
            strokeWidth={6}
            strokeLinecap="round"
            strokeDasharray={`${filled} ${half - filled}`}
            style={{ transition: 'stroke-dasharray 0.7s cubic-bezier(0.16,1,0.3,1)' }}
          />
        </g>

        {/* Sweep radar */}
        <g className="radar-sweep" style={{ transformOrigin: '110px 110px' }}>
          <line x1={110} y1={110} x2={110} y2={20} stroke={color.stroke} strokeWidth={1} strokeOpacity="0.7" />
          <path
            d={`M 110 110 L ${110 + Math.cos(0) * 90} ${110 + Math.sin(0) * 90} A 90 90 0 0 0 ${110 + Math.cos(-Math.PI / 4) * 90} ${110 + Math.sin(-Math.PI / 4) * 90} Z`}
            fill={color.stroke}
            fillOpacity={0.08}
          />
        </g>

        {/* Numeric */}
      </svg>

      {/* Center label */}
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <div className="text-[10px] tracking-[0.28em] text-cyan-300/70 font-display">CASCADE RISK</div>
        <div
          className="font-mono font-bold text-5xl mt-1"
          style={{ color: color.stroke, textShadow: `0 0 22px ${color.glow}` }}
        >
          <NumberAnim value={pct} />
        </div>
        <div className="text-[10px] font-display tracking-[0.32em] mt-1" style={{ color: color.stroke }}>
          {color.label}
        </div>
        <div className="mt-3 flex items-center gap-1 text-[10px] font-mono text-slate-400">
          <span>STABILITY</span>
          <span className="text-cyan-300">{Math.round(stability)}%</span>
        </div>
      </div>
    </div>
  );
}