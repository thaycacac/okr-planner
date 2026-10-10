"use client";

import {
  CheckCircle2Icon,
  CheckIcon,
  CircleAlertIcon,
  CircleDashedIcon,
  CircleIcon,
  InfoIcon,
  MinusIcon,
  TriangleAlertIcon,
  XIcon,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { type ReactNode, useCallback, useEffect, useState } from "react";
import { cn } from "cn";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { useApiErrorMessage } from "@/hooks/use-api-error-message";
import { useLoad } from "@/hooks/use-load";
import { usePlanJob } from "@/hooks/use-plan-job";
import { api } from "@/lib/api/client";
import { errorDetail, type LlmSettings, type PlanRunDetail, type PlanStage, type QuarterDetail } from "@/lib/api/types";
import { loadDraft } from "@/lib/plan/okr-draft";
import { okrCodes } from "@/lib/plan/plan-view";
import { currentStage, isActive, type KrProgress, type ProgressState, STAGES, type StageState } from "@/lib/plan/progress";
import { quarterLabel, quarterSlug, toRef } from "@/lib/plan/quarter";
import { startPlan } from "@/lib/plan/start-plan";

import { AiBadge, aiIdentity } from "./plan-bits";
import { formatElapsed, usePlanFormat } from "./use-plan-format";

const SLOW_AFTER_SECONDS = 60;
const SUGGESTIONS = ["switch_model", "switch_provider", "check_connection"] as const;
const isSuggestion = (value: string): value is (typeof SUGGESTIONS)[number] =>
  (SUGGESTIONS as readonly string[]).includes(value);
const REDIRECT_AFTER_MS = 1500;
const RESUME_CONFLICTS = ["okr_changed", "plan_not_resumable", "plan_in_progress"] as const;
const isResumeConflict = (value: string): value is (typeof RESUME_CONFLICTS)[number] =>
  (RESUME_CONFLICTS as readonly string[]).includes(value);
// Precheck messages follow the OKR's language, not the UI's, so known codes are translated here.
const INPUT_ISSUES = [
  "no_objectives",
  "too_many_objectives",
  "objective_too_short",
  "objective_too_long",
  "no_key_results",
  "too_many_key_results",
  "kr_too_short",
  "kr_too_long",
  "duplicate_id",
  "duplicate_kr",
  "context_too_long",
  "answer_too_long",
] as const;
const isInputIssue = (value: string): value is (typeof INPUT_ISSUES)[number] =>
  (INPUT_ISSUES as readonly string[]).includes(value);

type Restart = { busy: "regenerate" | "resume" | null; error: string | null };

export function GenerateStep({ jobId }: { jobId: string }) {
  const t = useTranslations("plan.generate");
  const job = usePlanJob(jobId);
  if (job.load === "not_found") {
    return (
      <Alert className="max-w-xl">
        <InfoIcon />
        <AlertDescription className="flex flex-wrap items-center gap-3 [&_a]:no-underline">
          {t("notFound")}
          <Button asChild size="sm" variant="outline">
            <Link href="/plan/new">{t("startOver")}</Link>
          </Button>
        </AlertDescription>
      </Alert>
    );
  }
  if (job.load === "error" && !job.detail) {
    return (
      <Alert variant="destructive" className="max-w-xl">
        <CircleAlertIcon />
        <AlertDescription className="flex flex-wrap items-center gap-3">
          {t("loadError")}
          <Button size="sm" variant="outline" onClick={job.retry}>
            {t("retry")}
          </Button>
        </AlertDescription>
      </Alert>
    );
  }
  if (!job.detail) return <GenerateSkeleton />;
  return <GenerateView jobId={jobId} detail={job.detail} progress={job.progress} refresh={job.refresh} />;
}

function GenerateSkeleton() {
  return (
    <div className="grid gap-6 md:grid-cols-[14rem_minmax(0,1fr)]" aria-busy="true">
      <Skeleton className="hidden h-56 md:block" />
      <div className="flex flex-col gap-4">
        <Skeleton className="h-8 w-72" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    </div>
  );
}

type Context = { quarter: QuarterDetail; settings: LlmSettings | null };

function GenerateView({
  jobId,
  detail,
  progress,
  refresh,
}: {
  jobId: string;
  detail: PlanRunDetail;
  progress: ProgressState;
  refresh: () => Promise<PlanRunDetail | null>;
}) {
  const quarterId = detail.quarter_id;
  const load = useCallback(async (): Promise<Context | undefined> => {
    const [quarter, settings] = await Promise.all([
      api.GET("/quarters/{quarter_id}", { params: { path: { quarter_id: quarterId } } }),
      api.GET("/settings/llm"),
    ]);
    return quarter.data ? { quarter: quarter.data, settings: settings.data ?? null } : undefined;
  }, [quarterId]);
  const [ctx] = useLoad(load);
  if (ctx.status !== "ready") return <GenerateSkeleton />;
  return <GenerateScreen jobId={jobId} detail={detail} progress={progress} refresh={refresh} ctx={ctx.data} />;
}

function GenerateScreen({
  jobId,
  detail,
  progress,
  refresh,
  ctx,
}: {
  jobId: string;
  detail: PlanRunDetail;
  progress: ProgressState;
  refresh: () => Promise<PlanRunDetail | null>;
  ctx: Context;
}) {
  const t = useTranslations("plan.generate");
  const tOkr = useTranslations("plan.okr");
  const fmt = usePlanFormat();
  const router = useRouter();
  const ref = toRef(ctx.quarter);
  const slug = quarterSlug(ref);
  const active = isActive(detail.status);
  const identity = aiIdentity(detail, ctx.settings);
  const [now, setNow] = useState(() => Date.now());
  const [cancelling, setCancelling] = useState(false);
  const [restart, setRestart] = useState<Restart>({ busy: null, error: null });
  const apiErrorMessage = useApiErrorMessage();
  const [draftPending] = useState(() => loadDraft(slug)?.synced === false);

  useEffect(() => {
    if (!active) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [active]);

  useEffect(() => {
    if (detail.status === "needs_clarification") router.replace(`/plan/new/clarify?job=${jobId}`);
    if (detail.status !== "succeeded") return;
    const timer = window.setTimeout(() => router.replace(`/q/${slug}/tasks`), REDIRECT_AFTER_MS);
    return () => window.clearTimeout(timer);
  }, [detail.status, jobId, router, slug]);

  const startedAt = Date.parse(detail.started_at ?? detail.created_at);
  const endedAt = detail.finished_at ? Date.parse(detail.finished_at) : now;
  const elapsed = Math.max(0, (endedAt - startedAt) / 1000);
  const stage = currentStage(progress);
  const reading = active && (stage === null || stage === "precheck" || stage === "clarify");
  const krCodes = okrCodes(ctx.quarter.objectives).krs;
  const krRows = ctx.quarter.objectives.flatMap((o) =>
    o.key_results.map((kr) => ({ id: kr.id, code: krCodes.get(kr.id)!, text: kr.text })),
  );
  // A finished run restored from step traces only knows the KRs it reached, not how many there were.
  const plannedKrs = ctx.quarter.objectives
    .filter((o) => o.active)
    .reduce((n, o) => n + o.key_results.filter((kr) => kr.active).length, 0);
  const percent = detail.status === "succeeded" ? 100 : progress.percent;
  const failedStep = detail.status === "failed" ? (detail.error?.step ?? null) : null;
  const stageState = (s: PlanStage): StageState => (s === failedStep ? "failed" : progress.stages[s]);
  // KRs reused from an earlier failed run leave no step trace, so a resumed run may show 0 done
  // while still keeping some; only a first attempt can be sure nothing is kept.
  const resumedRun = detail.parent_id !== null && detail.skip_clarification;
  const noneDecomposed = failedStep === "decompose" && !resumedRun && !progress.decomposed?.completed;
  const decomposed = progress.decomposed
    ? { completed: progress.decomposed.completed, total: Math.max(progress.decomposed.total, plannedKrs) }
    : noneDecomposed && plannedKrs > 0
      ? { completed: 0, total: plannedKrs }
      : null;

  async function cancel() {
    setCancelling(true);
    await api.POST("/plans/{job_id}/cancel", { params: { path: { job_id: jobId } } });
    await refresh();
    setCancelling(false);
  }

  async function regenerate() {
    setRestart({ busy: "regenerate", error: null });
    const result = await startPlan(api, ctx.quarter.id, slug, {
      domain: tOkr("domain"),
      constraints: tOkr("constraints"),
    });
    if ("job" in result) {
      router.push(`/plan/new/generate?job=${result.job.job_id}`);
      return;
    }
    setRestart({ busy: null, error: apiErrorMessage(result.error, t("restartError")) });
  }

  async function resume() {
    setRestart({ busy: "resume", error: null });
    let result;
    try {
      result = await api.POST("/plans/{job_id}/resume", { params: { path: { job_id: jobId } } });
    } catch {
      setRestart({ busy: null, error: t("restartError") });
      return;
    }
    if (result.data) {
      router.push(`/plan/new/generate?job=${result.data.job_id}`);
      return;
    }
    const code = errorDetail(result.error)?.code;
    const conflict = result.response.status === 409 && code && isResumeConflict(code) ? code : null;
    setRestart({ busy: null, error: conflict ? t(`resumeErrors.${conflict}`) : t("restartError") });
    // The run is no longer resumable after a conflict; refreshing hides the resume button.
    if (conflict) await refresh();
  }

  return (
    <div className="grid gap-6 md:grid-cols-[14rem_minmax(0,1fr)]">
      <aside className="hidden flex-col gap-4 md:flex" aria-label={t("stagesLabel")}>
        <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{t("stagesLabel")}</p>
        <ol className="flex flex-col gap-2.5">
          {STAGES.map((s) => (
            <li key={s} className="flex items-center gap-2 text-sm">
              <StageIcon state={stageState(s)} />
              <span className={cn(stageState(s) === "running" ? "font-semibold" : "text-muted-foreground")}>
                {t(`stages.${s}`)}
                {s === "decompose" && decomposed
                  ? ` (${decomposed.completed}/${decomposed.total})`
                  : null}
              </span>
              <span className="sr-only">{t(`stageStates.${stageState(s)}`)}</span>
            </li>
          ))}
        </ol>
        <AiBadge identity={identity} className="w-fit" />
      </aside>

      <div className="flex min-w-0 flex-col gap-5">
        <div className="flex flex-col gap-1">
          <h1 className="font-heading text-2xl font-semibold tracking-tight">
            {reading
              ? t("readingTitle")
              : t(active ? "title" : "endedTitle", { quarter: quarterLabel(ref) })}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t(detail.status === "failed" || detail.status === "cancelled" ? "stoppedAfter" : "elapsed", {
              time: formatElapsed(elapsed),
            })}
            {active && ` · ${identity?.provider === "local" ? t("expectLocal") : t("expectOpenai")}`}
          </p>
          <AiBadge identity={identity} className="w-fit md:hidden" />
        </div>

        <div className="flex flex-col gap-2" role="status" aria-live="polite">
          <div className="flex items-end justify-between gap-2">
            <span className="font-heading text-4xl font-semibold tabular-nums">{percent}%</span>
            {decomposed && (
              <span className="text-xs text-muted-foreground">
                {t("krDone", { done: decomposed.completed, total: decomposed.total })}
              </span>
            )}
          </div>
          <Progress value={percent} aria-label={t("progressLabel")} />
          <span className="sr-only">{stage ? t(`stages.${stage}`) : null}</span>
        </div>

        {active && elapsed > SLOW_AFTER_SECONDS && (
          <Alert>
            <InfoIcon />
            <AlertDescription>{t("slow")}</AlertDescription>
          </Alert>
        )}

        <Outcome
          detail={detail}
          slug={slug}
          krCode={(id) => krRows.find((k) => k.id === id)?.code ?? null}
          onRegenerate={regenerate}
          onResume={resume}
          restart={restart}
          draftPending={draftPending}
          noneDecomposed={noneDecomposed}
        />

        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <caption className="sr-only">{t("tableCaption")}</caption>
            <thead className="bg-muted/50 text-left text-xs text-muted-foreground uppercase">
              <tr>
                <th scope="col" className="px-3 py-2 font-medium">{t("colKr")}</th>
                <th scope="col" className="px-3 py-2 font-medium">{t("colName")}</th>
                <th scope="col" className="hidden px-3 py-2 font-medium sm:table-cell">{t("colProgress")}</th>
                <th scope="col" className="px-3 py-2 text-right font-medium">{t("colResult")}</th>
              </tr>
            </thead>
            <tbody>
              {krRows.map((row) => (
                <KrProgressRow
                  key={row.id}
                  code={row.code}
                  text={row.text}
                  progress={progress.krs[row.id]}
                  finished={detail.status === "succeeded" || progress.stages.decompose === "done"}
                  runEnded={!active}
                  fmtSeconds={(ms) => fmt.number(Math.round(ms / 100) / 10)}
                />
              ))}
            </tbody>
          </table>
        </div>

        {active && (
          <div className="flex flex-wrap items-center justify-between gap-3">
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="outline" className="border-destructive/40 text-destructive hover:text-destructive" disabled={cancelling}>
                  {cancelling && <Spinner data-icon="inline-start" />}
                  {t("cancel")}
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>{t("cancelTitle")}</AlertDialogTitle>
                  <AlertDialogDescription>{t("cancelBody")}</AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>{t("cancelKeep")}</AlertDialogCancel>
                  <AlertDialogAction variant="destructive" onClick={cancel}>
                    {t("cancelConfirm")}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
            <span className="text-xs text-muted-foreground">{t("autoOpen")}</span>
          </div>
        )}
      </div>
    </div>
  );
}

function StageIcon({ state }: { state: StageState }) {
  switch (state) {
    case "done":
      return <CheckCircle2Icon aria-hidden className="size-4 text-success" />;
    case "running":
      return <Spinner aria-hidden className="size-4" />;
    case "skipped":
      return <MinusIcon aria-hidden className="size-4 text-muted-foreground" />;
    case "failed":
      return <XIcon aria-hidden className="size-4 text-destructive" />;
    default:
      return <CircleIcon aria-hidden className="size-4 text-muted-foreground/50" />;
  }
}

function KrProgressRow({
  code,
  text,
  progress,
  finished,
  runEnded,
  fmtSeconds,
}: {
  code: string;
  text: string;
  progress: KrProgress | undefined;
  finished: boolean;
  runEnded: boolean;
  fmtSeconds: (ms: number) => string;
}) {
  const t = useTranslations("plan.generate");
  const reported = progress?.state ?? (finished ? "done" : "waiting");
  const state = runEnded && reported !== "done" && reported !== "failed" ? "notRun" : reported;
  const bar =
    state === "done"
      ? "w-full bg-success"
      : state === "running"
        ? "w-1/2 animate-pulse bg-foreground"
        : state === "retry"
          ? "w-1/3 bg-warning"
          : state === "failed"
            ? "w-full bg-destructive"
            : "w-0";
  return (
    <tr className={cn("border-t border-border", state === "failed" && "bg-destructive/5")}>
      <td className="px-3 py-2 font-mono text-xs whitespace-nowrap text-muted-foreground">{code}</td>
      <td className="max-w-0 truncate px-3 py-2" title={text}>
        {text}
      </td>
      <td className="hidden w-40 px-3 py-2 sm:table-cell">
        <div className="h-1.5 overflow-hidden rounded-full bg-muted" aria-hidden>
          <div className={cn("h-full rounded-full transition-all", bar)} />
        </div>
      </td>
      <td className="px-3 py-2 text-right text-xs whitespace-nowrap">
        {state === "done" && (
          <span className="inline-flex items-center gap-1 text-success">
            <CheckIcon className="size-3.5" aria-hidden />
            {progress?.durationMs ? t("krDoneIn", { seconds: fmtSeconds(progress.durationMs) }) : t("krStates.done")}
          </span>
        )}
        {state === "running" && (
          <span className="inline-flex items-center gap-1">
            <Spinner className="size-3.5" aria-hidden />
            {t("krStates.running")}
          </span>
        )}
        {state === "retry" && <span className="text-warning">{t("krRetry", { attempt: progress?.attempt ?? 2 })}</span>}
        {state === "failed" && <span className="text-destructive">{t("krStates.failed")}</span>}
        {state === "waiting" && (
          <span className="inline-flex items-center gap-1 text-muted-foreground">
            <CircleDashedIcon className="size-3.5" aria-hidden />
            {t("krStates.waiting")}
          </span>
        )}
        {state === "notRun" && <span className="text-muted-foreground">{t("krStates.notRun")}</span>}
      </td>
    </tr>
  );
}

function Outcome({
  detail,
  slug,
  krCode,
  onRegenerate,
  onResume,
  restart,
  draftPending,
  noneDecomposed,
}: {
  detail: PlanRunDetail;
  slug: string;
  krCode: (id: number) => string | null;
  onRegenerate: () => void;
  onResume: () => void;
  restart: Restart;
  /** A local OKR draft was edited but never submitted; the restart buttons ignore it. */
  draftPending: boolean;
  noneDecomposed: boolean;
}) {
  const t = useTranslations("plan.generate");
  const resumable = detail.status === "failed" && detail.resumable;
  const resume = resumable && (
    <Button size="sm" onClick={onResume} disabled={restart.busy !== null}>
      {restart.busy === "resume" && <Spinner data-icon="inline-start" />}
      {t("resume")}
    </Button>
  );
  const regenerate = (
    <Button size="sm" variant={resumable ? "outline" : "default"} onClick={onRegenerate} disabled={restart.busy !== null}>
      {restart.busy === "regenerate" && <Spinner data-icon="inline-start" />}
      {t("regenerate")}
    </Button>
  );
  const regenerateHint = (
    <span className="text-xs text-muted-foreground">
      {t(resumable ? (noneDecomposed ? "resumeHintFresh" : "resumeHint") : "regenerateHint")}
    </span>
  );
  const draftNotice = draftPending && (
    <p className="flex items-start gap-1.5 text-xs">
      <TriangleAlertIcon aria-hidden className="mt-0.5 size-3.5 shrink-0 text-warning" />
      {t("draftPending")}
    </p>
  );
  const editOkr = (
    <Button asChild size="sm" variant="outline">
      <Link href={`/plan/new/okr?q=${slug}`}>{t("editOkr")}</Link>
    </Button>
  );
  const restartError = restart.error && (
    <p role="alert" className="text-xs text-destructive">
      {restart.error}
    </p>
  );

  switch (detail.status) {
    case "succeeded":
      return (
        <Alert className="border-success/40 bg-success-muted text-success">
          <CheckCircle2Icon />
          <AlertTitle>{t("succeeded", { count: detail.task_count })}</AlertTitle>
          <AlertDescription className="text-success">{t("opening")}</AlertDescription>
          <Actions>
            <Button asChild size="sm" variant="outline">
              <Link href={`/q/${slug}/tasks`}>{t("openPlan")}</Link>
            </Button>
          </Actions>
        </Alert>
      );
    case "invalid_input":
      return (
        <Alert variant="destructive" className="*:data-[slot=alert-description]:text-foreground">
          <CircleAlertIcon />
          <AlertTitle>{t("invalidTitle")}</AlertTitle>
          <AlertDescription className="flex flex-col gap-2">
            <ul className="list-disc pl-4">
              {detail.issues.map((issue, i) => (
                <li key={i}>
                  {issue.key_result_id && krCode(issue.key_result_id) ? `${krCode(issue.key_result_id)}: ` : ""}
                  {isInputIssue(issue.code) ? t(`inputIssues.${issue.code}`) : issue.message}
                </li>
              ))}
            </ul>
          </AlertDescription>
          <Actions>{editOkr}</Actions>
        </Alert>
      );
    case "cancelled":
      return (
        <Alert>
          <InfoIcon />
          <AlertTitle>{t("cancelled")}</AlertTitle>
          <Actions notice={draftNotice} hint={regenerateHint} error={restartError}>
            {regenerate}
            {editOkr}
          </Actions>
        </Alert>
      );
    case "failed": {
      const error = detail.error;
      const code = error?.code ?? "internal_error";
      const kr = error?.key_result_id ? krCode(error.key_result_id) : null;
      const where = kr ?? (error?.step ? t(`stages.${error.step}`) : "—");
      return (
        <Alert variant="destructive" className="*:data-[slot=alert-description]:text-foreground">
          <CircleAlertIcon />
          <AlertTitle>{t(`failures.${code}.title`, { where })}</AlertTitle>
          <AlertDescription className="flex flex-col gap-2">
            <span>
              {t(`failures.${code}.body`, {
                provider: error?.provider ?? "—",
                model: error?.model ?? "—",
                attempts: error?.attempts ?? 0,
              })}
            </span>
            {error && error.suggestions.length > 0 && (
              <ul className="list-disc pl-4 text-xs">
                {error.suggestions.map((s) => (
                  <li key={s}>{isSuggestion(s) ? t(`suggestions.${s}`) : s}</li>
                ))}
              </ul>
            )}
            <span className="text-xs text-muted-foreground">{t("noFallback")}</span>
            {error?.message && (
              <details className="text-xs">
                <summary className="cursor-pointer text-muted-foreground">{t("technicalDetails")}</summary>
                <p className="mt-1 font-mono break-all text-muted-foreground">{error.message}</p>
              </details>
            )}
          </AlertDescription>
          <Actions notice={draftNotice} hint={regenerateHint} error={restartError}>
            {resume}
            {regenerate}
            <Button asChild size="sm" variant="outline">
              <Link href="/settings/ai">{t("openAiSettings")}</Link>
            </Button>
            {editOkr}
          </Actions>
        </Alert>
      );
    }
    default:
      return null;
  }
}

/** Kept outside AlertDescription, whose link styles would underline and recolor button links. */
function Actions({
  children,
  notice,
  hint,
  error,
}: {
  children: ReactNode;
  notice?: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
}) {
  return (
    <div className="col-start-2 mt-2 flex flex-col gap-2 text-foreground">
      {notice}
      <div className="flex flex-wrap gap-2">{children}</div>
      {hint}
      {error}
    </div>
  );
}
