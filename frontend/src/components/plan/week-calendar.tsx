"use client";

import {
  CalendarArrowUpIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CircleXIcon,
  GripVerticalIcon,
  InfoIcon,
  PinIcon,
} from "lucide-react";
import dynamic from "next/dynamic";
import { useSearchParams } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { type TouchEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { cn } from "cn";

import { GuardedLink } from "@/components/app-shell/unsaved-changes";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useMediaQuery } from "@/hooks/use-media-query";
import type { HolidayOut, ScheduleDay } from "@/lib/api/types";
import { addDays, eachDay, isoWeek, localToday, maxDate, minDate, startOfWeek } from "@/lib/plan/dates";
import { criteriaLines } from "@/lib/plan/criteria";
import { clampMonth, monthEnd, monthGrid, monthOf, monthsOf, monthStart } from "@/lib/plan/month";
import {
  blocksByDate,
  type CalendarBlock,
  calendarBlocks,
  daysByDate,
  dayLoads,
  type KrMarker,
  krMarkers,
  objectiveColor,
  type TaskView,
} from "@/lib/plan/plan-view";
import { quarterRange } from "@/lib/plan/quarter";

import { initialWeek, useReadyPlan } from "./plan-data";
import type { PlanFullCalendarProps } from "./plan-fullcalendar";
import { useTaskDialogs } from "./task-dialogs";
import { usePlanFormat } from "./use-plan-format";
import { useHolidays, useKrMilestones } from "./use-quarter-extras";
import { useTaskActions } from "./use-task-actions";

const SWIPE_PX = 50;
const TRAY_ID = "okr-unscheduled-tray";

function CalendarSkeleton() {
  return (
    <div className="grid grid-cols-7 gap-2" aria-busy="true">
      {Array.from({ length: 7 }, (_, i) => (
        <Skeleton key={i} className={cn("h-72", i >= 5 && "opacity-50")} />
      ))}
    </div>
  );
}

const PlanFullCalendar = dynamic<PlanFullCalendarProps>(() => import("./plan-fullcalendar"), {
  ssr: false,
  loading: CalendarSkeleton,
});

type Mode = "week" | "month";

function useCalendarData() {
  const plan = useReadyPlan();
  const { payload, view, ref, week } = plan;
  const locale = useLocale();
  const schedule = payload.schedule;
  const blocks = useMemo(() => calendarBlocks(view), [view]);
  const loads = useMemo(() => dayLoads(blocks), [blocks]);
  const byDate = useMemo(() => blocksByDate(blocks), [blocks]);
  const days = useMemo(() => daysByDate(schedule?.days ?? []), [schedule]);
  const [milestones] = useKrMilestones();
  const markers = useMemo(
    () => (milestones.status === "ready" ? krMarkers(view, milestones.data) : []),
    [milestones, view],
  );
  const markersByDate = useMemo(() => {
    const map = new Map<string, KrMarker[]>();
    for (const m of markers) map.set(m.date, [...(map.get(m.date) ?? []), m]);
    return map;
  }, [markers]);
  const [holidayState] = useHolidays([ref.year]);
  const holidays = holidayState.status === "ready" ? holidayState.data : new Map<string, HolidayOut>();
  const holidayName = (date: string) => {
    const h = holidays.get(date);
    if (!h || h.kind === "makeup_day") return null;
    return locale === "en" ? h.name_en || h.name_vi : h.name_vi;
  };
  const range = quarterRange(ref);
  const weekDays = eachDay(week, addDays(week, 6));
  const earliest = maxDate(range.start, localToday());
  const canDrop = (date: string) => {
    const day = days.get(date);
    return date >= earliest && date <= range.end && day !== undefined && !day.off_reason && day.capacity_minutes > 0;
  };
  return {
    ...plan,
    schedule,
    blocks,
    loads,
    byDate,
    days,
    markers,
    markersByDate,
    holidayName,
    weekDays,
    range,
    canDrop,
    firstWeek: startOfWeek(range.start),
    lastWeek: startOfWeek(range.end),
  };
}

type CalendarData = ReturnType<typeof useCalendarData>;

function useMoveHandler(data: CalendarData) {
  const actions = useTaskActions();
  const { view, loads, days } = data;
  return useCallback(
    async (taskId: number, date: string) => {
      const task = view.tasks.get(taskId);
      if (!task || task.done) return false;
      if (task.start === date) return true;
      const capacity = days.get(date)?.capacity_minutes ?? 0;
      const own = task.days.filter((d) => d.date === date).reduce((s, d) => s + d.minutes, 0);
      const after = (loads.get(date) ?? 0) - own + Math.min(task.task.estimate_minutes, capacity);
      return actions.moveTo(task, date, Math.max(0, after - capacity));
    },
    [actions, view, loads, days],
  );
}

export function WeekSummaryCard() {
  const t = useTranslations("plan.calendar");
  const fmt = usePlanFormat();
  const { weekDays, byDate, loads, days } = useCalendarData();
  const scheduled = weekDays.reduce((sum, d) => sum + (loads.get(d) ?? 0), 0);
  const capacity = weekDays.reduce((sum, d) => sum + (days.get(d)?.capacity_minutes ?? 0), 0);
  const tasks = new Set(weekDays.flatMap((d) => byDate.get(d) ?? []).map((b) => b.view.task.id)).size;
  return (
    <section className="flex flex-col gap-2 rounded-xl border border-border p-4 text-sm">
      <h2 className="font-heading font-semibold">{t("thisWeekCard", { week: isoWeek(weekDays[0]) })}</h2>
      <dl className="grid grid-cols-3 gap-2">
        <div>
          <dt className="text-xs text-muted-foreground">{t("scheduled")}</dt>
          <dd className="font-medium tabular-nums">{fmt.hours(scheduled)}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">{t("capacity")}</dt>
          <dd className="font-medium tabular-nums">{fmt.hours(capacity)}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">{t("taskCount")}</dt>
          <dd className="font-medium tabular-nums">{tasks}</dd>
        </div>
      </dl>
    </section>
  );
}

export function PlanCalendar() {
  const t = useTranslations("plan.calendar");
  const fmt = usePlanFormat();
  const data = useCalendarData();
  const params = useSearchParams();
  const { schedule, week, setWeek, ref, range, feasibility, slug, view } = data;
  const months = monthsOf(range.start, range.end);
  const mode: Mode = params.get("view") === "month" ? "month" : "week";
  const month = clampMonth(params.get("m") ?? monthOf(maxDate(week, range.start)), months);
  const [dayOpen, setDayOpen] = useState<string | null>(null);

  const setUrl = useCallback(
    (next: { view: Mode; m?: string }) => {
      const search = new URLSearchParams(params.toString());
      if (next.view === "month") {
        search.set("view", "month");
        search.set("m", next.m ?? month);
      } else {
        search.delete("view");
        search.delete("m");
      }
      const query = search.toString();
      window.history.replaceState(null, "", query ? `?${query}` : window.location.pathname);
    },
    [params, month],
  );

  function switchMode(next: Mode) {
    if (next === mode) return;
    if (next === "month") {
      setUrl({ view: "month", m: monthOf(maxDate(week, range.start)) });
    } else {
      const today = localToday();
      const inMonth = monthOf(today) === month ? today : monthStart(month);
      setWeek(minDate(maxDate(startOfWeek(inMonth), data.firstWeek), data.lastWeek));
      setUrl({ view: "week" });
    }
  }

  function openWeekOf(date: string) {
    setDayOpen(null);
    setWeek(minDate(maxDate(startOfWeek(date), data.firstWeek), data.lastWeek));
    setUrl({ view: "week" });
  }

  if (!schedule) {
    return (
      <Alert>
        <InfoIcon />
        <AlertDescription>{t("noSchedule")}</AlertDescription>
      </Alert>
    );
  }

  const pending = [...view.tasks.values()].filter((task) => (task.late || task.unplaced) && !task.done);

  return (
    <div className="flex flex-col gap-4">
      {feasibility && feasibility.lateTaskCount > 0 && (
        <Alert variant="destructive">
          <CircleXIcon />
          <AlertDescription className="flex flex-wrap items-center gap-x-3 gap-y-2 [&_a]:no-underline">
            <span>
              {t("lateBanner", {
                count: feasibility.lateTaskCount,
                hours: fmt.hours(feasibility.lateMinutes),
                date: fmt.date(feasibility.windowEnd),
              })}
            </span>
            <Button asChild size="sm" variant="outline">
              <GuardedLink href={`/q/${slug}/options`}>{t("seeOptions")}</GuardedLink>
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <ToggleGroup
        type="single"
        variant="outline"
        size="sm"
        value={mode}
        onValueChange={(v) => v && switchMode(v as Mode)}
        aria-label={t("viewLabel")}
        className="w-fit"
      >
        <ToggleGroupItem value="week">{t("viewWeek")}</ToggleGroupItem>
        <ToggleGroupItem value="month">{t("viewMonth")}</ToggleGroupItem>
      </ToggleGroup>

      {pending.length > 0 && <UnscheduledTray tasks={pending} />}

      {mode === "week" ? (
        <WeekView data={data} />
      ) : (
        <MonthView
          data={data}
          month={month}
          months={months}
          onMonth={(m) => setUrl({ view: "month", m })}
          onOpenDay={setDayOpen}
          quarterLabel={`Q${ref.number}/${ref.year}`}
        />
      )}

      <Legend objectives={view.objectives.map((o) => ({ index: o.index, title: o.objective.title }))} />
      <DayDialog data={data} date={dayOpen} onClose={() => setDayOpen(null)} onWeek={openWeekOf} />
    </div>
  );
}

function WeekView({ data }: { data: CalendarData }) {
  const t = useTranslations("plan.calendar");
  const fmt = usePlanFormat();
  const { week, setWeek, firstWeek, lastWeek, weekDays, days, byDate, blocks, markers, loads, selectTask, selectedTask, ref, schedule } =
    data;
  const desktop = useMediaQuery("(min-width: 768px)");
  const onMove = useMoveHandler(data);

  const canPrev = week > firstWeek;
  const canNext = week < lastWeek;
  const goWeek = (target: string) => setWeek(minDate(maxDate(startOfWeek(target), firstWeek), lastWeek));

  const shortcuts = useRef({ canPrev, canNext, week, goWeek, open: selectedTask !== null });
  useEffect(() => {
    shortcuts.current = { canPrev, canNext, week, goWeek, open: selectedTask !== null };
  });
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      const s = shortcuts.current;
      const target = event.target as HTMLElement | null;
      if (s.open || event.altKey || event.ctrlKey || event.metaKey) return;
      if (target?.closest("input, textarea, select, [contenteditable], [role=listbox], [role=menu], [role=dialog], [role=radiogroup], [role=group]")) return;
      if (event.key === "ArrowLeft" && s.canPrev) s.goWeek(addDays(s.week, -7));
      if (event.key === "ArrowRight" && s.canNext) s.goWeek(addDays(s.week, 7));
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const weekBlocks = weekDays.flatMap((d) => byDate.get(d) ?? []);
  const starts = blocks.map((b) => b.date);
  const firstDate = starts.length ? starts.reduce((a, b) => (a < b ? a : b)) : null;
  const lastDate = starts.length ? starts.reduce((a, b) => (a > b ? a : b)) : null;

  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center">
          <Button variant="outline" size="icon-sm" className="max-md:size-10" onClick={() => goWeek(addDays(week, -7))} disabled={!canPrev} aria-label={t("prevWeek")}>
            <ChevronLeftIcon />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => goWeek(initialWeek(ref, schedule, localToday()))}>
            {t("thisWeek")}
          </Button>
          <Button variant="outline" size="icon-sm" className="max-md:size-10" onClick={() => goWeek(addDays(week, 7))} disabled={!canNext} aria-label={t("nextWeek")}>
            <ChevronRightIcon />
          </Button>
        </div>
        <h2 className="font-heading font-semibold" aria-live="polite">
          {t("weekTitle", { week: isoWeek(week), from: fmt.dayMonth(week), to: fmt.date(addDays(week, 6)) })}
        </h2>
        <span className="hidden text-xs text-muted-foreground lg:inline">{t("keyboardHint")}</span>
      </div>

      {weekBlocks.length === 0 && (
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-dashed border-border p-4 text-sm">
          <span>
            {t("emptyWeek", { week: isoWeek(week) })}{" "}
            {lastDate && lastDate < week && t("lastTaskEnds", { date: fmt.date(lastDate) })}
            {firstDate && firstDate > addDays(week, 6) && t("firstTaskStarts", { date: fmt.date(firstDate) })}
          </span>
          {lastDate && lastDate < week && (
            <Button size="sm" variant="outline" onClick={() => goWeek(lastDate)}>
              {t("goLast")}
            </Button>
          )}
          {firstDate && firstDate > addDays(week, 6) && (
            <Button size="sm" variant="outline" onClick={() => goWeek(firstDate)}>
              {t("goFirst")}
            </Button>
          )}
        </div>
      )}

      {desktop ? (
        <PlanFullCalendar
          mode="week"
          date={week}
          blocks={blocks}
          markers={markers}
          days={days}
          renderHeader={(date) => <DayHeader date={date} day={days.get(date)} load={loads.get(date) ?? 0} />}
          renderBlock={(block) => <TaskBlock block={block} onSelect={selectTask} />}
          renderMarker={(marker) => <MarkerChip marker={marker} />}
          renderCell={(date) => <WeekCell date={date} data={data} />}
          canDrop={data.canDrop}
          onMove={onMove}
          trayId={TRAY_ID}
        />
      ) : (
        <MobileWeek key={week} data={data} goWeek={goWeek} />
      )}
    </>
  );
}

function MonthView({
  data,
  month,
  months,
  onMonth,
  onOpenDay,
  quarterLabel,
}: {
  data: CalendarData;
  month: string;
  months: string[];
  onMonth: (month: string) => void;
  onOpenDay: (date: string) => void;
  quarterLabel: string;
}) {
  const t = useTranslations("plan.calendar");
  const fmt = usePlanFormat();
  const desktop = useMediaQuery("(min-width: 768px)");
  const onMove = useMoveHandler(data);
  const { blocks, markers, days, selectTask } = data;
  const index = months.indexOf(month);
  const first = monthStart(month);
  const monthDays = eachDay(first, monthEnd(month));
  const working = monthDays.filter((d) => (days.get(d)?.capacity_minutes ?? 0) > 0);
  const load = monthDays.reduce((s, d) => s + (data.loads.get(d) ?? 0), 0);
  const capacity = monthDays.reduce((s, d) => s + (days.get(d)?.capacity_minutes ?? 0), 0);

  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1">
          <Button variant="outline" size="icon-sm" className="max-md:size-10" onClick={() => onMonth(months[index - 1])} disabled={index <= 0} aria-label={t("prevMonth")}>
            <ChevronLeftIcon />
          </Button>
          <Button variant="outline" size="icon-sm" className="max-md:size-10" onClick={() => onMonth(months[index + 1])} disabled={index >= months.length - 1} aria-label={t("nextMonth")}>
            <ChevronRightIcon />
          </Button>
        </div>
        <h2 className="font-heading font-semibold capitalize" aria-live="polite">
          {fmt.monthYear(first)}
        </h2>
        <span className="text-sm text-muted-foreground">
          {t("monthSummary", { days: working.length, load: fmt.hours(load), capacity: fmt.hours(capacity), quarter: quarterLabel })}
        </span>
      </div>
      {desktop ? (
        <PlanFullCalendar
          mode="month"
          date={first}
          blocks={blocks}
          markers={markers}
          days={days}
          renderHeader={(date) => <span className="block py-1 text-xs font-medium text-muted-foreground">{fmt.weekday(date)}</span>}
          renderBlock={(block) => <MonthChip block={block} onSelect={selectTask} />}
          renderMarker={(marker) => <MarkerChip marker={marker} compact />}
          renderCell={(date, inMonth) => <MonthCell date={date} inMonth={inMonth} data={data} onOpen={onOpenDay} />}
          renderMore={(count) => <span className="px-1 text-xs font-medium">{t("more", { count })}</span>}
          onMore={onOpenDay}
          canDrop={data.canDrop}
          onMove={onMove}
          trayId={TRAY_ID}
        />
      ) : (
        <MobileMonth key={month} data={data} month={month} />
      )}
    </>
  );
}

function LoadBar({ load, capacity }: { load: number; capacity: number }) {
  const fill = capacity > 0 ? Math.min(load / capacity, 1) * 100 : 0;
  return (
    <span className="block h-1 overflow-hidden rounded-full bg-muted" aria-hidden>
      <span className={cn("block h-full rounded-full", load > capacity ? "bg-destructive" : "bg-foreground/70")} style={{ width: `${fill}%` }} />
    </span>
  );
}

function DayHeader({ date, day, load }: { date: string; day: ScheduleDay | undefined; load: number }) {
  const t = useTranslations("plan.calendar");
  const fmt = usePlanFormat();
  const capacity = day?.capacity_minutes ?? 0;
  return (
    <div className={cn("flex flex-col items-stretch gap-1 px-1 py-1.5 text-left", (!day || day.off_reason) && "opacity-60")}>
      <span className="text-sm font-semibold">
        {fmt.weekday(date)} {fmt.dayOfMonth(date)}
      </span>
      {day && !day.off_reason ? (
        <>
          <span className={cn("text-xs font-normal tabular-nums", load > capacity ? "font-medium text-destructive" : "text-muted-foreground")}>
            {load > capacity && "! "}
            {t("load", { scheduled: fmt.hours(load), capacity: fmt.hours(capacity) })}
          </span>
          <LoadBar load={load} capacity={capacity} />
        </>
      ) : (
        <span className="text-xs font-normal text-muted-foreground">{day?.off_reason ? t(`off.${day.off_reason}`) : "—"}</span>
      )}
    </div>
  );
}

function WeekCell({ date, data }: { date: string; data: CalendarData }) {
  const t = useTranslations("plan.calendar");
  const day = data.days.get(date);
  if (!day?.off_reason) return <span />;
  const name = data.holidayName(date);
  return (
    <span className="m-1.5 block w-fit rounded-sm bg-background/90 px-1 text-xs text-muted-foreground">
      {name ?? `${t("offShort")}${day.off_reason === "holiday" ? ` · ${t("off.holiday")}` : ""}`}
    </span>
  );
}

function MonthCell({
  date,
  inMonth,
  data,
  onOpen,
}: {
  date: string;
  inMonth: boolean;
  data: CalendarData;
  onOpen: (date: string) => void;
}) {
  const t = useTranslations("plan.calendar");
  const fmt = usePlanFormat();
  const day = data.days.get(date);
  const load = data.loads.get(date) ?? 0;
  const capacity = day?.capacity_minutes ?? 0;
  const today = date === localToday();
  const name = day?.off_reason ? (data.holidayName(date) ?? t(`off.${day.off_reason}`)) : null;
  return (
    <div className={cn("flex w-full flex-col gap-1 p-1 text-left", !inMonth && "opacity-40")}>
      <div className="flex items-center justify-between gap-1">
        <button
          type="button"
          onClick={() => onOpen(date)}
          aria-label={t("openDay", { date: fmt.date(date) })}
          className={cn(
            "flex size-6 items-center justify-center rounded-full text-xs font-semibold outline-none hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring",
            today && "bg-foreground text-background hover:bg-foreground/90",
          )}
        >
          {fmt.dayOfMonth(date)}
        </button>
        {day && !day.off_reason && (
          <span className={cn("text-[11px] tabular-nums", load > capacity ? "font-medium text-destructive" : "text-muted-foreground")}>
            {load > capacity && "! "}
            {fmt.hours(load)}/{fmt.hours(capacity)}
          </span>
        )}
      </div>
      {day && !day.off_reason && <LoadBar load={load} capacity={capacity} />}
      {name && day?.off_reason !== "weekend" && (
        <span className="line-clamp-2 w-fit rounded-sm bg-background/90 px-1 text-[11px] text-muted-foreground">
          {name} · {fmt.hours(0)}
        </span>
      )}
    </div>
  );
}

function blockStyle(block: CalendarBlock) {
  const color = objectiveColor(block.view.objectiveIndex);
  return {
    borderLeftColor: color,
    backgroundColor: `color-mix(in oklab, ${color} ${block.view.done ? 6 : 14}%, var(--background))`,
  };
}

function TaskBlock({ block, onSelect }: { block: CalendarBlock; onSelect: (taskId: number) => void }) {
  const t = useTranslations("plan.calendar");
  const fmt = usePlanFormat();
  return (
    <button
      type="button"
      onClick={() => onSelect(block.view.task.id)}
      className={cn(
        "flex w-full flex-col gap-0.5 rounded-md border-l-[3px] px-2 py-1.5 text-left text-xs whitespace-normal text-foreground outline-none hover:brightness-95 focus-visible:ring-2 focus-visible:ring-ring",
        !block.view.done && "cursor-grab active:cursor-grabbing",
      )}
      style={{ ...blockStyle(block), minHeight: `${Math.max(2.5, (block.minutes / 60) * 1.1)}rem` }}
    >
      <span className={cn("line-clamp-3 font-medium", block.view.done && "text-muted-foreground line-through")}>
        {block.view.pinned && !block.view.done && (
          <PinIcon className="mr-1 inline size-3 align-[-1px]" role="img" aria-label={t("pinned")} />
        )}
        {block.view.task.title}
        {block.parts > 1 && ` (${block.part}/${block.parts})`}
      </span>
      <span className="text-muted-foreground">
        O{block.view.objectiveIndex + 1} · {block.view.krCode} · {fmt.hours(block.minutes)}
      </span>
      {block.view.scheduled?.uses_buffer && <span className="sr-only">{t("buffer")}</span>}
    </button>
  );
}

function MonthChip({ block, onSelect }: { block: CalendarBlock; onSelect: (taskId: number) => void }) {
  const fmt = usePlanFormat();
  return (
    <button
      type="button"
      onClick={() => onSelect(block.view.task.id)}
      title={`${block.view.code} · ${block.view.task.title} · ${fmt.hours(block.minutes)}`}
      className={cn(
        "block w-full truncate rounded-sm border-l-[3px] px-1.5 py-0.5 text-left text-[11px] text-foreground outline-none hover:brightness-95 focus-visible:ring-2 focus-visible:ring-ring",
        block.view.done && "text-muted-foreground line-through",
        !block.view.done && "cursor-grab active:cursor-grabbing",
      )}
      style={blockStyle(block)}
    >
      {block.view.task.title}
    </button>
  );
}

function MarkerChip({ marker, compact = false }: { marker: KrMarker; compact?: boolean }) {
  const t = useTranslations("plan.calendar");
  return (
    <span
      title={marker.text}
      className={cn(
        "block truncate rounded-sm border border-dashed px-1.5 py-0.5 text-[11px] font-medium text-foreground",
        !compact && "text-xs",
      )}
      style={{ borderColor: objectiveColor(marker.objectiveIndex) }}
    >
      {t("marker", { kr: marker.krCode })}
    </span>
  );
}

function UnscheduledTray({ tasks }: { tasks: TaskView[] }) {
  const t = useTranslations("plan.calendar");
  const fmt = usePlanFormat();
  const { selectTask } = useReadyPlan();
  const dialogs = useTaskDialogs();
  const minutes = tasks.reduce((s, task) => s + task.task.estimate_minutes, 0);
  return (
    <section className="flex flex-col gap-2 rounded-xl border border-dashed border-border p-3" aria-labelledby="tray-title">
      <h3 id="tray-title" className="text-sm font-semibold">
        {t("trayTitle", { count: tasks.length, hours: fmt.hours(minutes) })}
        <span className="ml-2 hidden font-normal text-muted-foreground md:inline">{t("trayHint")}</span>
      </h3>
      <ul id={TRAY_ID} className="flex flex-wrap gap-2">
        {tasks.map((task) => (
          <li
            key={task.task.id}
            data-drag-task={task.task.id}
            data-drag-title={task.task.title}
            className="flex max-w-full items-center gap-1 rounded-md border border-l-[3px] border-border bg-background py-0.5 pr-0.5 pl-1 text-xs"
            style={{ borderLeftColor: objectiveColor(task.objectiveIndex) }}
          >
            <GripVerticalIcon className="hidden size-3.5 shrink-0 cursor-grab text-muted-foreground md:block" aria-hidden />
            <button
              type="button"
              onClick={() => selectTask(task.task.id)}
              className="max-w-56 truncate rounded-sm text-left outline-none focus-visible:ring-2 focus-visible:ring-ring"
              title={task.task.title}
            >
              <span className="font-mono text-muted-foreground">{task.code}</span> {task.task.title} · {fmt.hours(task.task.estimate_minutes)}
            </button>
            <Button
              variant="ghost"
              size="icon-xs"
              className="max-md:size-9"
              onClick={() => dialogs.askMove(task)}
              aria-label={t("trayMove", { code: task.code })}
            >
              <CalendarArrowUpIcon />
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
}

function DayAgenda({ date, data, onSelect }: { date: string; data: CalendarData; onSelect: (taskId: number) => void }) {
  const t = useTranslations("plan.calendar");
  const fmt = usePlanFormat();
  const day = data.days.get(date);
  const blocks = data.byDate.get(date) ?? [];
  const markers = data.markersByDate.get(date) ?? [];
  const holiday = day?.off_reason ? data.holidayName(date) : null;
  return (
    <div className="flex flex-col gap-2">
      {markers.map((m) => (
        <MarkerChip key={m.krId} marker={m} />
      ))}
      {day?.off_reason ? (
        <p className="rounded-lg bg-muted p-4 text-sm text-muted-foreground">
          {holiday ?? t(`off.${day.off_reason}`)} · {fmt.hours(0)}
        </p>
      ) : blocks.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">{t("emptyDay")}</p>
      ) : (
        blocks.map((block) => (
          <button
            key={block.id}
            type="button"
            onClick={() => onSelect(block.view.task.id)}
            className="flex flex-col gap-1 rounded-lg border border-border border-l-4 p-3 text-left text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            style={{ borderLeftColor: objectiveColor(block.view.objectiveIndex) }}
          >
            <span className={cn("font-medium", block.view.done && "text-muted-foreground line-through")}>
              {block.view.task.title}
              {block.parts > 1 && ` (${block.part}/${block.parts})`}
            </span>
            <span className="text-xs text-muted-foreground">
              O{block.view.objectiveIndex + 1} · {block.view.krCode} · {fmt.hours(block.minutes)}
            </span>
            {criteriaLines(block.view.task.done_criteria)[0] && (
              <span className="line-clamp-2 text-xs text-muted-foreground">✓ {criteriaLines(block.view.task.done_criteria)[0]}</span>
            )}
          </button>
        ))
      )}
    </div>
  );
}

function DayDialog({
  data,
  date,
  onClose,
  onWeek,
}: {
  data: CalendarData;
  date: string | null;
  onClose: () => void;
  onWeek: (date: string) => void;
}) {
  const t = useTranslations("plan.calendar");
  const fmt = usePlanFormat();
  const day = date ? data.days.get(date) : undefined;
  const load = date ? (data.loads.get(date) ?? 0) : 0;
  return (
    <Dialog open={date !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent closeLabel={t("close")} className="sm:max-w-md">
        {date && (
          <>
            <DialogHeader>
              <DialogTitle className="capitalize">
                {fmt.weekday(date)} {fmt.date(date)}
              </DialogTitle>
              <DialogDescription>
                {day && !day.off_reason
                  ? t("load", { scheduled: fmt.hours(load), capacity: fmt.hours(day.capacity_minutes) })
                  : t("offShort")}
              </DialogDescription>
            </DialogHeader>
            <DayAgenda
              date={date}
              data={data}
              onSelect={(id) => {
                onClose();
                data.selectTask(id);
              }}
            />
            <DialogFooter>
              <Button variant="outline" onClick={() => onWeek(date)}>
                {t("seeWeek", { week: isoWeek(date) })}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

function MobileWeek({ data, goWeek }: { data: CalendarData; goWeek: (target: string) => void }) {
  const t = useTranslations("plan.calendar");
  const fmt = usePlanFormat();
  const { weekDays, days, byDate, loads, selectTask } = data;
  const today = localToday();
  const [selected, setSelected] = useState(() =>
    weekDays.includes(today) ? today : (weekDays.find((d) => byDate.has(d)) ?? weekDays[0]),
  );
  const touchX = useRef<number | null>(null);
  const day = days.get(selected);
  const capacity = day?.capacity_minutes ?? 0;
  const scheduled = loads.get(selected) ?? 0;

  function shift(delta: number) {
    const target = addDays(selected, delta);
    if (weekDays.includes(target)) setSelected(target);
    else goWeek(target);
  }

  return (
    <div
      className="flex flex-col gap-3"
      onTouchStart={(e: TouchEvent) => (touchX.current = e.touches[0].clientX)}
      onTouchEnd={(e: TouchEvent) => {
        if (touchX.current === null) return;
        const dx = e.changedTouches[0].clientX - touchX.current;
        touchX.current = null;
        if (Math.abs(dx) > SWIPE_PX) shift(dx < 0 ? 1 : -1);
      }}
    >
      <div className="grid grid-cols-7 gap-1" role="group" aria-label={t("daysLabel")}>
        {weekDays.map((d) => {
          const info = days.get(d);
          const load = info && info.capacity_minutes > 0 ? (loads.get(d) ?? 0) / info.capacity_minutes : 0;
          return (
            <button
              key={d}
              type="button"
              aria-pressed={d === selected}
              onClick={() => setSelected(d)}
              className={cn(
                "flex flex-col items-center gap-0.5 rounded-lg py-1.5 text-xs outline-none focus-visible:ring-2 focus-visible:ring-ring",
                d === selected ? "bg-foreground text-background" : "hover:bg-muted",
                (!info || info.off_reason) && d !== selected && "opacity-50",
              )}
            >
              <span>{fmt.weekday(d)}</span>
              <span className="text-sm font-semibold">{fmt.dayOfMonth(d)}</span>
              <span
                className={cn("size-1.5 rounded-full", load === 0 ? "bg-transparent" : load >= 1 ? "bg-current" : "bg-current opacity-50")}
                aria-hidden
              />
            </button>
          );
        })}
      </div>

      <section className="flex flex-col gap-2" aria-live="polite">
        <div className="flex items-center justify-between text-sm">
          <h3 className="font-semibold">
            {fmt.weekday(selected)} {fmt.date(selected)}
          </h3>
          {day && !day.off_reason && (
            <span className="text-xs text-muted-foreground tabular-nums">
              {t("load", { scheduled: fmt.hours(scheduled), capacity: fmt.hours(capacity) })}
            </span>
          )}
        </div>
        {day && !day.off_reason && <LoadBar load={scheduled} capacity={capacity} />}
        <DayAgenda date={selected} data={data} onSelect={selectTask} />
      </section>
    </div>
  );
}

function MobileMonth({ data, month }: { data: CalendarData; month: string }) {
  const t = useTranslations("plan.calendar");
  const fmt = usePlanFormat();
  const { days, byDate, loads, markersByDate, selectTask } = data;
  const grid = monthGrid(month);
  const today = localToday();
  const [selected, setSelected] = useState(() => {
    if (monthOf(today) === month) return today;
    const firstWorking = grid.find((d) => monthOf(d) === month && (days.get(d)?.capacity_minutes ?? 0) > 0);
    return firstWorking ?? monthStart(month);
  });
  const day = days.get(selected);
  const load = loads.get(selected) ?? 0;

  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-7 gap-1 text-center text-[11px] text-muted-foreground" aria-hidden>
        {grid.slice(0, 7).map((d) => (
          <span key={d}>{fmt.weekday(d)}</span>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1" role="group" aria-label={t("daysLabel")}>
        {grid.map((d) => {
          const info = days.get(d);
          const colors = [...new Set((byDate.get(d) ?? []).map((b) => b.view.objectiveIndex))].slice(0, 3);
          const inMonth = monthOf(d) === month;
          return (
            <button
              key={d}
              type="button"
              aria-pressed={d === selected}
              aria-label={fmt.date(d)}
              onClick={() => setSelected(d)}
              className={cn(
                "flex h-12 flex-col items-center justify-center gap-1 rounded-lg text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring",
                d === selected ? "bg-foreground text-background" : "hover:bg-muted",
                (!info || info.off_reason || !inMonth) && d !== selected && "opacity-40",
                d === today && d !== selected && "ring-1 ring-foreground",
              )}
            >
              <span className="font-semibold">{fmt.dayOfMonth(d)}</span>
              <span className="flex h-1.5 gap-0.5" aria-hidden>
                {colors.map((i) => (
                  <span key={i} className="size-1.5 rounded-full" style={{ backgroundColor: objectiveColor(i) }} />
                ))}
                {markersByDate.has(d) && <span className="size-1.5 rotate-45 bg-current" />}
              </span>
            </button>
          );
        })}
      </div>
      <section className="flex flex-col gap-2" aria-live="polite">
        <div className="flex items-center justify-between text-sm">
          <h3 className="font-semibold">
            {fmt.weekday(selected)} {fmt.date(selected)}
          </h3>
          {day && !day.off_reason && (
            <span className="text-xs text-muted-foreground tabular-nums">
              {t("load", { scheduled: fmt.hours(load), capacity: fmt.hours(day.capacity_minutes) })}
            </span>
          )}
        </div>
        <DayAgenda date={selected} data={data} onSelect={selectTask} />
      </section>
    </div>
  );
}

function Legend({ objectives }: { objectives: { index: number; title: string }[] }) {
  const t = useTranslations("plan.calendar");
  return (
    <ul className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted-foreground" aria-label={t("legend")}>
      {objectives.map((o) => (
        <li key={o.index} className="flex items-center gap-1.5">
          <span className="size-3 rounded-sm" style={{ backgroundColor: objectiveColor(o.index) }} aria-hidden />
          <span className="font-mono">O{o.index + 1}</span>
          <span className="max-w-40 truncate">{o.title}</span>
        </li>
      ))}
      <li className="flex items-center gap-1.5">
        <span className="okr-swatch-off size-3 rounded-sm border border-border" aria-hidden />
        {t("offShort")}
      </li>
      <li className="flex items-center gap-1.5">
        <span className="okr-swatch-holiday size-3 rounded-sm border border-border" aria-hidden />
        {t("off.holiday")}
      </li>
      <li className="flex items-center gap-1.5">
        <span className="okr-swatch-leave size-3 rounded-sm border border-border" aria-hidden />
        {t("off.leave")}
      </li>
      <li className="flex items-center gap-1.5">
        <span className="okr-swatch-buffer size-3 rounded-sm border border-border" aria-hidden />
        {t("buffer")}
      </li>
      <li className="flex items-center gap-1.5">
        <span className="size-3 rounded-sm border border-dashed border-foreground" aria-hidden />
        {t("markerLegend")}
      </li>
    </ul>
  );
}
