# Wave 2 Round 3 - Role-Based Start Paths and Guided Idea Intake

## Objective

Make the first Start experience ask who the user is and what outcome they want before showing tool-heavy surfaces.

## Panel critique summary

### Pass A - Layperson comprehension

New users should not need to understand models, MCP, agents, workflow YAML, or advanced settings before they see a path. Five role cards provide a plain-language first decision: founder, developer, agency, enterprise, or operator.

### Pass B - Functional workflow depth

Each role maps to recommended workflows and demo scenarios instead of merely changing copy. The guided brief captures the minimum information needed to route into Workflow Starter with a review-gated plan.

### Pass C - Feasibility and safety

This round remains frontend-only. The guided brief creates a `WorkflowStarterDraft` and does not call a model, store secrets, create files, or run automation. Role filtering is advisory: users can still open the full catalog.

## Competitor pattern takeaways

Dify, Flowise, Langflow, Open WebUI, AnythingLLM, OpenHands, LangGraph/LangSmith, CrewAI, AutoGen Studio, n8n, and Activepieces all reinforce the same pattern: templates, roles, examples, and guided task intake reduce blank-canvas anxiety. AGENT33's angle is role-to-demo-to-safe-workflow continuity rather than a standalone canvas or raw settings panel.

## MVP scope

- Add a `Guide Me` first tab under Start.
- Add five role profiles with recommended workflows, demo scenarios, and setup focus.
- Add a guided brief form that outputs a `WorkflowStarterDraft`.
- Pass the chosen role into Outcome Home and Demo Mode for role-aware recommendations.
- Keep all behavior local and review-gated.

## Acceptance criteria

- A beginner can choose a role before seeing advanced tool surfaces.
- The selected role changes recommended workflows and demo scenarios.
- Guided brief submission opens Workflow Starter with a prefilled draft.
- Empty required fields are surfaced as an inline alert.
- Focused tests cover role rendering, role selection, brief-to-draft conversion, and draft handoff.
