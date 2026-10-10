import { getLocale, getTranslations } from "next-intl/server";
import { cn } from "cn";

import { locales } from "@/i18n/config";
import { setLocale } from "@/i18n/actions";

export async function LocaleSwitcher({ className }: { className?: string }) {
  const [locale, t] = await Promise.all([getLocale(), getTranslations("locale")]);
  return (
    <form action={setLocale} className={className}>
      <div
        role="group"
        aria-label={t("label")}
        className="inline-flex rounded-lg border border-border bg-muted p-0.5"
      >
        {locales.map((value) => {
          const active = value === locale;
          return (
            <button
              key={value}
              type="submit"
              name="locale"
              value={value}
              lang={value}
              aria-pressed={active}
              title={t(value)}
              className={cn(
                "min-w-9 rounded-md px-2 py-1 text-xs font-semibold uppercase outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                active
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              <span aria-hidden>{value}</span>
              <span className="sr-only">{t(value)}</span>
            </button>
          );
        })}
      </div>
    </form>
  );
}
