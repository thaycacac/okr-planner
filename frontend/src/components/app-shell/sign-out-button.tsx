"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useTransition } from "react";
import { LogOutIcon } from "lucide-react";

import { useLeaveGuard } from "@/components/app-shell/unsaved-changes";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api/client";

export function SignOutButton() {
  const t = useTranslations("nav");
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const { confirmLeave } = useLeaveGuard();

  function signOut() {
    startTransition(async () => {
      try {
        await api.POST("/auth/logout");
      } finally {
        router.replace("/login");
      }
    });
  }

  return (
    <Button variant="ghost" size="sm" onClick={() => confirmLeave(signOut)} disabled={pending}>
      <LogOutIcon aria-hidden />
      <span className="hidden sm:inline">{t("signOut")}</span>
      <span className="sr-only sm:hidden">{t("signOut")}</span>
    </Button>
  );
}
