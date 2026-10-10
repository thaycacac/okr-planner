import type {
  KeyResultCreate,
  KeyResultKind,
  ObjectivePriority,
  QuarterDetail,
} from "@/lib/api/types";

// Mirrors the server pre-check (backend planner_llm/precheck.py) so the user sees the same errors
// before anything is saved or sent to the model.
export const MIN_TEXT_LENGTH = 5;
export const MAX_OBJECTIVES = 10;
export const MAX_KEY_RESULTS = 10;
export const SOFT_MAX_OBJECTIVES = 5;
export const SOFT_MAX_KEY_RESULTS = 5;
export const MAX_CONTEXT_LENGTH = 4000;

export type KrDraft = {
  key: string;
  serverId?: number;
  text: string;
  kind: KeyResultKind;
  // Kept as typed text so switching kind or typing "3,2" never loses input.
  baseline: string;
  target: string;
  unit: string;
  dueDate: string;
  note: string;
  /** Dropped from the plan on the server; editing keeps it out until it is restored. */
  inactive?: boolean;
};

export type ObjectiveDraft = {
  key: string;
  serverId?: number;
  title: string;
  priority: ObjectivePriority;
  domain: string;
  constraints: string;
  keyResults: KrDraft[];
  /** Paused on the server; editing keeps it out of the plan until it is restored. */
  inactive?: boolean;
};

export type OkrDraft = {
  objectives: ObjectiveDraft[];
  /** True once the draft matches what the server holds. */
  synced: boolean;
  savedAt: number | null;
};

let counter = 0;
export function newKey(prefix: string) {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter}`;
}

export function emptyKr(): KrDraft {
  return {
    key: newKey("kr"),
    text: "",
    kind: "numeric",
    baseline: "",
    target: "",
    unit: "",
    dueDate: "",
    note: "",
  };
}

export function emptyObjective(): ObjectiveDraft {
  return {
    key: newKey("o"),
    title: "",
    priority: "medium",
    domain: "",
    constraints: "",
    keyResults: [emptyKr()],
  };
}

export function emptyDraft(): OkrDraft {
  return { objectives: [emptyObjective()], synced: false, savedAt: null };
}

// --- numbers --------------------------------------------------------------------------------

/**
 * Accepts both vi and en notation: "2.000" / "2,000" are thousands (groups of exactly three
 * digits), "3,2" / "3.2" are decimals, and with both marks the last one is the decimal mark.
 */
export function parseNumber(text: string): number | null {
  const cleaned = text.trim().replace(/\s/g, "");
  if (!cleaned) return null;
  let normalized: string;
  if (/^-?\d{1,3}([.,]\d{3})+$/.test(cleaned) && new Set(cleaned.replace(/[^.,]/g, "")).size === 1) {
    normalized = cleaned.replace(/[.,]/g, "");
  } else if (cleaned.includes(".") && cleaned.includes(",")) {
    const decimal = cleaned.lastIndexOf(".") > cleaned.lastIndexOf(",") ? "." : ",";
    const group = decimal === "." ? "," : ".";
    normalized = cleaned.split(group).join("").replace(decimal, ".");
  } else {
    normalized = cleaned.replace(",", ".");
  }
  const value = Number(normalized);
  return Number.isFinite(value) ? value : null;
}

export function formatNumber(value: number | null | undefined): string {
  return value === null || value === undefined ? "" : String(value);
}

// --- pre-check ------------------------------------------------------------------------------

export type IssueCode =
  | "no_objectives"
  | "too_many_objectives"
  | "objective_too_short"
  | "no_key_results"
  | "too_many_key_results"
  | "kr_too_short"
  | "duplicate_kr"
  | "missing_baseline"
  | "missing_target"
  | "invalid_number"
  | "context_too_long";

export type IssueField = "title" | "text" | "baseline" | "target";

export type DraftIssue = {
  code: IssueCode;
  objectiveKey?: string;
  krKey?: string;
  field?: IssueField;
};

export type DraftWarning = "many_objectives" | "many_key_results";

function normalizeText(text: string) {
  return text
    .toLocaleLowerCase()
    .replace(/[^\p{L}\p{N}_\s]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function precheck(draft: OkrDraft, context = ""): DraftIssue[] {
  const issues: DraftIssue[] = [];
  const { objectives } = draft;
  if (objectives.length === 0) issues.push({ code: "no_objectives" });
  if (objectives.length > MAX_OBJECTIVES) issues.push({ code: "too_many_objectives" });
  if (context.length > MAX_CONTEXT_LENGTH) issues.push({ code: "context_too_long" });

  const seen = new Set<string>();
  for (const objective of objectives) {
    const objectiveKey = objective.key;
    if (objective.title.trim().length < MIN_TEXT_LENGTH) {
      issues.push({ code: "objective_too_short", objectiveKey, field: "title" });
    }
    if (objective.keyResults.length === 0) issues.push({ code: "no_key_results", objectiveKey });
    if (objective.keyResults.length > MAX_KEY_RESULTS) {
      issues.push({ code: "too_many_key_results", objectiveKey });
    }
    for (const kr of objective.keyResults) {
      const krKey = kr.key;
      const text = kr.text.trim();
      if (text.length < MIN_TEXT_LENGTH) {
        issues.push({ code: "kr_too_short", objectiveKey, krKey, field: "text" });
      } else {
        const normalized = normalizeText(text);
        if (seen.has(normalized)) {
          issues.push({ code: "duplicate_kr", objectiveKey, krKey, field: "text" });
        }
        seen.add(normalized);
      }
      if (kr.kind !== "numeric") continue;
      for (const field of ["baseline", "target"] as const) {
        const raw = kr[field];
        if (!raw.trim()) {
          issues.push({
            code: field === "baseline" ? "missing_baseline" : "missing_target",
            objectiveKey,
            krKey,
            field,
          });
        } else if (parseNumber(raw) === null) {
          issues.push({ code: "invalid_number", objectiveKey, krKey, field });
        }
      }
    }
  }
  return issues;
}

export function warnings(draft: OkrDraft): DraftWarning[] {
  const result: DraftWarning[] = [];
  if (draft.objectives.length > SOFT_MAX_OBJECTIVES) result.push("many_objectives");
  if (draft.objectives.some((o) => o.keyResults.length > SOFT_MAX_KEY_RESULTS)) {
    result.push("many_key_results");
  }
  return result;
}

// --- API mapping ----------------------------------------------------------------------------

/** Full set of KR fields, with the ones the kind does not use cleared. */
export function toKeyResultBody(kr: KrDraft, position: number): Required<KeyResultCreate> {
  const numeric = kr.kind === "numeric";
  return {
    text: kr.text.trim(),
    kind: kr.kind,
    baseline: numeric ? parseNumber(kr.baseline) : null,
    target: numeric ? parseNumber(kr.target) : null,
    unit: numeric && kr.unit.trim() ? kr.unit.trim() : null,
    due_date: kr.kind === "milestone" && kr.dueDate ? kr.dueDate : null,
    note: kr.kind === "other" && kr.note.trim() ? kr.note.trim() : null,
    position,
  };
}

/** Server tree → draft; context fields live only in the browser, so they are carried over. */
export function fromQuarterDetail(detail: QuarterDetail, previous?: OkrDraft | null): OkrDraft {
  const local = new Map(
    (previous?.objectives ?? []).filter((o) => o.serverId).map((o) => [o.serverId, o]),
  );
  const objectives = [...detail.objectives]
    .sort((a, b) => a.position - b.position)
    .map<ObjectiveDraft>((o) => ({
      key: newKey("o"),
      serverId: o.id,
      title: o.title,
      priority: o.priority,
      domain: local.get(o.id)?.domain ?? "",
      constraints: local.get(o.id)?.constraints ?? "",
      ...(o.active === false && { inactive: true }),
      keyResults: [...o.key_results]
        .sort((a, b) => a.position - b.position)
        .map<KrDraft>((kr) => ({
          key: newKey("kr"),
          serverId: kr.id,
          text: kr.text,
          kind: kr.kind,
          baseline: formatNumber(kr.baseline),
          target: formatNumber(kr.target),
          unit: kr.unit ?? "",
          dueDate: kr.due_date ?? "",
          note: kr.note ?? "",
          ...(kr.active === false && { inactive: true }),
        })),
    }));
  return { objectives, synced: true, savedAt: previous?.savedAt ?? null };
}

export type ContextLabels = { domain: string; constraints: string };

/** Objective-level context folded into the plan's single free-text context. */
export function buildContext(draft: OkrDraft, labels: ContextLabels): string | null {
  const lines = draft.objectives.flatMap((o, i) => {
    const parts = [
      o.domain.trim() && `${labels.domain}: ${o.domain.trim()}`,
      o.constraints.trim() && `${labels.constraints}: ${o.constraints.trim()}`,
    ].filter(Boolean);
    return parts.length ? [`O${i + 1} (${o.title.trim()}): ${parts.join("; ")}`] : [];
  });
  return lines.length ? lines.join("\n") : null;
}

export function countKeyResults(draft: OkrDraft) {
  return draft.objectives.reduce((sum, o) => sum + o.keyResults.length, 0);
}

// --- local draft storage --------------------------------------------------------------------

const STORAGE_PREFIX = "okr-planner.draft.";

function storage(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.localStorage;
  } catch {
    return null;
  }
}

export function loadDraft(slug: string): OkrDraft | null {
  const raw = storage()?.getItem(STORAGE_PREFIX + slug);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as OkrDraft;
    return Array.isArray(parsed.objectives) ? parsed : null;
  } catch {
    return null;
  }
}

export function saveDraft(slug: string, draft: OkrDraft): boolean {
  const store = storage();
  if (!store) return false;
  try {
    store.setItem(STORAGE_PREFIX + slug, JSON.stringify(draft));
    return true;
  } catch {
    return false;
  }
}
