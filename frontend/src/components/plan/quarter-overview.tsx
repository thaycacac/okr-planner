"use client";

import { ChartColumnIcon, DownloadIcon, EllipsisIcon, PlusIcon, SparklesIcon, Trash2Icon } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";
import { toast } from "sonner";

import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { LoadError } from "@/components/settings/load-error";
import { useLoad } from "@/hooks/use-load";
import { api } from "@/lib/api/client";
import type { FeasibilityStatus, QuarterSummary } from "@/lib/api/types";
import { localToday } from "@/lib/plan/dates";
import { isActive } from "@/lib/plan/progress";
import { overviewOrder, quarterLabel, quarterSlug, quarterStatus, toRef } from "@/lib/plan/quarter";
import { listQuarters } from "@/lib/plan/sync";

import { ExportDialog } from "./export-dialog";
import { FeasibilityBadge } from "./feasibility-panel";
import { QuarterStatusBadge } from "./plan-bits";
import { usePlanFormat } from "./use-plan-format";

const fetchQuarters = () => listQuarters(api);
const ALL = "all";

export function QuarterOverview() {
  const t = useTranslations("home");
  const [state, retry, refresh] = useLoad(fetchQuarters);
  const [year, setYear] = useState(ALL);
  const [exporting, setExporting] = useState<QuarterSummary | null>(null);
  const [deleting, setDeleting] = useState<QuarterSummary | null>(null);
  const quarters = state.status === "ready" ? state.data : [];
  const years = [...new Set(quarters.map((q) => q.year))].sort();
  const shown = [...quarters]
    .filter((q) => year === ALL || String(q.year) === year)
    .sort(overviewOrder(localToday()));

  return (
    <div className="flex max-w-4xl flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex flex-col gap-1">
          <h1 className="font-heading text-2xl font-semibold tracking-tight">{t("title")}</h1>
          <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
        </div>
        <Button asChild>
          <Link href="/plan/new">
            <PlusIcon data-icon="inline-start" />
            {t("newPlan")}
          </Link>
        </Button>
      </div>

      {years.length > 1 && (
        <ToggleGroup
          type="single"
          variant="outline"
          size="sm"
          value={year}
          onValueChange={(v) => v && setYear(v)}
          aria-label={t("yearFilter")}
          className="w-fit"
        >
          <ToggleGroupItem value={ALL}>{t("allYears")}</ToggleGroupItem>
          {years.map((y) => (
            <ToggleGroupItem key={y} value={String(y)}>
              {y}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      )}

      {state.status === "loading" && (
        <div className="grid gap-3 sm:grid-cols-2" aria-busy="true">
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
        </div>
      )}
      {state.status === "error" && <LoadError onRetry={retry} />}
      {state.status === "ready" &&
        (state.data.length === 0 ? (
          <div className="flex flex-col items-start gap-3 rounded-xl border border-dashed border-border p-6">
            <SparklesIcon className="size-6 text-muted-foreground" aria-hidden />
            <p className="font-medium">{t("emptyTitle")}</p>
            <p className="text-sm text-muted-foreground">{t("emptyBody")}</p>
            <Button asChild>
              <Link href="/plan/new">{t("start")}</Link>
            </Button>
          </div>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2">
            {shown.map((q) => (
              <li key={q.id}>
                <QuarterCard quarter={q} onExport={() => setExporting(q)} onDelete={() => setDeleting(q)} />
              </li>
            ))}
          </ul>
        ))}

      <ExportDialog
        key={exporting?.id ?? "none"}
        open={exporting !== null}
        onOpenChange={(open) => !open && setExporting(null)}
        quarters={quarters}
        initialQuarterId={exporting?.id ?? null}
      />
      <DeleteQuarterDialog
        quarter={deleting}
        onClose={() => setDeleting(null)}
        onExport={() => {
          setExporting(deleting);
          setDeleting(null);
        }}
        onDeleted={async () => {
          setDeleting(null);
          await refresh();
        }}
      />
    </div>
  );
}

function QuarterCard({
  quarter,
  onExport,
  onDelete,
}: {
  quarter: QuarterSummary;
  onExport: () => void;
  onDelete: () => void;
}) {
  const t = useTranslations("home");
  const fmt = usePlanFormat();
  const ref = toRef(quarter);
  const slug = quarterSlug(ref);
  const status = quarterStatus(ref, localToday());
  const job = quarter.latest_plan_run_id;
  const run = quarter.latest_plan_status;
  const hasTasks = quarter.task_count > 0;
  const fetchFeasibility = useCallback(async (): Promise<FeasibilityStatus | null | undefined> => {
    if (!hasTasks) return null;
    const { data, response } = await api.GET("/quarters/{quarter_id}/schedule", {
      params: { path: { quarter_id: quarter.id } },
    });
    if (response.status === 404) return null;
    return data?.feasibility.status;
  }, [hasTasks, quarter.id]);
  const [feasibility] = useLoad(fetchFeasibility);
  const red = feasibility.status === "ready" && feasibility.data === "red";

  let primary: { href: string; label: string };
  if (job && run && isActive(run)) primary = { href: `/plan/new/generate?job=${job}`, label: t("viewProgress") };
  else if (job && run === "needs_clarification") primary = { href: `/plan/new/clarify?job=${job}`, label: t("answer") };
  else if (quarter.task_count > 0) primary = { href: `/q/${slug}/tasks`, label: status.kind === "ended" ? t("review") : t("openPlan") };
  else primary = { href: `/plan/new/okr?q=${slug}`, label: t("continueOkr") };

  return (
    <Card size="sm" className="h-full">
      <CardContent className="flex h-full flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-heading text-lg font-semibold">{quarterLabel(ref)}</h2>
          <div className="flex flex-wrap items-center gap-1.5">
            {feasibility.status === "ready" && feasibility.data && <FeasibilityBadge status={feasibility.data} />}
            <QuarterStatusBadge status={status} />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon-sm" className="max-md:size-10" aria-label={t("menu", { quarter: quarterLabel(ref) })}>
                  <EllipsisIcon />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="min-w-48">
                {hasTasks && (
                  <DropdownMenuItem asChild>
                    <Link href={`/q/${slug}/workload`}>
                      <ChartColumnIcon />
                      {t("viewWorkload")}
                    </Link>
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem onSelect={onExport} disabled={!hasTasks}>
                  <DownloadIcon />
                  {t("export")}
                </DropdownMenuItem>
                {status.kind !== "ongoing" && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem variant="destructive" onSelect={onDelete}>
                      <Trash2Icon />
                      {t("delete")}
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
        <p className="text-xs text-muted-foreground">
          {fmt.date(quarter.start_date)} – {fmt.date(quarter.end_date)}
        </p>
        <p className="text-sm">
          {t("counts", {
            objectives: quarter.objective_count,
            krs: quarter.key_result_count,
            tasks: quarter.task_count,
          })}
        </p>
        {run && (
          <p className="text-xs text-muted-foreground">
            {t("lastRun", { status: t(`runStatus.${run}`) })}
          </p>
        )}
        <div className="mt-auto flex flex-wrap gap-2">
          <Button asChild size="sm">
            <Link href={primary.href}>{primary.label}</Link>
          </Button>
          {red && (
            <Button asChild size="sm" variant="outline">
              <Link href={`/q/${slug}/options`}>{t("seeOptions")}</Link>
            </Button>
          )}
          {hasTasks && !red && (
            <Button asChild size="sm" variant="outline">
              <Link href={`/q/${slug}/calendar`}>{t("calendar")}</Link>
            </Button>
          )}
          <Button asChild size="sm" variant="ghost">
            <Link href={`/plan/new/okr?q=${slug}`}>{t("editOkr")}</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function DeleteQuarterDialog({
  quarter,
  onClose,
  onExport,
  onDeleted,
}: {
  quarter: QuarterSummary | null;
  onClose: () => void;
  onExport: () => void;
  onDeleted: () => Promise<void>;
}) {
  const t = useTranslations("home.deleteDialog");
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const label = quarter ? quarterLabel(toRef(quarter)) : "";
  const matches = typed.trim().toUpperCase() === label.toUpperCase();

  function close() {
    setTyped("");
    onClose();
  }

  async function remove() {
    if (!quarter || !matches) return;
    setBusy(true);
    const { response } = await api.DELETE("/quarters/{quarter_id}", { params: { path: { quarter_id: quarter.id } } });
    setBusy(false);
    if (!response.ok) {
      toast.error(response.status === 409 ? t("running") : t("failed"));
      return;
    }
    setTyped("");
    toast.success(t("deleted", { quarter: label }));
    await onDeleted();
  }

  return (
    <AlertDialog open={quarter !== null} onOpenChange={(open) => !open && close()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{t("title", { quarter: label })}</AlertDialogTitle>
          <AlertDialogDescription>
            {t("body", { objectives: quarter?.objective_count ?? 0, tasks: quarter?.task_count ?? 0 })}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="delete-quarter-confirm">{t("typeToConfirm", { quarter: label })}</Label>
          <Input
            id="delete-quarter-confirm"
            value={typed}
            onChange={(e) => setTyped(e.target.value)}
            autoComplete="off"
            placeholder={label}
          />
        </div>
        <AlertDialogFooter className="flex-wrap">
          <AlertDialogCancel disabled={busy}>{t("cancel")}</AlertDialogCancel>
          {(quarter?.task_count ?? 0) > 0 && (
            <Button variant="outline" onClick={onExport} disabled={busy}>
              <DownloadIcon data-icon="inline-start" />
              {t("exportFirst")}
            </Button>
          )}
          <Button variant="destructive" onClick={() => void remove()} disabled={!matches || busy}>
            {busy && <Spinner data-icon="inline-start" />}
            {t("confirm")}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
