import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createApiClient, CROSS_SITE_REQUEST_CODE, resolveApiBaseUrl } from "./client";

function clientReturning(status: number, baseUrl = "http://api.test") {
  const requests: Request[] = [];
  const onUnauthorized = vi.fn();
  const client = createApiClient({
    baseUrl,
    onUnauthorized,
    fetch: async (request) => {
      requests.push(request);
      return new Response(JSON.stringify({ detail: { code: "x", message: "x" } }), {
        status,
        headers: { "Content-Type": "application/json" },
      });
    },
  });
  return { client, requests, onUnauthorized };
}

describe("resolveApiBaseUrl", () => {
  it("defaults to the same-origin /api proxy", () => {
    expect(resolveApiBaseUrl(undefined)).toBe("/api");
    expect(resolveApiBaseUrl("")).toBe("/api");
  });

  it("accepts an override and drops the trailing slash", () => {
    expect(resolveApiBaseUrl("http://localhost:8000/")).toBe("http://localhost:8000");
  });
});

describe("createApiClient with a relative base URL", () => {
  // Browsers resolve a relative Request URL against the page; Node's Request
  // (used under jsdom) throws instead.
  beforeEach(() => {
    const NodeRequest = globalThis.Request;
    vi.stubGlobal(
      "Request",
      class extends NodeRequest {
        constructor(input: RequestInfo | URL, init?: RequestInit) {
          super(typeof input === "string" ? new URL(input, window.location.href) : input, init);
        }
      },
    );
  });
  afterEach(() => vi.unstubAllGlobals());

  it("calls the /api proxy on the page origin with cookies", async () => {
    const { client, requests } = clientReturning(200, "/api");
    await client.GET("/settings/llm");
    expect(requests[0].credentials).toBe("include");
    expect(requests[0].url).toBe(`${window.location.origin}/api/settings/llm`);
  });

  it("keeps auth endpoints self-handled behind the /api prefix", async () => {
    const { client, onUnauthorized } = clientReturning(401, "/api");
    await client.GET("/auth/me");
    expect(onUnauthorized).not.toHaveBeenCalled();
    await client.GET("/settings/llm");
    expect(onUnauthorized).toHaveBeenCalledOnce();
  });
});

describe("createApiClient", () => {
  it("sends cookies with every request", async () => {
    const { client, requests } = clientReturning(200);
    await client.GET("/settings/llm");
    expect(requests[0].credentials).toBe("include");
    expect(requests[0].url).toBe("http://api.test/settings/llm");
  });

  it("reports 401 on data endpoints", async () => {
    const { client, onUnauthorized } = clientReturning(401);
    await client.GET("/settings/calendar");
    expect(onUnauthorized).toHaveBeenCalledOnce();
  });

  it("lets auth endpoints handle their own 401", async () => {
    const { client, onUnauthorized } = clientReturning(401);
    await client.POST("/auth/login", { body: { password: "nope" } });
    await client.GET("/auth/me");
    expect(onUnauthorized).not.toHaveBeenCalled();
  });

  it("ignores other error statuses", async () => {
    const { client, onUnauthorized } = clientReturning(500);
    await client.GET("/settings/llm");
    expect(onUnauthorized).not.toHaveBeenCalled();
  });
});

describe("createApiClient cross-site rejections", () => {
  function clientWith(status: number, code: string) {
    const onCrossSite = vi.fn();
    const client = createApiClient({
      baseUrl: "http://api.test",
      onUnauthorized: vi.fn(),
      onCrossSite,
      fetch: async () => Response.json({ detail: { code, message: "x" } }, { status }),
    });
    return { client, onCrossSite };
  }

  it("reports a 403 cross_site_request and still hands the body to the caller", async () => {
    const { client, onCrossSite } = clientWith(403, CROSS_SITE_REQUEST_CODE);
    const { error } = await client.PUT("/settings/calendar", { body: {} as never });
    expect(onCrossSite).toHaveBeenCalledOnce();
    expect(error).toMatchObject({ detail: { code: CROSS_SITE_REQUEST_CODE } });
  });

  it("ignores other 403 codes and other statuses", async () => {
    const forbidden = clientWith(403, "forbidden");
    await forbidden.client.PUT("/settings/calendar", { body: {} as never });
    expect(forbidden.onCrossSite).not.toHaveBeenCalled();

    const conflict = clientWith(409, CROSS_SITE_REQUEST_CODE);
    await conflict.client.PUT("/settings/calendar", { body: {} as never });
    expect(conflict.onCrossSite).not.toHaveBeenCalled();
  });
});
