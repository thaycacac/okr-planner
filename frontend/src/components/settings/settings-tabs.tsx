"use client";

import { GuardedLink } from "@/components/app-shell/unsaved-changes";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useRef } from "react";
import { cn } from "cn";

const TABS = [
  { href: "/settings/calendar", key: "calendar" },
  { href: "/settings/leave", key: "leave" },
  { href: "/settings/holidays", key: "holidays" },
  { href: "/settings/ai", key: "ai" },
] as const;

export function SettingsTabs() {
  const t = useTranslations("settings");
  const pathname = usePathname();
  const activeRef = useRef<HTMLAnchorElement>(null);

  // On the narrowest phones the row still scrolls; keep the current tab in view.
  useEffect(() => {
    activeRef.current?.scrollIntoView({ block: "nearest", inline: "nearest" });
  }, [pathname]);

  return (
    <nav aria-label={t("tabsLabel")} className="-mx-4 overflow-x-auto border-b border-border px-4 sm:mx-0 sm:px-0">
      <ul className="-mb-px flex whitespace-nowrap sm:gap-1">
        {TABS.map(({ href, key }) => {
          const active = pathname === href;
          return (
            <li key={key} className="flex-1 sm:flex-none">
              <GuardedLink
                ref={active ? activeRef : undefined}
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "block border-b-2 px-2 py-2 sm:px-4 text-center text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                  active
                    ? "border-foreground font-semibold text-foreground"
                    : "border-transparent text-muted-foreground hover:text-foreground",
                )}
              >
                {t(`tabs.${key}`)}
              </GuardedLink>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
