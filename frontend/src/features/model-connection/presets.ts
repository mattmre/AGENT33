import { OPENROUTER_STABLE_DEFAULT_MODEL } from "../../lib/openrouterModels";
import type { ModelConnectionForm } from "./helpers";

export type ProviderPresetId = "openrouter" | "ollama" | "lm-studio" | "custom-openai";

export interface ProviderModelRecommendation {
  id: string;
  name: string;
  badgeLabel: string;
  description: string;
  capabilities: string[];
  contextLength: number | null;
  isFree: boolean;
}

export interface ProviderPreset {
  id: ProviderPresetId;
  name: string;
  badge: string;
  description: string;
  bestFor: string;
  setupTime: string;
  baseUrlDefault: string;
  apiKeyLabel: string;
  apiKeyPlaceholder: string;
  apiKeyHint: string;
  needsApiKey: boolean;
  recommendedModels: ProviderModelRecommendation[];
}

export const PROVIDER_PRESETS: ProviderPreset[] = [
  {
    id: "openrouter",
    name: "OpenRouter",
    badge: "Cloud",
    description: "Use one API key to reach hosted models. Best first path for most users.",
    bestFor: "Fastest cloud setup",
    setupTime: "2 min",
    baseUrlDefault: "https://openrouter.ai/api/v1",
    apiKeyLabel: "OpenRouter API key",
    apiKeyPlaceholder: "sk-or-v1-...",
    apiKeyHint: "Paste a key from openrouter.ai; AGENT-33 never shows it after saving.",
    needsApiKey: true,
    recommendedModels: [
      {
        id: OPENROUTER_STABLE_DEFAULT_MODEL,
        name: "Qwen3 Coder Flash",
        badgeLabel: "Stable default",
        description: "A fast coding model for first builds, fixes, and workflow automation.",
        capabilities: ["code", "fast"],
        contextLength: 131_072,
        isFree: false
      },
      {
        id: "openrouter/qwen/qwen3-coder-30b-a3b-instruct",
        name: "Qwen3 Coder 30B",
        badgeLabel: "Bigger coder",
        description: "More capacity for larger implementation and planning tasks.",
        capabilities: ["code"],
        contextLength: 131_072,
        isFree: false
      },
      {
        id: "openrouter/auto",
        name: "OpenRouter Auto",
        badgeLabel: "Auto route",
        description: "Lets OpenRouter choose a compatible model when you are unsure.",
        capabilities: ["easy"],
        contextLength: null,
        isFree: false
      }
    ]
  },
  {
    id: "ollama",
    name: "Ollama",
    badge: "Local",
    description: "Run a model on your own computer. Leave the API key blank by default.",
    bestFor: "Private local testing",
    setupTime: "5 min",
    baseUrlDefault: "http://localhost:11434",
    apiKeyLabel: "Local API key",
    apiKeyPlaceholder: "Leave blank for Ollama",
    apiKeyHint: "Most Ollama setups do not need a key. Start Ollama before testing.",
    needsApiKey: false,
    recommendedModels: [
      {
        id: "ollama/qwen2.5-coder:7b",
        name: "Qwen2.5 Coder 7B",
        badgeLabel: "Local coder",
        description: "Good starter model for coding on CPU or small GPUs.",
        capabilities: ["code", "local"],
        contextLength: 32_768,
        isFree: true
      },
      {
        id: "ollama/llama3.1:8b",
        name: "Llama 3.1 8B",
        badgeLabel: "General local",
        description: "Useful for planning, summaries, and beginner experimentation.",
        capabilities: ["local"],
        contextLength: 128_000,
        isFree: true
      }
    ]
  },
  {
    id: "lm-studio",
    name: "LM Studio",
    badge: "Local",
    description: "Use downloaded model files through LM Studio's local server.",
    bestFor: "Point-and-click local models",
    setupTime: "5 min",
    baseUrlDefault: "http://localhost:1234/v1",
    apiKeyLabel: "LM Studio API key",
    apiKeyPlaceholder: "Leave blank unless LM Studio asks",
    apiKeyHint: "Start the LM Studio local server, then choose the loaded model name.",
    needsApiKey: false,
    recommendedModels: [
      {
        id: "lmstudio/local-model",
        name: "Loaded LM Studio model",
        badgeLabel: "Use loaded model",
        description: "Matches the model currently served by LM Studio.",
        capabilities: ["local", "easy"],
        contextLength: null,
        isFree: true
      },
      {
        id: "lmstudio/qwen2.5-coder-7b-instruct",
        name: "Qwen2.5 Coder 7B Instruct",
        badgeLabel: "Starter coder",
        description: "A practical local coding choice if you have it downloaded.",
        capabilities: ["code", "local"],
        contextLength: 32_768,
        isFree: true
      }
    ]
  },
  {
    id: "custom-openai",
    name: "OpenAI-compatible",
    badge: "Custom",
    description: "Connect any provider that accepts OpenAI-style chat requests.",
    bestFor: "Existing provider accounts",
    setupTime: "3 min",
    baseUrlDefault: "https://api.openai.com/v1",
    apiKeyLabel: "Provider API key",
    apiKeyPlaceholder: "Paste your provider key",
    apiKeyHint: "Use the endpoint and model name from your provider dashboard.",
    needsApiKey: true,
    recommendedModels: [
      {
        id: "gpt-4o-mini",
        name: "Provider default small model",
        badgeLabel: "Fast start",
        description: "A low-cost default for quick setup checks and smaller workflows.",
        capabilities: ["fast", "easy"],
        contextLength: 128_000,
        isFree: false
      },
      {
        id: "gpt-4.1",
        name: "Provider larger model",
        badgeLabel: "Higher capacity",
        description: "Use a stronger model when your provider account supports it.",
        capabilities: ["code"],
        contextLength: 1_000_000,
        isFree: false
      }
    ]
  }
];

export function getProviderPreset(id: string): ProviderPreset | null {
  return PROVIDER_PRESETS.find((preset) => preset.id === id) ?? null;
}

export function inferProviderPresetId(baseUrl: string): ProviderPresetId {
  const normalized = baseUrl.trim().toLowerCase();
  if (normalized.includes("localhost:11434") || normalized.includes("127.0.0.1:11434")) {
    return "ollama";
  }
  if (normalized.includes("localhost:1234") || normalized.includes("127.0.0.1:1234")) {
    return "lm-studio";
  }
  if (normalized.includes("openrouter.ai")) {
    return "openrouter";
  }
  return "custom-openai";
}

export function applyProviderPresetToForm(
  form: ModelConnectionForm,
  preset: ProviderPreset
): ModelConnectionForm {
  const [firstModel] = preset.recommendedModels;
  return {
    ...form,
    defaultModel: firstModel?.id ?? form.defaultModel,
    baseUrl: preset.baseUrlDefault,
    apiKey: preset.needsApiKey ? form.apiKey : "",
    removeStoredKey: preset.needsApiKey ? form.removeStoredKey : false
  };
}
