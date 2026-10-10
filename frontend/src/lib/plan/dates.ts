import type { Weekday } from "@/lib/api/types";

// Calendar dates travel as ISO strings (YYYY-MM-DD) like the API; arithmetic runs in UTC so the
// browser's time zone never shifts a day.

const MS_PER_DAY = 86_400_000;
const WEEKDAY_BY_UTC_DAY: readonly Weekday[] = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];

function pad(value: number) {
  return String(value).padStart(2, "0");
}

export function isoDate(year: number, month: number, day: number): string {
  return `${year}-${pad(month)}-${pad(day)}`;
}

export function localToday(now: Date = new Date()): string {
  return isoDate(now.getFullYear(), now.getMonth() + 1, now.getDate());
}

function toUtc(iso: string): number {
  const [y, m, d] = iso.split("-").map(Number);
  return Date.UTC(y, m - 1, d);
}

function fromUtc(ms: number): string {
  const date = new Date(ms);
  return isoDate(date.getUTCFullYear(), date.getUTCMonth() + 1, date.getUTCDate());
}

export function addDays(iso: string, days: number): string {
  return fromUtc(toUtc(iso) + days * MS_PER_DAY);
}

export function daysBetween(from: string, to: string): number {
  return Math.round((toUtc(to) - toUtc(from)) / MS_PER_DAY);
}

export function eachDay(start: string, end: string): string[] {
  const days: string[] = [];
  for (let day = start; day <= end; day = addDays(day, 1)) days.push(day);
  return days;
}

export function weekdayOf(iso: string): Weekday {
  return WEEKDAY_BY_UTC_DAY[new Date(toUtc(iso)).getUTCDay()];
}

/** Monday of the ISO week containing `iso`. */
export function startOfWeek(iso: string): string {
  const offset = (new Date(toUtc(iso)).getUTCDay() + 6) % 7;
  return addDays(iso, -offset);
}

/** ISO-8601 week number (weeks start Monday; week 1 holds the year's first Thursday). */
export function isoWeek(iso: string): number {
  const thursday = addDays(startOfWeek(iso), 3);
  const jan1 = `${thursday.slice(0, 4)}-01-01`;
  return Math.floor(daysBetween(jan1, thursday) / 7) + 1;
}

export function maxDate(a: string, b: string) {
  return a > b ? a : b;
}

export function minDate(a: string, b: string) {
  return a < b ? a : b;
}

/** A Date at UTC midnight, for `Intl.DateTimeFormat` with `timeZone: "UTC"`. */
export function utcDate(iso: string): Date {
  return new Date(toUtc(iso));
}
