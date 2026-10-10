import type { ScheduleDay } from "@/lib/api/types";

import { isoWeek, startOfWeek } from "./dates";
import { monthOf } from "./month";
import type { CalendarBlock, PlanView } from "./plan-view";

export type Granularity = "week" | "month";

export type WorkloadPeriod = {
  key: string;
  /** Monday of the week, or the first day of the month. */
  start: string;
  end: string;
  week: number | null;
  capacity: number;
  /** Capacity of the period's buffer days. */
  bufferCapacity: number;
  /** Planned minutes per objective index. */
  byObjective: number[];
  total: number;
  /** Rounded share of capacity in use; null when the period has no capacity. */
  percent: number | null;
  hasHoliday: boolean;
};

function periodKey(date: string, granularity: Granularity) {
  return granularity === "week" ? startOfWeek(date) : monthOf(date);
}

/** Capacity and unfinished planned work per week or month, stacked by objective. */
export function workloadPeriods(
  days: readonly ScheduleDay[],
  blocks: readonly CalendarBlock[],
  objectiveCount: number,
  granularity: Granularity,
): WorkloadPeriod[] {
  const periods = new Map<string, WorkloadPeriod>();
  const ensure = (date: string) => {
    const key = periodKey(date, granularity);
    let period = periods.get(key);
    if (!period) {
      period = {
        key,
        start: granularity === "week" ? key : `${key}-01`,
        end: date,
        week: granularity === "week" ? isoWeek(key) : null,
        capacity: 0,
        bufferCapacity: 0,
        byObjective: Array.from({ length: objectiveCount }, () => 0),
        total: 0,
        percent: null,
        hasHoliday: false,
      };
      periods.set(key, period);
    }
    if (date > period.end) period.end = date;
    return period;
  };
  for (const day of days) {
    const period = ensure(day.date);
    period.capacity += day.capacity_minutes;
    if (day.is_buffer) period.bufferCapacity += day.capacity_minutes;
    if (day.off_reason === "holiday") period.hasHoliday = true;
  }
  for (const block of blocks) {
    if (block.view.done) continue;
    const period = ensure(block.date);
    period.byObjective[block.view.objectiveIndex] += block.minutes;
    period.total += block.minutes;
  }
  return [...periods.values()]
    .sort((a, b) => a.start.localeCompare(b.start))
    .map((p) => ({ ...p, percent: p.capacity > 0 ? Math.round((p.total / p.capacity) * 100) : null }));
}

export function fullPeriodCount(periods: readonly WorkloadPeriod[]) {
  return periods.filter((p) => p.capacity > 0 && p.total >= p.capacity).length;
}

export type Progress = {
  doneTasks: number;
  totalTasks: number;
  doneMinutes: number;
  totalMinutes: number;
  /** Unfinished work whose (pinned or scheduled) days are all before today. */
  overdueMinutes: number;
};

export function taskProgress(view: PlanView, today: string): Progress {
  let doneTasks = 0;
  let doneMinutes = 0;
  let overdueMinutes = 0;
  for (const task of view.tasks.values()) {
    if (task.done) {
      doneTasks += 1;
      doneMinutes += task.task.estimate_minutes;
    } else if (task.end !== null && task.end < today) {
      overdueMinutes += task.task.estimate_minutes;
    }
  }
  return { doneTasks, totalTasks: view.taskCount, doneMinutes, totalMinutes: view.totalMinutes, overdueMinutes };
}
