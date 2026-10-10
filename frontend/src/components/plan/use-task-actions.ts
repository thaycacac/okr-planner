"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useMemo } from "react";
import { toast } from "sonner";

import { useApiErrorMessage } from "@/hooks/use-api-error-message";
import { api } from "@/lib/api/client";
import { errorDetail, type PinnedDay, type TaskOut } from "@/lib/api/types";
import type { TaskView } from "@/lib/plan/plan-view";
import { createPayload, pinChange, type TaskForm, updatePayload } from "@/lib/plan/task-form";

import { usePlanData } from "./plan-data";
import { usePlanFormat } from "./use-plan-format";

const UNDO_MS = 8000;

type Result<T> = { data?: T; error?: unknown; response: Response };

export class TaskActionError extends Error {
  constructor(
    readonly code: string,
    message: string,
  ) {
    super(message);
  }
}

function unwrap<T>(result: Result<T>): T {
  if (result.data !== undefined && result.response.ok) return result.data;
  if (result.response.ok) return undefined as T;
  const detail = errorDetail(result.error);
  throw new TaskActionError(detail?.code ?? `http_${result.response.status}`, detail?.message ?? "");
}

async function restorePin(taskId: number, previous: PinnedDay[] | null) {
  if (previous && previous.length > 0) {
    unwrap(await api.PUT("/tasks/{task_id}/pin", { params: { path: { task_id: taskId } }, body: { allocations: previous } }));
  } else {
    unwrap(await api.DELETE("/tasks/{task_id}/pin", { params: { path: { task_id: taskId } } }));
  }
}

async function recreate(task: TaskOut) {
  const created = unwrap(
    await api.POST("/key-results/{kr_id}/tasks", {
      params: { path: { kr_id: task.key_result_id } },
      body: {
        title: task.title,
        description: task.description,
        done_criteria: task.done_criteria,
        estimate_minutes: task.estimate_minutes,
        depends_on: task.depends_on,
        position: task.position,
      },
    }),
  );
  if (task.status !== "todo") {
    unwrap(await api.PATCH("/tasks/{task_id}", { params: { path: { task_id: created.id } }, body: { status: task.status } }));
  }
  if (task.pinned && task.pinned_allocations.length > 0) await restorePin(created.id, task.pinned_allocations);
}

export function useTaskActions() {
  const t = useTranslations("plan.actions");
  const fmt = usePlanFormat();
  const router = useRouter();
  const errorMessage = useApiErrorMessage();
  const { refresh, slug } = usePlanData();

  return useMemo(() => {
    const path = (taskId: number) => ({ params: { path: { task_id: taskId } } });

    async function run<T>(work: () => Promise<T>): Promise<T | null> {
      try {
        const value = await work();
        await refresh();
        return value;
      } catch (error) {
        toast.error(errorMessage(error));
        await refresh();
        return null;
      }
    }

    function undoable(message: string, undo: () => Promise<unknown>, extra?: { label: string; onClick: () => void }) {
      toast(message, {
        duration: UNDO_MS,
        action: { label: t("undo"), onClick: () => void run(undo) },
        cancel: extra,
      });
    }

    return {
      async setDone(view: TaskView, done: boolean) {
        const previous = view.task.status;
        const ok = await run(async () =>
          unwrap(await api.PATCH("/tasks/{task_id}", { ...path(view.task.id), body: { status: done ? "done" : "todo" } })),
        );
        if (ok) {
          undoable(done ? t("doneToast", { code: view.code }) : t("undoneToast", { code: view.code }), async () =>
            unwrap(await api.PATCH("/tasks/{task_id}", { ...path(view.task.id), body: { status: previous } })),
          );
        }
      },

      async pinHere(view: TaskView) {
        const ok = await run(async () => unwrap(await api.PUT("/tasks/{task_id}/pin", { ...path(view.task.id), body: {} })));
        if (ok) undoable(t("pinnedToast", { code: view.code }), () => restorePin(view.task.id, null));
      },

      async unpin(view: TaskView) {
        const previous = view.task.pinned_allocations;
        const ok = await run(async () => unwrap(await api.DELETE("/tasks/{task_id}/pin", path(view.task.id))));
        if (ok) undoable(t("unpinnedToast", { code: view.code }), () => restorePin(view.task.id, previous));
      },

      /** Moves the task to start on `date` and pins it there; `overBy` is how far that day now overflows. */
      async moveTo(view: TaskView, date: string, overBy = 0) {
        const previous = view.task.pinned ? view.task.pinned_allocations : null;
        const ok = await run(async () =>
          unwrap(await api.PUT("/tasks/{task_id}/pin", { ...path(view.task.id), body: { start_date: date } })),
        );
        if (!ok) return false;
        const message =
          overBy > 0
            ? t("movedOverToast", { code: view.code, date: fmt.dayMonth(date), over: fmt.hours(overBy) })
            : t("movedToast", { code: view.code, date: fmt.dayMonth(date) });
        undoable(message, () => restorePin(view.task.id, previous), {
          label: t("rescheduleNow"),
          onClick: () => window.dispatchEvent(new Event(RESCHEDULE_EVENT)),
        });
        return true;
      },

      async duplicate(view: TaskView) {
        const copy = await run(async () =>
          unwrap(
            await api.POST("/key-results/{kr_id}/tasks", {
              params: { path: { kr_id: view.task.key_result_id } },
              body: {
                title: t("copyTitle", { title: view.task.title }),
                description: view.task.description,
                done_criteria: view.task.done_criteria,
                estimate_minutes: view.task.estimate_minutes,
                depends_on: view.task.depends_on,
                position: view.task.position + 1,
              },
            }),
          ),
        );
        if (copy) {
          undoable(t("duplicatedToast", { code: view.code }), async () =>
            unwrap(await api.DELETE("/tasks/{task_id}", path(copy.id))),
          );
        }
        return copy;
      },

      async remove(view: TaskView, withDependents = false) {
        const snapshot = view.task;
        const ok = await run(async () => {
          unwrap(
            await api.DELETE("/tasks/{task_id}", {
              params: { path: { task_id: view.task.id }, query: { with_dependents: withDependents } },
            }),
          );
          return true;
        });
        if (!ok) return false;
        if (withDependents || view.blocks.length > 0) toast(t("deletedToast", { code: view.code }));
        else undoable(t("deletedToast", { code: view.code }), () => recreate(snapshot));
        return true;
      },

      /** Creates or updates a task from the sheet form; returns the task id or throws for inline errors. */
      async save(view: TaskView | null, krId: number, form: TaskForm) {
        let task: TaskOut;
        if (view) {
          const body = updatePayload(view.task, form);
          task =
            Object.keys(body).length > 0
              ? unwrap(await api.PATCH("/tasks/{task_id}", { ...path(view.task.id), body }))
              : view.task;
        } else {
          task = unwrap(await api.POST("/key-results/{kr_id}/tasks", { params: { path: { kr_id: krId } }, body: createPayload(form) }));
        }
        const pin = pinChange(view?.task ?? null, view?.start ?? null, form);
        try {
          if (pin?.kind === "pin") {
            unwrap(await api.PUT("/tasks/{task_id}/pin", { ...path(task.id), body: { start_date: pin.date } }));
          } else if (pin?.kind === "unpin") {
            unwrap(await api.DELETE("/tasks/{task_id}/pin", path(task.id)));
          }
        } finally {
          await refresh();
        }
        toast.success(view ? t("savedToast") : t("createdToast"));
        return task.id;
      },

      openOptions() {
        router.push(`/q/${slug}/options`);
      },
    };
  }, [t, fmt, router, errorMessage, refresh, slug]);
}

/** Lets toasts and banners anywhere in the quarter start the reschedule flow. */
export const RESCHEDULE_EVENT = "plan:reschedule";
