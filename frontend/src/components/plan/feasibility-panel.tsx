"use client";

import { CheckIcon, ChevronDownIcon, RefreshCwIcon, TriangleAlertIcon, XIcon } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { cn } from "cn";

import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Skeleton } from "@/components/ui/skeleton";
import type { FeasibilityStatus } from "@/lib/api/types";
import type { FeasibilitySummary } from "@/lib/plan/plan-view";

import { ObjectiveCode } from "./plan-bits";
import { RescheduleButton } from "./reschedule-flow";
import { usePlanFormat } from "./use-plan-format";

type Tone = { icon: typeof CheckIcon; text: string; iconColor: string; bg: string; bar: string };

// Red text on the red tint only reaches ~4:1, so red keeps its colour on the icon and uses foreground text.
const TONE: Record<FeasibilityStatus, Tone> = {
  green: { icon: CheckIcon, text: "text-success", iconColor: "text-success", bg: "bg-success-muted border-success/30", bar: "bg-success" },
  yellow: {
    icon: TriangleAlertIcon,
    text: "text-warning",
    iconColor: "text-warning",
    bg: "bg-warning-muted border-warning/30",
    bar: "bg-warning",
  },
  red: { icon: XIcon, text: "text-foreground", iconColor: "text-destructive", bg: "bg-destructive/10 border-destructive/30", bar: "bg-destructive" },
};

export function FeasibilityPanel({
  summary,
  slug,
  loading = false,
  className,
}: {
  summary: FeasibilitySummary | null;
  slug: string;
  loading?: boolean;
  className?: string;
}) {
  const t = useTranslations("plan.feasibility");
  const fmt = usePlanFormat();

  if (loading) {
    return (
      <section className={cn("flex flex-col gap-3 rounded-xl border border-border p-4", className)} aria-busy="true">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-16 w-full" />
      </section>
    );
  }
  if (!summary) {
    return (
      <section
        role="status"
        className={cn("rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground", className)}
      >
        {t("empty")}
      </section>
    );
  }

  if (summary.stale) return <StalePanel summary={summary} className={className} />;

  const tone = TONE[summary.status];
  const Icon = tone.icon;
  const supply = Math.max(summary.supplyMinutes, 1);
  const fill = Math.min(summary.demandMinutes / supply, 1) * 100;
  const marker = (summary.bufferedSupplyMinutes / supply) * 100;
  const spareMinutes = Math.max(0, summary.supplyMinutes - summary.demandMinutes);

  return (
    <section
      role="status"
      aria-label={t("label")}
      className={cn("flex flex-col gap-3 rounded-xl border p-4 text-sm", tone.bg, className)}
    >
      <h2 className={cn("flex items-center gap-2 font-heading text-base font-semibold", tone.text)}>
        <Icon className={cn("size-4", tone.iconColor)} aria-hidden />
        {t(`status.${summary.status}`)}
      </h2>
      <p>
        {summary.status === "green" &&
          t("summaryGreen", {
            date: summary.finishDate ? fmt.date(summary.finishDate) : "—",
            spare: fmt.hours(spareMinutes),
          })}
        {summary.status === "yellow" &&
          t("summaryYellow", {
            date: summary.finishDate ? fmt.date(summary.finishDate) : "—",
            used: fmt.hours(summary.bufferUsedMinutes),
            buffer: fmt.hours(summary.bufferMinutes),
          })}
        {summary.status === "red" &&
          t("summaryRed", { shortage: fmt.hours(summary.shortageMinutes), date: fmt.date(summary.windowEnd) })}
      </p>

      <dl className="grid grid-cols-3 gap-2">
        <Metric label={t("demand")} value={fmt.hours(summary.demandMinutes)} />
        <Metric label={t("supply")} value={fmt.hours(summary.supplyMinutes)} />
        {summary.status === "red" ? (
          <Metric label={t("shortage")} value={fmt.hours(summary.shortageMinutes)} className={tone.text} />
        ) : (
          <Metric label={t("used")} value={`${summary.usedPercent}%`} />
        )}
      </dl>

      <div className="flex flex-col gap-1">
        <div className="relative h-2 rounded-full bg-background/80" aria-hidden>
          <div className={cn("h-full rounded-full", tone.bar)} style={{ width: `${fill}%` }} />
          {summary.bufferMinutes > 0 && (
            <div className="absolute -top-1 h-4 w-0.5 bg-foreground/70" style={{ left: `${marker}%` }} />
          )}
        </div>
        {summary.bufferStart && (
          <span className="text-xs text-muted-foreground">
            {t("bufferFrom", { date: fmt.date(summary.bufferStart), hours: fmt.hours(summary.bufferMinutes) })}
          </span>
        )}
      </div>

      {summary.finishDate && summary.status !== "red" && (
        <p className="text-xs">{t("finish", { date: fmt.date(summary.finishDate) })}</p>
      )}

      {summary.status === "yellow" && (
        <div className="flex flex-col gap-1 text-xs">
          <p>
            {t("bufferUsage", {
              used: fmt.hours(summary.bufferUsedMinutes),
              buffer: fmt.hours(summary.bufferMinutes),
              count: summary.bufferTaskCount,
            })}
          </p>
          <Link href="/settings/calendar" className="font-medium underline underline-offset-4">
            {t("increaseCapacity")}
          </Link>
        </div>
      )}

      {summary.status === "red" && (
        <div className="flex flex-col gap-2 text-xs">
          <p className="font-medium">{t("lateKrs", { count: summary.lateTaskCount, hours: fmt.hours(summary.lateMinutes) })}</p>
          <ul className="flex flex-col gap-1">
            {summary.lateKrs.map((late) => (
              <li key={late.kr.kr.id}>
                <Link
                  href={`/q/${slug}/tasks?kr=${late.kr.kr.id}`}
                  className="flex flex-col gap-0.5 rounded-md px-1 py-0.5 hover:bg-background/60"
                >
                  <span className="flex items-center gap-1.5">
                    <ObjectiveCode index={late.objectiveIndex} />
                    <span className="font-mono">{late.kr.code}</span>
                    <span className="ml-auto whitespace-nowrap">
                      {t("lateKrItem", { count: late.count, hours: fmt.hours(late.minutes) })}
                    </span>
                  </span>
                  <span className="truncate text-muted-foreground" title={late.kr.kr.text}>
                    {late.kr.kr.text}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
          <Button asChild size="sm" className="w-fit">
            <Link href={`/q/${slug}/options`}>{t("seeOptions")}</Link>
          </Button>
          <div className="flex flex-col gap-1">
            <Link href="/settings/calendar" className="font-medium underline underline-offset-4">
              {t("increaseCapacity")}
            </Link>
            <Link href={`/plan/new/okr?q=${slug}`} className="font-medium underline underline-offset-4">
              {t("editOkr")}
            </Link>
            <Link href="/settings/leave" className="font-medium underline underline-offset-4">
              {t("leaveHolidays")}
            </Link>
          </div>
        </div>
      )}
    </section>
  );
}

/** A stale schedule says nothing reliable about the current tasks, so it gets no status colour. */
function StalePanel({ summary, className }: { summary: FeasibilitySummary; className?: string }) {
  const t = useTranslations("plan.feasibility");
  const fmt = usePlanFormat();
  const supply = Math.max(summary.supplyMinutes, 1);
  const fill = Math.min(summary.demandMinutes / supply, 1) * 100;
  return (
    <section
      role="status"
      aria-label={t("label")}
      className={cn("flex flex-col gap-3 rounded-xl border border-dashed border-border bg-muted/40 p-4 text-sm", className)}
    >
      <h2 className="flex items-center gap-2 font-heading text-base font-semibold">
        <RefreshCwIcon className="size-4 text-muted-foreground" aria-hidden />
        {t("staleTitle")}
      </h2>
      <p className="text-muted-foreground">{t("staleBody")}</p>
      <RescheduleButton />
      <div className="flex flex-col gap-2 text-muted-foreground">
        <span className="text-xs">{t("staleLast", { status: t(`chip.${summary.status}`) })}</span>
        <dl className="grid grid-cols-3 gap-2">
          <Metric label={t("demand")} value={fmt.hours(summary.demandMinutes)} muted />
          <Metric label={t("supply")} value={fmt.hours(summary.supplyMinutes)} muted />
          {summary.status === "red" ? (
            <Metric label={t("shortage")} value={fmt.hours(summary.shortageMinutes)} muted />
          ) : (
            <Metric label={t("used")} value={`${summary.usedPercent}%`} muted />
          )}
        </dl>
        <div className="h-2 rounded-full bg-background/80" aria-hidden>
          <div className="h-full rounded-full bg-muted-foreground/40" style={{ width: `${fill}%` }} />
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value, className, muted = false }: { label: string; value: string; className?: string; muted?: boolean }) {
  return (
    <div className="flex flex-col rounded-lg bg-background/70 px-2 py-1.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className={cn("font-heading text-base font-semibold tabular-nums", muted && "text-muted-foreground", className)}>{value}</dd>
    </div>
  );
}

/** Read-only status pill, e.g. on quarter cards. */
export function FeasibilityBadge({ status, className }: { status: FeasibilityStatus; className?: string }) {
  const t = useTranslations("plan.feasibility");
  const tone = TONE[status];
  const Icon = tone.icon;
  return (
    <span
      className={cn(
        "inline-flex h-6 w-fit items-center gap-1 rounded-full border px-2 text-xs font-medium",
        tone.bg,
        tone.text,
        className,
      )}
    >
      <Icon aria-hidden className={cn("size-3.5", tone.iconColor)} />
      {t(`chip.${status}`)}
    </span>
  );
}

/** Topbar pill that opens the same panel when there is no room for the rail. */
export function FeasibilityChip({
  summary,
  slug,
  className,
}: {
  summary: FeasibilitySummary | null;
  slug: string;
  className?: string;
}) {
  const t = useTranslations("plan.feasibility");
  if (!summary) return null;
  const tone = TONE[summary.status];
  const Icon = tone.icon;
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className={cn("gap-1.5", tone.bg, tone.text, className)}>
          <Icon aria-hidden className={tone.iconColor} />
          {t(`chip.${summary.status}`)}
          <ChevronDownIcon aria-hidden />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-[min(22rem,calc(100vw-2rem))] p-0">
        <FeasibilityPanel summary={summary} slug={slug} className="border-0" />
      </PopoverContent>
    </Popover>
  );
}
