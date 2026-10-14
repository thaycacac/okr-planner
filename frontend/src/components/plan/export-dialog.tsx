"use client";

import { DownloadIcon, ShieldCheckIcon } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { api } from "@/lib/api/client";
import type { ExportSheet, QuarterSummary } from "@/lib/api/types";
import {
  browserUtcOffset,
  defaultDondonTag,
  dondonFileName,
  type ExportMode,
  exportFileName,
  fileNameFromDisposition,
  formatUtcOffset,
  isDondonEmail,
  utcOffsetOptions,
} from "@/lib/plan/export";
import { quarterLabel, toRef } from "@/lib/plan/quarter";

const SHEETS: readonly ExportSheet[] = ["tasks", "days", "weeks"];
const EMAIL_KEY = "okr.dondonEmail";

function savedEmail(): string {
  try {
    return window.localStorage.getItem(EMAIL_KEY) ?? "";
  } catch {
    return "";
  }
}

function rememberEmail(email: string) {
  try {
    window.localStorage.setItem(EMAIL_KEY, email);
  } catch {
    // Private mode or blocked storage: the field simply starts empty next time.
  }
}

export function ExportButton({ quarter }: { quarter: QuarterSummary }) {
  const t = useTranslations("plan.export");
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button size="sm" variant="outline" onClick={() => setOpen(true)}>
        <DownloadIcon data-icon="inline-start" />
        {t("button")}
      </Button>
      <ExportDialog open={open} onOpenChange={setOpen} quarters={[quarter]} initialQuarterId={quarter.id} />
    </>
  );
}

export function ExportDialog({
  open,
  onOpenChange,
  quarters,
  initialQuarterId,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  quarters: readonly QuarterSummary[];
  initialQuarterId: number | null;
}) {
  const t = useTranslations("plan.export");
  const locale = useLocale();
  const [quarterId, setQuarterId] = useState<number | null>(initialQuarterId);
  const [format, setFormat] = useState<ExportMode>("xlsx");
  const [email, setEmail] = useState(savedEmail);
  const [tagEdit, setTagEdit] = useState<string | null>(null);
  const [workStart, setWorkStart] = useState("09:00");
  const [offset, setOffset] = useState(() => browserUtcOffset());
  const [mapPriority, setMapPriority] = useState(true);
  const [keepStatus, setKeepStatus] = useState(true);
  const [sheet, setSheet] = useState<ExportSheet>("tasks");
  const [details, setDetails] = useState(false);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const selected = quarters.find((q) => q.id === (quarterId ?? initialQuarterId)) ?? quarters[0];
  const empty = !selected || selected.task_count === 0;
  const tag = tagEdit ?? (selected ? defaultDondonTag(toRef(selected), locale) : "");
  const sql = format === "dondon";
  const sqlInvalid = sql && (!isDondonEmail(email) || !tag.trim() || !/^([01]\d|2[0-3]):[0-5]\d$/.test(workStart));
  const fileName = !selected
    ? ""
    : sql
      ? dondonFileName(toRef(selected))
      : exportFileName(toRef(selected), format, format === "csv" ? sheet : null);

  async function download() {
    if (!selected) return;
    setBusy(true);
    setFailed(false);
    const request = sql
      ? api.POST("/quarters/{quarter_id}/export/dondon-sql", {
          params: { path: { quarter_id: selected.id } },
          body: {
            email: email.trim(),
            tag_name: tag.trim(),
            work_start: workStart,
            utc_offset_minutes: offset,
            map_priority: mapPriority,
            keep_status: keepStatus,
          },
          parseAs: "blob",
        })
      : api.GET("/quarters/{quarter_id}/export", {
          params: {
            path: { quarter_id: selected.id },
            query: { format, sheet: format === "csv" ? sheet : undefined, lang: locale === "en" ? "en" : "vi", details },
          },
          parseAs: "blob",
        });
    const { data, response } = await request.catch(() => ({ data: undefined, response: undefined }));
    setBusy(false);
    if (!data || !response?.ok) {
      setFailed(true);
      return;
    }
    const url = URL.createObjectURL(data);
    const link = document.createElement("a");
    link.href = url;
    link.download = fileNameFromDisposition(response.headers.get("content-disposition")) ?? fileName;
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    if (sql) rememberEmail(email.trim());
    onOpenChange(false);
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) setFailed(false);
        onOpenChange(next);
      }}
    >
      <DialogContent closeLabel={t("close")} className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription>{t("body")}</DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          {quarters.length > 1 && (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="export-quarter">{t("quarter")}</Label>
              <Select value={selected ? String(selected.id) : ""} onValueChange={(v) => setQuarterId(Number(v))}>
                <SelectTrigger id="export-quarter" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {quarters.map((q) => (
                    <SelectItem key={q.id} value={String(q.id)}>
                      {quarterLabel(toRef(q))} · {t("taskCount", { count: q.task_count })}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <fieldset className="flex flex-col gap-2">
            <legend className="mb-1.5 text-sm font-medium">{t("format")}</legend>
            <RadioGroup value={format} onValueChange={(v) => setFormat(v as ExportMode)} className="gap-2">
              <Label className="flex items-start gap-2 font-normal">
                <RadioGroupItem value="xlsx" className="mt-0.5" />
                <span>
                  <span className="font-medium">{t("xlsx")}</span>
                  <span className="block text-xs text-muted-foreground">{t("xlsxHint")}</span>
                </span>
              </Label>
              <Label className="flex items-start gap-2 font-normal">
                <RadioGroupItem value="csv" className="mt-0.5" />
                <span>
                  <span className="font-medium">{t("csv")}</span>
                  <span className="block text-xs text-muted-foreground">{t("csvHint")}</span>
                </span>
              </Label>
              <Label className="flex items-start gap-2 font-normal">
                <RadioGroupItem value="dondon" className="mt-0.5" />
                <span>
                  <span className="font-medium">{t("dondon.title")}</span>
                  <span className="block text-xs text-muted-foreground">{t("dondon.hint")}</span>
                </span>
              </Label>
            </RadioGroup>
          </fieldset>

          {sql && (
            <div className="flex flex-col gap-3 rounded-lg border border-border p-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="dondon-email">{t("dondon.email")}</Label>
                <Input
                  id="dondon-email"
                  type="email"
                  autoComplete="email"
                  spellCheck={false}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  aria-invalid={email !== "" && !isDondonEmail(email) ? true : undefined}
                  aria-describedby="dondon-email-hint"
                />
                <p id="dondon-email-hint" className="text-xs text-muted-foreground">
                  {email !== "" && !isDondonEmail(email) ? t("dondon.emailInvalid") : t("dondon.emailHint")}
                </p>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="dondon-tag">{t("dondon.tag")}</Label>
                <Input id="dondon-tag" maxLength={100} value={tag} onChange={(e) => setTagEdit(e.target.value)} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="dondon-start">{t("dondon.workStart")}</Label>
                  <Input id="dondon-start" type="time" value={workStart} onChange={(e) => setWorkStart(e.target.value)} />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="dondon-zone">{t("dondon.timezone")}</Label>
                  <Select value={String(offset)} onValueChange={(v) => setOffset(Number(v))}>
                    <SelectTrigger id="dondon-zone" className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {utcOffsetOptions(offset).map((minutes) => (
                        <SelectItem key={minutes} value={String(minutes)}>
                          {formatUtcOffset(minutes)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Label className="flex items-start gap-2 font-normal">
                <Checkbox checked={mapPriority} onCheckedChange={(v) => setMapPriority(v === true)} className="mt-0.5" />
                {t("dondon.mapPriority")}
              </Label>
              <Label className="flex items-start gap-2 font-normal">
                <Checkbox checked={keepStatus} onCheckedChange={(v) => setKeepStatus(v === true)} className="mt-0.5" />
                {t("dondon.keepStatus")}
              </Label>
              <p className="text-xs text-muted-foreground">{t("dondon.howToRun")}</p>
            </div>
          )}

          {format === "csv" && (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="export-sheet">{t("sheet")}</Label>
              <Select value={sheet} onValueChange={(v) => setSheet(v as ExportSheet)}>
                <SelectTrigger id="export-sheet" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SHEETS.map((s) => (
                    <SelectItem key={s} value={s}>
                      {t(`sheets.${s}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {!sql && (
          <Label className="flex items-start gap-2 font-normal">
            <Checkbox checked={details} onCheckedChange={(v) => setDetails(v === true)} className="mt-0.5" />
            {t("details")}
          </Label>
          )}

          <p className="flex items-center gap-2 text-xs text-muted-foreground">
            <ShieldCheckIcon className="size-4 shrink-0" aria-hidden />
            {t("noSecrets")}
          </p>

          {empty && <p className="text-sm text-muted-foreground">{t("empty")}</p>}
          {failed && (
            <Alert variant="destructive" role="alert">
              <AlertDescription className="text-foreground">{t("failed")}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={busy}>
            {t("cancel")}
          </Button>
          <Button onClick={() => void download()} disabled={busy || empty || sqlInvalid}>
            {busy ? <Spinner data-icon="inline-start" /> : <DownloadIcon data-icon="inline-start" />}
            {failed ? t("retry") : t("download", { file: fileName })}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
