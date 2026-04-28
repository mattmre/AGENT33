# Wave 2 Round 6 - Workflow productization

## Goal

Round 6 turns workflow catalog entries from simple descriptions into beginner-readable product cards. A user should understand what they need to provide, what AGENT-33 will return, how long it may take, what it may cost, what risk gate applies, and what starter pack supports the workflow before opening Workflow Starter.

## Panel critique synthesis

- Layperson users do not trust a workflow if the card only says "analyze repo" or "build app". They need concrete input requirements and example outputs.
- The catalog should not be a blank prompt launcher. Each workflow should feel like a packaged product with scope, deliverables, dry-run preview, and safety expectations.
- Cost and risk estimates can be deterministic and approximate at this stage. Showing the estimate is more useful than hiding it until runtime.
- Dry-run preview should be simulated and local for now. It should explain what will happen without calling execution APIs.
- Starter packs can begin as curated hints from workflow metadata; live skill/template discovery can be layered later.

## Competitive patterns reviewed

- Dify and Flowise make workflows approachable with template cards, expected inputs, and output previews.
- n8n and Activepieces win with "recipes" that show trigger, inputs, and steps before activation.
- Langflow and CrewAI examples remain more builder-centric; AGENT-33 can differentiate by making the outcome pack the primary unit.
- Agent workbench tools increasingly expose run previews and approval gates, which supports the AGENT-33 safety-first positioning.

## Implementation decision

This slice adds a pure productization layer over the existing `OUTCOME_WORKFLOWS` catalog:

1. `productization.ts` derives input requirements, example outputs, estimates, dry-run steps, and starter pack hints.
2. `ProductWorkflowDetail` replaces the Workflow Catalog detail sidebar with a fuller product view.
3. The existing Workflow Starter handoff remains unchanged and still uses `buildWorkflowDraft`.

## Deferred follow-up

- Live starter pack discovery via workflow and skill APIs.
- User-editable input values directly inside the catalog card.
- Cost estimates based on actual selected provider/model pricing.
