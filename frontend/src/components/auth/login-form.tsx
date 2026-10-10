"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useId, useRef, useState } from "react";
import { EyeIcon, EyeOffIcon, InfoIcon, LockIcon } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { api, apiMockEnabled, CROSS_SITE_REQUEST_CODE } from "@/lib/api/client";
import { MOCK_PASSWORD } from "@/lib/api/mock-config";
import { errorDetail } from "@/lib/api/types";

type FormError =
  | { kind: "required" }
  | { kind: "invalid"; attemptsLeft: number | null }
  | { kind: "offline" }
  | { kind: "crossSite" };

export function formatCountdown(totalSeconds: number) {
  const s = Math.max(0, Math.ceil(totalSeconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

type Lock = { until: number; now: number; seconds: number };

function useLock() {
  const [lock, setLock] = useState<Lock | null>(null);
  const locked = lock !== null && lock.now < lock.until;

  useEffect(() => {
    if (!locked) return;
    const id = window.setInterval(() => {
      setLock((current) => current && { ...current, now: Date.now() });
    }, 1000);
    return () => window.clearInterval(id);
  }, [locked]);

  return {
    lock,
    locked,
    // Starting from the same instant as the deadline keeps the first frame at the full duration.
    start(seconds: number) {
      const now = Date.now();
      setLock({ until: now + seconds * 1000, now, seconds });
    },
    clear() {
      setLock(null);
    },
    secondsLeft: lock ? Math.max(0, (lock.until - lock.now) / 1000) : 0,
  };
}

export function LoginForm({ next, expired }: { next: string; expired: boolean }) {
  const t = useTranslations("auth");
  const tc = useTranslations("common");
  const router = useRouter();
  const inputId = useId();
  const errorId = useId();
  const [password, setPassword] = useState("");
  const [visible, setVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<FormError | null>(null);
  const { lock, locked, start: startLock, clear: clearLock, secondsLeft } = useLock();
  const unlocked = lock !== null && !locked;
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (unlocked) inputRef.current?.focus();
  }, [unlocked]);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (locked || submitting) return;
    clearLock();
    if (!password) {
      setError({ kind: "required" });
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const { response, error: body } = await api.POST("/auth/login", { body: { password } });
      if (response.ok) {
        router.replace(next);
        return;
      }
      const detail = errorDetail(body);
      if (response.status === 429) {
        const retry = detail?.retry_after_seconds ?? Number(response.headers.get("Retry-After") ?? 60);
        startLock(retry);
        setPassword("");
      } else if (response.status === 401) {
        setError({ kind: "invalid", attemptsLeft: detail?.attempts_left ?? null });
        setPassword("");
      } else if (response.status === 403 && detail?.code === CROSS_SITE_REQUEST_CODE) {
        setError({ kind: "crossSite" });
      } else {
        setError({ kind: "offline" });
      }
    } catch {
      setError({ kind: "offline" });
    }
    setSubmitting(false);
  }

  const fieldError =
    error?.kind === "required"
      ? t("required")
      : error?.kind === "invalid"
        ? error.attemptsLeft === null
          ? t("invalid")
          : t("invalidWithAttempts", { count: error.attemptsLeft })
        : null;

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-5">
      {/* Kept mounted so the lock and unlock are each announced once, not on every tick. */}
      <div role="status" className="sr-only">
        {locked && lock
          ? t("lockedAnnounce", { seconds: lock.seconds })
          : unlocked
            ? t("unlocked")
            : null}
      </div>
      {expired && !error && !lock && (
        <Alert role="note">
          <InfoIcon aria-hidden />
          <AlertDescription>{t("expired")}</AlertDescription>
        </Alert>
      )}
      {locked && (
        <Alert variant="destructive" role="note" aria-hidden>
          <LockIcon aria-hidden />
          <AlertTitle>{t("lockedTitle")}</AlertTitle>
          <AlertDescription>
            {t("lockedBody", { time: formatCountdown(secondsLeft) })}
          </AlertDescription>
        </Alert>
      )}
      {error?.kind === "offline" && (
        <Alert variant="destructive">
          <AlertDescription>{tc("serverUnreachable")}</AlertDescription>
        </Alert>
      )}
      {error?.kind === "crossSite" && (
        <Alert variant="destructive">
          <AlertDescription>{tc("crossSiteRequest")}</AlertDescription>
        </Alert>
      )}

      <Field data-invalid={fieldError ? true : undefined}>
        <FieldLabel htmlFor={inputId}>{t("password")}</FieldLabel>
        <div className="relative">
          <Input
            ref={inputRef}
            id={inputId}
            name="password"
            type={visible ? "text" : "password"}
            autoComplete="current-password"
            autoFocus
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={locked}
            aria-invalid={fieldError ? true : undefined}
            aria-describedby={fieldError ? errorId : undefined}
            className="h-11 pr-20"
          />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="absolute top-1/2 right-1.5 -translate-y-1/2"
            onClick={() => setVisible((v) => !v)}
            aria-pressed={visible}
            aria-controls={inputId}
            aria-label={t("showPassword")}
          >
            {visible ? <EyeOffIcon aria-hidden /> : <EyeIcon aria-hidden />}
            <span aria-hidden>{visible ? t("hide") : t("show")}</span>
          </Button>
        </div>
        <FieldError id={errorId}>{fieldError}</FieldError>
      </Field>

      <Button type="submit" size="lg" className="h-11 w-full" disabled={locked || submitting}>
        {submitting && <Spinner aria-hidden role="presentation" />}
        {submitting ? t("submitting") : t("submit")}
      </Button>

      <p className="text-center text-sm text-muted-foreground">{t("forgot")}</p>
      {apiMockEnabled && (
        <p className="text-center text-xs text-muted-foreground">
          {t("mockHint", { password: MOCK_PASSWORD })}
        </p>
      )}
    </form>
  );
}
