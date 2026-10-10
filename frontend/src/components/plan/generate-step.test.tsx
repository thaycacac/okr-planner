import "@testing-library/jest-dom/vitest";

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import vi_messages from "../../../messages/vi.json";
import type { PlanRunDetail, QuarterDetail } from "@/lib/api/types";

import { GenerateStep } from "./generate-step";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, replace: vi.fn() }) }));

const backend = vi.hoisted(() => ({
  resumable: true,
  status: "failed" as PlanRunDetail["status"],
  parentId: null as string | null,
  skipClarification: false,
  steps: [] as PlanRunDetail["steps"],
  resume: { status: 202, body: {} as unknown },
  resumeCalls: 0,
}));

const QUARTER: QuarterDetail = {
  id: 7,
  year: 2026,
  number: 4,
  start_date: "2026-10-01",
  end_date: "2026-12-31",
  plan_start: null,
  objective_count: 1,
  key_result_count: 2,
  task_count: 0,
  latest_plan_run_id: "run-1",
  latest_plan_status: "failed",
  created_at: "2026-09-30T00:00:00Z",
  objectives: [
    {
      id: 1,
      quarter_id: 7,
      title: "Ship onboarding",
      priority: "high",
      position: 0,
      active: true,
      key_results: [1, 2].map((id) => ({
        id,
        objective_id: 1,
        text: `KR text ${id}`,
        kind: "numeric" as const,
        baseline: null,
        target: null,
        unit: null,
        due_date: null,
        note: null,
        position: id - 1,
        active: true,
        tasks: [],
      })),
    },
  ],
};

function failedRun(): PlanRunDetail {
  return {
    id: "run-1",
    quarter_id: 7,
    parent_id: backend.parentId,
    status: backend.status,
    round: 1,
    skip_clarification: backend.skipClarification,
    language: "vi",
    provider: "local",
    models: { decompose: "qwen" },
    total_retries: 0,
    stage_duration_ms: {},
    duration_ms: 1000,
    steps: backend.steps,
    questions: [],
    clarifications: [],
    issues: [],
    error: {
      code: "provider_unavailable",
      step: "decompose",
      message: "connection refused",
      provider: "local",
      model: "qwen",
      objective_id: 1,
      key_result_id: 2,
      attempts: 3,
      errors: [],
      suggestions: [],
    },
    resumable: backend.resumable,
    task_count: 0,
    schedule_run_id: null,
    progress: null,
    created_at: "2026-10-01T00:00:00Z",
    started_at: "2026-10-01T00:00:00Z",
    finished_at: "2026-10-01T00:00:01Z",
  };
}

vi.mock("@/lib/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/client")>();
  return {
    ...actual,
    apiMockEnabled: false,
    api: actual.createApiClient({
      baseUrl: "http://api.test",
      fetch: async (request) => {
        const { pathname } = new URL(request.url);
        if (request.method === "POST" && pathname === "/plans/run-1/resume") {
          backend.resumeCalls += 1;
          return Response.json(backend.resume.body, { status: backend.resume.status });
        }
        if (pathname === "/plans/run-1") return Response.json(failedRun());
        if (pathname === "/quarters/7") return Response.json(QUARTER);
        return Response.json({ detail: { code: "not_found", message: "" } }, { status: 404 });
      },
      onUnauthorized: () => {},
    }),
  };
});

const KR1_DONE: PlanRunDetail["steps"] = [
  {
    step: "decompose",
    model: "qwen",
    objective_id: 1,
    key_result_id: 1,
    attempts: 1,
    retries: 0,
    duration_ms: 4000,
    errors: [],
  },
];

const DRAFT_KEY = "okr-planner.draft.2026-Q4";
const DRAFT_NOTICE = /Bạn có bản nháp OKR chưa gửi/;
const FRESH_HINT = /Chưa có KR nào phân rã xong/;

function storeDraft(synced: boolean) {
  window.localStorage.setItem(DRAFT_KEY, JSON.stringify({ objectives: [], synced, savedAt: 1 }));
}

function renderStep() {
  return render(
    <NextIntlClientProvider locale="vi" messages={vi_messages}>
      <GenerateStep jobId="run-1" />
    </NextIntlClientProvider>,
  );
}

describe("GenerateStep resume", () => {
  beforeEach(() => {
    push.mockReset();
    backend.resumable = true;
    backend.status = "failed";
    backend.parentId = null;
    backend.skipClarification = false;
    backend.steps = KR1_DONE;
    backend.resumeCalls = 0;
    window.localStorage.clear();
    backend.resume = {
      status: 202,
      body: { job_id: "run-2", quarter_id: 7, parent_id: "run-1", status: "queued", round: 1 },
    };
  });
  afterEach(cleanup);

  it("offers resuming next to regenerating and opens the new run", async () => {
    renderStep();
    const resume = await screen.findByRole("button", { name: "Chạy tiếp từ KR lỗi" });
    expect(screen.getByRole("button", { name: "Sinh lại từ đầu" })).toBeInTheDocument();
    expect(screen.getByText(/Chạy tiếp giữ các KR đã phân rã xong/)).toBeInTheDocument();
    expect(screen.queryByText("Các KR đã xong sẽ được phân rã lại.")).not.toBeInTheDocument();

    fireEvent.click(resume);
    await waitFor(() => expect(push).toHaveBeenCalledWith("/plan/new/generate?job=run-2"));
  });

  it("hides the resume button when the run is not resumable", async () => {
    backend.resumable = false;
    renderStep();
    expect(await screen.findByRole("button", { name: "Sinh lại từ đầu" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Chạy tiếp từ KR lỗi" })).not.toBeInTheDocument();
    expect(screen.getByText("Các KR đã xong sẽ được phân rã lại.")).toBeInTheDocument();
  });

  it("says resuming redoes every KR when none was decomposed yet", async () => {
    backend.steps = [];
    renderStep();
    expect(await screen.findByText(FRESH_HINT)).toBeInTheDocument();
    expect(screen.queryByText(/Chạy tiếp giữ các KR đã phân rã xong/)).not.toBeInTheDocument();
    expect(screen.getByText("0/2 KR xong")).toBeInTheDocument();
    expect(screen.getByText(/\(0\/2\)/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Chạy tiếp từ KR lỗi" })).toBeInTheDocument();
  });

  it("keeps the usual hint for a resumed run, whose reused KRs leave no trace", async () => {
    backend.steps = [];
    backend.parentId = "run-0";
    backend.skipClarification = true;
    renderStep();
    expect(await screen.findByText(/Chạy tiếp giữ các KR đã phân rã xong/)).toBeInTheDocument();
    expect(screen.queryByText(FRESH_HINT)).not.toBeInTheDocument();
    expect(screen.queryByText("0/2 KR xong")).not.toBeInTheDocument();
  });

  it("warns that an unsubmitted OKR draft is not used", async () => {
    storeDraft(false);
    renderStep();
    await screen.findByRole("button", { name: "Chạy tiếp từ KR lỗi" });
    expect(screen.getByText(DRAFT_NOTICE)).toBeInTheDocument();
  });

  it("does not warn when the draft matches the saved OKR", async () => {
    storeDraft(true);
    renderStep();
    await screen.findByRole("button", { name: "Chạy tiếp từ KR lỗi" });
    expect(screen.queryByText(DRAFT_NOTICE)).not.toBeInTheDocument();
  });

  it("warns about an unsubmitted draft on a cancelled run too", async () => {
    backend.status = "cancelled";
    storeDraft(false);
    renderStep();
    await screen.findByRole("button", { name: "Sinh lại từ đầu" });
    expect(screen.getByText(DRAFT_NOTICE)).toBeInTheDocument();
  });

  it("counts every planned KR when a finished run is reopened", async () => {
    renderStep();
    expect(await screen.findByText("1/2 KR xong")).toBeInTheDocument();
    expect(screen.getByText(/\(1\/2\)/)).toBeInTheDocument();
  });

  it("explains okr_changed and falls back to regenerating", async () => {
    backend.resume = {
      status: 409,
      body: { detail: { code: "okr_changed", message: "the OKR changed" } },
    };
    renderStep();
    fireEvent.click(await screen.findByRole("button", { name: "Chạy tiếp từ KR lỗi" }));
    backend.resumable = false;

    expect(await screen.findByRole("alert")).toHaveTextContent(/OKR đã được sửa sau lần chạy lỗi/);
    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "Chạy tiếp từ KR lỗi" })).not.toBeInTheDocument(),
    );
    expect(screen.getByRole("button", { name: "Sinh lại từ đầu" })).toBeEnabled();
    expect(backend.resumeCalls).toBe(1);
    expect(push).not.toHaveBeenCalled();
  });
});
