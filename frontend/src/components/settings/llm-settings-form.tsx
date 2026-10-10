"use client";

import { useFormatter, useTranslations } from "next-intl";
import { useId, useRef, useState } from "react";
import { CheckCircle2Icon, CircleAlertIcon, TriangleAlertIcon } from "lucide-react";

import { useUnsavedChanges } from "@/components/app-shell/unsaved-changes";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Field,
  FieldContent,
  FieldDescription,
  FieldError,
  FieldLabel,
  FieldTitle,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { useLoad } from "@/hooks/use-load";
import { api } from "@/lib/api/client";
import {
  errorDetail,
  type LlmProviderName,
  type LlmSettings,
  type LlmTestResult,
  type LocalApiStyle,
} from "@/lib/api/types";

import { LoadError } from "./load-error";
import {
  countChanges,
  type LlmDraft,
  needsRemoteConsent,
  normalize,
  remoteInfo,
  type RemoteProvider,
  toDraft,
  toTestRequest,
  validate,
} from "./llm-model";

const REMOTE_PROVIDERS: RemoteProvider[] = ["openai", "gemini", "claude"];

type SaveStatus = "idle" | "saving" | "saved" | "error" | "openai-not-configured";
type TestState =
  | { kind: "idle" }
  | { kind: "running" }
  | { kind: "done"; result: LlmTestResult; baseUrl: string }
  | { kind: "failed" };

async function fetchLlmSettings() {
  return (await api.GET("/settings/llm")).data;
}

export function LlmSettingsForm() {
  const [state, retry] = useLoad(fetchLlmSettings);
  if (state.status === "error") return <LoadError onRetry={retry} />;
  if (state.status === "loading") return <LlmSkeleton />;
  return <LlmForm initial={state.data} />;
}

function LlmForm({ initial }: { initial: LlmSettings }) {
  const t = useTranslations("settings");
  const tc = useTranslations("common");
  const ids = { heading: useId(), baseUrl: useId(), model: useId(), apiStyle: useId(), models: useId() };
  const [settings, setSettings] = useState(initial);
  const [draft, setDraft] = useState(() => toDraft(initial));
  const [showErrors, setShowErrors] = useState(false);
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [test, setTest] = useState<TestState>({ kind: "idle" });
  const [models, setModels] = useState<string[]>([]);
  const [consentFor, setConsentFor] = useState<RemoteProvider | null>(null);

  const testRun = useRef(0);

  const saved = toDraft(settings);
  const errors = validate(draft);
  const hasErrors = Object.keys(errors).length > 0;
  const changes = countChanges(saved, draft);
  useUnsavedChanges(changes);

  function update(patch: Partial<LlmDraft>) {
    setDraft((d) => ({ ...d, ...patch }));
    setStatus("idle");
    // A result for the previous configuration would be misleading next to the edited one.
    testRun.current += 1;
    setTest({ kind: "idle" });
  }

  function selectProvider(value: string) {
    const next = value as LlmProviderName;
    if (next === draft.provider) return;
    if (next !== "local" && needsRemoteConsent(saved.provider, next)) {
      setConsentFor(next);
      return;
    }
    update({ provider: next });
  }

  async function runTest() {
    if (hasErrors) {
      setShowErrors(true);
      return;
    }
    const request = toTestRequest(draft);
    const run = ++testRun.current;
    setTest({ kind: "running" });
    try {
      const { data } = await api.POST("/settings/llm/test", { body: request });
      if (!data) throw new Error("test failed");
      if (data.available_models.length > 0) setModels(data.available_models);
      if (run === testRun.current) {
        setTest({ kind: "done", result: data, baseUrl: request.local_base_url ?? "" });
      }
    } catch {
      if (run === testRun.current) setTest({ kind: "failed" });
    }
  }

  async function save() {
    if (hasErrors) {
      setShowErrors(true);
      return;
    }
    setStatus("saving");
    try {
      const { data, error } = await api.PUT("/settings/llm", { body: normalize(draft) });
      if (errorDetail(error)?.code === "openai_not_configured") {
        setStatus("openai-not-configured");
        return;
      }
      if (!data) throw new Error("save failed");
      setSettings(data);
      setDraft(toDraft(data));
      setStatus("saved");
    } catch {
      setStatus("error");
    }
  }

  const savedKey =
    draft.provider === "openai" ? settings.openai_api_key_saved : draft.provider === "gemini" ? settings.gemini_api_key_saved : false;
  const consentName = consentFor ? t(`ai.${consentFor}.title`) : "";
  const remote = draft.provider === "local" ? null : remoteInfo(settings, draft.provider);
  const baseUrlError = showErrors && errors.baseUrl ? t("ai.baseUrlInvalid") : null;
  const modelError = showErrors && errors.model ? t("ai.modelRequired") : null;

  return (
    <form
      noValidate
      className="flex max-w-3xl flex-col gap-6"
      onSubmit={(e) => {
        e.preventDefault();
        void save();
      }}
    >
      <div className="flex flex-col gap-1">
        <h2 id={ids.heading} className="text-sm font-semibold">
          {t("ai.provider")}
        </h2>
        <p className="text-sm text-muted-foreground">{t("ai.providerHint")}</p>
      </div>

      <RadioGroup
        aria-labelledby={ids.heading}
        value={draft.provider}
        onValueChange={selectProvider}
        className="grid gap-3 md:grid-cols-2"
      >
        <FieldLabel htmlFor="provider-local">
          <Field orientation="horizontal">
            <RadioGroupItem value="local" id="provider-local" />
            <FieldContent>
              <FieldTitle className="flex-wrap">
                {t("ai.local.title")}
                <Badge variant="secondary" className="bg-success-muted text-success">
                  {t("ai.local.badge")}
                </Badge>
              </FieldTitle>
              <FieldDescription>{t("ai.local.description")}</FieldDescription>
            </FieldContent>
          </Field>
        </FieldLabel>
        {REMOTE_PROVIDERS.map((provider) => (
          <FieldLabel key={provider} htmlFor={`provider-${provider}`}>
            <Field orientation="horizontal">
              <RadioGroupItem value={provider} id={`provider-${provider}`} />
              <FieldContent>
                <FieldTitle>{t(`ai.${provider}.title`)}</FieldTitle>
                <FieldDescription>{t(`ai.${provider}.description`)}</FieldDescription>
              </FieldContent>
            </Field>
          </FieldLabel>
        ))}
      </RadioGroup>

      <Card>
        <CardContent className="flex flex-col gap-5">
          {draft.provider === "local" || !remote ? (
            <div className="grid gap-5 md:grid-cols-2">
              <Field className="md:col-span-2">
                <FieldLabel htmlFor={ids.apiStyle}>{t("ai.apiStyle")}</FieldLabel>
                <Select
                  value={draft.local_api_style}
                  onValueChange={(value) => update({ local_api_style: value as LocalApiStyle })}
                >
                  <SelectTrigger id={ids.apiStyle} className="w-full md:w-96" aria-describedby={`${ids.apiStyle}-hint`}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ollama">{t("ai.apiStyleOllama")}</SelectItem>
                    <SelectItem value="openai_compatible">{t("ai.apiStyleOpenaiCompatible")}</SelectItem>
                  </SelectContent>
                </Select>
                <FieldDescription id={`${ids.apiStyle}-hint`}>{t("ai.apiStyleHint")}</FieldDescription>
              </Field>
              <Field data-invalid={baseUrlError ? true : undefined}>
                <FieldLabel htmlFor={ids.baseUrl}>{t("ai.baseUrl")}</FieldLabel>
                <Input
                  id={ids.baseUrl}
                  type="url"
                  inputMode="url"
                  spellCheck={false}
                  className="font-mono"
                  value={draft.local_base_url}
                  onChange={(e) => update({ local_base_url: e.target.value })}
                  aria-invalid={baseUrlError ? true : undefined}
                  aria-describedby={baseUrlError ? `${ids.baseUrl}-error` : undefined}
                />
                <FieldError id={`${ids.baseUrl}-error`}>{baseUrlError}</FieldError>
              </Field>
              <Field data-invalid={modelError ? true : undefined}>
                <FieldLabel htmlFor={ids.model}>{t("ai.model")}</FieldLabel>
                <Input
                  id={ids.model}
                  list={ids.models}
                  spellCheck={false}
                  autoComplete="off"
                  className="font-mono"
                  value={draft.local_model}
                  onChange={(e) => update({ local_model: e.target.value })}
                  aria-invalid={modelError ? true : undefined}
                  aria-describedby={`${ids.model}-hint${modelError ? ` ${ids.model}-error` : ""}`}
                />
                <datalist id={ids.models}>
                  {models.map((m) => (
                    <option key={m} value={m} />
                  ))}
                </datalist>
                <FieldDescription id={`${ids.model}-hint`}>{t("ai.modelHint")}</FieldDescription>
                <FieldError id={`${ids.model}-error`}>{modelError}</FieldError>
              </Field>
            </div>
          ) : (
            <div className="grid gap-5 md:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <span className="text-sm font-medium">{t("ai.openaiModel")}</span>
                <span className="font-mono text-sm">{remote.model}</span>
                <span className="text-sm text-muted-foreground">{t("ai.openaiModelHint")}</span>
              </div>
              <div className="flex flex-col gap-1.5">
                <span className="text-sm font-medium">
                  {draft.provider === "claude" ? t("ai.claudeCli") : t("ai.apiKey")}
                </span>
                <span>
                  {remote.ready ? (
                    <Badge variant="secondary" className="bg-success-muted text-success">
                      {t("ai.apiKeyConfigured")}
                    </Badge>
                  ) : (
                    <Badge variant="destructive">{t("ai.apiKeyMissing")}</Badge>
                  )}
                </span>
                {draft.provider === "claude" ? (
                  <span className="text-sm text-muted-foreground">{t("ai.claudeCliHint")}</span>
                ) : (
                  <>
                    <Input
                      type="password"
                      autoComplete="off"
                      spellCheck={false}
                      className="font-mono"
                      placeholder={t("ai.apiKeyPlaceholder")}
                      aria-label={t("ai.apiKeyInput")}
                      value={draft[`${draft.provider}_api_key`] ?? ""}
                      onChange={(e) => update({ [`${draft.provider}_api_key`]: e.target.value })}
                    />
                    {savedKey && draft[`${draft.provider}_api_key`] == null && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="w-fit"
                        onClick={() => update({ [`${draft.provider}_api_key`]: "" })}
                      >
                        {t("ai.apiKeyRemove")}
                      </Button>
                    )}
                    {savedKey && draft[`${draft.provider}_api_key`] === "" && (
                      <span className="text-sm text-warning">{t("ai.apiKeyWillRemove")}</span>
                    )}
                    <span className="text-sm text-muted-foreground">
                      {t("ai.apiKeyHint", { envVar: remote.envVar })}
                    </span>
                  </>
                )}
              </div>
              {!remote.ready && (
                <Alert role="note" className="border-warning/40 bg-warning-muted md:col-span-2">
                  <TriangleAlertIcon aria-hidden className="text-warning" />
                  <AlertDescription className="text-foreground/80">
                    {draft.provider === "claude"
                      ? t("ai.claudeMissingWarning")
                      : t("ai.keyMissingWarning", { provider: t(`ai.${draft.provider}.title`), envVar: remote.envVar })}
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}

          <div className="flex flex-col items-start gap-3">
            <Button type="button" variant="outline" onClick={runTest} disabled={test.kind === "running"}>
              {test.kind === "running" && <Spinner aria-hidden role="presentation" />}
              {test.kind === "running" ? t("ai.testing") : t("ai.test")}
            </Button>
            <div aria-live="polite" className="w-full">
              <TestOutcome state={test} />
            </div>
          </div>
        </CardContent>
      </Card>

      <Alert role="note" className="border-warning/40 bg-warning-muted">
        <TriangleAlertIcon aria-hidden className="text-warning" />
        <AlertTitle>{t("ai.noFallbackTitle")}</AlertTitle>
        <AlertDescription className="text-foreground/80">{t("ai.noFallbackBody")}</AlertDescription>
      </Alert>

      {status === "error" && (
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center gap-3">
            <span>{t("saveError")}</span>
            <Button type="submit" size="sm" variant="outline">
              {tc("retry")}
            </Button>
          </AlertDescription>
        </Alert>
      )}
      {status === "openai-not-configured" && (
        <Alert variant="destructive">
          <CircleAlertIcon aria-hidden />
          <AlertDescription>{t("ai.saveOpenaiNotConfigured")}</AlertDescription>
        </Alert>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <div role="status" className="text-sm text-success">
          {status === "saved" && (
            <span className="inline-flex items-center gap-1.5">
              <CheckCircle2Icon className="size-4" aria-hidden />
              {t("saved")}
            </span>
          )}
        </div>
        <span className="flex-1" />
        <Button type="submit" disabled={changes === 0 || status === "saving"} className="w-full sm:w-auto">
          {status === "saving" && <Spinner aria-hidden role="presentation" />}
          {status === "saving" ? t("ai.saving") : t("ai.save")}
        </Button>
      </div>

      <AlertDialog open={consentFor !== null} onOpenChange={(open) => !open && setConsentFor(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t("ai.consentTitle", { provider: consentName })}</AlertDialogTitle>
            <AlertDialogDescription>{t("ai.consentBody", { provider: consentName })}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t("ai.consentCancel")}</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => consentFor && update({ provider: consentFor })}
            >
              {t("ai.consentAccept", { provider: consentName })}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </form>
  );
}

function TestOutcome({ state }: { state: TestState }) {
  const t = useTranslations("settings.ai");
  const tc = useTranslations("common");
  const format = useFormatter();

  if (state.kind === "failed") {
    return (
      <Alert variant="destructive">
        <CircleAlertIcon aria-hidden />
        <AlertDescription>{tc("serverUnreachable")}</AlertDescription>
      </Alert>
    );
  }
  if (state.kind !== "done") return null;

  const { result, baseUrl } = state;
  if (result.ok) {
    const latency = format.number((result.latency_ms ?? 0) / 1000, {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    });
    return (
      <Alert className="border-success/30 bg-success-muted">
        <CheckCircle2Icon aria-hidden className="text-success" />
        <AlertDescription className="text-foreground">
          {t("testOk", { model: result.model, latency })}
        </AlertDescription>
      </Alert>
    );
  }

  const code = result.error_code ?? "unknown";
  const warn = code === "invalid_json";
  return (
    <Alert
      variant={warn ? "default" : "destructive"}
      className={warn ? "border-warning/40 bg-warning-muted" : undefined}
    >
      {warn ? (
        <TriangleAlertIcon aria-hidden className="text-warning" />
      ) : (
        <CircleAlertIcon aria-hidden />
      )}
      <AlertTitle>{t(`testErrorTitles.${code}`)}</AlertTitle>
      <AlertDescription className={warn ? "text-foreground/80" : undefined}>
        <p>{t(`testErrors.${code}`, { model: result.model, baseUrl })}</p>
        {code === "unknown" && result.error && <p className="font-mono text-xs">{result.error}</p>}
      </AlertDescription>
    </Alert>
  );
}

function LlmSkeleton() {
  return (
    <div className="flex max-w-3xl flex-col gap-3" aria-busy="true">
      <Skeleton className="h-4 w-80" />
      <div className="grid gap-3 md:grid-cols-2">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      <Skeleton className="h-48" />
    </div>
  );
}
