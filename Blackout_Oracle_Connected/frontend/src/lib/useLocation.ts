import { useCallback, useState } from 'react';

export type LocationSource = 'user' | 'geolocation' | 'ip_fallback' | 'demo_default';

export interface ActiveLocation {
  latitude: number;
  longitude: number;
  name: string;
  source: LocationSource;
}

const DEMO_LOCATION: ActiveLocation = {
  latitude: 34.0522,
  longitude: -118.2437,
  name: 'Los Angeles Grid Sector (Demo Default)',
  source: 'demo_default',
};

export function useLocation() {
  const [activeLocation, setActiveLocation] = useState<ActiveLocation>(DEMO_LOCATION);
  const [locationError, setLocationError] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);

  const selectLocation = useCallback((latitude: number, longitude: number, name: string) => {
    setLocationError(undefined);
    setActiveLocation({ latitude, longitude, name, source: 'user' });
  }, []);

  const requestBrowserLocation = useCallback(() => {
    setLoading(true);
    setLocationError(undefined);

    // Check if geolocation is available AND we're in a secure context
    const isSecureContext = window.isSecureContext || location.hostname === 'localhost' || location.hostname === '127.0.0.1';

    if (!navigator.geolocation || !isSecureContext) {
      // Browser geolocation not available (HTTP non-localhost) — fall back to IP geolocation
      fallbackToIpGeolocation();
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLoading(false);
        setLocationError(undefined);
        setActiveLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          name: 'Browser Location',
          source: 'geolocation',
        });
      },
      () => {
        // Browser geolocation denied or failed — fall back to IP geolocation
        fallbackToIpGeolocation();
      },
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 300000 },
    );

    function fallbackToIpGeolocation() {
      setLocationError('Detecting location via network...');
      // Try ipinfo.io first (reliable, HTTPS, generous free tier)
      fetch('https://ipinfo.io/json')
        .then((res) => {
          if (!res.ok) throw new Error('IP lookup failed');
          return res.json();
        })
        .then((data) => {
          setLoading(false);
          if (data.loc) {
            const [lat, lon] = data.loc.split(',').map(Number);
            if (Number.isFinite(lat) && Number.isFinite(lon)) {
              setLocationError(undefined);
              const locName = [data.city, data.region, data.country].filter(Boolean).join(', ');
              setActiveLocation({
                latitude: lat,
                longitude: lon,
                name: locName || 'Network Location',
                source: 'ip_fallback',
              });
              return;
            }
          }
          // Fallback: use geocode endpoint
          return fetch('https://ipinfo.io/geo').then(r => r.json()).then((geo) => {
            setLoading(false);
            if (geo.latitude && geo.longitude) {
              setLocationError(undefined);
              const locName = [geo.city, geo.region, geo.country].filter(Boolean).join(', ');
              setActiveLocation({
                latitude: geo.latitude,
                longitude: geo.longitude,
                name: locName || 'Network Location',
                source: 'ip_fallback',
              });
            } else {
              setLocationError('Could not determine location. Enter coordinates manually.');
            }
          });
        })
        .catch(() => {
          setLoading(false);
          setLocationError('Location detection failed. Enter coordinates manually.');
        });
    }
  }, []);

  return { activeLocation, locationError, loading, selectLocation, requestBrowserLocation };
}
