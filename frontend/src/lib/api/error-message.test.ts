import { describe, expect, it } from "vitest";

import en from "../../../messages/en.json";
import vi from "../../../messages/vi.json";
import { API_ERROR_CODES, dependencyChain, knownApiError } from "./error-message";

describe("apiErrors messages", () => {
  it.each([
    ["vi", vi],
    ["en", en],
  ])("%s translates every known code and nothing else", (_, messages) => {
    expect(Object.keys(messages.apiErrors).sort()).toEqual([...API_ERROR_CODES, "generic"].sort());
  });
});

describe("knownApiError", () => {
  it("reads an openapi-fetch error body", () => {
    expect(knownApiError({ detail: { code: "quarter_exists", message: "Q1/2026 already exists" } })).toEqual({
      code: "quarter_exists",
      message: "Q1/2026 already exists",
    });
  });

  it("reads an error detail or a thrown error carrying a code", () => {
    expect(knownApiError({ code: "task_done", message: "" })?.code).toBe("task_done");
    expect(knownApiError(Object.assign(new Error("dependency cycle: 1 → 2 → 1"), { code: "dependency_cycle" }))).toEqual({
      code: "dependency_cycle",
      message: "dependency cycle: 1 → 2 → 1",
    });
  });

  it("ignores unknown codes and bodies without a code", () => {
    expect(knownApiError({ detail: { code: "http_500", message: "boom" } })).toBeNull();
    expect(knownApiError({ detail: [{ loc: ["body"], msg: "Field required" }] })).toBeNull();
    expect(knownApiError(null)).toBeNull();
    expect(knownApiError(new Error("network"))).toBeNull();
  });
});

describe("dependencyChain", () => {
  it("strips the server prefix", () => {
    expect(dependencyChain("dependency cycle: 12 → 15 → 12")).toBe("12 → 15 → 12");
  });
});
