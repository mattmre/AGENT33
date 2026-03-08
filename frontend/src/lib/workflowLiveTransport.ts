import { buildUrl, getRuntimeConfig } from "./api";
import type { WorkflowLiveEvent, WorkflowLiveTransportConnection } from "../types";

export interface WorkflowLiveTransportOptions {
  runId: string;
  token?: string;
  apiKey?: string;
  onEvent: (event: WorkflowLiveEvent) => void;
  onError?: (error: Error) => void;
}

const WORKFLOW_GRAPH_REFRESH_EVENT_TYPES = new Set([
  "sync",
  "step_started",
  "step_completed",
  "step_failed",
  "step_skipped",
  "step_retrying",
  "workflow_completed",
  "workflow_failed"
]);

const WORKFLOW_TERMINAL_EVENT_TYPES = new Set(["workflow_completed", "workflow_failed"]);

export function shouldRefreshWorkflowGraph(event: WorkflowLiveEvent): boolean {
  return WORKFLOW_GRAPH_REFRESH_EVENT_TYPES.has(event.type);
}

export function isWorkflowTerminalEvent(event: WorkflowLiveEvent): boolean {
  return WORKFLOW_TERMINAL_EVENT_TYPES.has(event.type);
}

export function connectWorkflowLiveTransport(
  options: WorkflowLiveTransportOptions
): WorkflowLiveTransportConnection {
  const { API_BASE_URL } = getRuntimeConfig();

  let abortController: AbortController | null = null;
  abortController = new AbortController();
  void streamWorkflowEventsOverSse(API_BASE_URL, options, abortController.signal);

  return {
    close: () => {
      abortController?.abort();
    }
  };
}

export function buildWorkflowWebSocketUrl(baseUrl: string, runId: string, _token: string): string {
  void _token;
  const httpUrl = buildUrl(baseUrl, "/v1/workflows/{run_id}/ws", { run_id: runId });
  const url = new URL(httpUrl);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}

async function streamWorkflowEventsOverSse(
  baseUrl: string,
  options: WorkflowLiveTransportOptions,
  signal: AbortSignal
): Promise<void> {
  let reader: ReadableStreamDefaultReader<Uint8Array> | null = null;
  try {
    const response = await fetch(
      buildUrl(baseUrl, "/v1/workflows/{run_id}/events", { run_id: options.runId }),
      {
        headers: buildWorkflowLiveHeaders(options),
        signal
      }
    );

    if (!response.ok || !response.body) {
      throw new Error(`Workflow SSE request failed with status ${response.status}`);
    }

    reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (!signal.aborted) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) {
        const event = parseWorkflowSseChunk(part);
        if (event) {
          options.onEvent(event);
        }
      }
    }
  } catch (error) {
    if (!signal.aborted) {
      options.onError?.(toError(error, "Workflow live SSE connection failed"));
    }
  } finally {
    await reader?.cancel().catch(() => undefined);
  }
}

function buildWorkflowLiveHeaders(
  options: Pick<WorkflowLiveTransportOptions, "token" | "apiKey">
): HeadersInit {
  const headers: Record<string, string> = {
    Accept: "text/event-stream"
  };
  if (options.token?.trim()) {
    headers.Authorization = `Bearer ${options.token.trim()}`;
  }
  if (options.apiKey?.trim()) {
    headers["X-API-Key"] = options.apiKey.trim();
  }
  return headers;
}

function parseWorkflowSseChunk(chunk: string): WorkflowLiveEvent | null {
  const dataLines = chunk
    .split("\n")
    .filter((line) => line.startsWith("data: "))
    .map((line) => line.slice(6));

  if (dataLines.length === 0) {
    return null;
  }

  return JSON.parse(dataLines.join("\n")) as WorkflowLiveEvent;
}

function toError(error: unknown, fallbackMessage: string): Error {
  if (error instanceof Error) {
    return error;
  }
  return new Error(fallbackMessage);
}
