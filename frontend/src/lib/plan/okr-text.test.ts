import { describe, expect, it } from "vitest";

import { fromParsed, parseOkrText } from "./okr-text";

const Q4 = { year: 2026, start: "2026-10-01", end: "2026-12-31" };

const SAMPLE = `O1: Chinh phục chứng chỉ tiếng Anh B2

KR1: Đăng ký khóa học vào khoảng 20/10
KR2: Học mỗi ngày từ 20/10 đến 8/12, không bỏ buổi nào
KR3: Làm ít nhất 6 đề thi thử, 3 đề cuối đạt mức B2 trở lên
KR4: Thi đạt B2 vào khoảng 8/12`;

describe("parseOkrText", () => {
  it("reads one objective with its key results", () => {
    const { objectives, truncated } = parseOkrText(SAMPLE);
    expect(truncated).toBe(false);
    expect(objectives).toHaveLength(1);
    expect(objectives[0].title).toBe("Chinh phục chứng chỉ tiếng Anh B2");
    expect(objectives[0].keyResults.map((k) => k.text)).toEqual([
      "Đăng ký khóa học vào khoảng 20/10",
      "Học mỗi ngày từ 20/10 đến 8/12, không bỏ buổi nào",
      "Làm ít nhất 6 đề thi thử, 3 đề cuối đạt mức B2 trở lên",
      "Thi đạt B2 vào khoảng 8/12",
    ]);
    expect(objectives[0].keyResults.every((k) => k.kind === "other")).toBe(true);
  });

  it("splits several objectives and accepts English labels and bullets", () => {
    const { objectives } = parseOkrText(
      "Objective 1: Ship v2\n- Release beta\n- Fix top bugs\nO2) Grow users\nKey result 1 - Reach 1000 signups",
    );
    expect(objectives.map((o) => o.title)).toEqual(["Ship v2", "Grow users"]);
    expect(objectives[0].keyResults.map((k) => k.text)).toEqual(["Release beta", "Fix top bugs"]);
    expect(objectives[1].keyResults.map((k) => k.text)).toEqual(["Reach 1000 signups"]);
  });

  it("joins wrapped lines and treats an unlabelled first line as the objective", () => {
    const { objectives } = parseOkrText("Learn Spanish\nKR1: Finish the course\n and pass the test");
    expect(objectives[0].title).toBe("Learn Spanish");
    expect(objectives[0].keyResults[0].text).toBe("Finish the course and pass the test");
  });

  it("returns nothing for blank input and reports truncation", () => {
    expect(parseOkrText("  \n ").objectives).toHaveLength(0);
    const many = ["O1: A", ...Array.from({ length: 12 }, (_, i) => `KR${i + 1}: item ${i}`)].join("\n");
    const result = parseOkrText(many);
    expect(result.objectives[0].keyResults).toHaveLength(10);
    expect(result.truncated).toBe(true);
  });
});

describe("detectKr", () => {
  it("fills kind, due date and targets from the wording", () => {
    const krs = parseOkrText(SAMPLE, Q4).objectives[0].keyResults;
    expect(krs[0]).toMatchObject({ kind: "milestone", dueDate: "2026-10-20" });
    expect(krs[1].kind).toBe("other");
    expect(krs[2]).toMatchObject({ kind: "numeric", baseline: "0", target: "6", unit: "đề thi thử" });
    expect(krs[3]).toMatchObject({ kind: "milestone", dueDate: "2026-12-08" });
  });

  it("ignores dates outside the quarter", () => {
    const kr = parseOkrText("O1: A\nKR1: Ship on 5/2", Q4).objectives[0].keyResults[0];
    expect(kr.kind).toBe("other");
  });
});

describe("detectKr amounts", () => {
  it("reads 'đạt N <unit>' without swallowing the period", () => {
    const kr = parseOkrText(
      "O1: Web\nKR1: KungfuTech đạt 1.000 lượt nhấp từ Google trong 28 ngày (theo Google Search Console)",
      Q4,
    ).objectives[0].keyResults[0];
    expect(kr).toMatchObject({ kind: "numeric", baseline: "0", target: "1000", unit: "lượt nhấp" });
  });

  it("does not treat a level or a date after 'đạt' as an amount", () => {
    const krs = parseOkrText("O1: A\nKR1: Thi đạt B2\nKR2: Hoàn thành đạt 8/12", Q4).objectives[0].keyResults;
    expect(krs.map((k) => k.kind)).toEqual(["other", "milestone"]);
  });
});

describe("fromParsed", () => {
  it("maps API objectives to draft cards", () => {
    const [o] = fromParsed({
      objectives: [
        {
          title: "Grow",
          priority: "high",
          key_results: [
            { text: "1000 clicks", kind: "numeric", baseline: 0, target: 1000, unit: "clicks", due_date: null, note: null },
            { text: "Ship", kind: "milestone", baseline: null, target: null, unit: null, due_date: "2026-10-20", note: null },
          ],
        },
      ],
    });
    expect(o).toMatchObject({ title: "Grow", priority: "high" });
    expect(o.keyResults[0]).toMatchObject({ kind: "numeric", baseline: "0", target: "1000", unit: "clicks" });
    expect(o.keyResults[1]).toMatchObject({ kind: "milestone", dueDate: "2026-10-20" });
  });
});
