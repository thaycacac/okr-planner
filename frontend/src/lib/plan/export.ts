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
