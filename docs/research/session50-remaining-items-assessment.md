# Session 50: Remaining Items Assessment

**Date**: 2026-02-27
**Scope**: All deferred Tier 3 ARCH-AEP items, remaining priority work, and gap analyses
**Auditor**: Claude Opus 4.6 (Session 50 research)

---

## 1. Deferred Tier 3 ARCH-AEP Items

### Summary

The ARCH-AEP tracker (`docs/ARCH AGENTIC ENGINEERING AND PLANNING/cycles/2026-02-27/tracker-2026-02-27.md`) shows 24/29 items closed, with 5 items remaining open. All 5 are Tier 3 feature development items plus 2 CI infrastructure items.

| Finding ID | Title | Status | Effort | Category |
|---|---|---|---|---|
| AEP-20260227-H01 | Phase 32.1: Hook Framework | open | L | Feature Gap |
| AEP-20260227-H02 | Phase 32.8: Plugin SDK | open | L | Feature Gap |
| AEP-20260227-H03 | Phase 33: Skill Packs & Distribution | open | L | Feature Gap |
| AEP-20260227-H04 | SkillsBench Adapter | open | M | Feature Gap |
| AEP-20260227-H05 | AWM Tier 2 (A5 + A6) | open | L | Feature Gap |
| AEP-20260227-I02 | Mypy blocking in CI | open | S | CI Infra |
| AEP-20260227-I03 | Test naming convention | open | L | CI Infra |

Additionally, `next-session.md` calls out a Priority 0 item: **17 pre-existing multimodal test failures** (`test_connector_boundary_multimodal_adapters.py` + `test_multimodal_api.py`) referencing a `run_async` method that was renamed to async `run()` during the Phase 35 merge.

---

## 2. Item-by-Item Assessment

### 2.1 AEP-20260227-I02 -- Mypy Blocking in CI

**Current status**: Unblocked. PR #96 remediated all 165 mypy errors. The CI workflow (`ci.yml` line 96-99) has mypy as a step but with `continue-on-error: true` and a TODO comment.

**What needs doing**: Change `continue-on-error: true` to `continue-on-error: false` (or remove the line). Optionally also make the ruff check step blocking (same pattern at line 88-91).

**Effort**: S (10 minutes -- single CI YAML change)
**Dependencies**: None
**Recommendation**: **Do now** -- trivial change, immediate CI quality gate improvement. Should be the very first PR of the next session.

---

### 2.2 AEP-20260227-H01 -- Phase 32.1: Hook Framework

**Current status**: Not started. Session 47 attempted this but the branch was empty.

**What exists already**: The `engine/src/agent33/connectors/` package already implements:
- `middleware.py` -- Full middleware chain pattern with `ConnectorMiddleware` Protocol, plus 6 built-in middleware classes: GovernanceMiddleware, CircuitBreakerMiddleware, TimeoutMiddleware, RetryMiddleware, MetricsMiddleware
- `boundary.py` -- Shared connector-boundary construction, policy packs (default, strict-web, mcp-readonly)
- `circuit_breaker.py` -- CircuitBreaker with CLOSED/OPEN/HALF_OPEN state machine
- `governance.py` -- BlocklistConnectorPolicy
- `executor.py` -- ConnectorExecutor with middleware chain execution
- `models.py` -- ConnectorRequest and related models

**What H01 adds beyond the existing middleware chain**: The current `connectors/` middleware is scoped to external connector calls only. H01 extends the hook pattern to internal engine events:
- Agent invoke lifecycle hooks (pre/post)
- Tool execute lifecycle hooks (pre/post)
- Workflow step lifecycle hooks (pre/post)
- Request lifecycle hooks (pre/post)
- Hook registration with priority ordering
- Tenant-isolated hook configuration
- CRUD API endpoints for runtime hook management

**Effort estimate**: L (realistic estimate: 3-4 focused sessions)
- 9-11 new files across `engine/src/agent33/hooks/` (models, registry, executor, lifecycle events, API routes)
- 60-80 tests
- 6-8 new API endpoints
- Integration wiring in `main.py` lifespan

**Dependencies**: None upstream; blocks H02 (Plugin SDK)

**Risk**: The scope is well-defined by existing connector middleware patterns. The `ConnectorMiddleware` Protocol in `middleware.py` provides a proven template for the hook contract. The main complexity is deciding which engine events to expose as hook points and ensuring hook execution stays under the 500ms budget.

**Recommendation**: **Do now (next session)** -- This is the critical-path item that unblocks H02 and H03. The existing middleware infrastructure provides strong patterns to follow. Research doc exists at `docs/research/hooks-mcp-plugin-architecture-research.md`.

---

### 2.3 AEP-20260227-H02 -- Phase 32.8: Plugin SDK

**Current status**: Not started, blocked by H01.

**What it includes**:
- `PluginManifest` model (name, version, capabilities, hooks, permissions)
- `PluginBase` abstract class (lifecycle methods: install, activate, deactivate, uninstall)
- `PluginRegistry` (discover, install, activate, deactivate, uninstall, version management)
- Capability grants (fine-grained permission model for plugins)
- Sandboxed execution (plugins run within governance boundaries)
- CRUD API endpoints

**Effort estimate**: L (2-3 focused sessions, sequential after H01)

**Dependencies**: H01 (Hook Framework) -- plugins register hooks, so the hook infrastructure must exist first.

**Recommendation**: **Do after H01** -- Natural follow-on. The PluginBase/PluginManifest pattern is well-understood from the research. However, it may be worth descoping the initial implementation to a "Phase 32.8a" that delivers PluginManifest + PluginBase + PluginRegistry without the full sandboxing and capability grants, then iterating.

---

### 2.4 AEP-20260227-H03 -- Phase 33: Skill Packs & Distribution

**Current status**: Not started.

**What it includes**:
- Pack manifest format (PACK.yaml) with semver dependency declarations
- Pack registry and loader (discover, install, resolve dependencies)
- Marketplace API (publish, search, download)
- Agent Skills standard compatibility
- Cross-skill dependency resolution
- 4 ecosystem differentiation features (from the workflow plan)

**Effort estimate**: L (2-3 focused sessions, sequential after H02)
- 7-9 new files
- 70-90 tests
- 6-8 new API endpoints

**Dependencies**: H02 (Plugin SDK) -- packs are distributed bundles of skills + plugins, so the plugin infrastructure must exist first.

**Recommendation**: **Defer until H01 + H02 are complete.** This is the capstone of the extensibility chain. No point starting until the foundation layers are solid.

---

### 2.5 AEP-20260227-H04 -- SkillsBench Adapter

**Current status**: Partial. 536 lines of adapter code salvaged to `docs/research/salvaged-skillsbench-code/`.

See Section 3 below for detailed gap analysis.

**Effort estimate**: M (1-2 sessions)
**Dependencies**: Functionally independent of H01-H03. The adapter uses existing `AgentRuntime.invoke_iterative()`, `SkillRegistry`, `SkillMatcher`, and `TrialEvaluatorAdapter` Protocol -- all of which exist.
**Recommendation**: **Do now (can run in parallel with H01)** -- The salvaged code is high-quality and closely aligned with existing engine APIs. Integration work is the main remaining gap.

---

### 2.6 AEP-20260227-H05 -- AWM Tier 2 (A5 + A6)

**Current status**: Not started.

See Section 4 below for detailed readiness assessment.

**Effort estimate**: L (2-3 sessions)
**Dependencies**: A5 (synthetic environment generation) has no hard dependencies. A6 (group-relative scoring) benefits from A5 but can be implemented independently against existing evaluation infrastructure.
**Recommendation**: **Defer further** -- Lower priority than H01-H04. The ROI is primarily research-grade; H01-H04 deliver concrete product capabilities.

---

### 2.7 AEP-20260227-I03 -- Test Naming Convention

**Current status**: Not started.

See Section 7 below for scope estimate.

**Effort estimate**: L (spread across multiple sessions)
**Dependencies**: None
**Recommendation**: **Defer further / Close as won't-fix** -- The 79% coverage enforcement (PR #95) provides the quality gate that I03 was meant to address indirectly. The cost of renaming 55+ test files and updating all references outweighs the benefit. Instead, adopt a convention going forward: new test files should use 1:1 naming (`test_{module_name}.py`) where practical.

---

## 3. SkillsBench Adapter Gap Analysis (H04)

### 3.1 What Exists (Salvaged Code)

Four files totaling 536 lines in `docs/research/salvaged-skillsbench-code/`:

| File | Lines | Purpose | Quality |
|---|---|---|---|
| `__init__.py` | 5 | Package marker with docstring | Complete |
| `task_loader.py` | 170 | `SkillsBenchTaskLoader` + `SkillsBenchTask` dataclass | Complete, production-quality |
| `adapter.py` | 217 | `SkillsBenchAdapter` implementing `TrialEvaluatorAdapter` | Complete, production-quality |
| `pytest_runner.py` | 146 | `PytestBinaryRewardRunner` using subprocess pytest | Complete, production-quality |

### 3.2 API Alignment Verification

The salvaged code references the following engine APIs. All exist and are compatible:

| Referenced API | Location | Status |
|---|---|---|
| `TrialEvaluationOutcome` | `engine/src/agent33/evaluation/service.py:284` | Exists -- matches expected signature |
| `TrialEvaluatorAdapter` Protocol | `engine/src/agent33/evaluation/service.py:292` | Exists -- `evaluate()` signature matches |
| `AgentRuntime.invoke_iterative()` | `engine/src/agent33/agents/runtime.py:438` | Exists -- accepts `inputs: dict[str, Any]` |
| `SkillRegistry.discover()` | `engine/src/agent33/skills/registry.py` | Exists |
| `SkillRegistry.list_all()` | `engine/src/agent33/skills/registry.py` | Exists |
| `SkillMatcher` | `engine/src/agent33/skills/matching.py` | Exists -- 4-stage pipeline implemented |

### 3.3 What Still Needs Building

| Gap | Description | Effort | Priority |
|---|---|---|---|
| **Move to engine package** | Copy from `docs/research/salvaged-skillsbench-code/` to `engine/src/agent33/evaluation/skillsbench/` | S (15 min) | P0 |
| **IterativeAgentResult alignment** | The adapter accesses `result.tokens_used`, `result.iterations`, `result.tool_calls_made`, `result.termination_reason` -- verify these attributes exist on the actual `IterativeAgentResult` class | S (30 min) | P0 |
| **Tests** | Unit tests for task_loader, adapter, and pytest_runner (~150-200 lines) | M (2-3 hrs) | P0 |
| **Integration wiring** | Wire `SkillsBenchAdapter` into the evaluation API routes or as a CLI command | S (1 hr) | P1 |
| **SkillsBench repo checkout config** | Config setting for the SkillsBench repo path (default: `./skillsbench`) | S (15 min) | P1 |
| **CTRF report integration** | Wire pytest results into CTRF format (the `ctrf.py` module exists) | S (1 hr) | P2 |
| **Experiment config** | YAML experiment config loader for batch runs (referenced in SkillsBench analysis Step 8) | M (2-3 hrs) | P2 |
| **CI benchmark job** | The `benchmark-smoke` job in `ci.yml` already exists; extend to include SkillsBench tasks | S (30 min) | P2 |

### 3.4 Assessment

The salvaged code covers approximately **70% of the adapter work**. The remaining 30% is test writing, integration wiring, and config. The code quality is high -- it follows AGENT-33 conventions (TYPE_CHECKING imports, structured logging, proper error handling, dataclass models). No significant rework is needed.

**Total remaining effort**: M (1 focused session)

---

## 4. AWM Tier 2 Readiness Assessment (H05)

### 4.1 A5: Synthetic Environment Generation

**Goal**: Adapt AWM's 5-stage pipeline concept to generate test environments for AGENT-33's multi-agent DAG scenarios.

**Prerequisites**:
- Understanding of AWM's pipeline (`docs/research/agent-world-model-analysis.md` Section 5) -- DONE
- Access to OpenAI or compatible LLM API for generation -- EXISTS (ModelRouter + provider catalog)
- PostgreSQL for state storage -- EXISTS (multi-tenant DB layer)
- FastAPI for environment hosting -- EXISTS (main app framework)

**What needs building**:
1. Scenario generator that produces multi-agent workflow scenarios (not single-agent like AWM)
2. Database schema generator for scenario-specific tables
3. Task generator that creates evaluatable tasks per scenario
4. Verifier generator that produces pytest-compatible verification code
5. Environment runner that serves scenarios as MCP endpoints or internal API endpoints

**Effort**: L (3+ sessions). This is primarily a research/exploration effort. The AWM pipeline generates SQLite-backed single-agent environments; adapting to PostgreSQL multi-tenant multi-agent workflows is a non-trivial design challenge.

**Risk**: High -- the adaptation from single-agent SQLite to multi-agent PostgreSQL is architecturally different enough that this is more "inspired by AWM" than "adapting AWM." The value is primarily in expanding the evaluation suite beyond the current 7 golden tasks.

### 4.2 A6: Group-Relative Scoring (GRPO-Inspired)

**Goal**: Run the same task across multiple agents and compare performance relatively within the group, rather than against absolute thresholds.

**Prerequisites**:
- Multi-trial evaluation runner -- EXISTS (`evaluation/multi_trial.py`)
- Metrics calculator -- EXISTS (`evaluation/metrics.py`)
- Multiple agent definitions -- EXISTS (6 agents in `agent-definitions/`)
- Evaluation service with golden tasks -- EXISTS (`evaluation/service.py`, `evaluation/golden_tasks.py`)

**What needs building**:
1. Group evaluation orchestrator that runs N agents on the same task set
2. Group-relative scoring function (normalize within group, rank agents)
3. Cross-agent comparison report model
4. API endpoint for group evaluation results
5. Integration with improvement system (Phase 20) to trigger improvement intake when an agent consistently underperforms its group

**Effort**: M-L (2 sessions). More tractable than A5 because it builds directly on existing evaluation infrastructure.

### 4.3 Assessment

A6 is more immediately valuable and less risky than A5. A5 is a significant research project that could consume 3+ sessions with uncertain ROI. A6 produces actionable agent improvement signals using existing infrastructure.

**Recommendation**: If pursuing H05, do A6 first. Defer A5 until the extensibility chain (H01-H03) is complete and there is appetite for a research-heavy exploration.

---

## 5. Frontend Integration Gap Analysis

### 5.1 What Was Recovered (PRs #93 and #94)

**PR #93: Operations Hub Frontend** (G01)
- `frontend/src/features/operations-hub/OperationsHubPanel.tsx` -- 304 lines, full-featured panel with:
  - Process list with status filter, text search, auto-polling (1.5s interval)
  - Process detail view with metadata display, action history
  - Pause/resume/cancel controls with confirmation dialogs
- `frontend/src/features/operations-hub/api.ts` -- Typed API layer calling backend
- `frontend/src/features/operations-hub/helpers.ts` -- Status formatting, filtering, sorting utilities
- `frontend/src/features/operations-hub/helpers.test.ts` -- Unit tests for helpers
- `frontend/src/features/operations-hub/types.ts` -- TypeScript interfaces

**PR #94: Outcomes Dashboard Frontend** (G02)
- `frontend/src/features/outcomes-dashboard/OutcomesDashboardPanel.tsx` -- 285 lines, full-featured panel with:
  - SVG sparkline trend visualization
  - Domain filter, window size selector, metric type filter
  - Declining trend detection with automatic improvement intake form
  - Recent events table
- `frontend/src/features/outcomes-dashboard/api.ts` -- Typed API layer
- `frontend/src/features/outcomes-dashboard/helpers.ts` -- Metric formatting, sparkline generation, decline detection
- `frontend/src/features/outcomes-dashboard/helpers.test.ts` -- Unit tests
- `frontend/src/features/outcomes-dashboard/types.ts` -- TypeScript interfaces

### 5.2 App Integration Status

Both panels are wired into `frontend/src/App.tsx`:
- Operations Hub is available as the "Operations Hub" tab
- Outcomes Dashboard is available as the "Outcomes" tab
- Both accept `token`, `apiKey`, and `onResult` props from the App shell
- The App shell has 6 tabs: Chat Central, Voice Call, Integrations, Operations Hub, Outcomes, Advanced Settings

### 5.3 Remaining Frontend Gaps

| Gap | Description | Effort |
|---|---|---|
| **No E2E wiring verification** | The frontend API calls (`fetchOperationsHub`, `fetchOutcomesDashboard`, etc.) target backend API routes that exist (`operations_hub.py`, `outcomes.py`) but there is no integration test confirming the request/response shapes match | M |
| **No build/deploy pipeline** | The `frontend/` has a `package.json` but no CI build step. The `ci.yml` does not test frontend code | M |
| **Missing CSS** | The JSX references class names (e.g., `operations-hub-panel`, `outcomes-dashboard-panel`, `trend-sparkline`) that likely need CSS definitions. No CSS files were found in the recovered PRs | S-M |
| **Missing feature panels** | Several domain panels still use the legacy `DomainPanel` wrapper in the Advanced Settings tab rather than having dedicated feature panels like Operations Hub and Outcomes do | L |
| **No TypeScript strict mode** | Frontend has TypeScript installed but strictness level is unknown; no `tsconfig.json` was examined | S |
| **Vite config** | A Vite setup exists (node_modules include vite, vitest), but the build configuration and proxy settings for backend API calls were not verified | S |

### 5.4 Assessment

The frontend is in a **functional but incomplete** state. The two most important panels (Operations Hub and Outcomes Dashboard) are recovered and wired into the app shell. The immediate need is not more frontend features but rather:
1. Ensuring the existing frontend builds without errors
2. Adding a frontend build step to CI
3. CSS styling for the recovered components
4. E2E smoke test confirming backend API compatibility

---

## 6. Phase 29-33 Completion Matrix

Based on `docs/phases/PHASE-29-33-WORKFLOW-PLAN.md` and the phase index (`docs/phases/README.md`):

| Phase | Title | Status | Evidence | Remaining |
|---|---|---|---|---|
| **29** | Reasoning Protocol & ISC | **Complete** | Merged PRs #55, #57. `reasoning/`, `isc.py`, `stuck_detector.py` all in engine. Tests: `test_reasoning.py`, `test_isc.py`, `test_stuck_detector.py` | None |
| **30** | Adaptive Execution & Deterministic Routing | **Stage 1 complete** | Backend merged. `test_phase30_effort_routing.py` exists. Stage 2 UI was lost (PR #48) but recovered in PR #94 (Outcomes Dashboard) | Stage 2 UI styling/integration verification |
| **31** | Continuous Learning & Signal Capture | **Stage 1 complete** | `test_phase31_learning_signals.py` exists. Persistence and quality work noted as in-progress | Persistence layer, quality signal extraction refinement |
| **32** | Middleware Chain, MCP Connectors & Circuit Breakers | **Partial** | Kickoff merged (PR #67). `connectors/` package exists with middleware chain, circuit breaker, governance, boundary, executor. `test_phase32_connector_boundary.py` exists | **H01 (Hook Framework)** -- extends middleware to internal events. **H02 (Plugin SDK)** -- plugin infrastructure |
| **33** | Skill Packs & Distribution | **Not started** | No code, no tests | Entire phase. Blocked by H01 + H02 |
| **35** | Multimodal Async-Governance Convergence | **Complete** | Merged PR #85 | 17 test failures from `run_async` -> `run()` rename need fixing |

### Completion Summary

| Phase | % Complete | Blocker |
|---|---|---|
| 29 | 100% | -- |
| 30 | 80% | Frontend CSS/styling |
| 31 | 60% | Persistence, quality refinement |
| 32 | 50% | H01 (hooks), H02 (plugin SDK) |
| 33 | 0% | H01, H02 |
| 35 | 95% | 17 test failures |

---

## 7. Test Naming Convention Scope Estimate (I03)

### Current State

- **Source modules** (non-`__init__.py`): 216 files across `engine/src/agent33/`
- **Test files** (top-level): 65 files in `engine/tests/`
- **Exact 1:1 name matches**: 10 files (test file name matches source module name)
  - `airllm_provider`, `chat`, `context_manager`, `health`, `isc`, `llm_security`, `mcp_scanner`, `reasoning`, `stuck_detector`, `tool_loop`

### Naming Patterns in Use

| Pattern | Count | Examples |
|---|---|---|
| `test_{module_name}.py` (exact match) | 10 | `test_chat.py` -> `chat.py` |
| `test_{phase_N}_{topic}.py` (phase-based) | 8 | `test_phase14_security.py`, `test_phase15_review.py` |
| `test_{subsystem}_{subtopic}.py` (compound) | ~25 | `test_execution_cli_adapter.py`, `test_connector_boundary_llm_memory.py` |
| `test_{feature}_api.py` (API route tests) | ~10 | `test_operations_hub_api.py`, `test_outcomes_api.py` |
| `test_{integration/e2e}.py` (integration) | 4 | `test_integration_e2e.py`, `test_integration_wiring.py` |
| Other composite patterns | ~8 | `test_skillsbench_priority_surfaces.py`, `test_partial_features.py` |

### Scope of Standardization

If adopting strict 1:1 naming:
- 55+ test files would need renaming
- Some composite test files cover multiple source modules and would need splitting
- All import references in conftest and CI would need updating
- This is a **high-effort, low-value** change given that coverage enforcement (79%, 70% threshold) already provides the quality gate

### Recommendation

**Close as won't-fix** with a forward-looking convention:
- New test files should use `test_{module_name}.py` format where practical
- Composite test files are acceptable when they test a subsystem (e.g., `test_phase14_security.py` testing multiple security modules is fine)
- The 79% coverage threshold (PR #95) makes the mapping concern moot for regression prevention

---

## 8. Recommended Sequencing

### Immediate (Session 50)

| # | Item | AEP ID | Effort | Rationale |
|---|---|---|---|---|
| 1 | Fix 17 multimodal test failures | -- | S | P0 from next-session.md. Tests fail due to `run_async` -> `run()` rename. Quick fix. |
| 2 | Wire mypy as blocking in CI | I02 | S | Remove `continue-on-error: true` from CI. 10-minute change. |
| 3 | Wire ruff check as blocking in CI | -- | S | Same pattern. Both ruff and mypy are at 0 errors. |

### Next Session(s) (Session 50-51)

| # | Item | AEP ID | Effort | Rationale |
|---|---|---|---|---|
| 4 | Phase 32.1: Hook Framework | H01 | L | Critical path. Unblocks H02 and H03. Existing middleware patterns provide a template. |
| 5 | SkillsBench Adapter integration | H04 | M | Can run in parallel with H01 (different code areas). 70% already done. |

### Following Session(s) (Session 52-53)

| # | Item | AEP ID | Effort | Rationale |
|---|---|---|---|---|
| 6 | Phase 32.8: Plugin SDK | H02 | L | Blocked by H01. Natural follow-on. |
| 7 | Phase 31 persistence & quality | -- | M | Strengthen learning signal pipeline. |
| 8 | Frontend CI build step | -- | M | Ensure frontend builds cleanly, add to CI. |

### Later Sessions (Session 54+)

| # | Item | AEP ID | Effort | Rationale |
|---|---|---|---|---|
| 9 | Phase 33: Skill Packs & Distribution | H03 | L | Blocked by H01 + H02. Capstone of extensibility chain. |
| 10 | AWM Tier 2: A6 (group-relative scoring) | H05 (partial) | M | Useful for evaluation improvement. Lower priority than extensibility chain. |
| 11 | AWM Tier 2: A5 (synthetic environments) | H05 (partial) | L | Research-heavy. Defer until extensibility chain is complete. |

### Recommend Close / Won't-Fix

| Item | AEP ID | Reason |
|---|---|---|
| Test naming convention | I03 | Coverage enforcement (79%, 70% threshold) provides the quality gate. Adopt convention forward-looking. |

---

## 9. Critical Path Diagram

```
Session 50:
  [Fix multimodal tests] ──→ [CI: mypy + ruff blocking]
  [SkillsBench Adapter (H04)] ─────────────────────────→ [Benchmark smoke integration]
  [Hook Framework (H01)] ──→ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─→ ...

Session 51:
  ... ──→ [Hook Framework (H01) contd.] ──→ [Plugin SDK (H02)]

Session 52:
  [Plugin SDK (H02) contd.] ──→ [Skill Packs (H03)]
  [Phase 31 persistence]
  [Frontend CI]

Session 53:
  [Skill Packs (H03) contd.]
  [AWM A6: group-relative scoring]

Session 54+:
  [AWM A5: synthetic environments]
```

**Critical path**: H01 -> H02 -> H03 (estimated 6-9 sessions for the full extensibility chain)

**Parallel tracks**:
- H04 (SkillsBench) is independent and can proceed immediately
- Phase 31 persistence is independent
- Frontend CI is independent
- AWM A6 is independent of the extensibility chain

---

## 10. Risk Register

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| H01 scope creep (too many hook points) | Delays H02/H03 | Medium | Limit initial hook points to agent_invoke and tool_execute only. Add workflow_step and request_lifecycle in a follow-up. |
| SkillsBench repo unavailable | H04 cannot be fully tested | Low | Salvaged code includes the task loader; create a minimal test fixture set. |
| Multimodal test fixes cascade | More failures surface after fixing the 17 known ones | Low | The 17 failures are all the same root cause (`run_async` -> `run()`). Unlikely to cascade. |
| Plugin SDK capability model too complex | Delays H02 | Medium | Start with a simple allowlist model. Evolve to fine-grained capabilities later. |
| Frontend CSS debt blocks user testing | Users cannot evaluate recovered panels | Medium | Create a minimal CSS file for operations-hub and outcomes-dashboard classes in the same PR that adds frontend to CI. |

---

## Appendix A: File References

| Purpose | Absolute Path |
|---|---|
| ARCH-AEP backlog | `D:\GITHUB\AGENT33\docs\ARCH AGENTIC ENGINEERING AND PLANNING\backlog-2026-02-27.md` |
| ARCH-AEP tracker | `D:\GITHUB\AGENT33\docs\ARCH AGENTIC ENGINEERING AND PLANNING\cycles\2026-02-27\tracker-2026-02-27.md` |
| Phase 29-33 plan | `D:\GITHUB\AGENT33\docs\phases\PHASE-29-33-WORKFLOW-PLAN.md` |
| Phase index | `D:\GITHUB\AGENT33\docs\phases\README.md` |
| SkillsBench analysis | `D:\GITHUB\AGENT33\docs\research\skillsbench-analysis.md` |
| Salvaged SkillsBench code | `D:\GITHUB\AGENT33\docs\research\salvaged-skillsbench-code\` |
| AWM analysis | `D:\GITHUB\AGENT33\docs\research\agent-world-model-analysis.md` |
| Hook/Plugin research | `D:\GITHUB\AGENT33\docs\research\hooks-mcp-plugin-architecture-research.md` |
| Next session briefing | `D:\GITHUB\AGENT33\docs\next-session.md` |
| CI workflow | `D:\GITHUB\AGENT33\.github\workflows\ci.yml` |
| Connectors middleware | `D:\GITHUB\AGENT33\engine\src\agent33\connectors\middleware.py` |
| Evaluation service | `D:\GITHUB\AGENT33\engine\src\agent33\evaluation\service.py` |
| Agent runtime | `D:\GITHUB\AGENT33\engine\src\agent33\agents\runtime.py` |
| Frontend App shell | `D:\GITHUB\AGENT33\frontend\src\App.tsx` |
| Operations Hub panel | `D:\GITHUB\AGENT33\frontend\src\features\operations-hub\OperationsHubPanel.tsx` |
| Outcomes Dashboard panel | `D:\GITHUB\AGENT33\frontend\src\features\outcomes-dashboard\OutcomesDashboardPanel.tsx` |
