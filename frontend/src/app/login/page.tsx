import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { LoginForm } from "@/components/auth/login-form";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { safeNextPath } from "@/lib/auth";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("auth");
  return { title: `${t("title")} · OKR Planner` };
}

export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const [params, t] = await Promise.all([searchParams, getTranslations()]);
  return (
    <div className="flex min-h-svh flex-col bg-muted/40">
      <div className="flex justify-end px-4 py-4 md:px-6">
        <LocaleSwitcher />
      </div>
      <main className="flex flex-1 justify-center px-4 pt-6 pb-16 md:pt-16">
        <Card className="h-fit w-full max-w-md">
          <CardHeader className="gap-2">
            <span className="font-heading text-lg font-bold tracking-tight">{t("app.name")}</span>
            <CardTitle>
              <h1 className="font-heading text-xl font-semibold">{t("auth.title")}</h1>
            </CardTitle>
            <CardDescription>{t("auth.description")}</CardDescription>
          </CardHeader>
          <CardContent>
            <LoginForm next={safeNextPath(params.next)} expired={params.reason === "expired"} />
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
