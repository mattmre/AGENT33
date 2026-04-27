import { useEffect, useMemo, useState } from "react";

import { apiRequest } from "../../lib/api";
import {
  OPENROUTER_RECOMMENDED_MODELS,
  filterOpenRouterModels,
  formatOpenRouterNumber,
  normalizeLikelyOpenRouterModelRef,
  parseOpenRouterModels,
  type OpenRouterModelEntry
} from "../../lib/openrouterModels";
import type { ApiResult } from "../../types";
import {
  DEFAULT_MODEL_CONNECTION_BASELINE,
  buildOpenRouterConfigChanges,
  buildOpenRouterProbePayload,
  getModelReadinessLabel,
  normalizeConfiguredValue,
  type ModelConnectionBaseline,
  type ModelConnectionForm
} from "./helpers";

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

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function readString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function readNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function readStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function extractResultMessage(payload: unknown, fallback: string): string {
  const data = asRecord(payload);
  return (
    readString(data.message) ||
    readString(data.detail) ||
    readString(data.error) ||
    readString(data.status) ||
    fallback
  );
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
  const [modelSearch, setModelSearch] = useState("");
  const [loadStatus, setLoadStatus] = useState<StatusMessage>({
    tone: "info",
    message: "Loading model connection status..."
  });
  const [saveStatus, setSaveStatus] = useState<StatusMessage | null>(null);
  const [probeStatus, setProbeStatus] = useState<StatusMessage | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isProbing, setIsProbing] = useState(false);

  const hasCredentials = token.trim() !== "" || apiKey.trim() !== "";
  const probeSucceeded = probeStatus?.tone === "success";
  const readinessLabel = getModelReadinessLabel(
    hasCredentials,
    hasStoredKey || form.apiKey.trim() !== "",
    form.defaultModel,
    probeSucceeded
  );
  const filteredModels = useMemo(
    () => filterOpenRouterModels(models, modelSearch).slice(0, 8),
    [modelSearch, models]
  );

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
    setForm((current) => ({ ...current, [key]: value }));
  }

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
            Use plain-language defaults instead of raw config keys. Save a provider, choose a
            recommended model, test it, then launch a workflow with confidence.
          </p>
        </div>
        <div className="model-wizard-score">
          <strong>{readinessLabel}</strong>
          <span>{hasStoredKey ? "Stored provider key configured" : "No stored provider key detected"}</span>
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

      <div className="model-wizard-grid">
        <section className="model-wizard-card">
          <span>Step 1</span>
          <h3>Choose a recommended default</h3>
          <p>These are known-good picks for coding and workflow automation.</p>
          <div className="model-recommendation-list">
            {OPENROUTER_RECOMMENDED_MODELS.map((model) => (
              <button
                type="button"
                key={model.id}
                className={normalizeLikelyOpenRouterModelRef(form.defaultModel) === model.id ? "active" : ""}
                onClick={() => updateField("defaultModel", model.id)}
              >
                <strong>{model.name}</strong>
                <small>{model.badgeLabel} · {model.description}</small>
              </button>
            ))}
          </div>
        </section>

        <section className="model-wizard-card">
          <span>Step 2</span>
          <h3>Add provider access</h3>
          <label>
            OpenRouter API key
            <input
              type="password"
              value={form.apiKey}
              onChange={(event) => updateField("apiKey", event.target.value)}
              placeholder={hasStoredKey ? "Stored key already configured" : "sk-or-v1-..."}
            />
          </label>
          <label>
            Default model
            <input
              value={form.defaultModel}
              onChange={(event) => updateField("defaultModel", event.target.value)}
              list="model-wizard-openrouter-models"
            />
          </label>
          <datalist id="model-wizard-openrouter-models">
            {models.slice(0, 80).map((model) => (
              <option key={model.id} value={model.id}>{model.name}</option>
            ))}
          </datalist>
          <label>
            Base URL
            <input value={form.baseUrl} onChange={(event) => updateField("baseUrl", event.target.value)} />
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
          <p>Probe the selected provider before handing work to agents.</p>
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
            <h3 id="model-catalog-preview-title">Available OpenRouter models</h3>
            <p>Use search to find coding, free, long-context, or moderated model options.</p>
          </div>
          <label>
            Search models
            <input
              value={modelSearch}
              onChange={(event) => setModelSearch(event.target.value)}
              placeholder="coder, qwen, free, long context..."
            />
          </label>
        </div>
        <div className="model-catalog-grid">
          {filteredModels.map((model) => (
            <button type="button" key={model.id} onClick={() => updateField("defaultModel", model.id)}>
              <strong>{model.name}</strong>
              <span>{model.id}</span>
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
