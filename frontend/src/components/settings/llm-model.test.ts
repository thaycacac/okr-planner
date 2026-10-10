import { describe, expect, it } from "vitest";

import {
  countChanges,
  isDirty,
  type LlmDraft,
  needsRemoteConsent,
  toTestRequest,
  validate,
} from "./llm-model";

const local: LlmDraft = {
  provider: "local",
  local_base_url: "http://localhost:11434",
  local_model: "qwen3:8b",
  local_api_style: "ollama",
};

describe("validate", () => {
  it("accepts a valid local config", () => {
    expect(validate(local)).toEqual({});
  });

  it("flags a bad URL and empty model", () => {
    expect(
      validate({
        ...local,
        local_base_url: "localhost:11434",
        local_model: "  ",
      }),
    ).toEqual({
      baseUrl: "invalid",
      model: "required",
    });
  });

  it("skips local fields for OpenAI", () => {
    expect(
      validate({ ...local, provider: "openai", local_base_url: "" }),
    ).toEqual({});
  });
});

describe("toTestRequest", () => {
  it("tests the unsaved local values, normalised", () => {
    expect(
      toTestRequest({
        ...local,
        local_base_url: " http://localhost:11434/ ",
        local_model: " m ",
      }),
    ).toEqual({
      provider: "local",
      local_base_url: "http://localhost:11434",
      local_model: "m",
      local_api_style: "ollama",
    });
  });

  it("sends only the provider for OpenAI", () => {
    expect(toTestRequest({ ...local, provider: "openai" })).toEqual({
      provider: "openai",
    });
  });
});

describe("isDirty / needsRemoteConsent", () => {
  it("ignores whitespace and trailing slashes", () => {
    expect(
      isDirty(local, { ...local, local_base_url: "http://localhost:11434/" }),
    ).toBe(false);
    expect(isDirty(local, { ...local, local_model: "llama3.1:8b" })).toBe(true);
  });

  it("counts each changed field once", () => {
    expect(countChanges(local, local)).toBe(0);
    expect(
      countChanges(local, {
        ...local,
        local_model: "llama3.1:8b",
        local_api_style: "openai_compatible",
      }),
    ).toBe(2);
  });

  it("asks for consent only when moving to a different non-local provider", () => {
    expect(needsRemoteConsent("local", "openai")).toBe(true);
    expect(needsRemoteConsent("openai", "openai")).toBe(false);
    expect(needsRemoteConsent("openai", "local")).toBe(false);
    expect(needsRemoteConsent("local", "gemini")).toBe(true);
    expect(needsRemoteConsent("local", "claude")).toBe(true);
  });
});
