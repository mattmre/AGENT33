import { apiRequest } from "../../lib/api";
import type { ApiResult } from "../../types";
import type {
  SkillDiscoveryResponse,
  WorkflowCreateResponse,
  WorkflowResolutionResponse,
  WorkflowStarterRequest
} from "./types";

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function asStringOrNull(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

export function asWorkflowCreateResponse(data: unknown): WorkflowCreateResponse | null {
  if (!isObject(data)) {
    return null;
  }
  if (
    typeof data.name !== "string" ||
    typeof data.version !== "string" ||
    typeof data.step_count !== "number" ||
    typeof data.created !== "boolean"
  ) {
    return null;
  }
  return {
    name: data.name,
    version: data.version,
    step_count: data.step_count,
    created: data.created
  };
}

export function asWorkflowResolutionResponse(data: unknown): WorkflowResolutionResponse | null {
  if (!isObject(data) || typeof data.query !== "string" || !Array.isArray(data.matches)) {
    return null;
  }
  const matches = data.matches
    .map((item) => {
      if (!isObject(item)) {
        return null;
      }
      if (
        typeof item.name !== "string" ||
        typeof item.description !== "string" ||
        typeof item.score !== "number" ||
        typeof item.source !== "string" ||
        typeof item.version !== "string" ||
        !isStringArray(item.tags) ||
        typeof item.source_path !== "string"
      ) {
        return null;
      }
      return {
        name: item.name,
        description: item.description,
        score: item.score,
        source: item.source,
        version: item.version,
        tags: item.tags,
        source_path: item.source_path,
        pack: asStringOrNull(item.pack)
      };
    })
    .filter((item): item is NonNullable<typeof item> => item !== null);
  return matches.length === data.matches.length ? { query: data.query, matches } : null;
}

export function asSkillDiscoveryResponse(data: unknown): SkillDiscoveryResponse | null {
  if (!isObject(data) || typeof data.query !== "string" || !Array.isArray(data.matches)) {
    return null;
  }
  const matches = data.matches
    .map((item) => {
      if (!isObject(item)) {
        return null;
      }
      if (
        typeof item.name !== "string" ||
        typeof item.description !== "string" ||
        typeof item.score !== "number" ||
        typeof item.version !== "string" ||
        !isStringArray(item.tags)
      ) {
        return null;
      }
      return {
        name: item.name,
        description: item.description,
        score: item.score,
        version: item.version,
        tags: item.tags,
        pack: asStringOrNull(item.pack)
      };
    })
    .filter((item): item is NonNullable<typeof item> => item !== null);
  return matches.length === data.matches.length ? { query: data.query, matches } : null;
}

export function resolveWorkflows(query: string, token: string, apiKey: string): Promise<ApiResult> {
  return apiRequest({
    method: "GET",
    path: "/v1/discovery/workflows/resolve",
    token,
    apiKey,
    query: { q: query, limit: "5" }
  });
}

export function discoverSkills(query: string, token: string, apiKey: string): Promise<ApiResult> {
  return apiRequest({
    method: "GET",
    path: "/v1/discovery/skills",
    token,
    apiKey,
    query: { q: query, limit: "5" }
  });
}

export function createWorkflow(
  body: WorkflowStarterRequest,
  token: string,
  apiKey: string
): Promise<ApiResult> {
  return apiRequest({
    method: "POST",
    path: "/v1/workflows/",
    token,
    apiKey,
    body: JSON.stringify(body)
  });
}
