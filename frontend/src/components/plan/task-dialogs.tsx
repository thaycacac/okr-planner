"use client";

import {
  CheckIcon,
  CopyIcon,
  EllipsisIcon,
  PencilIcon,
  PinIcon,
  PinOffIcon,
  CalendarArrowUpIcon,
  Trash2Icon,
  UndoIcon,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { createContext, type ReactNode, useContext, useMemo, useState } from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Spinner } from "@/components/ui/spinner";
import { addDays, localToday, maxDate } from "@/lib/plan/dates";
import { calendarBlocks, dayLoads, type TaskView } from "@/lib/plan/plan-view";
import { quarterRange } from "@/lib/plan/quarter";

import { usePlanData } from "./plan-data";
import { usePlanFormat } from "./use-plan-format";
import { useTaskActions } from "./use-task-actions";

type TaskDialogsValue = { askMove: (view: TaskView) => void; askDelete: (view: TaskView) => void };

const TaskDialogsContext = createContext<TaskDialogsValue | null>(null);

export function useTaskDialogs() {
  const value = useContext(TaskDialogsContext);
  if (!value) throw new Error("useTaskDialogs must be used inside TaskDialogsProvider");
  return value;
}

export function TaskDialogsProvider({ children }: { children: ReactNode }) {
  const [moving, setMoving] = useState<TaskView | null>(null);
  const [deleting, setDeleting] = useState<TaskView | null>(null);
  const actions = useTaskActions();
  const value = useMemo<TaskDialogsValue>(
    () => ({
      askMove: setMoving,
      askDelete: (view) => {
        // Nothing waits on the task: delete straight away, the toast offers undo.
        if (view.blocks.length === 0) void actions.remove(view);
        else setDeleting(view);
      },
    }),
    [actions],
  );
  return (
    <TaskDialogsContext value={value}>
      {children}
      <MoveDialog view={moving} onClose={() => setMoving(null)} />
      <DeleteDialog view={deleting} onClose={() => setDeleting(null)} />
    </TaskDialogsContext>
  );
}

/** Minutes already planned on a day once `view` moves there, so the dialog can warn before saving. */
function useDayLoad() {
  const { view, state } = usePlanData();
  return useMemo(() => {
    const loads = view ? dayLoads(calendarBlocks(view)) : new Map<string, number>();
    const days = new Map((state.status === "ready" ? (state.data.schedule?.days ?? []) : []).map((d) => [d.date, d]));
    return { loads, days };
  }, [view, state]);
}

function MoveDialog({ view, onClose }: { view: TaskView | null; onClose: () => void }) {
  const t = useTranslations("plan.move");
  const fmt = usePlanFormat();
  const { ref } = usePlanData();
  const actions = useTaskActions();
  const { loads, days } = useDayLoad();
  const range = quarterRange(ref);
  const earliest = maxDate(range.start, localToday());
  const [date, setDate] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const chosen = date || (view?.start ? maxDate(view.start, earliest) : earliest);
  const info = days.get(chosen);
  const own = view?.days.filter((d) => d.date === chosen).reduce((s, d) => s + d.minutes, 0) ?? 0;
  const firstDay = Math.min(view?.task.estimate_minutes ?? 0, info?.capacity_minutes ?? 0);
  const after = (loads.get(chosen) ?? 0) - own + firstDay;
  const capacity = info?.capacity_minutes ?? 0;
  const off = info?.off_reason ?? null;

  async function submit() {
    if (!view) return;
    setBusy(true);
    const ok = await actions.moveTo(view, chosen, Math.max(0, after - capacity));
    setBusy(false);
    if (ok) close();
  }

  function close() {
    setDate("");
    onClose();
  }

  return (
    <Dialog open={view !== null} onOpenChange={(open) => !open && close()}>
      <DialogContent closeLabel={t("close")} className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription>
            {view && (
              <>
                <span className="mr-1 font-mono">{view.code}</span>
                {view.task.title} · {fmt.hours(view.task.estimate_minutes)}
              </>
            )}
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-2">
          <Label htmlFor="move-date">{t("date")}</Label>
          <Input
            id="move-date"
            type="date"
            value={chosen}
            min={earliest}
            max={range.end}
            onChange={(e) => setDate(e.target.value)}
            aria-describedby="move-date-hint"
          />
          <p id="move-date-hint" className="text-xs text-muted-foreground" aria-live="polite">
            {off
              ? t("offDay", { reason: t(`off.${off}`) })
              : info
                ? after > capacity
                  ? t("over", { load: fmt.hours(after), capacity: fmt.hours(capacity) })
                  : t("fits", { load: fmt.hours(after), capacity: fmt.hours(capacity) })
                : null}
          </p>
          <p className="text-xs text-muted-foreground">{t("pinNote")}</p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={close} disabled={busy}>
            {t("cancel")}
          </Button>
          <Button onClick={() => void submit()} disabled={busy || off !== null || chosen < earliest || chosen > range.end}>
            {busy && <Spinner data-icon="inline-start" />}
            {t("submit")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function dependentsOf(view: TaskView, tasks: ReadonlyMap<number, TaskView>) {
  const found = new Set<number>();
  const queue = [...view.blocks];
  while (queue.length) {
    const id = queue.shift()!;
    if (found.has(id)) continue;
    found.add(id);
    queue.push(...(tasks.get(id)?.blocks ?? []));
  }
  return [...found].map((id) => tasks.get(id)).filter((t): t is TaskView => t !== undefined);
}

function DeleteDialog({ view, onClose }: { view: TaskView | null; onClose: () => void }) {
  const t = useTranslations("plan.delete");
  const fmt = usePlanFormat();
  const plan = usePlanData();
  const actions = useTaskActions();
  const [mode, setMode] = useState<"unlink" | "cascade">("unlink");
  const dependents = view && plan.view ? dependentsOf(view, plan.view.tasks) : [];
  const cascadeMinutes = (view?.task.estimate_minutes ?? 0) + dependents.reduce((s, d) => s + d.task.estimate_minutes, 0);

  function close() {
    setMode("unlink");
    onClose();
  }

  return (
    <AlertDialog open={view !== null} onOpenChange={(open) => !open && close()}>
      <AlertDialogContent className="sm:max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle>{t("title", { code: view?.code ?? "", name: view?.task.title ?? "" })}</AlertDialogTitle>
          <AlertDialogDescription>
            {t("body", { count: dependents.length, codes: dependents.map((d) => d.code).join(", ") })}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <RadioGroup value={mode} onValueChange={(v) => setMode(v as typeof mode)} className="gap-2">
          <Label className="flex items-start gap-2 font-normal">
            <RadioGroupItem value="unlink" className="mt-0.5" />
            {t("unlink")}
          </Label>
          <Label className="flex items-start gap-2 font-normal">
            <RadioGroupItem value="cascade" className="mt-0.5" />
            {t("cascade", { count: dependents.length + 1, hours: fmt.hours(cascadeMinutes) })}
          </Label>
        </RadioGroup>
        <AlertDialogFooter>
          <AlertDialogCancel>{t("cancel")}</AlertDialogCancel>
          <AlertDialogAction
            variant="destructive"
            onClick={() => {
              if (view) void actions.remove(view, mode === "cascade");
              close();
            }}
          >
            {t("confirm")}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

/** Row "⋯" menu; every drag-and-drop move has this keyboard path too. */
export function TaskMenu({ view, align = "end" }: { view: TaskView; align?: "start" | "end" }) {
  const t = useTranslations("plan.actions");
  const { editTask, ref } = usePlanData();
  const actions = useTaskActions();
  const dialogs = useTaskDialogs();
  const range = quarterRange(ref);
  const ended = addDays(range.end, 1) <= localToday();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon-sm" className="max-md:size-10" aria-label={t("menu", { code: view.code })}>
          <EllipsisIcon />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align={align} className="min-w-52">
        <DropdownMenuItem onSelect={() => editTask(view.task.id)}>
          <PencilIcon />
          {t("edit")}
        </DropdownMenuItem>
        {!view.done && !ended && (
          <DropdownMenuItem onSelect={() => dialogs.askMove(view)}>
            <CalendarArrowUpIcon />
            {t("move")}
          </DropdownMenuItem>
        )}
        {!view.done &&
          (view.pinned ? (
            <DropdownMenuItem onSelect={() => void actions.unpin(view)}>
              <PinOffIcon />
              {t("unpin")}
            </DropdownMenuItem>
          ) : (
            view.days.length > 0 && (
              <DropdownMenuItem onSelect={() => void actions.pinHere(view)}>
                <PinIcon />
                {t("pinHere")}
              </DropdownMenuItem>
            )
          ))}
        <DropdownMenuItem onSelect={() => void actions.setDone(view, !view.done)}>
          {view.done ? <UndoIcon /> : <CheckIcon />}
          {view.done ? t("markTodo") : t("markDone")}
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => void actions.duplicate(view)}>
          <CopyIcon />
          {t("duplicate")}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem variant="destructive" onSelect={() => dialogs.askDelete(view)}>
          <Trash2Icon />
          {t("delete")}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}