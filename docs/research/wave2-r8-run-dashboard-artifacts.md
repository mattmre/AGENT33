# Wave 2 Round 8 - Agent/Run Dashboard and artifacts

## Goal

Round 8 makes run history readable for non-expert users. Instead of listing raw session IDs, the sessions dashboard now explains each run as an agent card with status, outcome, artifacts, replay hints, and next actions.

## Panel critique synthesis

- Beginners need to know "what happened" and "what should I do next", not just see a session identifier.
- Artifacts should be presented as first-class outputs: plans, diffs, logs, screenshots, files, and summaries.
- Failed runs need recovery language. "Replay with safer settings" is more useful than a raw error.
- This slice should reuse `/v1/sessions` and tolerate flexible backend shapes rather than requiring a new run API.

## Competitive patterns reviewed

- OpenHands and workbench-style agents emphasize run timelines, file diffs, and replay/retry entry points.
- LangSmith-style tracing makes outcomes and logs visible but is often too technical for beginners.
- n8n and Activepieces show run status plus next action, which is a useful pattern for AGENT-33 workflows.

## Implementation decision

Add a pure `runSummary.ts` adapter that converts flexible session records into stable UI cards:

1. Normalize statuses into queued/running/succeeded/failed/unknown.
2. Extract agent, title, outcome, updated time, and artifacts from multiple possible field names.
3. Generate next actions and replay hints by status.
4. Render the existing `SessionsDashboard` as cards without changing the sessions API.

## Deferred follow-up

- Live run timeline endpoint.
- Artifact download/view routes.
- One-click replay/retry once backend support is confirmed.
