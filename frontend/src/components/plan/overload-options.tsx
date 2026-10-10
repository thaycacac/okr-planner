"use client";

import { ArrowLeftIcon, MinusIcon, PlusIcon, XIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { cn } from "cn";

import { GuardedLink } from "@/components/app-shell/unsaved-changes";
import { LoadError } from "@/components/settings/load-error";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { useLoad } from "@/hooks/use-load";
import { api } from "@/lib/api/client";
import {
  errorDetail,
  type OptionEffect,
  type OptionEvaluation,
  type OptionGroup,
  type OptionOutcome,
  type OverloadOption,
  type OverloadOptions,
} from "@/lib/api/types";
import {
  blockedBy,
  isWeekdayOption,
  OPTION_GROUPS,
  orderedSelection,
  spareMinutes,
  weekdayOptionId,
} from "@/lib/plan/options";
import type { PlanView } from "@/lib/plan/plan-view";

import { FeasibilityBadge } from "./feasibility-panel";
import { useReadyPlan } from "./plan-data";
import { usePlanFormat } from "./use-plan-format";

const EVALUATE_DEBOUNCE_MS = 300;
const UNDO_MS = 8000;

type Evaluation = { status: "idle" } | { status: "loading" } | { status: "error" } | { status: "ready"; data: OptionEvaluation };

export function OverloadOptionsPanel() {
  const t = useTranslations("plan.options");
  const plan = useReadyPlan();
  const quarterId = plan.payload.summary?.id ?? null;
  const version = plan.payload.schedule?.created_at ?? "none";

  return (
    <div className="flex flex-col gap-4">
      <Button asChild variant="ghost" size="sm" className="w-fit">
        <GuardedLink href={`/q/${plan.slug}/tasks`}>
          <ArrowLeftIcon data-icon="inline-start" />
          {t("back")}
        </GuardedLink>
      </Button>
      {/* Keyed by the stored schedule so options are recomputed after every apply or undo. */}
      {quarterId !== null && <OptionsLoader key={version} quarterId={quarterId} plan={plan.view} />}
    </div>
  );
}

function OptionsLoader({ quarterId, plan }: { quarterId: number; plan: PlanView }) {
  const fetcher = useCallback(async () => {
    const { data } = await api.GET("/quarters/{quarter_id}/options", { params: { path: { quarter_id: quarterId } } });
    return data;
  }, [quarterId]);
  const [state, retry] = useLoad(fetcher);
  if (state.status === "loading") return <OptionsSkeleton />;
  if (state.status === "error") return <LoadError onRetry={retry} />;
  return <OptionsBody data={state.data} plan={plan} quarterId={quarterId} />;
}

function OptionsSkeleton() {
  const t = useTranslations("plan.options");
  return (
    <div className="flex flex-col gap-3" aria-busy="true">
      <p className="text-sm text-muted-foreground">{t("loading")}</p>
      {Array.from({ length: 4 }, (_, i) => (
        <Skeleton key={i} className="h-20 w-full" />
      ))}
    </div>
  );
}

function OptionsBody({ data, plan, quarterId }: { data: OverloadOptions; plan: PlanView; quarterId: number }) {
  const t = useTranslations("plan.options");
  const fmt = usePlanFormat();
  const { refresh } = useReadyPlan();
  const [selected, setSelected] = useState<ReadonlySet<string>>(() => new Set());
  const hint = data.weekday_hint;
  const listedWeekday = data.options.find((o) => o.kind === "weekday_minutes");
  const [extra, setExtra] = useState(listedWeekday?.extra_minutes ?? 60);
  const weekdayId = listedWeekday ? weekdayOptionId(extra) : null;
  const ids = useMemo(() => orderedSelection(data.options, selected, weekdayId), [data.options, selected, weekdayId]);
  const evaluation = useEvaluation(quarterId, ids);
  const weekdayAlone = useEvaluation(quarterId, listedWeekday && weekdayId !== listedWeekday.id ? [weekdayId!] : []);
  const [applying, setApplying] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const label = useOptionLabel(plan);

  if (!data.overloaded) {
    const spare = data.current.buffer_minutes - data.current.buffer_used_minutes;
    return (
      <div className="flex flex-col items-start gap-3 rounded-xl border border-dashed border-border p-6">
        <FeasibilityBadge status={data.current.feasibility.status} />
        <p className="font-medium">{t("notNeeded", { hours: fmt.hours(Math.max(0, spare)) })}</p>
      </div>
    );
  }

  function toggle(option: OverloadOption, checked: boolean) {
    const next = new Set(selected);
    if (checked) next.add(option.id);
    else next.delete(option.id);
    setSelected(next);
  }

  async function apply() {
    if (ids.length === 0) return;
    setApplying(true);
    const { data: applied, error } = await api
      .POST("/quarters/{quarter_id}/options/apply", {
        params: { path: { quarter_id: quarterId }, header: { "Idempotency-Key": crypto.randomUUID() } },
        body: { option_ids: ids },
      })
      .catch(() => ({ data: undefined, error: undefined }));
    setApplying(false);
    if (!applied) {
      toast.error(errorDetail(error)?.code === "plan_in_progress" ? t("planRunning") : t("applyFailed"));
      return;
    }
    setMobileOpen(false);
    await refresh();
    toast.success(
      t("appliedToast", { count: applied.option_ids.length, status: t(`status.${applied.after.feasibility.status}`) }),
      {
        duration: UNDO_MS,
        action: {
          label: t("undo"),
          onClick: () => {
            void api
              .POST("/option-applications/{application_id}/undo", { params: { path: { application_id: applied.id } } })
              .then(async ({ data: undone }) => {
                await refresh();
                if (undone) toast(t("undoneToast"));
                else toast.error(t("undoFailed"));
              });
          },
        },
      },
    );
  }

  const current = data.current;
  const rail = (
    <PreviewRail
      before={current}
      evaluation={evaluation}
      selectedIds={ids}
      label={label}
      options={data.options}
      onRemove={(id) => {
        const option = data.options.find((o) => o.id === id || (isWeekdayOption(id) && o.kind === "weekday_minutes"));
        if (option) toggle(option, false);
      }}
      onClear={() => setSelected(new Set())}
      onApply={() => void apply()}
      applying={applying}
    />
  );

  return (
    <div className="flex flex-col gap-5 pb-24 md:pb-0">
      <header className="flex flex-col gap-1.5">
        <h2 className="font-heading text-xl font-semibold">{t("title")}</h2>
        <p className="text-sm">
          {t("problem", {
            demand: fmt.hours(current.feasibility.demand_minutes),
            supply: fmt.hours(current.feasibility.supply_minutes),
            shortage: fmt.hours(current.shortfall_minutes),
            count: current.late_task_count,
          })}
        </p>
        <p className="text-xs text-muted-foreground">{t("intro")}</p>
      </header>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_24rem]">
        <div className="flex flex-col gap-5">
          {OPTION_GROUPS.map((group) => {
            const options = data.options.filter((o) => o.group === group);
            if (options.length === 0) return null;
            return (
              <section key={group} className="flex flex-col gap-2" aria-labelledby={`group-${group}`}>
                <h3 id={`group-${group}`} className="text-sm font-semibold">
                  {t(`groups.${group}`)}
                </h3>
                <ul className="flex flex-col gap-2">
                  {options.map((option) => {
                    const isWeekday = option.kind === "weekday_minutes";
                    const outcome =
                      isWeekday && weekdayId !== option.id
                        ? weekdayAlone.status === "ready"
                          ? weekdayAlone.data.after
                          : null
                        : option.outcome;
                    const blocker = blockedBy(option, selected);
                    return (
                      <OptionCard
                        key={option.id}
                        group={group}
                        option={option}
                        title={label(isWeekday && weekdayId ? weekdayId : option.id, option)}
                        detail={optionDetail(option, plan)}
                        outcome={outcome}
                        checked={selected.has(option.id)}
                        blocker={blocker ? label(blocker, data.options.find((o) => o.id === blocker)) : null}
                        onCheck={(checked) => toggle(option, checked)}
                      >
                        {isWeekday && hint && (
                          <WeekdayStepper
                            extra={extra}
                            step={hint.step_minutes}
                            base={Math.max(...hint.current_minutes)}
                            minGreen={hint.min_extra_minutes_green}
                            minNotRed={hint.min_extra_minutes_not_red}
                            onChange={setExtra}
                          />
                        )}
                      </OptionCard>
                    );
                  })}
                </ul>
              </section>
            );
          })}
        </div>
        <aside className="hidden xl:block" aria-label={t("previewLabel")}>
          <div className="sticky top-20">{rail}</div>
        </aside>
      </div>

      <MobileBar
        count={ids.length}
        evaluation={evaluation}
        before={current}
        onOpen={() => setMobileOpen(true)}
      />
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="bottom" closeLabel={t("close")} className="max-h-[85svh] overflow-y-auto">
          <SheetHeader>
            <SheetTitle className="sr-only">{t("previewTitle", { count: ids.length })}</SheetTitle>
            <SheetDescription className="sr-only">{t("previewLabel")}</SheetDescription>
          </SheetHeader>
          <div className="px-4 pb-6">{rail}</div>
        </SheetContent>
      </Sheet>
    </div>
  );
}

function useEvaluation(quarterId: number, ids: readonly string[]): Evaluation {
  const key = ids.join("|");
  const [result, setResult] = useState<{ key: string; value: Evaluation }>({ key: "", value: { status: "idle" } });
  const latest = useRef(key);
  useEffect(() => {
    latest.current = key;
    if (key === "") return;
    const timer = window.setTimeout(() => {
      api
        .POST("/quarters/{quarter_id}/options/evaluate", {
          params: { path: { quarter_id: quarterId } },
          body: { option_ids: key.split("|") },
        })
        .then(
          ({ data }) => {
            if (latest.current === key) setResult({ key, value: data ? { status: "ready", data } : { status: "error" } });
          },
          () => {
            if (latest.current === key) setResult({ key, value: { status: "error" } });
          },
        );
    }, EVALUATE_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [quarterId, key]);
  if (key === "") return { status: "idle" };
  return result.key === key ? result.value : { status: "loading" };
}

function useOptionLabel(plan: PlanView) {
  const t = useTranslations("plan.options");
  const fmt = usePlanFormat();
  return useCallback(
    (id: string, option?: OverloadOption) => {
      if (isWeekdayOption(id)) {
        const extra = Number(id.split("+")[1]);
        return t("label.weekday", { extra: fmt.hours(extra) });
      }
      const [kind, target] = id.split(":");
      const krCode = plan.codes.krs.get(Number(target)) ?? `#${target}`;
      const objectiveCode = plan.codes.objectives.get(Number(target))?.code ?? `#${target}`;
      const deferred = option?.effects.find((e) => e.code === "key_result_deferred");
      switch (kind) {
        case "work_saturday":
        case "work_sunday":
        case "work_holidays":
          return t(`label.${kind}`);
        case "drop_kr":
          return t("label.drop_kr", { kr: krCode });
        case "drop_objective":
          return t("label.drop_objective", { objective: objectiveCode });
        case "defer_kr":
          return t("label.defer_kr", {
            kr: krCode,
            quarter: deferred?.target_number ? `Q${deferred.target_number}/${deferred.target_year}` : t("nextQuarter"),
          });
        default:
          return id;
      }
    },
    [plan, t, fmt],
  );
}

function optionDetail(option: OverloadOption, plan: PlanView) {
  if (option.key_result_id !== null) {
    return plan.objectives.flatMap((o) => o.krs).find((k) => k.kr.id === option.key_result_id)?.kr.text ?? null;
  }
  if (option.objective_id !== null) {
    return plan.objectives.find((o) => o.objective.id === option.objective_id)?.objective.title ?? null;
  }
  return null;
}

function OutcomeLine({ outcome }: { outcome: OptionOutcome }) {
  const t = useTranslations("plan.options");
  const fmt = usePlanFormat();
  const f = outcome.feasibility;
  const parts = [
    f.status === "red"
      ? t("outcome.short", { hours: fmt.hours(outcome.shortfall_minutes), count: outcome.late_task_count })
      : outcome.buffer_used_minutes > 0
        ? t("outcome.buffer", { used: fmt.hours(outcome.buffer_used_minutes), buffer: fmt.hours(outcome.buffer_minutes) })
        : t("outcome.spare", { hours: fmt.hours(Math.max(0, spareMinutes(outcome))) }),
    outcome.finish_date ? t("outcome.finish", { date: fmt.dayMonth(outcome.finish_date) }) : null,
  ].filter(Boolean);
  return (
    <span className="flex flex-col items-end gap-1 text-right">
      <FeasibilityBadge status={f.status} />
      <span className="text-xs text-muted-foreground">{parts.join(" · ")}</span>
    </span>
  );
}

function OptionCard({
  group,
  option,
  title,
  detail,
  outcome,
  checked,
  blocker,
  onCheck,
  children,
}: {
  group: OptionGroup;
  option: OverloadOption;
  title: string;
  detail: string | null;
  outcome: OptionOutcome | null;
  checked: boolean;
  blocker: string | null;
  onCheck: (checked: boolean) => void;
  children?: React.ReactNode;
}) {
  const t = useTranslations("plan.options");
  const fmt = usePlanFormat();
  const id = `option-${option.id.replace(/[^a-z0-9]/gi, "-")}`;
  const signed = (minutes: number) => `${minutes > 0 ? "+" : "−"}${fmt.hours(Math.abs(minutes))}`;
  const gains = outcome
    ? [
        outcome.supply_delta_minutes !== 0 && t("gainSupply", { hours: signed(outcome.supply_delta_minutes) }),
        outcome.demand_delta_minutes !== 0 && t("gainDemand", { hours: signed(outcome.demand_delta_minutes) }),
      ].filter((g): g is string => Boolean(g))
    : [];
  return (
    <li
      className={cn(
        "flex flex-col gap-3 rounded-xl border border-border p-3 sm:flex-row sm:items-start",
        checked && "border-foreground/40 bg-muted/40",
        blocker && "opacity-60",
      )}
      data-group={group}
    >
      <div className="flex min-w-0 flex-1 items-start gap-3">
        <Checkbox
          id={id}
          checked={checked}
          disabled={blocker !== null}
          onCheckedChange={(v) => onCheck(v === true)}
          className="mt-0.5"
          aria-describedby={blocker ? `${id}-blocked` : undefined}
        />
        <div className="flex min-w-0 flex-col gap-1">
          <label htmlFor={id} className="font-medium">
            {title}
            {gains.length > 0 && (
              <span className="ml-2 text-sm font-normal whitespace-nowrap text-muted-foreground tabular-nums">{gains.join(" · ")}</span>
            )}
          </label>
          {detail && <span className="line-clamp-2 text-sm text-muted-foreground">{detail}</span>}
          {option.effects.some((e) => e.pinned_task_ids.length > 0) && (
            <Badge variant="outline" className="w-fit font-normal">
              {t("pinnedAffected", { count: option.effects.reduce((s, e) => s + e.pinned_task_ids.length, 0) })}
            </Badge>
          )}
          {blocker && (
            <span id={`${id}-blocked`} className="text-xs text-muted-foreground">
              {t("blocked", { other: blocker })}
            </span>
          )}
          {children}
        </div>
      </div>
      <div className="shrink-0 pl-7 sm:pl-0">{outcome ? <OutcomeLine outcome={outcome} /> : <Skeleton className="h-10 w-28" />}</div>
    </li>
  );
}

function WeekdayStepper({
  extra,
  step,
  base,
  minGreen,
  minNotRed,
  onChange,
}: {
  extra: number;
  step: number;
  base: number;
  minGreen: number | null;
  minNotRed: number | null;
  onChange: (extra: number) => void;
}) {
  const t = useTranslations("plan.options");
  const fmt = usePlanFormat();
  const max = Math.max(step, 16 * 60 - base);
  return (
    <div className="flex flex-col gap-1.5 pt-1">
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="icon-sm"
          className="max-md:size-10"
          onClick={() => onChange(Math.max(step, extra - step))}
          disabled={extra <= step}
          aria-label={t("less")}
        >
          <MinusIcon />
        </Button>
        <span className="min-w-28 text-center text-sm tabular-nums" aria-live="polite">
          {t("perDay", { hours: fmt.hours(base + extra) })}
        </span>
        <Button
          type="button"
          variant="outline"
          size="icon-sm"
          className="max-md:size-10"
          onClick={() => onChange(Math.min(max, extra + step))}
          disabled={extra >= max}
          aria-label={t("more")}
        >
          <PlusIcon />
        </Button>
      </div>
      {(minGreen !== null || minNotRed !== null) && (
        <span className="text-xs text-muted-foreground">
          {minGreen !== null
            ? t("hintGreen", { hours: fmt.hours(base + minGreen) })
            : t("hintNotRed", { hours: fmt.hours(base + (minNotRed ?? 0)) })}
        </span>
      )}
    </div>
  );
}

function PreviewRail({
  before,
  evaluation,
  selectedIds,
  label,
  options,
  onRemove,
  onClear,
  onApply,
  applying,
}: {
  before: OptionOutcome;
  evaluation: Evaluation;
  selectedIds: string[];
  label: (id: string, option?: OverloadOption) => string;
  options: OverloadOption[];
  onRemove: (id: string) => void;
  onClear: () => void;
  onApply: () => void;
  applying: boolean;
}) {
  const t = useTranslations("plan.options");
  const fmt = usePlanFormat();
  const after = evaluation.status === "ready" ? evaluation.data.after : null;
  const effects = evaluation.status === "ready" ? evaluation.data.effects : [];
  const rows: { key: string; label: string; before: string; after: string | null }[] = [
    { key: "demand", label: t("row.demand"), before: fmt.hours(before.feasibility.demand_minutes), after: after && fmt.hours(after.feasibility.demand_minutes) },
    { key: "supply", label: t("row.supply"), before: fmt.hours(before.feasibility.supply_minutes), after: after && fmt.hours(after.feasibility.supply_minutes) },
    { key: "gap", label: t("row.gap"), before: signedHours(spareMinutes(before), fmt.hours), after: after && signedHours(spareMinutes(after), fmt.hours) },
    { key: "finish", label: t("row.finish"), before: before.finish_date ? fmt.dayMonth(before.finish_date) : "—", after: after && (after.finish_date ? fmt.dayMonth(after.finish_date) : "—") },
    { key: "late", label: t("row.late"), before: String(before.late_task_count), after: after && String(after.late_task_count) },
  ];

  return (
    <section className="flex flex-col gap-4 rounded-xl border border-border p-4 text-sm">
      <h3 className="font-heading font-semibold">{t("previewTitle", { count: selectedIds.length })}</h3>
      {selectedIds.length === 0 ? (
        <p className="text-muted-foreground">{t("pickHint")}</p>
      ) : (
        <ul className="flex flex-wrap gap-1.5">
          {selectedIds.map((id) => (
            <li key={id}>
              <Badge variant="secondary" className="gap-1 pr-1 font-normal">
                {label(id, options.find((o) => o.id === id))}
                <button
                  type="button"
                  onClick={() => onRemove(id)}
                  className="rounded-full p-0.5 hover:bg-background focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                  aria-label={t("remove", { option: label(id, options.find((o) => o.id === id)) })}
                >
                  <XIcon className="size-3" aria-hidden />
                </button>
              </Badge>
            </li>
          ))}
        </ul>
      )}

      <table className="w-full text-sm">
        <thead>
          <tr className="text-xs text-muted-foreground">
            <th scope="col" className="py-1 text-left font-normal">
              <span className="sr-only">{t("row.metric")}</span>
            </th>
            <th scope="col" className="py-1 text-right font-normal">
              {t("before")}
            </th>
            <th scope="col" className="py-1 text-right font-normal">
              {t("after")}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr className="border-t border-border">
            <th scope="row" className="py-1.5 text-left font-normal">
              {t("row.status")}
            </th>
            <td className="py-1.5 text-right">
              <FeasibilityBadge status={before.feasibility.status} className="ml-auto" />
            </td>
            <td className="py-1.5 text-right">
              {after ? <FeasibilityBadge status={after.feasibility.status} className="ml-auto" /> : <AfterPlaceholder evaluation={evaluation} />}
            </td>
          </tr>
          {rows.map((row) => (
            <tr key={row.key} className="border-t border-border">
              <th scope="row" className="py-1.5 text-left font-normal">
                {row.label}
              </th>
              <td className="py-1.5 text-right tabular-nums text-muted-foreground">{row.before}</td>
              <td className="py-1.5 text-right font-medium tabular-nums">{row.after ?? <AfterPlaceholder evaluation={evaluation} />}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="flex flex-col gap-2">
        <UsageBar label={t("before")} outcome={before} />
        {after && <UsageBar label={t("after")} outcome={after} />}
      </div>

      {evaluation.status === "error" && (
        <Alert variant="destructive">
          <AlertDescription className="text-foreground">{t("evaluateFailed")}</AlertDescription>
        </Alert>
      )}

      {after && after.feasibility.status === "red" && (
        <p className="text-xs font-medium text-destructive">{t("stillShort", { hours: fmt.hours(after.shortfall_minutes) })}</p>
      )}

      {effects.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <h4 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{t("willChange")}</h4>
          <ul className="flex list-disc flex-col gap-1 pl-4 text-xs">
            {effects.map((effect, i) => (
              <EffectItem key={`${effect.option_id}-${effect.code}-${i}`} effect={effect} />
            ))}
            <li>{t("noAi")}</li>
          </ul>
        </div>
      )}

      <div className="flex flex-col gap-2">
        <Button size="lg" onClick={onApply} disabled={selectedIds.length === 0 || applying || evaluation.status === "loading"}>
          {applying && <Spinner data-icon="inline-start" />}
          {t("apply")}
        </Button>
        <Button variant="ghost" size="sm" onClick={onClear} disabled={selectedIds.length === 0 || applying}>
          {t("clear")}
        </Button>
      </div>
    </section>
  );
}

function AfterPlaceholder({ evaluation }: { evaluation: Evaluation }) {
  if (evaluation.status === "loading") return <Skeleton className="ml-auto h-4 w-10" />;
  return <span className="text-muted-foreground">—</span>;
}

function signedHours(minutes: number, hours: (m: number) => string) {
  return `${minutes >= 0 ? "+" : "−"}${hours(Math.abs(minutes))}`;
}

function UsageBar({ label, outcome }: { label: string; outcome: OptionOutcome }) {
  const t = useTranslations("plan.options");
  const f = outcome.feasibility;
  const supply = Math.max(f.supply_minutes, 1);
  const fill = Math.min(f.demand_minutes / supply, 1) * 100;
  const marker = (f.buffered_supply_minutes / supply) * 100;
  const percent = Math.round((f.demand_minutes / supply) * 100);
  const bar = f.status === "red" ? "bg-destructive" : f.status === "yellow" ? "bg-warning" : "bg-success";
  return (
    <div className="flex flex-col gap-1">
      <span className="flex justify-between text-xs text-muted-foreground">
        <span>{label}</span>
        <span className="tabular-nums">{t("usage", { percent })}</span>
      </span>
      <span className="relative block h-2 rounded-full bg-muted" aria-hidden>
        <span className={cn("block h-full rounded-full", bar)} style={{ width: `${fill}%` }} />
        {f.buffer_start && <span className="absolute -top-1 h-4 w-0.5 bg-foreground/70" style={{ left: `${marker}%` }} />}
      </span>
    </div>
  );
}

function EffectItem({ effect }: { effect: OptionEffect }) {
  const t = useTranslations("plan.options");
  const { view } = useReadyPlan();
  const krCode = effect.key_result_id !== null ? (view.codes.krs.get(effect.key_result_id) ?? "") : "";
  const objectiveCode = effect.objective_id !== null ? (view.codes.objectives.get(effect.objective_id)?.code ?? "") : "";
  switch (effect.code) {
    case "quarter_calendar_changed":
      return <li>{t("effect.calendar")}</li>;
    case "key_result_dropped":
      return <li>{t("effect.dropped", { kr: krCode, count: effect.task_count })}</li>;
    case "objective_paused":
      return <li>{t("effect.paused", { objective: objectiveCode, count: effect.task_count })}</li>;
    case "key_result_deferred":
      return (
        <li>
          {t(effect.target_quarter_exists ? "effect.deferred" : "effect.deferredNew", {
            kr: krCode,
            count: effect.task_count,
            quarter: `Q${effect.target_number}/${effect.target_year}`,
          })}
          {effect.pinned_task_ids.length > 0 && ` ${t("effect.unpinned", { count: effect.pinned_task_ids.length })}`}
        </li>
      );
    default:
      return null;
  }
}

function MobileBar({
  count,
  evaluation,
  before,
  onOpen,
}: {
  count: number;
  evaluation: Evaluation;
  before: OptionOutcome;
  onOpen: () => void;
}) {
  const t = useTranslations("plan.options");
  const fmt = usePlanFormat();
  const after = evaluation.status === "ready" ? evaluation.data.after : null;
  return (
    <div className="fixed inset-x-0 bottom-[calc(3.5rem+env(safe-area-inset-bottom))] z-30 flex items-center gap-3 border-t border-border bg-background/95 px-4 py-2 text-sm backdrop-blur xl:hidden md:bottom-0">
      <span className="min-w-0 flex-1 truncate">
        {t("mobileSelected", { count })}
        {after && (
          <>
            {" · "}
            {signedHours(spareMinutes(before), fmt.hours)} → {signedHours(spareMinutes(after), fmt.hours)} ·{" "}
            {t(`status.${after.feasibility.status}`)}
          </>
        )}
      </span>
      <Button size="sm" onClick={onOpen} disabled={count === 0}>
        {t("mobileOpen")}
      </Button>
    </div>
  );
}
