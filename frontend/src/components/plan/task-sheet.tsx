"use client";

import {
  CalendarArrowUpIcon,
  CheckIcon,
  MinusIcon,
  PencilIcon,
  PinIcon,
  PinOffIcon,
  PlusIcon,
  SquareIcon,
  Trash2Icon,
  UndoIcon,
  XIcon,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { useId, useState } from "react";
import { cn } from "cn";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Spinner } from "@/components/ui/spinner";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { useApiErrorMessage } from "@/hooks/use-api-error-message";
import { criteriaLines } from "@/lib/plan/criteria";
import { localToday, maxDate } from "@/lib/plan/dates";
import type { PlanView, TaskView } from "@/lib/plan/plan-view";
import { quarterRange } from "@/lib/plan/quarter";
import {
  dependencyCandidates,
  emptyTaskForm,
  HOURS_STEP,
  MAX_HOURS,
  sizeHint,
  type TaskForm,
  type TaskFormErrors,
  taskToForm,
  validateTaskForm,
} from "@/lib/plan/task-form";

import { ObjectiveCode } from "./plan-bits";
import { type SheetState, usePlanData } from "./plan-data";
import { useTaskDialogs } from "./task-dialogs";
import { usePlanFormat } from "./use-plan-format";
import { TaskActionError, useTaskActions } from "./use-task-actions";

export { criteriaLines as criteriaItems } from "@/lib/plan/criteria";

const SHEET_CLASS = "overflow-y-auto data-[side=right]:w-full data-[side=right]:sm:max-w-[460px]";

/** Status column: late/buffer from the schedule plus the user's own changes. */
export function ScheduleBadges({ view, compact = false }: { view: TaskView; compact?: boolean }) {
  const t = useTranslations("plan.tasks");
  const fmt = usePlanFormat();
  return (
    <>
      {view.done && (
        <Badge variant="outline" className="border-success/40 bg-success-muted font-normal text-success">
          {t("badgeDone")}
        </Badge>
      )}
      {view.pinned && !view.done && (
        <Badge variant="outline" className="gap-1 font-normal">
          <PinIcon aria-hidden />
          {view.start ? t("badgePinned", { date: fmt.dayMonth(view.start) }) : t("badgePinnedShort")}
        </Badge>
      )}
      {view.late && (
        <Badge variant="outline" className="border-destructive/40 bg-destructive/10 font-normal text-foreground">
          {t("late")}
        </Badge>
      )}
      {view.scheduled?.uses_buffer && !view.done && (
        <Badge variant="outline" className="border-warning/40 bg-warning-muted font-normal text-warning">
          {t("inBuffer")}
        </Badge>
      )}
      {!compact && view.isNew && (
        <Badge variant="secondary" className="font-normal">
          {t("badgeNew")}
        </Badge>
      )}
      {!compact && !view.isNew && view.task.user_edited && (
        <Badge variant="outline" className="border-dashed font-normal">
          {t("badgeEdited")}
        </Badge>
      )}
      {view.unplaced && (
        <Badge variant="outline" className="border-dashed font-normal text-muted-foreground">
          {t("badgeUnplaced")}
        </Badge>
      )}
    </>
  );
}

export function TaskSheet({ plan }: { plan: PlanView }) {
  const t = useTranslations("plan.tasks");
  const { sheet, closeSheet } = usePlanData();
  const taskId = sheet.mode === "view" || sheet.mode === "edit" ? sheet.taskId : null;
  const view = taskId === null ? undefined : plan.tasks.get(taskId);
  const open = sheet.mode === "new" || view !== undefined;

  return (
    <Sheet open={open} onOpenChange={(next) => !next && closeSheet()}>
      <SheetContent side="right" closeLabel={t("close")} className={SHEET_CLASS}>
        {sheet.mode === "view" && view && <TaskDetails plan={plan} view={view} />}
        {(sheet.mode === "edit" || sheet.mode === "new") && (
          <TaskEditor key={editorKey(sheet)} plan={plan} view={view ?? null} krId={sheet.mode === "new" ? sheet.krId : (view?.task.key_result_id ?? 0)} />
        )}
      </SheetContent>
    </Sheet>
  );
}

function editorKey(sheet: SheetState) {
  return sheet.mode === "new" ? `new-${sheet.krId}` : sheet.mode === "edit" ? `edit-${sheet.taskId}` : "none";
}

function SheetHead({ plan, view, krId }: { plan: PlanView; view: TaskView | null; krId: number }) {
  const kr = plan.objectives.flatMap((o) => o.krs).find((k) => k.kr.id === krId);
  const objectiveIndex = view?.objectiveIndex ?? plan.objectives.findIndex((o) => o.krs.some((k) => k.kr.id === krId));
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
      {objectiveIndex >= 0 && <ObjectiveCode index={objectiveIndex} />}
      {view && <span className="font-mono">{view.code}</span>}
      <span className="basis-full truncate" title={kr?.kr.text}>
        {kr?.code} {kr ? `· ${kr.kr.text}` : ""}
      </span>
    </div>
  );
}

function TaskDetails({ plan, view }: { plan: PlanView; view: TaskView }) {
  const t = useTranslations("plan.tasks");
  const ta = useTranslations("plan.actions");
  const fmt = usePlanFormat();
  const { selectTask, editTask } = usePlanData();
  const actions = useTaskActions();
  const dialogs = useTaskDialogs();

  return (
    <>
      <SheetHeader className="gap-2">
        <SheetHead plan={plan} view={view} krId={view.task.key_result_id} />
        <SheetTitle className={cn("text-lg leading-snug", view.done && "text-muted-foreground line-through")}>{view.task.title}</SheetTitle>
        <SheetDescription className="sr-only">{t("sheetDescription")}</SheetDescription>
        <div className="flex flex-wrap gap-1.5">
          <ScheduleBadges view={view} />
        </div>
        <div className="flex flex-wrap gap-2 pt-1">
          <Button size="sm" onClick={() => editTask(view.task.id)}>
            <PencilIcon data-icon="inline-start" />
            {ta("edit")}
          </Button>
          <Button size="sm" variant="outline" onClick={() => void actions.setDone(view, !view.done)}>
            {view.done ? <UndoIcon data-icon="inline-start" /> : <CheckIcon data-icon="inline-start" />}
            {view.done ? ta("markTodo") : ta("markDone")}
          </Button>
          {!view.done && (
            <Button size="sm" variant="outline" onClick={() => dialogs.askMove(view)}>
              <CalendarArrowUpIcon data-icon="inline-start" />
              {ta("move")}
            </Button>
          )}
          {!view.done && view.pinned && (
            <Button size="sm" variant="outline" onClick={() => void actions.unpin(view)}>
              <PinOffIcon data-icon="inline-start" />
              {ta("unpin")}
            </Button>
          )}
        </div>
      </SheetHeader>

      <div className="flex flex-col gap-5 px-4 pb-6 text-sm">
        <dl className="grid grid-cols-3 gap-2">
          <SheetMetric label={t("estimate")} value={fmt.hours(view.task.estimate_minutes)} />
          <SheetMetric label={t("start")} value={view.start ? fmt.date(view.start) : "—"} />
          <SheetMetric label={t("end")} value={view.end ? fmt.date(view.end) : "—"} />
        </dl>

        {view.task.description && (
          <section className="flex flex-col gap-1.5">
            <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{t("description")}</h3>
            <p className="whitespace-pre-line">{view.task.description}</p>
          </section>
        )}

        <section className="flex flex-col gap-1.5">
          <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{t("doneCriteria")}</h3>
          <ul className="flex flex-col gap-1.5">
            {criteriaLines(view.task.done_criteria).map((line) => (
              <li key={line} className="flex items-start gap-2">
                {view.done ? (
                  <CheckIcon className="mt-0.5 size-4 shrink-0 text-success" aria-hidden />
                ) : (
                  <SquareIcon className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden />
                )}
                {line}
              </li>
            ))}
          </ul>
        </section>

        {(view.dependsOn.length > 0 || view.blocks.length > 0) && (
          <section className="flex flex-col gap-2">
            <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{t("dependencies")}</h3>
            <DependencyList label={t("dependsOn")} ids={view.dependsOn} plan={plan} onSelect={selectTask} />
            <DependencyList label={t("blocks")} ids={view.blocks} plan={plan} onSelect={selectTask} />
          </section>
        )}

        <Separator />

        <section className="flex flex-col gap-1.5">
          <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{t("allocations")}</h3>
          {view.days.length > 0 ? (
            <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
              {view.days.map((a) => (
                <li key={a.date} className="flex justify-between px-3 py-1.5">
                  <span>
                    {fmt.weekday(a.date)} {fmt.date(a.date)}
                  </span>
                  <span className="tabular-nums">{fmt.hours(a.minutes)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted-foreground">
              {view.late ? t("lateExplain") : view.unplaced ? t("unplacedExplain") : t("noAllocations")}
            </p>
          )}
        </section>
      </div>
    </>
  );
}

type FieldErrors = TaskFormErrors & { deps?: string; general?: string };

function TaskEditor({ plan, view, krId }: { plan: PlanView; view: TaskView | null; krId: number }) {
  const t = useTranslations("plan.editor");
  const fmt = usePlanFormat();
  const id = useId();
  const { ref, closeSheet, selectTask } = usePlanData();
  const actions = useTaskActions();
  const dialogs = useTaskDialogs();
  const errorMessage = useApiErrorMessage();
  const range = quarterRange(ref);
  const defaultDate = maxDate(range.start, localToday());
  const [form, setForm] = useState<TaskForm>(() =>
    view ? taskToForm(view.task, view.start, defaultDate) : emptyTaskForm(defaultDate),
  );
  const [errors, setErrors] = useState<FieldErrors>({});
  const [saving, setSaving] = useState(false);
  const candidates = dependencyCandidates(view?.task.id ?? null, plan.tasks);
  const addable = [...plan.tasks.values()].filter((t) => candidates.has(t.task.id) && !form.dependsOn.includes(t.task.id));
  const hint = sizeHint(form.hours);

  const set = <K extends keyof TaskForm>(key: K, value: TaskForm[K]) => setForm((f) => ({ ...f, [key]: value }));

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const found = validateTaskForm(form);
    setErrors(found);
    if (Object.keys(found).length > 0) {
      document.getElementById(`${id}-${Object.keys(found)[0]}`)?.focus();
      return;
    }
    setSaving(true);
    try {
      const savedId = await actions.save(view, krId, form);
      selectTask(savedId);
    } catch (error) {
      const code = error instanceof TaskActionError ? error.code : "";
      const message = errorMessage(error);
      if (code.startsWith("dependency")) setErrors({ deps: message });
      else if (code.startsWith("pin_") || code === "task_not_scheduled") setErrors({ pinDate: "range", general: message });
      else setErrors({ general: message });
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={(e) => void submit(e)} className="flex min-h-full flex-col" noValidate>
      <SheetHeader className="gap-2">
        <SheetHead plan={plan} view={view} krId={krId} />
        <SheetTitle className="text-lg">{view ? t("editTitle") : t("newTitle")}</SheetTitle>
        <SheetDescription>{t("stagedNote")}</SheetDescription>
      </SheetHeader>

      <div className="flex flex-col gap-5 px-4 pb-4">
        {errors.general && (
          <Alert variant="destructive" role="alert">
            <AlertDescription className="text-foreground">{errors.general}</AlertDescription>
          </Alert>
        )}

        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${id}-title`}>{t("name")}</Label>
          <Input
            id={`${id}-title`}
            value={form.title}
            onChange={(e) => set("title", e.target.value)}
            aria-invalid={errors.title ? true : undefined}
            aria-describedby={errors.title ? `${id}-title-error` : undefined}
            maxLength={200}
            autoFocus
          />
          {errors.title && (
            <p id={`${id}-title-error`} className="text-xs text-destructive">
              {t("nameRequired")}
            </p>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${id}-hours`}>{t("estimate")}</Label>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="icon"
              className="max-md:size-10"
              aria-label={t("less")}
              onClick={() => set("hours", Math.max(HOURS_STEP, form.hours - HOURS_STEP))}
            >
              <MinusIcon />
            </Button>
            <Input
              id={`${id}-hours`}
              type="number"
              inputMode="decimal"
              min={HOURS_STEP}
              max={MAX_HOURS}
              step={HOURS_STEP}
              value={Number.isFinite(form.hours) ? form.hours : ""}
              onChange={(e) => set("hours", e.target.valueAsNumber)}
              className="w-20 text-right tabular-nums"
              aria-invalid={errors.hours ? true : undefined}
              aria-describedby={`${id}-hours-hint`}
            />
            <span className="text-muted-foreground">{t("hoursUnit")}</span>
            <Button
              type="button"
              variant="outline"
              size="icon"
              className="max-md:size-10"
              aria-label={t("more")}
              onClick={() => set("hours", Math.min(MAX_HOURS, form.hours + HOURS_STEP))}
            >
              <PlusIcon />
            </Button>
          </div>
          <p id={`${id}-hours-hint`} className={cn("text-xs", errors.hours ? "text-destructive" : "text-muted-foreground")}>
            {errors.hours ? t("hoursRange", { max: MAX_HOURS }) : hint === "split" ? t("hintSplit") : hint === "small" ? t("hintSmall") : t("hintOk")}
          </p>
        </div>

        {view && (
          <Label className="flex items-center gap-2 font-normal">
            <Checkbox checked={form.done} onCheckedChange={(v) => set("done", v === true)} />
            {t("done")}
          </Label>
        )}

        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${id}-description`}>{t("description")}</Label>
          <Textarea id={`${id}-description`} value={form.description} onChange={(e) => set("description", e.target.value)} rows={3} maxLength={4000} />
        </div>

        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1.5 text-sm font-medium">{t("criteria")}</legend>
          {form.criteria.map((line, i) => (
            <div key={i} className="flex items-center gap-2">
              <Input
                value={line}
                onChange={(e) => set("criteria", form.criteria.map((c, j) => (j === i ? e.target.value : c)))}
                aria-label={t("criterionN", { n: i + 1 })}
              />
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                className="max-md:size-10"
                aria-label={t("removeCriterion", { n: i + 1 })}
                onClick={() => set("criteria", form.criteria.length > 1 ? form.criteria.filter((_, j) => j !== i) : [""])}
              >
                <XIcon />
              </Button>
            </div>
          ))}
          <Button type="button" variant="ghost" size="sm" className="w-fit" onClick={() => set("criteria", [...form.criteria, ""])}>
            <PlusIcon data-icon="inline-start" />
            {t("addCriterion")}
          </Button>
        </fieldset>

        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1.5 text-sm font-medium">{t("dependencies")}</legend>
          {form.dependsOn.length > 0 && (
            <ul className="flex flex-wrap gap-1.5">
              {form.dependsOn.map((depId) => {
                const dep = plan.tasks.get(depId);
                return (
                  <li key={depId}>
                    <Badge variant="secondary" className="gap-1 pr-1 font-normal">
                      <span className="font-mono">{dep?.code ?? `#${depId}`}</span>
                      <span className="max-w-40 truncate">{dep?.task.title}</span>
                      <button
                        type="button"
                        onClick={() => set("dependsOn", form.dependsOn.filter((d) => d !== depId))}
                        className="rounded-full p-0.5 hover:bg-background focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                        aria-label={t("removeDependency", { code: dep?.code ?? "" })}
                      >
                        <XIcon className="size-3" aria-hidden />
                      </button>
                    </Badge>
                  </li>
                );
              })}
            </ul>
          )}
          <Select value="" onValueChange={(v) => set("dependsOn", [...form.dependsOn, Number(v)])}>
            <SelectTrigger className="w-full" aria-label={t("addDependency")} aria-invalid={errors.deps ? true : undefined} disabled={addable.length === 0}>
              <SelectValue placeholder={t("addDependency")} />
            </SelectTrigger>
            <SelectContent>
              {addable.map((dep) => (
                <SelectItem key={dep.task.id} value={String(dep.task.id)}>
                  <span className="font-mono text-xs text-muted-foreground">{dep.code}</span> {dep.task.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.deps && (
            <p className="text-xs text-destructive" role="alert">
              {errors.deps}
            </p>
          )}
        </fieldset>

        {!form.done && (
          <div className="flex flex-col gap-2">
            <Label className="flex items-center gap-2 font-medium">
              <Switch checked={form.pinned} onCheckedChange={(v) => set("pinned", v)} />
              {t("pin")}
            </Label>
            {form.pinned && (
              <div className="flex flex-col gap-1.5 pl-10">
                <Label htmlFor={`${id}-pinDate`} className="font-normal text-muted-foreground">
                  {t("pinDate")}
                </Label>
                <Input
                  id={`${id}-pinDate`}
                  type="date"
                  value={form.pinDate}
                  min={defaultDate}
                  max={range.end}
                  onChange={(e) => set("pinDate", e.target.value)}
                  aria-invalid={errors.pinDate ? true : undefined}
                  className="w-44"
                />
                <p className="text-xs text-muted-foreground">
                  {t("pinHint", { hours: fmt.hours(Math.round(form.hours * 60)) })}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      <SheetFooter className="sticky bottom-0 flex-row flex-wrap items-center border-t border-border bg-popover">
        {view && (
          <Button
            type="button"
            variant="outline"
            className="border-destructive/40 text-destructive hover:bg-destructive/10 hover:text-destructive"
            onClick={() => {
              closeSheet();
              dialogs.askDelete(view);
            }}
          >
            <Trash2Icon data-icon="inline-start" />
            {t("delete")}
          </Button>
        )}
        <span className="flex-1" />
        <Button type="button" variant="outline" onClick={() => (view ? selectTask(view.task.id) : closeSheet())} disabled={saving}>
          {t("cancel")}
        </Button>
        <Button type="submit" disabled={saving}>
          {saving && <Spinner data-icon="inline-start" />}
          {view ? t("save") : t("create")}
        </Button>
      </SheetFooter>
    </form>
  );
}

function SheetMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col rounded-lg bg-muted/60 px-2.5 py-2">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="font-medium tabular-nums">{value}</dd>
    </div>
  );
}

function DependencyList({
  label,
  ids,
  plan,
  onSelect,
}: {
  label: string;
  ids: number[];
  plan: PlanView;
  onSelect: (taskId: number) => void;
}) {
  if (ids.length === 0) return null;
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <ul className="flex flex-col gap-1">
        {ids.map((id) => {
          const dep = plan.tasks.get(id);
          if (!dep) return null;
          return (
            <li key={id}>
              <button
                type="button"
                onClick={() => onSelect(id)}
                className="flex w-full items-center gap-2 rounded-md px-2 py-1 text-left hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              >
                <span className="font-mono text-xs text-muted-foreground">{dep.code}</span>
                <span className="truncate">{dep.task.title}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
