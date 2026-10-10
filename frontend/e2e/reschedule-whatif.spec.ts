import type { APIRequestContext } from "@playwright/test";

import { apiCall, expect, signIn, test } from "./fixtures";

type Objective = { id: number; key_results: { id: number }[] };
type Schedule = { feasibility: { status: string }; unscheduled: unknown[] };
type RescheduleResult = { applied: boolean; schedule: Schedule };

const SLUG = "2027-Q1";
const KEEP = "Ship the Team plan";
const PAUSE = "Refresh the help center";

async function addTasks(request: APIRequestContext, krId: number, count: number) {
  for (let i = 1; i <= count; i++) {
    await apiCall(request, "POST", `/key-results/${krId}/tasks`, {
      title: `Work package ${krId}.${i}`,
      estimate_minutes: 360,
    });
  }
}

/** A future quarter holding ~390h of 6-hour tasks against ~230h of working time. */
async function overloadedQuarter(request: APIRequestContext) {
  const quarter = await apiCall<{ id: number }>(request, "POST", "/quarters", { year: 2027, number: 1 });
  const objective = async (title: string, priority: string) =>
    apiCall<Objective>(request, "POST", `/quarters/${quarter.id}/objectives`, {
      title,
      priority,
      key_results: [{ text: `${title}: key result`, kind: "binary" }],
    });
  const keep = await objective(KEEP, "high");
  const pause = await objective(PAUSE, "low");
  await addTasks(request, keep.key_results[0].id, 30);
  await addTasks(request, pause.key_results[0].id, 34);
  const result = await apiCall<RescheduleResult>(request, "POST", `/quarters/${quarter.id}/reschedule`, {});
  expect(result.schedule.feasibility.status).toBe("red");
  return { quarterId: quarter.id, pauseKrId: pause.key_results[0].id };
}

test("changing tasks, rescheduling and applying a what-if option clears the overload", async ({ page }) => {
  await signIn(page, "/settings");
  const { quarterId, pauseKrId } = await overloadedQuarter(page.request);
  await addTasks(page.request, pauseKrId, 1);

  await page.goto(`/q/${SLUG}/tasks`);
  const stale = page.getByRole("status").filter({ hasText: "Schedule is out of date" });
  await expect(stale).toBeVisible();
  await stale.getByRole("button", { name: "Reschedule" }).click();

  const preview = page.getByRole("dialog", { name: "Preview new schedule" });
  await expect(preview).toBeVisible();
  await expect(preview.getByText(/Still .+ short/)).toBeVisible();
  await preview.getByRole("button", { name: "Apply", exact: true }).click();
  await expect(preview).toBeHidden();
  await expect(stale).toBeHidden();

  const toast = page.getByText("Schedule updated, but the plan is still overloaded");
  await expect(toast).toBeVisible();
  await page.getByRole("button", { name: "See options" }).click();

  await expect(page).toHaveURL(new RegExp(`/q/${SLUG}/options`));
  await expect(page.getByRole("heading", { name: "Options when overloaded" })).toBeVisible();
  await expect(page.getByText(/needed, only .+ available/)).toBeVisible();

  const before = await apiCall<Schedule>(page.request, "GET", `/quarters/${quarterId}/schedule`);
  await page.getByRole("checkbox", { name: /^Pause O2\b/ }).check();

  const rail = page.getByRole("complementary", { name: "Option preview" });
  await expect(rail.getByText("Preview (1)")).toBeVisible();
  await expect(rail.getByText(/On track|Tight/).first()).toBeVisible();
  const unchanged = await apiCall<Schedule>(page.request, "GET", `/quarters/${quarterId}/schedule`);
  expect(unchanged).toEqual(before);

  await rail.getByRole("button", { name: "Apply options" }).click();
  await expect(page.getByText(/Applied 1 option/)).toBeVisible();
  await test.info().attach("options-applied", { body: await page.screenshot(), contentType: "image/png" });

  const after = await apiCall<Schedule>(page.request, "GET", `/quarters/${quarterId}/schedule`);
  expect(after.feasibility.status).not.toBe("red");
  expect(after.unscheduled).toHaveLength(0);
});
