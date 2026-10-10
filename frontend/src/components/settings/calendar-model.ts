import type { CalendarSettings, Weekday } from "@/lib/api/types";

export const WEEKDAYS: readonly Weekday[] = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
export const STEP_HOURS = 0.5;
export const MIN_HOURS = 0.5;
export const MAX_HOURS = 12;
export const DEFAULT_HOURS = 4;

export type DayDraft = { enabled: boolean; hours: number };
export type CalendarDraft = { days: Record<Weekday, DayDraft>; workHolidays: boolean };

export function clampHours(hours: number): number {
  if (!Number.isFinite(hours)) return DEFAULT_HOURS;
  const stepped = Math.round(hours / STEP_HOURS) * STEP_HOURS;
  return Math.min(MAX_HOURS, Math.max(MIN_HOURS, stepped));
}

export function parseHours(text: string): number | null {
  const value = Number.parseFloat(text.trim().replace(",", "."));
  return Number.isFinite(value) ? clampHours(value) : null;
}

function weekendFlag(settings: CalendarSettings, day: Weekday) {
  if (day === "sat") return settings.work_saturday;
  if (day === "sun") return settings.work_sunday;
  return true;
}

export function toDraft(settings: CalendarSettings): CalendarDraft {
  const days = {} as Record<Weekday, DayDraft>;
  for (const day of WEEKDAYS) {
    const minutes = settings.capacity_minutes[day];
    days[day] = {
      enabled: minutes > 0 && weekendFlag(settings, day),
      hours: minutes > 0 ? clampHours(minutes / 60) : DEFAULT_HOURS,
    };
  }
  return { days, workHolidays: settings.work_holidays };
}

export function fromDraft(draft: CalendarDraft): CalendarSettings {
  const capacity = {} as CalendarSettings["capacity_minutes"];
  for (const day of WEEKDAYS) {
    const { enabled, hours } = draft.days[day];
    capacity[day] = enabled ? Math.round(hours * 60) : 0;
  }
  return {
    capacity_minutes: capacity,
    work_saturday: draft.days.sat.enabled,
    work_sunday: draft.days.sun.enabled,
    work_holidays: draft.workHolidays,
  };
}

export function isDayChanged(saved: CalendarDraft, draft: CalendarDraft, day: Weekday) {
  const a = saved.days[day];
  const b = draft.days[day];
  return a.enabled !== b.enabled || (b.enabled && a.hours !== b.hours);
}

export function countChanges(saved: CalendarDraft, draft: CalendarDraft) {
  const days = WEEKDAYS.filter((day) => isDayChanged(saved, draft, day)).length;
  return days + (saved.workHolidays !== draft.workHolidays ? 1 : 0);
}

export function weeklyHours(draft: CalendarDraft) {
  return WEEKDAYS.reduce((sum, day) => {
    const { enabled, hours } = draft.days[day];
    return enabled ? sum + hours : sum;
  }, 0);
}

export function hasWorkingDay(draft: CalendarDraft) {
  return WEEKDAYS.some((day) => draft.days[day].enabled);
}
