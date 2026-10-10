"use client";

import { useTranslations } from "next-intl";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export function LoadError({ onRetry }: { onRetry: () => void }) {
  const t = useTranslations();
  return (
    <Alert variant="destructive" className="max-w-xl">
      <AlertDescription className="flex flex-wrap items-center gap-3">
        <span>
          {t("settings.loadError")} {t("common.serverUnreachable")}
        </span>
        <Button size="sm" variant="outline" onClick={onRetry}>
          {t("common.retry")}
        </Button>
      </AlertDescription>
    </Alert>
  );
}
