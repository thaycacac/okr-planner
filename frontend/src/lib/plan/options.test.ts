import { describe, expect, it } from "vitest";

import type { OptionOutcome, OverloadOption } from "@/lib/api/types";

import { blockedBy, isWeekdayOption, netGainMinutes, orderedSelection, spareMinutes, weekdayOptionId } from "./options";

function option(id: string, kind: string, conflicts: string[] = []): OverloadOption {
  return { id, kind, conflicts_with: conflicts } as unknown as OverloadOption;
}

const options = [
  option("weekday_minutes:+60", "weekday_minutes"),
  option("work_saturday", "work_saturday"),
  option("drop_kr:10", "drop_kr", ["defer_kr:10"]),
  option("defer_kr:10", "defer_kr", ["drop_kr:10"]),
];

describe("overload options", () => {
  it("builds and recognises weekday option ids", () => {
    expect(weekdayOptionId(90)).toBe("weekday_minutes:+90");
    expect(isWeekdayOption("weekday_minutes:+90")).toBe(true);
    expect(isWeekdayOption("work_saturday")).toBe(false);
  });

  it("reports which selected option rules another out", () => {
    const selected = new Set(["drop_kr:10"]);
    expect(blockedBy(options[3], selected)).toBe("drop_kr:10");
    expect(blockedBy(options[2], selected)).toBeNull();
    expect(blockedBy(options[1], selected)).toBeNull();
  });

  it("keeps list order and swaps in the chosen weekday amount", () => {
    const selected = new Set(["defer_kr:10", "weekday_minutes:+60", "work_saturday"]);
    expect(orderedSelection(options, selected, "weekday_minutes:+120")).toEqual([
      "weekday_minutes:+120",
      "work_saturday",
      "defer_kr:10",
    ]);
    expect(orderedSelection(options, selected, null)[0]).toBe("weekday_minutes:+60");
  });

  it("counts both extra supply and removed demand as gain", () => {
    const outcome = {
      supply_delta_minutes: 600,
      demand_delta_minutes: -300,
      feasibility: { supply_minutes: 3000, demand_minutes: 2700 },
    } as unknown as OptionOutcome;
    expect(netGainMinutes(outcome)).toBe(900);
    expect(spareMinutes(outcome)).toBe(300);
  });
});
