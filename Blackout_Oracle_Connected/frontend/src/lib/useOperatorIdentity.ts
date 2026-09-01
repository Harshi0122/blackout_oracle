import { useCallback, useState } from 'react';

const KEY = 'blackout-oracle-development-operator';

function initialValue() {
  try { return localStorage.getItem(KEY) || ''; } catch { return ''; }
}

export function useOperatorIdentity() {
  const [operatorId, setOperatorIdState] = useState(initialValue);
  const setOperatorId = useCallback((value: string) => {
    setOperatorIdState(value);
    try {
      if (value.trim()) localStorage.setItem(KEY, value.trim());
      else localStorage.removeItem(KEY);
    } catch { /* storage unavailable */ }
  }, []);
  return { operatorId, setOperatorId };
}
