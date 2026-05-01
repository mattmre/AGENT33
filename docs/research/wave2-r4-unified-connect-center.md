# Wave 2 Round 4 - Unified Connect Center

## Objective

Give new users one readable place to understand what must be connected before AGENT33 can run real work.

## Panel critique summary

### Pass A - Layperson comprehension

The existing setup surfaces are split across Models, Integrations, MCP Health, Tool Catalog, Safety, and Advanced controls. A beginner does not know which page matters first. Connect Center reframes setup as six plain-language questions: can the browser talk to the engine, can AGENT33 call a model, can it keep state, can it use tools, can users inspect tools, and will risky work ask first?

### Pass B - Functional workflow depth

The center does not replace the deeper setup pages. It acts as a hub that routes to them with context and shows why each connection matters for workflows, demos, research loops, and safe automation.

### Pass C - Feasibility and safety

This round reuses the existing onboarding readiness endpoint and existing navigation targets. It adds no new backend contract, stores no secrets, and does not auto-fix credentials or tool configuration.

## MVP scope

- Add a Connect Center tab under Start.
- Show six connection cards: engine access, model provider, runtime memory, MCP/tools, tool catalog, and safety approvals.
- Use existing onboarding status when credentials are present.
- Route actions to existing Models, Integrations, MCP Health, Tools, Safety, and Advanced pages.
- Add Help Assistant guidance for the new setup path.

## Acceptance criteria

- A beginner can see the setup checklist without credentials.
- Live readiness refresh runs only when an operator token or API key exists.
- Cards explain impact and next action in plain language.
- Actions navigate to existing setup surfaces.
- Focused tests cover card derivation and panel routing.
