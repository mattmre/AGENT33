# Wave 2 Round 2 - Demo Mode and First-Success Path

## Objective

Let a new user experience AGENT33's intended value before they connect a model, configure secrets, or understand agent terminology.

## Panel critique summary

### Pass A - Layperson comprehension

The current first-run path still asks users to configure the platform before they can see why it matters. Demo Mode should answer: "What will this actually do for me?" with sample outcomes, visible progress, and artifacts.

### Pass B - Functional workflow depth

The demo must not be a screenshot or marketing card. It should model the actual product loop: intake -> plan -> run timeline -> artifacts -> next action. Users should be able to send the sample into Workflow Starter once they connect credentials.

### Pass C - Feasibility and safety

This round is intentionally frontend-only and static. It avoids fake backend success states while clearly marking that the timeline is simulated and no model calls are made.

## MVP scope

- A Demo Mode page under the Start navigation group.
- Six sample outcomes: customer support dashboard, landing page launch kit, repo triage report, first product idea, customer export report, and team meeting bot.
- Simulated run timeline and reviewable artifacts.
- No credentials, model calls, or backend dependency.
- Routes to Models, Workflow Catalog, and Workflow Starter.

## Acceptance criteria

- The demo page states that zero credentials are needed.
- Users can switch six sample outcomes spanning founder, operator, developer, agency, and team-lead needs.
- Each sample includes inputs, timeline steps, and artifacts.
- "Customize this demo" passes a prefilled `WorkflowStarterDraft` into Workflow Starter.
- Tests cover demo data and UI interactions.
