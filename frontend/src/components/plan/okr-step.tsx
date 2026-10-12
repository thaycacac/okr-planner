"use client";

import { ArrowLeftIcon, ArrowRightIcon, CircleAlertIcon, InfoIcon, PlusIcon, SparklesIcon, TriangleAlertIcon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { LoadError } from "@/components/settings/load-error";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { Spinner } from "@/components/ui/spinner";
import { useApiErrorMessage } from "@/hooks/use-api-error-message";
import { useLoad } from "@/hooks/use-load";
import { api } from "@/lib/api/client";
import { errorDetail, type QuarterSummary } from "@/lib/api/types";
import {
  buildContext,
  countKeyResults,
  type DraftIssue,
  emptyDraft,
  emptyKr,
  emptyObjective,
  fromQuarterDetail,
  type KrDraft,
  loadDraft,
  newKey,
  type ObjectiveDraft,
  type OkrDraft,
  precheck,
  saveDraft,
  warnings,
} from "@/lib/plan/okr-draft";
import { type QuarterRef, findQuarter, quarterLabel, quarterRange, quarterSlug } from "@/lib/plan/quarter";
import { fromParsed, parseOkrText } from "@/lib/plan/okr-text";
import { getQuarterDetail, listQuarters, syncDraft } from "@/lib/plan/sync";

import { fieldId, type ObjectiveActions, ObjectiveCard, useIssueText } from "./objective-card";
import { usePlanFormat } from "./use-plan-format";

type Loaded = { draft: OkrDraft; quarter: QuarterSummary | null };

export function OkrStep({ quarter }: { quarter: QuarterRef }) {
  const { year, number } = quarter;
  const slug = quarterSlug(quarter);
  const load = useCallback(async (): Promise<Loaded | undefined> => {
    const ref = { year, number };
    const local = loadDraft(quarterSlug(ref));
    const summary = findQuarter(await listQuarters(api), ref) ?? null;
    if (local && !local.synced) return { draft: local, quarter: summary };
    if (summary && summary.objective_count > 0) {
      const detail = await getQuarterDetail(api, summary.id);
      return { draft: fromQuarterDetail(detail, local), quarter: summary };
    }
    return { draft: local ?? emptyDraft(), quarter: summary };
  }, [year, number]);
  const [state, retry] = useLoad(load);

  if (state.status === "error") return <LoadError onRetry={retry} />;
  if (state.status === "loading") {
    return (
      <div className="flex flex-col gap-4" aria-busy="true">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full max-w-4xl" />
        <Skeleton className="h-16 w-full max-w-4xl" />
      </div>
    );
  }
  return <OkrForm key={slug} quarter={quarter} initial={state.data.draft} summary={state.data.quarter} />;
}

function issueTarget(issue: DraftIssue) {
  if (issue.krKey && issue.field) return fieldId(issue.krKey, issue.field);
  if (issue.objectiveKey && issue.field) return fieldId(issue.objectiveKey, issue.field);
  return null;
}

type Submit = { state: "idle" } | { state: "busy" } | { state: "error"; message: string; runningJob?: string | null };

function OkrForm({ quarter, initial, summary }: { quarter: QuarterRef; initial: OkrDraft; summary: QuarterSummary | null }) {
  const t = useTranslations("plan.okr");
  const apiErrorMessage = useApiErrorMessage();
  const tIssue = useIssueText();
  const fmt = usePlanFormat();
  const router = useRouter();
  const slug = quarterSlug(quarter);
  const range = quarterRange(quarter);
  const [draft, setDraft] = useState(initial);
  const [touched, setTouched] = useState<Set<string>>(() => new Set());
  const [attempted, setAttempted] = useState(false);
  const [collapsed, setCollapsed] = useState<Set<string>>(() => new Set());
  const [savedAt, setSavedAt] = useState<number | null>(initial.savedAt);
  const [saveFailed, setSaveFailed] = useState(false);
  const [submit, setSubmit] = useState<Submit>({ state: "idle" });
  const [source, setSource] = useState("");
  const [filling, setFilling] = useState(false);

  const context = useMemo(
    () => buildContext(draft, { domain: t("domain"), constraints: t("constraints") }) ?? "",
    [draft, t],
  );
  const issues = useMemo(() => precheck(draft, context), [draft, context]);
  const softWarnings = useMemo(() => warnings(draft), [draft]);
  const visible = attempted
    ? issues
    : issues.filter((i) => {
        const target = issueTarget(i);
        return target !== null && touched.has(target);
      });

  useEffect(() => {
    if (draft === initial) return;
    const timer = window.setTimeout(() => {
      const now = Date.now();
      const ok = saveDraft(slug, { ...draft, savedAt: now });
      setSaveFailed(!ok);
      if (ok) setSavedAt(now);
    }, 1000);
    return () => window.clearTimeout(timer);
  }, [draft, initial, slug]);

  const edit = useCallback((fn: (objectives: ObjectiveDraft[]) => ObjectiveDraft[]) => {
    setDraft((d) => ({ ...d, objectives: fn(d.objectives), synced: false }));
  }, []);

  const touch = useCallback((id: string) => {
    setTouched((prev) => (prev.has(id) ? prev : new Set(prev).add(id)));
  }, []);

  function actionsFor(objective: ObjectiveDraft, index: number): ObjectiveActions {
    const key = objective.key;
    const mapObjective = (fn: (o: ObjectiveDraft) => ObjectiveDraft) =>
      edit((list) => list.map((o) => (o.key === key ? fn(o) : o)));
    return {
      update: (patch) => mapObjective((o) => ({ ...o, ...patch })),
      updateKr: (krKey, patch) =>
        mapObjective((o) => ({
          ...o,
          keyResults: o.keyResults.map((kr) => (kr.key === krKey ? { ...kr, ...patch } : kr)),
        })),
      addKr: () => {
        const kr = emptyKr();
        mapObjective((o) => ({ ...o, keyResults: [...o.keyResults, kr] }));
        window.setTimeout(() => document.getElementById(fieldId(kr.key, "text"))?.focus(), 0);
      },
      removeKr: (krKey) => {
        const at = objective.keyResults.findIndex((kr) => kr.key === krKey);
        const removed = objective.keyResults[at];
        mapObjective((o) => ({ ...o, keyResults: o.keyResults.filter((kr) => kr.key !== krKey) }));
        toast(t("deletedKr", { code: `KR ${index + 1}.${at + 1}` }), {
          duration: 5000,
          action: {
            label: t("undo"),
            onClick: () =>
              mapObjective((o) => {
                const keyResults = [...o.keyResults];
                keyResults.splice(at, 0, removed as KrDraft);
                return { ...o, keyResults };
              }),
          },
        });
      },
      duplicate: () =>
        edit((list) => {
          const copy: ObjectiveDraft = {
            ...objective,
            key: newKey("o"),
            serverId: undefined,
            inactive: undefined,
            keyResults: objective.keyResults.map((kr) => ({ ...kr, key: newKey("kr"), serverId: undefined, inactive: undefined })),
          };
          const next = [...list];
          next.splice(index + 1, 0, copy);
          return next;
        }),
      move: (delta) =>
        edit((list) => {
          const next = [...list];
          const [item] = next.splice(index, 1);
          next.splice(index + delta, 0, item);
          return next;
        }),
      remove: () => {
        edit((list) => list.filter((o) => o.key !== key));
        toast(t("deletedObjective", { code: `O${index + 1}` }), {
          duration: 5000,
          action: {
            label: t("undo"),
            onClick: () =>
              edit((list) => {
                const next = [...list];
                next.splice(index, 0, objective);
                return next;
              }),
          },
        });
      },
      touch,
    };
  }

  // The text box is a staging area: describe one or more OKRs, press the button, and the
  // structured cards are appended below. Then the box is free for the next batch.
  async function fillFromText() {
    const text = source.trim();
    if (!text || filling) return;
    setFilling(true);
    let parsed: ObjectiveDraft[];
    let usedFallback = false;
    try {
      const { data } = await api.POST("/okr/parse", { body: { text, year: quarter.year, number: quarter.number } });
      if (!data || data.objectives.length === 0) throw new Error("no result");
      parsed = fromParsed(data);
    } catch {
      parsed = parseOkrText(text, { year: quarter.year, ...range }).objectives;
      usedFallback = true;
    }
    setFilling(false);
    if (parsed.length === 0) {
      toast.error(t("paste.empty"));
      return;
    }
    const blank = (list: ObjectiveDraft[]) =>
      list.every((o) => !o.title.trim() && o.keyResults.every((kr) => !kr.text.trim()));
    edit((list) => (blank(list) ? parsed : [...list, ...parsed]));
    setSource("");
    toast.success(
      t("paste.filled", { objectives: parsed.length, krs: parsed.reduce((n, o) => n + o.keyResults.length, 0) }),
    );
    if (usedFallback) toast.warning(t("paste.aiFailed"));
  }

  function addObjective() {
    const objective = emptyObjective();
    edit((list) => [...list, objective]);
    window.setTimeout(() => document.getElementById(fieldId(objective.key, "title"))?.focus(), 0);
  }

  function fillExample() {
    const example = t.raw("example") as {
      title: string;
      domain: string;
      constraints: string;
      krs: Pick<KrDraft, "text" | "kind" | "baseline" | "target" | "unit">[];
    };
    const objective: ObjectiveDraft = {
      ...emptyObjective(),
      title: example.title,
      priority: "high",
      domain: example.domain,
      constraints: example.constraints,
      keyResults: example.krs.map((kr) => ({ ...emptyKr(), ...kr })),
    };
    edit(() => [objective]);
  }

  function jumpTo(issue: DraftIssue) {
    if (issue.objectiveKey && collapsed.has(issue.objectiveKey)) {
      setCollapsed((prev) => {
        const next = new Set(prev);
        next.delete(issue.objectiveKey!);
        return next;
      });
    }
    const target = issueTarget(issue);
    window.setTimeout(() => target && document.getElementById(target)?.focus(), 0);
  }

  async function onContinue() {
    setAttempted(true);
    if (issues.length > 0) {
      jumpTo(issues[0]);
      return;
    }
    setSubmit({ state: "busy" });
    try {
      const synced = await syncDraft(api, quarter, draft);
      saveDraft(slug, { ...synced.draft, savedAt: Date.now() });
      const { data, error, response } = await api.POST("/plans", {
        body: { quarter_id: synced.quarterId, context: context || null, skip_clarification: false },
      });
      if (data) {
        router.push(`/plan/new/generate?job=${data.job_id}`);
        return;
      }
      const detail = errorDetail(error);
      if (response.status === 409 && detail?.code === "plan_in_progress") {
        const running = findQuarter(await listQuarters(api), quarter)?.latest_plan_run_id ?? null;
        setSubmit({ state: "error", message: t("submitErrors.inProgress"), runningJob: running });
        return;
      }
      setSubmit({ state: "error", message: apiErrorMessage(error, t("submitErrors.generic")) });
    } catch {
      setSubmit({ state: "error", message: t("submitErrors.generic") });
    }
  }

  const krCount = countKeyResults(draft);
  const busy = submit.state === "busy";
  const hasTasks = (summary?.task_count ?? 0) > 0;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="font-heading text-2xl font-semibold tracking-tight">{t("title", { quarter: quarterLabel(quarter) })}</h1>
          <p className="text-sm text-muted-foreground">
            {fmt.date(range.start)} – {fmt.date(range.end)}
          </p>
        </div>
        <p className="text-xs text-muted-foreground" aria-live="polite">
          {savedAt ? t("savedAt", { time: fmt.clock(savedAt) }) : null}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_18rem]">
        <div className="flex min-w-0 flex-col gap-4">
          {hasTasks && (
            <Alert>
              <InfoIcon />
              <AlertDescription>{t("regenerateNotice")}</AlertDescription>
            </Alert>
          )}
          {saveFailed && (
            <Alert className="border-warning/40 bg-warning-muted text-warning">
              <TriangleAlertIcon />
              <AlertDescription className="text-warning">{t("saveFailed")}</AlertDescription>
            </Alert>
          )}
          {softWarnings.length > 0 && (
            <Alert className="border-warning/40 bg-warning-muted text-warning">
              <TriangleAlertIcon />
              <AlertDescription className="text-warning">
                {softWarnings.map((w) => t(`warnings.${w}`)).join(" ")}
              </AlertDescription>
            </Alert>
          )}
          {attempted && issues.length > 0 && (
            <Alert variant="destructive" aria-live="assertive">
              <CircleAlertIcon />
              <AlertTitle>{t("issuesTitle", { count: issues.length })}</AlertTitle>
              <AlertDescription>
                <ul className="flex flex-col gap-0.5">
                  {issues.slice(0, 6).map((issue, i) => (
                    <li key={i}>
                      <button
                        type="button"
                        className="text-left underline underline-offset-3"
                        onClick={() => jumpTo(issue)}
                      >
                        {issueLabel(draft, issue)}
                        {tIssue(issue.code)}
                      </button>
                    </li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}

          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-sm">
                <label htmlFor="okr-source">{t("paste.title")}</label>
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              <Textarea
                id="okr-source"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                disabled={filling}
                rows={8}
                spellCheck={false}
                className="font-mono text-sm"
                placeholder={t("paste.placeholder")}
                aria-describedby="okr-source-hint"
              />
              <p id="okr-source-hint" className="text-xs text-muted-foreground">
                {t("paste.hint")}
              </p>
              <div>
                <Button type="button" onClick={() => void fillFromText()} disabled={!source.trim() || filling}>
                  {filling ? <Spinner aria-hidden role="presentation" /> : <SparklesIcon data-icon="inline-start" />}
                  {filling ? t("paste.filling") : t("paste.fill")}
                </Button>
              </div>
            </CardContent>
          </Card>

          {draft.objectives.map((objective, index) => (
            <ObjectiveCard
              key={objective.key}
              objective={objective}
              index={index}
              count={draft.objectives.length}
              collapsed={collapsed.has(objective.key)}
              onToggle={() =>
                setCollapsed((prev) => {
                  const next = new Set(prev);
                  if (!next.delete(objective.key)) next.add(objective.key);
                  return next;
                })
              }
              issues={visible.filter((i) => i.objectiveKey === objective.key)}
              quarterStart={range.start}
              quarterEnd={range.end}
              actions={actionsFor(objective, index)}
            />
          ))}

          <div className="flex flex-wrap items-center gap-3">
            <Button variant="outline" onClick={addObjective}>
              <PlusIcon data-icon="inline-start" />
              {t("addObjective")}
            </Button>
            {krCount <= 1 && !draft.objectives[0]?.title && (
              <span className="text-sm text-muted-foreground">
                {t("emptyHint")}{" "}
                <button type="button" onClick={fillExample} className="font-medium text-foreground underline underline-offset-4">
                  {t("fillExample")}
                </button>
              </span>
            )}
          </div>
        </div>

        <aside className="flex flex-col gap-4" aria-label={t("summaryLabel")}>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs tracking-wide text-muted-foreground uppercase">{t("summary")}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <dl className="grid grid-cols-2 gap-2">
                <div className="flex flex-col-reverse">
                  <dt className="text-xs text-muted-foreground uppercase">{t("summaryObjectives")}</dt>
                  <dd className="font-heading text-2xl font-semibold">{draft.objectives.length}</dd>
                </div>
                <div className="flex flex-col-reverse">
                  <dt className="text-xs text-muted-foreground uppercase">{t("summaryKrs")}</dt>
                  <dd className="font-heading text-2xl font-semibold">{krCount}</dd>
                </div>
              </dl>
              {issues.length > 0 ? (
                <p className="flex items-center gap-1.5 rounded-md bg-destructive/10 px-2 py-1 text-xs">
                  <CircleAlertIcon className="size-3.5 shrink-0 text-destructive" aria-hidden />
                  {t("issuesShort", { count: issues.length })}
                </p>
              ) : (
                <p className="rounded-md bg-success-muted px-2 py-1 text-xs text-success">{t("noIssues")}</p>
              )}
            </CardContent>
          </Card>
          <Card size="sm" className="hidden lg:flex">
            <CardHeader>
              <CardTitle className="text-xs tracking-wide text-muted-foreground uppercase">{t("goodKr.title")}</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="flex list-disc flex-col gap-1 pl-4 text-sm">
                <li>{t("goodKr.measurable")}</li>
                <li>{t("goodKr.feasible")}</li>
                <li>{t("goodKr.outcome")}</li>
              </ul>
            </CardContent>
          </Card>
          <Alert className="hidden lg:grid">
            <SparklesIcon />
            <AlertDescription>{t("aiNotice")}</AlertDescription>
          </Alert>
        </aside>
      </div>

      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-border bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3 md:px-8">
          <Button asChild variant="ghost" className="hidden sm:inline-flex">
            <Link href={`/plan/new?q=${slug}`}>
              <ArrowLeftIcon data-icon="inline-start" />
              {t("back")}
            </Link>
          </Button>
          <div className="flex min-w-0 flex-1 items-center justify-end gap-2 text-xs" aria-live="polite">
            {submit.state === "error" && !busy ? (
              <>
                <span role="alert" className="flex min-w-0 items-center gap-1.5">
                  <CircleAlertIcon className="size-4 shrink-0 text-destructive" aria-hidden />
                  <span className="line-clamp-2">{submit.message}</span>
                </span>
                {submit.runningJob && (
                  <Button asChild size="sm" variant="outline">
                    <Link href={`/plan/new/generate?job=${submit.runningJob}`}>{t("submitErrors.openRunning")}</Link>
                  </Button>
                )}
              </>
            ) : (
              <span className="text-right text-muted-foreground">
                {busy ? t("submitting") : attempted && issues.length > 0 ? t("fixToContinue", { count: issues.length }) : null}
              </span>
            )}
          </div>
          <Button size="lg" onClick={onContinue} disabled={busy} className="flex-1 sm:flex-none">
            {busy && <Spinner data-icon="inline-start" />}
            {t("continue")}
            {!busy && <ArrowRightIcon data-icon="inline-end" />}
          </Button>
        </div>
      </div>
    </div>
  );
}

function issueLabel(draft: OkrDraft, issue: DraftIssue) {
  const oi = draft.objectives.findIndex((o) => o.key === issue.objectiveKey);
  if (oi < 0) return "";
  if (!issue.krKey) return `O${oi + 1}: `;
  const ki = draft.objectives[oi].keyResults.findIndex((kr) => kr.key === issue.krKey);
  return `KR ${oi + 1}.${ki + 1}: `;
}
