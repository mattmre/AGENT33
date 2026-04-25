import { apiRequest } from "../../lib/api";
import type { ApiResult } from "../../types";
import type {
  IngestionAssetHistoryEntry,
  IngestionAssetHistoryResponse,
  IngestionAssetSummary,
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

interface IngestionAssetCandidate {
  id: string;
  name: string;
  asset_type: string;
  status: string;
  confidence: string;
  source_uri: string | null;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  validated_at: string | null;
  published_at: string | null;
  revoked_at: string | null;
  revocation_reason: string | null;
  metadata: unknown;
}

interface IngestionAssetHistoryEntryCandidate {
  asset_id: string;
  tenant_id: string;
  from_status: string;
  to_status: string;
  event_type: string;
  operator: string;
  reason: string;
  details: unknown;
  occurred_at: string;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isStringOrNull(value: unknown): value is string | null {
  return typeof value === "string" || value === null;
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

function isIngestionAsset(value: unknown): value is IngestionAssetCandidate {
  if (!isObject(value)) {
    return false;
  }
  return (
    typeof value.id === "string" &&
    typeof value.name === "string" &&
    typeof value.asset_type === "string" &&
    typeof value.status === "string" &&
    typeof value.confidence === "string" &&
    isStringOrNull(value.source_uri) &&
    typeof value.tenant_id === "string" &&
    typeof value.created_at === "string" &&
    typeof value.updated_at === "string" &&
    isStringOrNull(value.validated_at) &&
    isStringOrNull(value.published_at) &&
    isStringOrNull(value.revoked_at) &&
    isStringOrNull(value.revocation_reason) &&
    isObject(value.metadata)
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

function toIngestionAsset(value: unknown): IngestionAssetSummary | null {
  if (!isIngestionAsset(value)) {
    return null;
  }
  const metadata = value.metadata as Record<string, unknown>;
  return {
    id: value.id,
    name: value.name,
    asset_type: value.asset_type,
    status: value.status,
    confidence: value.confidence,
    source_uri: value.source_uri,
    tenant_id: value.tenant_id,
    created_at: value.created_at,
    updated_at: value.updated_at,
    validated_at: value.validated_at,
    published_at: value.published_at,
    revoked_at: value.revoked_at,
    revocation_reason: value.revocation_reason,
    metadata
  };
}

function toHistoryEntry(value: unknown): IngestionAssetHistoryEntry | null {
  if (!isObject(value)) {
    return null;
  }
  const candidate = value as Partial<IngestionAssetHistoryEntryCandidate>;
  if (
    typeof candidate.asset_id !== "string" ||
    typeof candidate.tenant_id !== "string" ||
    typeof candidate.from_status !== "string" ||
    typeof candidate.to_status !== "string" ||
    typeof candidate.event_type !== "string" ||
    typeof candidate.operator !== "string" ||
    typeof candidate.reason !== "string" ||
    !isObject(candidate.details) ||
    typeof candidate.occurred_at !== "string"
  ) {
    return null;
  }
  return {
    asset_id: candidate.asset_id,
    tenant_id: candidate.tenant_id,
    from_status: candidate.from_status,
    to_status: candidate.to_status,
    event_type: candidate.event_type,
    operator: candidate.operator,
    reason: candidate.reason,
    details: candidate.details,
    occurred_at: candidate.occurred_at
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

export function asIngestionAssetHistoryResponse(data: unknown): IngestionAssetHistoryResponse | null {
  if (!isObject(data) || !Array.isArray(data.history)) {
    return null;
  }
  const asset = toIngestionAsset(data.asset);
  if (asset === null) {
    return null;
  }
  const history = data.history
    .map((item) => toHistoryEntry(item))
    .filter((item): item is IngestionAssetHistoryEntry => item !== null);
  if (history.length !== data.history.length) {
    return null;
  }
  return {
    asset,
    history
  };
}

export function asIngestionAssetList(data: unknown): IngestionAssetSummary[] | null {
  if (!Array.isArray(data)) {
    return null;
  }
  const assets = data
    .map((item) => toIngestionAsset(item))
    .filter((item): item is IngestionAssetSummary => item !== null);
  return assets.length === data.length ? assets : null;
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

export async function fetchReviewQueue(token: string, apiKey: string): Promise<ApiResult> {
  return apiRequest({
    method: "GET",
    path: "/v1/ingestion/review-queue",
    token,
    apiKey
  });
}

export async function fetchAssetHistory(
  assetId: string,
  token: string,
  apiKey: string
): Promise<ApiResult> {
  return apiRequest({
    method: "GET",
    path: "/v1/ingestion/candidates/{asset_id}/history",
    pathParams: { asset_id: assetId },
    token,
    apiKey
  });
}

export async function approveReviewAsset(
  assetId: string,
  operator: string,
  reason: string,
  token: string,
  apiKey: string
): Promise<ApiResult> {
  return apiRequest({
    method: "POST",
    path: "/v1/ingestion/review-queue/{asset_id}/approve",
    pathParams: { asset_id: assetId },
    body: JSON.stringify({ operator, reason }),
    token,
    apiKey
  });
}

export async function rejectReviewAsset(
  assetId: string,
  operator: string,
  reason: string,
  token: string,
  apiKey: string
): Promise<ApiResult> {
  return apiRequest({
    method: "POST",
    path: "/v1/ingestion/review-queue/{asset_id}/reject",
    pathParams: { asset_id: assetId },
    body: JSON.stringify({ operator, reason }),
    token,
    apiKey
  });
}
