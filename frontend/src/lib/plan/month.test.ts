import { describe, expect, it } from "vitest";

import { clampMonth, monthEnd, monthGrid, monthsOf } from "./month";

describe("month helpers", () => {
  it("finds the last day of the month, including leap years", () => {
    expect(monthEnd("2026-02")).toBe("2026-02-28");
    expect(monthEnd("2028-02")).toBe("2028-02-29");
    expect(monthEnd("2026-12")).toBe("2026-12-31");
  });

  it("lists every month a range touches, across the year boundary", () => {
    expect(monthsOf("2026-11-15", "2027-01-03")).toEqual(["2026-11", "2026-12", "2027-01"]);
    expect(monthsOf("2026-10-01", "2026-10-31")).toEqual(["2026-10"]);
  });

  it("keeps a month inside the quarter and ignores malformed input", () => {
    const months = ["2026-10", "2026-11", "2026-12"];
    expect(clampMonth("2026-09", months)).toBe("2026-10");
    expect(clampMonth("2027-01", months)).toBe("2026-12");
    expect(clampMonth("2026-11", months)).toBe("2026-11");
    expect(clampMonth("junk", months)).toBe("2026-10");
  });

  it("builds a Monday-first grid of whole weeks", () => {
    const grid = monthGrid("2026-10");
    expect(grid[0]).toBe("2026-09-28");
    expect(grid.at(-1)).toBe("2026-11-01");
    expect(grid.length % 7).toBe(0);
  });
});
