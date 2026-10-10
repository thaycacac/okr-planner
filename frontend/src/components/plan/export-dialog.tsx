"use client";

import { DownloadIcon, ShieldCheckIcon } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { api } from "@/lib/api/client";
import type { ExportFormat, ExportSheet, QuarterSummary } from "@/lib/api/types";
import { exportFileName, fileNameFromDisposition } from "@/lib/plan/export";
import { quarterLabel, toRef } from "@/lib/plan/quarter";

const SHEETS: readonly ExportSheet[] = ["tasks", "days", "weeks"];

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
  const [format, setFormat] = useState<ExportFormat>("xlsx");
  const [sheet, setSheet] = useState<ExportSheet>("tasks");
  const [details, setDetails] = useState(false);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const selected = quarters.find((q) => q.id === (quarterId ?? initialQuarterId)) ?? quarters[0];
  const empty = !selected || selected.task_count === 0;
  const fileName = selected ? exportFileName(toRef(selected), format, format === "csv" ? sheet : null) : "";

  async function download() {
    if (!selected) return;
    setBusy(true);
    setFailed(false);
    const { data, response } = await api
      .GET("/quarters/{quarter_id}/export", {
        params: {
          path: { quarter_id: selected.id },
          query: { format, sheet: format === "csv" ? sheet : undefined, lang: locale === "en" ? "en" : "vi", details },
        },
        parseAs: "blob",
      })
      .catch(() => ({ data: undefined, response: undefined }));
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
            <RadioGroup value={format} onValueChange={(v) => setFormat(v as ExportFormat)} className="gap-2">
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
            </RadioGroup>
          </fieldset>

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

          <Label className="flex items-start gap-2 font-normal">
            <Checkbox checked={details} onCheckedChange={(v) => setDetails(v === true)} className="mt-0.5" />
            {t("details")}
          </Label>

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
          <Button onClick={() => void download()} disabled={busy || empty}>
            {busy ? <Spinner data-icon="inline-start" /> : <DownloadIcon data-icon="inline-start" />}
            {failed ? t("retry") : t("download", { file: fileName })}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
