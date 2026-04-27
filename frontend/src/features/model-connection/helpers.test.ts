import { describe, expect, it } from "vitest";

import {
  DEFAULT_MODEL_CONNECTION_BASELINE,
  buildOpenRouterConfigChanges,
  buildOpenRouterProbePayload,
  getModelReadinessLabel,
  type ModelConnectionForm
} from "./helpers";

function form(overrides: Partial<ModelConnectionForm> = {}): ModelConnectionForm {
  return {
    ...DEFAULT_MODEL_CONNECTION_BASELINE,
    apiKey: "",
    writeToEnvFile: true,
    removeStoredKey: false,
    ...overrides
  };
}

describe("model connection helpers", () => {
  it("builds only changed OpenRouter config values", () => {
    const changes = buildOpenRouterConfigChanges(
      form({ defaultModel: "qwen/qwen3-32b", apiKey: "sk-test" }),
      DEFAULT_MODEL_CONNECTION_BASELINE
    );

    expect(changes.default_model).toBe("openrouter/qwen/qwen3-32b");
    expect(changes.openrouter_api_key).toBe("sk-test");
    expect(changes.openrouter_base_url).toBeUndefined();
  });

  it("builds a probe payload with normalized model and transient key", () => {
    const payload = buildOpenRouterProbePayload(form({ defaultModel: "qwen/qwen3-32b", apiKey: "sk-test" }));

    expect(payload.default_model).toBe("openrouter/qwen/qwen3-32b");
    expect(payload.openrouter_api_key).toBe("sk-test");
    expect(payload.openrouter_base_url).toBe(DEFAULT_MODEL_CONNECTION_BASELINE.baseUrl);
  });

  it("summarizes model readiness in user-facing states", () => {
    expect(getModelReadinessLabel(false, false, "", false)).toBe("Connect engine access");
    expect(getModelReadinessLabel(true, false, "", false)).toBe("Add provider key");
    expect(getModelReadinessLabel(true, true, "", false)).toBe("Choose a model");
    expect(getModelReadinessLabel(true, true, "openrouter/qwen/qwen3-32b", true)).toBe(
      "Ready for workflows"
    );
  });
});
