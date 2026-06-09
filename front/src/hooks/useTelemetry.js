import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchStatus } from '../services/api';

/**
 * Custom hook that polls the /status endpoint every `interval` ms.
 * Returns { status, loading, error, refetch }.
 */
export function useTelemetry(interval = 5000) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  const refetch = useCallback(async () => {
    try {
      const data = await fetchStatus();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Connection failed');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Initial fetch
    refetch();

    // Start polling
    intervalRef.current = setInterval(refetch, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [refetch, interval]);

  return { status, loading, error, refetch };
}
