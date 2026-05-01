import { describe, expect, it } from "vitest";

import { DEFAULT_MODEL_CONNECTION_BASELINE, type ModelConnectionForm } from "./helpers";
import {
  PROVIDER_PRESETS,
  applyProviderPresetToForm,
  getProviderPreset,
  inferProviderPresetId
} from "./presets";

function form(overrides: Partial<ModelConnectionForm> = {}): ModelConnectionForm {
  return {
    ...DEFAULT_MODEL_CONNECTION_BASELINE,
    apiKey: "",
    writeToEnvFile: true,
    removeStoredKey: false,
    ...overrides
  };
}

describe("provider presets", () => {
  it("defines beginner setup paths for cloud, local, and custom providers", () => {
    expect(PROVIDER_PRESETS.map((preset) => preset.id)).toEqual([
      "openrouter",
      "ollama",
      "lm-studio",
      "custom-openai"
    ]);
    for (const preset of PROVIDER_PRESETS) {
      expect(preset.name).toBeTruthy();
      expect(preset.description.length).toBeGreaterThan(20);
      expect(preset.recommendedModels.length).toBeGreaterThan(0);
    }
    expect(getProviderPreset("openrouter")?.baseUrlDefault).toContain("/v1");
    expect(getProviderPreset("ollama")?.baseUrlDefault).toBe("http://localhost:11434");
    expect(getProviderPreset("lm-studio")?.baseUrlDefault).toBe("http://localhost:1234/v1");
    expect(getProviderPreset("lm-studio")?.needsApiKey).toBe(false);
  });

  it("looks up and infers presets from base URLs", () => {
    expect(getProviderPreset("ollama")?.name).toBe("Ollama");
    expect(getProviderPreset("missing")).toBeNull();
    expect(inferProviderPresetId("http://localhost:11434/v1")).toBe("ollama");
    expect(inferProviderPresetId("http://localhost:1234/v1")).toBe("lm-studio");
    expect(inferProviderPresetId("https://openrouter.ai/api/v1")).toBe("openrouter");
    expect(inferProviderPresetId("https://example.com/v1")).toBe("custom-openai");
  });

  it("applies a local preset without carrying a typed cloud key into the local form", () => {
    const ollama = getProviderPreset("ollama");
    expect(ollama).not.toBeNull();

    const next = applyProviderPresetToForm(
      form({ apiKey: "sk-or-v1-secret", removeStoredKey: true }),
      ollama!
    );

    expect(next.baseUrl).toBe("http://localhost:11434");
    expect(next.defaultModel).toBe("ollama/qwen2.5-coder:7b");
    expect(next.apiKey).toBe("");
    expect(next.removeStoredKey).toBe(false);
  });
});
