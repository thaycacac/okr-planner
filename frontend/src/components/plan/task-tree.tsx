"use client";

import { ChevronRightIcon, CircleXIcon, PlusIcon, SearchIcon, XIcon } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useState } from "react";
import { cn } from "cn";

import { GuardedLink } from "@/components/app-shell/unsaved-changes";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { type KrView, type ObjectiveView, objectiveColor, type TaskView, taskMatches } from "@/lib/plan/plan-view";

import { DroppedGroup } from "./dropped-group";
import { ObjectiveCode, PriorityBadge } from "./plan-bits";
import { useReadyPlan } from "./plan-data";
import { TaskMenu } from "./task-dialogs";
import { ScheduleBadges } from "./task-sheet";
import { usePlanFormat } from "./use-plan-format";
import { useTaskActions } from "./use-task-actions";

const HIGHLIGHT_MS = 2000;
const TOGGLE_ROW =
  "flex w-full min-w-0 items-start gap-2 rounded-sm text-left outline-none focus-visible:ring-2 focus-visible:ring-ring";

type Group = { objective: ObjectiveView; krs: { kr: KrView; tasks: TaskView[] }[] };

const objectiveKey = (o: ObjectiveView) => `o-${o.objective.id}`;
const krKey = (k: KrView) => `k-${k.kr.id}`;

function lateLast(tasks: readonly TaskView[]) {
  return [...tasks].sort((a, b) => Number(a.late) - Number(b.late));
}

export function TaskTree({ krFilter }: { krFilter: number | null }) {
  const t = useTranslations("plan.tasks");
  const fmt = usePlanFormat();
  const { view, slug, collapsed, setCollapsed, selectTask, newTask, feasibility } = useReadyPlan();
  const [query, setQuery] = useState("");
  const [objectiveFilter, setObjectiveFilter] = useState("all");
  const [highlight, setHighlight] = useState<number | null>(null);
  const searching = query.trim() !== "";
  const filteredKr = krFilter === null ? undefined : view.objectives.flatMap((o) => o.krs).find((k) => k.kr.id === krFilter);

  const groups = useMemo<Group[]>(
    () =>
      view.objectives
        .filter((o) => objectiveFilter === "all" || String(o.objective.id) === objectiveFilter)
        .map((objective) => ({
          objective,
          krs: objective.krs
            .filter((kr) => krFilter === null || kr.kr.id === krFilter)
            .map((kr) => ({ kr, tasks: lateLast(kr.tasks.filter((task) => taskMatches(task, query))) }))
            .filter((k) => !searching || k.tasks.length > 0),
        }))
        .filter((g) => g.krs.length > 0),
    [view, objectiveFilter, krFilter, query, searching],
  );

  useEffect(() => {
    if (highlight === null) return;
    const timer = window.setTimeout(() => setHighlight(null), HIGHLIGHT_MS);
    return () => window.clearTimeout(timer);
  }, [highlight]);

  const isOpen = (key: string) => searching || !collapsed.has(key);
  const toggle = (key: string) => {
    const next = new Set(collapsed);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    setCollapsed(next);
  };
  const allOpen = collapsed.size === 0;

  function jumpTo(taskId: number) {
    const target = view.tasks.get(taskId);
    if (!target) return;
    const objective = view.objectives.find((o) => o.index === target.objectiveIndex);
    if (!objective) return;
    const kr = objective.krs.find((k) => k.kr.id === target.task.key_result_id);
    const next = new Set(collapsed);
    next.delete(objectiveKey(objective));
    if (kr) next.delete(krKey(kr));
    setCollapsed(next);
    setQuery("");
    setObjectiveFilter("all");
    setHighlight(taskId);
    window.requestAnimationFrame(() => {
      // Desktop table and mobile cards both render the task; only one of them is displayed.
      const anchor = Array.from(document.querySelectorAll<HTMLElement>(`[data-task-anchor="${taskId}"]`)).find(
        (node) => node.offsetParent !== null,
      );
      anchor?.scrollIntoView({ block: "center", behavior: "smooth" });
      anchor?.focus({ preventScroll: true });
    });
  }

  const firstKr = filteredKr ?? groups[0]?.krs[0]?.kr ?? view.objectives[0]?.krs[0];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-48 flex-1 sm:max-w-xs">
          <SearchIcon className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("search")}
            aria-label={t("search")}
            className="pl-8"
          />
        </div>
        <Select value={objectiveFilter} onValueChange={setObjectiveFilter}>
          <SelectTrigger className="w-44" aria-label={t("filterObjective")}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("allObjectives")}</SelectItem>
            {view.objectives.map((o) => (
              <SelectItem key={o.objective.id} value={String(o.objective.id)}>
                {o.code} · {o.objective.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(allOpen ? new Set(view.objectives.map(objectiveKey)) : new Set())}
        >
          {allOpen ? t("collapseAll") : t("expandAll")}
        </Button>
        {filteredKr && (
          <Badge variant="secondary" className="gap-1">
            {t("krFilter", { kr: filteredKr.code })}
            <Link href={`/q/${slug}/tasks`} aria-label={t("clearFilter")} className="rounded-full hover:text-foreground">
              <XIcon className="size-3" aria-hidden />
            </Link>
          </Badge>
        )}
        <span className="flex-1" />
        {firstKr && (
          <Button size="sm" variant="outline" onClick={() => newTask(firstKr.kr.id)}>
            <PlusIcon data-icon="inline-start" />
            {t("addTask")}
          </Button>
        )}
      </div>

      {feasibility && feasibility.lateTaskCount > 0 && (
        <Alert variant="destructive">
          <CircleXIcon />
          <AlertDescription className="flex flex-wrap items-center gap-x-3 gap-y-2 [&_a]:no-underline">
            <span>
              {t("lateBanner", {
                count: feasibility.lateTaskCount,
                hours: fmt.hours(feasibility.lateMinutes),
                date: fmt.date(feasibility.windowEnd),
              })}
            </span>
            <Button asChild size="sm" variant="outline">
              <GuardedLink href={`/q/${slug}/options`}>{t("seeOptions")}</GuardedLink>
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {groups.length === 0 ? (
        <p className="rounded-xl border border-dashed border-border p-6 text-sm text-muted-foreground">{t("noMatch")}</p>
      ) : (
        <>
          <div className="hidden overflow-hidden rounded-xl border border-border md:block">
            <Table aria-label={t("tableLabel")}>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">
                    <span className="sr-only">{t("colDone")}</span>
                  </TableHead>
                  <TableHead>{t("colName")}</TableHead>
                  <TableHead className="w-16 text-right">{t("colHours")}</TableHead>
                  <TableHead className="w-28">{t("colDates")}</TableHead>
                  <TableHead className="w-24">{t("colDeps")}</TableHead>
                  <TableHead className="w-32">{t("colStatus")}</TableHead>
                  <TableHead className="w-10">
                    <span className="sr-only">{t("colActions")}</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {groups.map(({ objective, krs }) => {
                  const oOpen = isOpen(objectiveKey(objective));
                  return [
                    <TableRow key={objectiveKey(objective)} className="bg-muted/40 hover:bg-muted/60">
                      <TableCell />
                      <TableCell className="max-w-0 whitespace-normal">
                        <button
                          type="button"
                          onClick={() => toggle(objectiveKey(objective))}
                          aria-expanded={oOpen}
                          className={cn(TOGGLE_ROW, "font-semibold")}
                        >
                          <ChevronRightIcon className={cn("mt-0.5 size-4 shrink-0 transition-transform", oOpen && "rotate-90")} aria-hidden />
                          <ObjectiveCode index={objective.index} />
                          <span className="flex min-w-0 flex-col gap-1">
                            <span className="line-clamp-2" title={objective.objective.title}>
                              {objective.objective.title}
                            </span>
                            <PriorityBadge priority={objective.objective.priority} className="w-fit text-xs" />
                          </span>
                        </button>
                      </TableCell>
                      <TableCell className="text-right align-top font-medium tabular-nums">{fmt.hours(objective.minutes)}</TableCell>
                      <TableCell className="align-top text-muted-foreground">{fmt.dayRange(objective.start, objective.end)}</TableCell>
                      <TableCell />
                      <TableCell />
                      <TableCell />
                    </TableRow>,
                    ...(oOpen
                      ? krs.flatMap(({ kr, tasks }) => {
                          const kOpen = isOpen(krKey(kr));
                          return [
                            <TableRow key={krKey(kr)}>
                              <TableCell />
                              <TableCell className="max-w-0 pl-6 whitespace-normal">
                                <button
                                  type="button"
                                  onClick={() => toggle(krKey(kr))}
                                  aria-expanded={kOpen}
                                  className={TOGGLE_ROW}
                                >
                                  <ChevronRightIcon className={cn("mt-0.5 size-4 shrink-0 transition-transform", kOpen && "rotate-90")} aria-hidden />
                                  <span className="mt-0.5 shrink-0 font-mono text-xs text-muted-foreground">{kr.code}</span>
                                  <span className="flex min-w-0 flex-col gap-1">
                                    <span className="line-clamp-2 font-medium" title={kr.kr.text}>
                                      {kr.kr.text}
                                    </span>
                                    <KrKind kr={kr} />
                                  </span>
                                </button>
                              </TableCell>
                              <TableCell className="text-right align-top tabular-nums">{fmt.hours(kr.minutes)}</TableCell>
                              <TableCell className="align-top text-muted-foreground">{fmt.dayRange(kr.start, kr.end)}</TableCell>
                              <TableCell />
                              <TableCell />
                              <TableCell />
                            </TableRow>,
                            ...(kOpen
                              ? tasks.map((task) => (
                                  <TableRow
                                    key={task.task.id}
                                    className={cn(
                                      task.late && "bg-destructive/5",
                                      highlight === task.task.id && "bg-accent",
                                    )}
                                  >
                                    <TableCell className="align-top">
                                      <DoneCheckbox task={task} />
                                    </TableCell>
                                    <TableCell className="max-w-0 pl-12 whitespace-normal">
                                      <button
                                        type="button"
                                        data-task-anchor={task.task.id}
                                        onClick={() => selectTask(task.task.id)}
                                        className="flex w-full min-w-0 items-start gap-2 rounded-sm text-left outline-none hover:underline focus-visible:ring-2 focus-visible:ring-ring"
                                      >
                                        <span
                                          className="mt-1.5 size-2 shrink-0 rounded-full"
                                          style={{ backgroundColor: objectiveColor(task.objectiveIndex) }}
                                          aria-hidden
                                        />
                                        <span className="mt-0.5 shrink-0 font-mono text-xs text-muted-foreground">{task.code}</span>
                                        <span
                                          className={cn("line-clamp-2", task.done && "text-muted-foreground line-through")}
                                          title={task.task.title}
                                        >
                                          {task.task.title}
                                        </span>
                                      </button>
                                    </TableCell>
                                    <TableCell className="text-right align-top tabular-nums">{fmt.hours(task.task.estimate_minutes)}</TableCell>
                                    <TableCell className="align-top whitespace-nowrap">{fmt.dayRange(task.start, task.end)}</TableCell>
                                    <TableCell className="align-top">
                                      <DependencyChips task={task} onJump={jumpTo} />
                                    </TableCell>
                                    <TableCell className="align-top">
                                      <div className="flex flex-wrap gap-1">
                                        <ScheduleBadges view={task} />
                                      </div>
                                    </TableCell>
                                    <TableCell className="py-1 align-top">
                                      <TaskMenu view={task} />
                                    </TableCell>
                                  </TableRow>
                                ))
                              : []),
                            ...(kOpen && !searching
                              ? [
                                  <TableRow key={`${krKey(kr)}-add`} className="hover:bg-transparent">
                                    <TableCell />
                                    <TableCell colSpan={6} className="py-1 pl-12">
                                      {tasks.length === 0 && (
                                        <span className="mr-2 text-sm text-muted-foreground">{t("krEmpty", { kr: kr.code })}</span>
                                      )}
                                      <Button variant="ghost" size="sm" onClick={() => newTask(kr.kr.id)}>
                                        <PlusIcon data-icon="inline-start" />
                                        {t("addTaskToKr", { kr: kr.code })}
                                      </Button>
                                    </TableCell>
                                  </TableRow>,
                                ]
                              : []),
                          ];
                        })
                      : []),
                  ];
                })}
              </TableBody>
            </Table>
          </div>

          <div className="flex flex-col gap-4 md:hidden">
            {groups.map(({ objective, krs }) => {
              const oOpen = isOpen(objectiveKey(objective));
              return (
                <section key={objectiveKey(objective)} className="flex flex-col gap-2">
                  <button
                    type="button"
                    onClick={() => toggle(objectiveKey(objective))}
                    aria-expanded={oOpen}
                    className="sticky top-14 z-10 flex items-center gap-2 border-b border-border bg-background/95 py-2 text-left font-semibold outline-none backdrop-blur focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <ChevronRightIcon className={cn("size-4 shrink-0 transition-transform", oOpen && "rotate-90")} aria-hidden />
                    <ObjectiveCode index={objective.index} />
                    <span className="min-w-0 flex-1 truncate">{objective.objective.title}</span>
                    <span className="text-sm font-normal text-muted-foreground">{fmt.hours(objective.minutes)}</span>
                  </button>
                  {oOpen &&
                    krs.map(({ kr, tasks }) => (
                      <div key={krKey(kr)} className="flex flex-col gap-2 pl-2">
                        <p className="flex items-center gap-2 text-sm">
                          <span className="font-mono text-xs text-muted-foreground">{kr.code}</span>
                          <span className="min-w-0 flex-1 truncate font-medium">{kr.kr.text}</span>
                          <span className="text-muted-foreground">{fmt.hours(kr.minutes)}</span>
                        </p>
                        {tasks.map((task) => (
                          <div
                            key={task.task.id}
                            className={cn(
                              "flex items-start gap-1 rounded-lg border border-border border-l-4 py-1 pr-1 pl-0 text-sm",
                              task.late && "bg-destructive/5",
                              highlight === task.task.id && "bg-accent",
                            )}
                            style={{ borderLeftColor: objectiveColor(task.objectiveIndex) }}
                          >
                            <DoneCheckbox task={task} touch />
                            <div className="flex min-w-0 flex-1 flex-col gap-1.5 py-2">
                              <button
                                type="button"
                                data-task-anchor={task.task.id}
                                onClick={() => selectTask(task.task.id)}
                                className={cn(
                                  "text-left font-medium outline-none focus-visible:ring-2 focus-visible:ring-ring",
                                  task.done && "text-muted-foreground line-through",
                                )}
                              >
                                <span className="mr-1.5 font-mono text-xs text-muted-foreground">{task.code}</span>
                                {task.task.title}
                              </button>
                              <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
                                <span>{fmt.hours(task.task.estimate_minutes)}</span>
                                <span aria-hidden>·</span>
                                <span>{fmt.dayRange(task.start, task.end)}</span>
                                <ScheduleBadges view={task} compact />
                              </p>
                              <DependencyChips task={task} onJump={jumpTo} prefix />
                            </div>
                            <TaskMenu view={task} />
                          </div>
                        ))}
                        {!searching && (
                          <Button variant="ghost" size="sm" className="h-10 w-fit" onClick={() => newTask(kr.kr.id)}>
                            <PlusIcon data-icon="inline-start" />
                            {t("addTaskToKr", { kr: kr.code })}
                          </Button>
                        )}
                      </div>
                    ))}
                </section>
              );
            })}
          </div>
        </>
      )}
      {!searching && krFilter === null && <DroppedGroup />}
    </div>
  );
}

function DoneCheckbox({ task, touch = false }: { task: TaskView; touch?: boolean }) {
  const t = useTranslations("plan.tasks");
  const actions = useTaskActions();
  return (
    <label className={cn("flex shrink-0 cursor-pointer items-center justify-center", touch ? "size-11" : "size-6")}>
      <Checkbox
        checked={task.done}
        onCheckedChange={(checked) => void actions.setDone(task, checked === true)}
        aria-label={t(task.done ? "markTodoLabel" : "markDoneLabel", { code: task.code })}
      />
    </label>
  );
}

function KrKind({ kr }: { kr: KrView }) {
  const t = useTranslations("plan.okr");
  const fmt = usePlanFormat();
  const { kind, baseline, target, unit } = kr.kr;
  const measure =
    kind === "numeric" && target !== null
      ? `${baseline !== null ? `${fmt.quantity(baseline, unit)} → ` : ""}${fmt.quantity(target, unit)}`
      : null;
  return (
    <span className="flex flex-wrap items-center gap-1.5">
      <Badge variant="outline" className="text-xs font-normal">
        {t(`kinds.${kind}`)}
      </Badge>
      {measure && <span className="text-xs whitespace-nowrap text-muted-foreground">{measure}</span>}
    </span>
  );
}

function DependencyChips({
  task,
  onJump,
  prefix = false,
}: {
  task: TaskView;
  onJump: (taskId: number) => void;
  prefix?: boolean;
}) {
  const { view } = useReadyPlan();
  if (task.dependsOn.length === 0) return prefix ? null : <span className="text-muted-foreground">—</span>;
  return (
    <span className="flex flex-wrap gap-1">
      {task.dependsOn.map((id) => {
        const dep = view.tasks.get(id);
        if (!dep) return null;
        return (
          <button
            key={id}
            type="button"
            title={dep.task.title}
            onClick={() => onJump(id)}
            className="rounded-md border border-border px-1.5 py-0.5 font-mono text-xs hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          >
            {prefix ? `← ${dep.code}` : dep.code}
          </button>
        );
      })}
    </span>
  );
}
