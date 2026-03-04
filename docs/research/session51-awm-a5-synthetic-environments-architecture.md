# Session 51: A5 Synthetic Environment Generation Architecture

Date: 2026-03-04
Status: planned for implementation in this branch
Related roadmap item: AWM Tier 2 A5

## Goal

Add a first production-safe implementation of A5 synthetic environment generation that:

- adapts AWM's synthetic environment idea to AGENT-33's multi-agent workflow model
- stays deterministic and testable without introducing LLM code generation into the main runtime
- produces environment bundles that future evaluation and improvement loops can consume
- documents the contract clearly enough that later A6 comparative scoring and Phase 31 persistence work can build on it

## Primary sources

- Internal analysis: `docs/research/agent-world-model-analysis.md`
- Upstream paper: https://arxiv.org/html/2602.10090
- Upstream repository: https://github.com/Snowflake-Labs/agent-world-model

The upstream AWM system is a 5-stage synthetic pipeline that generates scenarios, tasks, databases, environment code, and verifiers. AGENT-33 should not copy that pipeline 1:1 because our architecture is multi-agent, governance-heavy, and workflow-native rather than single-agent research-only.

## Constraints

- No benchmark-gaming implementation.
- No arbitrary code generation or dynamic server synthesis in the main app.
- No new unsafe execution path.
- Must work with existing workflow definitions and tool definitions already present in the repo.
- Must be deterministic under test.

## First-cut scope

The initial A5 implementation will generate synthetic environment bundles from AGENT-33 workflow definitions and tool definitions.

Each generated bundle will contain:

- workflow metadata
- inferred tool contracts
- a SQLite-compatible initial state contract expressed as SQL
- completion SQL representing the desired end state
- deterministic verifier queries
- synthetic task prompts that describe the environment objective

This gives us DB-backed, replayable synthetic environments without requiring the full AWM-style code-generation pipeline.

## Adapted pipeline

### Stage 1: Workflow seed discovery

Source existing workflow templates from `engine/workflow-definitions/` and turn them into synthetic environment seeds.

### Stage 2: Task synthesis

Generate deterministic task prompts from workflow metadata, steps, tags, and the current progress cursor for each variant.

### Stage 3: State synthesis

Create SQLite-compatible tables that represent workflow context, step state, and expected artifacts. Seed them with a partial-progress starting point.

### Stage 4: Environment bundle assembly

Package the workflow definition, tool contracts, state SQL, and task prompts into a single bundle object stored by a dedicated service.

### Stage 5: Verification synthesis

Generate SQL assertions plus completion SQL, and validate the bundle by applying both against an in-memory SQLite database.

## Why this shape is correct

- It preserves the AWM insight that synthetic environments should be stateful and verifiable.
- It uses AGENT-33's existing workflow and tool abstractions instead of inventing a parallel environment language.
- It is safe to expose through the API because the output is data, not executable code.
- It creates a clean handoff point for future work:
  - A6 can compare agents on shared synthetic bundles.
  - Phase 31 can persist generated bundles and outcomes.
  - later work can replace deterministic task synthesis with optional LLM-assisted expansion if needed.

## API surface

Add a new router under `/v1/evaluation/synthetic-environments` with:

- `GET /workflows`
  - list discovered workflow templates and inferred tool coverage
- `POST /bundles`
  - generate one or more synthetic environment variants
- `GET /bundles/{bundle_id}`
  - retrieve a previously generated bundle

The service should retain a bounded in-memory history of generated bundles.

## Data model

Planned models:

- `SyntheticWorkflowCatalogEntry`
- `SyntheticToolContract`
- `SyntheticTaskPrompt`
- `SyntheticVerificationQuery`
- `SyntheticEnvironment`
- `SyntheticEnvironmentBundle`

## Test plan

- service tests for workflow discovery and tool inference
- generation tests asserting deterministic bundle structure
- SQLite validation tests asserting initial-state and completion-state SQL are internally consistent
- API tests for workflow listing, bundle generation, and bundle retrieval

## Non-goals for this PR

- no live environment server generation
- no LLM-generated code or SQL
- no training loop integration
- no persistence layer for bundles
- no benchmark execution against the generated bundles yet

## Follow-up path

1. Persist generated bundles and evaluation outcomes in Phase 31 storage.
2. Feed synthetic bundle outputs into comparative evaluation populations.
3. Add optional LLM-assisted scenario expansion behind explicit flags once the deterministic base is stable.
