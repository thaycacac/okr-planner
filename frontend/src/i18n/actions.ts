"use server";

import { cookies } from "next/headers";

import { localeCookieName, resolveLocale } from "./config";

export async function setLocale(formData: FormData) {
  const locale = resolveLocale(formData.get("locale")?.toString());
  const store = await cookies();
  store.set(localeCookieName, locale, {
    path: "/",
    maxAge: 60 * 60 * 24 * 365,
    sameSite: "lax",
  });
}
