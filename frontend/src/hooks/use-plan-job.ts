"use client";

import { useCallback, useEffect, useReducer, useState } from "react";

import { api, apiBaseUrl, apiMockEnabled } from "@/lib/api/client";
import type { PlanEvent, PlanRunDetail } from "@/lib/api/types";
import { applyDetail, applyEvent, initialProgress, isActive, type ProgressState } from "@/lib/plan/progress";

const POLL_MS = 2000;
// While SSE is healthy a slow poll still runs, in case a proxy buffers the stream.
const SAFETY_POLL_MS = 10_000;
// The stream replays history on connect, so silence past this means something (e.g. gzip on a
// proxy) is buffering it; polling then gives fresher progress than a stalled stream.
const SSE_FIRST_EVENT_MS = 5000;

type Action =
  | { type: "event"; event: PlanEvent }
  | { type: "detail"; detail: PlanRunDetail }
  | { type: "reset"; detail: PlanRunDetail };

function reducer(state: ProgressState, action: Action): ProgressState {
  if (action.type === "event") return applyEvent(state, action.event);
  if (action.type === "detail") return applyDetail(state, action.detail);
  return applyDetail(initialProgress(action.detail.status), action.detail);
}

export type JobTransport = "sse" | "polling";
export type JobLoad = "loading" | "ready" | "not_found" | "error";

async function fetchDetail(jobId: string) {
  const { data, response } = await api.GET("/plans/{job_id}", { params: { path: { job_id: jobId } } });
  return { data, status: response.status };
}

export function usePlanJob(jobId: string | null) {
  const [detail, setDetail] = useState<PlanRunDetail | null>(null);
  const [load, setLoad] = useState<JobLoad>("loading");
  const [sseClosedFor, setSseClosedFor] = useState<string | null>(null);
  const [progress, dispatch] = useReducer(reducer, undefined, () => initialProgress());
  const [attempt, setAttempt] = useState(0);
  const active = detail ? isActive(detail.status) : false;
  const sseSupported = !apiMockEnabled && typeof EventSource !== "undefined";
  const transport: JobTransport = sseSupported && sseClosedFor !== jobId ? "sse" : "polling";

  const refresh = useCallback(async () => {
    if (!jobId) return null;
    try {
      const { data, status } = await fetchDetail(jobId);
      if (!data) {
        setLoad(status === 404 ? "not_found" : "error");
        return null;
      }
      setDetail(data);
      setLoad("ready");
      dispatch({ type: "detail", detail: data });
      return data;
    } catch {
      setLoad("error");
      return null;
    }
  }, [jobId]);

  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;
    fetchDetail(jobId).then(
      ({ data, status }) => {
        if (cancelled) return;
        if (!data) {
          setLoad(status === 404 ? "not_found" : "error");
          return;
        }
        setDetail(data);
        setLoad("ready");
        dispatch({ type: "reset", detail: data });
      },
      () => {
        if (!cancelled) setLoad("error");
      },
    );
    return () => {
      cancelled = true;
    };
  }, [jobId, attempt]);

  useEffect(() => {
    if (!jobId || !active || transport !== "sse") return;
    const source = new EventSource(`${apiBaseUrl}/plans/${encodeURIComponent(jobId)}/events`);
    let stallTimer: number | undefined = window.setTimeout(() => {
      source.close();
      setSseClosedFor(jobId);
    }, SSE_FIRST_EVENT_MS);
    const onMessage = (message: MessageEvent<string>) => {
      window.clearTimeout(stallTimer);
      stallTimer = undefined;
      try {
        const event = JSON.parse(message.data) as PlanEvent;
        dispatch({ type: "event", event });
        if (event.type === "end") {
          source.close();
          void refresh();
        }
      } catch {
        // A malformed frame is skipped; polling still reconciles the state.
      }
    };
    source.addEventListener("progress", onMessage);
    source.addEventListener("end", onMessage);
    source.onerror = () => {
      // EventSource retries by itself (resuming with Last-Event-ID); it only gives up when closed.
      if (source.readyState === EventSource.CLOSED) setSseClosedFor(jobId);
    };
    return () => {
      window.clearTimeout(stallTimer);
      source.close();
    };
  }, [jobId, active, transport, refresh]);

  useEffect(() => {
    if (!jobId || !active) return;
    const timer = window.setInterval(() => void refresh(), transport === "polling" ? POLL_MS : SAFETY_POLL_MS);
    return () => window.clearInterval(timer);
  }, [jobId, active, transport, refresh]);

  const retry = useCallback(() => {
    setLoad("loading");
    setAttempt((n) => n + 1);
  }, []);

  return { detail, load, progress, transport, refresh, retry };
}
