import { describe, expect, it } from "vitest";

import type { PlanEvent, PlanStepTrace } from "@/lib/api/types";

import { applyDetail, applyEvent, applySnapshot, currentStage, initialProgress } from "./progress";

let seq = 0;
function event(overrides: Partial<PlanEvent>): PlanEvent {
  seq += 1;
  return {
    seq,
    type: "progress",
    run_status: "running",
    stage: null,
    status: null,
    objective_id: null,
    key_result_id: null,
    attempt: null,
    completed: null,
    total: null,
    duration_ms: null,
    percent: 0,
    ...overrides,
  };
}

describe("applyEvent", () => {
  it("tracks stages, per-KR state and the overall percentage", () => {
    let state = initialProgress();
    state = applyEvent(state, event({ stage: "precheck", status: "started" }));
    state = applyEvent(state, event({ stage: "clarify", status: "skipped", percent: 20 }));
    expect(state.stages.precheck).toBe("done");
    expect(state.stages.clarify).toBe("skipped");

    state = applyEvent(state, event({ stage: "decompose", status: "started", completed: 0, total: 2, percent: 20 }));
    state = applyEvent(state, event({ stage: "decompose", status: "started", key_result_id: 5, completed: 0, total: 2 }));
    state = applyEvent(state, event({ stage: "decompose", status: "retry", key_result_id: 5, attempt: 2 }));
    expect(state.krs[5]).toEqual({ state: "retry", attempt: 2, durationMs: null });
    expect(currentStage(state)).toBe("decompose");

    state = applyEvent(
      state,
      event({ stage: "decompose", status: "completed", key_result_id: 5, completed: 1, total: 2, duration_ms: 900, percent: 50 }),
    );
    state = applyEvent(
      state,
      event({ stage: "decompose", status: "completed", key_result_id: 6, completed: 2, total: 2, percent: 80 }),
    );
    expect(state.krs[5]).toEqual({ state: "done", attempt: 2, durationMs: 900 });
    expect(state.stages.decompose).toBe("done");
    expect(state.decomposed).toEqual({ completed: 2, total: 2 });
    expect(state.percent).toBe(80);

    state = applyEvent(state, event({ type: "end", run_status: "succeeded", percent: 100 }));
    expect(state.ended).toBe(true);
    expect(Object.values(state.stages)).toEqual(["done", "skipped", "done", "done", "done", "done"]);
  });

  it("ignores replayed events and never lowers the percentage", () => {
    let state = initialProgress();
    const first = event({ stage: "precheck", status: "started", percent: 30 });
    state = applyEvent(state, first);
    expect(applyEvent(state, first)).toBe(state);
    state = applyEvent(state, event({ stage: "clarify", status: "started", percent: 10 }));
    expect(state.percent).toBe(30);
  });

  it("marks a failed KR and ends on a failed run", () => {
    let state = initialProgress();
    state = applyEvent(state, event({ stage: "decompose", status: "failed", key_result_id: 8, attempt: 3 }));
    expect(state.krs[8].state).toBe("failed");
    expect(state.stages.decompose).toBe("failed");
    state = applyEvent(state, event({ type: "end", run_status: "failed" }));
    expect(state.ended).toBe(true);
    expect(state.runStatus).toBe("failed");
  });
});

describe("applySnapshot", () => {
  it("lets the replayed stream fill in per-KR history after a polled snapshot", () => {
    const krOneDone = event({ stage: "decompose", status: "completed", key_result_id: 1, completed: 1, total: 2, duration_ms: 900 });
    const krTwoDone = event({ stage: "decompose", status: "completed", key_result_id: 2, completed: 2, total: 2 });
    const dedup = event({ stage: "dedup", status: "started", percent: 80 });

    let state = applySnapshot(initialProgress("running"), dedup);
    expect(state.percent).toBe(80);
    expect(state.lastSeq).toBe(0);
    expect(state.krs[1]).toBeUndefined();

    state = applyEvent(state, krOneDone);
    state = applyEvent(state, krTwoDone);
    state = applyEvent(state, dedup);
    expect(state.krs[1]).toEqual({ state: "done", attempt: 1, durationMs: 900 });
    expect(state.krs[2]?.state).toBe("done");
    expect(currentStage(state)).toBe("dedup");
    expect(state.percent).toBe(80);
  });

  it("closes KRs still retrying once a snapshot shows a later stage", () => {
    let state = applyEvent(initialProgress("running"), event({ stage: "decompose", status: "started", completed: 0, total: 2 }));
    state = applyEvent(state, event({ stage: "decompose", status: "completed", key_result_id: 1, completed: 1, total: 2 }));
    state = applyEvent(state, event({ stage: "decompose", status: "retry", key_result_id: 2, attempt: 2 }));
    event({ stage: "decompose", status: "completed", key_result_id: 2, completed: 2, total: 2 });

    state = applySnapshot(state, event({ stage: "dedup", status: "started", percent: 80 }));
    expect(state.krs[2]).toEqual({ state: "done", attempt: 2, durationMs: null });
    expect(state.decomposed).toEqual({ completed: 2, total: 2 });
    expect(state.stages.decompose).toBe("done");
    expect(currentStage(state)).toBe("dedup");
  });

  it("restores stage and KR history from the traces of a finished run", () => {
    const trace = (step: PlanStepTrace["step"], key_result_id: number | null, attempts: number, duration_ms: number) => ({
      step,
      model: "llama3.1:8b",
      objective_id: 1,
      key_result_id,
      attempts,
      retries: attempts - 1,
      duration_ms,
      errors: [],
    });
    const state = applyDetail(initialProgress("failed"), {
      status: "failed",
      progress: event({ type: "end", run_status: "failed", percent: 80 }),
      stage_duration_ms: { precheck: 0, clarify: 1000, decompose: 5000 },
      steps: [trace("precheck", null, 0, 0), trace("decompose", 1, 1, 2000), trace("decompose", 2, 2, 4000), trace("dedup", null, 3, 9000)],
      error: {
        code: "invalid_llm_output",
        step: "dedup",
        message: "model output still invalid after 2 retries",
        provider: "local",
        model: "llama3.1:8b",
        objective_id: 1,
        key_result_id: null,
        attempts: 3,
        errors: [],
        suggestions: ["switch_model"],
      },
    });
    expect(state.stages).toMatchObject({ precheck: "done", clarify: "done", decompose: "done", dedup: "pending" });
    expect(state.krs[2]).toEqual({ state: "done", attempt: 2, durationMs: 4000 });
    expect(state.decomposed).toEqual({ completed: 2, total: 2 });
    expect(state.percent).toBe(80);
  });

  it("ignores snapshots older than what the stream or an earlier snapshot delivered", () => {
    const early = event({ stage: "precheck", status: "started", percent: 2 });
    const later = event({ stage: "clarify", status: "started", percent: 10 });
    const streamed = applyEvent(initialProgress("running"), later);
    expect(applySnapshot(streamed, early)).toBe(streamed);
    const polled = applySnapshot(initialProgress("running"), later);
    expect(applySnapshot(polled, early)).toBe(polled);
  });
});
