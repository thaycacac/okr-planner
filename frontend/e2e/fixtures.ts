import { type APIRequestContext, expect, type Page, test as base } from "@playwright/test";

/** Must match `E2E_PASSWORD` in `backend/tests/e2e_server.py`. */
export const E2E_PASSWORD = "e2e-okr-planner";

export const test = base.extend({
  context: async ({ context, baseURL }, provide) => {
    await context.addCookies([{ name: "NEXT_LOCALE", value: "en", url: baseURL! }]);
    await provide(context);
  },
});

export { expect };

export async function signIn(page: Page, next = "/") {
  await page.goto(next);
  await expect(page).toHaveURL(/\/login/);
  await page.getByLabel("Password", { exact: true }).fill(E2E_PASSWORD);
  await page.getByRole("button", { name: "Enter app" }).click();
  await expect(page).not.toHaveURL(/\/login/);
}

/** Calls the backend through the Next.js proxy with the page's session cookie. */
export async function apiCall<T>(
  request: APIRequestContext,
  method: "GET" | "POST" | "PUT" | "PATCH",
  path: string,
  body?: unknown,
  headers: Record<string, string> = {},
): Promise<T> {
  const response = await request.fetch(`/api${path}`, {
    method,
    data: body,
    headers: { "Sec-Fetch-Site": "same-origin", ...headers },
  });
  expect(response.ok(), `${method} ${path}: ${response.status()} ${await response.text()}`).toBe(true);
  return (await response.json()) as T;
}
