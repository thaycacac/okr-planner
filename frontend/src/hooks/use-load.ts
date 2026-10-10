"use client";

import { useCallback, useEffect, useState } from "react";

export type LoadState<T> = { status: "loading" } | { status: "error" } | { status: "ready"; data: T };

// `fetcher` must be referentially stable (module-level or memoized).
export function useLoad<T>(fetcher: () => Promise<T | undefined>) {
  const [state, setState] = useState<LoadState<T>>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    fetcher().then(
      (data) => {
        if (!cancelled) setState(data === undefined ? { status: "error" } : { status: "ready", data });
      },
      () => {
        if (!cancelled) setState({ status: "error" });
      },
    );
    return () => {
      cancelled = true;
    };
  }, [fetcher, attempt]);

  const retry = useCallback(() => {
    setState({ status: "loading" });
    setAttempt((n) => n + 1);
  }, []);

  /** Refetches without the loading state; the current data stays when the request fails. */
  const refresh = useCallback(async () => {
    try {
      const data = await fetcher();
      if (data === undefined) return false;
      setState({ status: "ready", data });
      return true;
    } catch {
      return false;
    }
  }, [fetcher]);

  return [state, retry, refresh] as const;
}
