"use client";

import { PlusIcon, Trash2Icon } from "lucide-react";
import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";
import { toast } from "sonner";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { usePlanFormat } from "@/components/plan/use-plan-format";
import { useApiErrorMessage } from "@/hooks/use-api-error-message";
import { useLoad } from "@/hooks/use-load";
import { api } from "@/lib/api/client";
import { knownApiError } from "@/lib/api/error-message";
import type { LeaveDayOut } from "@/lib/api/types";
import { localToday } from "@/lib/plan/dates";
import { quarterLabel, quarterOf, yearOptions } from "@/lib/plan/quarter";

import { LoadError } from "./load-error";
import { useCalendarImpact } from "./use-calendar-impact";

const UNDO_MS = 8000;

export function LeaveDaysSettings() {
  const t = useTranslations("settings.leave");
  const fmt = usePlanFormat();
  const today = localToday();
  const [year, setYear] = useState(Number(today.slice(0, 4)));
  const fetcher = useCallback(async () => (await api.GET("/calendar/leave-days", { params: { query: { year } } })).data, [year]);
  const [state, retry, refresh] = useLoad(fetcher);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const notifyImpact = useCalendarImpact("leave");
  const apiErrorMessage = useApiErrorMessage();

  async function add(event: React.FormEvent) {
    event.preventDefault();
    if (!start) {
      setError(t("startRequired"));
      return;
    }
    if (end && end < start) {
      setError(t("endBeforeStart"));
      return;
    }
    setBusy(true);
    setError(null);
    const { data, error: failure } = await api
      .POST("/calendar/leave-days", { body: { start_date: start, end_date: end || null, note: note.trim() || null } })
      .catch(() => ({ data: undefined, error: undefined }));
    setBusy(false);
    if (!data) {
      setError(knownApiError(failure) ? t("saveFailedDetail", { detail: apiErrorMessage(failure) }) : t("saveFailed"));
      return;
    }
    setStart("");
    setEnd("");
    setNote("");
    if (Number(start.slice(0, 4)) !== year) setYear(Number(start.slice(0, 4)));
    else await refresh();
    toast.success(data.length > 0 ? t("added", { count: data.length }) : t("addedNone"));
    void notifyImpact(data.map((d) => d.date));
  }

  async function remove(day: LeaveDayOut) {
    const { response } = await api.DELETE("/calendar/leave-days/{leave_day_id}", {
      params: { path: { leave_day_id: day.id } },
    });
    if (!response.ok) {
      toast.error(t("deleteFailed"));
      return;
    }
    await refresh();
    void notifyImpact([day.date]);
    toast(t("deleted", { date: fmt.date(day.date) }), {
      duration: UNDO_MS,
      action: {
        label: t("undo"),
        onClick: () => {
          void api.POST("/calendar/leave-days", { body: { start_date: day.date, note: day.note } }).then(() => refresh());
        },
      },
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("formTitle")}</CardTitle>
          <CardDescription>{t("formBody")}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={(e) => void add(e)} className="flex flex-col gap-4" noValidate>
            <div className="grid gap-4 sm:grid-cols-[auto_auto_1fr]">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="leave-start">{t("start")}</Label>
                <Input id="leave-start" type="date" value={start} onChange={(e) => setStart(e.target.value)} className="sm:w-44" />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="leave-end">{t("end")}</Label>
                <Input
                  id="leave-end"
                  type="date"
                  value={end}
                  min={start || undefined}
                  onChange={(e) => setEnd(e.target.value)}
                  className="sm:w-44"
                  aria-describedby="leave-end-hint"
                />
                <span id="leave-end-hint" className="text-xs text-muted-foreground">
                  {t("endHint")}
                </span>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="leave-note">{t("note")}</Label>
                <Input id="leave-note" value={note} maxLength={200} onChange={(e) => setNote(e.target.value)} placeholder={t("notePlaceholder")} />
              </div>
            </div>
            {error && (
              <Alert variant="destructive" role="alert">
                <AlertDescription className="text-foreground">{error}</AlertDescription>
              </Alert>
            )}
            <p className="text-xs text-muted-foreground">{t("impactNote")}</p>
            <Button type="submit" className="w-fit" disabled={busy}>
              {busy ? <Spinner data-icon="inline-start" /> : <PlusIcon data-icon="inline-start" />}
              {t("add")}
            </Button>
          </form>
        </CardContent>
      </Card>

      <section className="flex flex-col gap-3" aria-labelledby="leave-list">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="leave-list" className="font-heading text-lg font-semibold">
            {t("listTitle")}
          </h2>
          <ToggleGroup
            type="single"
            variant="outline"
            size="sm"
            value={String(year)}
            onValueChange={(v) => v && setYear(Number(v))}
            aria-label={t("year")}
          >
            {yearOptions(today).map((y) => (
              <ToggleGroupItem key={y} value={String(y)}>
                {y}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </div>
        {state.status === "loading" && <Skeleton className="h-32 w-full" />}
        {state.status === "error" && <LoadError onRetry={retry} />}
        {state.status === "ready" &&
          (state.data.length === 0 ? (
            <p className="rounded-xl border border-dashed border-border p-6 text-sm text-muted-foreground">{t("empty", { year })}</p>
          ) : (
            <div className="overflow-hidden rounded-xl border border-border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead scope="col">{t("colDate")}</TableHead>
                    <TableHead scope="col" className="max-md:hidden">{t("colQuarter")}</TableHead>
                    <TableHead scope="col">{t("colNote")}</TableHead>
                    <TableHead scope="col" className="w-12">
                      <span className="sr-only">{t("colActions")}</span>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {state.data.map((day) => (
                    <TableRow key={day.id}>
                      <TableCell className="whitespace-nowrap">
                        {fmt.weekday(day.date)} {fmt.date(day.date)}
                      </TableCell>
                      <TableCell className="max-md:hidden">{quarterLabel(quarterOf(day.date))}</TableCell>
                      <TableCell className="max-w-64 truncate text-muted-foreground max-md:max-w-36">{day.note || "—"}</TableCell>
                      <TableCell className="py-1">
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          className="max-md:size-10"
                          onClick={() => void remove(day)}
                          aria-label={t("delete", { date: fmt.date(day.date) })}
                        >
                          <Trash2Icon />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ))}
      </section>
    </div>
  );
}
