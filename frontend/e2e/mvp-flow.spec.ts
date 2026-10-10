import { apiCall, expect, signIn, test } from "./fixtures";

/** Must match `CLARIFY_QUESTION` in `backend/tests/e2e_server.py`. */
const CLARIFY_QUESTION = "Bạn dành được bao nhiêu giờ mỗi ngày cho các OKR này?";

type Schedule = { tasks: { task_id: number; allocations: { date: string; minutes: number }[] }[] };
type Quarter = { id: number; year: number; number: number };

test("a new user goes from sign-in through quarter, OKR and clarification to a schedule", async ({ page }) => {
  await signIn(page, "/plan/new");

  await expect(page).toHaveURL(/\/plan\/new$/);
  await page.getByRole("button", { name: "Next: enter OKRs" }).click();

  await expect(page).toHaveURL(/\/plan\/new\/okr\?q=(\d{4})-Q(\d)/);
  const slug = new URL(page.url()).searchParams.get("q")!;
  await page.getByRole("button", { name: "Fill in an example" }).click();
  await page.getByRole("button", { name: "Submit & generate plan" }).click();

  await expect(page).toHaveURL(/\/plan\/new\/generate\?job=/);
  await expect(page.getByRole("progressbar", { name: "Plan generation progress" })).toBeVisible();

  await expect(page).toHaveURL(/\/plan\/new\/clarify\?job=/);
  await page.getByLabel(CLARIFY_QUESTION).fill("Khoảng 4 giờ mỗi ngày, từ thứ Hai đến thứ Sáu.");
  await page.getByRole("button", { name: "Submit answers" }).click();

  await expect(page).toHaveURL(/\/plan\/new\/generate\?job=/);
  await expect(page.getByRole("progressbar", { name: "Plan generation progress" })).toBeVisible();
  await expect(page.getByText(/\d+\/\d+ KRs done/)).toBeVisible();

  await expect(page).toHaveURL(new RegExp(`/q/${slug}/tasks`), { timeout: 60_000 });
  const table = page.getByRole("table", { name: "Objectives, KRs and tasks" });
  await expect(table).toBeVisible();
  await expect(table.getByText(/Task t1 for kr\d+/).first()).toBeVisible();

  const [year, number] = slug.split("-Q").map(Number);
  const quarters = await apiCall<Quarter[]>(page.request, "GET", "/quarters");
  const quarter = quarters.find((q) => q.year === year && q.number === number)!;
  const schedule = await apiCall<Schedule>(page.request, "GET", `/quarters/${quarter.id}/schedule`);
  expect(schedule.tasks.length).toBeGreaterThan(0);
  expect(schedule.tasks.every((task) => task.allocations.length > 0)).toBe(true);

  await page.getByRole("navigation", { name: "View" }).getByRole("link", { name: "Calendar" }).click();
  await expect(page).toHaveURL(new RegExp(`/q/${slug}/calendar`));
  await expect(page.getByText(/Task t1 for kr\d+/).first()).toBeVisible();
  await test.info().attach("calendar", { body: await page.screenshot(), contentType: "image/png" });
});
