import { describe, expect, it } from "vitest";

import type { QuarterDetail } from "@/lib/api/types";

import {
  buildContext,
  emptyKr,
  emptyObjective,
  fromQuarterDetail,
  type OkrDraft,
  parseNumber,
  precheck,
  toKeyResultBody,
  warnings,
} from "./okr-draft";

function draftWith(overrides: Partial<OkrDraft["objectives"][number]>[]): OkrDraft {
  return {
    objectives: overrides.map((o) => ({ ...emptyObjective(), ...o })),
    synced: false,
    savedAt: null,
  };
}

describe("parseNumber", () => {
  it("reads vi and en notation", () => {
    expect(parseNumber("800")).toBe(800);
    expect(parseNumber("2.000")).toBe(2000);
    expect(parseNumber("2,000")).toBe(2000);
    expect(parseNumber("3,2")).toBe(3.2);
    expect(parseNumber("3.2")).toBe(3.2);
    expect(parseNumber("1.234,5")).toBe(1234.5);
    expect(parseNumber("-5")).toBe(-5);
    expect(parseNumber("")).toBeNull();
    expect(parseNumber("abc")).toBeNull();
  });
});

describe("precheck", () => {
  it("accepts a complete OKR", () => {
    const draft = draftWith([
      {
        title: "Ra mắt phiên bản 2.0",
        keyResults: [{ ...emptyKr(), text: "Tăng WAU", baseline: "800", target: "2.000", unit: "WAU" }],
      },
    ]);
    expect(precheck(draft)).toEqual([]);
  });

  it("flags short text, missing metrics, bad numbers and duplicates", () => {
    const o = emptyObjective();
    const a = { ...emptyKr(), text: "Giảm tỉ lệ crash", baseline: "3,2", target: "" };
    const b = { ...emptyKr(), text: "giảm tỉ lệ CRASH!", kind: "binary" as const };
    const c = { ...emptyKr(), text: "NPS", baseline: "x", target: "50" };
    const draft = draftWith([{ ...o, title: "App", keyResults: [a, b, c] }]);
    const codes = precheck(draft).map((i) => [i.code, i.krKey ?? null, i.field ?? null]);
    expect(codes).toEqual([
      ["objective_too_short", null, "title"],
      ["missing_target", a.key, "target"],
      ["duplicate_kr", b.key, "text"],
      ["kr_too_short", c.key, "text"],
      ["invalid_number", c.key, "baseline"],
    ]);
  });

  it("requires key results and at least one objective", () => {
    expect(precheck({ objectives: [], synced: false, savedAt: null }).map((i) => i.code)).toEqual([
      "no_objectives",
    ]);
    const draft = draftWith([{ title: "Đạt JLPT N4", keyResults: [] }]);
    expect(precheck(draft).map((i) => i.code)).toEqual(["no_key_results"]);
  });

  it("warns softly above five objectives or five KRs", () => {
    const many = draftWith(Array.from({ length: 6 }, () => ({})));
    expect(warnings(many)).toEqual(["many_objectives"]);
  });
});

describe("toKeyResultBody", () => {
  it("clears fields the kind does not use but keeps the draft text", () => {
    const kr = { ...emptyKr(), text: " Ship v2 ", kind: "milestone" as const, baseline: "1", dueDate: "2026-11-30" };
    expect(toKeyResultBody(kr, 2)).toEqual({
      text: "Ship v2",
      kind: "milestone",
      baseline: null,
      target: null,
      unit: null,
      due_date: "2026-11-30",
      note: null,
      position: 2,
    });
    expect(kr.baseline).toBe("1");
  });
});

describe("fromQuarterDetail", () => {
  it("orders by position and keeps local context by server id", () => {
    const detail = {
      objectives: [
        { id: 7, quarter_id: 1, title: "B", priority: "low", position: 1, key_results: [] },
        {
          id: 3,
          quarter_id: 1,
          title: "A",
          priority: "high",
          position: 0,
          key_results: [
            { id: 9, objective_id: 3, text: "KR", kind: "numeric", baseline: 1, target: 2.5, unit: "%", due_date: null, note: null, position: 0, tasks: [] },
          ],
        },
      ],
    } as unknown as QuarterDetail;
    const previous = draftWith([{ serverId: 3, domain: "SaaS", constraints: "1 người" }]);
    const draft = fromQuarterDetail(detail, previous);
    expect(draft.synced).toBe(true);
    expect(draft.objectives.map((o) => [o.serverId, o.title, o.domain])).toEqual([
      [3, "A", "SaaS"],
      [7, "B", ""],
    ]);
    expect(draft.objectives[0].keyResults[0]).toMatchObject({ serverId: 9, baseline: "1", target: "2.5", unit: "%" });
  });
});

describe("buildContext", () => {
  it("folds objective context into one text and skips empty ones", () => {
    const draft = draftWith([
      { title: "Ra mắt 2.0", domain: "Phần mềm", constraints: "Một mình" },
      { title: "JLPT" },
    ]);
    expect(buildContext(draft, { domain: "Lĩnh vực", constraints: "Ràng buộc" })).toBe(
      "O1 (Ra mắt 2.0): Lĩnh vực: Phần mềm; Ràng buộc: Một mình",
    );
    expect(buildContext(draftWith([{ title: "X" }]), { domain: "d", constraints: "c" })).toBeNull();
  });
});
