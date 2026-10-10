import { getTranslations } from "next-intl/server";

import { SettingsTabs } from "@/components/settings/settings-tabs";

export default async function SettingsLayout({ children }: LayoutProps<"/settings">) {
  const t = await getTranslations("settings");
  return (
    <div className="flex max-w-5xl flex-col gap-6">
      <h1 className="font-heading text-2xl font-semibold tracking-tight">{t("title")}</h1>
      <SettingsTabs />
      {children}
    </div>
  );
}
