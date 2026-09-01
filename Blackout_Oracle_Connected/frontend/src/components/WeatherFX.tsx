import { useEffect, useRef } from 'react';
import type { WeatherData } from '../lib/types';

interface WeatherFXProps {
  weather: WeatherData;
  intensity?: number; // 0..1.5 multiplier
  hostRef?: React.RefObject<HTMLDivElement | null>;
}

// Cinematic full-screen weather FX — driven entirely by the live backend data.
// Renders into its own absolutely-positioned canvases stacked over the scene.
// Layers (back-to-front): clouds → back rain → mid rain → front rain → wind → lightning flash → wet glare.

export function WeatherFX({ weather, intensity = 1 }: WeatherFXProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const stateRef = useRef<{
    rainBack: RainField;
    rainMid: RainField;
    rainFront: RainField;
    wind: WindField;
    clouds: CloudField;
    lightning: LightningState;
    size: { w: number; h: number };
    dpr: number;
  } | null>(null);

  useEffect(() => {
    const host = wrapRef.current!;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const cloudCanvas = document.createElement('canvas');
    const rainBackCanvas = document.createElement('canvas');
    const rainMidCanvas = document.createElement('canvas');
    const rainFrontCanvas = document.createElement('canvas');
    const windCanvas = document.createElement('canvas');
    const flashCanvas = document.createElement('canvas');

    [cloudCanvas, rainBackCanvas, rainMidCanvas, rainFrontCanvas, windCanvas, flashCanvas].forEach((c) => {
      c.style.position = 'absolute';
      c.style.inset = '0';
      c.style.width = '100%';
      c.style.height = '100%';
      c.style.pointerEvents = 'none';
    });
    cloudCanvas.style.zIndex = '1';
    rainBackCanvas.style.zIndex = '2';
    rainMidCanvas.style.zIndex = '3';
    rainFrontCanvas.style.zIndex = '4';
    windCanvas.style.zIndex = '5';
    flashCanvas.style.zIndex = '6';
    flashCanvas.style.mixBlendMode = 'screen';

    host.appendChild(cloudCanvas);
    host.appendChild(rainBackCanvas);
    host.appendChild(rainMidCanvas);
    host.appendChild(rainFrontCanvas);
    host.appendChild(windCanvas);
    host.appendChild(flashCanvas);

    const ctx = {
      cloud: cloudCanvas.getContext('2d')!,
      rainBack: rainBackCanvas.getContext('2d')!,
      rainMid: rainMidCanvas.getContext('2d')!,
      rainFront: rainFrontCanvas.getContext('2d')!,
      wind: windCanvas.getContext('2d')!,
      flash: flashCanvas.getContext('2d')!,
    };

    const size = { w: 0, h: 0 };
    const resize = () => {
      const r = host.getBoundingClientRect();
      size.w = r.width;
      size.h = r.height;
      [cloudCanvas, rainBackCanvas, rainMidCanvas, rainFrontCanvas, windCanvas, flashCanvas].forEach((c) => {
        c.width = Math.floor(size.w * dpr);
        c.height = Math.floor(size.h * dpr);
      });
      Object.values(ctx).forEach((c) => c.setTransform(dpr, 0, 0, dpr, 0, 0));
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(host);

    stateRef.current = {
      rainBack: makeRain(size.w, size.h, 0.45, 0),
      rainMid: makeRain(size.w, size.h, 0.85, 1),
      rainFront: makeRain(size.w, size.h, 1.35, 2),
      wind: makeWind(size.w, size.h),
      clouds: makeClouds(size.w, size.h),
      lightning: { alpha: 0, lastStrike: performance.now(), nextIn: 5000 },
      size,
      dpr,
    };

    let raf = 0;
    let lastT = performance.now();

    const loop = (t: number) => {
      const dt = Math.min(0.05, (t - lastT) / 1000);
      lastT = t;
      const s = stateRef.current!;
      const weather = (window as any).__BO_WEATHER__ as WeatherData | undefined;

      // ── clouds ──
      ctx.cloud.clearRect(0, 0, s.size.w, s.size.h);
      drawClouds(ctx.cloud, s.clouds, dt, weather);

      // ── rain ──
      const rainAmt = Math.min(1.4, (weather?.rainfall ?? 50) / 90);
      const opacity = rainAmt > 0.05 ? 0.32 + rainAmt * 0.5 : 0;
      ctx.rainBack.clearRect(0, 0, s.size.w, s.size.h);
      ctx.rainMid.clearRect(0, 0, s.size.w, s.size.h);
      ctx.rainFront.clearRect(0, 0, s.size.w, s.size.h);

      if (opacity > 0) {
        const wind = (weather?.windSpeed ?? 0) / 80;
        const angle = wind * 0.25; // radians
        drawRain(ctx.rainBack, s.rainBack, dt, angle, opacity * 0.5, weather);
        drawRain(ctx.rainMid, s.rainMid, dt, angle, opacity * 0.8, weather);
        drawRain(ctx.rainFront, s.rainFront, dt, angle, opacity, weather);
      }

      // ── wind streaks (only in storm / heat) ──
      ctx.wind.clearRect(0, 0, s.size.w, s.size.h);
      const windSpd = (weather?.windSpeed ?? 0);
      if (windSpd > 14) {
        drawWind(ctx.wind, s.wind, dt, windSpd);
      }

      // ── lightning ──
      ctx.flash.clearRect(0, 0, s.size.w, s.size.h);
      const lr = (weather?.lightningRate ?? 0);
      if (lr > 0.5) {
        if (t - s.lightning.lastStrike > s.lightning.nextIn) {
          s.lightning.alpha = 0.95;
          s.lightning.lastStrike = t;
          // Next strike between 1.5s and 8s (faster when more strikes/min).
          s.lightning.nextIn = 1500 + Math.random() * (6500 / Math.max(1, lr / 2));
        }
        if (s.lightning.alpha > 0) {
          ctx.flash.fillStyle = `rgba(220, 235, 255, ${s.lightning.alpha})`;
          ctx.flash.fillRect(0, 0, s.size.w, s.size.h);
          // Bolt
          drawLightningBolt(ctx.flash, s.size, s.lightning.alpha);
          s.lightning.alpha = Math.max(0, s.lightning.alpha - dt * 2.4);
        }
      }

      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      [cloudCanvas, rainBackCanvas, rainMidCanvas, rainFrontCanvas, windCanvas, flashCanvas].forEach((c) => c.remove());
    };
  }, []);

  // Push the latest weather into a global for the rAF loop to read.
  useEffect(() => {
    (window as any).__BO_WEATHER__ = weather;
  }, [weather]);

  return (
    <div
      ref={wrapRef}
      aria-hidden
      style={{
        position: 'absolute',
        inset: 0,
        zIndex: 2,
        pointerEvents: 'none',
        opacity: intensity,
      }}
    />
  );
}

// ─── Rain ─────────────────────────────────────────────────────────────────
interface RainField {
  drops: { x: number; y: number; len: number; speed: number }[];
  count: number;
}

function makeRain(w: number, h: number, density: number, seedOffset: number): RainField {
  const count = Math.floor((w * h) / (14000 / density));
  const drops = new Array(count);
  for (let i = 0; i < count; i++) {
    drops[i] = {
      x: Math.random() * w,
      y: Math.random() * h,
      len: 8 + Math.random() * 18,
      speed: (4 + Math.random() * 8) * density,
    };
  }
  return { drops, count };
}

function drawRain(
  ctx: CanvasRenderingContext2D,
  field: RainField,
  dt: number,
  angle: number,
  opacity: number,
  weather: WeatherData | undefined,
) {
  const drops = field.drops;
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  ctx.lineWidth = 1.4;
  ctx.strokeStyle = `rgba(180, 220, 255, ${opacity})`;
  ctx.beginPath();
  for (let i = 0; i < drops.length; i++) {
    const d = drops[i];
    d.y += d.speed * dt * 60;
    d.x += d.speed * dt * 60 * sin * 0.4;
    if (d.y > field.count + 100 || d.x < -50 || d.x > 3000) {
      d.y = -Math.random() * 60;
      d.x = Math.random() * 3000;
    }
    ctx.moveTo(d.x, d.y);
    ctx.lineTo(d.x + sin * d.len, d.y + cos * d.len);
  }
  ctx.stroke();

  // Subtle splash layer near bottom for "wet surface" feel — only if rainAmt big.
  if (weather && weather.rainfall > 30 && opacity > 0.4) {
    const splashes = Math.floor(opacity * 30);
    ctx.fillStyle = `rgba(150, 200, 255, ${opacity * 0.6})`;
    for (let i = 0; i < splashes; i++) {
      const x = Math.random() * 3000;
      const y = 600 + Math.random() * 100;
      ctx.fillRect(x, y, 1.5, 1.5);
    }
  }
}

// ─── Wind streaks ──────────────────────────────────────────────────────────
interface WindField {
  streaks: { x: number; y: number; len: number; speed: number; alpha: number }[];
}

function makeWind(w: number, h: number): WindField {
  const streaks = Array.from({ length: 60 }, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    len: 40 + Math.random() * 80,
    speed: 1 + Math.random() * 2,
    alpha: 0.05 + Math.random() * 0.18,
  }));
  return { streaks };
}

function drawWind(ctx: CanvasRenderingContext2D, field: WindField, dt: number, speed: number) {
  ctx.lineWidth = 1;
  for (const s of field.streaks) {
    s.x += s.speed * (speed / 20) * dt * 60;
    if (s.x > 2000) {
      s.x = -s.len;
      s.y = Math.random() * 800;
    }
    ctx.strokeStyle = `rgba(200, 230, 255, ${s.alpha})`;
    ctx.beginPath();
    ctx.moveTo(s.x, s.y);
    ctx.lineTo(s.x + s.len, s.y);
    ctx.stroke();
  }
}

// ─── Clouds ────────────────────────────────────────────────────────────────
interface CloudField {
  puffs: { x: number; y: number; r: number; shade: number; speed: number }[];
}

function makeClouds(w: number, h: number): CloudField {
  const puffs = [];
  const count = 22;
  for (let i = 0; i < count; i++) {
    puffs.push({
      x: Math.random() * w * 1.4,
      y: Math.random() * h * 0.4,
      r: 80 + Math.random() * 180,
      shade: 0.05 + Math.random() * 0.18,
      speed: 0.2 + Math.random() * 0.8,
    });
  }
  return { puffs };
}

function drawClouds(
  ctx: CanvasRenderingContext2D,
  field: CloudField,
  dt: number,
  weather: WeatherData | undefined,
) {
  const dark = Math.min(1, (weather?.cloudCover ?? 0.5));
  for (const p of field.puffs) {
    p.x -= p.speed * dt * 12;
    if (p.x < -p.r * 2) p.x = 2000 + Math.random() * 200;
    const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r);
    const a = p.shade * (0.4 + dark * 0.9);
    grad.addColorStop(0, `rgba(20, 30, 60, ${a})`);
    grad.addColorStop(0.6, `rgba(15, 22, 45, ${a * 0.5})`);
    grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fill();
  }
}

// ─── Lightning ─────────────────────────────────────────────────────────────
interface LightningState {
  alpha: number;
  lastStrike: number;
  nextIn: number;
}

function drawLightningBolt(ctx: CanvasRenderingContext2D, size: { w: number; h: number }, alpha: number) {
  const startX = Math.random() * size.w;
  let x = startX;
  let y = 0;
  ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
  ctx.lineWidth = 2.2;
  ctx.shadowColor = `rgba(160, 200, 255, ${alpha})`;
  ctx.shadowBlur = 18;
  ctx.beginPath();
  ctx.moveTo(x, y);
  while (y < size.h * 0.55) {
    x += (Math.random() - 0.5) * 36;
    y += 18 + Math.random() * 24;
    ctx.lineTo(x, y);
  }
  ctx.stroke();
  ctx.shadowBlur = 0;
}