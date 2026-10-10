import { describe, expect, it } from "vitest";

import { isNavItemActive, navItems } from "./app-nav";

const hrefs = (pathname: string, today: string) =>
  Object.fromEntries(navItems(pathname, today).map((item) => [item.key, item.href]));

describe("navItems", () => {
  it("points tasks and calendar at the quarter being viewed", () => {
    expect(hrefs("/q/2027-Q1/calendar", "2026-10-01")).toMatchObject({
      tasks: "/q/2027-Q1/tasks",
      calendar: "/q/2027-Q1/calendar",
      workload: "/q/2027-Q1/workload",
    });
  });

  it("falls back to the current quarter elsewhere", () => {
    expect(hrefs("/settings/ai", "2026-11-15")).toMatchObject({
      plan: "/",
      tasks: "/q/2026-Q4/tasks",
      settings: "/settings",
    });
  });

  it("marks nested routes active but keeps home exact", () => {
    expect(isNavItemActive("/settings", "/settings/calendar")).toBe(true);
    expect(isNavItemActive("/", "/settings")).toBe(false);
    expect(isNavItemActive("/q/2026-Q4/tasks", "/q/2026-Q4/tasks")).toBe(true);
  });
});
