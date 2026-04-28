import { describe, expect, it } from "vitest";

import {
  buildAttentionQueue,
  buildBulkDecisionGuidance,
  getPolicyPreset,
  getTimeGuidance
} from "./attentionQueue";
import type { ToolApprovalRequest } from "./types";

const approval: ToolApprovalRequest = {
  approval_id: "APR-1",
  status: "pending",
  reason: "supervised_destructive",
  tool_name: "filesystem",
  operation: "delete",
  command: "rm -rf temp",
  requested_by: "agent",
  tenant_id: "tenant",
  details: "cleanup",
  created_at: "2026-01-01T12:00:00Z",
  expires_at: "2026-01-01T12:10:00Z",
  reviewed_by: "",
  reviewed_at: null,
  review_note: ""
};

describe("attention queue helpers", () => {
  it("prioritizes destructive pending approvals", () => {
    const [item] = buildAttentionQueue([approval], Date.parse("2026-01-01T12:00:00Z"));

    expect(item.priority).toBe("high");
    expect(item.policyPreset).toContain("Deny by default");
    expect(item.recommendedAction).toBe("Reject unless verified");
  });

  it("builds time-bound decision guidance", () => {
    expect(getTimeGuidance(approval, Date.parse("2026-01-01T12:00:00Z"))).toContain("Expires in 10 min");
    expect(getTimeGuidance({ ...approval, expires_at: "" })).toBe("No expiry. Review when convenient.");
  });

  it("summarizes bulk decision safety", () => {
    const queue = buildAttentionQueue([approval], Date.parse("2026-01-01T12:00:00Z"));
    expect(buildBulkDecisionGuidance(queue)).toBe("1 high-priority item should be reviewed one by one.");
    expect(buildBulkDecisionGuidance([])).toBe("No pending attention items.");
  });

  it("uses command-specific policy presets for non-destructive commands", () => {
    expect(getPolicyPreset({ ...approval, reason: "tool_policy_ask" })).toContain("exact command");
  });
});
