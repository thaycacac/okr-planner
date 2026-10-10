"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useLoad } from "@/hooks/use-load";
import { api } from "@/lib/api/client";
import { loginPath } from "@/lib/auth";

async function checkSession() {
  const { response } = await api.GET("/auth/me");
  if (response.status === 401) return "signed-out" as const;
  return response.ok ? ("signed-in" as const) : undefined;
}

// The session check runs in the browser by calling /auth/me through the /api
// proxy. The cookie is first-party on this origin, so a server-side check is
// possible later; until then the gate stays client-only.
export function AuthGate({ children }: { children: React.ReactNode }) {
  const t = useTranslations("common");
  const router = useRouter();
  const [state, retry] = useLoad(checkSession);
  const signedOut = state.status === "ready" && state.data === "signed-out";

  useEffect(() => {
    if (signedOut) {
      router.replace(loginPath({ next: window.location.pathname + window.location.search }));
    }
  }, [signedOut, router]);

  if (state.status === "ready" && state.data === "signed-in") return <>{children}</>;

  if (state.status === "error") {
    return (
      <Alert variant="destructive" className="max-w-xl">
        <AlertDescription className="flex flex-wrap items-center gap-3">
          <span>{t("serverUnreachable")}</span>
          <Button size="sm" variant="outline" onClick={retry}>
            {t("retry")}
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex flex-col gap-4" aria-busy="true">
      <span className="sr-only" role="status">
        {t("loading")}
      </span>
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-40 w-full max-w-3xl" />
    </div>
  );
}
