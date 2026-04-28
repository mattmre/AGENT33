import type { ToolApprovalRequest } from "./types";

export type AttentionPriority = "high" | "medium" | "low";

export interface AttentionQueueItem {
  id: string;
  title: string;
  priority: AttentionPriority;
  reason: string;
  policyPreset: string;
  timeGuidance: string;
  recommendedAction: string;
}

function getTitle(approval: ToolApprovalRequest): string {
  return approval.operation ? `${approval.tool_name}: ${approval.operation}` : approval.tool_name;
}

function getPriority(approval: ToolApprovalRequest): AttentionPriority {
  if (approval.reason === "supervised_destructive") {
    return "high";
  }
  if (approval.command || approval.operation) {
    return "medium";
  }
  return "low";
}

export function getPolicyPreset(approval: ToolApprovalRequest): string {
  if (approval.reason === "supervised_destructive") {
    return "Deny by default unless the command, target path, and requester are expected.";
  }
  if (approval.command) {
    return "Approve once only after reading the exact command.";
  }
  return "Approve routine requests when requester and tool scope match the workflow.";
}

export function getTimeGuidance(approval: ToolApprovalRequest, now = Date.now()): string {
  if (!approval.expires_at) {
    return "No expiry. Review when convenient.";
  }
  const expiresAt = Date.parse(approval.expires_at);
  if (!Number.isFinite(expiresAt)) {
    return "Expiry unknown. Review manually.";
  }
  const minutes = Math.round((expiresAt - now) / 60_000);
  if (minutes <= 0) {
    return "Expired or expiring now. Reject unless you can re-run safely.";
  }
  if (minutes <= 30) {
    return `Expires in ${minutes} min. Decide soon or reject.`;
  }
  return `Expires in ${minutes} min. Safe to review in order.`;
}

export function buildAttentionQueue(
  approvals: ToolApprovalRequest[],
  now = Date.now()
): AttentionQueueItem[] {
  return approvals
    .filter((approval) => approval.status === "pending")
    .map((approval) => {
      const priority = getPriority(approval);
      return {
        id: approval.approval_id,
        title: getTitle(approval),
        priority,
        reason:
          priority === "high"
            ? "Destructive or high-impact tool call"
            : priority === "medium"
              ? "Tool call needs operator review"
              : "Routine approval",
        policyPreset: getPolicyPreset(approval),
        timeGuidance: getTimeGuidance(approval, now),
        recommendedAction:
          priority === "high" ? "Reject unless verified" : "Approve with a review note if expected"
      };
    })
    .sort((a, b) => {
      const priorityOrder: Record<AttentionPriority, number> = { high: 0, medium: 1, low: 2 };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    });
}

export function buildBulkDecisionGuidance(items: AttentionQueueItem[]): string {
  if (items.length === 0) {
    return "No pending attention items.";
  }
  const highPriority = items.filter((item) => item.priority === "high").length;
  if (highPriority > 0) {
    return `${highPriority} high-priority item${highPriority === 1 ? "" : "s"} should be reviewed one by one.`;
  }
  return "Low and medium items may be reviewed together if requester, tool, and workflow match.";
}
