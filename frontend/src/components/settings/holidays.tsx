"use client";

import { EllipsisIcon, ExternalLinkIcon, PencilIcon, PlusIcon, RotateCcwIcon, Trash2Icon } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useCallback, useState } from "react";
import { toast } from "sonner";
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
} from "@/components/ui/alert-dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { usePlanFormat } from "@/components/plan/use-plan-format";
import { useLoad } from "@/hooks/use-load";
import { api } from "@/lib/api/client";
import { errorDetail, type HolidayKind, type HolidayOut, type HolidayStatus } from "@/lib/api/types";
import { localToday } from "@/lib/plan/dates";
import { quarterLabel, quarterOf, sameQuarter, yearOptions } from "@/lib/plan/quarter";

import { LoadError } from "./load-error";
import { useCalendarImpact } from "./use-calendar-impact";

const KINDS: readonly HolidayKind[] = ["public_holiday", "compensatory", "swapped_day_off", "makeup_day", "personal_day_off"];
const STATUSES: readonly HolidayStatus[] = ["official", "provisional"];

type Draft = { id: number | null; date: string; kind: HolidayKind; nameVi: string; nameEn: string; status: HolidayStatus };

const emptyDraft = (year: number): Draft => ({
  id: null,
  date: `${year}-01-01`,
  kind: "personal_day_off",
  nameVi: "",
  nameEn: "",
  status: "official",
});

export function HolidaySettings() {
  const t = useTranslations("settings.holidays");
  const fmt = usePlanFormat();
  const locale = useLocale();
  const today = localToday();
  const [year, setYear] = useState(Number(today.slice(0, 4)));
  const fetcher = useCallback(async () => (await api.GET("/calendar/holidays", { params: { query: { year } } })).data, [year]);
  const [state, retry, refresh] = useLoad(fetcher);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);
  const currentQuarter = quarterOf(today);
  const hasProvisional = state.status === "ready" && state.data.some((h) => h.status === "provisional");
  const notifyImpact = useCalendarImpact("holiday");

  async function remove(holiday: HolidayOut) {
    const { response } = await api.DELETE("/calendar/holidays/{holiday_id}", { params: { path: { holiday_id: holiday.id } } });
    if (!response.ok) {
      toast.error(t("deleteFailed"));
      return;
    }
    await refresh();
    void notifyImpact([holiday.date]);
    toast(t("deleted", { date: fmt.date(holiday.date) }), {
      duration: 8000,
      action: {
        label: t("undo"),
        onClick: () => {
          void api
            .POST("/calendar/holidays", {
              body: {
                date: holiday.date,
                kind: holiday.kind,
                name_vi: holiday.name_vi,
                name_en: holiday.name_en || null,
                status: holiday.status,
              },
            })
            .then(() => refresh());
        },
      },
    });
  }

  async function reset() {
    const { data, error } = await api.POST("/calendar/holidays/reset", { params: { query: { year } } });
    setConfirmReset(false);
    if (!data) {
      toast.error(errorDetail(error)?.code === "holiday_data_missing" ? t("resetMissing", { year }) : t("resetFailed"));
      return;
    }
    const before = state.status === "ready" ? state.data.map((h) => h.date) : [];
    await refresh();
    toast.success(t("resetDone", { year }));
    void notifyImpact([...before, ...data.map((h) => h.date)]);
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
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
        <span className="flex-1" />
        <Button variant="outline" size="sm" onClick={() => setConfirmReset(true)}>
          <RotateCcwIcon data-icon="inline-start" />
          {t("reset")}
        </Button>
        <Button size="sm" onClick={() => setDraft(emptyDraft(year))}>
          <PlusIcon data-icon="inline-start" />
          {t("add")}
        </Button>
      </div>

      <p className="text-sm text-muted-foreground">{t("intro")}</p>
      {hasProvisional && (
        <Alert>
          <AlertDescription>{t("provisionalNote")}</AlertDescription>
        </Alert>
      )}

      {state.status === "loading" && <Skeleton className="h-48 w-full" />}
      {state.status === "error" && <LoadError onRetry={retry} />}
      {state.status === "ready" &&
        (state.data.length === 0 ? (
          <p className="rounded-xl border border-dashed border-border p-6 text-sm text-muted-foreground">{t("empty", { year })}</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead scope="col">{t("colDate")}</TableHead>
                  <TableHead scope="col" className="max-md:hidden">
                    {t("colName")}
                  </TableHead>
                  <TableHead scope="col" className="max-md:hidden">
                    {t("colKind")}
                  </TableHead>
                  <TableHead scope="col" className="max-md:hidden">
                    {t("colStatus")}
                  </TableHead>
                  <TableHead scope="col" className="max-md:hidden">
                    {t("colSource")}
                  </TableHead>
                  <TableHead scope="col" className="w-12">
                    <span className="sr-only">{t("colActions")}</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {state.data.map((h) => {
                  const inCurrent = sameQuarter(quarterOf(h.date), currentQuarter);
                  const name = locale === "en" ? h.name_en || h.name_vi : h.name_vi;
                  const status =
                    h.status === "provisional" ? (
                      <Badge variant="outline" className="border-warning/40 bg-warning-muted font-normal text-warning">
                        ! {t("statuses.provisional")}
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground">{t("statuses.official")}</span>
                    );
                  return (
                    <TableRow key={h.id} className={cn(inCurrent && "bg-accent/40")}>
                      <TableCell className="whitespace-nowrap max-md:whitespace-normal">
                        {fmt.weekday(h.date)} {fmt.date(h.date)}
                        {inCurrent && (
                          <Badge variant="outline" className="ml-2 font-normal">
                            {quarterLabel(currentQuarter)}
                          </Badge>
                        )}
                        <span className="mt-1 flex flex-col gap-0.5 md:hidden">
                          <span className="font-medium">{name}</span>
                          <span className="flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground">
                            {t(`kinds.${h.kind}`)} · {status}
                            {h.custom && <Badge variant="secondary" className="font-normal">{t("custom")}</Badge>}
                          </span>
                        </span>
                      </TableCell>
                      <TableCell className="max-w-72 whitespace-normal max-md:hidden">
                        {name}
                        {h.custom && (
                          <Badge variant="secondary" className="ml-2 font-normal">
                            {t("custom")}
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="whitespace-nowrap max-md:hidden">{t(`kinds.${h.kind}`)}</TableCell>
                      <TableCell className="max-md:hidden">{status}</TableCell>
                      <TableCell className="max-md:hidden">
                        {h.source && /^https?:\/\//.test(h.source) ? (
                          <a
                            href={h.source}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 underline underline-offset-4"
                          >
                            {t("sourceLink")}
                            <ExternalLinkIcon className="size-3" aria-hidden />
                          </a>
                        ) : (
                          <span className="text-muted-foreground">{h.source || "—"}</span>
                        )}
                      </TableCell>
                      <TableCell className="py-1">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon-sm" className="max-md:size-10" aria-label={t("menu", { date: fmt.date(h.date) })}>
                              <EllipsisIcon />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onSelect={() =>
                                setDraft({ id: h.id, date: h.date, kind: h.kind, nameVi: h.name_vi, nameEn: h.name_en, status: h.status })
                              }
                            >
                              <PencilIcon />
                              {t("edit")}
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem variant="destructive" onSelect={() => void remove(h)}>
                              <Trash2Icon />
                              {t("delete")}
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        ))}
      <p className="text-xs text-muted-foreground">{t("impactNote")}</p>

      <HolidayDialog
        draft={draft}
        onClose={() => setDraft(null)}
        onSaved={async (saved) => {
          const previousDate = draft?.date;
          setDraft(null);
          if (Number(saved.date.slice(0, 4)) !== year) setYear(Number(saved.date.slice(0, 4)));
          else await refresh();
          toast.success(t("saved", { date: fmt.date(saved.date) }));
          void notifyImpact(previousDate && previousDate !== saved.date ? [previousDate, saved.date] : [saved.date]);
        }}
      />

      <AlertDialog open={confirmReset} onOpenChange={setConfirmReset}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t("resetTitle", { year })}</AlertDialogTitle>
            <AlertDialogDescription>{t("resetBody")}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t("cancel")}</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={() => void reset()}>
              {t("resetConfirm")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function HolidayDialog({
  draft,
  onClose,
  onSaved,
}: {
  draft: Draft | null;
  onClose: () => void;
  onSaved: (holiday: HolidayOut) => Promise<void>;
}) {
  const t = useTranslations("settings.holidays");
  return (
    <Dialog open={draft !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent closeLabel={t("close")} className="sm:max-w-md">
        {draft && <HolidayForm key={draft.id ?? "new"} initial={draft} onClose={onClose} onSaved={onSaved} />}
      </DialogContent>
    </Dialog>
  );
}

function HolidayForm({
  initial,
  onClose,
  onSaved,
}: {
  initial: Draft;
  onClose: () => void;
  onSaved: (holiday: HolidayOut) => Promise<void>;
}) {
  const t = useTranslations("settings.holidays");
  const [draft, setDraft] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState<{ date?: string; name?: string; general?: string }>({});
  const set = <K extends keyof Draft>(key: K, value: Draft[K]) => setDraft((d) => ({ ...d, [key]: value }));

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const found: typeof errors = {};
    if (!/^\d{4}-\d{2}-\d{2}$/.test(draft.date)) found.date = t("dateRequired");
    if (!draft.nameVi.trim()) found.name = t("nameRequired");
    setErrors(found);
    if (Object.keys(found).length > 0) return;
    setBusy(true);
    const body = {
      date: draft.date,
      kind: draft.kind,
      name_vi: draft.nameVi.trim(),
      name_en: draft.nameEn.trim() || null,
      status: draft.status,
    };
    const result =
      draft.id === null
        ? await api.POST("/calendar/holidays", { body })
        : await api.PATCH("/calendar/holidays/{holiday_id}", { params: { path: { holiday_id: draft.id } }, body });
    setBusy(false);
    if (!result.data) {
      const code = errorDetail(result.error)?.code;
      setErrors(code === "holiday_exists" ? { date: t("dateTaken") } : { general: t("saveFailed") });
      return;
    }
    await onSaved(result.data);
  }

  return (
    <form onSubmit={(e) => void submit(e)} className="flex flex-col gap-4" noValidate>
      <DialogHeader>
        <DialogTitle>{draft.id === null ? t("addTitle") : t("editTitle")}</DialogTitle>
        <DialogDescription>{t("formBody")}</DialogDescription>
      </DialogHeader>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="holiday-date">{t("colDate")}</Label>
        <Input
          id="holiday-date"
          type="date"
          value={draft.date}
          onChange={(e) => set("date", e.target.value)}
          aria-invalid={errors.date ? true : undefined}
          aria-describedby={errors.date ? "holiday-date-error" : undefined}
          className="w-44"
        />
        {errors.date && (
          <span id="holiday-date-error" className="text-xs text-destructive">
            {errors.date}
          </span>
        )}
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="holiday-kind">{t("colKind")}</Label>
          <Select value={draft.kind} onValueChange={(v) => set("kind", v as HolidayKind)}>
            <SelectTrigger id="holiday-kind" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {KINDS.map((k) => (
                <SelectItem key={k} value={k}>
                  {t(`kinds.${k}`)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="holiday-status">{t("colStatus")}</Label>
          <Select value={draft.status} onValueChange={(v) => set("status", v as HolidayStatus)}>
            <SelectTrigger id="holiday-status" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {STATUSES.map((s) => (
                <SelectItem key={s} value={s}>
                  {t(`statuses.${s}`)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="holiday-name-vi">{t("nameVi")}</Label>
        <Input
          id="holiday-name-vi"
          value={draft.nameVi}
          maxLength={200}
          onChange={(e) => set("nameVi", e.target.value)}
          aria-invalid={errors.name ? true : undefined}
        />
        {errors.name && <span className="text-xs text-destructive">{errors.name}</span>}
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="holiday-name-en">{t("nameEn")}</Label>
        <Input id="holiday-name-en" value={draft.nameEn} maxLength={200} onChange={(e) => set("nameEn", e.target.value)} />
      </div>
      {errors.general && (
        <Alert variant="destructive" role="alert">
          <AlertDescription className="text-foreground">{errors.general}</AlertDescription>
        </Alert>
      )}
      <DialogFooter>
        <Button type="button" variant="outline" onClick={onClose} disabled={busy}>
          {t("cancel")}
        </Button>
        <Button type="submit" disabled={busy}>
          {busy && <Spinner data-icon="inline-start" />}
          {t("save")}
        </Button>
      </DialogFooter>
    </form>
  );
}
