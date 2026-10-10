import { describe, expect, it } from "vitest";

import type { QuarterDetail } from "@/lib/api/types";

import { emptyKr, emptyObjective, type OkrDraft } from "./okr-draft";
import { planSync } from "./sync";

const serverKr = {
  id: 11,
  objective_id: 1,
  text: "Tăng WAU",
  kind: "numeric" as const,
  baseline: 800,
  target: 2000,
  unit: "WAU",
  due_date: null,
  note: null,
  position: 0,
  tasks: [],
};

const detail = {
  id: 1,
  objectives: [
    { id: 1, quarter_id: 1, title: "Ra mắt 2.0", priority: "high", position: 0, key_results: [serverKr, { ...serverKr, id: 12, text: "Crash", position: 1 }] },
    { id: 2, quarter_id: 1, title: "JLPT N4", priority: "medium", position: 1, key_results: [] },
  ],
} as unknown as QuarterDetail;

function kr(overrides: Partial<ReturnType<typeof emptyKr>>) {
  return { ...emptyKr(), ...overrides };
}

describe("planSync", () => {
  it("writes nothing when the draft matches the server", () => {
    const draft: OkrDraft = {
      synced: false,
      savedAt: null,
      objectives: [
        {
          ...emptyObjective(),
          serverId: 1,
          title: "Ra mắt 2.0",
          priority: "high",
          keyResults: [
            kr({ serverId: 11, text: "Tăng WAU", baseline: "800", target: "2.000", unit: "WAU" }),
            kr({ serverId: 12, text: "Crash", baseline: "800", target: "2000", unit: "WAU" }),
          ],
        },
        { ...emptyObjective(), serverId: 2, title: "JLPT N4", keyResults: [] },
      ],
    };
    expect(planSync(draft, detail)).toEqual([]);
  });

  it("keeps ids, deletes what was removed and creates what is new, deletes first", () => {
    const draft: OkrDraft = {
      synced: false,
      savedAt: null,
      objectives: [
        {
          ...emptyObjective(),
          serverId: 1,
          title: "Ra mắt 2.0",
          priority: "medium",
          keyResults: [
            kr({ serverId: 11, text: "Tăng WAU", baseline: "800", target: "2500", unit: "WAU" }),
            kr({ text: "Phát hành iOS", kind: "binary" }),
          ],
        },
        { ...emptyObjective(), title: "Thương hiệu cá nhân", keyResults: [kr({ text: "Viết 6 bài blog", kind: "other" })] },
      ],
    };
    const ops = planSync(draft, detail);
    expect(ops.map((op) => op.type)).toEqual([
      "deleteKr",
      "deleteObjective",
      "updateObjective",
      "updateKr",
      "createKr",
      "createObjective",
    ]);
    expect(ops[0]).toEqual({ type: "deleteKr", id: 12 });
    expect(ops[1]).toEqual({ type: "deleteObjective", id: 2 });
    expect(ops[3]).toMatchObject({ type: "updateKr", id: 11, body: { target: 2500 } });
    expect(ops[4]).toMatchObject({ type: "createKr", objectiveId: 1, body: { text: "Phát hành iOS", position: 1 } });
    expect(ops[5]).toMatchObject({
      type: "createObjective",
      body: { title: "Thương hiệu cá nhân", position: 1, key_results: [{ text: "Viết 6 bài blog", kind: "other" }] },
    });
  });

  it("recreates an objective whose server row disappeared", () => {
    const draft: OkrDraft = {
      synced: false,
      savedAt: null,
      objectives: [{ ...emptyObjective(), serverId: 99, title: "Mất rồi", keyResults: [] }],
    };
    const types = planSync(draft, detail).map((op) => op.type);
    expect(types).toEqual(["deleteObjective", "deleteObjective", "createObjective"]);
  });
});
