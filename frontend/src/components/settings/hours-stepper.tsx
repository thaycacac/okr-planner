"use client";

import { useFormatter } from "next-intl";
import { useState } from "react";
import { MinusIcon, PlusIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { clampHours, MAX_HOURS, MIN_HOURS, parseHours, STEP_HOURS } from "./calendar-model";

type HoursStepperProps = {
  value: number;
  onChange: (hours: number) => void;
  labels: { input: string; decrease: string; increase: string };
};

export function HoursStepper({ value, onChange, labels }: HoursStepperProps) {
  const format = useFormatter();
  return (
    <div className="flex items-center gap-1.5">
      <Button
        type="button"
        variant="outline"
        size="icon"
        aria-label={labels.decrease}
        disabled={value <= MIN_HOURS}
        onClick={() => onChange(clampHours(value - STEP_HOURS))}
      >
        <MinusIcon aria-hidden />
      </Button>
      <HoursInput
        key={value}
        initialText={format.number(value, { maximumFractionDigits: 1 })}
        label={labels.input}
        onCommit={(hours) => onChange(hours ?? value)}
      />
      <Button
        type="button"
        variant="outline"
        size="icon"
        aria-label={labels.increase}
        disabled={value >= MAX_HOURS}
        onClick={() => onChange(clampHours(value + STEP_HOURS))}
      >
        <PlusIcon aria-hidden />
      </Button>
    </div>
  );
}

function HoursInput({
  initialText,
  label,
  onCommit,
}: {
  initialText: string;
  label: string;
  onCommit: (hours: number | null) => void;
}) {
  const [text, setText] = useState(initialText);
  return (
    <Input
      inputMode="decimal"
      aria-label={label}
      className="w-16 text-center tabular-nums"
      value={text}
      onChange={(e) => setText(e.target.value)}
      onBlur={() => onCommit(parseHours(text))}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          onCommit(parseHours(text));
        }
      }}
    />
  );
}
