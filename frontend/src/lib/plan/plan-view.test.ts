import { describe, expect, it } from "vitest";

import type { QuarterDetail, QuarterSchedule, TaskOut } from "@/lib/api/types";

import {
  blocksByDate,
  buildPlanView,
  calendarBlocks,
  dayLoads,
  droppedTotals,
  krMarkers,
  summarizeFeasibility,
  taskMatches,
} from "./plan-view";
import { fullPeriodCount, taskProgress, workloadPeriods } from "./workload";

function task(id: number, kr: number, minutes: number, dependsOn: number[] = [], position = 0): TaskOut {
  return {
    id,
    key_result_id: kr,
    objective_id: 1,
    title: `Task ${id}`,
    description: "",
    done_criteria: "",
    estimate_minutes: minutes,
    status: "todo",
    pinned: false,
    position,
    depends_on: dependsOn,
    plan_run_id: "run",
    pinned_allocations: [],
    user_edited: false,
    completed_at: null,
  };
}

const detail = {
  id: 1,
  objectives: [
    {
      id: 1,
      quarter_id: 1,
      title: "Ra mắt",
      priority: "high",
      position: 0,
      key_results: [
        { id: 10, objective_id: 1, text: "KR a", kind: "numeric", baseline: 1, target: 2, unit: null, due_date: null, note: null, position: 0, tasks: [task(100, 10, 240, [], 0), task(101, 10, 120, [100], 1)] },
        { id: 11, objective_id: 1, text: "KR b", kind: "binary", baseline: null, target: null, unit: null, due_date: null, note: null, position: 1, tasks: [task(102, 11, 300)] },
      ],
    },
  ],
} as unknown as QuarterDetail;

const schedule = {
  id: 1,
  quarter_id: 1,
  plan_run_id: "run",
  created_at: "2026-09-30T00:00:00Z",
  today: "2026-09-30",
  window_start: "2026-10-01",
  window_end: "2026-12-31",
  feasibility: {
    status: "red",
    demand_minutes: 660,
    supply_minutes: 480,
    buffered_supply_minutes: 240,
    buffer_start: "2026-10-02",
    late_task_ids: [102],
    late_key_result_ids: [11],
    late_objective_ids: [1],
  },
  tasks: [
    { task_id: 100, key_result_id: 10, objective_id: 1, start_date: "2026-10-01", end_date: "2026-10-01", allocations: [{ date: "2026-10-01", minutes: 240 }], pinned: false, uses_buffer: false },
    { task_id: 101, key_result_id: 10, objective_id: 1, start_date: "2026-10-02", end_date: "2026-10-05", allocations: [{ date: "2026-10-02", minutes: 60 }, { date: "2026-10-05", minutes: 60 }], pinned: false, uses_buffer: true },
  ],
  unscheduled: [{ task_id: 102, key_result_id: 11, objective_id: 1, reason: "exceeds_quarter" }],
  warnings: [],
  days: [],
} as unknown as QuarterSchedule;

describe("buildPlanView", () => {
  it("lists dropped KRs and paused objectives outside the plan", () => {
    const [o1] = detail.objectives;
    const paused = { ...o1, id: 2, position: 1, active: false, key_results: o1.key_results.map((kr) => ({ ...kr, id: kr.id + 10 })) };
    const withDropped = {
      ...detail,
      objectives: [{ ...o1, key_results: [o1.key_results[0], { ...o1.key_results[1], active: false }] }, paused],
    } as unknown as QuarterDetail;
    const view = buildPlanView(withDropped, null);
    expect(view.objectives.map((o) => o.krs.length)).toEqual([1]);
    expect(view.dropped.map((d) => (d.kind === "kr" ? ["kr", d.kr.id, d.taskCount] : ["objective", d.objective.id, d.taskCount]))).toEqual([
      ["kr", 11, 1],
      ["objective", 2, 3],
    ]);
    expect(droppedTotals(view.dropped)).toEqual({ krs: 3, tasks: 4 });
    expect(buildPlanView(detail, null).dropped).toEqual([]);
  });

  it("numbers the tree, sums hours and links dependencies both ways", () => {
    const view = buildPlanView(detail, schedule);
    const [o1] = view.objectives;
    expect(o1.code).toBe("O1");
    expect(o1.krs.map((k) => [k.code, k.minutes, k.start, k.end])).toEqual([
      ["KR 1.1", 360, "2026-10-01", "2026-10-05"],
      ["KR 1.2", 300, null, null],
    ]);
    expect(view.tasks.get(101)?.code).toBe("T1.1.2");
    expect(view.tasks.get(100)?.blocks).toEqual([101]);
    expect(view.tasks.get(102)?.late).toBe(true);
    expect(view.totalMinutes).toBe(660);
    expect(view.taskCount).toBe(3);
  });

  it("keeps the codes of later KRs when a KR in the middle is dropped", () => {
    const [o1] = detail.objectives;
    const kr = (id: number, position: number, tasks: TaskOut[]) => ({ ...o1.key_results[1], id, position, tasks });
    const withDropped = {
      ...detail,
      objectives: [
        {
          ...o1,
          key_results: [
            { ...kr(20, 0, [task(200, 20, 60)]), active: false },
            kr(21, 1, [task(210, 21, 60), task(211, 21, 60, [], 1)]),
          ],
        },
      ],
    } as unknown as QuarterDetail;
    const view = buildPlanView(withDropped, null);
    expect(view.objectives[0].krs.map((k) => k.code)).toEqual(["KR 1.2"]);
    expect(view.tasks.get(211)).toMatchObject({ code: "T1.2.2", krCode: "KR 1.2" });
    expect(view.dropped.map((d) => d.code)).toEqual(["KR 1.1"]);
    expect(view.codes.krs.get(20)).toBe("KR 1.1");
  });

  it("keeps the code and colour index of later objectives when one is paused", () => {
    const objective = (id: number, position: number, krId: number, active = true) => ({
      ...detail.objectives[0],
      id,
      position,
      active,
      key_results: [{ ...detail.objectives[0].key_results[0], id: krId, tasks: [task(krId * 10, krId, 60)] }],
    });
    const withPaused = {
      ...detail,
      objectives: [objective(1, 0, 10), objective(2, 1, 20, false), objective(3, 2, 30)],
    } as unknown as QuarterDetail;
    const view = buildPlanView(withPaused, null);
    expect(view.objectives.map((o) => [o.code, o.index])).toEqual([
      ["O1", 0],
      ["O3", 2],
    ]);
    expect(view.tasks.get(300)).toMatchObject({ code: "T3.1.1", krCode: "KR 3.1", objectiveIndex: 2 });
    expect(view.dropped.map((d) => d.code)).toEqual(["O2"]);
    expect(view.objectiveSlots).toBe(3);

    const blocks = calendarBlocks(view).concat({
      id: "300-2026-10-01",
      date: "2026-10-01",
      minutes: 60,
      view: view.tasks.get(300)!,
      part: 1,
      parts: 1,
    });
    const [week] = workloadPeriods([], blocks, view.objectiveSlots, "week");
    expect(week.byObjective).toEqual([0, 0, 60]);
  });

  it("works before any schedule exists", () => {
    const view = buildPlanView(detail, null);
    expect(view.tasks.get(100)?.start).toBeNull();
    expect(view.objectives[0].start).toBeNull();
  });
});

describe("summarizeFeasibility", () => {
  it("reports shortage, buffer use and the KRs that do not fit", () => {
    const view = buildPlanView(detail, schedule);
    const summary = summarizeFeasibility(schedule, view);
    expect(summary).toMatchObject({
      status: "red",
      usedPercent: 138,
      shortageMinutes: 180,
      bufferMinutes: 240,
      bufferUsedMinutes: 240,
      bufferTaskCount: 1,
      lateTaskCount: 1,
      lateMinutes: 300,
      finishDate: "2026-10-05",
    });
    expect(summary.lateKrs.map((l) => [l.kr.code, l.count, l.minutes])).toEqual([["KR 1.2", 1, 300]]);
  });
});

describe("calendar blocks", () => {
  it("splits multi-day tasks into numbered parts per day", () => {
    const view = buildPlanView(detail, schedule);
    const byDate = blocksByDate(calendarBlocks(view));
    expect(byDate.get("2026-10-05")?.map((b) => [b.view.code, b.part, b.parts, b.minutes])).toEqual([["T1.1.2", 2, 2, 60]]);
  });

  it("places a pinned task on its pinned days even while the stored schedule is stale", () => {
    const pinned = structuredClone(detail);
    const t = pinned.objectives[0].key_results[0].tasks[0];
    t.pinned = true;
    t.pinned_allocations = [{ date: "2026-10-09", minutes: 240 }];
    const view = buildPlanView(pinned, schedule);
    const blocks = calendarBlocks(view);
    expect(blocks.filter((b) => b.view.task.id === 100).map((b) => b.date)).toEqual(["2026-10-09"]);
    expect(view.tasks.get(100)).toMatchObject({ start: "2026-10-09", end: "2026-10-09", pinned: true });
    expect(dayLoads(blocks).get("2026-10-01")).toBeUndefined();
    expect(dayLoads(blocks).get("2026-10-09")).toBe(240);
  });

  it("leaves finished work out of the day load", () => {
    const finished = structuredClone(detail);
    finished.objectives[0].key_results[0].tasks[0].status = "done";
    const view = buildPlanView(finished, schedule);
    expect(view.tasks.get(100)?.done).toBe(true);
    expect(dayLoads(calendarBlocks(view)).get("2026-10-01")).toBeUndefined();
  });
});

describe("task flags", () => {
  it("marks user-created tasks and tasks that have no days yet", () => {
    const added = structuredClone(detail);
    added.objectives[0].key_results[1].tasks.push({ ...task(103, 11, 120), plan_run_id: null });
    const view = buildPlanView(added, schedule);
    expect(view.tasks.get(103)).toMatchObject({ isNew: true, unplaced: true, late: false });
    expect(view.tasks.get(100)).toMatchObject({ isNew: false, unplaced: false });
  });

  it("leaves dropped objectives and key results out of the tree", () => {
    const dropped = structuredClone(detail);
    (dropped.objectives[0].key_results[1] as { active: boolean }).active = false;
    const view = buildPlanView(dropped, schedule);
    expect(view.krCount).toBe(1);
    expect(view.tasks.has(102)).toBe(false);
  });
});

describe("workload", () => {
  const day = (date: string, capacity: number, extra: object = {}) => ({
    date,
    capacity_minutes: capacity,
    is_buffer: false,
    off_reason: null,
    ...extra,
  });
  const days = [
    day("2026-10-01", 240),
    day("2026-10-02", 240, { is_buffer: true }),
    day("2026-10-05", 240),
    day("2026-10-06", 0, { off_reason: "holiday" }),
  ] as unknown as QuarterSchedule["days"];

  it("sums capacity and unfinished work per week, stacked by objective", () => {
    const view = buildPlanView(detail, schedule);
    const periods = workloadPeriods(days, calendarBlocks(view), 1, "week");
    expect(periods.map((p) => [p.start, p.week, p.capacity, p.bufferCapacity, p.byObjective, p.percent, p.hasHoliday])).toEqual([
      ["2026-09-28", 40, 480, 240, [300], 63, false],
      ["2026-10-05", 41, 240, 0, [60], 25, true],
    ]);
    expect(fullPeriodCount(periods)).toBe(0);
  });

  it("groups by month and leaves finished tasks out", () => {
    const finished = structuredClone(detail);
    finished.objectives[0].key_results[0].tasks[0].status = "done";
    const view = buildPlanView(finished, schedule);
    const [october] = workloadPeriods(days, calendarBlocks(view), 1, "month");
    expect(october).toMatchObject({ start: "2026-10-01", end: "2026-10-06", total: 120, capacity: 720 });
  });

  it("counts finished work and unfinished work that should already be done", () => {
    const finished = structuredClone(detail);
    finished.objectives[0].key_results[0].tasks[0].status = "done";
    const progress = taskProgress(buildPlanView(finished, schedule), "2026-10-10");
    expect(progress).toEqual({ doneTasks: 1, totalTasks: 3, doneMinutes: 240, totalMinutes: 660, overdueMinutes: 120 });
  });

  it("places KR markers on their expected completion date", () => {
    const view = buildPlanView(detail, schedule);
    const markers = krMarkers(view, [
      { key_result_id: 10, expected_completion_date: "2026-10-05" },
      { key_result_id: 11, expected_completion_date: null },
    ]);
    expect(markers).toEqual([{ krId: 10, date: "2026-10-05", krCode: "KR 1.1", objectiveIndex: 0, text: "KR a" }]);
  });
});

describe("taskMatches", () => {
  it("matches title or code, case-insensitively", () => {
    const view = buildPlanView(detail, schedule).tasks.get(101)!;
    expect(taskMatches(view, "task 101")).toBe(true);
    expect(taskMatches(view, "t1.1.2")).toBe(true);
    expect(taskMatches(view, "nope")).toBe(false);
  });
});
