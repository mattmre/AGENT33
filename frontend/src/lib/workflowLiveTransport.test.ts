import { waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  buildWorkflowWebSocketUrl,
  connectWorkflowLiveTransport
} from "./workflowLiveTransport";

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  readyState = MockWebSocket.CONNECTING;

  constructor(public readonly url: string) {
    MockWebSocket.instances.push(this);
  }

  close(): void {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  }

  emitOpen(): void {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.();
  }

  emitMessage(data: unknown): void {
    this.onmessage?.({ data: JSON.stringify(data) });
  }

  emitError(): void {
    this.onerror?.();
  }

  emitClose(): void {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  }
}

function buildSseResponse(bodyText: string): Response {
  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(encoder.encode(bodyText));
      controller.close();
    }
  });
  return new Response(body, {
    status: 200,
    headers: { "content-type": "text/event-stream" }
  });
}

describe("workflowLiveTransport", () => {
  afterEach(() => {
    MockWebSocket.instances = [];
    delete window.__AGENT33_CONFIG__;
  });

  it("builds a run-scoped workflow websocket url", () => {
    expect(
      buildWorkflowWebSocketUrl("https://agent33.test", "run-123", "abc-token")
    ).toBe("wss://agent33.test/v1/workflows/run-123/ws?token=abc-token");
  });

  it("prefers websocket when a bearer token is available", () => {
    vi.stubGlobal("WebSocket", MockWebSocket);
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const onEvent = vi.fn();

    const connection = connectWorkflowLiveTransport({
      runId: "run-ws",
      token: "jwt-token",
      onEvent
    });

    expect(MockWebSocket.instances).toHaveLength(1);
    MockWebSocket.instances[0].emitOpen();
    MockWebSocket.instances[0].emitMessage({
      type: "sync",
      run_id: "run-ws",
      workflow_name: "wf-live",
      timestamp: 1
    });

    expect(fetchMock).not.toHaveBeenCalled();
    expect(onEvent).toHaveBeenCalledWith(
      expect.objectContaining({ type: "sync", run_id: "run-ws" })
    );

    connection.close();
  });

  it("falls back to authenticated SSE when websocket cannot connect", async () => {
    vi.stubGlobal("WebSocket", MockWebSocket);
    const fetchMock = vi.fn().mockResolvedValue(
      buildSseResponse(
        'data: {"type":"sync","run_id":"run-fallback","workflow_name":"wf-live","timestamp":1}\n\n'
      )
    );
    vi.stubGlobal("fetch", fetchMock);
    const onEvent = vi.fn();

    connectWorkflowLiveTransport({
      runId: "run-fallback",
      token: "jwt-token",
      onEvent
    });

    expect(MockWebSocket.instances).toHaveLength(1);
    MockWebSocket.instances[0].emitError();
    MockWebSocket.instances[0].emitClose();

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    await waitFor(() =>
      expect(onEvent).toHaveBeenCalledWith(
        expect.objectContaining({ type: "sync", run_id: "run-fallback" })
      )
    );
  });

  it("uses SSE directly for api-key-only workflow live updates", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      buildSseResponse(
        'data: {"type":"sync","run_id":"run-sse","workflow_name":"wf-live","timestamp":1}\n\n'
      )
    );
    vi.stubGlobal("fetch", fetchMock);
    const webSocketSpy = vi.fn();
    vi.stubGlobal("WebSocket", webSocketSpy);
    const onEvent = vi.fn();

    connectWorkflowLiveTransport({
      runId: "run-sse",
      apiKey: "api-key",
      onEvent
    });

    expect(webSocketSpy).not.toHaveBeenCalled();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(fetchMock.mock.calls[0][1]).toMatchObject({
      headers: {
        Accept: "text/event-stream",
        "X-API-Key": "api-key"
      }
    });
    await waitFor(() =>
      expect(onEvent).toHaveBeenCalledWith(
        expect.objectContaining({ type: "sync", run_id: "run-sse" })
      )
    );
  });
});
