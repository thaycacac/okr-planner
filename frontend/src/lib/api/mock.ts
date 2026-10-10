import { remoteInfo } from "./llm-remote";
import { MOCK_LOCAL_MODELS, MOCK_LOCK_SECONDS, MOCK_MAX_ATTEMPTS, MOCK_PASSWORD } from "./mock-config";
import type {
  CalendarSettings,
  ErrorResponse,
  LlmSettings,
  LlmSettingsUpdate,
  LlmTestRequest,
  LlmTestResult,
} from "./types";

// In-browser stand-in for the backend while its auth/settings routes are not
// published. Enabled only with NEXT_PUBLIC_API_MOCK=1.

type MockState = {
  authenticated: boolean;
  failedAttempts: number;
  lockedUntil: number | null;
  calendar: CalendarSettings;
  llm: LlmSettings;
};

const STORAGE_KEY = "okr-planner.mock-api";

export function initialMockState(): MockState {
  return {
    authenticated: false,
    failedAttempts: 0,
    lockedUntil: null,
    calendar: {
      capacity_minutes: { mon: 240, tue: 240, wed: 240, thu: 240, fri: 240, sat: 0, sun: 0 },
      work_saturday: false,
      work_sunday: false,
      work_holidays: false,
    },
    llm: {
      provider: "local",
      local_base_url: "http://localhost:11434",
      local_model: "qwen3:8b",
      local_api_style: "ollama",
      openai_model: "gpt-4o-mini",
      openai_api_key_configured: true,
      openai_api_key_saved: false,
      gemini_api_key_saved: false,
      gemini_model: "gemini-3.1-flash-lite",
      gemini_api_key_configured: true,
      claude_model: "sonnet",
      claude_cli_available: true,
    },
  };
}

let memoryState: MockState | null = null;

function storage(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.sessionStorage;
  } catch {
    return null;
  }
}

function load(): MockState {
  const raw = storage()?.getItem(STORAGE_KEY);
  if (raw) {
    try {
      return JSON.parse(raw) as MockState;
    } catch {
      // fall through to a fresh state
    }
  }
  return memoryState ?? initialMockState();
}

function save(state: MockState) {
  memoryState = state;
  storage()?.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function resetMockState() {
  memoryState = null;
  storage()?.removeItem(STORAGE_KEY);
}

function json(status: number, body: unknown, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

function error(status: number, detail: ErrorResponse["detail"], headers?: Record<string, string>) {
  return json(status, { detail } satisfies ErrorResponse, headers);
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isHttpUrl(value: string | undefined) {
  if (!value) return false;
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function testLlm(state: MockState, req: LlmTestRequest): LlmTestResult {
  if (req.provider !== "local") {
    const { model, ready, envVar } = remoteInfo(state.llm, req.provider);
    if (!ready) {
      return {
        ok: false,
        provider: req.provider,
        model,
        latency_ms: null,
        error: `${envVar} is not set`,
        error_code: "not_configured",
        available_models: [],
      };
    }
    return {
      ok: true,
      provider: req.provider,
      model,
      latency_ms: 740,
      error: null,
      error_code: null,
      available_models: [model],
    };
  }

  const model = req.local_model ?? state.llm.local_model;
  const baseUrl = req.local_base_url ?? state.llm.local_base_url;
  if (!isHttpUrl(baseUrl) || !baseUrl.includes("localhost")) {
    return {
      ok: false,
      provider: "local",
      model,
      latency_ms: null,
      error: `connection refused at ${baseUrl}`,
      error_code: "connection_failed",
      available_models: [],
    };
  }
  if (!MOCK_LOCAL_MODELS.includes(model)) {
    return {
      ok: false,
      provider: "local",
      model,
      latency_ms: 120,
      error: `model '${model}' not found`,
      error_code: "model_not_found",
      available_models: MOCK_LOCAL_MODELS,
    };
  }
  return {
    ok: true,
    provider: "local",
    model,
    latency_ms: 1800,
    error: null,
    error_code: null,
    available_models: MOCK_LOCAL_MODELS,
  };
}

export async function handleMockRequest(
  request: Request,
  now = Date.now(),
  basePath = "",
): Promise<Response> {
  await delay(process.env.NODE_ENV === "test" ? 0 : 250);
  const { pathname } = new URL(request.url);
  const prefix = basePath.replace(/\/$/, "");
  const path = prefix && pathname.startsWith(`${prefix}/`) ? pathname.slice(prefix.length) : pathname;
  const route = `${request.method} ${path}`;
  const state = load();

  if (route === "POST /auth/login") {
    if (state.lockedUntil && state.lockedUntil > now) {
      const retry = Math.ceil((state.lockedUntil - now) / 1000);
      return error(
        429,
        { code: "rate_limited", message: "Too many attempts", retry_after_seconds: retry },
        { "Retry-After": String(retry) },
      );
    }
    const body = (await request.json()) as { password?: string };
    if (body.password === MOCK_PASSWORD) {
      save({ ...state, authenticated: true, failedAttempts: 0, lockedUntil: null });
      return json(200, { authenticated: true });
    }
    const failedAttempts = state.failedAttempts + 1;
    if (failedAttempts >= MOCK_MAX_ATTEMPTS) {
      save({ ...state, failedAttempts: 0, lockedUntil: now + MOCK_LOCK_SECONDS * 1000 });
      return error(
        429,
        { code: "rate_limited", message: "Too many attempts", retry_after_seconds: MOCK_LOCK_SECONDS },
        { "Retry-After": String(MOCK_LOCK_SECONDS) },
      );
    }
    save({ ...state, failedAttempts, lockedUntil: null });
    return error(401, {
      code: "invalid_password",
      message: "Invalid password",
      attempts_left: MOCK_MAX_ATTEMPTS - failedAttempts,
    });
  }

  if (route === "POST /auth/logout") {
    save({ ...state, authenticated: false });
    return new Response(null, { status: 204 });
  }

  if (!state.authenticated) {
    return error(401, { code: "not_authenticated", message: "Not authenticated" });
  }

  switch (route) {
    case "GET /auth/me":
      return json(200, { authenticated: true });
    case "GET /settings/calendar":
      return json(200, state.calendar);
    case "PUT /settings/calendar": {
      const calendar = (await request.json()) as CalendarSettings;
      save({ ...state, calendar });
      return json(200, calendar);
    }
    case "GET /settings/llm":
      return json(200, state.llm);
    case "PUT /settings/llm": {
      const update = (await request.json()) as LlmSettingsUpdate;
      if (update.provider !== "local" && !remoteInfo(state.llm, update.provider).ready) {
        return error(409, { code: "openai_not_configured", message: "API key is not set" });
      }
      const { openai_api_key, gemini_api_key, ...rest } = update;
      const llm = { ...state.llm, ...rest };
      if (openai_api_key != null) {
        llm.openai_api_key_saved = openai_api_key.trim() !== "";
        llm.openai_api_key_configured = llm.openai_api_key_saved;
      }
      if (gemini_api_key != null) {
        llm.gemini_api_key_saved = gemini_api_key.trim() !== "";
        llm.gemini_api_key_configured = llm.gemini_api_key_saved;
      }
      save({ ...state, llm });
      return json(200, llm);
    }
    case "POST /settings/llm/test": {
      const req = (await request.json()) as LlmTestRequest;
      await delay(process.env.NODE_ENV === "test" ? 0 : 900);
      return json(200, testLlm(state, req));
    }
    default:
      return error(404, { code: "not_found", message: `${route} is not mocked` });
  }
}
