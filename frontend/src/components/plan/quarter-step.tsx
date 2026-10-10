"use client";

import { ArrowRightIcon, CircleAlertIcon, InfoIcon, TriangleAlertIcon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { cn } from "cn";

import { LoadError } from "@/components/settings/load-error";
import { WEEKDAYS } from "@/components/settings/calendar-model";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useLoad } from "@/hooks/use-load";
import { api } from "@/lib/api/client";
import type { CalendarSettings, QuarterSummary } from "@/lib/api/types";
import { localToday } from "@/lib/plan/dates";
import {
  type CalendarExceptions,
  calendarExceptions,
  capacityStats,
  defaultQuarter,
  findQuarter,
  parseQuarterSlug,
  QUARTER_NUMBERS,
  type QuarterNumber,
  type QuarterRef,
  quarterLabel,
  quarterSlug,
  quarterStatus,
  SHORT_QUARTER_DAYS,
  toRef,
  weekdayMinutes,
  yearOptions,
} from "@/lib/plan/quarter";

import { QuarterStatusBadge } from "./plan-bits";
import { usePlanFormat } from "./use-plan-format";

type Loaded = { calendar: CalendarSettings; quarters: QuarterSummary[]; exceptions: CalendarExceptions };

async function loadQuarterStep(): Promise<Loaded | undefined> {
  const [calendar, quarters, holidays, leave] = await Promise.all([
    api.GET("/settings/calendar"),
    api.GET("/quarters"),
    api.GET("/calendar/holidays"),
    api.GET("/calendar/leave-days"),
  ]);
  if (!calendar.data || !quarters.data) return undefined;
  return {
    calendar: calendar.data,
    quarters: quarters.data,
    exceptions: calendarExceptions(holidays.data ?? [], leave.data ?? []),
  };
}

export function QuarterStep({ initial }: { initial?: string }) {
  const [state, retry] = useLoad(loadQuarterStep);
  if (state.status === "error") return <LoadError onRetry={retry} />;
  if (state.status === "loading") {
    return (
      <div className="mx-auto flex max-w-2xl flex-col gap-4" aria-busy="true">
        <Skeleton className="h-9 w-3/4" />
        <Skeleton className="h-10 w-72" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }
  return <QuarterPicker data={state.data} initial={parseQuarterSlug(initial)} />;
}

function QuarterPicker({ data, initial }: { data: Loaded; initial: QuarterRef | null }) {
  const t = useTranslations("plan.quarter");
  const tDays = useTranslations("weekdaysShort");
  const fmt = usePlanFormat();
  const router = useRouter();
  const [today] = useState(() => localToday());
  const [picked, setPicked] = useState<QuarterRef | null>(initial);
  const [starts, setStarts] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [startError, setStartError] = useState(false);
  const ref = picked ?? defaultQuarter(today, data.calendar, data.exceptions);
  const existing = findQuarter(data.quarters, ref);
  // Tasks start on this day: the chosen plan start, but never before today.
  const chosenStart = starts[quarterSlug(ref)] ?? existing?.plan_start ?? "";
  const planFrom = chosenStart && chosenStart > today ? chosenStart : today;
  const stats = capacityStats(ref, data.calendar, planFrom, data.exceptions);
  const status = quarterStatus(ref, today);
  const hasPlan = (existing?.objective_count ?? 0) > 0;
  const hasTasks = (existing?.task_count ?? 0) > 0;
  const slug = quarterSlug(ref);
  const label = quarterLabel(ref);
  const ended = status.kind === "ended";
  const workingDayNames = WEEKDAYS.filter((d) => weekdayMinutes(data.calendar, d) > 0).map((d) => tDays(d));
  const weeklyMinutes = WEEKDAYS.reduce((sum, d) => sum + weekdayMinutes(data.calendar, d), 0);
  const others = data.quarters.filter((q) => !(q.year === ref.year && q.number === ref.number));

  async function savePlanStart(): Promise<boolean> {
    if (chosenStart === (existing?.plan_start ?? "")) return true;
    let id = existing?.id;
    if (!id) {
      const created = await api.POST("/quarters", { body: { year: ref.year, number: ref.number } });
      id = created.data?.id ?? findQuarter((await api.GET("/quarters")).data ?? [], ref)?.id;
    }
    if (!id) return false;
    const { data } = await api.PUT("/quarters/{quarter_id}/plan-start", {
      params: { path: { quarter_id: id } },
      body: { plan_start: chosenStart || null },
    });
    return Boolean(data);
  }

  async function continueToOkr() {
    setSaving(true);
    setStartError(false);
    try {
      if (!(await savePlanStart())) throw new Error("plan start");
      router.push(`/plan/new/okr?q=${slug}`);
    } catch {
      setStartError(true);
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="font-heading text-2xl font-semibold tracking-tight md:text-3xl">{t("title")}</h1>
        <p className="text-muted-foreground">{t("subtitle")}</p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <ToggleGroup
          type="single"
          variant="outline"
          spacing={0}
          value={String(ref.number)}
          onValueChange={(value) => value && setPicked({ ...ref, number: Number(value) as QuarterNumber })}
          aria-label={t("quarterLabel")}
          className="w-full sm:w-auto"
        >
          {QUARTER_NUMBERS.map((n) => (
            <ToggleGroupItem key={n} value={String(n)} className="h-10 flex-1 px-5 text-base sm:flex-none">
              Q{n}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
        <Select value={String(ref.year)} onValueChange={(value) => setPicked({ ...ref, year: Number(value) })}>
          <SelectTrigger className="h-10 w-28" aria-label={t("yearLabel")}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {yearOptions(today).map((year) => (
              <SelectItem key={year} value={String(year)}>
                {year}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{t("range")}</p>
              <p className="font-heading text-xl font-semibold" aria-live="polite">
                {fmt.date(stats.start)} – {fmt.date(stats.end)}
              </p>
            </div>
            <QuarterStatusBadge status={status} />
          </div>
          <dl className="grid grid-cols-2 gap-4 border-t border-border pt-4 sm:grid-cols-4">
            <Metric label={t("metrics.days")} value={String(stats.totalDays)} />
            <Metric label={t("metrics.workingDays")} value={String(stats.workingDays)} />
            <Metric label={t("metrics.hours")} value={fmt.hours(stats.supplyMinutes)} />
            <Metric
              label={stats.bufferStart ? t("metrics.bufferFrom", { date: fmt.dayMonth(stats.bufferStart) }) : t("metrics.buffer")}
              value={fmt.hours(stats.bufferMinutes)}
            />
          </dl>
          <p className="border-t border-border pt-3 text-sm text-muted-foreground">
            {t("basis", { weekly: fmt.hours(weeklyMinutes), days: workingDayNames.join(", ") || "—" })}{" "}
            <Link href="/settings/calendar" className="font-medium text-foreground underline underline-offset-4">
              {t("edit")}
            </Link>
          </p>
        </CardContent>
      </Card>

      {!ended && (
        <div className="flex flex-col gap-2">
          <label htmlFor="plan-start" className="text-sm font-medium">
            {t("planStart.label")}
          </label>
          <div className="flex flex-wrap items-center gap-2">
            <Input
              id="plan-start"
              type="date"
              className="w-44"
              min={maxIso(stats.start, today)}
              max={stats.end}
              value={chosenStart}
              onChange={(e) => {
                setStartError(false);
                setStarts((s) => ({ ...s, [slug]: e.target.value }));
              }}
              aria-describedby="plan-start-hint"
            />
            {chosenStart && (
              <Button type="button" variant="ghost" size="sm" onClick={() => setStarts((s) => ({ ...s, [slug]: "" }))}>
                {t("planStart.reset")}
              </Button>
            )}
          </div>
          <p id="plan-start-hint" className="text-sm text-muted-foreground">
            {chosenStart && chosenStart > today
              ? t("planStart.custom", { date: fmt.date(chosenStart) })
              : t("planStart.hint", { date: fmt.date(planFrom) })}
          </p>
          {startError && <p className="text-sm text-destructive">{t("planStart.error")}</p>}
        </div>
      )}

      {status.kind === "ongoing" && today > stats.start && (
        <Alert className="border-warning/40 bg-warning-muted text-warning">
          <TriangleAlertIcon />
          <AlertTitle>{t("started.title", { date: fmt.date(stats.start) })}</AlertTitle>
          <AlertDescription className="text-warning">
            {t("started.body", {
              today: fmt.date(today),
              days: stats.workingDays,
              hours: fmt.hours(stats.supplyMinutes),
            })}
          </AlertDescription>
        </Alert>
      )}
      {!ended && stats.workingDays < SHORT_QUARTER_DAYS && (
        <Alert className="border-warning/40 bg-warning-muted text-warning">
          <TriangleAlertIcon />
          <AlertDescription className="text-warning">{t("short", { min: SHORT_QUARTER_DAYS })}</AlertDescription>
        </Alert>
      )}
      {ended && (
        <Alert>
          <InfoIcon />
          <AlertDescription>{t("ended", { quarter: label })}</AlertDescription>
        </Alert>
      )}
      {existing && hasPlan && (
        <Alert>
          <CircleAlertIcon />
          <AlertTitle>{t("existing.title", { quarter: label })}</AlertTitle>
          <AlertDescription>
            {t("existing.body", {
              objectives: existing.objective_count,
              krs: existing.key_result_count,
              tasks: existing.task_count,
            })}
          </AlertDescription>
          {hasTasks && (
            <Button asChild size="sm" className="col-start-2 mt-2 w-fit">
              <Link href={`/q/${slug}/tasks`}>{t("existing.open")}</Link>
            </Button>
          )}
        </Alert>
      )}

      {others.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">{t("others")}</p>
          <div className="flex flex-wrap gap-2">
            {others.map((q) => (
              <button
                key={q.id}
                type="button"
                onClick={() => setPicked(toRef(q))}
                className={cn(
                  "rounded-full border border-border px-3 py-1 text-xs outline-none hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring",
                )}
              >
                {t("otherChip", { quarter: quarterLabel(toRef(q)), objectives: q.objective_count, tasks: q.task_count })}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-border bg-background/95 p-4 backdrop-blur md:static md:border-0 md:bg-transparent md:p-0">
        <div className="mx-auto flex max-w-2xl justify-end">
          <Button
            size="lg"
            variant={hasTasks ? "outline" : "default"}
            className="w-full md:w-auto"
            disabled={ended || saving}
            onClick={() => void continueToOkr()}
          >
            {hasTasks ? t("editQuarterOkr") : hasPlan ? t("continueEditing") : t("continue")}
            <ArrowRightIcon data-icon="inline-end" />
          </Button>
        </div>
      </div>
    </div>
  );
}

function maxIso(a: string, b: string) {
  return a > b ? a : b;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="order-2 text-xs text-muted-foreground uppercase">{label}</dt>
      <dd className="order-1 font-heading text-2xl font-semibold tabular-nums">{value}</dd>
    </div>
  );
}
