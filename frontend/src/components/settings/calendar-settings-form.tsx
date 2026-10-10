"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { CheckCircle2Icon } from "lucide-react";

import { useUnsavedChanges } from "@/components/app-shell/unsaved-changes";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Switch } from "@/components/ui/switch";
import { useLoad } from "@/hooks/use-load";
import { api } from "@/lib/api/client";
import type { Weekday } from "@/lib/api/types";

import {
  type CalendarDraft,
  countChanges,
  fromDraft,
  hasWorkingDay,
  isDayChanged,
  toDraft,
  WEEKDAYS,
  weeklyHours,
} from "./calendar-model";
import { HoursStepper } from "./hours-stepper";
import { LoadError } from "./load-error";

type Status = "idle" | "saving" | "saved" | "error";

async function fetchCalendarSettings() {
  return (await api.GET("/settings/calendar")).data;
}

export function CalendarSettingsForm() {
  const [state, retry] = useLoad(fetchCalendarSettings);
  if (state.status === "error") return <LoadError onRetry={retry} />;
  if (state.status === "loading") return <CalendarSkeleton />;
  return <CalendarForm initial={toDraft(state.data)} />;
}

function CalendarForm({ initial }: { initial: CalendarDraft }) {
  const t = useTranslations("settings");
  const tDay = useTranslations("weekdays");
  const tc = useTranslations("common");
  const [saved, setSaved] = useState(initial);
  const [draft, setDraft] = useState(initial);
  const [status, setStatus] = useState<Status>("idle");

  const changes = countChanges(saved, draft);
  const valid = hasWorkingDay(draft);
  useUnsavedChanges(changes);

  function update(fn: (d: CalendarDraft) => CalendarDraft) {
    setDraft(fn);
    setStatus("idle");
  }

  function setDay(day: Weekday, patch: Partial<CalendarDraft["days"][Weekday]>) {
    update((d) => ({ ...d, days: { ...d.days, [day]: { ...d.days[day], ...patch } } }));
  }

  async function save() {
    if (!valid) return;
    setStatus("saving");
    try {
      const { data } = await api.PUT("/settings/calendar", { body: fromDraft(draft) });
      if (!data) throw new Error("save failed");
      const next = toDraft(data);
      setSaved(next);
      setDraft(next);
      setStatus("saved");
    } catch {
      setStatus("error");
    }
  }

  return (
    <form
      className="flex flex-col gap-6"
      onSubmit={(e) => {
        e.preventDefault();
        void save();
      }}
    >
      <p className="text-sm text-muted-foreground">{t("calendar.description")}</p>

      <fieldset className="flex max-w-xl flex-col gap-2">
        <legend className="mb-2 text-sm font-semibold">{t("calendar.hoursPerDay")}</legend>
        <div className="overflow-hidden rounded-xl border border-border">
          <div
            aria-hidden
            className="grid grid-cols-[1fr_4.5rem_10rem] items-center gap-2 border-b border-border bg-muted/60 px-3 py-2 text-xs font-medium tracking-wide text-muted-foreground uppercase"
          >
            <span>{t("calendar.colDay")}</span>
            <span>{t("calendar.colWorking")}</span>
            <span>{t("calendar.colHours")}</span>
          </div>
          <ul>
            {WEEKDAYS.map((day) => {
              const { enabled, hours } = draft.days[day];
              const dayName = tDay(day);
              const changed = isDayChanged(saved, draft, day);
              return (
                <li
                  key={day}
                  className={
                    "grid min-h-12 grid-cols-[1fr_4.5rem_10rem] items-center gap-2 border-b border-border px-3 py-1.5 last:border-b-0" +
                    (changed ? " bg-accent" : "")
                  }
                >
                  <span
                    className={
                      "flex min-w-0 items-center gap-2 text-sm" +
                      (enabled ? "" : " text-muted-foreground")
                    }
                  >
                    <span className="whitespace-nowrap">{dayName}</span>
                    {changed && (
                      <>
                        <Badge variant="secondary" className="max-sm:hidden">
                          {t("calendar.changed")}
                        </Badge>
                        <span
                          aria-hidden
                          className="size-2 shrink-0 rounded-full bg-primary sm:hidden"
                        />
                        <span className="sr-only sm:hidden">{t("calendar.changed")}</span>
                      </>
                    )}
                  </span>
                  <Switch
                    checked={enabled}
                    onCheckedChange={(checked) => setDay(day, { enabled: checked })}
                    aria-label={t("calendar.workingOn", { day: dayName })}
                  />
                  {enabled ? (
                    <HoursStepper
                      value={hours}
                      onChange={(value) => setDay(day, { hours: value })}
                      labels={{
                        input: t("calendar.hoursFor", { day: dayName }),
                        decrease: t("calendar.decrease", { day: dayName }),
                        increase: t("calendar.increase", { day: dayName }),
                      }}
                    />
                  ) : (
                    <span className="text-sm text-muted-foreground">{t("calendar.off")}</span>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
        <p className="text-sm text-muted-foreground">
          {t("calendar.hint", { total: weeklyHours(draft) })}
        </p>
        {!valid && (
          <p role="alert" className="text-sm text-destructive">
            {t("calendar.noWorkingDay")}
          </p>
        )}
      </fieldset>

      <div className="flex max-w-xl flex-col gap-3">
        <Card size="sm">
          <CardContent className="flex items-center justify-between gap-4">
            <div className="flex flex-col gap-0.5">
              <label htmlFor="work-holidays" className="text-sm font-medium">
                {t("calendar.holidays")}
              </label>
              <p id="work-holidays-hint" className="text-sm text-muted-foreground">
                {t("calendar.holidaysHint")}
              </p>
            </div>
            <Switch
              id="work-holidays"
              aria-describedby="work-holidays-hint"
              checked={draft.workHolidays}
              onCheckedChange={(checked) => update((d) => ({ ...d, workHolidays: checked }))}
            />
          </CardContent>
        </Card>
        <Card size="sm">
          <CardContent className="flex items-center justify-between gap-4">
            <div className="flex flex-col gap-0.5">
              <span className="text-sm font-medium">{t("calendar.buffer")}</span>
              <p className="text-sm text-muted-foreground">{t("calendar.bufferHint")}</p>
            </div>
            <Badge variant="outline">10%</Badge>
          </CardContent>
        </Card>
      </div>

      {status === "error" && (
        <Alert variant="destructive" className="max-w-xl">
          <AlertDescription className="flex flex-wrap items-center gap-3">
            <span>{t("saveError")}</span>
            <Button type="submit" size="sm" variant="outline">
              {tc("retry")}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <div role="status" className="min-h-5 text-sm text-success">
        {status === "saved" && (
          <span className="inline-flex items-center gap-1.5">
            <CheckCircle2Icon className="size-4" aria-hidden />
            {t("saved")}
          </span>
        )}
      </div>

      {changes > 0 && (
        <div className="sticky bottom-16 z-30 -mx-4 flex flex-col gap-2 border-t border-border bg-background/95 px-4 py-3 backdrop-blur sm:flex-row sm:items-center md:bottom-0 md:-mx-8 md:px-8">
          <span className="text-sm text-muted-foreground sm:flex-1">
            {t("calendar.unsaved", { count: changes })}
          </span>
          <div className="grid grid-cols-2 gap-2 sm:flex">
            <Button
              type="button"
              variant="outline"
              className="max-sm:h-11"
              onClick={() => {
                setDraft(saved);
                setStatus("idle");
              }}
              disabled={status === "saving"}
            >
              {t("calendar.discard")}
            </Button>
            <Button
              type="submit"
              className="max-sm:h-11"
              disabled={!valid || status === "saving"}
            >
              {status === "saving" && <Spinner aria-hidden role="presentation" />}
              {status === "saving" ? t("calendar.saving") : t("calendar.save")}
            </Button>
          </div>
        </div>
      )}
    </form>
  );
}

function CalendarSkeleton() {
  return (
    <div className="flex max-w-xl flex-col gap-3" aria-busy="true">
      <Skeleton className="h-4 w-72" />
      <Skeleton className="h-80 w-full" />
      <Skeleton className="h-16 w-full" />
    </div>
  );
}
