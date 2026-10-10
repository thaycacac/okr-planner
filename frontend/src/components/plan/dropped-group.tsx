"use client";

import { ChevronRightIcon, Undo2Icon } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { toast } from "sonner";
import { cn } from "cn";

import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Spinner } from "@/components/ui/spinner";
import { useApiErrorMessage } from "@/hooks/use-api-error-message";
import { api } from "@/lib/api/client";
import { type DroppedItem, droppedTotals } from "@/lib/plan/plan-view";

import { useReadyPlan } from "./plan-data";
import { useReschedule } from "./reschedule-flow";
const itemKey = (item: DroppedItem) => (item.kind === "objective" ? `o-${item.objective.id}` : `k-${item.kr.id}`);

/** KRs and Objectives an applied option took out of the plan, with a way to bring them back. */
export function DroppedGroup() {
  const t = useTranslations("plan.tasks.dropped");
  const { view, refresh, payload } = useReadyPlan();
  const { start } = useReschedule();
  const errorMessage = useApiErrorMessage();
  const [busy, setBusy] = useState<string | null>(null);
  if (view.dropped.length === 0) return null;
  const totals = droppedTotals(view.dropped);

  async function restore(item: DroppedItem) {
    setBusy(itemKey(item));
    const result =
      item.kind === "objective"
        ? await api.PATCH("/objectives/{objective_id}", {
            params: { path: { objective_id: item.objective.id } },
            body: { active: true },
          })
        : await api.PATCH("/key-results/{kr_id}", { params: { path: { kr_id: item.kr.id } }, body: { active: true } });
    setBusy(null);
    if (!result.response.ok) {
      toast.error(errorMessage(result.error));
      return;
    }
    await refresh();
    const quarterId = payload.summary?.id;
    const schedule = quarterId
      ? (await api.GET("/quarters/{quarter_id}/schedule", { params: { path: { quarter_id: quarterId } } }).catch(() => null))?.data
      : null;
    if (schedule?.stale) toast.success(t("restored"), { action: { label: t("reschedule"), onClick: start } });
    else toast.success(t("restoredFresh"));
  }

  return (
    <Collapsible className="rounded-xl border border-dashed border-border">
      <CollapsibleTrigger className="group flex w-full items-center gap-2 p-3 text-left text-sm font-medium text-muted-foreground outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring">
        <ChevronRightIcon className="size-4 shrink-0 transition-transform group-data-[state=open]:rotate-90" aria-hidden />
        {t("title", { krs: totals.krs, tasks: totals.tasks })}
      </CollapsibleTrigger>
      <CollapsibleContent>
        <ul className="flex flex-col divide-y divide-border border-t border-dashed border-border">
          {view.dropped.map((item) => (
            <li key={itemKey(item)} className="flex flex-wrap items-center gap-x-3 gap-y-2 p-3 text-sm">
              <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                <span className={cn("line-clamp-2 text-muted-foreground", item.kind === "objective" && "font-medium")}>
                  <span className="mr-1.5 font-mono text-xs">{item.code}</span>
                  {item.kind === "objective" ? item.objective.title : item.kr.text}
                </span>
                <span className="text-xs text-muted-foreground">
                  {item.kind === "objective"
                    ? t("objectiveMeta", { krs: item.krCount, tasks: item.taskCount })
                    : t("krMeta", { objective: item.objective.title, tasks: item.taskCount })}
                </span>
              </div>
              <Button
                size="sm"
                variant="outline"
                className="max-md:h-11"
                disabled={busy !== null}
                onClick={() => void restore(item)}
              >
                {busy === itemKey(item) ? <Spinner data-icon="inline-start" /> : <Undo2Icon data-icon="inline-start" />}
                {t("restore")}
              </Button>
            </li>
          ))}
        </ul>
      </CollapsibleContent>
    </Collapsible>
  );
}
