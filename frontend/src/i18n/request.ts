import { cookies } from "next/headers";
import { getRequestConfig } from "next-intl/server";

import { localeCookieName, resolveLocale } from "./config";

export default getRequestConfig(async () => {
  const store = await cookies();
  const locale = resolveLocale(store.get(localeCookieName)?.value);
  return {
    locale,
    // Single-user app planned in Vietnam; a fixed zone keeps server and client timestamps identical.
    timeZone: "Asia/Ho_Chi_Minh",
    messages: (await import(`../../messages/${locale}.json`)).default,
  };
});
