"use client";

import { createContext, type ReactNode, useCallback, useContext, useMemo, useState } from "react";

import { type LoadState, useLoad } from "@/hooks/use-load";
import { api } from "@/lib/api/client";
import type { LlmSettings, PlanRunDetail, QuarterDetail, QuarterSchedule, QuarterSummary } from "@/lib/api/types";
import { localToday, maxDate, minDate, startOfWeek } from "@/lib/plan/dates";
import {
  buildPlanView,
  type FeasibilitySummary,
  type PlanView,
  summarizeFeasibility,
} from "@/lib/plan/plan-view";
import { findQuarter, type QuarterRef, quarterRange, quarterSlug } from "@/lib/plan/quarter";
import { listQuarters } from "@/lib/plan/sync";

export type PlanPayload = {
  quarters: QuarterSummary[];
  summary: QuarterSummary | null;
  detail: QuarterDetail | null;
  schedule: QuarterSchedule | null;
  run: PlanRunDetail | null;
  settings: LlmSettings | null;
};

async function loadPlan(ref: QuarterRef): Promise<PlanPayload | undefined> {
  const [quarters, llm] = await Promise.all([listQuarters(api), api.GET("/settings/llm")]);
  const settings = llm.data ?? null;
  const summary = findQuarter(quarters, ref) ?? null;
  if (!summary) return { quarters, summary, detail: null, schedule: null, run: null, settings };
  const path = { params: { path: { quarter_id: summary.id } } };
  const [detail, schedule] = await Promise.all([
    api.GET("/quarters/{quarter_id}", path),
    api.GET("/quarters/{quarter_id}/schedule", path),
  ]);
  if (!detail.data) return undefined;
  if (!schedule.data && schedule.response.status !== 404) return undefined;
  const runId = schedule.data?.plan_run_id ?? summary.latest_plan_run_id;
  const run = runId ? (await api.GET("/plans/{job_id}", { params: { path: { job_id: runId } } })).data : undefined;
  return { quarters, summary, detail: detail.data, schedule: schedule.data ?? null, run: run ?? null, settings };
}

type PlanDataValue = {
  ref: QuarterRef;
  slug: string;
  state: LoadState<PlanPayload>;
  retry: () => void;
  /** Reloads quarter, tasks and schedule in the background after a change. */
  refresh: () => Promise<boolean>;
  view: PlanView | null;
  feasibility: FeasibilitySummary | null;
  /** Objective/KR groups the user collapsed; kept here so switching tabs keeps them. */
  collapsed: ReadonlySet<string>;
  setCollapsed: (next: ReadonlySet<string>) => void;
  selectedTask: number | null;
  selectTask: (taskId: number | null) => void;
  sheet: SheetState;
  editTask: (taskId: number) => void;
  newTask: (krId: number) => void;
  closeSheet: () => void;
  week: string;
  setWeek: (monday: string) => void;
};

/** The task sheet shows a task, edits it, or drafts a new task in a KR. */
export type SheetState =
  | { mode: "closed" }
  | { mode: "view"; taskId: number }
  | { mode: "edit"; taskId: number }
  | { mode: "new"; krId: number };

const PlanDataContext = createContext<PlanDataValue | null>(null);

export function initialWeek(ref: QuarterRef, schedule: QuarterSchedule | null, today = localToday()) {
  const range = quarterRange(ref);
  const start = schedule?.window_start ?? range.start;
  const end = schedule?.window_end ?? range.end;
  return startOfWeek(minDate(maxDate(today, start), end));
}

export function PlanDataProvider({ quarter, children }: { quarter: QuarterRef; children: ReactNode }) {
  const { year, number } = quarter;
  const fetcher = useCallback(() => loadPlan({ year, number }), [year, number]);
  const [state, retry, refresh] = useLoad(fetcher);
  const [collapsed, setCollapsed] = useState<ReadonlySet<string>>(() => new Set());
  const [sheet, setSheet] = useState<SheetState>({ mode: "closed" });
  const [chosenWeek, setWeek] = useState<string | null>(null);
  const selectedTask = sheet.mode === "view" || sheet.mode === "edit" ? sheet.taskId : null;
  const selectTask = useCallback(
    (taskId: number | null) => setSheet(taskId === null ? { mode: "closed" } : { mode: "view", taskId }),
    [],
  );
  const editTask = useCallback((taskId: number) => setSheet({ mode: "edit", taskId }), []);
  const newTask = useCallback((krId: number) => setSheet({ mode: "new", krId }), []);
  const closeSheet = useCallback(() => setSheet({ mode: "closed" }), []);

  const payload = state.status === "ready" ? state.data : null;
  const view = useMemo(
    () => (payload?.detail ? buildPlanView(payload.detail, payload.schedule) : null),
    [payload],
  );
  const feasibility = useMemo(
    () => (payload?.schedule && view ? summarizeFeasibility(payload.schedule, view) : null),
    [payload, view],
  );
  const week = chosenWeek ?? initialWeek({ year, number }, payload?.schedule ?? null);

  const value = useMemo<PlanDataValue>(
    () => ({
      ref: { year, number },
      slug: quarterSlug({ year, number }),
      state,
      retry,
      refresh,
      view,
      feasibility,
      collapsed,
      setCollapsed,
      selectedTask,
      selectTask,
      sheet,
      editTask,
      newTask,
      closeSheet,
      week,
      setWeek,
    }),
    [
      year,
      number,
      state,
      retry,
      refresh,
      view,
      feasibility,
      collapsed,
      selectedTask,
      selectTask,
      sheet,
      editTask,
      newTask,
      closeSheet,
      week,
    ],
  );
  return <PlanDataContext value={value}>{children}</PlanDataContext>;
}

export function usePlanData() {
  const value = useContext(PlanDataContext);
  if (!value) throw new Error("usePlanData must be used inside PlanDataProvider");
  return value;
}

/** Data for pages that only render once the plan has tasks (the shell handles the other states). */
export function useReadyPlan() {
  const data = usePlanData();
  if (data.state.status !== "ready" || !data.view) throw new Error("useReadyPlan needs a loaded plan");
  return { ...data, payload: data.state.data, view: data.view };
}
