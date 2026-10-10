import type { ApiClient } from "@/lib/api/client";
import type { KeyResultCreate, ObjectivePriority, QuarterDetail, QuarterSummary } from "@/lib/api/types";

import { fromQuarterDetail, type OkrDraft, toKeyResultBody } from "./okr-draft";
import { findQuarter, type QuarterRef } from "./quarter";

type KrBody = Required<KeyResultCreate>;

export type SyncOp =
  | { type: "deleteKr"; id: number }
  | { type: "deleteObjective"; id: number }
  | { type: "updateObjective"; id: number; body: { title: string; priority: ObjectivePriority; position: number } }
  | { type: "updateKr"; id: number; body: KrBody }
  | { type: "createKr"; objectiveId: number; body: KrBody }
  | {
      type: "createObjective";
      body: { title: string; priority: ObjectivePriority; position: number; active: boolean; key_results: KrBody[] };
    };

const ORDER: Record<SyncOp["type"], number> = {
  deleteKr: 0,
  deleteObjective: 1,
  updateObjective: 2,
  updateKr: 3,
  createKr: 4,
  createObjective: 5,
};

function sameKr(body: KrBody, server: QuarterDetail["objectives"][number]["key_results"][number]) {
  return (
    body.text === server.text &&
    body.kind === server.kind &&
    body.baseline === server.baseline &&
    body.target === server.target &&
    body.unit === server.unit &&
    body.due_date === server.due_date &&
    body.note === server.note &&
    body.position === server.position
  );
}

/**
 * Minimal set of writes that turns the server's OKR tree into the draft. Ids are kept for
 * everything that still exists so clarification answers and finished tasks stay attached.
 */
export function planSync(draft: OkrDraft, detail: QuarterDetail): SyncOp[] {
  const ops: SyncOp[] = [];
  const server = new Map(detail.objectives.map((o) => [o.id, o]));
  const kept = new Set<number>();

  draft.objectives.forEach((objective, position) => {
    const title = objective.title.trim();
    const bodies = objective.keyResults.map((kr, i) => toKeyResultBody(kr, i));
    const existing = objective.serverId ? server.get(objective.serverId) : undefined;
    if (!existing) {
      ops.push({
        type: "createObjective",
        body: { title, priority: objective.priority, position, active: true, key_results: bodies },
      });
      return;
    }
    kept.add(existing.id);
    if (existing.title !== title || existing.priority !== objective.priority || existing.position !== position) {
      ops.push({
        type: "updateObjective",
        id: existing.id,
        body: { title, priority: objective.priority, position },
      });
    }
    const serverKrs = new Map(existing.key_results.map((kr) => [kr.id, kr]));
    const keptKrs = new Set<number>();
    objective.keyResults.forEach((kr, i) => {
      const current = kr.serverId ? serverKrs.get(kr.serverId) : undefined;
      if (!current) {
        ops.push({ type: "createKr", objectiveId: existing.id, body: bodies[i] });
        return;
      }
      keptKrs.add(current.id);
      if (!sameKr(bodies[i], current)) ops.push({ type: "updateKr", id: current.id, body: bodies[i] });
    });
    for (const kr of existing.key_results) {
      if (!keptKrs.has(kr.id)) ops.push({ type: "deleteKr", id: kr.id });
    }
  });

  for (const objective of detail.objectives) {
    if (!kept.has(objective.id)) ops.push({ type: "deleteObjective", id: objective.id });
  }
  return ops.sort((a, b) => ORDER[a.type] - ORDER[b.type]);
}

export class SyncError extends Error {
  constructor(readonly status: number) {
    super(`sync failed with HTTP ${status}`);
  }
}

function check(response: Response) {
  if (!response.ok) throw new SyncError(response.status);
}

export async function listQuarters(client: ApiClient): Promise<QuarterSummary[]> {
  const { data, response } = await client.GET("/quarters");
  check(response);
  return data ?? [];
}

export async function ensureQuarter(client: ApiClient, ref: QuarterRef): Promise<number> {
  const found = findQuarter(await listQuarters(client), ref);
  if (found) return found.id;
  const { data, response } = await client.POST("/quarters", { body: ref });
  if (data) return data.id;
  if (response.status !== 409) throw new SyncError(response.status);
  const again = findQuarter(await listQuarters(client), ref);
  if (!again) throw new SyncError(response.status);
  return again.id;
}

export async function getQuarterDetail(client: ApiClient, quarterId: number): Promise<QuarterDetail> {
  const { data, response } = await client.GET("/quarters/{quarter_id}", {
    params: { path: { quarter_id: quarterId } },
  });
  check(response);
  return data!;
}

async function apply(client: ApiClient, quarterId: number, op: SyncOp) {
  switch (op.type) {
    case "deleteKr":
      return check((await client.DELETE("/key-results/{kr_id}", { params: { path: { kr_id: op.id } } })).response);
    case "deleteObjective":
      return check(
        (await client.DELETE("/objectives/{objective_id}", { params: { path: { objective_id: op.id } } }))
          .response,
      );
    case "updateObjective":
      return check(
        (
          await client.PATCH("/objectives/{objective_id}", {
            params: { path: { objective_id: op.id } },
            body: op.body,
          })
        ).response,
      );
    case "updateKr":
      return check(
        (await client.PATCH("/key-results/{kr_id}", { params: { path: { kr_id: op.id } }, body: op.body }))
          .response,
      );
    case "createKr":
      return check(
        (
          await client.POST("/objectives/{objective_id}/key-results", {
            params: { path: { objective_id: op.objectiveId } },
            body: op.body,
          })
        ).response,
      );
    case "createObjective":
      return check(
        (
          await client.POST("/quarters/{quarter_id}/objectives", {
            params: { path: { quarter_id: quarterId } },
            body: op.body,
          })
        ).response,
      );
  }
}

/** Saves the draft to the quarter (created on first save) and returns the server's view of it. */
export async function syncDraft(client: ApiClient, ref: QuarterRef, draft: OkrDraft) {
  const quarterId = await ensureQuarter(client, ref);
  const before = await getQuarterDetail(client, quarterId);
  const ops = planSync(draft, before);
  for (const op of ops) await apply(client, quarterId, op);
  const detail = ops.length ? await getQuarterDetail(client, quarterId) : before;
  return { quarterId, detail, draft: fromQuarterDetail(detail, withServerIds(draft, detail)) };
}

/** Matches newly created objectives to their server ids by position, to carry their context. */
function withServerIds(draft: OkrDraft, detail: QuarterDetail): OkrDraft {
  const sorted = [...detail.objectives].sort((a, b) => a.position - b.position);
  return {
    ...draft,
    objectives: draft.objectives.map((o, i) => ({ ...o, serverId: sorted[i]?.id ?? o.serverId })),
  };
}
