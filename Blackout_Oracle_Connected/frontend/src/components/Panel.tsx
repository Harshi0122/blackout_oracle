import { motion } from 'framer-motion';
import type { ReactNode } from 'react';
import { ChevronRight } from 'lucide-react';

interface PanelProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  accent?: 'cyan' | 'red' | 'amber' | 'green';
  rightSlot?: ReactNode;
}

const accentMap = {
  cyan: 'from-cyan-400/60 to-blue-500/60',
  red: 'from-rose-500/70 to-red-500/60',
  amber: 'from-amber-400/70 to-orange-500/60',
  green: 'from-emerald-400/70 to-cyan-500/60',
};

export function Panel({
  title,
  subtitle,
  icon,
  children,
  className,
  collapsible,
  defaultCollapsed,
  accent = 'cyan',
  rightSlot,
}: PanelProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      className={`glass hud-bracket relative overflow-hidden ${className ?? ''}`}
    >
      <div className={`absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r ${accentMap[accent]}`} />
      <div className="flex items-center justify-between px-4 pt-3 pb-2 border-b border-cyan-400/10">
        <div className="flex items-center gap-2">
          {icon && <span className="text-cyan-300">{icon}</span>}
          <div>
            <div className="text-[10px] tracking-[0.22em] font-display text-cyan-200/80 uppercase">{title}</div>
            {subtitle && <div className="text-[10px] text-slate-400 font-mono mt-0.5">{subtitle}</div>}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {rightSlot}
          {collapsible && <ChevronRight size={14} className="text-cyan-300/70" />}
        </div>
      </div>
      <div className="px-4 py-3">{children}</div>
    </motion.div>
  );
}