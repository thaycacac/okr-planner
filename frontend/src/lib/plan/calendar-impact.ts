import { addDays } from "./dates";
import { quarterOf, sameQuarter } from "./quarter";

/** Query flag that makes the quarter page open the reschedule preview on arrival. */
export const RESCHEDULE_QUERY = "reschedule";

type PlannedQuarter = { id: number; year: number; number: number; task_count: number };

/** Quarters holding tasks that one of the changed days falls in, with those days sorted. */
export function quartersHit<T extends PlannedQuarter>(dates: readonly string[], quarters: readonly T[]) {
  const hits = new Map<number, { quarter: T; dates: string[] }>();
  for (const date of [...new Set(dates)].sort()) {
    const quarter = quarters.find((q) => q.task_count > 0 && sameQuarter(q, quarterOf(date)));
    if (!quarter) continue;
    const hit = hits.get(quarter.id) ?? { quarter, dates: [] };
    hit.dates.push(date);
    hits.set(quarter.id, hit);
  }
  return [...hits.values()];
}

/** Consecutive days folded into [start, end] runs so a week of leave reads as one range. */
export function dateRuns(sortedDates: readonly string[]): [string, string][] {
  const runs: [string, string][] = [];
  for (const date of sortedDates) {
    const last = runs.at(-1);
    if (last && addDays(last[1], 1) === date) last[1] = date;
    else runs.push([date, date]);
  }
  return runs;
}
