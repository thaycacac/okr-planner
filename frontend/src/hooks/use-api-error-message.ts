"use client";

import { useTranslations } from "next-intl";
import { useCallback } from "react";

import { dependencyChain, knownApiError } from "@/lib/api/error-message";

/**
 * Translates an API error by its code. Unknown codes fall back to `fallback`, a message for
 * the action that failed, or to a generic message.
 */
export function useApiErrorMessage() {
  const t = useTranslations("apiErrors");
  return useCallback(
    (error: unknown, fallback?: string) => {
      const known = knownApiError(error);
      if (!known) return fallback ?? t("generic");
      if (known.code === "dependency_cycle") return t("dependency_cycle", { chain: dependencyChain(known.message) });
      return t(known.code);
    },
    [t],
  );
}
