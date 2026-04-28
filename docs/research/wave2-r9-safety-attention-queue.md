# Wave 2 Round 9 - Safety/attention queue v2

## Goal

Round 9 makes safety approvals easier for layperson operators. Instead of only listing governed tool calls, Safety Center now highlights the riskiest pending decisions, explains the policy preset, gives time-bound guidance, and recommends whether to review one-by-one or in a batch.

## Panel critique synthesis

- Users do not know which pending approval matters most. Destructive and command-bearing approvals should rise to the top.
- Approval screens need policy language, not just tool names and raw commands.
- Expiry should be translated into action: decide soon, reject, or review in order.
- Bulk approval should be guided conservatively; high-risk items should not be batch-approved.

## Competitive patterns reviewed

- Agent workbenches increasingly use human-in-the-loop queues for risky tool calls.
- n8n and Activepieces show failed/blocked actions in plain language, which maps well to AGENT-33 approvals.
- Security dashboards prioritize risk first; Safety Center should do the same for destructive tools.

## Implementation decision

Add a pure attention queue adapter over existing tool approval records:

1. `attentionQueue.ts` normalizes pending approvals into priority queue items.
2. Safety Center renders the top pending decisions before the detailed approval list.
3. Policy presets and bulk guidance are deterministic and frontend-only.
4. Existing approval/rejection API calls remain unchanged.

## Deferred follow-up

- Actual bulk approval/rejection API support.
- Time-bound approvals.
- Cross-surface queue items from failed runs and ingestion review decisions.
