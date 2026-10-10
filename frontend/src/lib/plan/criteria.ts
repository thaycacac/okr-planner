/** Splits the free-text done criteria the planner writes into checklist lines. */
export function criteriaLines(text: string): string[] {
  return text
    .split(/\r?\n|;\s+/)
    .map((line) => line.replace(/^\s*(?:[-*•]|\d+[.)])\s*/, "").trim())
    .filter(Boolean);
}
