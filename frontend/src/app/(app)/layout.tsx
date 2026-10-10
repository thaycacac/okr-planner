import { getTranslations } from "next-intl/server";

import { CrossSiteNotice } from "@/components/app-shell/cross-site-notice";
import { SignOutButton } from "@/components/app-shell/sign-out-button";
import {
  GuardedLink,
  UnsavedChangesProvider,
} from "@/components/app-shell/unsaved-changes";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { Badge } from "@/components/ui/badge";
import { Toaster } from "@/components/ui/sonner";
import { apiMockEnabled } from "@/lib/api/client";

export default async function AppLayout({ children }: LayoutProps<"/">) {
  const t = await getTranslations();
  return (
    <UnsavedChangesProvider>
      <div className="flex min-h-svh flex-col">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-background focus:px-3 focus:py-2 focus:shadow"
        >
          {t("common.skipToContent")}
        </a>
        <header className="sticky top-0 z-40 flex h-14 items-center gap-3 border-b border-border bg-background/95 px-4 backdrop-blur md:px-6">
          <GuardedLink
            href="/"
            className="font-heading text-base font-bold tracking-tight"
          >
            {t("app.name")}
          </GuardedLink>
          {apiMockEnabled && (
            <Badge
              variant="outline"
              className="hidden sm:inline-flex"
              title={t("common.mockMode")}
            >
              {t("common.mockBadge")}
            </Badge>
          )}
          <span className="flex-1" />
          <LocaleSwitcher />
          <SignOutButton />
        </header>
        {children}
      </div>
      <Toaster position="bottom-center" />
      <CrossSiteNotice />
    </UnsavedChangesProvider>
  );
}
