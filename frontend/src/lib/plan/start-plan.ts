import type { ApiClient } from "@/lib/api/client";
import { errorDetail, type ErrorDetail, type PlanJob } from "@/lib/api/types";

import { buildContext, type ContextLabels, loadDraft } from "./okr-draft";

/** Starts a fresh run for the quarter, reusing the context of the locally saved draft. */
export async function startPlan(
  client: ApiClient,
  quarterId: number,
  slug: string,
  labels: ContextLabels,
): Promise<{ job: PlanJob } | { error: ErrorDetail | null; status: number }> {
  const draft = loadDraft(slug);
  const context = draft ? buildContext(draft, labels) : null;
  const { data, error, response } = await client.POST("/plans", {
    body: { quarter_id: quarterId, context, skip_clarification: false },
  });
  if (data) return { job: data };
  return { error: errorDetail(error), status: response.status };
}
