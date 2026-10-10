"use client";

import {
  CalendarDaysIcon,
  ChartColumnIcon,
  HistoryIcon,
  InfoIcon,
  ListTreeIcon,
  PencilIcon,
  RefreshCwIcon,
  SparklesIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { cn } from "cn";

import { GuardedLink } from "@/components/app-shell/unsaved-changes";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { LoadError } from "@/components/settings/load-error";
import type { QuarterSummary } from "@/lib/api/types";
import { isActive } from "@/lib/plan/progress";
import { previousQuarterWithPlan, type QuarterRef, quarterLabel, quarterSlug, toRef } from "@/lib/plan/quarter";

import { ExportButton } from "./export-dialog";
import { FeasibilityChip, FeasibilityPanel } from "./feasibility-panel";
import { AiBadge, aiIdentity } from "./plan-bits";
import { usePlanData } from "./plan-data";
import { RescheduleButton, RescheduleProvider, useReschedule } from "./reschedule-flow";
import { TaskDialogsProvider } from "./task-dialogs";
import { TaskSheet } from "./task-sheet";
import { usePlanFormat } from "./use-plan-format";
import { WeekSummaryCard } from "./week-calendar";

export function PlanShell({ children }: { children: ReactNode }) {
  const data = usePlanData();
  const t = useTranslations("plan.result");
  const { state, retry, ref, slug, view, feasibility } = data;
  const label = quarterLabel(ref);
  const pathname = usePathname();
  // Workload and options pages lay out their own right-hand column.
  const wide = /\/(workload|options)$/.test(pathname);

  if (state.status === "loading") {
    return (
      <div className="flex flex-col gap-4" aria-busy="true">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96 max-w-full" />
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]">
          <div className="flex flex-col gap-2">
            {Array.from({ length: 8 }, (_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
          <FeasibilityPanel summary={null} slug={slug} loading className="hidden xl:flex" />
        </div>
      </div>
    );
  }
  if (state.status === "error") return <LoadError onRetry={retry} />;

  const { summary, run, settings, quarters } = state.data;
  const runBanner = summary ? <RunBanner summary={summary} /> : null;

  if (!view || view.taskCount === 0) {
    const hasObjectives = (summary?.objective_count ?? 0) > 0;
    const others = quarters.filter((q) => q.task_count > 0 && q.id !== summary?.id);
    return (
      <div className="flex max-w-2xl flex-col gap-4">
        <h1 className="font-heading text-2xl font-semibold tracking-tight">{t("title", { quarter: label })}</h1>
        {runBanner}
        <div className="flex flex-col items-start gap-3 rounded-xl border border-dashed border-border p-6">
          <SparklesIcon className="size-6 text-muted-foreground" aria-hidden />
          <p className="font-medium">{t("empty", { quarter: label })}</p>
          <p className="text-sm text-muted-foreground">{t("emptyBody")}</p>
          <Button asChild>
            <Link href={hasObjectives ? `/plan/new/okr?q=${slug}` : `/plan/new?q=${slug}`}>{t("enterOkr")}</Link>
          </Button>
        </div>
        {others.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="text-muted-foreground">{t("otherPlans")}</span>
            {others.map((q) => (
              <Button key={q.id} asChild size="sm" variant="outline">
                <Link href={`/q/${quarterSlug(toRef(q))}/tasks`}>{quarterLabel(toRef(q))}</Link>
              </Button>
            ))}
          </div>
        )}
      </div>
    );
  }

  const schedule = state.data.schedule;
  const needsReschedule = !schedule || schedule.stale;

  return (
    <RescheduleProvider>
      <TaskDialogsProvider>
        <div className="flex flex-col gap-5">
          <PageHead
            label={label}
            slug={slug}
            counts={{ objectives: view.objectives.length, krs: view.krCount, tasks: view.taskCount }}
            totalMinutes={view.totalMinutes}
            identity={aiIdentity(run, settings)}
            generatedAt={run?.finished_at ?? schedule?.created_at ?? null}
            chip={
              needsReschedule ? (
                <StalePill />
              ) : (
                <FeasibilityChip summary={feasibility} slug={slug} className="xl:hidden" />
              )
            }
            actions={
              <>
                {summary && <ExportButton quarter={summary} />}
                <PreviousQuarterLink quarters={quarters} current={ref} />
              </>
            }
          />
          {runBanner}
          {needsReschedule && <StaleBanner hasSchedule={schedule !== null} />}
          {wide ? (
            children
          ) : (
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]">
              <div className="min-w-0">{children}</div>
              <aside className="hidden flex-col gap-4 xl:flex" aria-label={t("railLabel")}>
                <div className="sticky top-20 flex flex-col gap-4">
                  <FeasibilityPanel summary={feasibility} slug={slug} />
                  {pathname.endsWith("/calendar") && <WeekSummaryCard />}
                </div>
              </aside>
            </div>
          )}
          <TaskSheet plan={view} />
          <MobileStaleBar show={needsReschedule} />
        </div>
      </TaskDialogsProvider>
    </RescheduleProvider>
  );
}

function StalePill() {
  const t = useTranslations("plan.reschedule");
  const { start, busy } = useReschedule();
  return (
    <Button variant="outline" size="sm" className="border-dashed" onClick={start} disabled={busy}>
      <RefreshCwIcon data-icon="inline-start" className={cn(busy && "animate-spin")} aria-hidden />
      {t("pill")}
    </Button>
  );
}

function StaleBanner({ hasSchedule }: { hasSchedule: boolean }) {
  const t = useTranslations("plan.reschedule");
  return (
    <div
      role="status"
      className="flex flex-wrap items-center gap-3 rounded-xl border border-dashed border-border bg-muted/40 px-4 py-3 text-sm"
    >
      <RefreshCwIcon className="size-4 shrink-0 text-muted-foreground" aria-hidden />
      <span className="min-w-0 flex-1">
        <span className="font-medium">{hasSchedule ? t("staleTitle") : t("noScheduleTitle")}</span>{" "}
        <span className="text-muted-foreground">{t("staleBody")}</span>
      </span>
      <span className="hidden md:inline-flex">
        <RescheduleButton />
      </span>
    </div>
  );
}

/** Sticky bar above the tab bar on phones, where the page-head button scrolls away. */
function MobileStaleBar({ show }: { show: boolean }) {
  const t = useTranslations("plan.reschedule");
  if (!show) return null;
  return (
    <div className="fixed inset-x-0 bottom-[calc(3.5rem+env(safe-area-inset-bottom))] z-30 flex items-center gap-3 border-t border-border bg-background/95 px-4 py-2 text-sm backdrop-blur md:hidden">
      <span className="min-w-0 flex-1 truncate">{t("mobileBar")}</span>
      <RescheduleButton />
    </div>
  );
}

function PreviousQuarterLink({ quarters, current }: { quarters: QuarterSummary[]; current: QuarterRef }) {
  const t = useTranslations("plan.result");
  const previous = previousQuarterWithPlan(quarters, current);
  if (!previous) return null;
  return (
    <Button asChild size="sm" variant="ghost">
      <GuardedLink href={`/q/${quarterSlug(previous)}/tasks`}>
        <HistoryIcon data-icon="inline-start" />
        {t("previousQuarter", { quarter: quarterLabel(previous) })}
      </GuardedLink>
    </Button>
  );
}

function RunBanner({ summary }: { summary: QuarterSummary }) {
  const t = useTranslations("plan.result");
  const status = summary.latest_plan_status;
  const job = summary.latest_plan_run_id;
  if (!job || !status) return null;
  if (isActive(status)) {
    return (
      <Alert>
        <InfoIcon />
        <AlertDescription className="flex flex-wrap items-center gap-3 [&_a]:no-underline">
          {t("runActive")}
          <Button asChild size="sm" variant="outline">
            <Link href={`/plan/new/generate?job=${job}`}>{t("viewProgress")}</Link>
          </Button>
        </AlertDescription>
      </Alert>
    );
  }
  if (status === "needs_clarification") {
    return (
      <Alert>
        <InfoIcon />
        <AlertDescription className="flex flex-wrap items-center gap-3 [&_a]:no-underline">
          {t("runNeedsAnswers")}
          <Button asChild size="sm" variant="outline">
            <Link href={`/plan/new/clarify?job=${job}`}>{t("answer")}</Link>
          </Button>
        </AlertDescription>
      </Alert>
    );
  }
  return null;
}

function PageHead({
  label,
  slug,
  counts,
  totalMinutes,
  identity,
  generatedAt,
  chip,
  actions,
}: {
  label: string;
  slug: string;
  counts: { objectives: number; krs: number; tasks: number };
  totalMinutes: number;
  identity: ReturnType<typeof aiIdentity>;
  generatedAt: string | null;
  chip: ReactNode;
  actions: ReactNode;
}) {
  const t = useTranslations("plan.result");
  const fmt = usePlanFormat();
  const pathname = usePathname();
  const tabs = [
    { href: `/q/${slug}/tasks`, label: t("tabs.tasks"), icon: ListTreeIcon },
    { href: `/q/${slug}/calendar`, label: t("tabs.calendar"), icon: CalendarDaysIcon },
    { href: `/q/${slug}/workload`, label: t("tabs.workload"), icon: ChartColumnIcon },
  ];
  return (
    <header className="flex flex-col gap-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 flex-col gap-1.5">
          <h1 className="font-heading text-2xl font-semibold tracking-tight">{t("title", { quarter: label })}</h1>
          <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground">
            <span>{t("provenance", { ...counts, hours: fmt.hours(totalMinutes) })}</span>
            <AiBadge identity={identity} />
            {generatedAt && <span>{t("generatedAt", { time: fmt.time(generatedAt) })}</span>}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {chip}
          <Button asChild size="sm" variant="outline">
            <Link href={`/plan/new/okr?q=${slug}`}>
              <PencilIcon data-icon="inline-start" />
              {t("editOkr")}
            </Link>
          </Button>
          {actions}
        </div>
      </div>
      <nav aria-label={t("tabs.label")} className="inline-flex w-fit rounded-lg bg-muted/50 p-1">
        {tabs.map(({ href, label: tabLabel, icon: Icon }) => {
          const active = pathname === href;
          return (
            <GuardedLink
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring",
                active ? "bg-background font-medium shadow-sm" : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Icon className="size-4" aria-hidden />
              {tabLabel}
            </GuardedLink>
          );
        })}
      </nav>
    </header>
  );
}
