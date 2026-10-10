import { describe, expect, it } from "vitest";

import { criteriaItems } from "./task-sheet";

describe("criteriaItems", () => {
  it("splits bullet and numbered lines", () => {
    expect(criteriaItems("- Có bản nháp\n* Được review\n1. Đã merge")).toEqual([
      "Có bản nháp",
      "Được review",
      "Đã merge",
    ]);
  });

  it("splits sentences joined by semicolons and drops blanks", () => {
    expect(criteriaItems("Demo chạy được; có test\n\n")).toEqual(["Demo chạy được", "có test"]);
  });

  it("keeps a single sentence as one item", () => {
    expect(criteriaItems("Landing page live on production")).toEqual(["Landing page live on production"]);
  });
});
