import type { LlmProviderName, LlmSettings } from "./types";

export type RemoteProvider = Exclude<LlmProviderName, "local">;

// What the settings card shows for a non-local provider. Claude has no API key: it needs the
// `claude` CLI on the server's PATH.
export function remoteInfo(settings: LlmSettings, provider: RemoteProvider) {
  switch (provider) {
    case "openai":
      return { model: settings.openai_model, ready: settings.openai_api_key_configured, envVar: "OPENAI_API_KEY" };
    case "gemini":
      return { model: settings.gemini_model, ready: settings.gemini_api_key_configured, envVar: "GEMINI_API_KEY" };
    case "claude":
      return { model: settings.claude_model, ready: settings.claude_cli_available, envVar: "claude" };
  }
}
