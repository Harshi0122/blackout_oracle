import { useState } from 'react';
import { Play, LoaderCircle, AlertTriangle, CheckCircle2 } from 'lucide-react';
import type { TwinConfig } from './DigitalTwin';
import { executeFullSimulationWorkflow } from '../api/simulations';
import type { SimulationResponse } from '../api/types';

export function SimulationRunner({ config }: { config: TwinConfig }) {
  const [simulation, setSimulation] = useState<SimulationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  const run = async () => {
    setError(null);
    setRunning(true);
    try {
      const changes = config.substationFailed ? [{
        asset_id: config.substationFailed,
        parameter: 'availability',
        value: false,
        description: 'User-selected hypothetical asset failure for the digital twin.',
      }] : [];

      const result = await executeFullSimulationWorkflow({
        simulation_type: 'cascade',
        time_horizon_minutes: 60,
        time_step_seconds: 60,
        scenario: {
          name: 'Interactive Command Center Scenario',
          description: 'User-initiated hypothetical scenario created from Digital Twin controls.',
          simulation_type: 'cascade',
          changes,
          parameters: {
            rainfall_mm_per_hour: config.rainfall,
            wind_speed_kmh: config.wind,
            temperature_c: config.temp,
            demand_percent: config.demand,
            solar_percent: config.solar,
            wind_generation_percent: config.windGen,
            battery_soc_percent: config.battery,
          },
          metadata: { source: 'frontend_digital_twin' },
        },
      }, setSimulation);
      setSimulation(result.simulation);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Simulation request failed.');
    } finally {
      setRunning(false);
    }
  };

  return (
    <PanelShell>
      <button disabled={running} onClick={run} className="w-full flex items-center justify-center gap-2 rounded-md px-3 py-2 bg-cyan-500/15 border border-cyan-400/35 text-cyan-100 text-[10px] font-display tracking-[0.16em] disabled:opacity-60">
        {running ? <LoaderCircle size={13} className="animate-spin" /> : <Play size={13} />}
        {running ? 'RUNNING BACKEND SIMULATION' : 'RUN BACKEND SIMULATION'}
      </button>
      {simulation && <div className="mt-2 text-[10px] font-mono text-slate-300">
        <div className="flex items-center gap-1.5"><CheckCircle2 size={12} className="text-cyan-300" /> {simulation.status.toUpperCase()} · {simulation.id}</div>
        {simulation.warnings.length > 0 && <div className="mt-1 text-amber-300">{simulation.warnings.join(' · ')}</div>}
        {simulation.errors.length > 0 && <div className="mt-1 text-rose-300">{simulation.errors.join(' · ')}</div>}
      </div>}
      {error && <div className="mt-2 flex gap-1.5 text-[10px] text-rose-300"><AlertTriangle size={12}/>{error}</div>}
    </PanelShell>
  );
}

function PanelShell({ children }: { children: React.ReactNode }) {
  return <div className="glass-soft rounded-lg p-3 border border-cyan-400/10">{children}</div>;
}
