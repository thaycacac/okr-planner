import type { PinConflict, RescheduleAction, TaskDateChange } from "@/lib/api/types";

export type Choices = Record<number, RescheduleAction>;

/** Keeping the pin is the default whenever the conflict allows it. */
export function initialChoices(conflicts: readonly PinConflict[]): Choices {
  const choices: Choices = {};
  for (const c of conflicts) {
    const fallback = c.allowed_actions.includes("keep") ? "keep" : c.allowed_actions[0];
    choices[c.task_id] = c.resolution ?? fallback ?? "keep";
  }
  return choices;
}

export function toResolutions(choices: Choices) {
  return Object.entries(choices).map(([taskId, action]) => ({ task_id: Number(taskId), action }));
}

/** A task can have several conflicts (e.g. two overfull days); the dialog shows one card per task. */
export function conflictsByTask(conflicts: readonly PinConflict[]) {
  const groups = new Map<number, PinConflict[]>();
  for (const c of conflicts) groups.set(c.task_id, [...(groups.get(c.task_id) ?? []), c]);
  return [...groups.entries()].map(([taskId, items]) => ({
    taskId,
    conflicts: items,
    allowed: items.reduce<RescheduleAction[]>(
      (acc, c) => acc.filter((a) => c.allowed_actions.includes(a)),
      [...items[0].allowed_actions],
    ),
  }));
}

export type KeepVariant = "dependency" | "nonWorkingDay" | "overCapacity" | "generic";

/** Which consequence the "keep pin" option carries; the dependency break is the most severe, so it wins. */
export function keepVariant(conflicts: readonly PinConflict[]): KeepVariant {
  const codes = new Set(conflicts.map((c) => c.code));
  if (codes.has("pinned_dependency_conflict")) return "dependency";
  if (codes.has("pinned_non_working_day")) return "nonWorkingDay";
  if (codes.has("pinned_over_capacity")) return "overCapacity";
  return "generic";
}

/** Conflicts whose pin stays in place under the current choices. */
export function keptConflicts(conflicts: readonly PinConflict[], choices: Choices) {
  return conflicts.filter((c) => (choices[c.task_id] ?? c.resolution) === "keep");
}

export type ChangeRow = TaskDateChange & { kind: "moved" | "added" | "removed" };

/** Tasks whose dates move, earliest new date first; unchanged rows are dropped. */
export function changeRows(changes: readonly TaskDateChange[]): ChangeRow[] {
  return changes
    .filter((c) => c.before_start !== c.after_start || c.before_end !== c.after_end)
    .map<ChangeRow>((c) => ({
      ...c,
      kind: c.before_start === null ? "added" : c.after_start === null ? "removed" : "moved",
    }))
    .sort((a, b) => (a.after_start ?? "9999").localeCompare(b.after_start ?? "9999") || a.task_id - b.task_id);
}
