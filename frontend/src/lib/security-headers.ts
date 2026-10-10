// Page-only rules: /api/* responses come from the backend, which sends its own
// JSON-oriented headers (CSP `default-src 'none'`) that must not be replaced.
export const PAGE_PATHS = "/((?!api/|api$).*)";

export const STATIC_SECURITY_HEADERS = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
];

export const HSTS_HEADER = {
  key: "Strict-Transport-Security",
  value: "max-age=31536000; includeSubDomains",
};

type HeaderRule = {
  source: string;
  headers: { key: string; value: string }[];
  has?: { type: "header"; key: string; value: string }[];
};

export function pageSecurityHeaders({ dev }: { dev: boolean }): HeaderRule[] {
  const rules: HeaderRule[] = [{ source: PAGE_PATHS, headers: STATIC_SECURITY_HEADERS }];
  if (!dev) {
    // `next start` and the Docker image also run on plain http://localhost, so HSTS
    // additionally requires the TLS-terminating edge to report an HTTPS request.
    rules.push({
      source: PAGE_PATHS,
      has: [{ type: "header", key: "x-forwarded-proto", value: "https" }],
      headers: [HSTS_HEADER],
    });
  }
  return rules;
}

export function buildContentSecurityPolicy({ nonce, dev }: { nonce: string; dev: boolean }) {
  const directives: [string, ...string[]][] = [
    ["default-src", "'self'"],
    // Next.js puts the nonce on its own scripts; 'strict-dynamic' lets them load
    // further chunks. React only needs eval in development (server error stacks).
    ["script-src", "'self'", `'nonce-${nonce}'`, "'strict-dynamic'", ...(dev ? ["'unsafe-eval'"] : [])],
    // 'unsafe-inline' without a nonce (a nonce would make browsers ignore it): SSR
    // emits style="" attributes, and Radix, sonner and FullCalendar inject <style>
    // tags at runtime. Scripts stay nonce-only, which is what blocks XSS.
    ["style-src", "'self'", "'unsafe-inline'"],
    ["img-src", "'self'", "data:", "blob:"],
    // FullCalendar ships its icon font as a data: URI.
    ["font-src", "'self'", "data:"],
    // API calls and the plan SSE stream go through the same-origin /api proxy.
    ["connect-src", "'self'"],
    ["object-src", "'none'"],
    ["base-uri", "'self'"],
    ["form-action", "'self'"],
    ["frame-ancestors", "'none'"],
  ];
  return directives.map((d) => d.join(" ")).join("; ");
}
