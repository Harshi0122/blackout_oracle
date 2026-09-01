import { useEffect, useRef } from 'react';
import type { WeatherData } from '../lib/types';
import { NumberAnim } from './NumberAnim';

interface Props {
  weather: WeatherData;
  className?: string;
}

// Cinematic weather visualization — not a card of numbers, but a small
// animated weather scene inside the panel.

export function WeatherViz({ weather, className }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext('2d')!;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let raf = 0;
    const drops: { x: number; y: number; l: number; s: number }[] = [];
    const clouds: { x: number; y: number; r: number; v: number; a: number }[] = [];

    const resize = () => {
      const r = canvas.getBoundingClientRect();
      canvas.width = Math.floor(r.width * dpr);
      canvas.height = Math.floor(r.height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    // init
    for (let i = 0; i < 80; i++) {
      drops.push({ x: Math.random() * 300, y: Math.random() * 200, l: 6 + Math.random() * 14, s: 4 + Math.random() * 8 });
    }
    for (let i = 0; i < 6; i++) {
      clouds.push({ x: Math.random() * 300, y: 20 + Math.random() * 60, r: 30 + Math.random() * 40, v: 0.3 + Math.random() * 0.5, a: 0.5 + Math.random() * 0.3 });
    }

    const render = () => {
      const r = canvas.getBoundingClientRect();
      ctx.clearRect(0, 0, r.width, r.height);

      // sky gradient
      const sky = ctx.createLinearGradient(0, 0, 0, r.height);
      const dark = Math.min(1, weather.cloudCover);
      sky.addColorStop(0, `rgba(${10 + (1 - dark) * 60}, ${16 + (1 - dark) * 30}, ${36 + (1 - dark) * 40}, 1)`);
      sky.addColorStop(1, 'rgba(2, 6, 18, 1)');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, r.width, r.height);

      // sun for heat mode
      if (weather.mode === 'heat') {
        const g = ctx.createRadialGradient(r.width * 0.78, r.height * 0.22, 0, r.width * 0.78, r.height * 0.22, 60);
        g.addColorStop(0, 'rgba(255, 200, 80, 0.95)');
        g.addColorStop(0.4, 'rgba(255, 150, 30, 0.4)');
        g.addColorStop(1, 'rgba(255, 100, 0, 0)');
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(r.width * 0.78, r.height * 0.22, 50, 0, Math.PI * 2);
        ctx.fill();
      }

      // clouds
      for (const c of clouds) {
        c.x -= c.v;
        if (c.x < -c.r) c.x = r.width + c.r;
        const grad = ctx.createRadialGradient(c.x, c.y, 0, c.x, c.y, c.r);
        grad.addColorStop(0, `rgba(20, 28, 50, ${c.a * (0.4 + dark * 0.8)})`);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2);
        ctx.fill();
      }

      // rain
      if (weather.rainfall > 0.5) {
        const opacity = Math.min(0.85, weather.rainfall / 90);
        ctx.strokeStyle = `rgba(180, 220, 255, ${opacity})`;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        for (const d of drops) {
          d.y += d.s;
          d.x -= 0.4;
          if (d.y > r.height) {
            d.y = -10;
            d.x = Math.random() * r.width;
          }
          ctx.moveTo(d.x, d.y);
          ctx.lineTo(d.x - 1, d.y + d.l);
        }
        ctx.stroke();
      }

      // flood water at bottom
      if (weather.floodLevel > 0.3) {
        const fh = r.height * weather.floodLevel * 0.35;
        const fg = ctx.createLinearGradient(0, r.height - fh, 0, r.height);
        fg.addColorStop(0, `rgba(34, 211, 238, ${weather.floodLevel * 0.5})`);
        fg.addColorStop(1, `rgba(20, 30, 80, ${weather.floodLevel * 0.9})`);
        ctx.fillStyle = fg;
        ctx.fillRect(0, r.height - fh, r.width, fh);
        // ripple lines
        ctx.strokeStyle = `rgba(150, 220, 255, ${weather.floodLevel * 0.6})`;
        ctx.lineWidth = 1;
        for (let i = 0; i < 4; i++) {
          ctx.beginPath();
          const y = r.height - fh + 4 + i * 5;
          for (let x = 0; x < r.width; x += 4) {
            ctx.lineTo(x, y + Math.sin((x + performance.now() / 300) * 0.1) * 1.4);
          }
          ctx.stroke();
        }
      }

      // lightning
      if (weather.lightningRate > 1 && Math.random() < 0.002 * weather.lightningRate) {
        ctx.fillStyle = 'rgba(220, 235, 255, 0.45)';
        ctx.fillRect(0, 0, r.width, r.height);
      }

      raf = requestAnimationFrame(render);
    };
    raf = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, [weather]);

  const metrics = [
    { label: 'RAINFALL', value: weather.rainfall, unit: 'mm/hr', color: 'text-cyan-300' },
    { label: 'WIND', value: weather.windSpeed, unit: 'km/h', color: 'text-sky-300' },
    { label: 'TEMP', value: weather.temperature, unit: '°C', color: 'text-amber-300' },
    { label: 'HUMIDITY', value: weather.humidity, unit: '%', color: 'text-emerald-300' },
    { label: 'PRESSURE', value: weather.pressure, unit: 'hPa', color: 'text-indigo-300' },
    { label: 'FLOOD', value: weather.floodLevel * 100, unit: '%', color: 'text-blue-400' },
  ];

  return (
    <div className={`relative overflow-hidden rounded-lg ${className ?? ''}`}>
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />
      <div className="relative grid grid-cols-3 gap-2 p-3 pt-2">
        {metrics.map((m) => (
          <div key={m.label} className="bg-black/30 backdrop-blur-sm border border-cyan-400/10 rounded-md p-2">
            <div className="text-[9px] tracking-[0.18em] text-slate-400 font-display">{m.label}</div>
            <div className={`font-mono text-base font-semibold ${m.color}`}>
              <NumberAnim value={m.value} decimals={m.label === 'PRESSURE' || m.label === 'TEMP' ? 1 : 0} />
              <span className="text-[9px] ml-1 opacity-70 font-display">{m.unit}</span>
            </div>
          </div>
        ))}
      </div>
      <div className="absolute top-2 right-2 px-2 py-0.5 rounded bg-cyan-500/20 border border-cyan-400/30 text-[9px] tracking-widest text-cyan-200 font-display">
        MODE · {weather.mode.toUpperCase()}
      </div>
    </div>
  );
}