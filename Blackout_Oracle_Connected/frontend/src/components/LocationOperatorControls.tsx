import { useState } from 'react';
import { Crosshair, MapPin, UserRound, ChevronUp, ChevronDown, Loader2 } from 'lucide-react';
import type { ActiveLocation } from '../lib/useLocation';

interface Props {
  location: ActiveLocation;
  locationError?: string;
  loading?: boolean;
  onSelect: (latitude: number, longitude: number, name: string) => void;
  onBrowserLocation: () => void;
  operatorId: string;
  onOperatorChange: (value: string) => void;
}

export function LocationOperatorControls({
  location, locationError, loading, onSelect, onBrowserLocation, operatorId, onOperatorChange,
}: Props) {
  const [latitude, setLatitude] = useState(String(location.latitude));
  const [longitude, setLongitude] = useState(String(location.longitude));
  const [name, setName] = useState(location.name);
  const [collapsed, setCollapsed] = useState(false);

  const apply = () => {
    const lat = Number(latitude);
    const lon = Number(longitude);
    if (Number.isFinite(lat) && lat >= -90 && lat <= 90 && Number.isFinite(lon) && lon >= -180 && lon <= 180) {
      onSelect(lat, lon, name.trim() || 'User Selected Location');
    }
  };

  const sourceLabel = location.source === 'geolocation' ? 'LIVE GPS'
    : location.source === 'ip_fallback' ? 'LIVE NETWORK'
    : location.source === 'user' ? 'MANUAL'
    : 'DEMO DEFAULT';

  return (
    <div className="fixed left-3 bottom-3 z-[70] w-[310px] glass rounded-lg border border-cyan-400/20 p-3 text-[10px] shadow-2xl transition-all duration-300">
      <div className="flex items-center gap-2 text-cyan-200 font-display tracking-[0.16em] cursor-pointer select-none" onClick={() => setCollapsed(!collapsed)}>
        <MapPin size={13} /> LOCATION · {sourceLabel}
        <span className="ml-auto text-cyan-400/60">{collapsed ? <ChevronUp size={13} /> : <ChevronDown size={13} />}</span>
      </div>
      {!collapsed && (
        <>
          <div className="mt-2 text-slate-300 truncate">{location.name}</div>

          {/* Live location button */}
          <button
            onClick={onBrowserLocation}
            disabled={loading}
            className="mt-2 w-full flex items-center justify-center gap-2 rounded bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400/40 px-3 py-2 text-cyan-100 font-display tracking-widest text-[11px] transition disabled:opacity-50"
          >
            {loading ? <Loader2 size={14} className="text-cyan-300 animate-spin" /> : <Crosshair size={14} className="text-cyan-300" />}
            {loading ? 'DETECTING...' : 'USE LIVE LOCATION'}
          </button>

          <div className="mt-2 flex items-center gap-2 text-[9px] text-slate-500 font-display tracking-widest">
            <div className="flex-1 h-px bg-cyan-400/10" />
            OR ENTER MANUALLY
            <div className="flex-1 h-px bg-cyan-400/10" />
          </div>

          <div className="mt-2 grid grid-cols-2 gap-2">
            <input value={latitude} onChange={(e) => setLatitude(e.target.value)} placeholder="Latitude" className="bg-black/30 border border-cyan-400/15 rounded px-2 py-1.5 text-cyan-100" />
            <input value={longitude} onChange={(e) => setLongitude(e.target.value)} placeholder="Longitude" className="bg-black/30 border border-cyan-400/15 rounded px-2 py-1.5 text-cyan-100" />
          </div>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Location name" className="mt-2 w-full bg-black/30 border border-cyan-400/15 rounded px-2 py-1.5 text-cyan-100" />
          <button onClick={apply} className="mt-2 w-full rounded bg-slate-700/50 border border-slate-500/30 px-2 py-1.5 text-slate-100 font-display tracking-widest text-[10px]">
            APPLY COORDINATES
          </button>

          {locationError && <div className="mt-2 text-amber-300 text-center">{locationError}</div>}

          <div className="mt-3 pt-2 border-t border-cyan-400/10 flex items-center gap-2 text-slate-400 font-display tracking-[0.12em]">
            <UserRound size={12} /> DEVELOPMENT OPERATOR
          </div>
          <input value={operatorId} onChange={(e) => onOperatorChange(e.target.value)} placeholder="Enter operator identity for actions" className="mt-2 w-full bg-black/30 border border-cyan-400/15 rounded px-2 py-1.5 text-cyan-100" />
        </>
      )}
    </div>
  );
}
