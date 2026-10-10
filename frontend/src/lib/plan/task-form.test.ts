import { describe, expect, it } from "vitest";

import type { TaskOut } from "@/lib/api/types";

import {
  createPayload,
  dependencyCandidates,
  emptyTaskForm,
  pinChange,
  sizeHint,
  taskToForm,
  updatePayload,
  validateTaskForm,
} from "./task-form";

const stored: TaskOut = {
  id: 7,
  key_result_id: 1,
  objective_id: 1,
  title: "Viết đặc tả",
  description: "Nháp đầu",
  done_criteria: "- Có mục tiêu\n- Có phạm vi",
  estimate_minutes: 240,
  status: "todo",
  pinned: false,
  position: 0,
  depends_on: [3, 2],
  plan_run_id: "run",
  pinned_allocations: [],
  user_edited: false,
  completed_at: null,
};

describe("task form", () => {
  it("round-trips a stored task without producing an update", () => {
    const form = taskToForm(stored, "2026-10-05", "2026-10-01");
    expect(form.criteria).toEqual(["Có mục tiêu", "Có phạm vi"]);
    expect(form.hours).toBe(4);
    expect(updatePayload(stored, { ...form, dependsOn: [2, 3] })).toEqual({});
  });

  it("sends only the fields that changed", () => {
    const form = { ...taskToForm(stored, null, "2026-10-01"), title: "  Viết đặc tả v2 ", hours: 5.5, done: true };
    expect(updatePayload(stored, form)).toEqual({ title: "Viết đặc tả v2", estimate_minutes: 330, status: "done" });
  });

  it("drops empty criteria lines when creating", () => {
    const form = { ...emptyTaskForm("2026-10-01"), title: "Mới", criteria: ["a", " ", "b "] };
    expect(createPayload(form)).toMatchObject({ title: "Mới", estimate_minutes: 240, done_criteria: "a\nb" });
  });

  it("validates the title, hour range and pin date", () => {
    const form = { ...emptyTaskForm(""), hours: 41, pinned: true };
    expect(validateTaskForm(form)).toEqual({ title: "required", hours: "range", pinDate: "required" });
    expect(validateTaskForm({ ...emptyTaskForm("2026-10-01"), title: "ok" })).toEqual({});
  });

  it("suggests splitting large tasks and merging tiny ones", () => {
    expect(sizeHint(8)).toBe("split");
    expect(sizeHint(1)).toBe("small");
    expect(sizeHint(4)).toBeNull();
  });

  it("works out pin changes and never pins a finished task", () => {
    const form = taskToForm(stored, "2026-10-05", "2026-10-01");
    expect(pinChange(stored, "2026-10-05", { ...form, pinned: true })).toEqual({ kind: "pin", date: "2026-10-05" });
    const pinned = { ...stored, pinned: true };
    expect(pinChange(pinned, "2026-10-05", { ...form, pinned: true })).toBeNull();
    expect(pinChange(pinned, "2026-10-05", { ...form, pinned: false })).toEqual({ kind: "unpin" });
    expect(pinChange(stored, null, { ...form, pinned: true, done: true })).toBeNull();
  });

  it("offers only dependencies that cannot form a cycle", () => {
    const tasks = new Map([
      [1, { dependsOn: [] }],
      [2, { dependsOn: [1] }],
      [3, { dependsOn: [2] }],
      [4, { dependsOn: [] }],
    ]);
    expect([...dependencyCandidates(2, tasks)].sort()).toEqual([1, 4]);
    expect(dependencyCandidates(null, tasks).size).toBe(4);
  });
});
