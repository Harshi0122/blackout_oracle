import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { NumberAnim } from './NumberAnim';
import { Live } from './Live';
import type { BackendSnapshot } from '../lib/types';
import { ChevronRight, ShieldCheck, Zap, Cpu, Activity } from 'lucide-react';

interface Props {
  data: BackendSnapshot;
  onEnter: () => void;
}

export function Landing({ data, onEnter }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [typed, setTyped] = useState('');

  useEffect(() => {
    const target = 'BLACKOUT ORACLE';
    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setTyped(target.slice(0, i));
      if (i >= target.length) clearInterval(id);
    }, 90);
    return () => clearInterval(id);
  }, []);

  // City skyline canvas
  useEffect(() => {
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext('2d')!;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let raf = 0;
    const buildings: { x: number; w: number; h: number; windows: { x: number; y: number; state: number }[]; tx: number; ty: number }[] = [];
    const drops: { x: number; y: number; l: number; s: number }[] = [];
    const lines: { x1: number; y1: number; x2: number; y2: number; life: number; p: number }[] = [];

    const resize = () => {
      const r = canvas.getBoundingClientRect();
      canvas.width = r.width * dpr;
      canvas.height = r.height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const w = r.width;
      const h = r.height;
      buildings.length = 0;
      drops.length = 0;
      // generation of buildings
      let x = 0;
      while (x < w) {
        const bw = 30 + Math.random() * 60;
        const bh = 80 + Math.random() * 180;
        const wins: { x: number; y: number; state: number }[] = [];
        for (let i = 0; i < 8; i++) {
          for (let j = 0; j < Math.floor(bh / 18); j++) {
            wins.push({ x: i * (bw / 8) + bw / 16, y: h - bh + j * 18 + 12, state: Math.random() });
          }
        }
        buildings.push({ x, w: bw, h: bh, windows: wins, tx: x, ty: h - bh });
        x += bw + 2;
      }
      for (let i = 0; i < 220; i++) {
        drops.push({ x: Math.random() * w, y: Math.random() * h, l: 6 + Math.random() * 14, s: 4 + Math.random() * 8 });
      }
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const render = () => {
      const r = canvas.getBoundingClientRect();
      const w = r.width;
      const h = r.height;
      ctx.clearRect(0, 0, w, h);

      // sky gradient
      const sky = ctx.createLinearGradient(0, 0, 0, h);
      sky.addColorStop(0, '#0a1530');
      sky.addColorStop(0.5, '#1a2a52');
      sky.addColorStop(1, '#0a1428');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, w, h);

      // far clouds
      ctx.fillStyle = 'rgba(20, 25, 45, 0.7)';
      for (let i = 0; i < 6; i++) {
        const cx = ((i * 240 + performance.now() / 60) % (w + 200)) - 100;
        const cy = 60 + i * 12;
        ctx.beginPath();
        ctx.ellipse(cx, cy, 90, 22, 0, 0, Math.PI * 2);
        ctx.fill();
      }

      // buildings
      for (const b of buildings) {
        // body
        const grad = ctx.createLinearGradient(0, h - b.h, 0, h);
        grad.addColorStop(0, '#0a1838');
        grad.addColorStop(1, '#020714');
        ctx.fillStyle = grad;
        ctx.fillRect(b.x, h - b.h, b.w, b.h);
        // outline
        ctx.strokeStyle = 'rgba(34, 211, 238, 0.25)';
        ctx.lineWidth = 1;
        ctx.strokeRect(b.x + 0.5, h - b.h + 0.5, b.w - 1, b.h - 1);
        // windows
        for (const win of b.windows) {
          const flick = (Math.sin(performance.now() / 800 + win.x + win.y) + 1) / 2;
          if (flick > 0.35) {
            ctx.fillStyle = flick > 0.7 ? 'rgba(34, 211, 238, 0.6)' : 'rgba(250, 204, 21, 0.55)';
            ctx.fillRect(b.x + win.x - 2, win.y - 2, 4, 4);
          }
        }
        // antenna on tall ones
        if (b.h > 180) {
          ctx.strokeStyle = 'rgba(34, 211, 238, 0.8)';
          ctx.beginPath();
          ctx.moveTo(b.x + b.w / 2, h - b.h);
          ctx.lineTo(b.x + b.w / 2, h - b.h - 18);
          ctx.stroke();
          ctx.fillStyle = 'rgba(244, 63, 94, 0.95)';
          ctx.beginPath();
          ctx.arc(b.x + b.w / 2, h - b.h - 18, 1.6, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // transmission towers (silhouettes)
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
      ctx.lineWidth = 1.5;
      [0.15, 0.85].forEach((p) => {
        const tx = w * p;
        const ty = h - 40;
        ctx.beginPath();
        ctx.moveTo(tx, ty);
        ctx.lineTo(tx - 14, ty - 60);
        ctx.moveTo(tx, ty);
        ctx.lineTo(tx + 14, ty - 60);
        ctx.moveTo(tx - 14, ty - 60);
        ctx.lineTo(tx + 14, ty - 60);
        ctx.moveTo(tx - 10, ty - 36);
        ctx.lineTo(tx + 10, ty - 36);
        ctx.moveTo(tx - 6, ty - 48);
        ctx.lineTo(tx + 6, ty - 48);
        ctx.stroke();
      });
      // power lines between towers
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.3)';
      ctx.lineWidth = 0.6;
      ctx.beginPath();
      const x1 = w * 0.15;
      const x2 = w * 0.85;
      const y1 = h - 100;
      const y2 = h - 100;
      ctx.moveTo(x1, y1);
      // catenary
      for (let t = 0; t <= 1; t += 0.02) {
        const sag = Math.sin(t * Math.PI) * 16;
        ctx.lineTo(x1 + (x2 - x1) * t, y1 + sag);
      }
      ctx.stroke();

      // electricity flow along the power line
      const now = performance.now() / 1000;
      for (let k = 0; k < 5; k++) {
        const phase = (now * 0.6 + k * 0.18) % 1;
        const px = x1 + (x2 - x1) * phase;
        const py = y1 + Math.sin(phase * Math.PI) * 16;
        ctx.fillStyle = 'rgba(34, 211, 238, 0.9)';
        ctx.shadowColor = 'rgba(34, 211, 238, 0.9)';
        ctx.shadowBlur = 12;
        ctx.beginPath();
        ctx.arc(px, py, 2.2, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.shadowBlur = 0;

      // rain
      const rainAmt = Math.min(1, (data.weather.rainfall || 60) / 90);
      ctx.strokeStyle = `rgba(180, 220, 255, ${0.25 + rainAmt * 0.55})`;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      for (const d of drops) {
        d.y += d.s;
        d.x -= 0.5;
        if (d.y > h) {
          d.y = -10;
          d.x = Math.random() * w;
        }
        ctx.moveTo(d.x, d.y);
        ctx.lineTo(d.x - 1, d.y + d.l);
      }
      ctx.stroke();

      // lightning occasionally
      if (Math.random() < 0.0025 * (data.weather.lightningRate || 1)) {
        ctx.fillStyle = 'rgba(220, 235, 255, 0.45)';
        ctx.fillRect(0, 0, w, h);
        lines.push({ x1: Math.random() * w, y1: 0, x2: 0, y2: 0, life: 1, p: 0 });
      }
      ctx.strokeStyle = 'rgba(255,255,255,0.8)';
      ctx.lineWidth = 2;
      for (let i = lines.length - 1; i >= 0; i--) {
        const l = lines[i];
        l.life -= 0.04;
        if (l.life <= 0) { lines.splice(i, 1); continue; }
        let bx = l.x1, by = l.y1;
        ctx.beginPath();
        ctx.moveTo(bx, by);
        while (by < h * 0.55) {
          bx += (Math.random() - 0.5) * 28;
          by += 18 + Math.random() * 22;
          ctx.lineTo(bx, by);
        }
        ctx.stroke();
      }

      raf = requestAnimationFrame(render);
    };
    raf = requestAnimationFrame(render);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, [data.weather.rainfall, data.weather.lightningRate]);

  return (
    <div className="absolute inset-0 overflow-hidden">
      {/* Background city scene */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />

      {/* Cinematic gradient overlays */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#02030a] via-transparent to-[#02030a]/40 pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-r from-[#02030a]/60 via-transparent to-[#02030a]/60 pointer-events-none" />

      {/* Grid overlay */}
      <div className="absolute inset-0 bg-grid opacity-30 pointer-events-none" />

      {/* Top HUD */}
      <div className="absolute top-0 left-0 right-0 px-6 py-4 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center font-bold text-slate-900">B</div>
          <div className="leading-tight">
            <div className="text-xs font-display tracking-[0.32em] text-cyan-300">ORACLE · v2.4</div>
            <div className="text-[10px] font-mono text-slate-400">AGENTIC AI · CLIMATE GRID</div>
          </div>
        </div>
        <Live />
      </div>

      {/* Hero */}
      <div className="absolute inset-0 flex flex-col items-center justify-center px-6 text-center z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9 }}
          className="text-[11px] tracking-[0.4em] font-display text-cyan-300/80 mb-3"
        >
          AGENTIC AI · CLIMATE-RESILIENT SMART GRID
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.1, delay: 0.15 }}
          className="font-display font-bold text-5xl md:text-7xl lg:text-8xl tracking-tight"
        >
          <span className="bg-gradient-to-r from-cyan-300 via-blue-400 to-purple-400 bg-clip-text text-transparent drop-shadow-[0_0_30px_rgba(34,211,238,0.4)]">
            {typed || 'BLACKOUT ORACLE'}
          </span>
          <span className="inline-block w-1 h-12 md:h-20 bg-cyan-300 ml-1 animate-pulse" />
        </motion.h1>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-4 text-sm md:text-base text-slate-300 max-w-2xl font-display tracking-wide"
        >
          AI-powered climate &amp; smart grid crisis intelligence.
          <span className="block text-[11px] md:text-xs text-cyan-300/70 tracking-[0.2em] mt-1">
            ANTICIPATE · MITIGATE · RESTORE
          </span>
        </motion.div>

        {/* Live info chips */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
          className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-3 w-full max-w-4xl"
        >
          <InfoChip label="ENVIRONMENT" value="HEAVY RAIN" accent="cyan" />
          <InfoChip label="GRID STABILITY" value={`${Math.round(data.grid.stability)}%`} accent={data.grid.stability < 60 ? 'red' : 'cyan'} mono />
          <InfoChip label="CASCADE RISK" value={`${Math.round(data.grid.cascadeRisk * 100)}%`} accent={data.grid.cascadeRisk > 0.6 ? 'red' : 'amber'} mono />
          <InfoChip label="RAINFALL" value={`${data.weather.rainfall.toFixed(0)} mm/hr`} accent="cyan" mono />
        </motion.div>

        <motion.button
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.3 }}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={onEnter}
          className="mt-10 group relative px-8 py-4 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-900 font-bold tracking-[0.2em] text-sm shadow-[0_0_40px_rgba(34,211,238,0.5)] hover:shadow-[0_0_60px_rgba(34,211,238,0.8)] transition-all flex items-center gap-3"
        >
          <span className="absolute inset-0 rounded-lg bg-cyan-400 blur-xl opacity-40 group-hover:opacity-60 transition" />
          <span className="relative">ENTER LIVE COMMAND CENTER</span>
          <ChevronRight size={18} className="relative" />
        </motion.button>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.6 }}
          className="mt-8 flex items-center gap-6 text-[10px] tracking-[0.22em] font-display text-slate-400"
        >
          <span className="flex items-center gap-1.5"><ShieldCheck size={12} className="text-emerald-400" /> GRID-RESILIENT</span>
          <span className="flex items-center gap-1.5"><Zap size={12} className="text-amber-400" /> 150 ms LATENCY</span>
          <span className="flex items-center gap-1.5"><Cpu size={12} className="text-cyan-400" /> 17 NODES</span>
          <span className="flex items-center gap-1.5"><Activity size={12} className="text-rose-400 live-dot" /> LIVE FEED</span>
        </motion.div>
      </div>

      {/* Bottom marquee */}
      <div className="absolute bottom-0 left-0 right-0 bg-black/60 border-y border-cyan-400/10 overflow-hidden z-10">
        <div className="flex marquee-track whitespace-nowrap py-2 text-[10px] tracking-[0.22em] font-mono text-cyan-300/70">
          {Array.from({ length: 2 }).map((_, dup) => (
            <span key={dup} className="flex">
              {[
                '⚠ SUBSTATION A UTILIZATION 91%',
                '🌧 STORM CELL B 82 mm/hr',
                '⚡ 4 LIGHTNING STRIKES / MIN',
                '🔋 BATTERY BANK A SOC 42%',
                '⚠ HOSPITAL CASCADE EXPOSURE HIGH',
                '🤖 AGENTIC CORE: CASCADE-MITIGATION RECOMMENDED',
                '☀ SOLAR GENERATION REDUCED — CLOUD COVER 88%',
                '🏥 CENTRAL HOSPITAL PROTECTED BY REDUNDANT FEED',
                '⚡ OFFSHORE WIND GENERATION 102 MW',
                '🛰 LIVE TELEMETRY · 1500ms POLL · 17 NODES',
              ].map((s, i) => (
                <span key={i} className="px-6">{s}</span>
              ))}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function InfoChip({ label, value, accent, mono }: { label: string; value: string; accent: 'cyan' | 'amber' | 'red'; mono?: boolean }) {
  const colorMap = {
    cyan: 'from-cyan-400/15 to-blue-500/10 border-cyan-400/30 text-cyan-200',
    amber: 'from-amber-400/15 to-orange-500/10 border-amber-400/30 text-amber-200',
    red: 'from-rose-400/15 to-red-500/10 border-rose-400/30 text-rose-200',
  };
  return (
    <div className={`glass-soft rounded-md border ${colorMap[accent]} px-3 py-2 backdrop-blur-md`}>
      <div className="text-[9px] tracking-[0.22em] font-display opacity-70">{label}</div>
      <div className={`mt-1 ${mono ? 'font-mono text-base font-semibold' : 'font-display tracking-wide text-sm'} `}>{value}</div>
    </div>
  );
}