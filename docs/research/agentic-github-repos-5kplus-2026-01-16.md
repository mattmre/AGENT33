# Agentic GitHub Repos (≥5k stars) — landscape scan (as of 2026-01-16)

This note complements AGENT 33’s model-agnostic orchestration core by cataloging high-signal, widely adopted OSS repos that implement *agentic* patterns (multi-agent orchestration, tool-use, approval flows, run logs, stateful graphs, and “coding agents”).

**Selection intent (your ask):**
- ≥ 5k GitHub stars
- Actively updated *within the last week* (relative to 2026-01-16) **where verification was available**
- Focused on agentic workflows / orchestration / autonomous coding

> Note: For a few repos, GitHub returned “Internal Error” when attempting to load the commit history endpoint during this scan; those repos are included as “high-signal but recency not verifiable in snapshot.”

---

## A. Verified as updated within the last week (public commit/release evidence)

### 1) OpenHands — All-Hands-AI/OpenHands
- Stars: ~66.7k
- Evidence of recent activity: release v0.49.1 dated **2026-01-16**
- What it is: agentic software engineering platform (task execution, repo operations, tool use, run tracking)
- Why it matters to AGENT 33: strong examples of “end-to-end run” lifecycle + environment/tool boundary management + audit trail primitives
- Repo: https://github.com/All-Hands-AI/OpenHands

### 2) Microsoft Agent Framework — microsoft/agent-framework
- Stars: ~6.6k
- Evidence of recent activity: commits dated **2026-01-16** and **2026-01-15**
- What it is: multi-language (Python + .NET) agent + workflow framework with “graph-based orchestration” positioning
- Why it matters to AGENT 33: clean separation of *agent API* vs *workflow runtime*, plus explicit patterns for approval flows and tool support
- Repo: https://github.com/microsoft/agent-framework

### 3) CrewAI — crewAIInc/crewAI
- Stars: ~34.5k
- Evidence of recent activity: commits dated **2026-01-15**
- What it is: role-based multi-agent orchestration (“crews”, tasks, tools) with a strong emphasis on practical workflows
- Why it matters to AGENT 33: usable “procedural intuition” around role decomposition, task contracts, and tool gating
- Repo: https://github.com/crewAIInc/crewAI

### 4) LangGraph — langchain-ai/langgraph
- Stars: ~13.9k
- Evidence of recent activity: commits dated **2026-01-13**
- What it is: stateful graph runtime for agentic workflows (graphs/state machines, checkpointing, streaming, human-in-the-loop)
- Why it matters to AGENT 33: maps directly to orchestration primitives (state, transitions, resumability, event streams)
- Repo: https://github.com/langchain-ai/langgraph

---

## B. High-signal agentic repos that meet the star threshold, but do not meet / cannot be verified for the “updated in last week” constraint in this snapshot

These are still materially useful for “what good looks like” in agentic architecture, data models, and operator experience. Treat them as **reference designs** and/or “watchlist repos” to track.

### 5) AutoGPT — Significant-Gravitas/AutoGPT
- Stars: ~176k
- Snapshot note: last-week update could not be verified from the retrieved commit-history excerpts in this scan
- What it is: one of the most influential “autonomous agent platform” repos; many downstream patterns (plugin/tool abstractions, run loops) trace here
- Repo: https://github.com/Significant-Gravitas/AutoGPT

### 6) Agent Zero — agent0ai/agent-zero
- Stars: ~13.6k
- Snapshot note: GitHub returned **Internal Error** when attempting to load the commits endpoint during this scan
- What it is: agent framework oriented toward building agent behaviors with tools and workflows
- Repo: https://github.com/agent0ai/agent-zero

### 7) CAMEL — camel-ai/camel
- Stars: ~15.5k
- Snapshot note: GitHub returned **Internal Error** when attempting to load the commits endpoint during this scan
- What it is: multi-agent research/engineering framework (agent scaling, agent interactions)
- Repo: https://github.com/camel-ai/camel

### 8) AutoGen — microsoft/autogen
- Stars: ~53.4k
- Snapshot note: most recent commits visible in retrieved commit page were dated **2025-10-04**
- What it is: a major Microsoft multi-agent framework; still a meaningful architecture reference even when less active
- Repo: https://github.com/microsoft/autogen

### 9) Open Interpreter — openinterpreter/open-interpreter
- Stars: ~59.4k
- Snapshot note: most recent commits visible in retrieved commit page were dated **2025-12-05**
- What it is: “agent that can run code / operate on your system” concept; relevant to tool boundary and operator safety controls
- Repo: https://github.com/openinterpreter/open-interpreter

### 10) GPT Pilot — Pythagora-io/gpt-pilot
- Stars: ~33.3k
- Snapshot note: most recent commit visible in retrieved commit page was dated **2025-03-04**; repo page states it’s no longer maintained
- What it is: autonomous coding agent approach; useful for UX/workflow ideas even if stale
- Repo: https://github.com/Pythagora-io/gpt-pilot

---

## Cross-cutting engineering patterns worth harvesting into AGENT 33

### 1) “Run ledger” as a first-class artifact
Common implicit standard:
- **Run ID** (stable identifier)
- **Inputs** (prompt + config + tool allowlist)
- **Events** (tool calls, intermediate plans, approvals)
- **Evidence** (commands, test results, artifacts)
- **Outcome** (status + diff summary + follow-ups)

**AGENT 33 suggestion:** codify a canonical `RUN_LOG.md` schema and a machine-readable `run.jsonl` stream spec that all repos can adopt.

### 2) Statefulness and resumability (graphs / checkpoints)
LangGraph and Agent Framework push toward:
- checkpointing state
- explicit transitions
- streaming events and “human-in-the-loop” pause points

**AGENT 33 suggestion:** a *model-agnostic state machine contract*:
- `State` (schema + persistence rules)
- `Step` (preconditions/postconditions)
- `Interrupt` (approval gates)
- `Replay` (deterministic re-run where possible)

### 3) Tool governance (approval flows + allowlists)
Across modern agent frameworks:
- pre-declared tool manifests (name, args schema, side-effect category)
- “requires approval” tool classes (filesystem write, network, secrets, deployments)
- structured tool results (stdout/stderr, exit code, artifact pointers)

**AGENT 33 suggestion:** a single canonical `tools/manifest.json` + `approval-policy.md` used across repos.

### 4) “Role decomposition” and task contracts
CrewAI-style patterns show pragmatic value:
- narrow roles
- strict acceptance criteria
- minimal diffs
- reviewer gates for high-risk actions

**AGENT 33 suggestion:** extend your existing handoff protocol (PLAN/TASKS/STATUS/DECISIONS/PRIORITIES) with a mandatory **Acceptance Criteria** and **Evidence Plan** section per task.

### 5) Developer ergonomics
The best repos emphasize:
- fast local loop (devcontainers, scripts, smoke tests)
- CI that validates agent outputs (format, lint, tests)
- “operator manual” for debugging runs

**AGENT 33 suggestion:** add a repo-agnostic `operator/` bundle:
- `OPERATOR_MANUAL.md`
- `DEBUG_PLAYBOOK.md`
- `EVIDENCE_CAPTURE.md`
- `RISK_TRIGGERS.md` (you already have the concept; make it a reusable template)

---

## “Direct lift” items to consider for `core/`

1. `core/contracts/run-log.schema.json` — JSON schema for run metadata/events  
2. `core/contracts/tool-manifest.schema.json` — tool definitions + side-effect classification  
3. `core/policies/approval-policy.md` — gating policy keyed by tool side-effects  
4. `core/policies/review-gates.md` — mandatory reviewer triggers (security/schema/api/ci/large refactors)  
5. `core/patterns/stateful-orchestration.md` — graph/state machine patterns + examples  
6. `core/patterns/human-in-the-loop.md` — interrupt/resume, confirmations, escalation paths  
7. `core/templates/RUN_LOG.md` + `core/templates/PR_CHECKLIST.md` — minimal diff, evidence-first checklist  

---

## Appendix: quick compare grid (high level)

- **Workflow runtime emphasis:** LangGraph, Agent Framework  
- **Multi-agent “roles and tasks” emphasis:** CrewAI, CAMEL  
- **Autonomous coding / repo manipulation emphasis:** OpenHands, GPT Pilot, AutoGPT, Agent Zero  
- **Tool boundary / local execution emphasis:** Open Interpreter, OpenHands  
