"use client";

import {
  ArrowDownIcon,
  ArrowUpIcon,
  ChevronDownIcon,
  CopyIcon,
  EllipsisIcon,
  PlusIcon,
  Trash2Icon,
  XIcon,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { useId, useState } from "react";
import { cn } from "cn";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { KeyResultKind, ObjectivePriority } from "@/lib/api/types";
import {
  type DraftIssue,
  type IssueCode,
  type IssueField,
  type KrDraft,
  type ObjectiveDraft,
  SOFT_MAX_KEY_RESULTS,
} from "@/lib/plan/okr-draft";
import { objectiveColor } from "@/lib/plan/plan-view";

import { ObjectiveCode } from "./plan-bits";

export function useIssueText() {
  const t = useTranslations("plan.okr");
  return (code: IssueCode) => t(`issues.${code}`);
}

const KINDS: readonly KeyResultKind[] = ["numeric", "milestone", "binary", "other"];
const PRIORITIES: readonly ObjectivePriority[] = ["high", "medium", "low"];

export function fieldId(key: string, field: IssueField | "title") {
  return `okr-${key}-${field}`;
}

export type ObjectiveActions = {
  update: (patch: Partial<ObjectiveDraft>) => void;
  updateKr: (krKey: string, patch: Partial<KrDraft>) => void;
  addKr: () => void;
  removeKr: (krKey: string) => void;
  duplicate: () => void;
  move: (delta: -1 | 1) => void;
  remove: () => void;
  touch: (id: string) => void;
};

type Props = {
  objective: ObjectiveDraft;
  index: number;
  count: number;
  collapsed: boolean;
  onToggle: () => void;
  issues: DraftIssue[];
  quarterStart: string;
  quarterEnd: string;
  actions: ObjectiveActions;
};

export function ObjectiveCard({
  objective,
  index,
  count,
  collapsed,
  onToggle,
  issues,
  quarterStart,
  quarterEnd,
  actions,
}: Props) {
  const t = useTranslations("plan.okr");
  const tIssue = useIssueText();
  const [contextOpen, setContextOpen] = useState(Boolean(objective.domain || objective.constraints));
  const bodyId = useId();
  const titleIssue = issues.find((i) => !i.krKey && i.field === "title");
  const objectiveIssues = issues.filter((i) => !i.krKey && !i.field);
  const domains = t.raw("domains") as string[];

  return (
    <section
      aria-labelledby={fieldId(objective.key, "title")}
      className="rounded-xl border border-border bg-card shadow-xs"
      style={{ borderLeft: `4px solid ${objectiveColor(index)}` }}
    >
      <div className="flex flex-wrap items-end gap-2 p-3 md:flex-nowrap">
        <div className="pb-2">
          <ObjectiveCode index={index} />
        </div>
        <div className="flex min-w-0 flex-1 basis-full flex-col gap-1.5 md:basis-auto">
          <Label htmlFor={fieldId(objective.key, "title")} className="text-xs text-muted-foreground">
            {t("fields.objective")}
          </Label>
          <Input
            id={fieldId(objective.key, "title")}
            value={objective.title}
            placeholder={t("objectivePlaceholder")}
            onChange={(e) => actions.update({ title: e.target.value })}
            onBlur={() => actions.touch(fieldId(objective.key, "title"))}
            aria-invalid={titleIssue ? true : undefined}
            aria-describedby={titleIssue ? `${fieldId(objective.key, "title")}-error` : undefined}
            className="font-medium"
          />
        </div>
        {(objective.inactive || (objective.keyResults.length > 0 && objective.keyResults.every((kr) => kr.inactive))) && (
          <Badge variant="outline" className="border-dashed bg-muted font-normal text-muted-foreground">
            {t("paused")}
          </Badge>
        )}
        <div className="flex flex-col gap-1.5">
          <span id={`${objective.key}-priority`} className="text-xs text-muted-foreground">
            {t("fields.priority")}
          </span>
          <ToggleGroup
            type="single"
            size="sm"
            variant="outline"
            spacing={0}
            value={objective.priority}
            onValueChange={(value) => value && actions.update({ priority: value as ObjectivePriority })}
            aria-labelledby={`${objective.key}-priority`}
          >
            {PRIORITIES.map((p) => (
              <ToggleGroupItem key={p} value={p} className="px-3">
                {t(`priorityShort.${p}`)}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </div>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={actions.remove}
          aria-label={t("deleteObjective", { code: `O${index + 1}` })}
          title={t("deleteObjective", { code: `O${index + 1}` })}
        >
          <Trash2Icon />
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon-sm" aria-label={t("objectiveMenu", { code: `O${index + 1}` })}>
              <EllipsisIcon />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onSelect={actions.duplicate}>
              <CopyIcon /> {t("duplicate")}
            </DropdownMenuItem>
            <DropdownMenuItem disabled={index === 0} onSelect={() => actions.move(-1)}>
              <ArrowUpIcon /> {t("moveUp")}
            </DropdownMenuItem>
            <DropdownMenuItem disabled={index === count - 1} onSelect={() => actions.move(1)}>
              <ArrowDownIcon /> {t("moveDown")}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem variant="destructive" onSelect={actions.remove}>
              <Trash2Icon /> {t("delete")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={onToggle}
          aria-expanded={!collapsed}
          aria-controls={bodyId}
          aria-label={collapsed ? t("expand") : t("collapse")}
        >
          <ChevronDownIcon className={cn("transition-transform", !collapsed && "rotate-180")} />
        </Button>
      </div>
      {titleIssue && (
        <p id={`${fieldId(objective.key, "title")}-error`} className="-mt-1 px-3 pb-2 text-xs text-destructive">
          {tIssue(titleIssue.code)}
        </p>
      )}

      <div id={bodyId} hidden={collapsed} className="flex flex-col gap-3 border-t border-border p-3">
        {contextOpen ? (
          <div className="grid gap-3 rounded-lg bg-muted/50 p-3 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor={`${objective.key}-domain`}>{t("domain")}</Label>
              <Input
                id={`${objective.key}-domain`}
                list={`${objective.key}-domains`}
                value={objective.domain}
                placeholder={t("domainPlaceholder")}
                onChange={(e) => actions.update({ domain: e.target.value })}
              />
              <datalist id={`${objective.key}-domains`}>
                {domains.map((d) => (
                  <option key={d} value={d} />
                ))}
              </datalist>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor={`${objective.key}-constraints`}>{t("constraints")}</Label>
              <Input
                id={`${objective.key}-constraints`}
                value={objective.constraints}
                placeholder={t("constraintsPlaceholder")}
                onChange={(e) => actions.update({ constraints: e.target.value })}
              />
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setContextOpen(true)}
            className="w-fit text-sm font-medium text-muted-foreground underline-offset-4 outline-none hover:text-foreground hover:underline focus-visible:ring-2 focus-visible:ring-ring"
          >
            {t("addContext")}
          </button>
        )}

        <ol className="flex flex-col gap-3" aria-label={t("krList", { code: `O${index + 1}` })}>
          {objective.keyResults.map((kr, ki) => (
            <KrRow
              key={kr.key}
              kr={kr}
              code={`KR ${index + 1}.${ki + 1}`}
              issues={issues.filter((i) => i.krKey === kr.key)}
              quarterStart={quarterStart}
              quarterEnd={quarterEnd}
              onChange={(patch) => actions.updateKr(kr.key, patch)}
              onRemove={() => actions.removeKr(kr.key)}
              onTouch={actions.touch}
            />
          ))}
        </ol>

        {objectiveIssues.map((issue) => (
          <p key={issue.code} className="text-xs text-destructive">
            {tIssue(issue.code)}
          </p>
        ))}

        <div className="flex flex-wrap items-center gap-3">
          <Button variant="ghost" size="sm" onClick={actions.addKr}>
            <PlusIcon data-icon="inline-start" />
            {t("addKr")}
          </Button>
          <span
            className={cn(
              "text-xs",
              objective.keyResults.length > SOFT_MAX_KEY_RESULTS ? "text-warning" : "text-muted-foreground",
            )}
          >
            {t("krCount", { count: objective.keyResults.length, max: SOFT_MAX_KEY_RESULTS })}
          </span>
        </div>
      </div>
    </section>
  );
}

type KrRowProps = {
  kr: KrDraft;
  code: string;
  issues: DraftIssue[];
  quarterStart: string;
  quarterEnd: string;
  onChange: (patch: Partial<KrDraft>) => void;
  onRemove: () => void;
  onTouch: (id: string) => void;
};

function KrRow({ kr, code, issues, quarterStart, quarterEnd, onChange, onRemove, onTouch }: KrRowProps) {
  const t = useTranslations("plan.okr");
  const tIssue = useIssueText();
  const issueFor = (field: IssueField) => issues.find((i) => i.field === field);
  const errorId = (field: IssueField) => `${fieldId(kr.key, field)}-error`;
  const invalid = (field: IssueField) =>
    issueFor(field) ? { "aria-invalid": true as const, "aria-describedby": errorId(field) } : {};

  return (
    <li className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-2 rounded-lg border border-border p-3 md:grid-cols-[4.5rem_minmax(0,1fr)_9rem_auto] md:items-start md:border-0 md:p-0">
      <span className="col-start-1 row-start-1 font-mono text-xs font-semibold text-muted-foreground md:pt-7">{code}</span>
      <div className="col-span-2 flex flex-col gap-1.5 md:col-span-1 md:col-start-2 md:row-start-1">
        <Label htmlFor={fieldId(kr.key, "text")} className="text-xs text-muted-foreground">
          {t("fields.keyResult")}
        </Label>
        <Input
          id={fieldId(kr.key, "text")}
          value={kr.text}
          placeholder={t("krPlaceholder")}
          onChange={(e) => onChange({ text: e.target.value })}
          onBlur={() => onTouch(fieldId(kr.key, "text"))}
          {...invalid("text")}
        />
        {issueFor("text") && (
          <p id={errorId("text")} className="text-xs text-destructive">
            {tIssue(issueFor("text")!.code)}
          </p>
        )}
        {kr.inactive && (
          <p className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <Badge variant="outline" className="border-dashed bg-muted font-normal text-muted-foreground">
              {t("dropped")}
            </Badge>
            {t("droppedHint")}
          </p>
        )}
      </div>
      <div className="col-span-2 flex flex-col gap-1.5 md:col-span-1 md:col-start-3 md:row-start-1">
        <Label htmlFor={`${kr.key}-kind`} className="text-xs text-muted-foreground">
          {t("fields.kind")}
        </Label>
        <Select value={kr.kind} onValueChange={(value) => onChange({ kind: value as KeyResultKind })}>
          <SelectTrigger id={`${kr.key}-kind`} className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {KINDS.map((kind) => (
              <SelectItem key={kind} value={kind}>
                {t(`kinds.${kind}`)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="col-span-2 flex flex-col gap-2 empty:hidden md:col-span-1 md:col-start-2 md:row-start-2">
        {kr.kind === "numeric" && (
          <div className="grid grid-cols-3 gap-2">
            {(["baseline", "target"] as const).map((field) => (
              <div key={field} className="flex flex-col gap-1">
                <Label htmlFor={fieldId(kr.key, field)} className="text-xs text-muted-foreground">
                  {t(field)}
                </Label>
                <Input
                  id={fieldId(kr.key, field)}
                  inputMode="decimal"
                  value={kr[field]}
                  placeholder={field === "baseline" ? "800" : "2.000"}
                  onChange={(e) => onChange({ [field]: e.target.value })}
                  onBlur={() => onTouch(fieldId(kr.key, field))}
                  {...invalid(field)}
                />
              </div>
            ))}
            <div className="flex flex-col gap-1">
              <Label htmlFor={`${kr.key}-unit`} className="text-xs text-muted-foreground">
                {t("unit")}
              </Label>
              <Input
                id={`${kr.key}-unit`}
                value={kr.unit}
                placeholder={t("unitPlaceholder")}
                onChange={(e) => onChange({ unit: e.target.value })}
              />
            </div>
            {(["baseline", "target"] as const).map(
              (field) =>
                issueFor(field) && (
                  <p key={field} id={errorId(field)} className="col-span-3 text-xs text-destructive">
                    {tIssue(issueFor(field)!.code)}
                  </p>
                ),
            )}
          </div>
        )}
        {kr.kind === "milestone" && (
          <div className="flex flex-col gap-1 sm:max-w-56">
            <Label htmlFor={`${kr.key}-due`} className="text-xs text-muted-foreground">
              {t("dueDate")}
            </Label>
            <Input
              id={`${kr.key}-due`}
              type="date"
              min={quarterStart}
              max={quarterEnd}
              value={kr.dueDate}
              onChange={(e) => onChange({ dueDate: e.target.value })}
            />
          </div>
        )}
        {kr.kind === "other" && (
          <div className="flex flex-col gap-1">
            <Label htmlFor={`${kr.key}-note`} className="text-xs text-muted-foreground">
              {t("note")}
            </Label>
            <Input
              id={`${kr.key}-note`}
              value={kr.note}
              placeholder={t("notePlaceholder")}
              onChange={(e) => onChange({ note: e.target.value })}
            />
          </div>
        )}
      </div>
      <Button
        variant="ghost"
        size="icon-sm"
        className="col-start-2 row-start-1 justify-self-end md:col-start-4 md:mt-6"
        onClick={onRemove}
        aria-label={t("removeKr", { code })}
      >
        <XIcon />
      </Button>
    </li>
  );
}
