import { useEffect, useState } from 'react';

// Live clock + tick marker.
export function Live() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  const t = now.toISOString().split('T')[1].slice(0, 8);
  return (
    <div className="flex items-center gap-2 text-[11px] font-mono text-cyan-200/80">
      <span className="w-2 h-2 rounded-full bg-rose-500 live-dot shadow-[0_0_10px_rgba(244,63,94,0.7)]" />
      <span className="tracking-[0.2em] text-rose-300/80">LIVE</span>
      <span className="text-slate-300/70">{t}</span>
    </div>
  );
}