"use client";

import { CheckIcon } from "lucide-react";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { cn } from "cn";

import { Progress } from "@/components/ui/progress";

const STEPS = ["quarter", "okr", "clarify", "generate", "plan"] as const;
type Step = (typeof STEPS)[number];

export function stepForPath(pathname: string): Step {
  if (pathname.endsWith("/okr")) return "okr";
  if (pathname.endsWith("/clarify")) return "clarify";
  if (pathname.endsWith("/generate")) return "generate";
  return "quarter";
}

export function WizardStepper() {
  const t = useTranslations("plan.steps");
  const current = STEPS.indexOf(stepForPath(usePathname()));
  return (
    <nav aria-label={t("label")} className="border-b border-border bg-background">
      <ol className="mx-auto hidden max-w-4xl items-center gap-2 px-6 py-3 md:flex">
        {STEPS.map((step, i) => {
          const done = i < current;
          const active = i === current;
          return (
            <li key={step} className="flex flex-1 items-center gap-2 last:flex-none">
              <span
                aria-current={active ? "step" : undefined}
                className={cn(
                  "flex items-center gap-2 text-sm whitespace-nowrap",
                  active ? "font-semibold text-foreground" : "text-muted-foreground",
                )}
              >
                <span
                  className={cn(
                    "flex size-6 items-center justify-center rounded-full border text-xs font-semibold",
                    done && "border-success bg-success text-background",
                    active && "border-foreground bg-foreground text-background",
                  )}
                  aria-hidden
                >
                  {done ? <CheckIcon className="size-3.5" /> : i + 1}
                </span>
                {t(step)}
                {done && <span className="sr-only">{t("done")}</span>}
              </span>
              {i < STEPS.length - 1 && (
                <span aria-hidden className={cn("h-px flex-1", done ? "bg-success" : "bg-border")} />
              )}
            </li>
          );
        })}
      </ol>
      <div className="flex flex-col gap-2 px-4 py-2 md:hidden">
        <p className="text-sm font-medium">
          {t("mobile", { step: current + 1, total: STEPS.length, name: t(STEPS[current]) })}
        </p>
        <Progress value={((current + 1) / STEPS.length) * 100} aria-hidden className="h-1" />
      </div>
    </nav>
  );
}
