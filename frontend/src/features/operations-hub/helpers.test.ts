import { describe, expect, it } from "vitest";

import {
  canCancel,
  canPause,
  canResume,
  filterAndSortProcesses,
  getStatusClass,
  getStatusLabel
} from "./helpers";
import type { OperationsHubProcessDetail, OperationsHubProcessSummary } from "./types";

describe("operations hub helpers", () => {
  it("maps status to css classes", () => {
    expect(getStatusClass("running")).toBe("status-running");
    expect(getStatusClass("suspended")).toBe("status-paused");
    expect(getStatusClass("expired")).toBe("status-cancelled");
    expect(getStatusClass("success")).toBe("status-ok");
    expect(getStatusClass("failed")).toBe("status-error");
  });

  it("formats status labels", () => {
    expect(getStatusLabel("in_progress")).toBe("In Progress");
    expect(getStatusLabel("test-status")).toBe("Test Status");
    expect(getStatusLabel("")).toBe("Unknown");
  });

  it("filters and sorts process summaries", () => {
    const input: OperationsHubProcessSummary[] = [
      {
        id: "a",
        type: "trace",
        status: "running",
        started_at: "2026-02-18T10:00:00Z",
        name: "Trace A"
      },
      {
        id: "b",
        type: "autonomy_budget",
        status: "active",
        started_at: "2026-02-18T12:00:00Z",
        name: "Budget B"
      }
    ];

    const filtered = filterAndSortProcesses(input, "active", "");
    expect(filtered).toHaveLength(1);
    expect(filtered[0].id).toBe("b");

    const searched = filterAndSortProcesses(input, "all", "trace");
    expect(searched).toHaveLength(1);
    expect(searched[0].id).toBe("a");
  });

  it("enforces control availability by process type/status", () => {
    const activeBudget: OperationsHubProcessDetail = {
      id: "budget-1",
      type: "autonomy_budget",
      status: "active",
      started_at: "2026-02-18T11:00:00Z",
      name: "budget"
    };
    const suspendedBudget: OperationsHubProcessDetail = {
      ...activeBudget,
      status: "suspended"
    };
    const runningTrace: OperationsHubProcessDetail = {
      id: "trace-1",
      type: "trace",
      status: "running",
      started_at: "2026-02-18T12:00:00Z",
      name: "trace"
    };

    expect(canPause(activeBudget)).toBe(true);
    expect(canPause(suspendedBudget)).toBe(false);
    expect(canResume(suspendedBudget)).toBe(true);
    expect(canResume(activeBudget)).toBe(false);
    expect(canCancel(runningTrace)).toBe(true);
    expect(canCancel({ ...runningTrace, status: "completed" })).toBe(false);
  });
});
