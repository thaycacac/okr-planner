import type { TaskCreate, TaskOut, TaskUpdate } from "@/lib/api/types";

import { criteriaLines } from "./criteria";

/** Tasks the planner writes are 2–6h; outside that range the form suggests splitting or merging. */
export const SUGGESTED_MIN_HOURS = 2;
export const SUGGESTED_MAX_HOURS = 6;
/** Hard limit of the API (2400 minutes). */
export const MAX_HOURS = 40;
export const HOURS_STEP = 0.5;

export type TaskForm = {
  title: string;
  hours: number;
  description: string;
  criteria: string[];
  dependsOn: number[];
  pinned: boolean;
  pinDate: string;
  done: boolean;
};

export type TaskFormErrors = Partial<Record<"title" | "hours" | "pinDate", "required" | "range">>;

export function emptyTaskForm(defaultDate: string): TaskForm {
  return {
    title: "",
    hours: 4,
    description: "",
    criteria: [""],
    dependsOn: [],
    pinned: false,
    pinDate: defaultDate,
    done: false,
  };
}

export function taskToForm(task: TaskOut, start: string | null, defaultDate: string): TaskForm {
  const criteria = criteriaLines(task.done_criteria);
  return {
    title: task.title,
    hours: task.estimate_minutes / 60,
    description: task.description,
    criteria: criteria.length ? criteria : [""],
    dependsOn: [...task.depends_on],
    pinned: task.pinned,
    pinDate: start ?? defaultDate,
    done: task.status === "done",
  };
}

export function validateTaskForm(form: TaskForm): TaskFormErrors {
  const errors: TaskFormErrors = {};
  if (!form.title.trim()) errors.title = "required";
  if (!Number.isFinite(form.hours) || form.hours <= 0 || form.hours > MAX_HOURS) errors.hours = "range";
  if (form.pinned && !/^\d{4}-\d{2}-\d{2}$/.test(form.pinDate)) errors.pinDate = "required";
  return errors;
}

export function sizeHint(hours: number): "split" | "small" | null {
  if (hours > SUGGESTED_MAX_HOURS) return "split";
  if (hours < SUGGESTED_MIN_HOURS) return "small";
  return null;
}

function doneCriteria(form: TaskForm) {
  return form.criteria.map((line) => line.trim()).filter(Boolean).join("\n");
}

export function toMinutes(hours: number) {
  return Math.max(1, Math.round(hours * 60));
}

export function createPayload(form: TaskForm): TaskCreate {
  return {
    title: form.title.trim(),
    estimate_minutes: toMinutes(form.hours),
    description: form.description.trim(),
    done_criteria: doneCriteria(form),
    depends_on: form.dependsOn,
  };
}

/** Only the fields that differ from the stored task, so an untouched task stays "not edited". */
export function updatePayload(task: TaskOut, form: TaskForm): TaskUpdate {
  const next = createPayload(form);
  const update: TaskUpdate = {};
  if (next.title !== task.title) update.title = next.title;
  if (next.estimate_minutes !== task.estimate_minutes) update.estimate_minutes = next.estimate_minutes;
  if (next.description !== task.description) update.description = next.description;
  if (next.done_criteria !== doneCriteria(taskToForm(task, null, ""))) update.done_criteria = next.done_criteria;
  const deps = [...(next.depends_on ?? [])].sort((a, b) => a - b);
  const current = [...task.depends_on].sort((a, b) => a - b);
  if (deps.join() !== current.join()) update.depends_on = next.depends_on;
  if (form.done !== (task.status === "done")) update.status = form.done ? "done" : "todo";
  return update;
}

export type PinChange = { kind: "pin"; date: string } | { kind: "unpin" } | null;

/** Finished tasks are never pinned: the scheduler keeps their history instead. */
export function pinChange(task: TaskOut | null, start: string | null, form: TaskForm): PinChange {
  if (form.done) return null;
  if (form.pinned && (!task?.pinned || form.pinDate !== start)) return { kind: "pin", date: form.pinDate };
  if (!form.pinned && task?.pinned) return { kind: "unpin" };
  return null;
}

/** Tasks a new dependency may point at: not the task itself and not anything that already waits on it. */
export function dependencyCandidates(
  taskId: number | null,
  tasks: ReadonlyMap<number, { dependsOn: readonly number[] }>,
): Set<number> {
  const blocked = new Set<number>();
  if (taskId !== null) {
    blocked.add(taskId);
    let grew = true;
    while (grew) {
      grew = false;
      for (const [id, t] of tasks) {
        if (!blocked.has(id) && t.dependsOn.some((d) => blocked.has(d))) {
          blocked.add(id);
          grew = true;
        }
      }
    }
  }
  return new Set([...tasks.keys()].filter((id) => !blocked.has(id)));
}
