# Adaptive Evolution Strategy

**Date:** 2026-02-14
**Basis:** 30 repository dossiers, paradigm analysis, AGENT-33 phase plan (Phases 14-20)
**Philosophy:** Assimilate paradigms, don't chase feature checklists.

---

## Core Principle

AGENT-33 evolves by absorbing proven patterns from the research sprint and integrating them into its existing architecture, not by replicating features from other projects. Each evolution cycle targets a **paradigm shift** -- a fundamental change in how the system operates -- rather than a feature list. The difference: a feature checklist says "add BM25 search." A paradigm shift says "transform AGENT-33 from vector-only retrieval to hybrid intelligence that understands both keywords and semantics, with the retrieval strategy itself becoming a tunable parameter in the training loop."

---

## Evolution Cycles

### Cycle A: Foundation Hardening (Phases 14-15)

**Paradigm target:** Transform AGENT-33 from a system where governance exists in code but not in behavior, to one where every agent action is governed at both the runtime AND prompt level.

**Why this is first:** The research sprint confirmed the governance-prompt disconnect is the #1 architectural flaw. Every subsequent cycle depends on governance actually working. The training loop optimizes prompts that must reach the LLM. Conversational routing needs guardrails the LLM understands. Skills need governance injected at load time.

#### Phase 14: Security Hardening and Prompt Injection Defense

**From dossiers -- high-priority recommendations:**

| Recommendation | Source | Implementation |
|---|---|---|
| Fix governance-prompt disconnect: inject `GovernanceConstraints` into system prompts | agent-zero, claude-code, system-prompts-ai-tools | Modify `runtime.py:_build_system_prompt()` to load governance templates from `prompts/governance/{role}.md`. Every agent gets safety rules, capability allowlists, and behavioral constraints in its system message. |
| Three-tier permission model (read/modify/execute) | claude-code, opencode | Add `PermissionTier` enum to security models. Tag each tool in registry. Extend `AuthMiddleware` for session-scoped and persistent approvals. |
| PreToolUse/PostToolUse hooks with decision control | claude-code, continuous-claude-v3 | Add `hooks/` module with event types. Hooks return allow/deny/ask + optional input modification. Integrate with `execution/executor.py` pipeline. |
| Recursive secret masking in logs | agent-zero | Add `mask_recursive()` to structlog processor pipeline. Define sensitive key patterns. Apply to tool args, LLM responses, workflow state. |
| Prompt injection defense: multi-layer (blocklist + context isolation + fail-closed) | claude-code, zeroclaw | Strengthen existing `security/` prompt injection detection. Add input sanitization for user messages before they reach agent prompts. Context-isolate untrusted content. |
| Command allowlisting with deny-first defaults | zeroclaw, claude-code | Replace current global allowlist with deny-first model. Use deny rules + hooks instead of fragile argument-based allowlisting. |
| Fail-hard on default secrets in production | trivy (supply chain hardening) | Upgrade `API_SECRET_KEY`/`JWT_SECRET` from warn-only to startup failure when `ENVIRONMENT=production` and defaults detected. |

**Success metrics:**
- Every agent's system prompt includes governance constraints (verifiable by prompt inspection)
- Zero tool calls execute without permission tier check
- Secret patterns in log output are zero (tested by log scanning)
- Prompt injection detection catches OWASP top-10 injection patterns

#### Phase 15: Review Automation and Two-Layer Review

**From dossiers -- high-priority recommendations:**

| Recommendation | Source | Implementation |
|---|---|---|
| Iterative refinement with advisor agents | ai-researcher | Add `refinement_cycle` workflow action that loops code-worker output through QA agent until quality threshold met or max iterations exceeded. |
| Hierarchical documentation synthesis | ai-researcher | Extend `SessionSummarizer` to use staged generation: extract facts, build section narratives, assemble with consistency checks, verify. |
| Progressive skill disclosure (L0/L1/L2) | awesome-claude-skills, claude-code | Modify agent loading to inject only description + capability list at L0. Load full system prompt at L1 (invocation). Load bundled resources at L2 (on demand). |
| Template-guided output with schema validation | ai-researcher, sparrow | Define output templates for common artifacts (agent definitions, workflow results, execution reports). Validate outputs against schemas before persisting. |
| SKILL.md-compatible skill format | awesome-claude-skills, agent-zero, claude-plugins | Define AGENT-33 skill format: YAML frontmatter + markdown body + scripts/templates/references directories. Support `invocation_mode`, `allowed_tools`, `execution_context`. |

**Success metrics:**
- QA agent catches >50% of issues that previously required human review
- Agent loading reduces base prompt size by >60% via progressive disclosure
- All agent outputs validate against defined schemas

---

### Cycle B: Intelligence Upgrade (Phases 16-17)

**Paradigm target:** Transform AGENT-33 from a vector-only retrieval system with single-evaluator scoring to a hybrid intelligence platform with multi-strategy retrieval and ensemble evaluation.

**Why second:** Intelligence upgrades require the governance foundation from Cycle A. Without governed agents, smarter retrieval just feeds better data to ungoverned behavior.

#### Phase 16: Observability and Trace Pipeline

**From dossiers -- high-priority recommendations:**

| Recommendation | Source | Implementation |
|---|---|---|
| Tool execution progress streaming | agent-zero | Add `set_progress(status)` to tool base class. Emit events to observability layer. Display in dashboard real-time view. |
| WebSocket state sync for real-time monitoring | agent-zero, livekit | Add `/ws/state` endpoint. Broadcast workflow steps, tool calls, agent invocations. Namespace isolation for multi-tenancy. |
| Structured cost tracking per operation | edgequake | Track `prompt_tokens`, `completion_tokens`, `total_tokens` per LLM call. Aggregate by agent, workflow, and tenant. Calculate cost by model pricing. |
| Kubernetes-ready health endpoints | edgequake, trivy | Extend health checks to include component-level status: DB, Redis, NATS, LLM provider, memory store. Return structured JSON with version and status. |
| JSON-lines trajectory logging for replay | rlm | Log iteration-level execution traces (prompt, response, tool calls, timing) as append-only JSONL. Enable replay and debugging of agent behavior. |

**Success metrics:**
- Every tool call has progress visibility (not black-box until completion)
- Cost-per-workflow trackable to individual LLM calls
- Execution replays reproducible from trace logs

#### Phase 17: Evaluation Suite Expansion and Regression Gates

**From dossiers -- high-priority recommendations:**

| Recommendation | Source | Implementation |
|---|---|---|
| Hybrid retrieval: BM25 + vector + weighted merge | weknora, edgequake, zeroclaw | Add PostgreSQL FTS for BM25 keyword search. Implement weighted merge scoring alongside existing pgvector similarity. Strategy weights configurable per knowledge base. |
| Query rewriting for conversational context | weknora | Add preprocessing step: LLM rewrites context-dependent queries into standalone forms before retrieval. Run both rewritten NL query and extracted keywords. |
| Batch embeddings (67x speedup) | edgequake | Replace sequential embedding in `embeddings.py:36` with batched processing. Use MAX_EMBEDDING_BATCH_SIZE constants (2048 for OpenAI, 512 for Ollama). |
| HTTP client pooling | edgequake | Initialize HTTP clients once during provider construction in `ollama.py`, not per-request. Store on provider instance. Reuse across all requests. |
| Chunk size upgrade: 500 chars to 1200 tokens | rag-anything, weknora | Increase chunk size with tokenizer-aware splitting. Add configurable overlap (100 tokens). Avoid mid-word/mid-sentence breaks. |
| Debiased multi-evaluator assessment | ai-researcher | Use multiple LLM judges with randomized presentation order and temperature=1.0. Aggregate scores across providers. Detect and compensate for positional bias. |
| Benchmark-driven development | ai-researcher | Create `benchmarks/` directory with curated test cases (input, expected output, evaluation criteria). Integrate into CI/CD for regression detection. |
| Reranking pipeline | rag-anything, weknora | Add optional reranking stage after retrieval. Support Jina/Cohere rerankers or local cross-encoder. Configurable per query. |

**Success metrics:**
- Retrieval relevance improves >25% on benchmark suite (hybrid vs vector-only)
- Embedding throughput increases >50x via batching
- Evaluation variance decreases >40% with multi-evaluator ensemble
- Query rewriting improves retrieval hit rate for conversational queries by >30%

---

### Cycle C: Capability Expansion (Phase 18+)

**Paradigm target:** Transform AGENT-33 from a text-only system with static workflows to a multimodal platform with dynamic routing and document understanding.

**Why third:** Capability expansion builds on governed tools (Cycle A) and intelligent retrieval (Cycle B). Document processing feeds into RAG. Dynamic routing requires mature governance.

#### Phase 18: Autonomy Budget Enforcement and Policy Automation

**From dossiers -- high-priority recommendations:**

| Recommendation | Source | Implementation |
|---|---|---|
| Dynamic agent routing (LLM-decided handoffs) | swarm, agent-zero, opencode | Add `invoke_agent_dynamic` workflow action. Orchestrator LLM selects target agent from registry based on task description. Log routing reasoning for auditability. |
| Document processing (PDF, images, tables) | paddleocr, sparrow, rag-anything | Add `DocumentProcessorTool` wrapping PaddleOCR Python API. Support PDF text extraction, table structure recognition, and layout analysis. |
| Media extraction (audio/video metadata) | yt-dlp | Add `MediaExtractorTool` wrapping yt-dlp for transcript extraction and metadata from web media sources. |
| Multi-runtime code execution with session persistence | agent-zero | Add session management to `execution/executor.py`. Maintain `sessions: dict[str, ExecutionSession]`. Preserve environment across calls within session. |
| Skill search tool for large catalogs | claude-code, awesome-claude-skills | Add `SkillSearchTool` that queries skill registry on-demand. Activate when skill definitions exceed context budget threshold. |
| Accessibility-first browser interaction | chromepilot | Replace CSS selectors in `browser.py` with accessibility tree extraction. Filter to actionable elements. Reduce context from ~387 to ~100-150 elements. |
| Context_variables for workflow state | swarm | Add mutable dict passed through workflow steps, complementing existing expression evaluator. Enable runtime state accumulation across agent handoffs. |

**Success metrics:**
- Dynamic routing selects correct agent >80% of the time on benchmark
- PDF text extraction accuracy >90% on document benchmark
- Code execution sessions persist state across calls (install once, run many)
- Browser tool context reduces >60% via accessibility filtering

---

### Cycle D: Autonomy and Self-Improvement (Phases 19-20)

**Paradigm target:** Transform AGENT-33 from a human-directed system to one that autonomously improves its own policies, prompts, and retrieval strategies based on measured outcomes.

**Why last:** Full autonomy requires mature governance (Cycle A), reliable intelligence (Cycle B), and broad capabilities (Cycle C). Autonomous improvement of a broken system amplifies errors.

#### Phase 19: Release and Sync Automation

**From dossiers -- high-priority recommendations:**

| Recommendation | Source | Implementation |
|---|---|---|
| SBOM generation and supply chain verification | trivy | Generate CycloneDX SBOM for releases. Sign with Cosign. Scan own dependencies with Trivy. |
| Checkpoint-resume durable execution | trigger.dev | Add waitpoints to long-running workflows. Checkpoint state and release resources. Resume from same point after dependencies complete. |
| Sub-workflow composition | n8n-workflows | Add `invoke_subworkflow` action. Support sync and async modes. Memory isolation per sub-workflow. Nesting limit of 2-3 levels. |
| Managed enterprise settings | claude-code | Add system-wide config at `/etc/agent33/managed-settings.json`. Priority: Managed > CLI > Project > User. `allowManagedPermissionRulesOnly`, `allowManagedHooksOnly`. |
| Semantic release automation | cc-wf-studio | Integrate semantic-release for automated versioning from commit messages. Generate changelogs from structured commits. |

#### Phase 20: Continuous Improvement and Research Intake

**From dossiers -- high-priority recommendations:**

| Recommendation | Source | Implementation |
|---|---|---|
| LLM-driven memory consolidation | agent-zero | Add `memory_consolidation.py` that queries similar memories on insertion. LLM analyzes and decides: MERGE, REPLACE, UPDATE, KEEP_SEPARATE, SKIP. 0.9 similarity threshold for REPLACE. |
| Multi-agent credit assignment | multi-agent-rl-survey | Score individual agent contributions to workflow outcomes. Implement attention-based credit assignment. Optimize per-agent prompts based on team-level rewards. |
| Progressive experimental cycles | ai-researcher | Test policy changes on minimal data first. Validate with advisor agent. Deploy to full production only after prototype passes. |
| Hierarchical prompt composition with inheritance | agent-zero | Add `base_agent` field to agent definitions. Load base definition and merge. Accumulate prompts from base + current. Enable project-specific customization without duplication. |
| Community skill contribution pipeline | awesome-claude-skills | Validation rules for submitted skills. Automated security scanning. Version pinning. Review gates before catalog inclusion. |
| Knowledge graph extraction for entity-relationship retrieval | edgequake, rag-anything | Extract entities and relationships via LLM. Store in graph alongside vectors. Enable relationship-based queries. Apply Glean pattern (+18% recall). |

**Success metrics:**
- Memory consolidation reduces storage growth by >30% without recall degradation
- Multi-agent credit assignment improves team-level workflow outcomes by >15%
- Policy changes tested on prototype before full deployment (zero untested production changes)
- Knowledge graph queries outperform vector-only on relationship-dependent questions by >20%

---

## Feature Assimilation Queue

Ordered by dependency chain (each row requires preceding rows to be complete):

| Priority | Feature | Source Paradigm | Source Repos | Target Phase | Effort | Impact |
|----------|---------|-----------------|--------------|--------------|--------|--------|
| **A1** | Governance-prompt injection | Tool-Augmented | agent-zero, claude-code, system-prompts | 14 | Medium | Critical |
| **A2** | Three-tier permissions | Tool-Augmented | claude-code, opencode | 14 | Medium | High |
| **A3** | PreToolUse/PostToolUse hooks | Tool-Augmented | claude-code, continuous-claude-v3 | 14 | High | Critical |
| **A4** | Recursive secret masking | Security | agent-zero | 14 | Low | High |
| **A5** | Batch embeddings + HTTP pooling | RAG-Native | edgequake | 14-15 | Low | High |
| **A6** | Chunk size upgrade (1200 tokens) | RAG-Native | rag-anything, weknora | 14-15 | Low | Medium |
| **B1** | Iterative refinement loops | Self-Improvement | ai-researcher | 15 | Medium | High |
| **B2** | Progressive skill disclosure | Skill Ecosystem | awesome-claude-skills | 15 | Medium | High |
| **B3** | SKILL.md format + discovery | Skill Ecosystem | awesome-claude-skills, agent-zero | 15 | High | Medium |
| **C1** | BM25 hybrid search | RAG-Native | weknora, edgequake, zeroclaw | 16-17 | High | High |
| **C2** | Query rewriting | RAG-Native | weknora | 17 | Medium | Medium |
| **C3** | Multi-evaluator ensemble | Self-Improvement | ai-researcher | 17 | Medium | High |
| **C4** | Real-time WebSocket state | Observability | agent-zero, livekit | 16 | Medium | Medium |
| **C5** | Reranking pipeline | RAG-Native | rag-anything, weknora | 17 | Medium | Medium |
| **D1** | Dynamic agent routing | Conversational | swarm, agent-zero | 18 | High | High |
| **D2** | Document processing | Document/Media | paddleocr, sparrow | 18 | High | High |
| **D3** | Code execution sessions | Tool-Augmented | agent-zero | 18 | Medium | Medium |
| **D4** | Sub-workflow composition | Orchestration | n8n-workflows | 19 | High | High |
| **D5** | Memory consolidation | Self-Improvement | agent-zero | 20 | Medium | High |
| **D6** | Multi-agent credit assignment | Self-Improvement | multi-agent-rl-survey | 20 | Very High | High |

---

## Anti-Patterns to Avoid

These patterns were observed in the research sprint as common failure modes. AGENT-33 must actively avoid them.

### 1. Governance Theater
**Pattern:** Define governance constraints in code (models, schemas, enums) but never communicate them to the LLM that makes decisions.
**Observed in:** AGENT-33 (current), Claude Code (permissions exist but not in prompts), Awesome-Claude-Skills (frontmatter not injected into skill body).
**Avoidance:** Every governance constraint MUST appear in both (a) runtime enforcement code AND (b) the agent's system prompt. If the LLM doesn't know about a constraint, the constraint is theater.

### 2. Feature Checklist Syndrome
**Pattern:** Copy features from other projects without understanding the paradigm they serve. Results in disconnected capabilities that don't compose.
**Observed in:** Repos that add "RAG" by bolting vector search onto a chat app without retrieval strategy, reranking, or query rewriting.
**Avoidance:** Each feature assimilation must connect to a paradigm shift (Cycles A-D). If a feature doesn't serve a paradigm, defer it.

### 3. Security-Last Development
**Pattern:** Build capabilities first, add security later. "Later" never arrives because the codebase now has architectural assumptions that conflict with security.
**Observed in:** OpenCode explicitly states "permissions are UX guardrails, not security boundaries." Agent-Zero has layered timeouts but open filesystem access.
**Avoidance:** Cycle A (Foundation Hardening) is first for a reason. Every subsequent capability is built on the security foundation, not retrofitted.

### 4. Premature Optimization
**Pattern:** Rewrite working Python in Rust/Go because benchmarks from another project show better numbers, without profiling your own bottlenecks.
**Observed in:** ZeroClaw and EdgeQuake demonstrate impressive Rust performance, but their workload profiles (high-concurrency RAG serving) differ from AGENT-33's (orchestration with moderate concurrency).
**Avoidance:** Profile first. AGENT-33's actual bottlenecks are LLM API latency and sequential embedding -- both fixable in Python (batching, pooling). Only move to Rust extensions after Python optimizations plateau.

### 5. Monolithic Skill Ingestion
**Pattern:** Accept community skills/plugins without sandboxing, versioning, or security review. One malicious skill compromises the entire system.
**Observed in:** Awesome-Claude-Skills (no execution isolation for bundled scripts), Agent-Zero (skills run with full host access).
**Avoidance:** All community skills run through `CodeExecutor` with `SandboxConfig`. Disclosure level L2 (show user full script + confirm) for any skill that executes code. Pin skill versions. Scan for secrets patterns.

### 6. Training Loop Disconnected from Governance
**Pattern:** Optimize agent prompts via training loop, but the optimized prompts never include governance rules, so the training learns to be capable but ungoverned.
**Observed in:** AGENT-33 (current) -- training subsystem exists but governance never reaches prompts being optimized.
**Avoidance:** Training loop MUST optimize the complete prompt including governance section. Evaluation must penalize governance violations, not just task completion.

---

## Success Metrics by Cycle

### Cycle A (Phases 14-15) -- Foundation
- [ ] 100% of agent system prompts include governance constraints (automated check)
- [ ] Zero tool calls bypass permission tier checks (integration test)
- [ ] Zero secret patterns in log output (log scanning test)
- [ ] Prompt injection detection covers OWASP top-10 patterns (benchmark)
- [ ] Base prompt size reduced >60% via progressive disclosure (measurement)
- [ ] Embedding throughput >50x improvement via batching (benchmark)

### Cycle B (Phases 16-17) -- Intelligence
- [ ] Retrieval relevance >25% improvement on benchmark (hybrid vs vector-only)
- [ ] Evaluation variance <40% of single-evaluator baseline (multi-evaluator)
- [ ] Cost-per-workflow trackable to individual LLM calls (observability)
- [ ] Every tool call has progress visibility (not black-box)
- [ ] Query rewriting improves conversational retrieval >30% (benchmark)

### Cycle C (Phase 18+) -- Capability
- [ ] Dynamic routing accuracy >80% on agent selection benchmark
- [ ] PDF text extraction accuracy >90% on document benchmark
- [ ] Browser tool context reduction >60% via accessibility filtering
- [ ] Code execution session persistence across calls (integration test)

### Cycle D (Phases 19-20) -- Autonomy
- [ ] Memory consolidation reduces storage growth >30% (measurement)
- [ ] Multi-agent team outcomes improve >15% with credit assignment (benchmark)
- [ ] Zero untested policy changes reach production (process check)
- [ ] Sub-workflow composition supports 2-level nesting (integration test)

---

## Appendix: Dossier-to-Cycle Mapping

Which dossiers inform which evolution cycle:

| Cycle | Primary Dossiers | Secondary Dossiers |
|-------|-----------------|-------------------|
| **A (Foundation)** | agent-zero, anthropic-claude-code, system-prompts-ai-tools, zeroclaw, trivy | opencode, awesome-claude-skills, claude-plugins-official |
| **B (Intelligence)** | tencent-weknora, edgequake, rag-anything, ai-researcher | rlm, memorizer, ui-ux-pro-max |
| **C (Capability)** | openai-swarm, paddleocr, sparrow, chromepilot, n8n-workflows | yt-dlp, agent-zero, cc-wf-studio, livekit |
| **D (Autonomy)** | ai-researcher, multi-agent-rl-survey, continuous-claude-v3, trigger-dev | agent-zero, edgequake, rag-anything, plane |
