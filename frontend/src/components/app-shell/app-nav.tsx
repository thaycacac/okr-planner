"use client";

import { GuardedLink } from "@/components/app-shell/unsaved-changes";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { cn } from "cn";
import { CalendarDaysIcon, ChartColumnIcon, ListTreeIcon, SettingsIcon, TargetIcon, type LucideIcon } from "lucide-react";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { localToday } from "@/lib/plan/dates";
import { quarterOf, quarterSlug } from "@/lib/plan/quarter";

type NavKey = "plan" | "tasks" | "calendar" | "workload" | "settings";
type NavItem = { key: NavKey; href: string; icon: LucideIcon };

const QUARTER_PATH = /^\/q\/([^/]+)(?:\/|$)/;

export function navItems(pathname: string, today: string): NavItem[] {
  const slug = QUARTER_PATH.exec(pathname)?.[1] ?? quarterSlug(quarterOf(today));
  return [
    { key: "plan", href: "/", icon: TargetIcon },
    { key: "tasks", href: `/q/${slug}/tasks`, icon: ListTreeIcon },
    { key: "calendar", href: `/q/${slug}/calendar`, icon: CalendarDaysIcon },
    { key: "workload", href: `/q/${slug}/workload`, icon: ChartColumnIcon },
    { key: "settings", href: "/settings", icon: SettingsIcon },
  ];
}

export function isNavItemActive(href: string, pathname: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

function useNavItems() {
  const pathname = usePathname();
  return { pathname, items: navItems(pathname, localToday()) };
}

/** An icon rail on tablets, where the week calendar needs the width; full labels from xl. */
export function AppSidebar() {
  const t = useTranslations("nav");
  const { pathname, items } = useNavItems();
  return (
    <nav
      aria-label={t("label")}
      className="hidden w-16 shrink-0 border-r border-sidebar-border bg-sidebar p-3 md:block xl:w-56"
    >
      <TooltipProvider>
        <ul className="flex flex-col gap-1">
          {items.map(({ href, key, icon: Icon }) => {
            const active = isNavItemActive(href, pathname);
            return (
              <li key={key}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <GuardedLink
                      href={href}
                      aria-current={active ? "page" : undefined}
                      className={cn(
                        "flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background xl:justify-start",
                        active
                          ? "bg-sidebar-accent font-semibold text-sidebar-accent-foreground"
                          : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                      )}
                    >
                      <Icon className="size-4 shrink-0" aria-hidden />
                      <span className="sr-only xl:not-sr-only">{t(key)}</span>
                    </GuardedLink>
                  </TooltipTrigger>
                  <TooltipContent side="right" className="xl:hidden">
                    {t(key)}
                  </TooltipContent>
                </Tooltip>
              </li>
            );
          })}
        </ul>
      </TooltipProvider>
    </nav>
  );
}

export function AppTabBar() {
  const t = useTranslations("nav");
  const { pathname, items } = useNavItems();
  return (
    <nav
      aria-label={t("label")}
      className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-background pb-[env(safe-area-inset-bottom)] md:hidden"
    >
      <ul className="grid grid-cols-5">
        {items.map(({ href, key, icon: Icon }) => {
          const active = isNavItemActive(href, pathname);
          return (
            <li key={key}>
              <GuardedLink
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex min-h-14 flex-col items-center justify-center gap-0.5 text-xs outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                  active ? "font-semibold text-foreground" : "text-muted-foreground",
                )}
              >
                <Icon className="size-5" aria-hidden />
                {t(key === "plan" ? "planShort" : key)}
              </GuardedLink>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
