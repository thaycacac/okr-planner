import type {
  LlmProviderName,
  LlmSettings,
  LlmSettingsUpdate,
  LlmTestRequest,
} from "@/lib/api/types";

export type LlmDraft = LlmSettingsUpdate;
export type LlmFieldErrors = { baseUrl?: "invalid"; model?: "required" };

export function toDraft(settings: LlmSettings): LlmDraft {
  return {
    provider: settings.provider,
    local_base_url: settings.local_base_url,
    local_model: settings.local_model,
    local_api_style: settings.local_api_style,
  };
}

export function isHttpUrl(value: string) {
  try {
    const url = new URL(value.trim());
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

export function validate(draft: LlmDraft): LlmFieldErrors {
  if (draft.provider !== "local") return {};
  const errors: LlmFieldErrors = {};
  if (!isHttpUrl(draft.local_base_url)) errors.baseUrl = "invalid";
  if (!draft.local_model.trim()) errors.model = "required";
  return errors;
}

export const KEY_FIELDS = ["openai_api_key", "gemini_api_key"] as const;

export function normalize(draft: LlmDraft): LlmDraft {
  const normalized: LlmDraft = {
    ...draft,
    local_base_url: draft.local_base_url.trim().replace(/\/+$/, ""),
    local_model: draft.local_model.trim(),
  };
  // undefined = keep the stored key, "" = remove it, anything else replaces it.
  for (const field of KEY_FIELDS) {
    const value = draft[field];
    if (value == null) delete normalized[field];
    else normalized[field] = value.trim();
  }
  return normalized;
}

export function toTestRequest(draft: LlmDraft): LlmTestRequest {
  if (draft.provider !== "local") {
    // A key typed in the form is tested before it is saved.
    const key = draft.provider === "openai" ? draft.openai_api_key : draft.provider === "gemini" ? draft.gemini_api_key : undefined;
    return key?.trim() ? { provider: draft.provider, [`${draft.provider}_api_key`]: key.trim() } : { provider: draft.provider };
  }
  const { local_base_url, local_model, local_api_style } = normalize(draft);
  return { provider: "local", local_base_url, local_model, local_api_style };
}

const DRAFT_FIELDS = [
  "provider",
  "local_base_url",
  "local_model",
  "local_api_style",
  ...KEY_FIELDS,
] as const;

export function countChanges(saved: LlmDraft, draft: LlmDraft) {
  const a = normalize(saved);
  const b = normalize(draft);
  return DRAFT_FIELDS.filter((field) => a[field] !== b[field]).length;
}

export function isDirty(saved: LlmDraft, draft: LlmDraft) {
  return countChanges(saved, draft) > 0;
}

// Every provider except Local sends OKR content off the machine (OpenAI, Gemini, and
// Claude through the local CLI all reach a cloud API), so switching needs explicit consent.
export function needsRemoteConsent(savedProvider: LlmProviderName, next: LlmProviderName) {
  return next !== "local" && next !== savedProvider;
}

export { remoteInfo, type RemoteProvider } from "@/lib/api/llm-remote";
