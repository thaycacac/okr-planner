import { describe, expect, it } from "vitest";

import { parseOkrText } from "./okr-text";

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
