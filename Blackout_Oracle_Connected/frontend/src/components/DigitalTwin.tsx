import { useState } from 'react';
import { Sliders, Wind, Droplets, Thermometer, Zap, Sun, Battery, AlertTriangle, RotateCcw } from 'lucide-react';

interface Props {
  onChange: (config: TwinConfig) => void;
  config: TwinConfig;
  className?: string;
}

export interface TwinConfig {
  rainfall: number;
  wind: number;
  temp: number;
  demand: number;
  solar: number;
  windGen: number;
  battery: number;
  substationFailed: string | null;
}

// Interactive controls for the digital-twin simulator.
export function DigitalTwin({ onChange, config, className }: Props) {
  const [local, setLocal] = useState<TwinConfig>(config);

  const update = (patch: Partial<TwinConfig>) => {
    const next = { ...local, ...patch };
    setLocal(next);
    onChange(next);
  };

  const reset = () => {
    const def: TwinConfig = {
      rainfall: 50, wind: 35, temp: 20, demand: 60, solar: 30, windGen: 70, battery: 60, substationFailed: null,
    };
    setLocal(def);
    onChange(def);
  };

  const Slider = ({
    label, icon, value, min, max, onChange, unit, color,
  }: { label: string; icon: React.ReactNode; value: number; min: number; max: number; onChange: (n: number) => void; unit: string; color: string }) => (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-[10px] tracking-[0.18em] font-display">
        <span className="flex items-center gap-1.5 text-slate-400">{icon} {label}</span>
        <span className={`font-mono ${color}`}>{value.toFixed(0)}{unit}</span>
      </div>
      <input
        type="range" min={min} max={max} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full"
        style={{
          background: `linear-gradient(90deg, ${color.includes('rose') ? '#fb7185' : color.includes('amber') ? '#fbbf24' : color.includes('emerald') ? '#34d399' : color.includes('cyan') ? '#22d3ee' : '#a78bfa'} ${((value - min) / (max - min)) * 100}%, rgba(56,189,248,0.1) ${((value - min) / (max - min)) * 100}%)`,
        }}
      />
    </div>
  );

  return (
    <div className={`glass-soft rounded-lg p-3 space-y-3 ${className ?? ''}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sliders size={14} className="text-cyan-300" />
          <span className="text-[10px] tracking-[0.22em] font-display text-cyan-300">DIGITAL TWIN CONTROLS</span>
        </div>
        <button onClick={reset} className="text-[10px] flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800/60 hover:bg-slate-700/60 text-slate-300 font-display tracking-widest">
          <RotateCcw size={10} /> RESET
        </button>
      </div>

      <Slider label="RAINFALL" icon={<Droplets size={11} />} value={local.rainfall} min={0} max={150} onChange={(v) => update({ rainfall: v })} unit=" mm/hr" color="text-cyan-300" />
      <Slider label="WIND" icon={<Wind size={11} />} value={local.wind} min={0} max={120} onChange={(v) => update({ wind: v })} unit=" km/h" color="text-sky-300" />
      <Slider label="TEMPERATURE" icon={<Thermometer size={11} />} value={local.temp} min={-5} max={45} onChange={(v) => update({ temp: v })} unit="°C" color="text-amber-300" />
      <Slider label="DEMAND" icon={<Zap size={11} />} value={local.demand} min={0} max={150} onChange={(v) => update({ demand: v })} unit="%" color="text-rose-300" />
      <Slider label="SOLAR" icon={<Sun size={11} />} value={local.solar} min={0} max={100} onChange={(v) => update({ solar: v })} unit="%" color="text-emerald-300" />
      <Slider label="WIND GEN" icon={<Wind size={11} />} value={local.windGen} min={0} max={100} onChange={(v) => update({ windGen: v })} unit="%" color="text-cyan-300" />
      <Slider label="BATTERY SOC" icon={<Battery size={11} />} value={local.battery} min={0} max={100} onChange={(v) => update({ battery: v })} unit="%" color="text-emerald-300" />

      <div className="space-y-1.5">
        <div className="text-[10px] tracking-[0.18em] font-display text-slate-400 flex items-center gap-1.5">
          <AlertTriangle size={11} className="text-rose-300" /> SUBSTATION FAILURE
        </div>
        <div className="grid grid-cols-4 gap-1.5">
          {[
            { id: null, label: 'NONE' },
            { id: 'SUB-A', label: 'A' },
            { id: 'SUB-B', label: 'B' },
            { id: 'SUB-C', label: 'C' },
          ].map((s) => (
            <button
              key={String(s.id)}
              onClick={() => update({ substationFailed: s.id })}
              className={`text-[10px] py-1 rounded font-display tracking-widest transition ${
                local.substationFailed === s.id
                  ? 'bg-rose-500/20 text-rose-200 border border-rose-400/40'
                  : 'bg-slate-800/40 text-slate-300 border border-slate-700/40 hover:bg-slate-700/40'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}