import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Activity, ShieldCheck, ChevronRight } from 'lucide-react';
import type { Alert, GridData } from '../lib/types';
import { store } from '../lib/store';
import { acknowledgeAlert, dismissAlert, resolveAlert } from '../api/alerts';

interface Props {
  alert: Alert;
  grid: GridData;
  className?: string;
  operatorId: string;
  onMutated?: () => void;
}

// Cinematic critical alert overlay — slight vignette, focused on node,
// animated warning wave.

export function CriticalAlert({ alert, grid, className, operatorId, onMutated }: Props) {
  const [open, setOpen] = useState(true);
  const [acknowledged, setAcknowledged] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const perform = async (action: 'acknowledge' | 'resolve' | 'dismiss') => {
    setActionError(null);
    if ((action === 'acknowledge' || action === 'resolve') && !operatorId.trim()) {
      setActionError('Enter a development operator identity before this action.');
      return;
    }
    setBusy(true);
    try {
      if (action === 'acknowledge') {
        await acknowledgeAlert(alert.id, { acknowledged_by: operatorId.trim() });
        setAcknowledged(true);
      } else if (action === 'resolve') {
        await resolveAlert(alert.id, { resolved_by: operatorId.trim() });
        setOpen(false);
      } else {
        await dismissAlert(alert.id);
        setOpen(false);
      }
      onMutated?.();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Alert action failed.');
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    setOpen(true);
    setAcknowledged(false);
  }, [alert.id]);

  const node = grid.nodes.find((n) => n.id === alert.nodeId);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Page-wide vignette */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 pointer-events-none z-40 alert-vignette"
            aria-hidden
          />

          <motion.div
            initial={{ x: 380, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 380, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 200, damping: 24 }}
            className={`fixed top-1/2 -translate-y-1/2 right-6 z-50 w-[380px] ${className ?? ''}`}
          >
            <div className="glass rounded-lg overflow-hidden border-rose-500/40 shadow-[0_0_50px_rgba(244,63,94,0.35)]">
              {/* Header */}
              <div className="relative bg-gradient-to-r from-rose-600/30 via-rose-500/20 to-rose-700/20 px-4 py-3 border-b border-rose-500/30">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <AlertTriangle size={22} className="text-rose-300" />
                    <span className="absolute inset-0 rounded-full pulse-ring border-2 border-rose-400/60" />
                  </div>
                  <div>
                    <div className="text-[10px] tracking-[0.32em] font-display text-rose-300">CRITICAL EVENT DETECTED</div>
                    <div className="text-base font-display text-white mt-0.5">{alert.title}</div>
                  </div>
                </div>
              </div>

              {/* Body */}
              <div className="p-4 space-y-3">
                <div className="text-sm text-slate-300">{alert.subtitle}</div>

                {alert.cascadeWindowMin && (
                  <div className="bg-rose-500/10 border border-rose-500/30 rounded-md p-3 flex items-center justify-between">
                    <div>
                      <div className="text-[10px] tracking-[0.22em] font-display text-rose-300/80">ESTIMATED CASCADE WINDOW</div>
                      <div className="font-mono text-2xl font-bold text-rose-200 mt-0.5">{alert.cascadeWindowMin}<span className="text-sm text-rose-300/70 ml-1">MIN</span></div>
                    </div>
                    <Activity size={28} className="text-rose-400/60 live-dot" />
                  </div>
                )}

                {node && (
                  <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                    <div className="bg-black/30 border border-cyan-400/10 rounded-md p-2">
                      <div className="text-[9px] tracking-widest text-slate-400">UTILIZATION</div>
                      <div className="text-rose-300 font-semibold">{(node.utilization * 100).toFixed(0)}%</div>
                    </div>
                    <div className="bg-black/30 border border-cyan-400/10 rounded-md p-2">
                      <div className="text-[9px] tracking-widest text-slate-400">LOAD</div>
                      <div className="text-cyan-200 font-semibold">{node.load.toFixed(1)} MW</div>
                    </div>
                  </div>
                )}

                {/* Warning wave */}
                <div className="relative h-10 rounded-md overflow-hidden bg-rose-500/5 border border-rose-500/20">
                  <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-[200%] h-full flex">
                    <div className="w-1/2 h-full bg-gradient-to-r from-transparent via-rose-400/30 to-transparent" />
                    <div className="w-1/2 h-full bg-gradient-to-r from-transparent via-rose-400/30 to-transparent" />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-2">
                  <button
                    onClick={() => void perform('acknowledge')} disabled={busy}
                    className="glass-soft hover:bg-rose-500/10 px-3 py-2 rounded-md flex items-center justify-between text-rose-200 text-xs font-display tracking-widest border-rose-400/30"
                  >
                    <span className="flex items-center gap-2"><Activity size={14} /> ANALYZE CAUSE</span>
                    <ChevronRight size={14} />
                  </button>
                  <button onClick={() => void perform('resolve')} disabled={busy} className="glass-soft hover:bg-amber-500/10 px-3 py-2 rounded-md flex items-center justify-between text-amber-200 text-xs font-display tracking-widest border-amber-400/30 disabled:opacity-50">
                    <span className="flex items-center gap-2"><ShieldCheck size={14} /> RESOLVE ALERT</span>
                    <ChevronRight size={14} />
                  </button>
                  <button className="glass-soft hover:bg-cyan-500/10 px-3 py-2 rounded-md flex items-center justify-between text-cyan-200 text-xs font-display tracking-widest border-cyan-400/30">
                    <span className="flex items-center gap-2"><ChevronRight size={14} /> VIEW INTERVENTIONS</span>
                    <ChevronRight size={14} />
                  </button>
                </div>
              </div>

              {actionError && <div className="px-4 pb-2 text-[10px] text-rose-300">{actionError}</div>}
              {/* Footer */}
              <div className="px-4 py-2 border-t border-rose-500/20 flex items-center justify-between text-[10px] font-mono text-slate-400">
                <span>ORACLE · {acknowledged ? 'ACKNOWLEDGED' : 'AWAITING OPERATOR'}</span>
                <button onClick={() => void perform('dismiss')} disabled={busy} className="hover:text-white disabled:opacity-50">DISMISS</button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}