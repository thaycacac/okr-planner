import { beforeEach, describe, expect, it } from "vitest";

import { handleMockRequest, initialMockState, resetMockState } from "./mock";
import { MOCK_MAX_ATTEMPTS, MOCK_PASSWORD } from "./mock-config";

const base = "http://api.test";

function call(method: string, path: string, body?: unknown, now?: number) {
  const request = new Request(`${base}${path}`, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  return handleMockRequest(request, now);
}

describe("mock API", () => {
  beforeEach(() => resetMockState());

  it("requires a session for settings", async () => {
    expect((await call("GET", "/settings/llm")).status).toBe(401);
    expect((await call("GET", "/auth/me")).status).toBe(401);
    await call("POST", "/auth/login", { password: MOCK_PASSWORD });
    expect((await call("GET", "/settings/llm")).status).toBe(200);
    await call("POST", "/auth/logout");
    expect((await call("GET", "/settings/llm")).status).toBe(401);
  });

  it("routes requests behind the /api proxy prefix", async () => {
    const viaProxy = (method: string, path: string, body?: unknown) =>
      handleMockRequest(
        new Request(`${base}/api${path}`, {
          method,
          headers: body === undefined ? undefined : { "Content-Type": "application/json" },
          body: body === undefined ? undefined : JSON.stringify(body),
        }),
        Date.now(),
        "/api",
      );
    expect((await viaProxy("POST", "/auth/login", { password: MOCK_PASSWORD })).status).toBe(200);
    expect((await viaProxy("GET", "/auth/me")).status).toBe(200);
  });

  it("counts down attempts, then locks with 429", async () => {
    const now = 1_000_000;
    const first = await call("POST", "/auth/login", { password: "wrong" }, now);
    expect(first.status).toBe(401);
    expect((await first.json()).detail.attempts_left).toBe(MOCK_MAX_ATTEMPTS - 1);

    for (let i = 1; i < MOCK_MAX_ATTEMPTS - 1; i++) {
      await call("POST", "/auth/login", { password: "wrong" }, now);
    }
    const locked = await call("POST", "/auth/login", { password: "wrong" }, now);
    expect(locked.status).toBe(429);
    expect((await locked.json()).detail.retry_after_seconds).toBe(60);

    const stillLocked = await call("POST", "/auth/login", { password: MOCK_PASSWORD }, now + 10_000);
    expect(stillLocked.status).toBe(429);
    const unlocked = await call("POST", "/auth/login", { password: MOCK_PASSWORD }, now + 61_000);
    expect(unlocked.status).toBe(200);
  });

  it("reports connection test outcomes with error codes", async () => {
    await call("POST", "/auth/login", { password: MOCK_PASSWORD });
    const ok = await (await call("POST", "/settings/llm/test", { provider: "local" })).json();
    expect(ok).toMatchObject({ ok: true, model: "qwen3:8b", latency_ms: 1800 });

    const missing = await (
      await call("POST", "/settings/llm/test", { provider: "local", local_model: "nope:1b" })
    ).json();
    expect(missing).toMatchObject({ ok: false, error_code: "model_not_found" });

    const refused = await (
      await call("POST", "/settings/llm/test", { provider: "local", local_base_url: "http://gpu-box:11434" })
    ).json();
    expect(refused).toMatchObject({ ok: false, error_code: "connection_failed" });
  });

  it("rejects switching to OpenAI when its key is not configured", async () => {
    sessionStorage.setItem(
      "okr-planner.mock-api",
      JSON.stringify({
        ...initialMockState(),
        authenticated: true,
        llm: { ...initialMockState().llm, openai_api_key_configured: false },
      }),
    );
    const { llm } = initialMockState();
    const res = await call("PUT", "/settings/llm", {
      provider: "openai",
      local_base_url: llm.local_base_url,
      local_model: llm.local_model,
      local_api_style: llm.local_api_style,
    });
    expect(res.status).toBe(409);
    expect((await res.json()).detail.code).toBe("openai_not_configured");
  });

  it("persists calendar updates", async () => {
    await call("POST", "/auth/login", { password: MOCK_PASSWORD });
    const current = await (await call("GET", "/settings/calendar")).json();
    const next = { ...current, work_saturday: true, capacity_minutes: { ...current.capacity_minutes, sat: 120 } };
    expect((await call("PUT", "/settings/calendar", next)).status).toBe(200);
    expect(await (await call("GET", "/settings/calendar")).json()).toEqual(next);
  });
});
