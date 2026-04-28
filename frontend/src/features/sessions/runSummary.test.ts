import { describe, expect, it } from "vitest";

import {
  buildRunDashboardCards,
  buildRunNextActions,
  normalizeRunStatus
} from "./runSummary";

describe("run summary helpers", () => {
  it("normalizes common run statuses", () => {
    expect(normalizeRunStatus("completed")).toBe("succeeded");
    expect(normalizeRunStatus("in_progress")).toBe("running");
    expect(normalizeRunStatus("error")).toBe("failed");
    expect(normalizeRunStatus("pending")).toBe("queued");
    expect(normalizeRunStatus("mystery")).toBe("unknown");
  });

  it("builds user-readable run cards from flexible session records", () => {
    const [card] = buildRunDashboardCards([
      {
        session_id: "ses-1",
        agent_name: "safe-implementer",
        status: "completed",
        goal: "Build landing page",
        summary: "Created plan and artifacts.",
        artifacts: [{ name: "plan.md" }, { path: "diff.patch" }],
        updated_at: "now"
      }
    ]);

    expect(card.id).toBe("ses-1");
    expect(card.agent).toBe("safe-implementer");
    expect(card.status).toBe("succeeded");
    expect(card.artifacts).toEqual(["plan.md", "diff.patch"]);
    expect(card.nextActions).toContain("Review artifacts");
  });

  it("recommends safer actions for failed runs", () => {
    expect(buildRunNextActions("failed")).toEqual([
      "Review failure",
      "Replay with safer settings",
      "Open logs"
    ]);
  });
});
