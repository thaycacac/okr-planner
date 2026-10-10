"use client";

import { BotIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { cn } from "cn";

import { Badge } from "@/components/ui/badge";
import type { LlmSettings, ObjectivePriority, PlanRunDetail } from "@/lib/api/types";
import { remoteInfo } from "@/lib/api/llm-remote";
import { objectiveColor } from "@/lib/plan/plan-view";
import type { QuarterStatus } from "@/lib/plan/quarter";

export function ObjectiveCode({ index, className }: { index: number; className?: string }) {
  return (
    <span
      className={cn(
        // Sans, not mono: in Geist Mono the letter O is nearly identical to the digit 0.
        "inline-flex h-5 min-w-7 shrink-0 items-center justify-center rounded-md px-1.5 font-sans text-xs font-semibold text-white tabular-nums",
        className,
      )}
      style={{ backgroundColor: objectiveColor(index) }}
    >
      O{index + 1}
    </span>
  );
}

export function PriorityBadge({ priority, className }: { priority: ObjectivePriority; className?: string }) {
  const t = useTranslations("plan.priority");
  return (
    <Badge variant={priority === "high" ? "secondary" : "outline"} className={cn("font-normal", className)}>
      {t(priority)}
    </Badge>
  );
}

export function QuarterStatusBadge({ status }: { status: QuarterStatus }) {
  const t = useTranslations("plan.quarter");
  if (status.kind === "upcoming") return <Badge variant="secondary">{t("status.upcoming", { days: status.daysUntil })}</Badge>;
  if (status.kind === "ongoing") return <Badge className="bg-warning-muted text-warning">{t("status.ongoing")}</Badge>;
  return <Badge variant="outline">{t("status.ended")}</Badge>;
}

export type AiIdentity = { provider: string; model: string | null };

/** Provider + model a finished run used, falling back to the saved settings while it runs. */
export function aiIdentity(run: PlanRunDetail | null, settings: LlmSettings | null): AiIdentity | null {
  if (run?.provider) {
    const model = run.models.decompose ?? run.models.clarify ?? Object.values(run.models)[0] ?? null;
    return { provider: run.provider, model };
  }
  if (!settings) return null;
  return {
    provider: settings.provider,
    model: settings.provider === "local" ? settings.local_model : remoteInfo(settings, settings.provider).model,
  };
}

export function AiBadge({ identity, className }: { identity: AiIdentity | null; className?: string }) {
  const t = useTranslations("plan.ai");
  if (!identity) return null;
  const known = ["openai", "gemini", "claude", "local"] as const;
  const provider = known.find((k) => k === identity.provider) ? t(identity.provider as (typeof known)[number]) : identity.provider;
  return (
    <Badge variant="outline" className={cn("gap-1 font-normal", className)}>
      <BotIcon aria-hidden />
      {t("badge", { provider, model: identity.model ?? "—" })}
    </Badge>
  );
}
