"use client";

import { InfoIcon } from "lucide-react";
import dynamic from "next/dynamic";
import { useTranslations } from "next-intl";
import { useMemo, useState } from "react";
import { cn } from "cn";

import { GuardedLink } from "@/components/app-shell/unsaved-changes";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { KeyResultMilestones, MilestoneCheckpoint } from "@/lib/api/types";
import { localToday } from "@/lib/plan/dates";
import { monthOf } from "@/lib/plan/month";
import { calendarBlocks, hours, type KrView, objectiveColor } from "@/lib/plan/plan-view";
import { fullPeriodCount, type Granularity, taskProgress, type WorkloadPeriod, workloadPeriods } from "@/lib/plan/workload";

import { FeasibilityBadge } from "./feasibility-panel";
import { useReadyPlan } from "./plan-data";
import { usePlanFormat } from "./use-plan-format";
import { useKrMilestones } from "./use-quarter-extras";
import type { WorkloadChartProps, WorkloadChartRow } from "./workload-chart";

const WorkloadChart = dynamic<WorkloadChartProps>(() => import("./workload-chart"), {
  ssr: false,
  loading: () => <Skeleton className="h-80 w-full" />,
});

export function WorkloadDashboard() {
  const t = useTranslations("plan.workload");
  const fmt = usePlanFormat();
  const { view, payload, feasibility, slug } = useReadyPlan();
  const [granularity, setGranularity] = useState<Granularity>("week");
  const schedule = payload.schedule;
  const blocks = useMemo(() => calendarBlocks(view), [view]);
  const periods = useMemo(
    () => workloadPeriods(schedule?.days ?? [], blocks, view.objectiveSlots, granularity),
    [schedule, blocks, view, granularity],
  );
  const weeks = useMemo(
    () => (granularity === "week" ? periods : workloadPeriods(schedule?.days ?? [], blocks, view.objectiveSlots, "week")),
    [granularity, periods, schedule, blocks, view],
  );
  const progress = taskProgress(view, localToday());

  if (!schedule || !feasibility) {
    return (
      <Alert>
        <InfoIcon />
        <AlertDescription>{t("empty")}</AlertDescription>
      </Alert>
    );
  }

  const periodLabel = (p: WorkloadPeriod) =>
    p.week !== null ? t("weekShort", { week: p.week }) : fmt.monthShort(p.start);
  const rows: WorkloadChartRow[] = periods.map((p) => ({
    label: `${periodLabel(p)}${p.hasHoliday ? "*" : ""}`,
    ...Object.fromEntries(view.objectives.map((o) => [`o${o.index}`, hours(p.byObjective[o.index])])),
    free: hours(Math.max(0, p.capacity - p.total)),
    late: 0,
    capacity: hours(p.capacity),
    percentLabel: p.percent === null ? "—" : `${p.percent}%`,
    tooltipTitle: `${periodLabel(p)} · ${fmt.dayRange(p.start, p.end)}${p.hasHoliday ? ` · ${t("holidayNote")}` : ""}`,
  }));
  if (feasibility.lateMinutes > 0) {
    rows.push({
      label: t("unscheduledShort"),
      free: 0,
      late: hours(feasibility.lateMinutes),
      capacity: 0,
      percentLabel: fmt.hours(feasibility.lateMinutes),
      tooltipTitle: t("unscheduled", { count: feasibility.lateTaskCount }),
    });
  }
  const fullWeeks = fullPeriodCount(weeks);
  const weeksWithCapacity = weeks.filter((w) => w.capacity > 0).length;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="font-heading text-lg font-semibold">{t("title")}</h2>
        <FeasibilityBadge status={feasibility.status} />
        {feasibility.stale && <span className="text-xs text-muted-foreground">{t("staleNote")}</span>}
        <span className="flex-1" />
        {feasibility.status === "red" && (
          <Button asChild size="sm" variant="outline">
            <GuardedLink href={`/q/${slug}/options`}>{t("seeOptions")}</GuardedLink>
          </Button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kpi
          label={t("kpiDemand")}
          value={`${fmt.hours(feasibility.demandMinutes)} / ${fmt.hours(feasibility.supplyMinutes)}`}
          note={t("kpiUsed", { percent: feasibility.usedPercent })}
        />
        <Kpi
          label={t("kpiFinish")}
          value={feasibility.finishDate ? fmt.date(feasibility.finishDate) : "—"}
          note={
            feasibility.lateTaskCount > 0
              ? t("kpiLate", { count: feasibility.lateTaskCount })
              : feasibility.bufferStart && feasibility.finishDate && feasibility.finishDate >= feasibility.bufferStart
                ? t("kpiInBuffer", { date: fmt.dayMonth(feasibility.bufferStart) })
                : feasibility.bufferStart
                  ? t("kpiBeforeBuffer", { date: fmt.dayMonth(feasibility.bufferStart) })
                  : null
          }
          tone={feasibility.lateTaskCount > 0 ? "red" : undefined}
        />
        <Kpi
          label={t("kpiFullWeeks")}
          value={t("kpiFullWeeksValue", { count: fullWeeks, total: weeksWithCapacity })}
          note={fullWeeks > 0 ? t("kpiFullWeeksNote") : t("kpiNoFullWeeks")}
        />
        <Kpi
          label={t("kpiProgress")}
          value={t("kpiProgressValue", { done: progress.doneTasks, total: progress.totalTasks })}
          note={
            progress.overdueMinutes > 0
              ? t("kpiBehind", { hours: fmt.hours(progress.overdueMinutes), done: fmt.hours(progress.doneMinutes) })
              : t("kpiOnTrack", { done: fmt.hours(progress.doneMinutes) })
          }
          tone={progress.overdueMinutes > 0 ? "yellow" : undefined}
        />
      </div>

      <Card>
        <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-3">
          <div className="flex flex-col gap-1">
            <CardTitle>{t("chartTitle")}</CardTitle>
            <CardDescription>{t("chartBody")}</CardDescription>
          </div>
          <ToggleGroup
            type="single"
            variant="outline"
            size="sm"
            value={granularity}
            onValueChange={(v) => v && setGranularity(v as Granularity)}
            aria-label={t("granularity")}
          >
            <ToggleGroupItem value="week">{t("byWeek")}</ToggleGroupItem>
            <ToggleGroupItem value="month">{t("byMonth")}</ToggleGroupItem>
          </ToggleGroup>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="hidden md:block" role="img" aria-label={t("chartLabel", { count: periods.length })}>
            <WorkloadChart
              rows={rows}
              objectives={view.objectives.map((o) => ({ index: o.index, code: `${o.code} · ${o.objective.title}` }))}
              labels={{ capacity: t("capacity"), free: t("free"), late: t("unscheduledShort"), hoursUnit: "h" }}
              formatHours={(h) => fmt.hours(h * 60)}
            />
          </div>
          <PeriodBars periods={periods} label={periodLabel} />
          <ChartLegend objectives={view.objectives.map((o) => ({ index: o.index, code: o.code, title: o.objective.title }))} />
          <PeriodTable periods={periods} label={periodLabel} objectives={view.objectives.map((o) => ({ index: o.index, code: o.code }))} />
        </CardContent>
      </Card>

      <MilestoneSection krs={view.objectives.flatMap((o) => o.krs.map((kr) => ({ kr, objectiveIndex: o.index })))} />
    </div>
  );
}

function Kpi({ label, value, note, tone }: { label: string; value: string; note: string | null; tone?: "red" | "yellow" }) {
  return (
    <Card size="sm">
      <CardContent className="flex flex-col gap-1">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className="font-heading text-xl font-semibold tabular-nums">{value}</span>
        {note && (
          <span
            className={cn(
              "text-xs",
              tone === "red" ? "text-destructive" : tone === "yellow" ? "text-warning" : "text-muted-foreground",
            )}
          >
            {tone === "red" ? "× " : tone === "yellow" ? "! " : ""}
            {note}
          </span>
        )}
      </CardContent>
    </Card>
  );
}

/** Phone layout, and a readable fallback of the chart: one bar per period. */
function PeriodBars({ periods, label }: { periods: WorkloadPeriod[]; label: (p: WorkloadPeriod) => string }) {
  const fmt = usePlanFormat();
  return (
    <ul className="flex flex-col gap-1.5 md:hidden">
      {periods.map((p) => {
        const over = p.total > p.capacity;
        return (
          <li key={p.key} className="grid grid-cols-[3.5rem_1fr_5.5rem] items-center gap-2 text-xs">
            <span className="font-medium">
              {label(p)}
              {p.hasHoliday && "*"}
            </span>
            <span className="flex h-3 overflow-hidden rounded-sm bg-muted" aria-hidden>
              {p.byObjective.map((m, i) =>
                m > 0 && p.capacity > 0 ? (
                  <span key={i} style={{ width: `${Math.min(100, (m / p.capacity) * 100)}%`, backgroundColor: objectiveColor(i) }} />
                ) : null,
              )}
            </span>
            <span className={cn("text-right tabular-nums", over && "font-medium text-destructive")}>
              {over && "! "}
              {fmt.hours(p.total)}/{fmt.hours(p.capacity)}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

function ChartLegend({ objectives }: { objectives: { index: number; code: string; title: string }[] }) {
  const t = useTranslations("plan.workload");
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-muted-foreground">
      {objectives.map((o) => (
        <li key={o.index} className="flex items-center gap-1.5">
          <span className="size-3 rounded-sm" style={{ backgroundColor: objectiveColor(o.index) }} aria-hidden />
          <span className="font-mono">{o.code}</span>
          <span className="max-w-48 truncate">{o.title}</span>
        </li>
      ))}
      <li className="flex items-center gap-1.5">
        <span className="size-3 rounded-sm border border-dashed border-muted-foreground" aria-hidden />
        {t("free")}
      </li>
      <li>{t("holidayLegend")}</li>
    </ul>
  );
}

function PeriodTable({
  periods,
  label,
  objectives,
}: {
  periods: WorkloadPeriod[];
  label: (p: WorkloadPeriod) => string;
  objectives: { index: number; code: string }[];
}) {
  const t = useTranslations("plan.workload");
  const fmt = usePlanFormat();
  return (
    <table className="sr-only">
      <caption>{t("chartTitle")}</caption>
      <thead>
        <tr>
          <th scope="col">{t("period")}</th>
          <th scope="col">{t("capacity")}</th>
          {objectives.map((o) => (
            <th key={o.index} scope="col">
              {o.code}
            </th>
          ))}
          <th scope="col">%</th>
        </tr>
      </thead>
      <tbody>
        {periods.map((p) => (
          <tr key={p.key}>
            <th scope="row">{label(p)}</th>
            <td>{fmt.hours(p.capacity)}</td>
            {objectives.map((o) => (
              <td key={o.index}>{fmt.hours(p.byObjective[o.index])}</td>
            ))}
            <td>{p.percent === null ? "—" : `${p.percent}%`}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

type KrRow = { kr: KrView; objectiveIndex: number };

function MilestoneSection({ krs }: { krs: KrRow[] }) {
  const t = useTranslations("plan.workload");
  const fmt = usePlanFormat();
  const [state, retry] = useKrMilestones();
  const [granularity, setGranularity] = useState<Granularity>("month");
  const byKr = useMemo(
    () => new Map((state.status === "ready" ? state.data : []).map((m) => [m.key_result_id, m])),
    [state],
  );
  const sample = state.status === "ready" ? state.data[0] : undefined;
  const checkpoints = (m: KeyResultMilestones | undefined) => (granularity === "month" ? m?.monthly : m?.weekly) ?? [];
  const columns = checkpoints(sample).map((c) => c.period_end);
  const thisMonth = monthOf(localToday());

  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-3">
        <div className="flex flex-col gap-1">
          <CardTitle>{t("milestonesTitle")}</CardTitle>
          <CardDescription>{t("milestonesMethod")}</CardDescription>
        </div>
        <ToggleGroup
          type="single"
          variant="outline"
          size="sm"
          value={granularity}
          onValueChange={(v) => v && setGranularity(v as Granularity)}
          aria-label={t("granularity")}
        >
          <ToggleGroupItem value="month">{t("byMonthShort")}</ToggleGroupItem>
          <ToggleGroupItem value="week">{t("byWeekShort")}</ToggleGroupItem>
        </ToggleGroup>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {state.status === "loading" && <Skeleton className="h-40 w-full" />}
        {state.status === "error" && (
          <Alert variant="destructive">
            <AlertDescription className="flex flex-wrap items-center gap-3 text-foreground">
              {t("milestonesError")}
              <Button size="sm" variant="outline" onClick={retry}>
                {t("retry")}
              </Button>
            </AlertDescription>
          </Alert>
        )}
        {state.status === "ready" && (
          <>
            <div className="hidden overflow-x-auto rounded-lg border border-border md:block">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead scope="col" className="min-w-56">
                      {t("colKr")}
                    </TableHead>
                    <TableHead scope="col" className="text-right">
                      {t("colBaseline")}
                    </TableHead>
                    {columns.map((end) => (
                      <TableHead key={end} scope="col" className="text-right whitespace-nowrap">
                        {t("colEnd", { period: granularity === "month" ? fmt.monthShort(end) : fmt.dayMonth(end) })}
                      </TableHead>
                    ))}
                    <TableHead scope="col" className="text-right">
                      {t("colTarget")}
                    </TableHead>
                    <TableHead scope="col" className="text-right">
                      {t("colExpected")}
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {krs.map(({ kr, objectiveIndex }) => {
                    const m = byKr.get(kr.kr.id);
                    return (
                      <TableRow key={kr.kr.id}>
                        <TableCell className="max-w-72 whitespace-normal">
                          <span className="flex items-start gap-2">
                            <span className="mt-1.5 size-2 shrink-0 rounded-full" style={{ backgroundColor: objectiveColor(objectiveIndex) }} aria-hidden />
                            <span className="font-mono text-xs whitespace-nowrap text-muted-foreground">{kr.code}</span>
                            <span className="line-clamp-2" title={kr.kr.text}>
                              {kr.kr.text}
                            </span>
                          </span>
                        </TableCell>
                        <TableCell className="text-right tabular-nums">{valueText(fmt, kr, kr.kr.baseline)}</TableCell>
                        {columns.map((end) => (
                          <TableCell key={end} className="text-right tabular-nums">
                            <CheckpointValue kr={kr} checkpoint={checkpoints(m).find((c) => c.period_end === end)} completion={m?.expected_completion_date} />
                          </TableCell>
                        ))}
                        <TableCell className="text-right font-medium tabular-nums">{valueText(fmt, kr, kr.kr.target)}</TableCell>
                        <TableCell className="text-right whitespace-nowrap tabular-nums">
                          {m?.expected_completion_date ? (
                            <>
                              {kr.kr.kind === "milestone" && "◆ "}
                              {fmt.dayMonth(m.expected_completion_date)}
                            </>
                          ) : (
                            <Badge variant="outline" className="font-normal">
                              {t("notPlanned")}
                            </Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
            <ul className="flex flex-col gap-2 md:hidden">
              {krs.map(({ kr, objectiveIndex }) => {
                const m = byKr.get(kr.kr.id);
                const current = m?.monthly.find((c) => monthOf(c.period_end) === thisMonth) ?? m?.monthly.at(-1);
                return (
                  <li
                    key={kr.kr.id}
                    className="flex flex-col gap-1 rounded-lg border border-l-4 border-border p-3 text-sm"
                    style={{ borderLeftColor: objectiveColor(objectiveIndex) }}
                  >
                    <span className="flex gap-2">
                      <span className="font-mono text-xs whitespace-nowrap text-muted-foreground">{kr.code}</span>
                      <span className="line-clamp-2 font-medium">{kr.kr.text}</span>
                    </span>
                    {current && (
                      <span className="text-xs text-muted-foreground">
                        {t("colEnd", { period: fmt.monthShort(current.period_end) })}:{" "}
                        <span className="font-medium text-foreground">
                          <CheckpointValue kr={kr} checkpoint={current} completion={m?.expected_completion_date} />
                        </span>{" "}
                        · {t("colTarget")} {valueText(fmt, kr, kr.kr.target)}
                      </span>
                    )}
                  </li>
                );
              })}
            </ul>
            <p className="text-xs text-muted-foreground">{t("milestonesNote")}</p>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function valueText(fmt: ReturnType<typeof usePlanFormat>, kr: KrView, value: number | null) {
  if (value === null || kr.kr.kind !== "numeric") return "—";
  return fmt.quantity(value, kr.kr.unit);
}

function CheckpointValue({
  kr,
  checkpoint,
  completion,
}: {
  kr: KrView;
  checkpoint: MilestoneCheckpoint | undefined;
  completion: string | null | undefined;
}) {
  const fmt = usePlanFormat();
  if (!checkpoint) return <>—</>;
  if (kr.kr.kind === "numeric" && checkpoint.expected_value !== null) return <>{valueText(fmt, kr, checkpoint.expected_value)}</>;
  if (kr.kr.kind === "milestone") {
    return <>{checkpoint.progress >= 1 && completion ? `◆ ${fmt.dayMonth(completion)}` : "—"}</>;
  }
  return <>{fmt.quantity(Math.round(checkpoint.progress * 100), "%")}</>;
}
