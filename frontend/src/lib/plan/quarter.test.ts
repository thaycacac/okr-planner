import { describe, expect, it } from "vitest";

import type { CalendarSettings } from "@/lib/api/types";

import { addDays, isoWeek, startOfWeek, weekdayOf } from "./dates";
import {
  bufferStartIndex,
  calendarExceptions,
  capacityStats,
  dayCapacity,
  defaultQuarter,
  overviewOrder,
  parseQuarterSlug,
  previousQuarter,
  previousQuarterWithPlan,
  quarterRange,
  quarterSlug,
  type QuarterRef,
  quarterStatus,
} from "./quarter";

const weekdays4h: CalendarSettings = {
  capacity_minutes: { mon: 240, tue: 240, wed: 240, thu: 240, fri: 240, sat: 0, sun: 0 },
  work_saturday: false,
  work_sunday: false,
  work_holidays: false,
};

describe("dates", () => {
  it("does calendar arithmetic without time zone drift", () => {
    expect(addDays("2026-12-31", 1)).toBe("2027-01-01");
    expect(weekdayOf("2026-10-01")).toBe("thu");
    expect(startOfWeek("2026-10-04")).toBe("2026-09-28");
    expect(startOfWeek("2026-10-05")).toBe("2026-10-05");
  });

  it("numbers ISO weeks across year boundaries", () => {
    expect(isoWeek("2026-10-05")).toBe(41);
    expect(isoWeek("2026-12-21")).toBe(52);
    expect(isoWeek("2026-12-31")).toBe(53);
    expect(isoWeek("2027-01-03")).toBe(53);
    expect(isoWeek("2027-01-04")).toBe(1);
  });
});

describe("quarter slugs and ranges", () => {
  it("round-trips slugs and rejects junk", () => {
    expect(quarterSlug({ year: 2026, number: 4 })).toBe("2026-Q4");
    expect(parseQuarterSlug("2026-q4")).toEqual({ year: 2026, number: 4 });
    expect(parseQuarterSlug("2026-Q5")).toBeNull();
    expect(parseQuarterSlug(undefined)).toBeNull();
  });

  it("knows the last day of each quarter", () => {
    expect(quarterRange({ year: 2026, number: 4 })).toEqual({ start: "2026-10-01", end: "2026-12-31" });
    expect(quarterRange({ year: 2028, number: 1 }).end).toBe("2028-03-31");
    expect(quarterRange({ year: 2026, number: 2 }).end).toBe("2026-06-30");
  });

  it("classifies quarters relative to today", () => {
    expect(quarterStatus({ year: 2026, number: 4 }, "2026-09-30")).toEqual({ kind: "upcoming", daysUntil: 1 });
    expect(quarterStatus({ year: 2026, number: 3 }, "2026-09-30")).toEqual({ kind: "ongoing" });
    expect(quarterStatus({ year: 2026, number: 2 }, "2026-09-30")).toEqual({ kind: "ended" });
  });

  it("lists the current quarter first, then upcoming, then past ones", () => {
    const quarters: QuarterRef[] = [
      { year: 2026, number: 2 },
      { year: 2027, number: 2 },
      { year: 2026, number: 1 },
      { year: 2027, number: 1 },
      { year: 2026, number: 4 },
    ];
    expect(quarters.sort(overviewOrder("2026-10-01")).map(quarterSlug)).toEqual([
      "2026-Q4",
      "2027-Q1",
      "2027-Q2",
      "2026-Q2",
      "2026-Q1",
    ]);
  });
});

describe("capacityStats", () => {
  it("counts Q4/2026 from the weekly calendar", () => {
    const stats = capacityStats({ year: 2026, number: 4 }, weekdays4h, "2026-09-30");
    expect(stats.totalDays).toBe(92);
    expect(stats.workingDays).toBe(66);
    expect(stats.supplyMinutes).toBe(66 * 240);
    expect(stats.bufferStart).toBe("2026-12-23");
    expect(stats.bufferMinutes).toBe(7 * 240);
  });

  it("subtracts holidays and leave, and adds make-up days", () => {
    const exceptions = calendarExceptions(
      [
        { date: "2026-11-24", kind: "public_holiday" },
        { date: "2026-10-10", kind: "makeup_day" },
      ],
      [{ date: "2026-10-20" }],
    );
    expect(dayCapacity(weekdays4h, "2026-11-24", exceptions)).toBe(0);
    expect(dayCapacity({ ...weekdays4h, work_holidays: true }, "2026-11-24", exceptions)).toBe(240);
    expect(dayCapacity(weekdays4h, "2026-10-10", exceptions)).toBe(240);
    expect(dayCapacity(weekdays4h, "2026-10-20", exceptions)).toBe(0);

    const holidayOnly = calendarExceptions([{ date: "2026-11-24", kind: "public_holiday" }], []);
    const stats = capacityStats({ year: 2026, number: 4 }, weekdays4h, "2026-09-30", holidayOnly);
    expect(stats.workingDays).toBe(65);
    expect(stats.supplyMinutes).toBe(260 * 60);
    expect(stats.bufferMinutes).toBe(28 * 60);
  });

  it("starts an ongoing quarter from today", () => {
    const stats = capacityStats({ year: 2026, number: 3 }, weekdays4h, "2026-09-30");
    expect(stats.started).toBe(true);
    expect(stats.windowStart).toBe("2026-09-30");
    expect(stats.workingDays).toBe(1);
    expect(stats.supplyMinutes).toBe(240);
  });

  it("uses the shortest whole-day suffix holding 10% of supply as buffer", () => {
    expect(bufferStartIndex([60, 60, 60, 60, 60, 60, 60, 60, 60, 60])).toBe(9);
    expect(bufferStartIndex([100, 10, 5, 5])).toBe(1);
    expect(bufferStartIndex([0, 0])).toBeNull();
  });
});

describe("defaultQuarter", () => {
  it("skips to the next quarter when fewer than 10 working days are left", () => {
    expect(defaultQuarter("2026-09-30", weekdays4h)).toEqual({ year: 2026, number: 4 });
    expect(defaultQuarter("2026-08-03", weekdays4h)).toEqual({ year: 2026, number: 3 });
    expect(defaultQuarter("2026-12-28", weekdays4h)).toEqual({ year: 2027, number: 1 });
  });
});

describe("previous quarter", () => {
  it("steps back across the year boundary", () => {
    expect(previousQuarter({ year: 2027, number: 1 })).toEqual({ year: 2026, number: 4 });
    expect(previousQuarter({ year: 2026, number: 3 })).toEqual({ year: 2026, number: 2 });
  });

  it("skips earlier quarters that have no tasks", () => {
    const quarters = [
      { year: 2026, number: 4, task_count: 12 },
      { year: 2026, number: 3, task_count: 0 },
      { year: 2026, number: 2, task_count: 8 },
      { year: 2025, number: 4, task_count: 5 },
    ];
    expect(previousQuarterWithPlan(quarters, { year: 2026, number: 4 })).toEqual({ year: 2026, number: 2 });
    expect(previousQuarterWithPlan(quarters, { year: 2025, number: 4 })).toBeNull();
  });
});
