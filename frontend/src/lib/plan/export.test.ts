import { describe, expect, it } from "vitest";

import {
  browserUtcOffset,
  defaultDondonTag,
  dondonFileName,
  exportFileName,
  fileNameFromDisposition,
  formatUtcOffset,
  isDondonEmail,
  utcOffsetOptions,
} from "./export";

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

describe("dondon export helpers", () => {
  it("names the file and the default tag per language", () => {
    expect(dondonFileName({ year: 2026, number: 4 })).toBe("okr-q4-2026-dondon.sql");
    expect(defaultDondonTag({ year: 2026, number: 4 }, "vi")).toBe("OKR Quý 4");
    expect(defaultDondonTag({ year: 2026, number: 4 }, "en")).toBe("OKR Q4");
  });

  it("accepts plain emails and rejects ones that could break out of a SQL string", () => {
    expect(isDondonEmail(" me@example.com ")).toBe(true);
    expect(isDondonEmail("a+b@mail.example.co")).toBe(true);
    for (const bad of ["me", "me@x", "a'b@example.com", "a@b.com; DROP", 'a"b@example.com', "a b@example.com"]) {
      expect(isDondonEmail(bad)).toBe(false);
    }
  });

  it("reads and lists UTC offsets", () => {
    expect(browserUtcOffset(new Date("2026-10-10T00:00:00Z"))).toBeTypeOf("number");
    expect(formatUtcOffset(420)).toBe("UTC+07:00");
    expect(formatUtcOffset(-210)).toBe("UTC-03:30");
    expect(utcOffsetOptions(420)).toHaveLength(27);
    expect(utcOffsetOptions(330)).toContain(330);
    expect(utcOffsetOptions(330).indexOf(330)).toBeGreaterThan(utcOffsetOptions(330).indexOf(300));
  });
});
