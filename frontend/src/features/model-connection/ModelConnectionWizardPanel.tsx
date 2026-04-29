import { useEffect, useMemo, useState } from "react";

import { apiRequest } from "../../lib/api";
import {
  filterOpenRouterModels,
  formatOpenRouterNumber,
  normalizeLikelyOpenRouterModelRef,
  parseOpenRouterModels,
  type OpenRouterModelEntry
} from "../../lib/openrouterModels";
import {
  asRecord,
  extractResultMessage,
  readNumber,
  readString,
  readStringArray
} from "../../lib/valueReaders";
import type { ApiResult } from "../../types";
import { ModelCapabilityBadges } from "./ModelCapabilityBadges";
import { ProviderPresetSelector } from "./ProviderPresetSelector";
import {
  DEFAULT_MODEL_CONNECTION_BASELINE,
  buildOpenRouterConfigChanges,
  buildOpenRouterProbePayload,
  formatOllamaModelRef,
  getModelReadinessLabel,
  normalizeOllamaBaseUrl,
  normalizeConfiguredValue,
  stripOllamaModelRef,
  type ModelConnectionBaseline,
  type ModelConnectionForm
} from "./helpers";
import {
  PROVIDER_PRESETS,
  applyProviderPresetToForm,
  getProviderPreset,
  inferProviderPresetId,
  type ProviderPreset,
  type ProviderPresetId
} from "./presets";

interface ModelConnectionWizardPanelProps {
  token: string;
  apiKey: string;
  onOpenSetup: () => void;
  onOpenWorkflowCatalog: () => void;
  onResult: (label: string, result: ApiResult) => void;
}

type StatusTone = "info" | "success" | "warning" | "error";

interface StatusMessage {
  tone: StatusTone;
  message: string;
}

interface ConfigSnapshot {
  baseline: ModelConnectionBaseline;
  hasStoredKey: boolean;
  storedKeyHint: string;
}

interface OllamaModelEntry {
  name: string;
  size: number | null;
  parameterSize: string;
  quantizationLevel: string;
}

interface OllamaRuntimeStatus {
  state: "available" | "empty" | "unavailable" | "error";
  ok: boolean;
  baseUrl: string;
  message: string;
  models: OllamaModelEntry[];
}

function buildConfigSnapshot(data: unknown): ConfigSnapshot {
  const root = asRecord(data);
  const groups = asRecord(root.groups);
  const llm = asRecord(groups.llm);
  const ollama = asRecord(groups.ollama);
  const storedKeyHint =
    readString(llm.openrouter_api_key) || readString(llm.openrouter_api_key_redacted);

  return {
    baseline: {
      defaultModel:
        normalizeLikelyOpenRouterModelRef(
          readString(llm.default_model) || readString(ollama.default_model)
        ) || DEFAULT_MODEL_CONNECTION_BASELINE.defaultModel,
      baseUrl: readString(llm.openrouter_base_url) || DEFAULT_MODEL_CONNECTION_BASELINE.baseUrl,
      siteUrl: readString(llm.openrouter_site_url) || DEFAULT_MODEL_CONNECTION_BASELINE.siteUrl,
      appName: readString(llm.openrouter_app_name) || DEFAULT_MODEL_CONNECTION_BASELINE.appName,
      appCategory:
        readString(llm.openrouter_app_category) || DEFAULT_MODEL_CONNECTION_BASELINE.appCategory
    },
    hasStoredKey: storedKeyHint.trim() !== "",
    storedKeyHint
  };
}

function renderStatus(status: StatusMessage | null): JSX.Element | null {
  if (status === null) {
    return null;
  }
  return (
    <div className={`model-wizard-status model-wizard-status--${status.tone}`} role={status.tone === "error" ? "alert" : "status"}>
      {status.message}
    </div>
  );
}

function parseOllamaRuntimeStatus(data: unknown): OllamaRuntimeStatus {
  const root = asRecord(data);
  const models = Array.isArray(root.models)
    ? root.models.map(parseOllamaModel).filter((model): model is OllamaModelEntry => model !== null)
    : [];
  const state = readString(root.state);
  const normalizedState =
    state === "available" || state === "empty" || state === "unavailable" || state === "error"
      ? state
      : "error";

  return {
    state: normalizedState,
    ok: root.ok === true,
    baseUrl: readString(root.base_url),
    message: readString(root.message) || "Could not read Ollama status.",
    models
  };
}

function parseOllamaModel(data: unknown): OllamaModelEntry | null {
  const root = asRecord(data);
  const name = readString(root.name);
  if (!name) {
    return null;
  }
  const details = asRecord(root.details);
  return {
    name,
    size: readNumber(root.size),
    parameterSize: readString(details.parameter_size),
    quantizationLevel: readString(details.quantization_level)
  };
}

function formatModelSize(size: number | null): string {
  if (size === null || size <= 0) {
    return "size unknown";
  }
  const gib = size / 1024 ** 3;
  return `${gib.toFixed(gib >= 10 ? 0 : 1)} GB`;
}

export function ModelConnectionWizardPanel({
  token,
  apiKey,
  onOpenSetup,
  onOpenWorkflowCatalog,
  onResult
}: ModelConnectionWizardPanelProps): JSX.Element {
  const [form, setForm] = useState<ModelConnectionForm>({
    ...DEFAULT_MODEL_CONNECTION_BASELINE,
    apiKey: "",
    writeToEnvFile: true,
    removeStoredKey: false
  });
  const [baseline, setBaseline] = useState<ModelConnectionBaseline>(
    DEFAULT_MODEL_CONNECTION_BASELINE
  );
  const [hasStoredKey, setHasStoredKey] = useState(false);
  const [storedKeyHint, setStoredKeyHint] = useState("");
  const [models, setModels] = useState<OpenRouterModelEntry[]>([]);
  const [ollamaStatus, setOllamaStatus] = useState<OllamaRuntimeStatus | null>(null);
  const [modelSearch, setModelSearch] = useState("");
  const [selectedPresetId, setSelectedPresetId] = useState<ProviderPresetId>("openrouter");
  const [loadStatus, setLoadStatus] = useState<StatusMessage>({
    tone: "info",
    message: "Loading model connection status..."
  });
  const [saveStatus, setSaveStatus] = useState<StatusMessage | null>(null);
  const [probeStatus, setProbeStatus] = useState<StatusMessage | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isProbing, setIsProbing] = useState(false);
  const [isLoadingOllama, setIsLoadingOllama] = useState(false);

  const hasCredentials = token.trim() !== "" || apiKey.trim() !== "";
  const effectiveHasKey = form.removeStoredKey ? false : hasStoredKey || form.apiKey.trim() !== "";
  const selectedPreset = getProviderPreset(selectedPresetId) ?? PROVIDER_PRESETS[0];
  const providerAccessReady = selectedPreset.needsApiKey ? effectiveHasKey : true;
  const probeSucceeded = probeStatus?.tone === "success";
  const readinessLabel = getModelReadinessLabel(
    hasCredentials,
    providerAccessReady,
    form.defaultModel,
    probeSucceeded
  );
  const filteredModels = useMemo(
    () => filterOpenRouterModels(models, modelSearch).slice(0, 8),
    [modelSearch, models]
  );
  const ollamaModels = ollamaStatus?.models ?? [];
  const liveOllamaModelRefs = ollamaModels.map((model) => formatOllamaModelRef(model.name));

  useEffect(() => {
    if (!hasCredentials) {
      setLoadStatus({
        tone: "warning",
        message: "Connect an operator token or API key before inspecting model settings."
      });
      return;
    }

    let cancelled = false;

    async function load(): Promise<void> {
      setLoadStatus({ tone: "info", message: "Loading model settings and catalog..." });
      const [configResult, catalogResult] = await Promise.allSettled([
        apiRequest({ method: "GET", path: "/v1/operator/config", token, apiKey }),
        apiRequest({ method: "GET", path: "/v1/openrouter/models", token, apiKey })
      ]);
      if (cancelled) {
        return;
      }

      if (configResult.status === "fulfilled") {
        onResult("Model Wizard - Config", configResult.value);
        if (configResult.value.ok) {
          const snapshot = buildConfigSnapshot(configResult.value.data);
          setBaseline(snapshot.baseline);
          setForm((current) => ({ ...current, ...snapshot.baseline, apiKey: "" }));
          setSelectedPresetId(inferProviderPresetId(snapshot.baseline.baseUrl));
          setHasStoredKey(snapshot.hasStoredKey);
          setStoredKeyHint(snapshot.storedKeyHint);
        }
      }

      if (catalogResult.status === "fulfilled") {
        onResult("Model Wizard - Catalog", catalogResult.value);
        if (catalogResult.value.ok) {
          setModels(parseOpenRouterModels(catalogResult.value.data));
        }
      }

      setLoadStatus({
        tone:
          configResult.status === "fulfilled" && configResult.value.ok ? "success" : "warning",
        message:
          configResult.status === "fulfilled" && configResult.value.ok
            ? "Model settings loaded. Choose a default and test the connection."
            : "Could not load current model settings; you can still prepare local form values."
      });
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [apiKey, hasCredentials, onResult, token]);

  function updateField<K extends keyof ModelConnectionForm>(
    key: K,
    value: ModelConnectionForm[K]
  ): void {
    setForm((current) => {
      const next = { ...current, [key]: value };
      if (key === "apiKey" && String(value).trim() !== "") {
        next.removeStoredKey = false;
      }
      return next;
    });
  }

  function selectProviderPreset(preset: ProviderPreset): void {
    setSelectedPresetId(preset.id);
    setForm((current) => applyProviderPresetToForm(current, preset));
    setSaveStatus(null);
    setProbeStatus(null);
    setOllamaStatus(null);
  }

  async function loadOllamaStatus(baseUrl = form.baseUrl): Promise<OllamaRuntimeStatus | null> {
    if (!hasCredentials) {
      setOllamaStatus(null);
      return null;
    }
    setIsLoadingOllama(true);
    try {
      const result = await apiRequest({
        method: "GET",
        path: "/v1/ollama/status",
        token,
        apiKey,
        query: { base_url: normalizeOllamaBaseUrl(baseUrl) }
      });
      onResult("Model Wizard - Ollama Status", result);
      const status = parseOllamaRuntimeStatus(result.data);
      setOllamaStatus(status);
      return status;
    } catch (error) {
      const status: OllamaRuntimeStatus = {
        state: "error",
        ok: false,
        baseUrl: normalizeOllamaBaseUrl(baseUrl),
        message: error instanceof Error ? error.message : "Could not check Ollama status.",
        models: []
      };
      setOllamaStatus(status);
      return status;
    } finally {
      setIsLoadingOllama(false);
    }
  }

  useEffect(() => {
    if (selectedPresetId !== "ollama" || !hasCredentials) {
      return;
    }
    void loadOllamaStatus();
    // Run when the operator enters the Ollama path; manual refresh handles base URL edits.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasCredentials, selectedPresetId]);

  async function saveSettings(): Promise<void> {
    const changes = buildOpenRouterConfigChanges(form, baseline);
    if (Object.keys(changes).length === 0) {
      setSaveStatus({ tone: "info", message: "No model settings changed yet." });
      return;
    }
    setIsSaving(true);
    setSaveStatus({ tone: "info", message: "Saving model settings..." });
    try {
      const result = await apiRequest({
        method: "POST",
        path: "/v1/config/apply",
        token,
        apiKey,
        body: JSON.stringify({ changes, write_to_env_file: form.writeToEnvFile })
      });
      onResult("Model Wizard - Save", result);
      const payload = asRecord(result.data);
      const validationErrors = readStringArray(payload.validation_errors);
      const rejected = Array.isArray(payload.rejected)
        ? payload.rejected
            .filter((item): item is [string, string] => Array.isArray(item) && item.length >= 2)
            .map(([field, reason]) => `${field}: ${reason}`)
        : [];
      if (!result.ok || validationErrors.length > 0 || rejected.length > 0) {
        setSaveStatus({
          tone: "error",
          message:
            [...validationErrors, ...rejected].join(" ") ||
            extractResultMessage(result.data, "Could not save model settings.")
        });
        return;
      }

      const nextBaseline: ModelConnectionBaseline = {
        defaultModel: normalizeLikelyOpenRouterModelRef(form.defaultModel),
        baseUrl: normalizeConfiguredValue(form.baseUrl, DEFAULT_MODEL_CONNECTION_BASELINE.baseUrl),
        siteUrl: normalizeConfiguredValue(form.siteUrl, DEFAULT_MODEL_CONNECTION_BASELINE.siteUrl),
        appName: normalizeConfiguredValue(form.appName, DEFAULT_MODEL_CONNECTION_BASELINE.appName),
        appCategory: normalizeConfiguredValue(
          form.appCategory,
          DEFAULT_MODEL_CONNECTION_BASELINE.appCategory
        )
      };
      setBaseline(nextBaseline);
      setForm((current) => ({ ...current, ...nextBaseline, apiKey: "", removeStoredKey: false }));
      setHasStoredKey(form.removeStoredKey ? false : form.apiKey.trim() !== "" || hasStoredKey);
      setStoredKeyHint(form.removeStoredKey ? "" : form.apiKey.trim() ? "configured" : storedKeyHint);
      setSaveStatus({ tone: "success", message: "Model settings saved." });
    } catch (error) {
      setSaveStatus({
        tone: "error",
        message: error instanceof Error ? error.message : "Could not save model settings."
      });
    } finally {
      setIsSaving(false);
    }
  }

  async function probeConnection(): Promise<void> {
    setIsProbing(true);
    setProbeStatus({ tone: "info", message: "Testing model connection..." });
    try {
      if (selectedPresetId === "ollama") {
        const status = await loadOllamaStatus();
        const selectedModel = stripOllamaModelRef(form.defaultModel);
        const hasSelectedModel =
          status?.models.some((model) => model.name === selectedModel) ?? false;
        const ok = status?.ok === true && hasSelectedModel;
        setProbeStatus({
          tone: ok ? "success" : "error",
          message: ok
            ? `Ollama is ready at ${status.baseUrl}. Model: ${form.defaultModel}.`
            : status?.ok
              ? `Ollama is running, but ${selectedModel || "the selected model"} is not installed.`
              : status?.message ?? "Ollama connection failed."
        });
        return;
      }

      const result = await apiRequest({
        method: "POST",
        path: "/v1/openrouter/probe",
        token,
        apiKey,
        body: JSON.stringify(buildOpenRouterProbePayload(form))
      });
      onResult("Model Wizard - Probe", result);
      const payload = asRecord(result.data);
      const ok = result.ok && payload.ok !== false && !readString(payload.error);
      const latency = readNumber(payload.latency_ms) ?? readNumber(payload.duration_ms);
      const model = readString(payload.model) || readString(payload.default_model) || form.defaultModel;
      setProbeStatus({
        tone: ok ? "success" : "error",
        message: `${extractResultMessage(result.data, ok ? "Connection succeeded." : "Connection failed.")} Model: ${model}.${latency !== null ? ` Latency: ${Math.round(latency)}ms.` : ""}`
      });
    } catch (error) {
      setProbeStatus({
        tone: "error",
        message: error instanceof Error ? error.message : "Connection test failed."
      });
    } finally {
      setIsProbing(false);
    }
  }

  return (
    <section className="model-wizard-panel" aria-labelledby="model-wizard-title">
      <header className="model-wizard-hero">
        <div>
          <p className="eyebrow">Model Connection Wizard</p>
          <h2 id="model-wizard-title">Connect a model before you build</h2>
          <p>
            Pick {selectedPreset.name}, save a recommended model, test the connection, then launch
            a workflow with confidence.
          </p>
        </div>
        <div className="model-wizard-score">
          <strong>{readinessLabel}</strong>
          <span>
            {selectedPreset.needsApiKey
              ? hasStoredKey
                ? "Stored provider key configured"
                : "Provider key needed"
              : "Local path can run without a key"}
          </span>
        </div>
      </header>

      {!hasCredentials ? (
        <article className="onboarding-callout onboarding-callout-error">
          <h3>Connect engine access first</h3>
          <p>Add an API key or operator token so AGENT-33 can inspect and save model settings.</p>
          <button type="button" onClick={onOpenSetup}>Open integrations</button>
        </article>
      ) : null}

      {renderStatus(loadStatus)}

      <ProviderPresetSelector
        presets={PROVIDER_PRESETS}
        selectedPresetId={selectedPresetId}
        onSelectPreset={selectProviderPreset}
      />

      <div className="model-wizard-grid">
        <section className="model-wizard-card">
          <span>Step 1</span>
          <h3>Choose a recommended default</h3>
          <p>{selectedPreset.bestFor}. These picks are safe defaults for this provider path.</p>
          <div className="model-recommendation-list" role="group" aria-label="Recommended default models">
            {selectedPreset.recommendedModels.map((model) => (
              <button
                type="button"
                key={model.id}
                className={normalizeLikelyOpenRouterModelRef(form.defaultModel) === model.id ? "active" : ""}
                aria-pressed={normalizeLikelyOpenRouterModelRef(form.defaultModel) === model.id}
                aria-label={`Use ${model.name} as the default model`}
                onClick={() => updateField("defaultModel", model.id)}
              >
                <strong>{model.name}</strong>
                <small>{model.badgeLabel} · {model.description}</small>
                <ModelCapabilityBadges model={model} />
              </button>
            ))}
          </div>
          {selectedPresetId === "ollama" ? (
            <div className="local-runtime-panel">
              <div>
                <strong>Local Ollama status</strong>
                <p>
                  {isLoadingOllama
                    ? "Checking Ollama..."
                    : ollamaStatus?.message ??
                      "Check whether Ollama is running and which models are installed."}
                </p>
              </div>
              <button
                type="button"
                onClick={() => void loadOllamaStatus()}
                disabled={!hasCredentials || isLoadingOllama}
              >
                {isLoadingOllama ? "Checking..." : "Refresh Ollama"}
              </button>
              {ollamaModels.length > 0 ? (
                <div className="local-runtime-models" role="group" aria-label="Detected Ollama models">
                  {ollamaModels.map((model) => {
                    const modelRef = formatOllamaModelRef(model.name);
                    const meta = [
                      model.parameterSize,
                      model.quantizationLevel,
                      formatModelSize(model.size)
                    ].filter(Boolean).join(" · ");
                    return (
                      <button
                        type="button"
                        key={model.name}
                        className={form.defaultModel === modelRef ? "active" : ""}
                        aria-pressed={form.defaultModel === modelRef}
                        onClick={() => updateField("defaultModel", modelRef)}
                      >
                        <strong>{model.name}</strong>
                        <small>{meta || "Local Ollama model"}</small>
                      </button>
                    );
                  })}
                </div>
              ) : null}
            </div>
          ) : null}
        </section>

        <section className="model-wizard-card">
          <span>Step 2</span>
          <h3>Add provider access</h3>
          <label>
            {selectedPreset.apiKeyLabel}
            <input
              type="password"
              value={form.apiKey}
              onChange={(event) => updateField("apiKey", event.target.value)}
              placeholder={hasStoredKey ? "Stored key already configured" : selectedPreset.apiKeyPlaceholder}
            />
          </label>
          <p className="model-wizard-field-hint">{selectedPreset.apiKeyHint}</p>
          <label>
            Default model
            <input
              value={form.defaultModel}
              onChange={(event) => updateField("defaultModel", event.target.value)}
              list="model-wizard-model-options"
            />
          </label>
          <datalist id="model-wizard-model-options">
            {selectedPresetId === "ollama"
              ? liveOllamaModelRefs.map((modelRef) => (
                  <option key={modelRef} value={modelRef}>{stripOllamaModelRef(modelRef)}</option>
                ))
              : models.slice(0, 80).map((model) => (
                  <option key={model.id} value={model.id}>{model.name}</option>
                ))}
          </datalist>
          <label>
            Base URL
            <input
              value={form.baseUrl}
              onChange={(event) => {
                const nextBaseUrl = event.target.value;
                updateField("baseUrl", nextBaseUrl);
                setSelectedPresetId(inferProviderPresetId(nextBaseUrl));
              }}
            />
          </label>
          <label className="model-wizard-checkbox">
            <input
              type="checkbox"
              checked={form.writeToEnvFile}
              onChange={(event) => updateField("writeToEnvFile", event.target.checked)}
            />
            Save to env file when supported
          </label>
          {hasStoredKey ? (
            <label className="model-wizard-checkbox">
              <input
                type="checkbox"
                checked={form.removeStoredKey}
                disabled={form.apiKey.trim() !== ""}
                onChange={(event) => updateField("removeStoredKey", event.target.checked)}
              />
              Remove stored OpenRouter key
            </label>
          ) : null}
          <div className="model-wizard-actions">
            <button type="button" onClick={() => void saveSettings()} disabled={!hasCredentials || isSaving}>
              {isSaving ? "Saving..." : "Save model settings"}
            </button>
          </div>
          {renderStatus(saveStatus)}
        </section>

        <section className="model-wizard-card">
          <span>Step 3</span>
          <h3>Test and launch</h3>
          <p>
            Test {selectedPreset.name}. If it succeeds, open the workflow catalog and start from a
            packaged outcome.
          </p>
          <div className="model-wizard-actions">
            <button type="button" onClick={() => void probeConnection()} disabled={!hasCredentials || isProbing}>
              {isProbing ? "Testing..." : "Test connection"}
            </button>
            <button type="button" onClick={onOpenWorkflowCatalog}>
              Open workflow catalog
            </button>
          </div>
          {renderStatus(probeStatus)}
        </section>
      </div>

      <section className="model-catalog-preview" aria-labelledby="model-catalog-preview-title">
        <div className="outcome-section-head">
          <div>
            <p className="eyebrow">Model catalog</p>
            <h3 id="model-catalog-preview-title">
              {selectedPresetId === "ollama" ? "Detected Ollama models" : "Available OpenRouter models"}
            </h3>
            <p>
              {selectedPresetId === "ollama"
                ? "Use detected local models after starting Ollama. No prompts or secrets are sent during this check."
                : "Use search to find coding, free, long-context, or moderated model options."}
            </p>
          </div>
          {selectedPresetId !== "ollama" ? (
            <label>
            Search models
            <input
              value={modelSearch}
              onChange={(event) => setModelSearch(event.target.value)}
              placeholder="coder, qwen, free, long context..."
            />
            </label>
          ) : null}
        </div>
        <div className="model-catalog-grid">
          {selectedPresetId === "ollama"
            ? ollamaModels.map((model) => {
                const modelRef = formatOllamaModelRef(model.name);
                return (
                  <button type="button" key={model.name} onClick={() => updateField("defaultModel", modelRef)}>
                    <strong>{model.name}</strong>
                    <span>{modelRef}</span>
                    <small>
                      {[model.parameterSize, model.quantizationLevel, formatModelSize(model.size)]
                        .filter(Boolean)
                        .join(" · ") || "Local Ollama model"}
                    </small>
                  </button>
                );
              })
            : filteredModels.map((model) => (
                <button type="button" key={model.id} onClick={() => updateField("defaultModel", model.id)}>
                  <strong>{model.name}</strong>
                  <span>{model.id}</span>
                  <ModelCapabilityBadges model={model} />
                  <small>
                    {model.contextLength ? `${formatOpenRouterNumber(model.contextLength)} context` : "Context unknown"}
                    {model.promptPrice ? ` · ${model.promptPrice} input` : ""}
                    {model.isFree ? " · Free option" : ""}
                  </small>
                </button>
              ))}
        </div>
      </section>
    </section>
  );
}
