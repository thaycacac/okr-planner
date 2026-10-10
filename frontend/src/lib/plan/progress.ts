import type { PlanEvent, PlanRunDetail, PlanRunStatus, PlanStage } from "@/lib/api/types";

export const STAGES: readonly PlanStage[] = ["precheck", "clarify", "decompose", "dedup", "validate", "schedule"];

export type StageState = "pending" | "running" | "done" | "skipped" | "failed";
export type KrState = "waiting" | "running" | "retry" | "done" | "failed";
export type KrProgress = { state: KrState; attempt: number; durationMs: number | null };

export type ProgressState = {
  /** Highest seq folded in from the event stream. */
  lastSeq: number;
  /** Highest seq seen in a polled snapshot; kept apart so a stream replay still fills in history. */
  snapshotSeq: number;
  percent: number;
  runStatus: PlanRunStatus;
  stages: Record<PlanStage, StageState>;
  krs: Record<number, KrProgress>;
  decomposed: { completed: number; total: number } | null;
  ended: boolean;
};

export const ACTIVE_RUN_STATUSES: readonly PlanRunStatus[] = ["queued", "running"];

export function isActive(status: PlanRunStatus) {
  return ACTIVE_RUN_STATUSES.includes(status);
}

export function initialProgress(runStatus: PlanRunStatus = "queued"): ProgressState {
  return {
    lastSeq: 0,
    snapshotSeq: 0,
    percent: 0,
    runStatus,
    stages: Object.fromEntries(STAGES.map((s) => [s, "pending"])) as Record<PlanStage, StageState>,
    krs: {},
    decomposed: null,
    ended: !isActive(runStatus),
  };
}

function closeEarlierStages(stages: Record<PlanStage, StageState>, stage: PlanStage) {
  const index = STAGES.indexOf(stage);
  const next = { ...stages };
  for (const earlier of STAGES.slice(0, index)) {
    if (next[earlier] === "pending" || next[earlier] === "running") next[earlier] = "done";
  }
  return next;
}

function krState(status: PlanEvent["status"]): KrState | null {
  switch (status) {
    case "started":
      return "running";
    case "retry":
      return "retry";
    case "completed":
      return "done";
    case "failed":
      return "failed";
    default:
      return null;
  }
}

/** Folds one event in; replays (seq already seen) are ignored so SSE reconnects are harmless. */
export function applyEvent(state: ProgressState, event: PlanEvent): ProgressState {
  if (event.seq <= state.lastSeq) return state;
  let { stages, krs, decomposed } = state;

  if (event.stage && event.status) {
    stages = closeEarlierStages(stages, event.stage);
    const stageState: StageState =
      event.status === "skipped"
        ? "skipped"
        : event.status === "failed"
          ? "failed"
          : event.status === "completed" && event.key_result_id === null && event.objective_id === null
            ? "done"
            : "running";
    stages = { ...stages, [event.stage]: stageState };

    if (event.stage === "decompose") {
      if (event.total !== null) decomposed = { completed: event.completed ?? 0, total: event.total };
      if (decomposed && decomposed.total > 0 && decomposed.completed >= decomposed.total) {
        stages = { ...stages, decompose: "done" };
      }
      const next = krState(event.status);
      if (event.key_result_id !== null && next) {
        const previous = krs[event.key_result_id];
        krs = {
          ...krs,
          [event.key_result_id]: {
            state: next,
            attempt: event.attempt ?? previous?.attempt ?? 1,
            durationMs: event.duration_ms ?? previous?.durationMs ?? null,
          },
        };
      }
    }
  }

  const ended = event.type === "end";
  const pastDecompose =
    (event.stage !== null && STAGES.indexOf(event.stage) > STAGES.indexOf("decompose")) ||
    event.run_status === "succeeded";
  if (pastDecompose && stages.decompose !== "skipped") {
    // A snapshot may skip the per-KR completions, but later stages only run once every KR decomposed.
    krs = Object.fromEntries(
      Object.entries(krs).map(([id, kr]) => [id, kr.state === "failed" ? kr : { ...kr, state: "done" as const }]),
    );
    if (decomposed) decomposed = { completed: decomposed.total, total: decomposed.total };
  }
  if (ended && event.run_status === "succeeded") {
    stages = Object.fromEntries(
      STAGES.map((s) => [s, stages[s] === "skipped" ? "skipped" : "done"]),
    ) as Record<PlanStage, StageState>;
  }

  return {
    lastSeq: event.seq,
    snapshotSeq: state.snapshotSeq,
    percent: Math.max(state.percent, event.percent),
    runStatus: event.run_status,
    stages,
    krs,
    decomposed,
    ended: ended || !isActive(event.run_status),
  };
}

/**
 * Folds in the latest event carried by a polled run detail. The stream replays every event from
 * the start, so a snapshot must not advance `lastSeq` or the replayed per-KR events would be dropped.
 */
export function applySnapshot(state: ProgressState, event: PlanEvent): ProgressState {
  if (event.seq <= state.lastSeq || event.seq <= state.snapshotSeq) return state;
  return { ...applyEvent(state, event), lastSeq: state.lastSeq, snapshotSeq: event.seq };
}

type RunHistory = Pick<PlanRunDetail, "status" | "progress" | "steps" | "stage_duration_ms" | "error">;

/**
 * Folds in a polled run detail. Finished runs also carry per-stage/per-KR traces, which restore the
 * history a late visitor (or a polling-only client) never saw as events.
 */
export function applyDetail(state: ProgressState, detail: RunHistory): ProgressState {
  const next = detail.progress ? applySnapshot(state, detail.progress) : state;
  if (detail.steps.length === 0) return next;
  const failure = detail.status === "failed" ? detail.error : null;

  const stages = { ...next.stages };
  for (const stage of STAGES) {
    const finished = detail.stage_duration_ms[stage] !== undefined;
    if (finished && stage !== failure?.step && (stages[stage] === "pending" || stages[stage] === "running")) {
      stages[stage] = "done";
    }
  }

  const krs = { ...next.krs };
  let completed = 0;
  for (const trace of detail.steps) {
    if (trace.step !== "decompose" || trace.key_result_id === null) continue;
    const failed = failure?.step === "decompose" && failure.key_result_id === trace.key_result_id;
    if (!failed) completed += 1;
    krs[trace.key_result_id] = {
      state: failed ? "failed" : "done",
      attempt: Math.max(trace.attempts, 1),
      durationMs: trace.duration_ms,
    };
  }
  const total = Math.max(next.decomposed?.total ?? 0, completed);
  const decomposed = total > 0 ? { completed, total } : next.decomposed;
  return { ...next, stages, krs, decomposed };
}

export function currentStage(state: ProgressState): PlanStage | null {
  return STAGES.find((s) => state.stages[s] === "running") ?? null;
}
