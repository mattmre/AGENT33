import { describe, expect, it } from "vitest";

import {
  mapWorkflowEdgesToReactFlow,
  mapWorkflowNodesToReactFlow,
  type WorkflowEdge,
  type WorkflowNode
} from "./WorkflowGraph";

describe("mapWorkflowNodesToReactFlow", () => {
  it("maps nodes with position field", () => {
    const nodes: WorkflowNode[] = [
      {
        id: "node-1",
        name: "Start Node",
        action: "start",
        position: { x: 100, y: 200 },
        status: "active"
      }
    ];

    const result = mapWorkflowNodesToReactFlow(nodes);

    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("node-1");
    expect(result[0].position).toEqual({ x: 100, y: 200 });
    expect(result[0].data.label).toBe("Start Node");
    expect(result[0].data.action).toBe("start");
    expect(result[0].data.status).toBe("active");
  });

  it("maps nodes with x/y fields", () => {
    const nodes: WorkflowNode[] = [
      {
        id: "node-2",
        name: "Transform",
        action: "transform",
        x: 300,
        y: 400
      }
    ];

    const result = mapWorkflowNodesToReactFlow(nodes);

    expect(result).toHaveLength(1);
    expect(result[0].position).toEqual({ x: 300, y: 400 });
  });

  it("defaults to zero position when no coordinates provided", () => {
    const nodes: WorkflowNode[] = [
      {
        id: "node-3",
        name: "End Node",
        action: "end"
      }
    ];

    const result = mapWorkflowNodesToReactFlow(nodes);

    expect(result[0].position).toEqual({ x: 0, y: 0 });
  });

  it("uses name as label, falls back to id", () => {
    const nodes: WorkflowNode[] = [
      {
        id: "node-4",
        name: "Custom Name",
        action: "custom"
      },
      {
        id: "node-5",
        name: "",
        action: "test"
      }
    ];

    const result = mapWorkflowNodesToReactFlow(nodes);

    expect(result[0].data.label).toBe("Custom Name");
    expect(result[1].data.label).toBe("node-5");
  });

  it("includes metadata in node data", () => {
    const nodes: WorkflowNode[] = [
      {
        id: "node-6",
        name: "With Meta",
        action: "process",
        metadata: { timeout: 30, retries: 3 }
      }
    ];

    const result = mapWorkflowNodesToReactFlow(nodes);

    expect(result[0].data.metadata).toEqual({ timeout: 30, retries: 3 });
  });
});

describe("mapWorkflowEdgesToReactFlow", () => {
  it("maps edges correctly", () => {
    const edges: WorkflowEdge[] = [
      {
        id: "edge-1",
        source: "node-1",
        target: "node-2"
      },
      {
        id: "edge-2",
        source: "node-2",
        target: "node-3"
      }
    ];

    const result = mapWorkflowEdgesToReactFlow(edges);

    expect(result).toHaveLength(2);
    expect(result[0].id).toBe("edge-1");
    expect(result[0].source).toBe("node-1");
    expect(result[0].target).toBe("node-2");
    expect(result[0].type).toBe("smoothstep");
    expect(result[0].animated).toBe(false);

    expect(result[1].id).toBe("edge-2");
    expect(result[1].source).toBe("node-2");
    expect(result[1].target).toBe("node-3");
  });

  it("handles empty edge list", () => {
    const result = mapWorkflowEdgesToReactFlow([]);

    expect(result).toEqual([]);
  });
});
