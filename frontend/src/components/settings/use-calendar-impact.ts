"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useCallback } from "react";
import { toast } from "sonner";

import { usePlanFormat } from "@/components/plan/use-plan-format";
import { api } from "@/lib/api/client";
import { dateRuns, quartersHit, RESCHEDULE_QUERY } from "@/lib/plan/calendar-impact";
import { quarterLabel, quarterSlug, toRef } from "@/lib/plan/quarter";

/**
 * After leave or holidays change, tells the user which planned quarters now have an outdated
 * schedule and offers to preview the new one there.
 */
export function useCalendarImpact(kind: "leave" | "holiday") {
  const t = useTranslations("settings.impact");
  const fmt = usePlanFormat();
  const router = useRouter();

  return useCallback(
    async (dates: readonly string[]) => {
      if (dates.length === 0) return;
      const quarters = (await api.GET("/quarters").catch(() => null))?.data;
      if (!quarters) return;
      const hits = quartersHit(dates, quarters);
      const stale = await Promise.all(
        hits.map(async (hit) => {
          const schedule = await api
            .GET("/quarters/{quarter_id}/schedule", { params: { path: { quarter_id: hit.quarter.id } } })
            .catch(() => null);
          return schedule?.data?.stale ? hit : null;
        }),
      );
      for (const hit of stale) {
        if (!hit) continue;
        const days = dateRuns(hit.dates)
          .map(([start, end]) => fmt.dayRange(start, end))
          .join(", ");
        const ref = toRef(hit.quarter);
        const slug = quarterSlug(ref);
        toast.warning(t(kind, { quarter: quarterLabel(ref), days }), {
          id: `calendar-impact-${slug}`,
          duration: 15_000,
          action: { label: t("preview"), onClick: () => router.push(`/q/${slug}?${RESCHEDULE_QUERY}=1`) },
        });
      }
    },
    [t, fmt, router, kind],
  );
}
