import createClient, { type Middleware } from "openapi-fetch";

import { loginPath } from "@/lib/auth";

import type { paths } from "./schema";
import { errorDetail } from "./types";

// Relative by default: Next.js rewrites /api/* to the backend, so the session
// cookie stays first-party on the frontend origin.
export const DEFAULT_API_BASE_URL = "/api";

export function resolveApiBaseUrl(configured: string | undefined) {
  return (configured || DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

export const apiBaseUrl = resolveApiBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL);

export const apiMockEnabled = process.env.NEXT_PUBLIC_API_MOCK === "1";

// The auth endpoints answer 401 as part of their normal contract, so the
// caller decides what to do instead of being bounced to the login page.
const SELF_HANDLED_401 = ["/auth/login", "/auth/me"];

export function unauthorizedMiddleware(onUnauthorized: () => void): Middleware {
  return {
    onResponse({ request, response }) {
      if (response.status !== 401) return;
      const path = new URL(request.url).pathname;
      if (SELF_HANDLED_401.some((p) => path.endsWith(p))) return;
      onUnauthorized();
    },
  };
}

export const CROSS_SITE_REQUEST_CODE = "cross_site_request";
export const CROSS_SITE_EVENT = "api:cross-site-request";

// The backend rejects writes whose Origin is not the app itself (403). Same-origin
// calls through the /api proxy never hit this, so it signals a misconfigured
// deployment or a stale page on another host rather than a user mistake.
export function crossSiteMiddleware(onCrossSite: () => void): Middleware {
  return {
    async onResponse({ response }) {
      if (response.status !== 403) return;
      const body: unknown = await response.clone().json().catch(() => null);
      if (errorDetail(body)?.code === CROSS_SITE_REQUEST_CODE) onCrossSite();
    },
  };
}

type ApiClientOptions = {
  baseUrl: string;
  fetch?: (input: Request) => Promise<Response>;
  onUnauthorized: () => void;
  onCrossSite?: () => void;
};

export function createApiClient({ baseUrl, fetch, onUnauthorized, onCrossSite }: ApiClientOptions) {
  const client = createClient<paths>({ baseUrl, credentials: "include", fetch });
  client.use(unauthorizedMiddleware(onUnauthorized));
  if (onCrossSite) client.use(crossSiteMiddleware(onCrossSite));
  return client;
}

export type ApiClient = ReturnType<typeof createApiClient>;

function redirectToLogin() {
  if (typeof window === "undefined") return;
  const { pathname, search } = window.location;
  if (pathname === "/login") return;
  window.location.assign(loginPath({ next: pathname + search, reason: "expired" }));
}

function announceCrossSite() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(CROSS_SITE_EVENT));
}

async function mockFetch(request: Request): Promise<Response> {
  const { handleMockRequest } = await import("./mock");
  const basePath = new URL(apiBaseUrl, request.url).pathname;
  return handleMockRequest(request, Date.now(), basePath);
}

export const api = createApiClient({
  baseUrl: apiBaseUrl,
  fetch: apiMockEnabled ? mockFetch : undefined,
  onUnauthorized: redirectToLogin,
  onCrossSite: announceCrossSite,
});
