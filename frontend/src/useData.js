import { useState, useEffect, useRef } from "react";

/**
 * Fetches data whenever `deps` change.
 * The fetcher is called fresh on each dep change — no stale closure issues.
 */
export function useData(fetcher, deps = []) {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    let cancelled = false;

    setLoading(true);
    setError(null);

    fetcher()
      .then(d  => { if (!cancelled) { setData(d); setLoading(false); } })
      .catch(e => {
        if (!cancelled) {
          setError(e?.response?.data?.detail ?? e.message ?? "Request failed");
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  const reload = () => {
    setLoading(true);
    setError(null);
    fetcher()
      .then(d  => { setData(d);    setLoading(false); })
      .catch(e => { setError(e?.response?.data?.detail ?? e.message ?? "Request failed"); setLoading(false); });
  };

  return { data, loading, error, reload };
}
