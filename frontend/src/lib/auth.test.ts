import { describe, expect, it } from "vitest";

import { loginPath, safeNextPath } from "./auth";

describe("safeNextPath", () => {
  it("keeps same-origin paths", () => {
    expect(safeNextPath("/settings/ai")).toBe("/settings/ai");
    expect(safeNextPath(["/settings?tab=1", "/x"])).toBe("/settings?tab=1");
  });

  it.each([undefined, null, "", "https://evil.test", "//evil.test", "/\\evil.test", "settings", "/login", "/login?next=/"])(
    "falls back to / for %s",
    (value) => {
      expect(safeNextPath(value)).toBe("/");
    },
  );
});

describe("loginPath", () => {
  it("omits empty params", () => {
    expect(loginPath()).toBe("/login");
    expect(loginPath({ next: "/" })).toBe("/login");
  });

  it("encodes next and reason", () => {
    expect(loginPath({ next: "/settings/ai?x=1", reason: "expired" })).toBe(
      "/login?next=%2Fsettings%2Fai%3Fx%3D1&reason=expired",
    );
  });
});
