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
import {
  ProviderModelHealthSummary,
  type LocalModelHealth,
  type LocalModelHealthState,
  type LocalProviderHealth,
  type LocalProviderHealthState
} from "./ProviderModelHealthSummary";
import { ProviderPresetSelector } from "./ProviderPresetSelector";
import {
  DEFAULT_MODEL_CONNECTION_BASELINE,
  buildOpenRouterConfigChanges,
  buildOpenRouterProbePayload,
  formatLmStudioModelRef,
  formatOllamaModelRef,
  getModelReadinessLabel,
  normalizeLmStudioBaseUrl,
  normalizeOllamaBaseUrl,
  normalizeConfiguredValue,
  stripLmStudioModelRef,
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
  localRuntimeBaseUrls: LocalRuntimeBaseUrls;
}

interface LocalRuntimeBaseUrls {
  ollama: string;
  lmStudio: string;
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

interface LMStudioModelEntry {
  name: string;
  ownedBy: string;
  contextLength: number | null;
}

interface LMStudioRuntimeStatus {
  state: "available" | "empty" | "unavailable" | "error";
  ok: boolean;
  baseUrl: string;
  message: string;
  models: LMStudioModelEntry[];
}

interface LoadLocalModelHealthOptions {
  ollamaBaseUrl?: string;
  lmStudioBaseUrl?: string;
}

function buildConfigSnapshot(data: unknown): ConfigSnapshot {
  const root = asRecord(data);
  const groups = asRecord(root.groups);
  const llm = asRecord(groups.llm);
  const ollama = asRecord(groups.ollama);
  const lmStudio = asRecord(groups.lm_studio);
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
    storedKeyHint,
    localRuntimeBaseUrls: {
      ollama: readString(ollama.ollama_base_url),
      lmStudio: readString(lmStudio.lm_studio_base_url)
    }
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

function parseLMStudioRuntimeStatus(data: unknown): LMStudioRuntimeStatus {
  const root = asRecord(data);
  const models = Array.isArray(root.models)
    ? root.models
        .map(parseLMStudioModel)
        .filter((model): model is LMStudioModelEntry => model !== null)
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
    message: readString(root.message) || "Could not read LM Studio status.",
    models
  };
}

function parseLMStudioModel(data: unknown): LMStudioModelEntry | null {
  const root = asRecord(data);
  const name = readString(root.name) || readString(root.id);
  if (!name) {
    return null;
  }
  return {
    name,
    ownedBy: readString(root.owned_by),
    contextLength: readNumber(root.context_length)
  };
}

function parseLocalModelHealth(data: unknown): LocalModelHealth {
  const root = asRecord(data);
  const providers = Array.isArray(root.providers)
    ? root.providers
        .map(parseLocalProviderHealth)
        .filter((provider): provider is LocalProviderHealth => provider !== null)
    : [];
  const state = readString(root.overall_state);
  const overallState: LocalModelHealthState =
    state === "ready" || state === "needs_attention" || state === "unavailable"
      ? state
      : "unavailable";

  return {
    overallState,
    summary: readString(root.summary) || "Local model health could not be summarized.",
    readyProviderCount: readNumber(root.ready_provider_count) ?? 0,
    attentionProviderCount: readNumber(root.attention_provider_count) ?? 0,
    totalModelCount: readNumber(root.total_model_count) ?? 0,
    providers
  };
}

function parseLocalProviderHealth(data: unknown): LocalProviderHealth | null {
  const root = asRecord(data);
  const provider = readString(root.provider);
  if (provider !== "ollama" && provider !== "lm-studio") {
    return null;
  }
  const state = readString(root.state);
  const normalizedState: LocalProviderHealthState =
    state === "available" || state === "empty" || state === "unavailable" || state === "error"
      ? state
      : "error";

  return {
    provider,
    label: readString(root.label) || (provider === "ollama" ? "Ollama" : "LM Studio"),
    state: normalizedState,
    ok: root.ok === true,
    baseUrl: readString(root.base_url),
    modelCount: readNumber(root.model_count) ?? 0,
    message: readString(root.message) || "Status unavailable.",
    action: readString(root.action) || "Refresh local health after checking this runtime."
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
  const [localRuntimeBaseUrls, setLocalRuntimeBaseUrls] = useState<LocalRuntimeBaseUrls>({
    ollama: "",
    lmStudio: ""
  });
  const [models, setModels] = useState<OpenRouterModelEntry[]>([]);
  const [ollamaStatus, setOllamaStatus] = useState<OllamaRuntimeStatus | null>(null);
  const [lmStudioStatus, setLMStudioStatus] = useState<LMStudioRuntimeStatus | null>(null);
  const [localModelHealth, setLocalModelHealth] = useState<LocalModelHealth | null>(null);
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
  const [isLoadingLMStudio, setIsLoadingLMStudio] = useState(false);
  const [isLoadingLocalHealth, setIsLoadingLocalHealth] = useState(false);

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
  const lmStudioModels = lmStudioStatus?.models ?? [];
  const liveLMStudioModelRefs = lmStudioModels.map((model) => formatLmStudioModelRef(model.name));
  const isOllamaSelected = selectedPresetId === "ollama";
  const isLMStudioSelected = selectedPresetId === "lm-studio";
  const isLocalModelCatalog = isOllamaSelected || isLMStudioSelected;

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
          setLocalRuntimeBaseUrls(snapshot.localRuntimeBaseUrls);
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
    setForm((current) => {
      const next = applyProviderPresetToForm(current, preset);
      if (preset.id === "ollama" && localRuntimeBaseUrls.ollama.trim()) {
        next.baseUrl = localRuntimeBaseUrls.ollama;
      }
      if (preset.id === "lm-studio" && localRuntimeBaseUrls.lmStudio.trim()) {
        next.baseUrl = localRuntimeBaseUrls.lmStudio;
      }
      return next;
    });
    setSaveStatus(null);
    setProbeStatus(null);
    setOllamaStatus(null);
    setLMStudioStatus(null);
  }

  function getOllamaBaseUrlOverride(): string | undefined {
    const preset = getProviderPreset("ollama");
    const current = normalizeOllamaBaseUrl(form.baseUrl);
    const configured = normalizeOllamaBaseUrl(
      localRuntimeBaseUrls.ollama || preset?.baseUrlDefault || ""
    );
    return current && current !== configured ? form.baseUrl : undefined;
  }

  function getLMStudioBaseUrlOverride(): string | undefined {
    const preset = getProviderPreset("lm-studio");
    const current = normalizeLmStudioBaseUrl(form.baseUrl);
    const configured = normalizeLmStudioBaseUrl(
      localRuntimeBaseUrls.lmStudio || preset?.baseUrlDefault || ""
    );
    return current && current !== configured ? form.baseUrl : undefined;
  }

  async function loadOllamaStatus(baseUrl?: string): Promise<OllamaRuntimeStatus | null> {
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
        query: baseUrl ? { base_url: normalizeOllamaBaseUrl(baseUrl) } : undefined
      });
      onResult("Model Wizard - Ollama Status", result);
      const status = parseOllamaRuntimeStatus(result.data);
      setOllamaStatus(status);
      return status;
    } catch (error) {
      const status: OllamaRuntimeStatus = {
        state: "error",
        ok: false,
        baseUrl: baseUrl ? normalizeOllamaBaseUrl(baseUrl) : ollamaStatus?.baseUrl ?? "",
        message: error instanceof Error ? error.message : "Could not check Ollama status.",
        models: []
      };
      setOllamaStatus(status);
      return status;
    } finally {
      setIsLoadingOllama(false);
    }
  }

  async function loadLMStudioStatus(baseUrl?: string): Promise<LMStudioRuntimeStatus | null> {
    if (!hasCredentials) {
      setLMStudioStatus(null);
      return null;
    }
    setIsLoadingLMStudio(true);
    try {
      const result = await apiRequest({
        method: "GET",
        path: "/v1/lm-studio/status",
        token,
        apiKey,
        query: baseUrl ? { base_url: normalizeLmStudioBaseUrl(baseUrl) } : undefined
      });
      onResult("Model Wizard - LM Studio Status", result);
      const status = parseLMStudioRuntimeStatus(result.data);
      setLMStudioStatus(status);
      return status;
    } catch (error) {
      const status: LMStudioRuntimeStatus = {
        state: "error",
        ok: false,
        baseUrl: baseUrl ? normalizeLmStudioBaseUrl(baseUrl) : lmStudioStatus?.baseUrl ?? "",
        message: error instanceof Error ? error.message : "Could not check LM Studio status.",
        models: []
      };
      setLMStudioStatus(status);
      return status;
    } finally {
      setIsLoadingLMStudio(false);
    }
  }

  async function loadLocalModelHealth(
    options: LoadLocalModelHealthOptions = {}
  ): Promise<LocalModelHealth | null> {
    if (!hasCredentials) {
      setLocalModelHealth(null);
      return null;
    }
    const query: Record<string, string> = {};
    if (options.ollamaBaseUrl) {
      query.ollama_base_url = normalizeOllamaBaseUrl(options.ollamaBaseUrl);
    }
    if (options.lmStudioBaseUrl) {
      query.lm_studio_base_url = normalizeLmStudioBaseUrl(options.lmStudioBaseUrl);
    }

    setIsLoadingLocalHealth(true);
    try {
      const result = await apiRequest({
        method: "GET",
        path: "/v1/model-health",
        token,
        apiKey,
        query: Object.keys(query).length > 0 ? query : undefined
      });
      onResult("Model Wizard - Local Model Health", result);
      const health = parseLocalModelHealth(result.data);
      setLocalModelHealth(health);
      return health;
    } catch {
      const health: LocalModelHealth = {
        overallState: "unavailable",
        summary: "Could not check local model health. Confirm the engine is reachable.",
        readyProviderCount: 0,
        attentionProviderCount: 0,
        totalModelCount: 0,
        providers: []
      };
      setLocalModelHealth(health);
      return health;
    } finally {
      setIsLoadingLocalHealth(false);
    }
  }

  useEffect(() => {
    if (!hasCredentials) {
      setLocalModelHealth(null);
      return;
    }
    void loadLocalModelHealth();
    // Run once when engine credentials become available; manual refresh handles URL edits.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasCredentials, token, apiKey]);

  useEffect(() => {
    if (!hasCredentials) {
      return;
    }
    if (selectedPresetId === "ollama") {
      void loadOllamaStatus(getOllamaBaseUrlOverride());
    }
    if (selectedPresetId === "lm-studio") {
      void loadLMStudioStatus(getLMStudioBaseUrlOverride());
    }
    // Run when the operator enters a local runtime path; manual refresh handles base URL edits.
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
        const status = await loadOllamaStatus(getOllamaBaseUrlOverride());
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

      if (selectedPresetId === "lm-studio") {
        const status = await loadLMStudioStatus(getLMStudioBaseUrlOverride());
        const selectedModel = stripLmStudioModelRef(form.defaultModel);
        const hasSelectedModel =
          status?.models.some((model) => model.name === selectedModel) ?? false;
        const ok = status?.ok === true && hasSelectedModel;
        setProbeStatus({
          tone: ok ? "success" : "error",
          message: ok
            ? `LM Studio is ready at ${status.baseUrl}. Model: ${form.defaultModel}.`
            : status?.ok
              ? `LM Studio is running, but ${selectedModel || "the selected model"} is not listed.`
              : status?.message ?? "LM Studio connection failed."
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

      <ProviderModelHealthSummary
        health={localModelHealth}
        isLoading={isLoadingLocalHealth}
        hasCredentials={hasCredentials}
        selectedPresetId={selectedPresetId}
        selectedProviderName={selectedPreset.name}
        onRefresh={() =>
          void loadLocalModelHealth({
            ollamaBaseUrl: isOllamaSelected ? getOllamaBaseUrlOverride() : undefined,
            lmStudioBaseUrl: isLMStudioSelected ? getLMStudioBaseUrlOverride() : undefined
          })
        }
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
          {isOllamaSelected ? (
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
                onClick={() => void loadOllamaStatus(getOllamaBaseUrlOverride())}
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
          {isLMStudioSelected ? (
            <div className="local-runtime-panel">
              <div>
                <strong>Local LM Studio status</strong>
                <p>
                  {isLoadingLMStudio
                    ? "Checking LM Studio..."
                    : lmStudioStatus?.message ??
                      "Check whether the LM Studio local server is running and listing models."}
                </p>
              </div>
              <button
                type="button"
                onClick={() => void loadLMStudioStatus(getLMStudioBaseUrlOverride())}
                disabled={!hasCredentials || isLoadingLMStudio}
              >
                {isLoadingLMStudio ? "Checking..." : "Refresh LM Studio"}
              </button>
              {lmStudioModels.length > 0 ? (
                <div className="local-runtime-models" role="group" aria-label="Detected LM Studio models">
                  {lmStudioModels.map((model) => {
                    const modelRef = formatLmStudioModelRef(model.name);
                    const meta = [
                      model.ownedBy,
                      model.contextLength ? `${formatOpenRouterNumber(model.contextLength)} context` : ""
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
                        <small>{meta || "LM Studio local model"}</small>
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
            {isOllamaSelected
              ? liveOllamaModelRefs.map((modelRef) => (
                  <option key={modelRef} value={modelRef}>{stripOllamaModelRef(modelRef)}</option>
                ))
              : isLMStudioSelected
                ? liveLMStudioModelRefs.map((modelRef) => (
                    <option key={modelRef} value={modelRef}>{stripLmStudioModelRef(modelRef)}</option>
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
              {isOllamaSelected
                ? "Detected Ollama models"
                : isLMStudioSelected
                  ? "Detected LM Studio models"
                  : "Available OpenRouter models"}
            </h3>
            <p>
              {isOllamaSelected
                ? "Use detected local models after starting Ollama. No prompts or secrets are sent during this check."
                : isLMStudioSelected
                  ? "Use detected local models after starting the LM Studio server. No prompts or secrets are sent during this check."
                : "Use search to find coding, free, long-context, or moderated model options."}
            </p>
          </div>
          {!isLocalModelCatalog ? (
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
          {isOllamaSelected
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
            : isLMStudioSelected
              ? lmStudioModels.map((model) => {
                  const modelRef = formatLmStudioModelRef(model.name);
                  return (
                    <button type="button" key={model.name} onClick={() => updateField("defaultModel", modelRef)}>
                      <strong>{model.name}</strong>
                      <span>{modelRef}</span>
                      <small>
                        {[model.ownedBy, model.contextLength ? `${formatOpenRouterNumber(model.contextLength)} context` : ""]
                          .filter(Boolean)
                          .join(" · ") || "LM Studio local model"}
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
