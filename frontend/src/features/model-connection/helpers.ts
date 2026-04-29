import {
  OPENROUTER_STABLE_DEFAULT_MODEL,
  normalizeLikelyOpenRouterModelRef
} from "../../lib/openrouterModels";

export interface ModelConnectionBaseline {
  defaultModel: string;
  baseUrl: string;
  siteUrl: string;
  appName: string;
  appCategory: string;
}

export interface ModelConnectionForm extends ModelConnectionBaseline {
  apiKey: string;
  writeToEnvFile: boolean;
  removeStoredKey: boolean;
}

export const DEFAULT_MODEL_CONNECTION_BASELINE: ModelConnectionBaseline = {
  defaultModel: OPENROUTER_STABLE_DEFAULT_MODEL,
  baseUrl: "https://openrouter.ai/api/v1",
  siteUrl: "http://localhost",
  appName: "AGENT-33",
  appCategory: "cli-agent"
};

export function normalizeConfiguredValue(value: string, fallback: string): string {
  return value.trim() || fallback;
}

export function buildOpenRouterConfigChanges(
  form: ModelConnectionForm,
  baseline: ModelConnectionBaseline
): Record<string, unknown> {
  const normalizedForm = {
    defaultModel: normalizeLikelyOpenRouterModelRef(form.defaultModel),
    baseUrl: normalizeConfiguredValue(form.baseUrl, DEFAULT_MODEL_CONNECTION_BASELINE.baseUrl),
    siteUrl: normalizeConfiguredValue(form.siteUrl, DEFAULT_MODEL_CONNECTION_BASELINE.siteUrl),
    appName: normalizeConfiguredValue(form.appName, DEFAULT_MODEL_CONNECTION_BASELINE.appName),
    appCategory: normalizeConfiguredValue(
      form.appCategory,
      DEFAULT_MODEL_CONNECTION_BASELINE.appCategory
    )
  };
  const normalizedBaseline = {
    defaultModel: normalizeLikelyOpenRouterModelRef(baseline.defaultModel),
    baseUrl: normalizeConfiguredValue(baseline.baseUrl, DEFAULT_MODEL_CONNECTION_BASELINE.baseUrl),
    siteUrl: normalizeConfiguredValue(baseline.siteUrl, DEFAULT_MODEL_CONNECTION_BASELINE.siteUrl),
    appName: normalizeConfiguredValue(baseline.appName, DEFAULT_MODEL_CONNECTION_BASELINE.appName),
    appCategory: normalizeConfiguredValue(
      baseline.appCategory,
      DEFAULT_MODEL_CONNECTION_BASELINE.appCategory
    )
  };

  const changes: Record<string, unknown> = {};
  if (normalizedForm.defaultModel !== normalizedBaseline.defaultModel) {
    changes.default_model = normalizedForm.defaultModel;
  }
  if (normalizedForm.baseUrl !== normalizedBaseline.baseUrl) {
    changes.openrouter_base_url = normalizedForm.baseUrl;
  }
  if (normalizedForm.siteUrl !== normalizedBaseline.siteUrl) {
    changes.openrouter_site_url = normalizedForm.siteUrl;
  }
  if (normalizedForm.appName !== normalizedBaseline.appName) {
    changes.openrouter_app_name = normalizedForm.appName;
  }
  if (normalizedForm.appCategory !== normalizedBaseline.appCategory) {
    changes.openrouter_app_category = normalizedForm.appCategory;
  }

  const trimmedApiKey = form.apiKey.trim();
  if (trimmedApiKey) {
    changes.openrouter_api_key = trimmedApiKey;
  } else if (form.removeStoredKey) {
    changes.openrouter_api_key = "";
  }

  return changes;
}

export function buildOpenRouterProbePayload(form: ModelConnectionForm): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    openrouter_base_url: normalizeConfiguredValue(
      form.baseUrl,
      DEFAULT_MODEL_CONNECTION_BASELINE.baseUrl
    ),
    openrouter_site_url: normalizeConfiguredValue(
      form.siteUrl,
      DEFAULT_MODEL_CONNECTION_BASELINE.siteUrl
    ),
    openrouter_app_name: normalizeConfiguredValue(
      form.appName,
      DEFAULT_MODEL_CONNECTION_BASELINE.appName
    ),
    openrouter_app_category: normalizeConfiguredValue(
      form.appCategory,
      DEFAULT_MODEL_CONNECTION_BASELINE.appCategory
    )
  };

  const model = normalizeLikelyOpenRouterModelRef(form.defaultModel);
  if (model) {
    payload.default_model = model;
  }
  if (form.apiKey.trim()) {
    payload.openrouter_api_key = form.apiKey.trim();
  } else if (form.removeStoredKey) {
    payload.openrouter_api_key = "";
  }

  return payload;
}

export function normalizeOllamaBaseUrl(baseUrl: string): string {
  const trimmed = baseUrl.trim().replace(/\/+$/, "");
  return trimmed.toLowerCase().endsWith("/v1") ? trimmed.slice(0, -3).replace(/\/+$/, "") : trimmed;
}

export function normalizeLmStudioBaseUrl(baseUrl: string): string {
  const trimmed = baseUrl.trim().replace(/\/+$/, "");
  if (!trimmed || trimmed.toLowerCase().endsWith("/v1")) {
    return trimmed;
  }
  return `${trimmed}/v1`;
}

export function formatOllamaModelRef(modelName: string): string {
  const trimmed = modelName.trim();
  return trimmed.startsWith("ollama/") ? trimmed : `ollama/${trimmed}`;
}

export function stripOllamaModelRef(modelRef: string): string {
  const trimmed = modelRef.trim();
  return trimmed.startsWith("ollama/") ? trimmed.slice("ollama/".length) : trimmed;
}

export function formatLmStudioModelRef(modelName: string): string {
  return modelName.trim();
}

export function stripLmStudioModelRef(modelRef: string): string {
  return modelRef.trim();
}

export function getModelReadinessLabel(
  hasCredentials: boolean,
  hasStoredKey: boolean,
  defaultModel: string,
  probeSucceeded: boolean
): string {
  if (!hasCredentials) {
    return "Connect engine access";
  }
  if (!hasStoredKey) {
    return "Add provider key";
  }
  if (!defaultModel.trim()) {
    return "Choose a model";
  }
  return probeSucceeded ? "Ready for workflows" : "Test connection";
}
