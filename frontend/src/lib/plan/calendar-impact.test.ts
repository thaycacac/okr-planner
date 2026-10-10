import { describe, expect, it } from "vitest";

import { dateRuns, quartersHit } from "./calendar-impact";

const quarters = [
  { id: 1, year: 2026, number: 4, task_count: 12 },
  { id: 2, year: 2027, number: 1, task_count: 0 },
  { id: 3, year: 2027, number: 2, task_count: 5 },
];

describe("calendar impact", () => {
  it("keeps only quarters with tasks, grouping and sorting their days", () => {
    const hits = quartersHit(["2026-10-17", "2027-01-05", "2026-10-16", "2027-04-30", "2026-10-16"], quarters);
    expect(hits.map((h) => [h.quarter.id, h.dates])).toEqual([
      [1, ["2026-10-16", "2026-10-17"]],
      [3, ["2027-04-30"]],
    ]);
  });

  it("folds consecutive days into ranges, across month ends", () => {
    expect(dateRuns(["2026-10-16", "2026-10-17", "2026-10-20", "2026-10-31", "2026-11-01"])).toEqual([
      ["2026-10-16", "2026-10-17"],
      ["2026-10-20", "2026-10-20"],
      ["2026-10-31", "2026-11-01"],
    ]);
    expect(dateRuns([])).toEqual([]);
  });
});
