import { describe, expect, it } from "vitest";

import { exportFileName, fileNameFromDisposition } from "./export";

describe("export file names", () => {
  it("names workbooks by quarter and CSV files by sheet", () => {
    expect(exportFileName({ year: 2026, number: 4 }, "xlsx", null)).toBe("okr-q4-2026.xlsx");
    expect(exportFileName({ year: 2026, number: 4 }, "csv", "weeks")).toBe("okr-q4-2026-weeks.csv");
  });

  it("reads plain and RFC 5987 filenames from Content-Disposition", () => {
    expect(fileNameFromDisposition('attachment; filename="okr-q4-2026.xlsx"')).toBe("okr-q4-2026.xlsx");
    expect(fileNameFromDisposition("attachment; filename*=UTF-8''okr%20q4.csv")).toBe("okr q4.csv");
    expect(fileNameFromDisposition("attachment")).toBeNull();
    expect(fileNameFromDisposition(null)).toBeNull();
  });
});
