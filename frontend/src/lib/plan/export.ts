import type { ExportFormat, ExportSheet } from "@/lib/api/types";

import type { QuarterRef } from "./quarter";

export function exportFileName(ref: QuarterRef, format: ExportFormat, sheet: ExportSheet | null): string {
  const base = `okr-q${ref.number}-${ref.year}`;
  return sheet ? `${base}-${sheet}.${format}` : `${base}.${format}`;
}

/** Reads `filename="…"` (or RFC 5987 `filename*=`) from a Content-Disposition header. */
export function fileNameFromDisposition(header: string | null): string | null {
  if (!header) return null;
  const extended = /filename\*=(?:UTF-8'')?([^;]+)/i.exec(header);
  if (extended) {
    try {
      return decodeURIComponent(extended[1].trim().replace(/^"|"$/g, ""));
    } catch {
      return null;
    }
  }
  const plain = /filename="?([^";]+)"?/i.exec(header);
  return plain ? plain[1].trim() : null;
}

export type ExportMode = ExportFormat | "dondon";

export function dondonFileName(ref: QuarterRef): string {
  return `okr-q${ref.number}-${ref.year}-dondon.sql`;
}

export function defaultDondonTag(ref: QuarterRef, locale: string): string {
  return locale === "en" ? `OKR Q${ref.number}` : `OKR Quý ${ref.number}`;
}

// Mirrors the server check, which also rejects quotes, backslashes, semicolons and spaces.
const DONDON_EMAIL = /^[^@\s'"\\;`]{1,64}@[^@\s'"\\;`]{1,190}\.[^@\s'"\\;`]{2,63}$/;

export function isDondonEmail(value: string): boolean {
  return DONDON_EMAIL.test(value.trim());
}

/** Minutes east of UTC for the browser's current zone (Vietnam = 420). */
export function browserUtcOffset(now: Date = new Date()): number {
  return -now.getTimezoneOffset() || 0;
}

export function formatUtcOffset(minutes: number): string {
  const sign = minutes < 0 ? "-" : "+";
  const abs = Math.abs(minutes);
  return `UTC${sign}${String(Math.floor(abs / 60)).padStart(2, "0")}:${String(abs % 60).padStart(2, "0")}`;
}

/** Whole-hour zones from UTC-12 to UTC+14, plus the browser's own when it falls in between. */
export function utcOffsetOptions(current: number): number[] {
  const hours = Array.from({ length: 27 }, (_, i) => (i - 12) * 60);
  return hours.includes(current) ? hours : [...hours, current].sort((a, b) => a - b);
}
