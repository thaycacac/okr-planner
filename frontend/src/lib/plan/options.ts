import type { OptionGroup, OptionOutcome, OverloadOption } from "@/lib/api/types";

export const OPTION_GROUPS: readonly OptionGroup[] = ["more_time", "less_scope", "defer"];

const WEEKDAY_PREFIX = "weekday_minutes:+";

export function weekdayOptionId(extraMinutes: number) {
  return `${WEEKDAY_PREFIX}${extraMinutes}`;
}

export function isWeekdayOption(id: string) {
  return id.startsWith(WEEKDAY_PREFIX);
}

/** The selected option that rules this one out, if any. */
export function blockedBy(option: OverloadOption, selected: ReadonlySet<string>): string | null {
  if (selected.has(option.id)) return null;
  return option.conflicts_with.find((id) => selected.has(id)) ?? null;
}

/** Selected ids in the order the options are listed, so evaluate requests are stable. */
export function orderedSelection(options: readonly OverloadOption[], selected: ReadonlySet<string>, weekdayId: string | null) {
  return options.flatMap((o) => {
    const id = o.kind === "weekday_minutes" && weekdayId ? weekdayId : o.id;
    return selected.has(o.id) ? [id] : [];
  });
}

/** Net hours the option frees up: extra supply plus removed demand. */
export function netGainMinutes(outcome: OptionOutcome) {
  return outcome.supply_delta_minutes - outcome.demand_delta_minutes;
}

export function spareMinutes(outcome: OptionOutcome) {
  return outcome.feasibility.supply_minutes - outcome.feasibility.demand_minutes;
}
