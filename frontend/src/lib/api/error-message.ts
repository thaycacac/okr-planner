import { errorDetail } from "./types";

/** Backend error codes with a translated message under the `apiErrors` namespace. */
export const API_ERROR_CODES = [
  "not_found",
  "not_authenticated",
  "rate_limited",
  "auth_not_configured",
  "invalid_password",
  "cross_site_request",
  "field_required",
  "quarter_exists",
  "no_previous_quarter",
  "schedule_not_found",
  "holiday_exists",
  "holiday_data_missing",
  "plan_in_progress",
  "plan_not_running",
  "plan_not_awaiting_answers",
  "plan_already_answered",
  "unknown_question",
  "okr_changed",
  "plan_not_resumable",
  "dependency_cycle",
  "dependency_on_itself",
  "unknown_dependency",
  "key_result_not_in_quarter",
  "task_done",
  "task_not_scheduled",
  "pin_outside_quarter",
  "pin_non_working_day",
  "pin_exceeds_quarter",
  "pin_duplicate_date",
  "pin_minutes_mismatch",
  "schedule_input_error",
  "unknown_option",
  "option_not_applicable",
  "options_conflict",
  "no_options",
  "openai_not_configured",
] as const;

export type ApiErrorCode = (typeof API_ERROR_CODES)[number];

const isApiErrorCode = (code: string): code is ApiErrorCode => (API_ERROR_CODES as readonly string[]).includes(code);

export type KnownApiError = { code: ApiErrorCode; message: string };

function codeAndMessage(error: unknown): { code: string; message: string } | null {
  const detail = errorDetail(error);
  if (detail) return { code: detail.code, message: detail.message };
  if (error && typeof error === "object" && "code" in error && typeof error.code === "string") {
    const message = "message" in error && typeof error.message === "string" ? error.message : "";
    return { code: error.code, message };
  }
  return null;
}

/**
 * The translatable error behind an openapi-fetch error body, its `detail`, or a thrown error
 * carrying a `code`. The server's `message` is English prose meant for logs, never for display.
 */
export function knownApiError(error: unknown): KnownApiError | null {
  const found = codeAndMessage(error);
  return found && isApiErrorCode(found.code) ? { code: found.code, message: found.message } : null;
}

/** The task chain from a `dependency_cycle` message, e.g. "12 → 15 → 12". */
export function dependencyChain(message: string) {
  return message.replace(/^dependency cycle:\s*/, "");
}
