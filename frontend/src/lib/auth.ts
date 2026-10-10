export type LoginReason = "expired";

export function safeNextPath(value: string | string[] | undefined | null): string {
  const raw = Array.isArray(value) ? value[0] : value;
  if (!raw || !raw.startsWith("/") || raw.startsWith("//") || raw.startsWith("/\\")) {
    return "/";
  }
  if (raw === "/login" || raw.startsWith("/login?")) return "/";
  return raw;
}

export function loginPath({ next, reason }: { next?: string; reason?: LoginReason } = {}) {
  const params = new URLSearchParams();
  const target = safeNextPath(next);
  if (target !== "/") params.set("next", target);
  if (reason) params.set("reason", reason);
  const query = params.toString();
  return query ? `/login?${query}` : "/login";
}
