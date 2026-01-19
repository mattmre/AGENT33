## Template (for new entries)
### Canonicalization Decisions
| Date | Canonical File | Sources Considered | Rationale (Recency/Completeness/Reuse) | Notes |
| --- | --- | --- | --- | --- |
| YYYY-MM-DD | core/<path> | collected/<repo>/<path>, ... |  |  |

## [Unreleased]
### Canonicalization Decisions
| Date | Canonical File | Sources Considered | Rationale (Recency/Completeness/Reuse) | Notes |
| --- | --- | --- | --- | --- |
| 2026-01-16 | core/arch/* (AEP templates & guides) | collected/*/docs/ARCH AGENTIC ENGINEERING AND PLANNING/* | Identical copies across repos; selected RSMFConverter as canonical baseline. | Removed suffixed variants in core/arch. |
| 2026-01-16 | core/prompts/agentic-review-framework.md | collected/*/docs/agentic-review-framework.md | Identical copies; selected RSMFConverter baseline. |  |
| 2026-01-16 | core/prompts/agentic-review-prompts.md | collected/*/docs/agentic-review-prompts.md | Identical copies; selected RSMFConverter baseline. |  |
| 2026-01-16 | core/agents/CLAUDE.md | collected/*/CLAUDE.md and collected/*/docs/CLAUDE.md | Selected most complete (RSMFConverter docs version, 25,208 bytes). |  |
| 2026-01-16 | core/agents/CLAUDE_SESSION_WRAP_CONTEXT_AGENT.md | collected/*/docs/CLAUDE_SESSION_WRAP_CONTEXT_AGENT.md | Identical copies; selected RSMFConverter baseline. |  |
| 2026-01-16 | core/agents/AGENTS.md | collected/EDCwayback/AGENTS.md, collected/example-project/AGENTS.md | Selected most complete (EDCwayback is longer). |  |
| 2026-01-16 | core/orchestrator/* | collected/Cladius Maximus/local-agent-orchestrator/* | Only repo containing orchestrator assets. |  |
| 2026-01-16 | core/workflows/* | collected/RSMFConverter/.github/* | Baseline workflow set; other repos pending merge review. |  |
| 2026-01-16 | core/workflows/instructions/csharp.instructions.md | collected/example-project/.github/instructions/csharp.instructions.md | Only repo providing C# instruction file. | Promoted to canonical instructions. |
| 2026-01-16 | core/workflows/instructions/python.instructions.md | collected/EDCwayback/.github/instructions/python.instructions.md | Only repo providing Python instruction file. | Promoted to canonical instructions. |
| 2026-01-16 | core/agents/sources/* | collected/*/CLAUDE.md, collected/*/AGENTS.md, collected/*/docs/agentic-review-*.md | Archived for reference; non-canonical. | Flattened filenames. |
| 2026-01-16 | core/workflows/sources/* | collected/*/.github/* | Archived for later workflow merge. |  |
| 2026-01-16 | core/agents/AGENTS.md | collected/EDCwayback/AGENTS.md, collected/example-project/AGENTS.md | Consolidated project-specific constraints into a single core file. |  |
| 2026-01-16 | core/agents/CLAUDE_SOURCES.md | core/agents/sources/* | Added index for archived CLAUDE variants. |  |
| 2026-01-16 | core/workflows/workflows/dotnet-build.yml | collected/example-project/.github/workflows/dotnet-build.yml | Selected as reusable .NET CI template. |  |
| 2026-01-16 | core/workflows/dependabot.yml | collected/myainewsbot.com/.github/dependabot.yml | Simple baseline dependabot config. |  |
| 2026-01-16 | core/agents/CLAUDE.md | core/agents/sources/* CLAUDE variants | Added condensed sections for EDCToolkit, EDCwayback, Claudius Maximus. |  |
| 2026-01-16 | core/orchestrator/README.md | (new) | Added model-agnostic orchestrator entrypoint. |  |
| 2026-01-16 | core/orchestrator/handoff/DEFINITION_OF_DONE.md | (new) | Added definition of done checklist. |  |
| 2026-01-16 | core/orchestrator/handoff/TASKS.md | core/orchestrator/handoff/TASKS.md | Added review capture + DoD step. |  |
| 2026-01-16 | core/orchestrator/prompts/SYSTEM.md | core/orchestrator/prompts/SYSTEM.md | Added risk triggers and model-agnostic wording. |  |
| 2026-01-16 | core/orchestrator/prompts/WORKER_RULES.md | core/orchestrator/prompts/WORKER_RULES.md | Model-agnostic worker guidance. |  |
| 2026-01-16 | core/orchestrator/agents/CLAUDE_ORCHESTRATOR_RULES.md | core/orchestrator/agents/CLAUDE_ORCHESTRATOR_RULES.md | Model-agnostic orchestrator rules. |  |
| 2026-01-16 | core/orchestrator/agents/QWEN_WORKER_RULES.md | core/orchestrator/agents/QWEN_WORKER_RULES.md | Model-agnostic worker rules. |  |
| 2026-01-16 | core/orchestrator/agents/GEMINI_REVIEW_RULES.md | core/orchestrator/agents/GEMINI_REVIEW_RULES.md | Model-agnostic reviewer rules. |  |
| 2026-01-16 | core/orchestrator/PROMPT_PACK.md | core/orchestrator/PROMPT_PACK.md | Model-agnostic prompt pack. |  |
| 2026-01-16 | core/orchestrator/handoff/PLAN.md | core/orchestrator/handoff/PLAN.md | Removed model-specific references. |  |
| 2026-01-16 | core/orchestrator/handoff/STATUS.md | core/orchestrator/handoff/STATUS.md | Made status model-agnostic with local runtime example. |  |
| 2026-01-16 | core/workflows/PROMOTION_CRITERIA.md | (new) | Added workflow promotion criteria. |  |
| 2026-01-16 | core/workflows/SOURCES_INDEX.md | (new) | Added workflow sources index. |  |
| 2026-01-16 | core/orchestrator/analysis/README.md | (new) | Added orchestration analysis index. |  |
| 2026-01-16 | core/arch/workflow.md | core/arch/workflow.md | Updated quick links to canonical core paths. |  |
| 2026-01-16 | core/orchestrator/agents/DIRECTOR_RULES.md | (new) | Added model-agnostic Director role. |  |
| 2026-01-16 | core/orchestrator/OPERATOR_MANUAL.md | (new) | Added operator manual tying handoff to AEP workflow. |  |
| 2026-01-16 | core/orchestrator/PROMPT_PACK.md | core/orchestrator/PROMPT_PACK.md | Added Director prompt. |  |
| 2026-01-16 | core/orchestrator/README.md | core/orchestrator/README.md | Linked operator manual and director role. |  |
| 2026-01-16 | core/agents/CLAUDE.md | core/agents/CLAUDE.md | Added context selector table. |  |
| 2026-01-16 | core/orchestrator/handoff/PRIORITIES.md | (new) | Added rolling priorities view. |  |
| 2026-01-16 | core/orchestrator/handoff/REVIEW_CAPTURE.md | (new) | Added review capture template. |  |
| 2026-01-16 | core/orchestrator/handoff/TASKS.md | core/orchestrator/handoff/TASKS.md | Linked review capture template. |  |
| 2026-01-16 | core/orchestrator/AGENT_ROUTING_MAP.md | (new) | Added agent routing map by task type. |  |
| 2026-01-16 | core/orchestrator/README.md | core/orchestrator/README.md | Linked priorities and routing map. |  |
| 2026-01-16 | core/orchestrator/handoff/REVIEW_CHECKLIST.md | (new) | Added model-agnostic review checklist. |  |
| 2026-01-16 | core/ORCHESTRATION_INDEX.md | (new) | Added orchestration index linking core systems. |  |
| 2026-01-16 | core/agents/CLAUDE.md | core/agents/CLAUDE.md | Added quick links to sources and diff report. |  |
| 2026-01-16 | core/README.md | core/README.md | Added orchestration overview links. |  |
| 2026-01-16 | core/orchestrator/GLOSSARY.md | (new) | Added orchestration glossary. |  |
| 2026-01-16 | core/agents/CLAUDE_ADDENDUM.md | (new) | Moved non-RSMF contexts into addendum. |  |
| 2026-01-16 | core/agents/CLAUDE.md | core/agents/CLAUDE.md | Linked addendum and removed non-RSMF contexts. |  |
| 2026-01-16 | core/orchestrator/README.md | core/orchestrator/README.md | Added orchestration quickstart. |  |
| 2026-01-16 | core/orchestrator/AGENT_ROUTING_MAP.md | core/orchestrator/AGENT_ROUTING_MAP.md | Added role selection checklist. |  |
| 2026-01-16 | core/orchestrator/handoff/ESCALATION_PATHS.md | (new) | Added escalation paths guidance. |  |
| 2026-01-16 | core/orchestrator/handoff/EVIDENCE_CAPTURE.md | (new) | Added evidence capture template. |  |
| 2026-01-16 | core/orchestrator/handoff/SESSION_WRAP.md | (new) | Added session wrap template. |  |
| 2026-01-16 | core/orchestrator/CHEAT_SHEET.md | (new) | Added orchestration cheat sheet. |  |
| 2026-01-16 | core/orchestrator/README.md | core/orchestrator/README.md | Linked cheat sheet and evidence capture in quickstart. |  |
| 2026-01-16 | core/orchestrator/handoff/PLAN.md | core/orchestrator/handoff/PLAN.md | Added minimum required artifacts section. |  |
| 2026-01-16 | core/orchestrator/handoff/STATUS.md | core/orchestrator/handoff/STATUS.md | Added task status glossary. |  |
| 2026-01-16 | core/orchestrator/prompts/SYSTEM.md | core/orchestrator/prompts/SYSTEM.md | Added risk trigger matrix. |  |
| 2026-01-16 | core/orchestrator/handoff/EVIDENCE_CAPTURE.md | core/orchestrator/handoff/EVIDENCE_CAPTURE.md | Added review outcomes section. |  |
| 2026-01-16 | core/orchestrator/CHEAT_SHEET.md | core/orchestrator/CHEAT_SHEET.md | Added task lifecycle diagram. |  |
| 2026-01-16 | core/orchestrator/handoff/REVIEW_CHECKLIST.md | core/orchestrator/handoff/REVIEW_CHECKLIST.md | Added risk trigger checklist. |  |
| 2026-01-16 | core/orchestrator/README.md | core/orchestrator/README.md | Clarified review vs evidence capture. |  |
| 2026-01-16 | core/ORCHESTRATION_INDEX.md | core/ORCHESTRATION_INDEX.md | Added model-agnostic principle note. |  |
| 2026-01-16 | core/orchestrator/handoff/EVIDENCE_CAPTURE.md | core/orchestrator/handoff/EVIDENCE_CAPTURE.md | Added evidence checklist. |  |
| 2026-01-16 | core/workflows/PROMOTION_CRITERIA.md | core/workflows/PROMOTION_CRITERIA.md | Added promotion decision log template. |  |
| 2026-01-16 | core/agents/README.md | core/agents/README.md | Linked CLAUDE addendum usage. |  |
| 2026-01-16 | core/orchestrator/handoff/STATUS.md | core/orchestrator/handoff/STATUS.md | Added handoff file map. |  |
| 2026-01-16 | core/orchestrator/handoff/TASKS.md | core/orchestrator/handoff/TASKS.md | Added minimum task payload. |  |
| 2026-01-16 | core/orchestrator/handoff/ESCALATION_PATHS.md | core/orchestrator/handoff/ESCALATION_PATHS.md | Added review escalation criteria. |  |
| 2026-01-16 | core/orchestrator/handoff/TASKS.md | core/orchestrator/handoff/TASKS.md | Added acceptance criteria examples. |  |
| 2026-01-16 | core/orchestrator/handoff/SESSION_WRAP.md | core/orchestrator/handoff/SESSION_WRAP.md | Added handoff checklist. |  |
| 2026-01-16 | core/arch/verification-log.md | core/arch/verification-log.md | Added usage note for verification log. |  |
| 2026-01-16 | core/research/agentic-orchestration-trends-2025H2.md | docs/research/agentic-orchestration-trends-2025H2.md | Promoted research doc to core for canonical reference. |  |
| 2026-01-16 | core/orchestrator/handoff/EVIDENCE_CAPTURE.md | core/orchestrator/handoff/EVIDENCE_CAPTURE.md | Added evidence example. |  |
| 2026-01-16 | core/orchestrator/handoff/REVIEW_CAPTURE.md | core/orchestrator/handoff/REVIEW_CAPTURE.md | Added risk trigger references. |  |
| 2026-01-16 | core/arch/workflow.md | core/arch/workflow.md | Linked orchestration index. |  |
| 2026-01-16 | core/orchestrator/README.md | core/orchestrator/README.md | Added task evidence quick checklist. |  |
| 2026-01-16 | core/orchestrator/handoff/SESSION_WRAP.md | core/orchestrator/handoff/SESSION_WRAP.md | Added review handoff summary. |  |
| 2026-01-16 | core/workflows/SOURCES_INDEX.md | core/workflows/SOURCES_INDEX.md | Added promotion workflow note. |  |
| 2026-01-16 | core/orchestrator/handoff/TASKS.md | core/orchestrator/handoff/TASKS.md | Added status update template. |  |
| 2026-01-16 | core/orchestrator/GLOSSARY.md | core/orchestrator/GLOSSARY.md | Added role responsibility summary. |  |
| 2026-01-16 | core/orchestrator/OPERATOR_MANUAL.md | core/orchestrator/OPERATOR_MANUAL.md | Added orchestration consistency checklist. |  |
| 2026-01-16 | core/orchestrator/handoff/PRIORITIES.md | core/orchestrator/handoff/PRIORITIES.md | Added handoff cadence note. |  |
| 2026-01-16 | core/orchestrator/handoff/REVIEW_CAPTURE.md | core/orchestrator/handoff/REVIEW_CAPTURE.md | Added review summary example. |  |
| 2026-01-16 | core/orchestrator/handoff/SESSION_WRAP.md | core/orchestrator/handoff/SESSION_WRAP.md | Added verification evidence example. |  |
| 2026-01-16 | core/orchestrator/handoff/STATUS.md | core/orchestrator/handoff/STATUS.md | Added handoff ownership fields. |  |
| 2026-01-16 | core/orchestrator/handoff/DECISIONS.md | core/orchestrator/handoff/DECISIONS.md | Added decision template example. |  |
| 2026-01-16 | core/orchestrator/README.md | core/orchestrator/README.md | Added session logs guidance. |  |
| 2026-01-16 | core/orchestrator/handoff/STATUS.md | core/orchestrator/handoff/STATUS.md | Added runtime assumptions checklist. |  |
| 2026-01-16 | core/orchestrator/handoff/DECISIONS.md | core/orchestrator/handoff/DECISIONS.md | Added decision types list. |  |
| 2026-01-16 | core/ORCHESTRATION_INDEX.md | core/ORCHESTRATION_INDEX.md | Added SESSION_WRAP link. |  |
| 2026-01-16 | core/orchestrator/handoff/SESSION_WRAP.md | core/orchestrator/handoff/SESSION_WRAP.md | Added handoff metadata section. |  |
| 2026-01-16 | core/orchestrator/handoff/TASKS.md | core/orchestrator/handoff/TASKS.md | Added reviewer required field. |  |
| 2026-01-16 | core/orchestrator/handoff/STATUS.md | core/orchestrator/handoff/STATUS.md | Added task status mapping. |  |
| 2026-01-16 | README.md | README.md | Rewrote repo README with model-agnostic specs and usage. |  |
| 2026-01-16 | core/README.md | core/README.md | Added core specifications section. |  |
| 2026-01-16 | docs/README.md | (new) | Added local docs overview and canonical references. |  |

## Release Notes
- 2026-01-16: `RELEASE_NOTES_2026-01-16.md`
