# Repo Dossier: HKUDS/AI-Researcher
**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

AI-Researcher is a fully autonomous scientific research system from Hong Kong University's Data Science Lab, accepted as a NeurIPS 2025 Spotlight paper, that orchestrates end-to-end research workflows from literature review through implementation to manuscript generation. The system employs a sophisticated multi-agent architecture where specialized agents (Knowledge Acquisition, Resource Analyst with Paper/Code/Plan sub-agents, Code Agent, Advisor Agent with Judge/Review/Analysis sub-agents, Documentation Agent, and Idea Generator) collaborate through structured sequential pipelines across three major stages: literature review and idea generation, algorithm design/implementation/validation, and automated scientific documentation. Operating within Docker containerized environments for security and reproducibility, the system implements iterative refinement cycles modeling academic mentorship where implementations undergo multiple review-feedback-improvement loops, achieving 93.8% completion rates and 2.65/5.0 correctness scores on the Scientist-Bench benchmark spanning Computer Vision, NLP, Data Mining, and Information Retrieval domains.

## 2) Core orchestration model

**Sequential Pipeline with Three-Stage Progression:**

AI-Researcher implements a **linear stage-based architecture** rather than dynamic DAG orchestration, with agents progressing through fixed phases where one agent's output becomes the next agent's input:

1. **Stage 1 - Literature Review & Ideation**: Knowledge Acquisition Agent retrieves papers/code from academic databases → Resource Filter evaluates impact via citation metrics → Idea Generator formulates novel directions through systematic gap analysis
2. **Stage 2 - Implementation & Validation**: Design phase (Plan Agent creates roadmaps) → Implementation (Code Agent translates to executable code) → Validation (Advisor Agent evaluates via specialized tools) → Refinement (iterative improvement cycles)
3. **Stage 3 - Documentation**: Writer Agent synthesizes artifacts into publication-ready manuscripts

**Information Flow Pattern:**
The Resource Analyst functions as a "critical bridge between abstract concepts and their concrete implementations," receiving inputs from upstream agents and passing structured outputs downstream. This is fundamentally a **sequential handoff model** with no parallel execution or dynamic routing—each stage must complete before the next begins.

**Iterative Refinement Embedded in Stage 2:**
Within the implementation stage, the system employs a **cyclical mentor-student paradigm**: Code Agent generates prototype → Advisor Agent reviews with detailed feedback → Code Agent incorporates modifications → process repeats until success criteria met or deemed unfeasible. The refinement loop is contained within Stage 2 and does not affect the overall sequential progression.

**Key Limitation**: The orchestration is **deterministic and pre-scripted**—no LLM-driven routing, no agent-to-agent negotiation, no dynamic workflow adaptation. Compare to Swarm's conversational routing or n8n's conditional branching; AI-Researcher has fixed pipelines suitable for repeatable research tasks but inflexible for exploratory scenarios.

## 3) Tooling and execution

**Execution Environment:**
- **Docker containerization**: All operations execute within isolated containers providing "robust security boundaries that prevent unauthorized system modifications" while enabling "dynamic package management where agents can autonomously install additional dependencies"
- **Minimal manual setup**: Works out-of-box with basic `.env` configuration (LLM API keys, model selection, research category)
- **GPU allocation**: Configurable via Docker environment variables for compute-intensive tasks

**LLM Integration (LiteLLM-based):**
- Multi-provider support: Claude, OpenAI, Deepseek, Gemini, and 100+ models via OpenRouter API or GitHub AI tokens
- Unified OpenAI-compatible interface eliminates provider-specific code
- Configuration stored in `.env` with model selection via `LITELLM_MODEL` variable
- Temperature set to 1.0 for evaluation, configurable for generation tasks

**Resource Analyst Tooling (Core Innovation):**
The Resource Analyst employs specialized sub-agents with distinct capabilities:
- **Paper Analyst**: RAG-based extraction of mathematical formulations from LaTeX files—systematically parses downloaded papers to identify atomic concepts and their formal expressions
- **Code Analyst**: Repository analysis to locate implementations corresponding to mathematical formulations—identifies critical reference files and dependencies
- **Concept Decomposition**: Breaks research objectives "into atomic academic concepts—fundamental, indivisible research elements" with bidirectional mappings between theory (math) and practice (code), "dramatically reducing hallucination risks"
- **Plan Agent**: Transforms analysis results into "comprehensive implementation roadmap addressing training procedures, testing methodologies, and dataset requirements"

**Code Agent Capabilities:**
- Generates "structured implementations with comprehensive file system and execution capabilities"
- "Enforcing strict code independence principles while ensuring faithful translation of academic concepts into working code"
- Prototype testing on minimal data (1-2 epochs) before full-scale experiments
- Progressive experimental cycles: baseline feasibility → review incorporation → full deployment → classification as unfeasible after persistent failures

**Advisor Agent (Validation Toolkit):**
- "Specialized navigation tools and visualizations" for result examination
- Generates "detailed assessment reports with specific, actionable modification recommendations"
- Conducts "supplementary investigations spanning implementation refinements, validation studies, visualizations, and comparative analyses aligned with established research standards"
- Judge Agent: Assesses implementation quality on 5-point scale
- Code Review Agent: Validates implementation fidelity to research concepts
- Experiment Analysis Agent: Evaluates experimental results

**Package Management:**
- **uv package manager** (Astral, Rust-based): Replaces conda/pip for 10-100x faster dependency resolution
- Installation: `curl -LsSf https://astral.sh/uv/install.sh | sh && uv venv --python 3.11 && uv pip install -e .`
- Docker image: `docker pull tjbtech1/airesearcher:v1`
- Multi-stage Docker builds separate dependency installation from application code for caching efficiency

**Web Interface:**
- Gradio-based GUI via `python web_ai_researcher.py`
- Two-level input system:
  - Level 1 (Detailed Idea): `python run_infer_plan.py --instance_path ../benchmark/final/${category}/${instance_id}.json`
  - Level 2 (Papers-Only Ideation): `python run_infer_idea.py --instance_path ../benchmark/final/${category}/${instance_id}.json`
- Paper generation: `python writing.py --research_field ${research_field} --instance_id ${instance_id}`

**Notable Tool Gaps vs. AGENT-33:**
- No built-in web scraping (relies on pre-downloaded papers/code)
- No file operations toolkit beyond code generation (no FileOpsTool equivalent)
- No browser automation (headless or otherwise)
- No shell/terminal access for general command execution
- Tool suite is **domain-specific** (research-only) rather than general-purpose

## 4) Observability and evaluation

**Two-Stage Evaluation Framework (Scientist-Bench):**

**Stage 1 - Technical Execution Validation:**
- **Metric**: Completion ratio (proportion of required functionality successfully implemented)
- **Mechanism**: "Specialized code review agent to verify whether the implementation code faithfully realizes the AI-conducted research innovations"
- **Criteria**: Algorithm correctness, computational efficiency, constraint adherence
- **Results**: 93.8% completeness with Claude-series models; failures only in "complex technical challenges such as tensor dimension conflicts and datatype mismatches"

**Stage 2 - Scientific Contribution Evaluation:**
- **Metric**: Comparative rating r ∈ {-3, -2, -1, 0, 1, 2, 3} via formula `r,J = PaperReview(RandomSwap(p,y);g)` comparing AI paper against ground truth
- **Mechanism**: Calibrated review agent compares AI-generated vs. human expert papers
- **Debiasing**: Random presentation order swapping, multiple independent evaluations using diverse LLMs (GPT, Claude, Gemini), temperature=1.0
- **Hierarchical Metrics**:
  - Novelty: Assessing innovation and uniqueness
  - Experimental Comprehensiveness: Evaluating design, execution, rigor
  - Theoretical Foundation: Verifying mathematical soundness
  - Result Analysis: Checking interpretation quality
  - Writing Quality: Assessing manuscript clarity
- **Results**: 2.65/5.0 average correctness score; "percentage of AI papers scoring ≥-1.0 representing research contributions that achieve at least near-human quality"

**Benchmark Coverage:**
- **Scientist-Bench**: "First comprehensive benchmark enabling standardized assessment across both guided innovation scenarios and open-ended exploration tasks"
- **Domains**: 4 major areas (CV, NLP, Data Mining, IR) with 22 benchmark papers
- **Ground Truth**: Human expert-written papers as reference standards
- **Open-Source**: "Complete access to processed datasets, data collection pipelines, and processing code"
- **Leaderboard**: Available at autoresearcher.github.io/leaderboard

**Observability Mechanisms:**
- **Agent reasoning logs**: Execution traces capture intermediate agent outputs
- **Execution logs**: Docker container logs track implementation progress
- **Experimental outcomes**: Performance metrics, visualizations, comparative analyses
- **Iterative refinement traces**: Advisor feedback cycles documented for each refinement iteration

**Key Limitation - No Runtime Observability:**
Unlike AGENT-33's structlog/tracing/lineage system, AI-Researcher appears to lack **real-time observability during execution**. The evaluation framework is **post-hoc** (runs after completion), not live monitoring. No evidence of:
- Structured logging with correlation IDs
- Distributed tracing across agent handoffs
- Metrics dashboards (latency, token consumption, etc.)
- Alerting on agent failures
- Replay/debugging capabilities beyond Docker logs

**Critical Gap**: Evaluation focuses on **output quality** (paper correctness, code completeness) but provides minimal insight into **process quality** (agent decision-making, bottleneck identification, failure analysis). For production deployment, teams would need to add observability infrastructure on top of the base system.

## 5) Extensibility

**LLM Provider Extensibility (Strong):**
- **LiteLLM integration**: Supports 100+ models via unified OpenAI-compatible interface
- **Zero-code provider switching**: Change `LITELLM_MODEL` environment variable to swap between Claude/GPT/Gemini/Deepseek without modifying agent code
- **Custom model endpoints**: Can point to local models, OpenRouter, or custom API gateways
- **Cost-aware routing**: LiteLLM's built-in load balancing, fallback mechanisms, and usage-based routing (though unclear if AI-Researcher uses these features)

**Agent Extensibility (Moderate-to-Weak):**
- **Modular agent design**: Separate classes for Knowledge Acquisition, Resource Analyst, Code Agent, Advisor, Documentation—could theoretically add new agents
- **Sub-agent pattern**: Resource Analyst contains Paper/Code/Plan sub-agents; Advisor contains Judge/Review/Analysis sub-agents—suggests composability
- **Limitation**: No evidence of **plugin system** or **agent registry**. Adding new agents likely requires modifying core orchestration code in `run_infer_*.py` scripts
- **Fixed pipeline**: Sequential stage progression is hardcoded—cannot easily inject new stages or reorder existing ones without refactoring

**Domain Extensibility (Weak):**
- System is **tightly coupled to scientific research workflows** (literature → idea → implementation → validation → paper)
- Benchmark is research-specific (CV/NLP/DM/IR domains)
- Tooling (Paper Analyst parsing LaTeX, Code Analyst analyzing repos) assumes academic context
- **No evidence of generalization** to other domains (e.g., marketing campaigns, legal research, product development)—would require significant rework

**Tool Extensibility (Unclear):**
- Code Agent can "autonomously install additional dependencies" via dynamic package management
- Advisor Agent uses "specialized navigation tools and visualizations" (not specified whether these are extensible)
- **No documentation** on adding custom tools (e.g., new data sources, external APIs, specialized analysis libraries)
- **Assumption**: Tool additions likely require agent prompt modifications rather than declarative tool definitions

**Configuration Extensibility (Moderate):**
- `.env` file controls Docker settings, LLM models, GPU allocation, research categories
- `instance_path` JSON files define benchmark tasks—could create custom task specifications
- **Limitation**: Configuration is shallow (environment variables only)—no evidence of complex policy engines, workflow DSLs, or behavior customization beyond model/task selection

**Deployment Extensibility (Strong):**
- **Docker-first architecture**: Containerization enables deployment to any Docker-compatible infrastructure (Kubernetes, AWS ECS, GCP Cloud Run)
- **Web GUI option**: Gradio interface provides user-friendly alternative to CLI
- **Benchmark decoupling**: Can use AI-Researcher as a library (import agents) or standalone service (REST API, though not documented)

**Comparison to AGENT-33's Extensibility:**
- **AGENT-33 advantages**: Agent registry auto-discovers JSON definitions, workflow actions are composable, tool governance system with allowlists, capability taxonomy, plugin architecture
- **AI-Researcher advantages**: LiteLLM provides better LLM provider abstraction than AGENT-33's ModelRouter, Docker containerization is more mature than AGENT-33's sandbox approach
- **Key gap**: AI-Researcher has no equivalent to AGENT-33's workflow DAG engine—cannot define custom multi-step processes declaratively

## 6) Notable practices worth adopting in AGENT-33

**1) Resource Analyst Pattern - Atomic Concept Decomposition with Bidirectional Mapping**
- **What**: Break complex tasks into "atomic, indivisible elements" with explicit mappings between abstract representation (mathematical formulas, requirements) and concrete implementation (code, configuration)
- **Why**: "Dramatically reducing hallucination risks" by forcing LLMs to establish verifiable correspondences rather than generating unconstrained outputs
- **AGENT-33 application**: In code execution (Phase 13), decompose user requests into atomic operations (read file → parse → transform → validate → write) with explicit contracts linking intent to implementation. In workflows, map each step's inputs/outputs to concrete data schemas. In memory ingestion, link observations to source artifacts bidirectionally.
- **Implementation**: Add `concept_decomposition` field to `AgentDefinition` prompts instructing agents to break down tasks and establish mappings; extend `ExecutionContract` to require bidirectional traceability between user intent and code actions.

**2) Iterative Refinement with Specialized Advisor Agents**
- **What**: Implement explicit mentor-student feedback loops where Advisor agents review work products and generate "detailed assessment reports with specific, actionable modification recommendations," triggering refinement cycles
- **Why**: "Progressive algorithm improvement through multiple refinement cycles" models proven academic collaboration patterns; catches errors early in prototype phase (1-2 epochs) before full-scale deployment
- **AGENT-33 application**: Add `AdvisorAgent` to agent definitions with capability to review code-worker outputs; implement workflow action `refinement_cycle` that loops until quality threshold met or max iterations exceeded; extend observability to track refinement provenance (which feedback led to which changes)
- **Implementation**: Create `advisor` agent definition with Judge/Review/Analysis sub-capabilities; add `refinement` workflow action in `actions/`; modify `CodeExecutor` to support iterative improvement mode with feedback incorporation

**3) Progressive Experimental Cycles (Prototype → Validate → Full-Scale)**
- **What**: Test implementations on minimal data first (1-2 epochs, small subsets), obtain Advisor approval, then advance to full experiments—classify as unfeasible only after multiple refinement failures
- **Why**: Reduces wasted compute on fundamentally flawed approaches; provides early signal for course correction; prevents "all-or-nothing" execution where failures are catastrophic
- **AGENT-33 application**: In code execution, run user code on synthetic/minimal inputs first, validate output structure, then execute on real data; in workflows, add `prototype_mode` flag that runs abbreviated versions of expensive steps before full execution; in training, test new policies on small rollout batches before production deployment
- **Implementation**: Extend `SandboxConfig` with `prototype_mode: bool` and `data_subset_size: int`; modify `CLIAdapter` to support dry-run/preview execution; add validation checkpoints to workflow engine

**4) Hierarchical Documentation Synthesis (Prevent Long-Form LLM Hallucinations)**
- **What**: Documentation Agent uses "multi-stage generation framework" that "decomposes the complex writing task into manageable components while preserving logical connections across sections and maintaining factual integrity"
- **Why**: "Overcomes LLM limitations by decomposing the complex writing task" to prevent "hallucinations and inconsistencies that typically plague LLM-generated long-form content"; ensures cross-document consistency
- **AGENT-33 application**: When generating session summaries, evaluation reports, or system documentation, implement hierarchical synthesis: (1) Extract facts from artifacts, (2) Build section-level narratives from facts, (3) Assemble sections with consistency checks, (4) Apply "one more step" verification pass with specialized checklists
- **Implementation**: Create `DocumentationAgent` with hierarchical prompt structure; add `verify_consistency` workflow action that cross-references sections for contradictions; extend `SessionSummarizer` to use staged generation instead of single-pass prompts

**5) Template-Guided Structure with Domain-Appropriate Schemas**
- **What**: Use "domain-appropriate templates that establish section hierarchies and logical flow" to constrain LLM outputs to expected formats while allowing content variation
- **Why**: Balances flexibility (LLM-generated content) with consistency (predictable structure); enables downstream parsing and validation; reduces prompt engineering burden
- **AGENT-33 application**: Define templates for common outputs (agent definitions, workflow step results, execution reports, evaluation summaries) with explicit section markers; validate outputs against templates before persisting to DB; use template schemas as few-shot examples in prompts
- **Implementation**: Add `templates/` directory with Jinja2 templates for each output type; extend `AgentRuntime._build_system_prompt()` to inject relevant templates; add schema validation to `WorkflowEngine.execute_action()`

**6) Debiased Multi-Evaluator Assessment (Random Order Swapping, Diverse LLMs)**
- **What**: Evaluation framework uses "random presentation order swapping, multiple independent evaluations using diverse LLMs (GPT, Claude, Gemini), temperature=1.0" to reduce bias
- **Why**: Single-evaluator assessments are subject to position bias, model-specific quirks, and consistency failures; ensembling across models and randomizing presentation produces more reliable ratings
- **AGENT-33 application**: In training system evaluation (`training/evaluation.py`), use multiple LLM judges with randomized rollout presentation order; in workflow validation, cross-validate results with different models; in agent capability assessment, aggregate scores from diverse evaluators
- **Implementation**: Extend `ModelRouter` to support multi-model ensembling; add `EvaluationOrchestrator` that runs same prompt across multiple providers and aggregates results; modify `PerformanceEvaluator` to use ensemble scoring

**7) Benchmark-Driven Development with Ground Truth References**
- **What**: Scientist-Bench provides "expert-written papers as ground truth references" with "complete access to processed datasets, data collection pipelines, and processing code" enabling standardized assessment
- **Why**: Without concrete benchmarks, improvements are anecdotal; ground truth enables regression detection and progress measurement; open-sourcing methodology fosters community contributions
- **AGENT-33 application**: Create benchmark suite for agent tasks (code generation, workflow orchestration, tool usage) with curated examples of correct outputs; use benchmarks in CI/CD to prevent regressions; publish benchmark construction methodology to enable domain-specific extensions
- **Implementation**: Add `benchmarks/` directory with JSON test cases (input, expected output, evaluation criteria); integrate benchmark evaluation into pytest suite; create `benchmark.py` CLI for running evaluations and publishing results

**8) Docker Containerization with Autonomous Dependency Management**
- **What**: "Docker containerized environment" provides "robust security boundaries" while "enabling dynamic package management where agents can autonomously install additional dependencies"
- **Why**: Reproducibility (same environment every run), security (isolation from host system), flexibility (agents adapt to task requirements by installing packages on-demand)
- **AGENT-33 application**: Phase 13 code execution already has `SandboxConfig`—extend it to use Docker instead of/in addition to CLI adapter; allow code to specify dependencies declaratively (e.g., `# requires: pandas>=2.0`), auto-install in container; capture installed packages in execution logs for reproducibility
- **Implementation**: Add `DockerAdapter` to `execution/adapters/`; parse dependency comments from code; use `uv pip install` within container for fast installation; extend `ExecutionResult` to include `installed_packages: List[str]`

**9) UV Package Manager for 10-100x Faster Dependency Resolution**
- **What**: Uses Astral's Rust-based `uv` package manager instead of pip/conda for dependency installation
- **Why**: Dramatically faster installs (especially in containerized environments with multi-stage builds), better caching, more reliable dependency resolution
- **AGENT-33 application**: Replace pip in Docker builds (`engine/Dockerfile`, CI/CD workflows) with uv; use `uv venv` for local development instead of venv/virtualenv; leverage uv's lock files for reproducible builds
- **Implementation**: Update `Dockerfile` to install uv via `curl -LsSf https://astral.sh/uv/install.sh | sh`; change `pip install -e .[dev]` to `uv pip install -e .[dev]`; add `uv.lock` to version control; update `CLAUDE.md` installation instructions

**10) Structured Feedback Generation with "Supplementary Investigations" Framework**
- **What**: Advisor Agent generates feedback that includes "implementation refinements, validation studies, visualizations, and comparative analyses aligned with established research standards"—not just "good/bad" ratings but actionable next steps
- **Why**: Generic feedback ("this doesn't work") is less effective than specific directives ("add input validation for edge case X, compare performance against baseline Y"); structured feedback categories ensure comprehensive reviews
- **AGENT-33 application**: In code execution validation, generate feedback reports with categories (correctness, performance, security, maintainability); in workflow step reviews, provide refinement suggestions, alternative approaches, and validation checkpoints; in agent output assessment, specify which constraints were violated and how to fix
- **Implementation**: Define `FeedbackReport` model with structured fields (categories, action_items, references); extend `CodeExecutor` to generate reports when validation fails; add `supplementary_investigations` workflow action that probes edge cases based on initial results

## 7) Risks / limitations to account for

**1) Hallucination Risks Despite Mitigation Efforts**
- **Evidence**: While the Resource Analyst's bidirectional mapping "dramatically reduces hallucination risks," the system still fails 6.2% of the time (93.8% completion rate) on "tensor dimension conflicts and datatype mismatches"—classic hallucination symptoms where LLMs generate syntactically valid but semantically incorrect code
- **Research context**: Studies show "over 60% of errors in model outputs are unverifiable," and "43% of hallucinated packages were repeated in 10 queries"—package hallucinations remain a critical threat
- **Risk for AGENT-33**: If adopting the Resource Analyst pattern, AGENT-33 must implement **validation layers beyond bidirectional mapping**: static analysis (type checking, linting), runtime assertions (schema validation, bounds checking), and human-in-the-loop review for critical operations
- **Mitigation**: Extend Phase 13 validation (IV-01 through IV-05) with hallucination-specific checks; add `hallucination_detection` module that flags common LLM fabrications (non-existent packages, impossible API calls, contradictory logic); require explicit user approval for package installations

**2) Sequential Pipeline Inflexibility**
- **Evidence**: AI-Researcher uses fixed three-stage progression (literature → implementation → documentation) with no dynamic routing or conditional branching
- **Limitation**: Cannot adapt workflow based on intermediate results (e.g., if literature review finds no novel gaps, cannot short-circuit to alternative research directions); cannot parallelize independent tasks (e.g., run multiple implementation strategies concurrently)
- **Risk for AGENT-33**: Adopting sequential mentor-student refinement loops risks **rigidity**—Phase 14's security hardening or Phase 15's review automation may require flexible workflows that adapt to context
- **Mitigation**: Implement iterative refinement **as a workflow action** (not a hardcoded pipeline stage) so it can be conditionally applied; use AGENT-33's existing DAG engine to enable parallel refinement branches; add `skip_if` and `retry_until` conditions to refinement loops

**3) No Real-Time Observability During Execution**
- **Evidence**: Evaluation is entirely post-hoc (runs after research cycle completes); no evidence of structured logging, distributed tracing, or live metrics dashboards
- **Limitation**: Cannot detect runaway processes mid-execution (e.g., LLM stuck in infinite refinement loop); cannot debug failures without re-running entire pipeline; no cost/latency visibility until job finishes
- **Risk for AGENT-33**: If adopting hierarchical documentation synthesis or progressive experimental cycles, **lack of runtime visibility** would make debugging failures extremely difficult
- **Mitigation**: AGENT-33 already has Phase 16 observability (structlog, tracing, lineage)—ensure any AI-Researcher patterns integrate with this infrastructure; add instrumentation to refinement loops, document synthesis stages, and experimental cycles; emit metrics at each pipeline transition

**4) Domain-Specific Design Limits Generalization**
- **Evidence**: System is tightly coupled to scientific research workflows (LaTeX parsing, citation analysis, academic paper generation); Scientist-Bench covers only research domains (CV/NLP/DM/IR)
- **Limitation**: Cannot directly apply to other multi-step reasoning tasks (financial analysis, legal research, product planning) without significant modifications to agent prompts and tooling
- **Risk for AGENT-33**: If adopting Resource Analyst or Advisor Agent patterns, overly research-specific implementations would reduce reusability across AGENT-33's broader use cases
- **Mitigation**: Abstract the **core patterns** (atomic decomposition, bidirectional mapping, iterative refinement) from their **domain instantiations** (LaTeX/code analysis); create generic `DecompositionAgent` and `AdvisorAgent` definitions that specialize via capability overrides; test patterns on non-research tasks (e.g., apply iterative refinement to web scraping, use bidirectional mapping for data transformations)

**5) Limited Tool Extensibility Compared to AGENT-33**
- **Evidence**: No documentation on adding custom tools; agents can install packages but unclear how to expose new APIs/data sources; no tool registry or governance system
- **Limitation**: Adding specialized capabilities (browser automation, database queries, API integrations) likely requires modifying agent prompt code rather than declarative tool definitions
- **Risk for AGENT-33**: If AI-Researcher's refinement/advisor patterns become central to AGENT-33, need to ensure they **compose with existing tool governance** (Phase 12's allowlists, registry, provenance)
- **Mitigation**: When implementing `AdvisorAgent` or `refinement_cycle` action, ensure they use AGENT-33's existing `ToolRegistry.invoke()` mechanism; make advisor feedback reference tool names from registry (not hardcoded capabilities); test that tool allowlists apply to refinement loops

**6) High Compute Costs from Iterative Refinement**
- **Evidence**: System performs "multiple refinement cycles" with full LLM invocations at each iteration (Code Agent generates → Advisor reviews → Code Agent refines); progressive experimental cycles run 1-2 epoch prototypes then full training
- **Implication**: For a single research task, could easily consume 10-20+ LLM calls (literature analysis, idea generation, implementation v1, advisor review, implementation v2, advisor review, ..., documentation) plus substantial compute for experimental validation
- **Risk for AGENT-33**: If naively applying iterative refinement to all workflows, **token costs could explode**—especially for large contexts (long code files, extensive memory histories, complex workflow states)
- **Mitigation**: Implement **budget controls** on refinement loops (max iterations, cumulative token limits); use cheaper models for early refinement passes (fast prototyping) and expensive models for final validation; cache intermediate results to avoid re-analysis; add `refinement_budget` to `WorkflowDefinition`

**7) Prototype-First Approach Assumes Cheap Fast Feedback**
- **Evidence**: Progressive experimental cycles run 1-2 epochs on small data before full-scale experiments
- **Assumption**: That prototypes are orders of magnitude cheaper/faster than full runs—true for ML training, may not hold for other domains
- **Risk for AGENT-33**: In code execution, "prototype mode" might mean running on synthetic data, but if real data is needed for meaningful validation, prototype cost approaches full execution cost
- **Mitigation**: Add `prototype_cost_ratio` to task definitions (ratio of prototype:full execution cost); only use progressive cycles when ratio < 0.1; for tasks with expensive prototypes, use **static analysis** or **dry-run mode** instead of actual execution

**8) Ground Truth Dependency for Evaluation**
- **Evidence**: Scientist-Bench requires "expert-written papers as ground truth references" for comparative evaluation
- **Limitation**: Evaluation only works for tasks where ground truth exists and is obtainable—not suitable for novel/exploratory work where correct answer is unknown
- **Risk for AGENT-33**: If adopting benchmark-driven development, need to handle cases where ground truth is unavailable (greenfield projects, exploratory research, user-specific workflows)
- **Mitigation**: Implement **dual evaluation modes**: (1) ground-truth comparison when available (regression tests, known tasks), (2) constraint satisfaction + heuristic scoring when unavailable (validate outputs meet specs, check for hallucinations, measure performance); document which evaluation mode applies to each benchmark

**9) Fixed Two-Level Input System May Not Cover All Use Cases**
- **Evidence**: System supports Level 1 (detailed idea provided) and Level 2 (papers-only ideation) but nothing in between or beyond
- **Limitation**: Cannot handle hybrid scenarios (partial idea + some constraints), iterative idea refinement (user provides feedback mid-generation), or multi-stakeholder input (multiple users contributing requirements)
- **Risk for AGENT-33**: If adopting hierarchical synthesis or idea generation patterns, fixed input levels could constrain workflow flexibility
- **Mitigation**: Generalize to **configurable input schemas** rather than hardcoded levels; allow workflows to specify required fields (idea_description, reference_papers, constraints, etc.) and optional fields; support incremental input where users refine specifications across multiple interactions

**10) Security Boundaries Rely on Docker Isolation Alone**
- **Evidence**: "Docker containerized environment provides robust security boundaries" but no mention of additional sandboxing (seccomp profiles, AppArmor, network isolation, resource limits)
- **Risk**: Docker provides process isolation but if agents have network access, can autonomously install packages, and execute arbitrary code, potential for data exfiltration, resource exhaustion, or supply chain attacks (malicious packages)
- **AGENT-33 context**: Phase 13 code execution already has sandboxing, Phase 14 adds security hardening—AI-Researcher's autonomous package installation pattern introduces new attack vectors
- **Mitigation**: If implementing autonomous dependency installation, require **allowlists** (only permit packages from curated registries), **integrity checks** (verify package hashes), **network policies** (block outbound connections during execution), and **resource quotas** (CPU/memory/disk limits); log all installations for audit; extend Phase 14 security review to cover supply chain risks

## 8) Feature extraction (for master matrix)

| Feature Category | Feature | AI-Researcher | AGENT-33 | Notes |
|---|---|---|---|---|
| **Orchestration** | Sequential pipeline stages | ✅ (3 stages) | ❌ (DAG-based) | AI-Researcher: fixed literature→implementation→documentation progression |
| | Dynamic workflow routing | ❌ | ✅ (conditional/parallel) | AI-Researcher lacks runtime adaptation |
| | Iterative refinement loops | ✅ (mentor-student) | ❌ | AI-Researcher: embedded in Stage 2; AGENT-33 should adopt as action |
| | Parallel execution | ❌ | ✅ (parallel_group) | AI-Researcher is strictly sequential |
| | Sub-workflows | ❌ | ❌ | Neither system supports hierarchical DAGs |
| **Agent Architecture** | Agent registry | ❌ | ✅ (auto-discovery) | AI-Researcher agents are hardcoded in scripts |
| | Sub-agent composition | ✅ (Resource/Advisor) | ❌ | AI-Researcher: Paper/Code/Plan sub-agents; Judge/Review/Analysis sub-agents |
| | Capability taxonomy | ❌ | ✅ (25 entries P/I/V/R/X) | AI-Researcher has implicit capabilities, no formal taxonomy |
| | Agent specialization | ✅ (6 specialized) | ✅ (6 definitions) | Similar specialization levels |
| | LLM provider abstraction | ✅ (LiteLLM 100+ models) | ⚠️ (ModelRouter 3 providers) | AI-Researcher has superior provider flexibility |
| **Code Execution** | Sandboxed execution | ✅ (Docker) | ✅ (SandboxConfig) | Different approaches: Docker vs. subprocess isolation |
| | Autonomous dependency installation | ✅ | ❌ | AI-Researcher allows agents to install packages; AGENT-33 has fixed environment |
| | Progressive experimental cycles | ✅ (prototype→full) | ❌ | AI-Researcher tests on minimal data first; AGENT-33 should adopt |
| | Multi-language support | ⚠️ (Python-focused) | ⚠️ (CLI-agnostic) | Both support multiple languages but optimized for Python |
| | Static code analysis | ❌ | ✅ (IV-01 validation) | AGENT-33 has input validation; AI-Researcher lacks pre-execution checks |
| **Evaluation** | Benchmark suite | ✅ (Scientist-Bench) | ❌ | AI-Researcher has 22-paper benchmark across 4 domains; AGENT-33 has test harnesses but no benchmarks |
| | Ground truth comparison | ✅ (expert papers) | ❌ | AI-Researcher uses human-written references; AGENT-33 has no ground truth framework |
| | Multi-evaluator debiasing | ✅ (GPT/Claude/Gemini) | ❌ | AI-Researcher ensembles across models; AGENT-33 uses single-model evaluation |
| | Completion ratio metric | ✅ (93.8%) | ❌ | AI-Researcher measures % of functionality implemented |
| | Correctness scoring | ✅ (5-point scale) | ❌ | AI-Researcher uses Judge Agent; AGENT-33 has pass/fail tests |
| | Hierarchical metrics | ✅ (novelty/rigor/analysis) | ❌ | AI-Researcher evaluates multiple dimensions; AGENT-33 lacks structured evaluation |
| **Observability** | Real-time tracing | ❌ | ✅ (structlog/spans) | AGENT-33 has Phase 16 observability; AI-Researcher is post-hoc only |
| | Execution logs | ✅ (Docker logs) | ✅ (observability/) | Both capture logs but AI-Researcher lacks structured correlation |
| | Metrics dashboards | ❌ | ⚠️ (planned Phase 16) | Neither has production dashboards yet |
| | Lineage tracking | ❌ | ✅ (observability/lineage.py) | AGENT-33 tracks artifact provenance; AI-Researcher doesn't |
| | Replay/debugging | ❌ | ⚠️ (observability/replay.py) | AGENT-33 has replay module; AI-Researcher requires full re-run |
| **Knowledge Management** | Atomic concept decomposition | ✅ (Resource Analyst) | ❌ | AI-Researcher breaks tasks into indivisible elements; AGENT-33 should adopt |
| | Bidirectional concept mapping | ✅ (math↔code) | ❌ | AI-Researcher links theory to implementation; AGENT-33 lacks this abstraction |
| | RAG-based paper analysis | ✅ (Paper Analyst) | ⚠️ (memory/rag.py) | AI-Researcher uses RAG for LaTeX parsing; AGENT-33 has general RAG but no doc-specific analysis |
| | Hierarchical documentation synthesis | ✅ (Documentation Agent) | ❌ | AI-Researcher prevents long-form hallucinations via staged generation; AGENT-33 should adopt |
| | Template-guided outputs | ✅ (domain schemas) | ❌ | AI-Researcher uses templates for structure; AGENT-33 has free-form outputs |
| **Tooling** | Tool registry | ❌ | ✅ (ToolRegistry) | AGENT-33 has declarative tool definitions; AI-Researcher has implicit tools |
| | Tool governance/allowlists | ❌ | ✅ (Phase 12) | AGENT-33 enforces tool permissions; AI-Researcher has unrestricted tool access |
| | Built-in browser automation | ❌ | ✅ (browser-agent) | AGENT-33 has Playwright integration; AI-Researcher lacks browser tools |
| | File operations | ⚠️ (code generation only) | ✅ (FileOpsTool) | AGENT-33 has comprehensive file ops; AI-Researcher generates code but no general file tools |
| | Web scraping | ❌ | ✅ (web_fetch) | AGENT-33 has WebFetchTool; AI-Researcher relies on pre-downloaded papers |
| **Memory & Context** | Short-term buffer | ❌ | ✅ (ConversationBuffer) | AGENT-33 maintains session state; AI-Researcher is stateless across stages |
| | pgvector long-term memory | ❌ | ✅ (memory/long_term.py) | AGENT-33 has vector store; AI-Researcher has no persistent memory |
| | Session management | ❌ | ✅ (SessionState) | AGENT-33 tracks multi-turn conversations; AI-Researcher is single-shot |
| | Observation capture | ✅ (execution logs) | ✅ (ObservationCapture) | Both capture execution artifacts but AI-Researcher lacks structured observation model |
| **Security** | Prompt injection detection | ❌ | ✅ (Phase 14) | AGENT-33 has detection module; AI-Researcher lacks injection defenses |
| | Input validation | ⚠️ (schema checks) | ✅ (IV-01..05) | AGENT-33 has comprehensive validation; AI-Researcher has minimal checks |
| | JWT/API key auth | ❌ | ✅ (security/auth.py) | AGENT-33 has multi-tenant auth; AI-Researcher is single-user |
| | Secrets management | ❌ | ✅ (security/vault.py) | AGENT-33 has encryption/vault; AI-Researcher uses plain .env files |
| | Audit logging | ⚠️ (Docker logs) | ✅ (observability/) | AGENT-33 has structured audit logs; AI-Researcher has unstructured logs |
| **Extensibility** | Plugin architecture | ❌ | ⚠️ (partial) | Neither has full plugin system; AGENT-33 has modular actions |
| | Custom workflow actions | ❌ | ✅ (actions/) | AGENT-33 allows new actions; AI-Researcher has fixed pipeline |
| | Multi-provider LLM switching | ✅ (LiteLLM) | ⚠️ (ModelRouter) | AI-Researcher superior: 100+ models vs. 3 providers |
| | Docker containerization | ✅ (core feature) | ⚠️ (optional) | AI-Researcher Docker-native; AGENT-33 uses local processes |
| | Package manager (uv) | ✅ (10-100x faster) | ❌ (uses pip) | AI-Researcher uses Rust-based uv; AGENT-33 should adopt |
| **Refinement & Feedback** | Advisor Agent pattern | ✅ (Judge/Review/Analysis) | ❌ | AI-Researcher has specialized review agents; AGENT-33 lacks this |
| | Structured feedback reports | ✅ (supplementary investigations) | ❌ | AI-Researcher generates actionable feedback; AGENT-33 has generic errors |
| | Refinement iteration tracking | ✅ (logs cycles) | ❌ | AI-Researcher documents improvement history; AGENT-33 lacks refinement abstraction |
| | Quality thresholds | ✅ (5-point scale) | ❌ | AI-Researcher gates progression on quality; AGENT-33 has binary pass/fail |
| **Integration** | Web GUI | ✅ (Gradio) | ❌ | AI-Researcher has built-in UI; AGENT-33 is API-only |
| | REST API | ⚠️ (not documented) | ✅ (FastAPI) | AGENT-33 has comprehensive API; AI-Researcher API unclear |
| | CLI interface | ✅ (run_infer_*.py) | ✅ (agent33 CLI) | Both have CLI but different patterns |
| | External messaging (Telegram/Discord) | ❌ | ✅ (messaging/) | AGENT-33 has chat integrations; AI-Researcher is standalone |
| | Webhooks | ❌ | ✅ (automation/webhooks.py) | AGENT-33 has webhook registry; AI-Researcher lacks external triggers |

**Summary Stats:**
- AI-Researcher advantages: LLM provider flexibility (LiteLLM), iterative refinement patterns, evaluation benchmarks, Docker-native architecture, hierarchical synthesis, autonomous dependency management
- AGENT-33 advantages: Real-time observability, tool governance, security hardening, multi-tenancy, persistent memory, dynamic workflows, extensibility
- Convergence opportunities: Integrate AI-Researcher's refinement/advisor patterns into AGENT-33's workflow engine; adopt UV package manager; implement bidirectional concept mapping; add benchmark suite; enhance LLM provider abstraction

## 9) Evidence links

**Primary Sources:**
- [GitHub Repository - HKUDS/AI-Researcher](https://github.com/HKUDS/AI-Researcher)
- [AI-Researcher ArXiv Paper (HTML)](https://arxiv.org/html/2505.18705v1)
- [NeurIPS 2025 Poster](https://neurips.cc/virtual/2025/poster/116385)
- [OpenReview Submission](https://openreview.net/pdf/a1c63cdd0495de94664b1513f7d95a3aedcb483a.pdf)
- [AI-Researcher on EmergentMind](https://www.emergentmind.com/papers/2505.18705)

**Technical Documentation:**
- [DeepWiki Configuration & Deployment Guide](https://deepwiki.com/HKUDS/AI-Researcher/4-usage-guide)
- [Docker for AI Science Agents](https://www.docker.com/blog/ai-science-agents-research-workflows/)
- [UV Package Manager Documentation](https://docs.astral.sh/uv/getting-started/installation/)
- [UV Docker Integration Guide](https://docs.astral.sh/uv/guides/integration/docker/)
- [LiteLLM Documentation](https://docs.litellm.ai/docs/)

**Research Context:**
- [SOK: Hallucinations and Security Risks in AI-Assisted Development](https://arxiv.org/html/2502.18468v1)
- [Nonsense and Malicious Packages: LLM Hallucinations in Code Generation (ACM)](https://cacm.acm.org/news/nonsense-and-malicious-packages-llm-hallucinations-in-code-generation/)
- [AstaBench: Rigorous AI Agent Benchmarking (AI2)](https://allenai.org/blog/astabench)
- [ResearcherBench: Evaluating Deep AI Research Systems (GAIR-NLP)](https://github.com/GAIR-NLP/ResearcherBench)
- [Anthropic Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)

**Community & Analysis:**
- [HT-X Analysis: Autonomous Scientific Innovation](https://ht-x.com/en/posts/2025/09/ai-researcher-autonomous-scientific-innovation/)
- [InfoQ: AI Agent Orchestration Architecture](https://www.infoq.com/news/2025/10/ai-agent-orchestration/)
- [Stanford AI Index 2025: Technical Performance](https://hai.stanford.edu/ai-index/2025-ai-index-report/technical-performance)
- [HKUDS Data Intelligence Lab](https://github.com/HKUDS)

**Comparative Research:**
- [Agentic AI: Comprehensive Survey of Architectures](https://arxiv.org/html/2510.25445v1)
- [Deep Research: A Survey of Autonomous Research Agents](https://arxiv.org/html/2508.12752v1)
- [OpenAI Frontier Science Evaluation](https://openai.com/index/frontierscience/)
- [Google Research: AI Co-Scientist](https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/)

---

**Dossier compiled by:** Claude Sonnet 4.5
**Research depth:** 11 web searches, 2 successful WebFetch operations, comprehensive analysis of architecture, orchestration, tooling, evaluation, and extensibility patterns
**Recommended next steps:** Pilot iterative refinement pattern in Phase 15 (Review Automation); evaluate UV package manager for Phase 19 (Release Automation); design Advisor Agent definition for code review workflows; prototype bidirectional concept mapping in Phase 13 (Code Execution)
