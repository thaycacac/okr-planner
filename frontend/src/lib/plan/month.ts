import { addDays, startOfWeek } from "./dates";

/** "YYYY-MM" of an ISO date. */
export function monthOf(iso: string): string {
  return iso.slice(0, 7);
}

export function monthStart(month: string): string {
  return `${month}-01`;
}

export function monthEnd(month: string): string {
  const [year, m] = month.split("-").map(Number);
  const last = new Date(Date.UTC(year, m, 0)).getUTCDate();
  return `${month}-${String(last).padStart(2, "0")}`;
}

/** Every month touched by the range, in order. */
export function monthsOf(start: string, end: string): string[] {
  const months: string[] = [];
  let [year, month] = start.split("-").map(Number);
  const last = monthOf(end);
  for (;;) {
    const key = `${year}-${String(month).padStart(2, "0")}`;
    months.push(key);
    if (key >= last) return months;
    month += 1;
    if (month > 12) {
      month = 1;
      year += 1;
    }
  }
}

export function clampMonth(month: string, months: readonly string[]): string {
  if (!/^\d{4}-\d{2}$/.test(month) || months.length === 0) return months[0] ?? month;
  if (month < months[0]) return months[0];
  if (month > months[months.length - 1]) return months[months.length - 1];
  return month;
}

/** Monday-first grid of whole weeks covering the month. */
export function monthGrid(month: string): string[] {
  const first = startOfWeek(monthStart(month));
  const lastDay = monthEnd(month);
  const days: string[] = [];
  for (let day = first; day <= lastDay || days.length % 7 !== 0; day = addDays(day, 1)) days.push(day);
  return days;
}
