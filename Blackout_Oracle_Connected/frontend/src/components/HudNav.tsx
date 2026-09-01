import { motion } from 'framer-motion';
import { Activity, BarChart3, Brain, GitCompare, MapPinned, Sparkles, Cpu } from 'lucide-react';

export type ViewKey = 'command' | 'cascade' | 'digital-twin' | 'interventions' | 'before-after';

interface Props {
  active: ViewKey;
  onChange: (v: ViewKey) => void;
}

const NAV: { key: ViewKey; label: string; sub: string; icon: React.ReactNode }[] = [
  { key: 'command', label: 'COMMAND', sub: 'Live Grid', icon: <Activity size={14} /> },
  { key: 'cascade', label: 'CASCADE', sub: 'Failure Sim', icon: <BarChart3 size={14} /> },
  { key: 'digital-twin', label: 'DIGITAL TWIN', sub: 'Scenario Lab', icon: <MapPinned size={14} /> },
  { key: 'interventions', label: 'AI CONTROL', sub: 'Interventions', icon: <Brain size={14} /> },
  { key: 'before-after', label: 'COMPARE', sub: 'Before / After', icon: <GitCompare size={14} /> },
];

export function HudNav({ active, onChange }: Props) {
  return (
    <div className="flex items-center gap-1">
      {NAV.map((n) => (
        <button
          key={n.key}
          onClick={() => onChange(n.key)}
          className={`relative px-3 py-2 rounded-md transition-colors group ${
            active === n.key ? 'bg-cyan-500/15 text-cyan-100' : 'text-slate-300 hover:bg-slate-700/30'
          }`}
        >
          {active === n.key && (
            <motion.div
              layoutId="nav-active"
              className="absolute inset-0 rounded-md border border-cyan-400/50"
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            />
          )}
          <div className="relative flex items-center gap-2">
            <span className={active === n.key ? 'text-cyan-300' : 'text-slate-400'}>{n.icon}</span>
            <div className="text-left">
              <div className="text-[10px] font-display tracking-[0.2em] leading-none">{n.label}</div>
              <div className="text-[8px] font-mono text-slate-500 leading-none mt-0.5">{n.sub}</div>
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}