import { AnimatePresence, motion } from 'framer-motion';
import { useLiveData } from './lib/useLiveData';
import { RefreshCw, Wifi, WifiOff } from 'lucide-react';
import { Landing } from './components/Landing';
import { CommandCenter } from './components/CommandCenter';
import { LocationOperatorControls } from './components/LocationOperatorControls';
import { store } from './lib/store';
import { useEffect, useState } from 'react';
import { useLocation } from './lib/useLocation';
import { useOperatorIdentity } from './lib/useOperatorIdentity';

function App() {
  const location = useLocation();
  const operator = useOperatorIdentity();
  const { data, meta, refresh } = useLiveData(location.activeLocation);
  const [view, setView] = useState<'landing' | 'command'>(store.get().view === 'landing' ? 'landing' : 'command');

  useEffect(() => {
    const unsub = store.subscribe(() => {
      const next = store.get().view === 'landing' ? 'landing' : 'command';
      setView(next);
    });
    return unsub;
  }, []);

  const onEnter = () => {
    store.set({ view: 'command' });
    setView('command');
  };

  return (
    <div className="app-shell">
      <div className={`api-status ${meta.connected ? 'online' : 'offline'}`}>
        {meta.connected ? <Wifi size={13}/> : <WifiOff size={13}/>}
        {meta.connected ? (meta.partial ? 'LIVE • PARTIAL' : 'LIVE • API') : 'BACKEND UNAVAILABLE'}
        <button onClick={refresh} title="Refresh backend"><RefreshCw size={13}/></button>
      </div>
      <LocationOperatorControls
        location={location.activeLocation}
        locationError={location.locationError}
        loading={location.loading}
        onSelect={location.selectLocation}
        onBrowserLocation={location.requestBrowserLocation}
        operatorId={operator.operatorId}
        onOperatorChange={operator.setOperatorId}
      />
      <AnimatePresence mode="wait">
        {view === 'landing' ? (
          <motion.div key="landing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, scale: 1.04, filter: 'blur(8px)' }} transition={{ duration: 0.6 }} className="absolute inset-0">
            <Landing data={data} onEnter={onEnter} />
          </motion.div>
        ) : (
          <motion.div key="command" initial={{ opacity: 0, scale: 0.97, filter: 'blur(8px)' }} animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }} exit={{ opacity: 0 }} transition={{ duration: 0.7 }} className="absolute inset-0">
            <CommandCenter data={data} operatorId={operator.operatorId} onRefresh={refresh} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
