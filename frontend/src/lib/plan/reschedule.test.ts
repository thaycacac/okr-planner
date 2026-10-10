import { describe, expect, it } from "vitest";

import type { PinConflict, TaskDateChange } from "@/lib/api/types";

import { changeRows, conflictsByTask, initialChoices, keepVariant, keptConflicts, toResolutions } from "./reschedule";

function conflict(taskId: number, allowed: PinConflict["allowed_actions"], resolution: PinConflict["resolution"] = null): PinConflict {
  return {
    task_id: taskId,
    code: "pinned_over_capacity",
    dates: ["2026-10-05"],
    allowed_actions: allowed,
    resolution,
    related_task_ids: [],
  } as unknown as PinConflict;
}

describe("reschedule helpers", () => {
  it("defaults to keeping the pin when allowed, otherwise the first allowed action", () => {
    const choices = initialChoices([conflict(1, ["keep", "unpin"]), conflict(2, ["unpin", "repin"]), conflict(3, ["keep"], "unpin")]);
    expect(choices).toEqual({ 1: "keep", 2: "unpin", 3: "unpin" });
    expect(toResolutions({ 2: "repin" })).toEqual([{ task_id: 2, action: "repin" }]);
  });

  it("groups conflicts per task and keeps only actions every conflict allows", () => {
    const groups = conflictsByTask([conflict(1, ["keep", "unpin", "repin"]), conflict(1, ["unpin", "repin"]), conflict(2, ["keep"])]);
    expect(groups.map((g) => [g.taskId, g.conflicts.length, g.allowed])).toEqual([
      [1, 2, ["unpin", "repin"]],
      [2, 1, ["keep"]],
    ]);
  });

  it("lists only tasks whose dates change, earliest new date first", () => {
    const change = (id: number, before: string | null, after: string | null): TaskDateChange =>
      ({ task_id: id, before_start: before, before_end: before, after_start: after, after_end: after }) as TaskDateChange;
    const rows = changeRows([
      change(1, "2026-10-01", "2026-10-01"),
      change(2, "2026-10-01", "2026-10-08"),
      change(3, null, "2026-10-02"),
      change(4, "2026-10-03", null),
    ]);
    expect(rows.map((r) => [r.task_id, r.kind])).toEqual([
      [3, "added"],
      [2, "moved"],
      [4, "removed"],
    ]);
  });

  it("labels keeping a pin by its most severe consequence", () => {
    const withCode = (code: PinConflict["code"]) => ({ ...conflict(1, ["keep"]), code }) as PinConflict;
    expect(keepVariant([withCode("pinned_over_capacity")])).toBe("overCapacity");
    expect(keepVariant([withCode("pinned_over_capacity"), withCode("pinned_non_working_day")])).toBe("nonWorkingDay");
    expect(keepVariant([withCode("pinned_non_working_day"), withCode("pinned_dependency_conflict")])).toBe("dependency");
    expect(keepVariant([withCode("pinned_overdue")])).toBe("generic");
  });

  it("finds the pins kept under the current choices, falling back to the server resolution", () => {
    const kept = keptConflicts([conflict(1, ["keep", "unpin"]), conflict(2, ["keep", "unpin"], "keep"), conflict(3, ["keep"])], {
      1: "unpin",
      3: "keep",
    });
    expect(kept.map((c) => c.task_id)).toEqual([2, 3]);
  });
});
