import { describe, expect, it } from "vitest";

import {
  getRunningNodeIds,
  hasActiveNodes,
  mapWorkflowEdgesToReactFlow,
  mapWorkflowNodesToReactFlow,
  type WorkflowEdge,
  type WorkflowNode
} from "./WorkflowGraph";

import { statusToColor } from "./WorkflowStatusNode";

// ---------------------------------------------------------------------------
// mapWorkflowNodesToReactFlow
// ---------------------------------------------------------------------------
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

  it("sets node type to workflowStatus for all nodes", () => {
    const nodes: WorkflowNode[] = [
      { id: "a", name: "A", action: "run", status: "success" },
      { id: "b", name: "B", action: "run", status: "pending" }
    ];

    const result = mapWorkflowNodesToReactFlow(nodes);

    for (const node of result) {
      expect(node.type).toBe("workflowStatus");
    }
  });
});

// ---------------------------------------------------------------------------
// statusToColor — node status → border color mapping
// ---------------------------------------------------------------------------
describe("statusToColor", () => {
  it("returns green for success", () => {
    expect(statusToColor("success")).toBe("#22c55e");
  });

  it("returns red for failed", () => {
    expect(statusToColor("failed")).toBe("#ef4444");
  });

  it("returns blue for running", () => {
    expect(statusToColor("running")).toBe("#3b82f6");
  });

  it("returns gray for pending", () => {
    expect(statusToColor("pending")).toBe("#9ca3af");
  });

  it("returns gray for undefined (default)", () => {
    expect(statusToColor(undefined)).toBe("#9ca3af");
  });

  it("returns gray for unknown status strings", () => {
    expect(statusToColor("cancelled")).toBe("#9ca3af");
    expect(statusToColor("")).toBe("#9ca3af");
  });
});

// ---------------------------------------------------------------------------
// mapWorkflowEdgesToReactFlow — edge animation detection
// ---------------------------------------------------------------------------
describe("mapWorkflowEdgesToReactFlow", () => {
  const edges: WorkflowEdge[] = [
    { id: "e1", source: "a", target: "b" },
    { id: "e2", source: "b", target: "c" },
    { id: "e3", source: "c", target: "d" }
  ];

  it("maps edges with type smoothstep", () => {
    const result = mapWorkflowEdgesToReactFlow(edges);

    expect(result).toHaveLength(3);
    expect(result[0].type).toBe("smoothstep");
  });

  it("sets animated=false when no running node ids provided", () => {
    const result = mapWorkflowEdgesToReactFlow(edges);

    for (const edge of result) {
      expect(edge.animated).toBe(false);
    }
  });

  it("sets animated=true on edges whose source is a running node", () => {
    const running = new Set(["b"]);
    const result = mapWorkflowEdgesToReactFlow(edges, running);

    // e1: source=a, target=b → animated (target is running)
    expect(result[0].animated).toBe(true);
    // e2: source=b → animated (source is running)
    expect(result[1].animated).toBe(true);
    // e3: source=c, target=d → NOT animated
    expect(result[2].animated).toBe(false);
  });

  it("sets animated=true on edges whose target is a running node", () => {
    const running = new Set(["c"]);
    const result = mapWorkflowEdgesToReactFlow(edges, running);

    // e2: target=c → animated
    expect(result[1].animated).toBe(true);
    // e3: source=c → animated
    expect(result[2].animated).toBe(true);
    // e1: neither → not animated
    expect(result[0].animated).toBe(false);
  });

  it("handles empty edge list", () => {
    const result = mapWorkflowEdgesToReactFlow([]);

    expect(result).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// hasActiveNodes — polling activation detection
// ---------------------------------------------------------------------------
describe("hasActiveNodes", () => {
  it("returns true when any node has status running", () => {
    const nodes: WorkflowNode[] = [
      { id: "a", name: "A", action: "run", status: "success" },
      { id: "b", name: "B", action: "run", status: "running" }
    ];
    expect(hasActiveNodes(nodes)).toBe(true);
  });

  it("returns true when any node has status pending", () => {
    const nodes: WorkflowNode[] = [
      { id: "a", name: "A", action: "run", status: "success" },
      { id: "b", name: "B", action: "run", status: "pending" }
    ];
    expect(hasActiveNodes(nodes)).toBe(true);
  });

  it("returns false when all nodes are terminal (success/failed)", () => {
    const nodes: WorkflowNode[] = [
      { id: "a", name: "A", action: "run", status: "success" },
      { id: "b", name: "B", action: "run", status: "failed" }
    ];
    expect(hasActiveNodes(nodes)).toBe(false);
  });

  it("returns false when nodes have no status", () => {
    const nodes: WorkflowNode[] = [{ id: "a", name: "A", action: "run" }];
    expect(hasActiveNodes(nodes)).toBe(false);
  });

  it("returns false for empty node list", () => {
    expect(hasActiveNodes([])).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// getRunningNodeIds — helper for edge animation
// ---------------------------------------------------------------------------
describe("getRunningNodeIds", () => {
  it("collects only running node IDs", () => {
    const nodes: WorkflowNode[] = [
      { id: "a", name: "A", action: "run", status: "running" },
      { id: "b", name: "B", action: "run", status: "success" },
      { id: "c", name: "C", action: "run", status: "running" }
    ];

    const ids = getRunningNodeIds(nodes);

    expect(ids.size).toBe(2);
    expect(ids.has("a")).toBe(true);
    expect(ids.has("c")).toBe(true);
    expect(ids.has("b")).toBe(false);
  });

  it("returns empty set when no nodes are running", () => {
    const nodes: WorkflowNode[] = [
      { id: "a", name: "A", action: "run", status: "success" },
      { id: "b", name: "B", action: "run", status: "pending" }
    ];

    const ids = getRunningNodeIds(nodes);

    expect(ids.size).toBe(0);
  });
});
