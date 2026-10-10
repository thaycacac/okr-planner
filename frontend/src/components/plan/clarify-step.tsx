"use client";

import { CircleAlertIcon, InfoIcon, SparklesIcon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useState } from "react";
import { cn } from "cn";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { LoadError } from "@/components/settings/load-error";
import { useApiErrorMessage } from "@/hooks/use-api-error-message";
import { useLoad } from "@/hooks/use-load";
import { api } from "@/lib/api/client";
import {
  type ClarificationQuestion,
  errorDetail,
  type LlmSettings,
  type PlanRunDetail,
  type QuarterDetail,
} from "@/lib/api/types";
import { okrCodes } from "@/lib/plan/plan-view";
import { isActive } from "@/lib/plan/progress";
import { quarterLabel, quarterSlug, toRef } from "@/lib/plan/quarter";

import { AiBadge, aiIdentity } from "./plan-bits";

const MAX_ROUNDS = 2;

type Loaded = { run: PlanRunDetail; quarter: QuarterDetail; settings: LlmSettings | null };
type Answers = Record<string, string>;

function storageKey(jobId: string) {
  return `okr-planner.answers.${jobId}`;
}

function readAnswers(jobId: string): Answers {
  try {
    const raw = window.sessionStorage.getItem(storageKey(jobId));
    return raw ? (JSON.parse(raw) as Answers) : {};
  } catch {
    return {};
  }
}

export function ClarifyStep({ jobId }: { jobId: string }) {
  const load = useCallback(async (): Promise<Loaded | undefined> => {
    const run = await api.GET("/plans/{job_id}", { params: { path: { job_id: jobId } } });
    if (!run.data) return undefined;
    const [quarter, settings] = await Promise.all([
      api.GET("/quarters/{quarter_id}", { params: { path: { quarter_id: run.data.quarter_id } } }),
      api.GET("/settings/llm"),
    ]);
    if (!quarter.data) return undefined;
    return { run: run.data, quarter: quarter.data, settings: settings.data ?? null };
  }, [jobId]);
  const [state, retry] = useLoad(load);

  if (state.status === "loading") {
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-4" aria-busy="true">
        <Skeleton className="h-8 w-80" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }
  if (state.status === "error") return <LoadError onRetry={retry} />;
  return <ClarifyRedirect jobId={jobId} loaded={state.data} />;
}

function ClarifyRedirect({ jobId, loaded }: { jobId: string; loaded: Loaded }) {
  const router = useRouter();
  const t = useTranslations("plan.clarify");
  const status = loaded.run.status;
  const slug = quarterSlug(toRef(loaded.quarter));
  useEffect(() => {
    if (isActive(status) || status === "failed" || status === "cancelled" || status === "invalid_input") {
      router.replace(`/plan/new/generate?job=${jobId}`);
    } else if (status === "succeeded") {
      router.replace(`/q/${slug}/tasks`);
    }
  }, [jobId, router, slug, status]);

  if (status !== "needs_clarification") {
    return (
      <p className="flex items-center gap-2 text-sm text-muted-foreground" role="status">
        <Spinner /> {t("redirecting")}
      </p>
    );
  }
  return <ClarifyForm jobId={jobId} loaded={loaded} />;
}

function ClarifyForm({ jobId, loaded }: { jobId: string; loaded: Loaded }) {
  const t = useTranslations("plan.clarify");
  const apiErrorMessage = useApiErrorMessage();
  const router = useRouter();
  const { run, quarter, settings } = loaded;
  const ref = toRef(quarter);
  const slug = quarterSlug(ref);
  const [answers, setAnswers] = useState<Answers>(() => readAnswers(jobId));
  const [skipped, setSkipped] = useState<Set<string>>(() => new Set());
  const [submit, setSubmit] = useState<{ busy: boolean; error: string | null }>({ busy: false, error: null });

  useEffect(() => {
    try {
      window.sessionStorage.setItem(storageKey(jobId), JSON.stringify(answers));
    } catch {
      // sessionStorage may be unavailable (private mode); answers still live in memory.
    }
  }, [answers, jobId]);

  const krCodes = okrCodes(quarter.objectives).krs;
  const krLabel = new Map<number, { code: string; text: string }>();
  quarter.objectives.forEach((o) =>
    o.key_results.forEach((kr) => krLabel.set(kr.id, { code: krCodes.get(kr.id)!, text: kr.text })),
  );

  const questions = run.questions;
  const required = questions.filter((q) => q.source === "precheck");
  const answered = questions.filter((q) => !skipped.has(q.id) && (answers[q.id] ?? "").trim() !== "");
  const handled = questions.filter((q) => answered.includes(q) || skipped.has(q.id));
  const missingRequired = required.filter((q) => (answers[q.id] ?? "").trim() === "");
  const skippedAny = questions.some((q) => skipped.has(q.id));
  const canSubmit = missingRequired.length === 0 && (answered.length > 0 || skippedAny);

  function setAnswer(id: string, value: string) {
    setAnswers((prev) => ({ ...prev, [id]: value }));
    if (value.trim()) setSkipped((prev) => (prev.has(id) ? new Set([...prev].filter((x) => x !== id)) : prev));
  }

  function toggleSkip(id: string) {
    setSkipped((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function send() {
    setSubmit({ busy: true, error: null });
    const body = {
      answers: answered.map((q) => ({ question_id: q.id, answer: answers[q.id].trim() })),
      // Skipping a question means "don't ask me again": go straight to generation.
      generate_anyway: skippedAny,
    };
    const { data, error, response } = await api.POST("/plans/{job_id}/answers", {
      params: { path: { job_id: jobId } },
      body,
    });
    if (data) {
      window.sessionStorage.removeItem(storageKey(jobId));
      router.push(`/plan/new/generate?job=${data.job_id}`);
      return;
    }
    const detail = errorDetail(error);
    const message =
      response.status === 409 && detail?.code === "plan_already_answered"
        ? t("alreadyAnswered")
        : apiErrorMessage(error, t("submitError"));
    setSubmit({ busy: false, error: message });
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <h1 className="font-heading text-2xl font-semibold tracking-tight">
            {t("title", { count: questions.length, quarter: quarterLabel(ref) })}
          </h1>
          <AiBadge identity={aiIdentity(run, settings)} />
        </div>
        <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
        <div className="flex flex-col gap-1.5">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{t("answered", { done: handled.length, total: questions.length })}</span>
            <span>{t("round", { round: run.round, max: MAX_ROUNDS })}</span>
          </div>
          <Progress
            value={questions.length ? (handled.length / questions.length) * 100 : 0}
            aria-label={t("progressLabel")}
          />
        </div>
        {run.round >= MAX_ROUNDS && (
          <Alert>
            <InfoIcon />
            <AlertDescription>{t("lastRound")}</AlertDescription>
          </Alert>
        )}
      </div>

      <ol className="flex flex-col gap-4">
        {questions.map((q, i) => (
          <QuestionCard
            key={q.id}
            index={i}
            question={q}
            kr={q.key_result_id ? krLabel.get(q.key_result_id) : undefined}
            value={answers[q.id] ?? ""}
            skipped={skipped.has(q.id)}
            onChange={(v) => setAnswer(q.id, v)}
            onToggleSkip={() => toggleSkip(q.id)}
            editHref={`/plan/new/okr?q=${slug}`}
          />
        ))}
      </ol>

      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-border bg-background/95 pb-[env(safe-area-inset-bottom)] backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 md:px-8">
          <Button asChild variant="outline">
            <Link href={`/plan/new/okr?q=${slug}`}>{t("editOkr")}</Link>
          </Button>
          <div className="flex flex-wrap items-center gap-3">
            {submit.error ? (
              <span className="text-sm text-destructive" role="alert">
                {submit.error}
              </span>
            ) : missingRequired.length > 0 ? (
              <span className="text-sm text-muted-foreground">
                {t("missingRequired", { count: missingRequired.length })}
              </span>
            ) : !canSubmit ? (
              <span className="text-sm text-muted-foreground">{t("needOne")}</span>
            ) : null}
            <Button onClick={send} disabled={!canSubmit || submit.busy}>
              {submit.busy && <Spinner data-icon="inline-start" />}
              {!skippedAny ? t("submit") : answered.length === 0 ? t("skipAndGenerate") : t("submitAndGenerate")}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function QuestionCard({
  index,
  question,
  kr,
  value,
  skipped,
  onChange,
  onToggleSkip,
  editHref,
}: {
  index: number;
  question: ClarificationQuestion;
  kr: { code: string; text: string } | undefined;
  value: string;
  skipped: boolean;
  onChange: (value: string) => void;
  onToggleSkip: () => void;
  editHref: string;
}) {
  const t = useTranslations("plan.clarify");
  const required = question.source === "precheck";
  const id = `answer-${question.id}`;
  return (
    <li>
      <Card size="sm" className={cn(skipped && "opacity-60")}>
        <CardContent className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="font-mono text-muted-foreground">{t("questionNumber", { n: index + 1 })}</span>
            {kr && (
              <Badge variant="outline" className="max-w-full truncate" title={kr.text}>
                {kr.code} · {kr.text}
              </Badge>
            )}
            {required ? (
              <Badge variant="outline" className="border-destructive/50 text-foreground">
                {t("required")}
              </Badge>
            ) : (
              <Badge variant="secondary">
                <SparklesIcon aria-hidden />
                {t("optional")}
              </Badge>
            )}
          </div>
          <label htmlFor={id} className="font-medium">
            {question.question}
          </label>
          {question.reason && (
            <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
              <CircleAlertIcon className="mt-0.5 size-3.5 shrink-0" aria-hidden />
              {t("reason", { reason: question.reason })}
            </p>
          )}
          <Textarea
            id={id}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={t("placeholder")}
            rows={3}
            disabled={skipped}
            aria-required={required}
          />
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
            <Link href={editHref} className="text-foreground underline underline-offset-4">
              {t("editKr")}
            </Link>
            {!required && (
              <Button variant="ghost" size="sm" onClick={onToggleSkip}>
                {skipped ? t("unskip") : t("skip")}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </li>
  );
}
