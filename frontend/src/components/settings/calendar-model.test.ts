import { describe, expect, it } from "vitest";

import type { CalendarSettings } from "@/lib/api/types";

import {
  clampHours,
  countChanges,
  DEFAULT_HOURS,
  fromDraft,
  hasWorkingDay,
  parseHours,
  toDraft,
  weeklyHours,
} from "./calendar-model";

const defaults: CalendarSettings = {
  capacity_minutes: { mon: 240, tue: 240, wed: 240, thu: 240, fri: 240, sat: 0, sun: 0 },
  work_saturday: false,
  work_sunday: false,
  work_holidays: false,
};

describe("clampHours / parseHours", () => {
  it("rounds to 0.5h steps within 0.5–12h", () => {
    expect(clampHours(4.2)).toBe(4);
    expect(clampHours(4.3)).toBe(4.5);
    expect(clampHours(0)).toBe(0.5);
    expect(clampHours(30)).toBe(12);
    expect(clampHours(Number.NaN)).toBe(DEFAULT_HOURS);
  });

  it("accepts a decimal comma", () => {
    expect(parseHours("4,5")).toBe(4.5);
    expect(parseHours(" 6 ")).toBe(6);
    expect(parseHours("abc")).toBeNull();
  });
});

describe("toDraft / fromDraft", () => {
  it("round-trips the default calendar", () => {
    expect(fromDraft(toDraft(defaults))).toEqual(defaults);
  });

  it("treats Saturday as off when its flag is off even with capacity", () => {
    const draft = toDraft({ ...defaults, capacity_minutes: { ...defaults.capacity_minutes, sat: 180 } });
    expect(draft.days.sat).toEqual({ enabled: false, hours: 3 });
  });

  it("maps an enabled weekend day to its flag and minutes", () => {
    const draft = toDraft(defaults);
    draft.days.sat = { enabled: true, hours: 2.5 };
    const out = fromDraft(draft);
    expect(out.work_saturday).toBe(true);
    expect(out.capacity_minutes.sat).toBe(150);
    expect(out.work_sunday).toBe(false);
    expect(out.capacity_minutes.sun).toBe(0);
  });

  it("sends 0 minutes for a disabled weekday", () => {
    const draft = toDraft(defaults);
    draft.days.wed = { enabled: false, hours: 4 };
    expect(fromDraft(draft).capacity_minutes.wed).toBe(0);
  });
});

describe("change tracking", () => {
  it("counts changed days and the holiday switch", () => {
    const saved = toDraft(defaults);
    const draft = toDraft(defaults);
    draft.days.sat = { enabled: true, hours: 4 };
    draft.days.mon = { enabled: true, hours: 5 };
    draft.workHolidays = true;
    expect(countChanges(saved, draft)).toBe(3);
  });

  it("ignores hours on a day that stays off", () => {
    const saved = toDraft(defaults);
    const draft = toDraft(defaults);
    draft.days.sun = { enabled: false, hours: 8 };
    expect(countChanges(saved, draft)).toBe(0);
  });

  it("sums weekly hours and requires a working day", () => {
    const draft = toDraft(defaults);
    expect(weeklyHours(draft)).toBe(20);
    for (const day of Object.keys(draft.days) as (keyof typeof draft.days)[]) {
      draft.days[day] = { ...draft.days[day], enabled: false };
    }
    expect(hasWorkingDay(draft)).toBe(false);
  });
});
