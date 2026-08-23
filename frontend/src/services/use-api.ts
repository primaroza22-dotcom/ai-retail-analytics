"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { errorMessage } from "./api";

interface ApiState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  refresh: () => void;
}

/**
 * Fetch data from the backend on mount and whenever `refresh` is called.
 * The fetcher is stored in a ref so callers can pass an inline closure without
 * triggering repeated requests.
 */
export function useApi<T>(fetcher: () => Promise<T>): ApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  const fetcherRef = useRef(fetcher);
  useEffect(() => {
    fetcherRef.current = fetcher;
  });

  const refresh = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;

    Promise.resolve()
      .then(() => {
        if (cancelled) return undefined;
        setLoading(true);
        setError(null);
        return fetcherRef.current();
      })
      .then((result) => {
        if (!cancelled && result !== undefined) {
          setData(result);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(errorMessage(err));
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [tick]);

  return { data, error, loading, refresh };
}
