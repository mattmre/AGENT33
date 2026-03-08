import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { OperationConfig } from "../types";

const {
  apiRequestMock,
  connectWorkflowLiveTransportMock,
  shouldRefreshWorkflowGraphMock,
  isWorkflowTerminalEventMock
} = vi.hoisted(() => ({
  apiRequestMock: vi.fn(),
  connectWorkflowLiveTransportMock: vi.fn(),
  shouldRefreshWorkflowGraphMock: vi.fn((event: { type: string }) => event.type !== "heartbeat"),
  isWorkflowTerminalEventMock: vi.fn(
    (event: { type: string }) =>
      event.type === "workflow_completed" || event.type === "workflow_failed"
  )
}));

vi.mock("../lib/api", () => ({
  apiRequest: apiRequestMock
}));

vi.mock("../lib/workflowLiveTransport", () => ({
  connectWorkflowLiveTransport: connectWorkflowLiveTransportMock,
  shouldRefreshWorkflowGraph: shouldRefreshWorkflowGraphMock,
  isWorkflowTerminalEvent: isWorkflowTerminalEventMock
}));

vi.mock("./WorkflowGraph", () => ({
  WorkflowGraph: ({ data }: { data: { workflow_id: string; nodes: unknown[] } }) => (
    <div data-testid="workflow-graph">
      {data.workflow_id}:{data.nodes.length}
    </div>
  )
}));

import { OperationCard } from "./OperationCard";

const workflowExecuteOperation: OperationConfig = {
  id: "workflows-execute",
  title: "Execute Workflow",
  method: "POST",
  path: "/v1/workflows/{name}/execute",
  description: "Execute a workflow.",
  defaultPathParams: { name: "hello-flow" },
  defaultQuery: {},
  defaultBody: JSON.stringify({ inputs: { name: "AGENT-33" } }, null, 2),
  uxHint: "workflow-execute"
};

describe("OperationCard", () => {
  beforeEach(() => {
    apiRequestMock.mockReset();
    connectWorkflowLiveTransportMock.mockReset();
    shouldRefreshWorkflowGraphMock.mockClear();
    isWorkflowTerminalEventMock.mockClear();
  });

  it("wires single-run workflow execution to graph fetch and live refreshes", async () => {
    vi.spyOn(globalThis.crypto, "randomUUID").mockReturnValue(
      "11111111-1111-4111-8111-111111111111"
    );

    let liveEventHandler: ((event: { type: string }) => Promise<void> | void) | undefined;
    const disconnectMock = vi.fn();
    connectWorkflowLiveTransportMock.mockImplementation(
      (options: { onEvent: (event: { type: string }) => Promise<void> | void }) => {
        liveEventHandler = options.onEvent;
        return { close: disconnectMock };
      }
    );

    apiRequestMock
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        durationMs: 10,
        url: "/v1/workflows/hello-flow/execute",
        data: { run_id: "11111111-1111-4111-8111-111111111111", status: "success" }
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        durationMs: 5,
        url: "/v1/visualizations/workflows/hello-flow/graph?run_id=11111111-1111-4111-8111-111111111111",
        data: {
          workflow_id: "hello-flow",
          nodes: [{ id: "step-a" }],
          edges: []
        }
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        durationMs: 5,
        url: "/v1/visualizations/workflows/hello-flow/graph?run_id=11111111-1111-4111-8111-111111111111",
        data: {
          workflow_id: "hello-flow",
          nodes: [{ id: "step-a" }, { id: "step-b" }],
          edges: []
        }
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        durationMs: 5,
        url: "/v1/visualizations/workflows/hello-flow/graph?run_id=11111111-1111-4111-8111-111111111111",
        data: {
          workflow_id: "hello-flow",
          nodes: [{ id: "step-a" }, { id: "step-b" }, { id: "step-c" }],
          edges: []
        }
      });

    const onResult = vi.fn();
    render(
      <OperationCard
        operation={workflowExecuteOperation}
        token="jwt-token"
        apiKey=""
        onResult={onResult}
      />
    );

    await userEvent.click(screen.getByRole("button", { name: "Run" }));

    await waitFor(() => expect(apiRequestMock).toHaveBeenCalledTimes(2));
    expect(JSON.parse(apiRequestMock.mock.calls[0][0].body as string)).toMatchObject({
      inputs: { name: "AGENT-33" },
      run_id: "11111111-1111-4111-8111-111111111111"
    });
    expect(apiRequestMock.mock.calls[1][0]).toMatchObject({
      method: "GET",
      path: "/v1/visualizations/workflows/{workflow_id}/graph",
      pathParams: { workflow_id: "hello-flow" },
      query: { run_id: "11111111-1111-4111-8111-111111111111" }
    });
    expect(connectWorkflowLiveTransportMock).toHaveBeenCalledWith(
      expect.objectContaining({ runId: "11111111-1111-4111-8111-111111111111", token: "jwt-token" })
    );
    expect(screen.getByTestId("workflow-graph")).toHaveTextContent("hello-flow:1");

    await act(async () => {
      await liveEventHandler?.({ type: "heartbeat" });
    });
    expect(apiRequestMock).toHaveBeenCalledTimes(2);

    await act(async () => {
      await liveEventHandler?.({ type: "step_completed" });
    });
    await waitFor(() => expect(apiRequestMock).toHaveBeenCalledTimes(3));
    expect(screen.getByTestId("workflow-graph")).toHaveTextContent("hello-flow:2");

    await act(async () => {
      await liveEventHandler?.({ type: "workflow_completed" });
    });
    await waitFor(() => expect(apiRequestMock).toHaveBeenCalledTimes(4));
    expect(disconnectMock).toHaveBeenCalled();
    expect(screen.getByTestId("workflow-graph")).toHaveTextContent("hello-flow:3");
    expect(onResult).toHaveBeenCalledTimes(1);
  });

  it("keeps repeat-mode execution on the existing non-live path", async () => {
    apiRequestMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      durationMs: 10,
      url: "/v1/workflows/hello-flow/execute",
      data: { status: "success", executions: 2 }
    });

    render(
      <OperationCard
        operation={workflowExecuteOperation}
        token="jwt-token"
        apiKey=""
        onResult={vi.fn()}
      />
    );

    await userEvent.selectOptions(screen.getByLabelText("Mode"), "repeat");
    await userEvent.click(screen.getByRole("button", { name: "Run" }));

    await waitFor(() => expect(apiRequestMock).toHaveBeenCalledTimes(1));
    expect(JSON.parse(apiRequestMock.mock.calls[0][0].body as string)).toMatchObject({
      inputs: { name: "AGENT-33" },
      repeat_count: 3,
      autonomous: false
    });
    expect(JSON.parse(apiRequestMock.mock.calls[0][0].body as string)).not.toHaveProperty("run_id");
    expect(connectWorkflowLiveTransportMock).not.toHaveBeenCalled();
  });
});
