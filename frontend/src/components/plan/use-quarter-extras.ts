"use client";

import { useCallback } from "react";

import { useLoad } from "@/hooks/use-load";
import { api } from "@/lib/api/client";

import { usePlanData } from "./plan-data";

/** KR checkpoints for the loaded quarter; refetched whenever the stored schedule changes. */
export function useKrMilestones() {
  const { state } = usePlanData();
  const payload = state.status === "ready" ? state.data : null;
  const quarterId = payload?.summary?.id ?? null;
  const version = payload?.schedule?.created_at ?? null;
  const fetcher = useCallback(async () => {
    if (quarterId === null || version === null) return [];
    const { data } = await api.GET("/quarters/{quarter_id}/kr-milestones", {
      params: { path: { quarter_id: quarterId } },
    });
    return data;
  }, [quarterId, version]);
  return useLoad(fetcher);
}

/** Holidays and make-up days of the given years, keyed by date. */
export function useHolidays(years: readonly number[]) {
  const key = [...new Set(years)].sort().join(",");
  const fetcher = useCallback(async () => {
    const lists = await Promise.all(
      key.split(",").map((y) => api.GET("/calendar/holidays", { params: { query: { year: Number(y) } } })),
    );
    if (lists.some((l) => !l.data)) return undefined;
    return new Map(lists.flatMap((l) => l.data ?? []).map((h) => [h.date, h]));
  }, [key]);
  return useLoad(fetcher);
}
