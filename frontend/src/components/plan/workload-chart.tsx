"use client";

import {
  Bar,
  CartesianGrid,
  ComposedChart,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  type TooltipContentProps,
  type TooltipValueType,
  XAxis,
  YAxis,
} from "recharts";

import { objectiveColor } from "@/lib/plan/plan-view";

export type WorkloadChartRow = {
  label: string;
  /** Hours per objective, keyed `o0`, `o1`, … */
  [objective: `o${number}`]: number;
  free: number;
  late: number;
  capacity: number;
  percentLabel: string;
  tooltipTitle: string;
};

export type WorkloadChartProps = {
  rows: WorkloadChartRow[];
  objectives: { index: number; code: string }[];
  labels: { capacity: string; free: string; late: string; hoursUnit: string };
  formatHours: (hours: number) => string;
};

export default function WorkloadChart({ rows, objectives, labels, formatHours }: WorkloadChartProps) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <ComposedChart data={rows.map((row) => ({ ...row, cap: 0.001 }))} margin={{ top: 24, right: 8, bottom: 0, left: 0 }} barCategoryGap="18%">
        <CartesianGrid vertical={false} stroke="var(--border)" />
        <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: "var(--muted-foreground)", fontSize: 12 }} interval={0} />
        <YAxis
          tickLine={false}
          axisLine={false}
          width={40}
          tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
          tickFormatter={(v: number) => `${v}${labels.hoursUnit}`}
        />
        <Tooltip
          cursor={{ fill: "var(--muted)", opacity: 0.5 }}
          content={(props: TooltipContentProps<TooltipValueType, string | number>) => (
            <ChartTooltip {...props} objectives={objectives} labels={labels} formatHours={formatHours} />
          )}
        />
        {objectives.map((o) => (
          <Bar key={o.index} dataKey={`o${o.index}`} stackId="load" fill={objectiveColor(o.index)} name={o.code} isAnimationActive={false} />
        ))}
        <Bar
          dataKey="late"
          stackId="load"
          fill="color-mix(in oklab, var(--destructive) 30%, transparent)"
          stroke="var(--destructive)"
          strokeDasharray="4 3"
          isAnimationActive={false}
        />
        <Bar
          dataKey="free"
          stackId="load"
          fill="transparent"
          stroke="var(--muted-foreground)"
          strokeDasharray="4 3"
          strokeOpacity={0.6}
          isAnimationActive={false}
        />
        {/* Recharts skips labels on zero-height bars, so full periods get their % from a hairline cap. */}
        <Bar dataKey="cap" stackId="load" fill="transparent" isAnimationActive={false}>
          <LabelList dataKey="percentLabel" position="top" fill="var(--foreground)" fontSize={12} />
        </Bar>
      </ComposedChart>
    </ResponsiveContainer>
  );
}

function ChartTooltip({
  active,
  payload,
  objectives,
  labels,
  formatHours,
}: TooltipContentProps<TooltipValueType, string | number> & Omit<WorkloadChartProps, "rows">) {
  const row = payload?.[0]?.payload as WorkloadChartRow | undefined;
  if (!active || !row) return null;
  return (
    <div className="flex min-w-44 flex-col gap-1 rounded-lg border border-border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-md">
      <p className="font-medium">{row.tooltipTitle}</p>
      <p className="flex justify-between gap-4 text-muted-foreground">
        <span>{labels.capacity}</span>
        <span className="tabular-nums">{formatHours(row.capacity)}</span>
      </p>
      {objectives.map((o) =>
        row[`o${o.index}`] > 0 ? (
          <p key={o.index} className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-1.5">
              <span className="size-2 rounded-sm" style={{ backgroundColor: objectiveColor(o.index) }} aria-hidden />
              {o.code}
            </span>
            <span className="tabular-nums">{formatHours(row[`o${o.index}`])}</span>
          </p>
        ) : null,
      )}
      {row.late > 0 && (
        <p className="flex justify-between gap-4 text-destructive">
          <span>{labels.late}</span>
          <span className="tabular-nums">{formatHours(row.late)}</span>
        </p>
      )}
      <p className="flex justify-between gap-4 border-t border-border pt-1 font-medium">
        <span>{row.percentLabel}</span>
        {row.free > 0 && (
          <span className="font-normal text-muted-foreground">
            {labels.free} {formatHours(row.free)}
          </span>
        )}
      </p>
    </div>
  );
}
