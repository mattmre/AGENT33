# Wave 2 Round 7 - Guided Agent Builder v2

## Goal

Round 7 reduces the blank-canvas problem in Agent Builder. Instead of asking beginners to understand roles, capabilities, provider fit, and autonomy from scratch, the builder now starts with guided templates and a review-before-save summary.

## Panel critique synthesis

- Beginners do not know what an "implementer" or "researcher" should be allowed to do. The UI needs opinionated templates with safe defaults.
- Capability toggles are dangerous without plain-language consequences. Write, code, and API access should create visible review gates.
- Provider binding should be explained before save, even when the builder does not directly connect a model.
- The save moment needs a final review card: template, autonomy level, network scope, enabled capabilities, and required approvals.

## Competitive patterns reviewed

- AutoGen Studio and CrewAI examples lean on agent role templates, but often expose too many raw controls too early.
- Dify and Open WebUI make provider choice more approachable with presets; Agent Builder should echo that by recommending provider fit for each agent type.
- OpenHands-style workbench flows emphasize review gates before file writes. AGENT-33 should keep that safety posture central.

## Implementation decision

This PR-sized slice keeps the existing Agent Builder API behavior and adds:

1. Three guided templates: Research analyst, Safe implementer, and QA reviewer.
2. Template application that fills name, role, description, and capability toggles.
3. Recommended setup guidance for provider binding, skills, and tools.
4. Review-before-save summary showing autonomy, network, enabled capabilities, and approval gates.
5. Safer governance payloads that mark file-write, code-execution, and API calls as review-required.

## Deferred follow-up

- Persisting templates server-side.
- Direct provider selection inside Agent Builder.
- Live skill/tool discovery from the MCP service.
- A multi-step wizard that prevents saving until every required design decision is reviewed.
