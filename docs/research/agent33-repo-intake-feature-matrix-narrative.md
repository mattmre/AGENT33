# AGENT 33 Narrative: Temporary Repo Pull + Multi‑Agent Analysis to Produce a Master Features Matrix and 40‑Phase Roadmap

**Objective:** Provide a repeatable, evidence-first orchestration narrative that your code (and your agents) can execute to:
1) **Temporarily pull** a set of high-signal agentic repos (shallow clone, snapshot, cleanup),
2) Run **multi-agent analysis** to extract/normalize features into a **master features matrix**, and
3) Produce **per-repo dossiers** plus a **40-phase development plan** for your own orchestration system.

This is written to align with AGENT 33 principles: **model-agnostic**, **evidence-first**, **minimal diffs**, **auditability**, **promotion discipline**.

---

## 1) Operating constraints (non-negotiables)

### 1.1 Safety, governance, and legal
- **Do not execute** code from untrusted repos during intake. Treat every repo as potentially hostile.
- Analysis is **read-only**: parse text files, metadata, and configs. Do not run install scripts, build steps, or test suites unless explicitly approved.
- **Respect licenses**: store only *necessary* excerpts for evidence (paths/line refs), not bulk copying code. Keep raw snapshots immutable.
- Run clones in an **isolated workspace** (container or sandbox) with controlled network and filesystem scope.

### 1.2 Auditability and repeatability
Each run must produce:
- the exact repo list + selection criteria used,
- commit SHAs and timestamps,
- extraction evidence (file paths + line anchors where feasible),
- the generated matrix and dossiers,
- a changelog entry if anything is promoted to `core/`.

---

## 2) Inputs and outputs (contract)

### 2.1 Inputs
- A YAML/JSON `repo_set` containing candidate repos and constraints:
  - `min_stars: 5000`
  - `updated_within_days: 7`
  - `topics: ["agent", "agentic", "orchestration", "autonomous", "workflow", "mcp"]`
- A canonical **Feature Taxonomy** (YAML) maintained in `core/features/taxonomy.yaml`
- AGENT 33 operator policy: approval gates, risk triggers, evidence format

### 2.2 Outputs (deliverables)
For each run `RUN_ID`:
1) `collected/github/<RUN_ID>/repos/<org__repo>/`  
   - immutable snapshot metadata: repo URL, SHA, timestamp, stars, default branch, license  
2) `collected/github/<RUN_ID>/evidence/<org__repo>.md`  
   - extraction evidence: file pointers and citations  
3) `core/features/matrix/<RUN_ID>.md` + `core/features/matrix/<RUN_ID>.csv`  
   - master feature matrix (normalized + comparable)  
4) `core/repo-dossiers/<org__repo>.md`  
   - “extensive” per-repo dossiers (architecture, primitives, ops, security, strengths/gaps)  
5) `docs/roadmaps/<RUN_ID>-40-phases.md`  
   - 40-phase development plan for your system, derived from the comparative analysis  
6) `core/CHANGELOG.md` entry  
   - what was promoted, why, and acceptance evidence  

---

## 3) Repo set: starting list (configurable)

**Initial “agentic” repo candidates (examples):**
- All-Hands-AI/OpenHands
- microsoft/agent-framework
- crewAIInc/crewAI
- langchain-ai/langgraph
- Significant-Gravitas/AutoGPT
- microsoft/autogen
- openinterpreter/open-interpreter
- camel-ai/camel
- agent0ai/agent-zero
- Pythagora-io/gpt-pilot

Your code should treat this as a **seed list** and then enforce the star/recency filters programmatically (GitHub API/`gh`).

---

## 4) Data model: Feature Taxonomy + Evidence objects (make it machine-friendly)

### 4.1 Feature Taxonomy (YAML skeleton)
Store this at: `core/features/taxonomy.yaml`

```yaml
version: 1
domains:
  orchestration:
    - id: orchestration_model
      type: enum
      values: [graph, role_task, loop_planner, hybrid, unknown]
    - id: state_checkpointing
      type: enum
      values: [none, in_memory, durable, durable_with_replay]
    - id: human_in_loop
      type: enum
      values: [none, approvals, interrupts_resumable, full_ui]
  tooling:
    - id: tool_protocol
      type: enum
      values: [mcp, custom, openapi, plugin_system, mixed]
    - id: sandboxing
      type: enum
      values: [none, partial, container, vm, unknown]
    - id: network_policy
      type: enum
      values: [off_by_default, allowlist, unrestricted, unknown]
  sd_lifecycle:
    - id: diff_first
      type: enum
      values: [no, partial, yes]
    - id: verification_gating
      type: enum
      values: [none, basic, ci_integrated, policy_driven]
  observability:
    - id: run_logs
      type: enum
      values: [none, basic, structured_events, traces]
    - id: eval_harness
      type: enum
      values: [none, ad_hoc, benchmark_suite, continuous]
  extensibility:
    - id: plugin_extensibility
      type: enum
      values: [none, limited, strong]
    - id: language_support
      type: set
      values: [python, typescript, dotnet, go, java, rust, other]
```

### 4.2 Evidence object (JSON Lines recommended)
Store per-repo evidence as JSONL for easy diffing:
- `collected/github/<RUN_ID>/evidence/<org__repo>.jsonl`

```json
{"feature_id":"tool_protocol","value":"mcp","evidence":[{"path":"README.md","lines":"120-165","quote":"<<=25 words excerpt>>","confidence":0.8}],"sha":"abc123","collectedAt":"2026-01-16T18:42:00Z"}
```

**Rule:** every feature value must have at least one evidence pointer OR be explicitly tagged as `unknown` with rationale.

---

## 5) Pipeline: end-to-end procedure (what your code should do)

### Step 0 — Create a run envelope
- Generate `RUN_ID = YYYY-MM-DD__HHMM__shortsha`
- Create working directories:
  - `tmp/<RUN_ID>/clones/`
  - `collected/github/<RUN_ID>/...`

### Step 1 — Resolve repo candidates and enforce constraints
- Query GitHub for each candidate:
  - stars ≥ 5k
  - pushed within last 7 days
  - optional topic keyword match
- Output a `selected_repos.json` with:
  - `org/repo`, URL, stars, pushed_at, default_branch, license

**Stop condition:** If fewer than 5 repos meet criteria, widen `updated_within_days` to 14 for this run, but log the deviation in DECISIONS.

### Step 2 — Temporary pull (safe shallow clone)
For each selected repo:
- `git clone --depth 1 --single-branch <url> tmp/<RUN_ID>/clones/<org__repo>`
- capture:
  - HEAD SHA
  - `git log -1 --format=fuller`
  - repo size (optional)
- copy only *metadata* + selected file excerpts into `collected/`:
  - `README*`, `docs/`, `pyproject.toml`, `package.json`, `requirements*.txt`, `Dockerfile*`, `.github/workflows/*`, `Makefile`, `LICENSE`
- delete clone after extraction unless you explicitly keep it for deeper static analysis.

### Step 3 — Static indexing (no execution)
- Create a file inventory with hashes:
  - language breakdown (`.py`, `.ts`, `.cs`, etc.)
  - key directories (`agent/`, `orchestrator/`, `tools/`, `prompts/`, `workflow/`, `eval/`, `traces/`)
- Extract structural signals:
  - presence of MCP servers/clients
  - presence of graph/workflow runtime
  - evidence of approval gates / interrupts
  - logging/tracing/event streaming formats
  - CI pipelines and test harnesses

### Step 4 — Multi-agent extraction (parallel)
Orchestrator assigns **one repo per Extraction Worker** (or more, depending on throughput). Each worker produces:
- `repo_dossier_draft.md`
- `evidence.jsonl` with taxonomy-aligned feature values
- a “Top 20 borrowable ideas” list (must cite file paths)

### Step 5 — Normalization + de-duplication (aggregation agent)
Aggregation agent:
- validates evidence completeness per feature
- resolves conflicting interpretations (worker disagreements)
- normalizes values into the canonical taxonomy
- emits:
  - `matrix.csv` + `matrix.md`
  - `disagreements.md` (if needed)

### Step 6 — Reviewer gate (risk triggers)
Reviewer agent checks:
- evidence pointers are present and within quote limits
- any “security posture” claims are backed by config/code pointers
- no license violations (no bulk copying)
- matrix values are consistent with taxonomy

### Step 7 — Roadmap synthesis (40 phases)
Director + Planner agents:
- derive your system backlog from:
  - the feature matrix (what’s table stakes)
  - AGENT 33 principles (what must be model-agnostic and auditable)
  - your current repo baseline
- produce `40-phases.md` with:
  - phase goals
  - acceptance criteria
  - deliverables
  - risks and review gates

### Step 8 — Promotion discipline
Only promote reusable and proven patterns into `core/`:
- template schemas, contracts, checklists, policy packs
- NEVER promote repo-specific hacks
- log promotions in `core/CHANGELOG.md`

---

## 6) Multi-agent work design (how to parallelize efficiently)

### Roles (AGENT 33 aligned)
- **Director:** sets priorities, ensures scope discipline, approves deviations
- **Orchestrator:** partitions work, assigns repos to agents, enforces evidence rules
- **Worker (Extractor):** analyzes assigned repo and emits taxonomy-aligned evidence + dossier
- **Worker (Implementer):** maintains ingestion scripts + parsers + matrix generator
- **QA:** validates schema, matrix completeness, and reproducibility
- **Reviewer:** risk triggers, security posture, license compliance, minimal diffs
- **Documentation:** final polish + cross-links for AGENT 33 consumption

### Recommended parallel topology
- 1 Orchestrator
- 6–10 Extractor Workers (1 repo each)
- 1 Aggregator (normalization + matrix)
- 1 Reviewer
- 1 QA
- 1 Director/Planner (roadmap synthesis)

---

## 7) Agent “task narratives” (copy/paste to drive the system)

These are **prompt-like procedural narratives** to hand to your internal agents. Use your standard handoff headers.

### 7.1 Orchestrator narrative
**PLAN:** enforce repo selection constraints; create run envelope; assign one repo per extractor; define acceptance checks.  
**TASKS:** (1) select repos via API; (2) clone+snapshot; (3) assign extraction; (4) aggregate; (5) reviewer+QA; (6) generate roadmap.  
**STATUS:** update after each repo completes.  
**DECISIONS:** log any constraint relaxation (e.g., updated_within_days widened).  
**PRIORITIES:** completeness > speed; evidence > speculation; minimal diffs.

### 7.2 Extraction Worker narrative (per repo)
You own **exactly one repo**. Do not generalize; cite evidence.
Deliver:
- `core/repo-dossiers/<org__repo>.md` draft
- `collected/.../<org__repo>.jsonl` evidence aligned to taxonomy
- a list of “borrowable patterns” with file paths

Your dossier must cover:
1) architecture overview (modules, runtime, state)  
2) orchestration model (graph/roles/loop)  
3) tool integration (MCP, plugin, OpenAPI, etc.)  
4) safety controls (sandboxing, approvals, network policy)  
5) observability (logs/traces)  
6) eval harness (benchmarks, tests)  
7) extensibility points (plugins, tool registry)  
8) operator UX (CLI/UI)  
9) “steal list”: patterns to promote into AGENT 33

### 7.3 Aggregator narrative
Merge all evidence, normalize values, produce:
- `matrix.csv` + `matrix.md`
- “coverage report” (missing features/evidence)
- “disagreement report” (if conflicts)

### 7.4 Reviewer narrative
Gate on:
- evidence completeness (no uncited claims)
- license compliance
- security statements backed by config pointers
- matrix taxonomy correctness

### 7.5 Planner narrative (40 phases)
Use the matrix to propose:
- foundational contracts + policies
- ingestion automation
- evidence ledger
- tool governance and approvals
- stateful orchestration runtime
- CI integration and evaluation suite
- promotion workflow across repos

---

## 8) The Features Matrix: how to structure it so it stays useful

### 8.1 Matrix columns (recommended)
- Repo
- Stars
- Last push
- License
- Orchestration model (enum)
- State/checkpointing (enum)
- Human-in-loop (enum)
- Tool protocol (enum)
- Sandboxing (enum)
- Network policy (enum)
- Diff-first posture (enum)
- Verification gating (enum)
- Run logs (enum)
- Eval harness (enum)
- Plugin extensibility (enum)
- Languages (set)
- Notes (short)
- Evidence links (paths into `collected/`)

### 8.2 Normalization rules
- If unclear, use `unknown` and explain why.
- Prefer primary pointers:
  - code/config > README claims
- For every `yes`, cite at least one file pointer.

---

## 9) Roadmap: 40 phases for building your system (high-confidence sequence)

This roadmap is intentionally **procedural** and **evidence-driven**—each phase produces verifiable artifacts you can sync to your other repos.

### Wave 1 — Governance, taxonomy, and run envelope (Phases 01–08)
01) **Create Feature Taxonomy v1** (`core/features/taxonomy.yaml`) + schema tests.  
02) **Define Evidence JSONL spec** (`core/contracts/evidence.schema.json`).  
03) **Define Run Ledger spec** (`core/contracts/run-log.schema.json`).  
04) **Create RepoSet config format** (`core/contracts/repo-set.schema.json`).  
05) **Implement Run Envelope generator** (RUN_ID, folders, manifest stubs).  
06) **Implement immutable ingestion policy** (raw snapshots stay in `collected/`).  
07) **Add license-handling rules** (what may be stored, quote limits, attribution).  
08) **Add risk triggers for external intake** (network, secrets, untrusted code).

### Wave 2 — Intake + static indexing (Phases 09–16)
09) **GitHub selection module** (stars/recency/topics; emits `selected_repos.json`).  
10) **Safe shallow clone manager** (temp workspace, cleanup, SHA capture).  
11) **Metadata snapshotter** (license, readme, workflows, dependency manifests).  
12) **Static index builder** (file inventory, language stats, directory signals).  
13) **Config signal extractor** (CI steps, lint/test commands, tool manifests).  
14) **Security signal extractor** (network use, secrets patterns, sandbox hints).  
15) **Docs signal extractor** (operator manuals, architecture docs).  
16) **Evidence packager** (consistent file pointers, excerpt rules).

### Wave 3 — Multi-agent extraction and normalization (Phases 17–24)
17) **Extractor agent template v1** (per-repo dossier + evidence JSONL).  
18) **Aggregator agent template v1** (merge + normalize + coverage report).  
19) **Disagreement resolution protocol** (tie-break rules + reviewer gate).  
20) **Matrix generator v1** (CSV + Markdown + evidence links).  
21) **Matrix QA checks** (coverage thresholds, schema validation, link checks).  
22) **Dossier generator template v1** (standard sections, cross-links).  
23) **Borrowable-patterns list format** (promotability criteria).  
24) **Promotion workflow integration** (auto-open PR stubs + changelog notes).

### Wave 4 — Orchestration core primitives (Phases 25–32)
25) **Tool manifest contract** (side-effect classification).  
26) **Approval policy engine** (tools requiring approval; risk-trigger mapping).  
27) **Autonomy budget contract** (scope/allowlists/stop conditions).  
28) **State model contract** (state schema + checkpointing interface).  
29) **Event stream contract** (`run.jsonl`, trace hooks, structured logs).  
30) **Human-in-loop primitives** (interrupt/resume, escalation paths).  
31) **Diff-first PR contract** (patch-size rules, file allowlists).  
32) **Evidence-first verification gates** (tests/lints required per task).

### Wave 5 — Operator experience + CI integration (Phases 33–38)
33) **Operator manual v1** (how to run scans, interpret outputs, debug).  
34) **CLI runner v1** (one command: select → clone → extract → matrix → dossiers).  
35) **CI workflow for matrix refresh** (scheduled run + artifact publishing).  
36) **Local cache and incremental runs** (avoid re-cloning when unchanged).  
37) **Regression tracking** (diff matrix over time; highlight changes).  
38) **Eval harness for your agent workflows** (golden tasks + success metrics).

### Wave 6 — Scaling and continuous improvement (Phases 39–40)
39) **Repo expansion strategy** (topic search + curated allowlist; provenance signals).  
40) **Continuous refinement loop** (monthly ingest → dedup → promote → measure).

**Acceptance criteria for every phase:** must produce an artifact in `core/` or `docs/` plus evidence in `collected/`, and must pass schema/validation checks.

---

## 10) Implementation guidance (what your code should actually enforce)

### 10.1 Hard gates (fail the run)
- missing SHAs / timestamps for selected repos
- matrix contains uncited “yes” claims
- evidence JSONL fails schema
- repos cloned outside temp workspace
- outputs not written to the run envelope

### 10.2 Soft gates (warn + log)
- fewer than N repos meet recency threshold
- ambiguous feature values (unknowns above threshold)
- repo content too large (partial snapshot required)

---

## 11) Minimal directory layout recommendation for this subsystem

```
collected/
  github/
    <RUN_ID>/
      selected_repos.json
      repos/
        <org__repo>/
          meta.json
          files/ (whitelisted docs/configs)
      evidence/
        <org__repo>.jsonl
        <org__repo>.md

core/
  features/
    taxonomy.yaml
    matrix/
      <RUN_ID>.md
      <RUN_ID>.csv
  repo-dossiers/
    <org__repo>.md
  contracts/
    evidence.schema.json
    run-log.schema.json
    repo-set.schema.json
  policies/
    approval-policy.md
    autonomy-budget.md

docs/
  roadmaps/
    <RUN_ID>-40-phases.md
  sessions/
    <RUN_ID>/
      plan.md
      status.md
      decisions.md
```

---

## 12) What “extensive per-repo markdown” must contain (dossier template)

Each `core/repo-dossiers/<org__repo>.md` must include:

1) **Repo facts** (stars, last push, license, SHA analyzed)  
2) **Architecture** (modules, runtime loop, state)  
3) **Orchestration model** (graph/roles/loop; cite code/docs)  
4) **Tooling** (MCP/plugins/OpenAPI/custom; cite manifest/adapters)  
5) **Human-in-loop** (approvals, interrupts, UI; cite)  
6) **Safety posture** (sandboxing, network policy, secrets handling; cite)  
7) **Observability** (structured logs/traces; cite)  
8) **Evaluation** (tests/benchmarks; cite)  
9) **Operator UX** (CLI/UI; setup steps; cite docs)  
10) **Borrowable patterns** (top 20 ideas) + promotability notes for AGENT 33  
11) **Gaps and risks** (what’s missing; potential failure modes)  

---

## 13) Final note: how to use this narrative in AGENT 33

- Store this file as a **canonical operator narrative** in `core/orchestrator/` (or `core/research/` if you prefer).
- Your actual code should implement the pipeline steps and enforce the hard gates.
- Your agents should follow the role narratives and produce artifacts exactly where the run envelope specifies.

*End of narrative.*
