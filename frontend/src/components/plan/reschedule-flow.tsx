"use client";

import { ArrowRightIcon, PinIcon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useApiErrorMessage } from "@/hooks/use-api-error-message";
import { api } from "@/lib/api/client";
import { errorDetail, type PinConflict, type RescheduleResult } from "@/lib/api/types";
import { RESCHEDULE_QUERY } from "@/lib/plan/calendar-impact";
import {
  type Choices,
  changeRows,
  conflictsByTask,
  initialChoices,
  keepVariant,
  keptConflicts,
  toResolutions,
} from "@/lib/plan/reschedule";

import { FeasibilityBadge } from "./feasibility-panel";
import { usePlanData } from "./plan-data";
import { RESCHEDULE_EVENT, TaskActionError } from "./use-task-actions";
import { usePlanFormat } from "./use-plan-format";

const PREVIEW_ROWS = 3;

type Step =
  | { kind: "idle" }
  | { kind: "conflicts"; result: RescheduleResult; choices: Choices }
  | { kind: "preview"; result: RescheduleResult; choices: Choices; conflicts: RescheduleResult | null };

type RescheduleValue = { start: () => void; busy: boolean };

const RescheduleContext = createContext<RescheduleValue | null>(null);

export function useReschedule() {
  const value = useContext(RescheduleContext);
  if (!value) throw new Error("useReschedule must be used inside RescheduleProvider");
  return value;
}

export function RescheduleProvider({ children }: { children: ReactNode }) {
  const t = useTranslations("plan.reschedule");
  const errorMessage = useApiErrorMessage();
  const { state, refresh, slug } = usePlanData();
  const quarterId = state.status === "ready" ? state.data.summary?.id : undefined;
  const router = useRouter();
  const [step, setStep] = useState<Step>({ kind: "idle" });
  const [busy, setBusy] = useState(false);
  const retryRef = useRef<{
    preview: (choices: Choices, conflicts: RescheduleResult | null) => Promise<void>;
    apply: (choices: Choices) => Promise<void>;
  } | null>(null);

  const call = useCallback(
    async (choices: Choices, dryRun: boolean) => {
      if (quarterId === undefined) return null;
      const { data, error, response } = await api.POST("/quarters/{quarter_id}/reschedule", {
        params: { path: { quarter_id: quarterId } },
        body: { dry_run: dryRun, resolutions: toResolutions(choices) },
      });
      if (!data) {
        const detail = errorDetail(error);
        throw new TaskActionError(detail?.code ?? `http_${response.status}`, detail?.message ?? "");
      }
      return data;
    },
    [quarterId],
  );

  const fail = useCallback(
    (error: unknown, retry: () => void) => {
      toast.error(t("failed"), {
        description: errorMessage(error),
        action: { label: t("retry"), onClick: retry },
      });
    },
    [t, errorMessage],
  );

  const preview = useCallback(
    async (choices: Choices, conflicts: RescheduleResult | null) => {
      setBusy(true);
      try {
        const result = await call(choices, true);
        if (!result) return;
        if (result.unresolved_task_ids.length > 0) {
          setStep({ kind: "conflicts", result, choices: { ...initialChoices(result.conflicts), ...choices } });
        } else {
          setStep({ kind: "preview", result, choices, conflicts });
        }
      } catch (error) {
        fail(error, () => void retryRef.current?.preview(choices, conflicts));
      } finally {
        setBusy(false);
      }
    },
    [call, fail],
  );

  const start = useCallback(() => {
    if (busy) return;
    void preview({}, null);
  }, [busy, preview]);

  const apply = useCallback(
    async (choices: Choices) => {
      setBusy(true);
      try {
        const result = await call(choices, false);
        if (!result) return;
        if (!result.applied) {
          setStep({ kind: "conflicts", result, choices: { ...initialChoices(result.conflicts), ...choices } });
          return;
        }
        setStep({ kind: "idle" });
        await refresh();
        if (result.after.status === "red") {
          toast.warning(t("appliedRed"), {
            duration: 10_000,
            action: { label: t("seeOptions"), onClick: () => router.push(`/q/${slug}/options`) },
          });
        } else {
          toast.success(t("applied"));
        }
      } catch (error) {
        fail(error, () => void retryRef.current?.apply(choices));
      } finally {
        setBusy(false);
      }
    },
    [call, fail, refresh, router, slug, t],
  );

  useEffect(() => {
    retryRef.current = { preview, apply };
  }, [preview, apply]);

  const canStart = state.status === "ready" && quarterId !== undefined && state.data.schedule !== null;
  const autoStarted = useRef(false);
  useEffect(() => {
    if (!canStart || autoStarted.current) return;
    const params = new URLSearchParams(window.location.search);
    if (params.get(RESCHEDULE_QUERY) !== "1") return;
    const timer = window.setTimeout(() => {
      autoStarted.current = true;
      params.delete(RESCHEDULE_QUERY);
      const query = params.toString();
      router.replace(`${window.location.pathname}${query ? `?${query}` : ""}`, { scroll: false });
      start();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [canStart, router, start]);

  useEffect(() => {
    const onEvent = () => start();
    window.addEventListener(RESCHEDULE_EVENT, onEvent);
    return () => window.removeEventListener(RESCHEDULE_EVENT, onEvent);
  }, [start]);

  const value = useMemo(() => ({ start, busy }), [start, busy]);
  const close = () => !busy && setStep({ kind: "idle" });

  return (
    <RescheduleContext value={value}>
      {children}
      <ConflictDialog
        step={step.kind === "conflicts" ? step : null}
        busy={busy}
        onClose={close}
        onChange={(choices) => step.kind === "conflicts" && setStep({ ...step, choices })}
        onContinue={(choices) => step.kind === "conflicts" && void preview(choices, step.result)}
      />
      <PreviewDialog
        step={step.kind === "preview" ? step : null}
        busy={busy}
        slug={slug}
        onClose={close}
        onBack={() => {
          if (step.kind === "preview") {
            setStep({ kind: "conflicts", result: step.conflicts ?? step.result, choices: step.choices });
          }
        }}
        onApply={(choices) => void apply(choices)}
      />
    </RescheduleContext>
  );
}

/** "Xếp lại lịch" button with its loading note; disabled while a request is running. */
export function RescheduleButton({ size = "sm", variant = "default" }: { size?: "sm" | "default"; variant?: "default" | "outline" }) {
  const t = useTranslations("plan.reschedule");
  const { start, busy } = useReschedule();
  return (
    <Button size={size} variant={variant} onClick={start} disabled={busy} aria-busy={busy}>
      {busy && <Spinner data-icon="inline-start" />}
      {busy ? t("running") : t("button")}
    </Button>
  );
}

function useConflictParams() {
  const fmt = usePlanFormat();
  const { view } = usePlanData();
  return (c: PinConflict) => ({
    code: view?.tasks.get(c.task_id)?.code ?? `#${c.task_id}`,
    dates: c.dates.map((d) => fmt.dayMonth(d)).join(", "),
    pinned: fmt.hours(c.pinned_minutes ?? 0),
    capacity: fmt.hours(c.capacity_minutes ?? 0),
    related:
      c.related_task_ids
        .map((id) => view?.tasks.get(id)?.code)
        .filter(Boolean)
        .join(", ") || "—",
  });
}

function useConflictText() {
  const t = useTranslations("plan.reschedule.reason");
  const params = useConflictParams();
  return (c: PinConflict) => t(c.code, params(c));
}

/** Pins the user chose to keep, explaining a red status that is not caused by missing hours. */
function useKeptPinCauses() {
  const t = useTranslations("plan.reschedule.cause");
  const params = useConflictParams();
  return (result: RescheduleResult, choices: Choices) =>
    keptConflicts(result.conflicts, choices).map((c) => t(c.code, params(c)));
}

/** "Keep pin" means different things per conflict, so the label states the actual consequence. */
function useKeepLabel() {
  const t = useTranslations("plan.reschedule.keep");
  const params = useConflictParams();
  return (conflicts: readonly PinConflict[]) => {
    const variant = keepVariant(conflicts);
    if (variant === "dependency") {
      const dependency = conflicts.find((c) => c.code === "pinned_dependency_conflict")!;
      return { label: t("dependency", { related: params(dependency).related }), note: t("dependencyNote") };
    }
    return { label: t(variant), note: null };
  };
}

function ConflictDialog({
  step,
  busy,
  onClose,
  onChange,
  onContinue,
}: {
  step: { result: RescheduleResult; choices: Choices } | null;
  busy: boolean;
  onClose: () => void;
  onChange: (choices: Choices) => void;
  onContinue: (choices: Choices) => void;
}) {
  const t = useTranslations("plan.reschedule");
  const { view } = usePlanData();
  const reason = useConflictText();
  const keepLabel = useKeepLabel();
  const groups = step ? conflictsByTask(step.result.conflicts) : [];

  return (
    <Dialog open={step !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent closeLabel={t("close")} className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{t("conflictsTitle", { count: groups.length })}</DialogTitle>
          <DialogDescription>{t("conflictsBody")}</DialogDescription>
        </DialogHeader>
        <ul className="flex flex-col gap-3">
          {groups.map((g) => {
            const task = view?.tasks.get(g.taskId);
            const value = step?.choices[g.taskId] ?? "keep";
            return (
              <li key={g.taskId} className="flex flex-col gap-2 rounded-lg border border-border p-3">
                <p className="flex items-start gap-2 font-medium">
                  <PinIcon className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden />
                  <span>
                    <span className="mr-1.5 font-mono text-xs text-muted-foreground">{task?.code}</span>
                    {task?.task.title ?? `#${g.taskId}`}
                  </span>
                </p>
                <ul className="flex flex-col gap-0.5 pl-6 text-muted-foreground">
                  {g.conflicts.map((c, i) => (
                    <li key={i}>{reason(c)}</li>
                  ))}
                </ul>
                <RadioGroup
                  value={value}
                  onValueChange={(action) => step && onChange({ ...step.choices, [g.taskId]: action as Choices[number] })}
                  aria-label={t("choiceLabel", { code: task?.code ?? "" })}
                  className="gap-1.5 pl-6"
                >
                  {g.allowed.map((action) => {
                    const keep = action === "keep" ? keepLabel(g.conflicts) : null;
                    return (
                      <Label key={action} className="flex items-start gap-2 font-normal">
                        <RadioGroupItem value={action} className="mt-0.5" />
                        <span className="flex flex-col">
                          {keep ? keep.label : t(`action.${action}`)}
                          {keep?.note && <span className="text-xs text-muted-foreground">{keep.note}</span>}
                        </span>
                      </Label>
                    );
                  })}
                </RadioGroup>
              </li>
            );
          })}
        </ul>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={busy}>
            {t("cancel")}
          </Button>
          <Button onClick={() => step && onContinue(step.choices)} disabled={busy}>
            {busy && <Spinner data-icon="inline-start" />}
            {t("continue")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function PreviewDialog({
  step,
  busy,
  slug,
  onClose,
  onBack,
  onApply,
}: {
  step: { result: RescheduleResult; choices: Choices; conflicts: RescheduleResult | null } | null;
  busy: boolean;
  slug: string;
  onClose: () => void;
  onBack: () => void;
  onApply: (choices: Choices) => void;
}) {
  const t = useTranslations("plan.reschedule");
  const fmt = usePlanFormat();
  const { view } = usePlanData();
  const [showAll, setShowAll] = useState(false);
  const rows = step ? changeRows(step.result.changes) : [];
  const visible = showAll ? rows : rows.slice(0, PREVIEW_ROWS);
  const result = step?.result;
  const keptCauses = useKeptPinCauses();
  const shortage = result ? Math.max(0, result.after.demand_minutes - result.after.supply_minutes) : 0;
  const redByPins = result?.after.status === "red" && shortage === 0 && result.after.late_task_ids.length === 0;
  const causes = step && redByPins ? keptCauses(step.result, step.choices) : [];
  const range = (start: string | null, end: string | null) => (start ? fmt.dayRange(start, end) : t("notScheduled"));

  return (
    <Dialog
      open={step !== null}
      onOpenChange={(open) => {
        if (!open) {
          setShowAll(false);
          onClose();
        }
      }}
    >
      <DialogContent closeLabel={t("close")} className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{t("previewTitle")}</DialogTitle>
          <DialogDescription>{t("previewBody")}</DialogDescription>
        </DialogHeader>
        {result && (
          <>
            <dl className="grid gap-2 rounded-lg bg-muted/60 p-3 sm:grid-cols-3">
              <div className="flex flex-col gap-1">
                <dt className="text-xs text-muted-foreground">{t("feasibility")}</dt>
                <dd className="flex flex-wrap items-center gap-1">
                  {result.before && <FeasibilityBadge status={result.before.status} />}
                  <ArrowRightIcon className="size-3.5 text-muted-foreground" aria-label={t("to")} />
                  <FeasibilityBadge status={result.after.status} />
                </dd>
              </div>
              <div className="flex flex-col gap-1">
                <dt className="text-xs text-muted-foreground">{t("demand")}</dt>
                <dd className="tabular-nums">
                  {result.before ? fmt.hours(result.before.demand_minutes) : "—"} → {fmt.hours(result.after.demand_minutes)}
                </dd>
              </div>
              <div className="flex flex-col gap-1">
                <dt className="text-xs text-muted-foreground">{t("finish")}</dt>
                <dd className="tabular-nums">
                  {result.before_finish_date ? fmt.dayMonth(result.before_finish_date) : "—"} →{" "}
                  {result.after_finish_date ? fmt.dayMonth(result.after_finish_date) : "—"}
                </dd>
              </div>
            </dl>
            {result.after.status === "red" && !redByPins && (
              <p className="rounded-lg border border-destructive/30 bg-destructive/10 p-3">
                {t("stillRed", { shortage: fmt.hours(shortage), count: result.after.late_task_ids.length })}{" "}
                <Link href={`/q/${slug}/options`} className="font-medium underline underline-offset-4" onClick={onClose}>
                  {t("seeOptions")}
                </Link>
              </p>
            )}
            {redByPins && (
              <div className="flex flex-col gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3">
                <p>{causes.length > 0 ? t("redByPins") : t("redNoShortage")}</p>
                {causes.length > 0 && (
                  <ul className="list-disc pl-5">
                    {causes.map((cause, i) => (
                      <li key={i}>{cause}</li>
                    ))}
                  </ul>
                )}
                {result.conflicts.length > 0 && (
                  <Button variant="outline" size="sm" className="w-fit" onClick={onBack} disabled={busy}>
                    {t("backToChoices")}
                  </Button>
                )}
              </div>
            )}
            {rows.length === 0 ? (
              <p className="text-muted-foreground">{t("noChanges")}</p>
            ) : (
              <div className="flex flex-col gap-2">
                <p className="font-medium">{t("changedCount", { count: rows.length })}</p>
                <div className="max-h-72 overflow-y-auto rounded-lg border border-border">
                  <Table className="max-md:hidden">
                    <TableHeader>
                      <TableRow>
                        <TableHead>{t("colTask")}</TableHead>
                        <TableHead className="w-28">{t("colBefore")}</TableHead>
                        <TableHead className="w-28">{t("colAfter")}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {visible.map((row) => {
                        const task = view?.tasks.get(row.task_id);
                        return (
                          <TableRow key={row.task_id}>
                            <TableCell className="max-w-0 whitespace-normal">
                              <span className="mr-1.5 font-mono text-xs text-muted-foreground">{task?.code}</span>
                              <span className="line-clamp-1" title={task?.task.title}>
                                {task?.task.title ?? `#${row.task_id}`}
                              </span>
                            </TableCell>
                            <TableCell className="text-muted-foreground tabular-nums">{range(row.before_start, row.before_end)}</TableCell>
                            <TableCell className="font-medium tabular-nums">{range(row.after_start, row.after_end)}</TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                  <ul className="divide-y divide-border md:hidden">
                    {visible.map((row) => {
                      const task = view?.tasks.get(row.task_id);
                      return (
                        <li key={row.task_id} className="flex flex-col gap-0.5 px-3 py-2">
                          <span>
                            <span className="mr-1.5 font-mono text-xs text-muted-foreground">{task?.code}</span>
                            {task?.task.title ?? `#${row.task_id}`}
                          </span>
                          <span className="text-xs tabular-nums">
                            <span className="text-muted-foreground">{range(row.before_start, row.before_end)}</span>
                            {" → "}
                            <span className="font-medium">{range(row.after_start, row.after_end)}</span>
                          </span>
                        </li>
                      );
                    })}
                  </ul>
                </div>
                {rows.length > PREVIEW_ROWS && (
                  <Button variant="link" size="sm" className="w-fit px-0" onClick={() => setShowAll((v) => !v)}>
                    {showAll ? t("showLess") : t("showAll", { count: rows.length - PREVIEW_ROWS })}
                  </Button>
                )}
              </div>
            )}
          </>
        )}
        <DialogFooter>
          {step?.conflicts ? (
            <Button variant="outline" onClick={onBack} disabled={busy}>
              {t("back")}
            </Button>
          ) : (
            <Button variant="outline" onClick={onClose} disabled={busy}>
              {t("cancel")}
            </Button>
          )}
          <Button onClick={() => step && onApply(step.choices)} disabled={busy}>
            {busy && <Spinner data-icon="inline-start" />}
            {t("apply")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
