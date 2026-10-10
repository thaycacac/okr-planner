import type { CalendarSettings, QuarterSummary, Weekday } from "@/lib/api/types";

import { daysBetween, eachDay, isoDate, maxDate, weekdayOf } from "./dates";

export type QuarterNumber = 1 | 2 | 3 | 4;
export type QuarterRef = { year: number; number: QuarterNumber };

export const QUARTER_NUMBERS: readonly QuarterNumber[] = [1, 2, 3, 4];
/** A quarter with fewer working days left than this is "too short": default to the next one. */
export const SHORT_QUARTER_DAYS = 10;

export function quarterSlug({ year, number }: QuarterRef): string {
  return `${year}-Q${number}`;
}

export function parseQuarterSlug(value: string | string[] | undefined | null): QuarterRef | null {
  const raw = Array.isArray(value) ? value[0] : value;
  const match = raw ? /^(\d{4})-Q([1-4])$/i.exec(raw) : null;
  if (!match) return null;
  return { year: Number(match[1]), number: Number(match[2]) as QuarterNumber };
}

export function quarterLabel({ year, number }: QuarterRef): string {
  return `Q${number}/${year}`;
}

export function quarterRange({ year, number }: QuarterRef) {
  const startMonth = (number - 1) * 3 + 1;
  const endMonth = startMonth + 2;
  const lastDay = new Date(Date.UTC(year, endMonth, 0)).getUTCDate();
  return { start: isoDate(year, startMonth, 1), end: isoDate(year, endMonth, lastDay) };
}

export function quarterOf(iso: string): QuarterRef {
  const [year, month] = iso.split("-").map(Number);
  return { year, number: (Math.floor((month - 1) / 3) + 1) as QuarterNumber };
}

export function nextQuarter({ year, number }: QuarterRef): QuarterRef {
  return number === 4 ? { year: year + 1, number: 1 } : { year, number: (number + 1) as QuarterNumber };
}

export function previousQuarter({ year, number }: QuarterRef): QuarterRef {
  return number === 1 ? { year: year - 1, number: 4 } : { year, number: (number - 1) as QuarterNumber };
}

/** The latest earlier quarter that has tasks, so "previous quarter" never lands on an empty page. */
export function previousQuarterWithPlan(
  quarters: readonly Pick<QuarterSummary, "year" | "number" | "task_count">[],
  current: QuarterRef,
): QuarterRef | null {
  const earlier = quarters
    .filter((q) => q.task_count > 0 && (q.year < current.year || (q.year === current.year && q.number < current.number)))
    .sort((a, b) => b.year - a.year || b.number - a.number);
  return earlier.length > 0 ? toRef(earlier[0]) : null;
}

export function sameQuarter(a: Pick<QuarterRef, "year"> & { number: number }, b: QuarterRef) {
  return a.year === b.year && a.number === b.number;
}

export function findQuarter<T extends { year: number; number: number }>(
  quarters: readonly T[],
  ref: QuarterRef,
): T | undefined {
  return quarters.find((q) => sameQuarter(q, ref));
}

export function toRef(summary: Pick<QuarterSummary, "year" | "number">): QuarterRef {
  return { year: summary.year, number: summary.number as QuarterNumber };
}

export type QuarterStatus =
  | { kind: "upcoming"; daysUntil: number }
  | { kind: "ongoing" }
  | { kind: "ended" };

export function quarterStatus(ref: QuarterRef, today: string): QuarterStatus {
  const { start, end } = quarterRange(ref);
  if (today < start) return { kind: "upcoming", daysUntil: daysBetween(today, start) };
  if (today > end) return { kind: "ended" };
  return { kind: "ongoing" };
}

/** Sorts the current quarter first, then upcoming ones nearest first, then past ones newest first. */
export function overviewOrder(today: string) {
  const rank = { ongoing: 0, upcoming: 1, ended: 2 } as const;
  return (a: Pick<QuarterSummary, "year" | "number">, b: Pick<QuarterSummary, "year" | "number">) => {
    const kindA = quarterStatus(toRef(a), today).kind;
    const kindB = quarterStatus(toRef(b), today).kind;
    if (kindA !== kindB) return rank[kindA] - rank[kindB];
    const chronological = a.year - b.year || a.number - b.number;
    return kindA === "ended" ? -chronological : chronological;
  };
}

/** Whole-day buffer: the shortest suffix of days holding at least 10% of the supply. */
export function bufferStartIndex(capacities: readonly number[]): number | null {
  const supply = capacities.reduce((sum, c) => sum + c, 0);
  if (supply === 0) return null;
  let suffix = 0;
  for (let i = capacities.length - 1; i >= 0; i--) {
    suffix += capacities[i];
    if (suffix * 10 >= supply) return i;
  }
  return 0;
}

export type CapacityStats = {
  start: string;
  end: string;
  /** First schedulable day: the later of the quarter start and today. */
  windowStart: string;
  started: boolean;
  totalDays: number;
  workingDays: number;
  supplyMinutes: number;
  bufferMinutes: number;
  bufferStart: string | null;
};

export function weekdayMinutes(settings: CalendarSettings, day: Weekday): number {
  if (day === "sat" && !settings.work_saturday) return 0;
  if (day === "sun" && !settings.work_sunday) return 0;
  return settings.capacity_minutes[day];
}

export type CalendarExceptions = {
  holidays: ReadonlySet<string>;
  makeupDays: ReadonlySet<string>;
  leaveDays: ReadonlySet<string>;
};

export const NO_EXCEPTIONS: CalendarExceptions = { holidays: new Set(), makeupDays: new Set(), leaveDays: new Set() };

const MAKEUP_KIND = "makeup_day";
const DEFAULT_WORKDAY_MINUTES = 480;

export function calendarExceptions(
  holidays: readonly { date: string; kind: string }[],
  leaveDays: readonly { date: string }[],
): CalendarExceptions {
  const leave = new Set(leaveDays.map((d) => d.date));
  return {
    holidays: new Set(holidays.filter((h) => h.kind !== MAKEUP_KIND).map((h) => h.date)),
    makeupDays: new Set(holidays.filter((h) => h.kind === MAKEUP_KIND && !leave.has(h.date)).map((h) => h.date)),
    leaveDays: leave,
  };
}

/** Mirrors the scheduler's precedence: make-up day > leave > weekend switch > holiday switch > weekday. */
export function dayCapacity(settings: CalendarSettings, iso: string, exceptions = NO_EXCEPTIONS): number {
  if (exceptions.makeupDays.has(iso)) {
    const weekdays = (["mon", "tue", "wed", "thu", "fri"] as const).map((d) => settings.capacity_minutes[d]);
    return Math.max(...weekdays) || DEFAULT_WORKDAY_MINUTES;
  }
  if (exceptions.leaveDays.has(iso)) return 0;
  const day = weekdayOf(iso);
  if ((day === "sat" || day === "sun") && weekdayMinutes(settings, day) === 0) return 0;
  if (exceptions.holidays.has(iso) && !settings.work_holidays) return 0;
  return settings.capacity_minutes[day];
}

export function capacityStats(
  ref: QuarterRef,
  settings: CalendarSettings,
  today: string,
  exceptions = NO_EXCEPTIONS,
): CapacityStats {
  const { start, end } = quarterRange(ref);
  const windowStart = maxDate(start, today);
  const days = windowStart > end ? [] : eachDay(windowStart, end);
  const capacities = days.map((day) => dayCapacity(settings, day, exceptions));
  const bufferIndex = bufferStartIndex(capacities);
  const supplyMinutes = capacities.reduce((sum, c) => sum + c, 0);
  const bufferMinutes = bufferIndex === null ? 0 : capacities.slice(bufferIndex).reduce((s, c) => s + c, 0);
  return {
    start,
    end,
    windowStart,
    started: today > start,
    totalDays: days.length,
    workingDays: capacities.filter((c) => c > 0).length,
    supplyMinutes,
    bufferMinutes,
    bufferStart: bufferIndex === null ? null : days[bufferIndex],
  };
}

export function defaultQuarter(
  today: string,
  settings: CalendarSettings | null,
  exceptions = NO_EXCEPTIONS,
): QuarterRef {
  const current = quarterOf(today);
  if (!settings) return current;
  const { workingDays } = capacityStats(current, settings, today, exceptions);
  return workingDays < SHORT_QUARTER_DAYS ? nextQuarter(current) : current;
}

export function yearOptions(today: string): number[] {
  const year = Number(today.slice(0, 4));
  return [year - 1, year, year + 1];
}
