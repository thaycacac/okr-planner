import type { OkrParseResult } from "@/lib/api/types";

import {
  emptyKr,
  emptyObjective,
  type KrDraft,
  MAX_KEY_RESULTS,
  MAX_OBJECTIVES,
  type ObjectiveDraft,
  parseNumber,
} from "./okr-draft";

// Free-text OKRs such as
//   O1: Pass the B2 English exam
//   KR1: Enrol in a course around 20/10
// Objective lines start with O / Objective / Mục tiêu, key results with KR / Key result / Kết quả;
// a number and one of ":", ".", ")", "-" may follow. A bullet under an objective is a key result too.
const OBJECTIVE = /^(?:objectives?|mục\s*tiêu|obj|o)\s*\d*\s*[:.)\-–—]\s*(.+)$/iu;
const KEY_RESULT = /^(?:key\s*results?|kết\s*quả(?:\s*then\s*chốt)?|kr)\s*\d*\s*[:.)\-–—]\s*(.+)$/iu;
const BULLET = /^(?:[-*•–]|\d+[.)])\s+(.+)$/u;

/** Quarter the text is planned for: dates without a year resolve to it, and a due date must fall inside. */
export type OkrTextContext = { year: number; start: string; end: string };

const DATE = /(\d{1,2})\/(\d{1,2})(?:\/(\d{4}))?/g;
const AMOUNT =
  /(?:ít\s+nhất|tối\s+thiểu|đạt|at\s+least|minimum(?:\s+of)?|reach|hit)\s+(\d[\d.,]*)(?![\d/])\s*(%|\p{L}+(?:\s\p{L}+){0,2})?/iu;
// Words that end a unit: "1.000 lượt nhấp từ Google" counts "lượt nhấp", not "lượt nhấp từ".
const UNIT_STOP = new Set(["từ", "trong", "mỗi", "vào", "trên", "ở", "tại", "và", "in", "from", "per", "by", "within", "on"]);

function unitOf(raw: string | undefined): string {
  if (!raw) return "";
  if (raw === "%") return raw;
  const words: string[] = [];
  for (const word of raw.split(/\s+/)) {
    if (UNIT_STOP.has(word.toLowerCase())) break;
    words.push(word);
  }
  return words.join(" ");
}

function isoDates(text: string, year: number): string[] {
  const found: string[] = [];
  for (const m of text.matchAll(DATE)) {
    const day = Number(m[1]);
    const month = Number(m[2]);
    if (month < 1 || month > 12 || day < 1 || day > 31) continue;
    const y = m[3] ? Number(m[3]) : year;
    found.push(`${y}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`);
  }
  return found;
}

/**
 * Guesses how a key result is measured from its wording: "at least 6 mock tests" is numeric,
 * a single date ("around 20/10") is a milestone with that due date; anything else stays free text.
 */
export function detectKr(text: string, ctx?: OkrTextContext): Partial<KrDraft> {
  if (!ctx) return {};
  const amount = AMOUNT.exec(text);
  const target = amount ? parseNumber(amount[1]) : null;
  if (amount && target !== null) {
    return { kind: "numeric", baseline: "0", target: String(target), unit: unitOf(amount[2]) };
  }
  const dates = isoDates(text, ctx.year).filter((d) => d >= ctx.start && d <= ctx.end);
  // "from 20/10 to 8/12" describes a period, not a single deadline.
  const isRange = dates.length > 1 || /\b(?:từ|from)\b.+\b(?:đến|tới|to|until)\b/iu.test(text);
  if (dates.length > 0 && !isRange) return { kind: "milestone", dueDate: dates[0] };
  return {};
}

export type ParsedOkrText = {
  objectives: ObjectiveDraft[];
  /** Key results or objectives beyond the limits, which were left out. */
  truncated: boolean;
};

export function parseOkrText(text: string, ctx?: OkrTextContext): ParsedOkrText {
  const objectives: ObjectiveDraft[] = [];
  let truncated = false;
  // Where a plain line gets appended: the last key result, else the objective title.
  let last: "title" | "kr" | null = null;

  const current = () => objectives[objectives.length - 1];
  const startObjective = (title: string) => {
    if (objectives.length >= MAX_OBJECTIVES) {
      truncated = true;
      return false;
    }
    objectives.push({ ...emptyObjective(), title, keyResults: [] });
    last = "title";
    return true;
  };
  const addKr = (kr: string) => {
    if (objectives.length === 0 && !startObjective("")) return;
    const objective = current();
    if (objective.keyResults.length >= MAX_KEY_RESULTS) {
      truncated = true;
      return;
    }
    objective.keyResults.push({ ...emptyKr(), kind: "other", text: kr, ...detectKr(kr, ctx) });
    last = "kr";
  };

  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line) continue;
    const kr = KEY_RESULT.exec(line);
    const objective = kr ? null : OBJECTIVE.exec(line);
    if (kr) addKr(kr[1].trim());
    else if (objective) startObjective(objective[1].trim());
    else if (objectives.length > 0 && BULLET.test(line)) addKr(BULLET.exec(line)![1].trim());
    else if (objectives.length === 0) startObjective(line);
    else if (last === "kr") {
      const krs = current().keyResults;
      const joined = krs[krs.length - 1];
      joined.text += ` ${line}`;
      Object.assign(joined, detectKr(joined.text, ctx));
    } else if (last === "title") current().title += ` ${line}`;
  }

  for (const objective of objectives) {
    if (objective.keyResults.length === 0) objective.keyResults.push(emptyKr());
  }
  return { objectives, truncated };
}

/** Objectives returned by ``POST /okr/parse`` as editable draft cards. */
export function fromParsed(result: OkrParseResult): ObjectiveDraft[] {
  return result.objectives.map((o) => ({
    ...emptyObjective(),
    title: o.title,
    priority: o.priority,
    keyResults: (o.key_results.length ? o.key_results : [null]).map((kr) =>
      kr
        ? {
            ...emptyKr(),
            text: kr.text,
            kind: kr.kind,
            baseline: kr.baseline == null ? "" : String(kr.baseline),
            target: kr.target == null ? "" : String(kr.target),
            unit: kr.unit ?? "",
            dueDate: kr.due_date ?? "",
            note: kr.note ?? "",
          }
        : emptyKr(),
    ),
  }));
}
