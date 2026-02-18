import { apiRequest } from "../../lib/api";
import type { ApiResult } from "../../types";
import type {
  OperationsHubControlAction,
  OperationsHubProcessAction,
  OperationsHubProcessDetail,
  OperationsHubProcessSummary,
  OperationsHubResponse
} from "./types";

interface ProcessSummaryCandidate {
  id: string;
  type: string;
  status: string;
  started_at: string;
  name: string;
  metadata?: unknown;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isProcessSummary(value: unknown): value is ProcessSummaryCandidate {
  if (!isObject(value)) {
    return false;
  }
  return (
    typeof value.id === "string" &&
    typeof value.type === "string" &&
    typeof value.status === "string" &&
    typeof value.started_at === "string" &&
    typeof value.name === "string"
  );
}

function toProcessSummary(value: unknown): OperationsHubProcessSummary | null {
  if (!isProcessSummary(value)) {
    return null;
  }
  const metadata =
    value.metadata !== undefined && isObject(value.metadata)
      ? value.metadata
      : undefined;
  return {
    id: value.id,
    type: value.type,
    status: value.status,
    started_at: value.started_at,
    name: value.name,
    metadata
  };
}

function toProcessActions(value: unknown): OperationsHubProcessAction[] | undefined {
  if (!Array.isArray(value)) {
    return undefined;
  }
  const actions = value
    .map((item) => {
      if (!isObject(item)) {
        return null;
      }
      if (
        typeof item.step_id !== "string" ||
        typeof item.action_count !== "number" ||
        (item.completed_at !== null && typeof item.completed_at !== "string")
      ) {
        return null;
      }
      return {
        step_id: item.step_id,
        action_count: item.action_count,
        completed_at: item.completed_at
      };
    })
    .filter((item): item is OperationsHubProcessAction => item !== null);
  return actions;
}

export function asOperationsHubResponse(data: unknown): OperationsHubResponse | null {
  if (!isObject(data)) {
    return null;
  }
  if (
    typeof data.timestamp !== "string" ||
    typeof data.active_count !== "number" ||
    !Array.isArray(data.processes)
  ) {
    return null;
  }
  const processes = data.processes
    .map((item) => toProcessSummary(item))
    .filter((item): item is OperationsHubProcessSummary => item !== null);
  if (processes.length !== data.processes.length) {
    return null;
  }
  return {
    timestamp: data.timestamp,
    active_count: data.active_count,
    processes
  };
}

export function asOperationsHubDetail(data: unknown): OperationsHubProcessDetail | null {
  const summary = toProcessSummary(data);
  if (summary === null || !isObject(data)) {
    return null;
  }
  const actions = data.actions !== undefined ? toProcessActions(data.actions) : undefined;
  if (data.actions !== undefined && actions === undefined) {
    return null;
  }
  return {
    ...summary,
    actions
  };
}

export async function fetchOperationsHub(token: string, apiKey: string): Promise<ApiResult> {
  return apiRequest({
    method: "GET",
    path: "/v1/operations/hub",
    token,
    apiKey
  });
}

export async function fetchProcessDetail(
  processId: string,
  token: string,
  apiKey: string
): Promise<ApiResult> {
  return apiRequest({
    method: "GET",
    path: "/v1/operations/processes/{process_id}",
    pathParams: { process_id: processId },
    token,
    apiKey
  });
}

export async function controlProcess(
  processId: string,
  action: OperationsHubControlAction,
  token: string,
  apiKey: string
): Promise<ApiResult> {
  return apiRequest({
    method: "POST",
    path: "/v1/operations/processes/{process_id}/control",
    pathParams: { process_id: processId },
    body: JSON.stringify({ action }),
    token,
    apiKey
  });
}
