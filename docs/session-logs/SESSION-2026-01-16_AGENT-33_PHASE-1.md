# Session Log: Phase 1 Inventory + Triage

## Date
2026-01-16

## Objectives
- Review `manifest.md` and summarize sources by repo.
- Create `core/` folder layout draft.
- Build collision list of suffixed files and propose canonical picks.
- Draft `core/CHANGELOG.md` template.

## Inventory Summary (by repo)
- RSMFConverter: docs, .claude, .github, venv agents; plus agentic review framework/prompts, CLAUDE, AEP docs, agent tasks.
- EDCTool: docs, .claude, .github; AGENTS/CLAUDE; agentic review framework/prompts; AEP docs.
- EDCwayback: docs, .claude, .github; AGENTS/CLAUDE; AEP docs.
- myainewsbot.com: docs, .github; CLAUDE; AEP docs.
- CHELATEDAI: docs; CLAUDE; AEP docs.
- Cladius Maximus: docs, .claude, multiple .github variants; local-agent-orchestrator assets; multiple CLAUDE files; PROMPT_PACK.

## Proposed core/ Layout (Draft)
- `core/agents/`: consolidated AGENTS + CLAUDE guidance + sources index.
- `core/orchestrator/`: orchestrator rules, operator manual, handoff templates, routing map.
- `core/arch/`: ARCH-AEP workflow, templates, trackers, phase summaries.
- `core/workflows/`: CI/CD workflows, instructions, promotion criteria, sources index.
- `core/prompts/`: canonical review frameworks/prompts.
- `core/logs/`: archived logs from source repos (immutable copies).
- `core/research/`: specifications and research notes.
- `core/phases/`, `core/roadmap/`, `core/templates/`, `core/user-guide/`, `core/api/`: supporting canonical assets.

## Collision List (Suffixed Files) + Canonical Picks
Criteria: dedup-policy priority order (recency, completeness, reuse).

| Base File | Variants (suffix) | Proposed Canonical | Rationale |
| --- | --- | --- | --- |
| `docs/CLAUDE.md` | `__RSMFConverter`, `__EDCTool`, `__EDCwayback`, `__myainewsbot.com`, `__CHELATEDAI`, `__Cladius_Maximus` | `core/agents/CLAUDE.md` (baseline: RSMFConverter docs) | Most complete; already consolidated in core. |
| `docs/agentic-review-framework.md` | `__RSMFConverter`, `__EDCTool`, `__Cladius_Maximus` | `core/prompts/agentic-review-framework.md` | Identical copies; choose RSMFConverter baseline. |
| `docs/agentic-review-prompts.md` | `__RSMFConverter`, `__EDCTool`, `__Cladius_Maximus` | `core/prompts/agentic-review-prompts.md` | Identical copies; choose RSMFConverter baseline. |
| `docs/ARCH.../orchestrator-briefing.md` | `__RSMFConverter`, `__EDCTool`, `__EDCwayback`, `__CHELATEDAI`, `__myainewsbot.com`, `__Cladius_Maximus` | `core/arch/orchestrator-briefing.md` | Identical copies; choose RSMFConverter baseline. |
| `docs/ARCH.../agent-learning.md` | `__RSMFConverter`, `__EDCTool`, `__EDCwayback`, `__CHELATEDAI`, `__myainewsbot.com`, `__Cladius_Maximus` | `core/arch/agent-learning.md` | Identical copies; choose RSMFConverter baseline. |
| `docs/agent-tasks/AGENT-IMPLEMENTATION-GUIDE.md` | `__RSMFConverter` | `core/agents/AGENT-IMPLEMENTATION-GUIDE.md` (or archive) | Single source; promote if needed. |
| `local-agent-orchestrator/orchestrator/PROMPT_PACK.md` | `__Cladius_Maximus` | `core/orchestrator/PROMPT_PACK.md` | Only source for orchestrator prompt pack. |

## Acceptance Criteria (Phase 1 Tasks)
- Manifest summary recorded with repo coverage and notable assets.
- Draft core/ layout recorded for Phase 2 canonicalization.
- All suffixed file collisions identified with proposed canonical target + rationale.
- `core/CHANGELOG.md` contains a reusable template section.

## Work Completed
- Reviewed `manifest.md` and summarized source repos.
- Drafted a core layout consistent with existing canonical folders.
- Enumerated suffixed collisions and proposed canonical picks.
- Added a template section to `core/CHANGELOG.md`.
- Referenced evidence capture template in handoff docs: `core/orchestrator/handoff/EVIDENCE_CAPTURE.md`.

## Files Touched
- `core/CHANGELOG.md`
- `docs/session-logs/SESSION-2026-01-16_AGENT-33_PHASE-1.md`

## Notes
- Collision picks align with existing canonical selections in `core/CHANGELOG.md`.
- Evidence capture format lives in `core/orchestrator/handoff/EVIDENCE_CAPTURE.md` and should be used for future phase logs.
