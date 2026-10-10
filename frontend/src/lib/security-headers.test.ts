import { describe, expect, it } from "vitest";

import { config as proxyConfig } from "@/proxy";

import {
  buildContentSecurityPolicy,
  PAGE_PATHS,
  pageSecurityHeaders,
} from "./security-headers";

function directives(csp: string) {
  return new Map(
    csp.split("; ").map((d) => {
      const [name, ...values] = d.split(" ");
      return [name, values] as const;
    }),
  );
}

function headerMap(dev: boolean, https: boolean) {
  const out = new Map<string, string>();
  for (const rule of pageSecurityHeaders({ dev })) {
    const needsHttps = rule.has?.some((h) => h.key === "x-forwarded-proto" && h.value === "https");
    if (needsHttps && !https) continue;
    for (const h of rule.headers) out.set(h.key, h.value);
  }
  return out;
}

describe("buildContentSecurityPolicy", () => {
  it("covers the baseline directives for pages", () => {
    const csp = directives(buildContentSecurityPolicy({ nonce: "abc", dev: false }));
    expect(csp.get("default-src")).toEqual(["'self'"]);
    expect(csp.get("connect-src")).toEqual(["'self'"]);
    expect(csp.get("frame-ancestors")).toEqual(["'none'"]);
    expect(csp.get("base-uri")).toEqual(["'self'"]);
    expect(csp.get("form-action")).toEqual(["'self'"]);
    expect(csp.get("object-src")).toEqual(["'none'"]);
  });

  it("allows scripts only by nonce and never inline", () => {
    const script = directives(buildContentSecurityPolicy({ nonce: "abc", dev: false })).get("script-src");
    expect(script).toContain("'nonce-abc'");
    expect(script).toContain("'strict-dynamic'");
    expect(script).not.toContain("'unsafe-inline'");
    expect(script).not.toContain("'unsafe-eval'");
  });

  it("adds 'unsafe-eval' only in development", () => {
    const script = directives(buildContentSecurityPolicy({ nonce: "abc", dev: true })).get("script-src");
    expect(script).toContain("'unsafe-eval'");
  });

  it("allows FullCalendar's data: icon font", () => {
    const font = directives(buildContentSecurityPolicy({ nonce: "abc", dev: false })).get("font-src");
    expect(font).toEqual(["'self'", "data:"]);
  });

  it("keeps style-src free of a nonce so 'unsafe-inline' stays effective", () => {
    const style = directives(buildContentSecurityPolicy({ nonce: "abc", dev: false })).get("style-src");
    expect(style).toEqual(["'self'", "'unsafe-inline'"]);
  });
});

describe("pageSecurityHeaders", () => {
  it("sends the static hardening headers on pages", () => {
    const headers = headerMap(false, false);
    expect(headers.get("X-Content-Type-Options")).toBe("nosniff");
    expect(headers.get("X-Frame-Options")).toBe("DENY");
    expect(headers.get("Referrer-Policy")).toBe("strict-origin-when-cross-origin");
    expect(headers.get("Permissions-Policy")).toBe("camera=(), microphone=(), geolocation=()");
  });

  it("sends HSTS only for production builds reached over HTTPS", () => {
    expect(headerMap(false, true).get("Strict-Transport-Security")).toBe(
      "max-age=31536000; includeSubDomains",
    );
    expect(headerMap(false, false).has("Strict-Transport-Security")).toBe(false);
    expect(headerMap(true, true).has("Strict-Transport-Security")).toBe(false);
  });
});

describe("page path matching", () => {
  // Next.js anchors these sources the same way (path-to-regexp over the full pathname).
  const pageRule = new RegExp(`^${PAGE_PATHS}$`);
  const proxySource = proxyConfig.matcher[0].source;
  const proxyRule = new RegExp(`^${proxySource}$`);

  it.each(["/", "/login", "/settings/ai", "/plan/new/generate", "/apiary"])("covers page %s", (path) => {
    expect(pageRule.test(path)).toBe(true);
    expect(proxyRule.test(path)).toBe(true);
  });

  it.each(["/api", "/api/health", "/api/plans/1/events"])("leaves backend route %s alone", (path) => {
    expect(pageRule.test(path)).toBe(false);
    expect(proxyRule.test(path)).toBe(false);
  });

  it("skips static assets in the CSP proxy", () => {
    expect(proxyRule.test("/_next/static/chunks/main.js")).toBe(false);
    expect(proxyRule.test("/favicon.ico")).toBe(false);
  });
});
