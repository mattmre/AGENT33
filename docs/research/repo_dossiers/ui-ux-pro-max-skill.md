# Repo Dossier: nextlevelbuilder/ui-ux-pro-max-skill

**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

UI UX Pro Max (31.2k stars, MIT license) is a Claude Code skill that provides design intelligence through a BM25-powered search engine over 11 CSV knowledge bases containing 67 UI styles, 96 color palettes, 57 font pairings, 100 industry-specific reasoning rules, and 25 chart types across 13 tech stacks. The v2.0 flagship feature is a **Design System Generator** that processes natural language UI/UX requests through parallel multi-domain searches, applies reasoning rules with priority keyword injection, and produces comprehensive markdown design systems with hierarchical persistence (MASTER.md + page-specific overrides). The skill auto-activates in Claude Code/Cursor/Windsurf by detecting UI/UX keywords and exposes a Python CLI (`python3 scripts/search.py`) for both direct invocation and programmatic integration, distributed via npm package (`uipro-cli`) that symlinks canonical CSV/script assets from `src/ui-ux-pro-max/` across multiple platform integrations.

## 2) Core orchestration model

**Pattern: Declarative knowledge base + BM25 retrieval + rule-based synthesis**

The skill has **no runtime orchestrator** — it operates as a **passive search engine** invoked via CLI or skill activation patterns. The orchestration model is **stateless request-response**:

1. **Skill activation**: Claude Code detects UI/UX keywords in user messages → auto-executes `search.py` with extracted query
2. **Multi-domain search**: For design system requests (`--design-system` flag), the generator executes **5 parallel searches** (product, style, color, landing, typography) with result limits (1, 3, 2, 2, 2 respectively)
3. **Reasoning rule application**: Product type search identifies applicable reasoning rule from `ui-reasoning.csv` (100 industry-specific rules) → extracts priority keywords → **re-runs style search with injected keywords** for semantic bias
4. **Result selection**: `_select_best_match()` scores candidates: exact style name match (10 pts) > keyword field match (3 pts) > general content match (1 pt)
5. **Synthesis**: Combines search results with reasoning rule defaults (effects, anti-patterns, decision logic) → formats as markdown with ASCII box layout or structured docs
6. **Persistence**: Optional `--persist` flag creates hierarchical file structure: `design-system/[project]/MASTER.md` (global colors/typography/spacing) + `pages/[name].md` (page-specific overrides only)

**Key difference from agent frameworks**: No dynamic planning, no multi-turn refinement, no execution monitoring. The skill is a **one-shot transformation** from query → CSV search → markdown output. Claude Code handles the conversational layer; the skill is a pure data retrieval + formatting pipeline.

**Stack-specific search**: Separate `search_stack()` function searches 13 framework guidelines (React, Next.js, Vue, Nuxt, Svelte, Astro, SwiftUI, Jetpack Compose, React Native, Flutter, HTML+Tailwind, shadcn/ui, Nuxt UI) stored in `data/stacks/` directory with same BM25 approach.

## 3) Tooling and execution

**Execution layer: CSV + BM25 + Python subprocess**

All design knowledge lives in **11 CSV files** (`src/ui-ux-pro-max/data/`):
- `charts.csv`, `colors.csv`, `icons.csv`, `landing.csv`, `products.csv`, `styles.csv`, `typography.csv`, `ui-reasoning.csv`, `ux-guidelines.csv`, `web-interface.csv`, `react-performance.csv`
- Plus `stacks/` subdirectory for framework-specific guidelines

**BM25 implementation** (`core.py`):
- **Tokenization**: lowercase, split, remove punctuation, filter short words (<3 chars)
- **Index building**: calculates inverse document frequency (IDF) for each term across all CSV rows
- **Scoring**: ranks documents using term frequency + document length normalization
- **Auto-domain detection**: counts keyword matches across 9 domains (color, chart, landing, product, style, ux, typography, icons, react, web) when domain unspecified

**Search configuration**: Two dictionaries define per-domain search and output columns:
- `SEARCH_CONFIGS`: maps domain → CSV file path + columns to index for tokenization
- `OUTPUT_COLUMNS`: maps domain → columns to return in results
- Example: `styles` domain indexes 11 columns (category, keywords, colors, effects, etc.) but only returns subset for display

**Design system generation** (`design_system.py`):
- **DesignSystemGenerator class** orchestrates 4-stage pipeline:
  1. Product category detection → loads applicable reasoning rule
  2. Multi-domain search with priority hints (style search gets keyword injection from reasoning rules)
  3. Intelligent result selection via scoring (exact match > keyword match > general match)
  4. Reasoning application → synthesizes search results + rule defaults
- **Output formats**: ASCII box (terminal) or markdown (documentation)
- **Lazy CSV loading**: reasoning rules load on first instantiation only
- **Effect merging**: combines search-derived effects with rule-derived defaults
- **Responsive specs**: includes breakpoint guidance (375px, 768px, 1024px, 1440px)

**Persistence pattern** (Master + Overrides):
```
design-system/[project-slug]/
├── MASTER.md          # Global rules: colors, typography, spacing, components
└── pages/
    └── [page-name].md # Page-specific overrides only (not full system)
```
Retrieval hierarchy: check page file first → fall back to MASTER.md. Override files generated via `_generate_intelligent_overrides()` using additional domain searches (avoids hardcoded page types).

**CLI interface** (`search.py` argparse):
```bash
# Domain-specific search
python3 scripts/search.py "minimalist dashboard" --domain style

# Design system generation
python3 scripts/search.py "SaaS analytics" --design-system -p "ProjectName"

# Stack-specific guidance
python3 scripts/search.py "performance" --stack react

# Persistence
python3 scripts/search.py "healthcare app" --design-system --persist
```

**No sandboxing**: Python scripts run in user environment (requires Python 3.x). No containerization, no execution safety layer.

## 4) Observability and evaluation

**Zero observability infrastructure**. The skill is a CLI tool with no:
- Logging (beyond stdout/stderr)
- Metrics collection
- Tracing
- Error reporting
- Usage analytics
- Performance monitoring

**Evaluation approach: Human review only**

No automated evaluation gates. The design system quality depends on:
1. **CSV completeness**: 100 reasoning rules cover common industries but gaps exist (issues #124 mentions Ant Design missing)
2. **BM25 tuning**: No configurable k1/b parameters, no result quality metrics, no A/B testing
3. **User validation**: Community issues (#133, #135, #109) surface bugs/limitations post-release
4. **Manual testing**: No test suite evident in repo (no `tests/` directory, no CI badges)

**Notable limitation** (from issues): Installation failures (#133) due to broken symlinks, file writing errors (#135), Windows path resolution issues (#109) — all discovered in production by users, not pre-release testing.

**Output validation**: Design systems include "Pre-Delivery Checklists" covering:
- Accessibility (contrast ratios, WCAG compliance)
- Interaction patterns (cursor-pointer on clickables, no layout shift on hover)
- Icon usage (SVG over emoji)
- Performance (avoid excessive animation)

These are **generated recommendations**, not enforced checks. No programmatic validation that generated CSS/design tokens meet stated accessibility criteria.

## 5) Extensibility

**Extension points:**

1. **CSV knowledge base expansion**:
   - Add rows to existing CSVs (new styles, colors, reasoning rules)
   - Add new CSV files with corresponding `SEARCH_CONFIGS` entry in `core.py`
   - No schema validation — any CSV with matching columns works

2. **New search domains**:
   - Add domain to `detect_domain()` keyword mapping
   - Add CSV config to `SEARCH_CONFIGS` dict
   - Add output columns to `OUTPUT_COLUMNS` dict
   - Example: `react-performance.csv` and `web-interface.csv` show pattern for new domains

3. **Stack-specific guidelines**:
   - Add CSV to `data/stacks/` directory
   - Follows same BM25 search pattern as main domains
   - No code changes needed (directory scan + convention)

4. **Template customization**:
   - Modify `templates/base/quick-reference.md` and `skill-content.md`
   - Templates referenced by design system generator for output formatting
   - No template engine (simple string formatting)

5. **CLI distribution**:
   - npm package `uipro-cli` (v2.2.3) built with Bun
   - Dependencies: commander, chalk, ora, prompts
   - Symlinks canonical assets from `src/` to multiple platform integrations (.claude/, .cursor/, etc.)
   - **Critical constraint**: "Always edit canonical files in src/; CLI syncs before publish" (from CLAUDE.md)

**Skill packaging for Claude Code**:
- Skill defined in `.claude/skills/ui-ux-pro-max/SKILL.md`
- `data/` and `scripts/` are symlinks to `src/ui-ux-pro-max/`
- Auto-activation: Claude Code detects UI/UX keywords → executes skill
- Slash command mode: `/ui-ux-pro-max [request]` for explicit invocation

**Platform support**: Claude Code, Cursor, Windsurf, Antigravity, Codex CLI, Continue, Gemini CLI (via CLI installer that adapts directory structure per platform)

**Limitation**: BM25 algorithm hardcoded in `core.py` — no pluggable ranker interface. To use semantic search or hybrid retrieval, must fork and rewrite `BM25` class.

## 6) Notable practices worth adopting in AGENT-33

**1. Hierarchical persistence pattern (Master + Overrides)**
```
design-system/[project]/
├── MASTER.md          # Global source of truth
└── pages/[page].md    # Only overrides, inherits rest from Master
```
**AGENT-33 application**: Session/workflow state could use same pattern:
- `session/[id]/MASTER.md` — global context (agent roster, shared memory)
- `session/[id]/workflows/[wf-id].md` — workflow-specific state (only deviations from master)

Retrieval: check specific first → fall back to master. Avoids duplication, maintains single source of truth.

**2. CSV as knowledge base for declarative rules**
- 100 industry-specific reasoning rules in `ui-reasoning.csv` (product type → pattern + style priorities + color mood + anti-patterns + decision logic)
- BM25 search over CSV enables **semantic retrieval without embeddings/vector DB**
- Much faster than LLM prompting for structured knowledge

**AGENT-33 application**: Tool governance rules, capability taxonomy, workflow patterns could live in CSV:
- `tool-rules.csv`: tool_name, allowed_contexts, security_constraints, anti_patterns, severity
- `workflow-patterns.csv`: pattern_name, trigger_conditions, recommended_dag, critical_steps
- BM25 search at runtime → inject into prompts (addresses governance-prompt disconnect finding)

**3. Priority keyword injection for semantic biasing**
- Reasoning rule search identifies applicable rule → extracts style keywords → **re-runs style search with injected keywords**
- Biases BM25 toward semantically relevant results without full semantic search

**AGENT-33 application**: Agent selection could use similar pattern:
- Orchestrator detects task domain → looks up domain-specific agent hints in CSV → re-runs agent capability search with injected keywords
- Cheaper than embedding all agent definitions, more precise than keyword-only search

**4. Auto-domain detection via keyword counting**
```python
def detect_domain(query):
    counts = {domain: count_keyword_matches(query, domain_keywords[domain])
              for domain in domains}
    return max(counts, key=counts.get)
```
Simple, fast, surprisingly effective for routing user queries to correct knowledge domain.

**AGENT-33 application**: Route user requests to correct subsystem (chat vs. workflow vs. tool execution) without LLM classification call.

**5. CLI-first design with skill wrapper**
- Core functionality in standalone Python CLI (`search.py`)
- Claude skill is thin wrapper that calls CLI
- Enables: (a) direct testing, (b) programmatic integration, (c) non-AI use cases

**AGENT-33 application**: Each subsystem (memory, workflows, tools) could expose CLI interface:
- `agent33 memory search "query"` → testable without FastAPI
- `agent33 workflow execute workflow.yaml` → usable in CI/CD
- Claude Code skill wraps CLI calls for conversational interface

**6. Lazy CSV loading pattern**
```python
class DesignSystemGenerator:
    _reasoning_rules = None  # Class variable

    def __init__(self):
        if DesignSystemGenerator._reasoning_rules is None:
            DesignSystemGenerator._reasoning_rules = load_csv()
```
Loads expensive data once per process, not per request. Avoids repeated file I/O.

**AGENT-33 application**: Agent definitions, tool registry, capability taxonomy load once at startup → cache in memory (already done for agent registry, could extend to tool allowlists).

**7. Pre-delivery checklists as part of generated output**
Every design system includes checklist:
- Accessibility: contrast ratios, WCAG compliance, focus states
- Interaction: cursor-pointer, no layout shift, loading states
- Icons: SVG over emoji, consistent sizing
- Performance: animation limits, image optimization

**AGENT-33 application**: Workflow execution could generate post-run validation checklists:
- Code execution: "Verify command ran in correct directory, check exit code, validate output format"
- Agent invocation: "Confirm response addresses original request, check for hallucination indicators"
- Tool usage: "Validate tool output schema, check for partial failures, verify side effects"

These aren't automated checks — they're **guidance for human reviewers** (or future validation steps).

## 7) Risks / limitations to account for

**1. BM25-only retrieval fails for semantic queries**
- User asks "calming medical interface" → BM25 won't match "healthcare + accessible + ethical" reasoning rule without exact keyword overlap
- No query expansion, no semantic embeddings, no synonym handling
- **Issue**: Many user requests use natural language that doesn't match CSV keyword vocabulary

**Mitigation for AGENT-33**: Hybrid search (BM25 + embeddings) for capability/tool matching. Current RAG is vector-only (opposite problem); combining both = best of both worlds.

**2. No input validation or sanitization**
- User query passed directly to BM25 tokenizer
- No SQL injection risk (CSV not SQL) but potential for malformed input breaking tokenizer
- No length limits, no character filtering

**AGENT-33 risk**: Phase 13 code execution already has IV-01..05 validation. Skills should have similar input validation layer.

**3. Windows path resolution issues**
- Issue #109: "missing script file detection (.shared/ui-ux-pro-max/scripts/search.py)"
- Symlink-based distribution breaks on Windows without developer mode
- CLI installer fails with EINVAL errors (#133)

**AGENT-33 mitigation**: Already documented in CLAUDE.md ("Windows Platform Notes"). Avoid symlinks in distribution; use file copying or package bundling instead.

**4. No versioning for knowledge base**
- CSV files updated directly in repo
- No schema migrations, no backward compatibility checks
- Breaking changes to CSV columns would break search configs silently

**AGENT-33 risk**: Tool/agent definitions need version tracking. If schema changes (e.g., new governance fields), old workflows/tools should still load or fail explicitly.

**5. Zero observability = debugging is trial-and-error**
- No logs of what reasoning rules matched, what search scores were, what keywords were injected
- When design system output is wrong, no way to trace why
- Issues (#135 "error writing file") have no stack traces, no debug context

**AGENT-33 mitigation**: Phase 16 observability is critical. Lineage tracking, structured logging, request tracing must be non-negotiable for debugging agent/workflow behavior.

**6. Reasoning rules are opaque to LLM**
- 100 CSV rules guide system behavior but **Claude never sees the rules**
- When Claude invokes skill, it gets back final design system with no explanation of which rules applied
- LLM can't reason about rule conflicts or missing coverage

**AGENT-33 parallel**: Governance constraints exist in code but never reach LLM prompts (critical finding from research sprint). Skills should return **explanation metadata** (which rules matched, why) so LLM can incorporate into reasoning.

**7. No conflict resolution for multi-domain recommendations**
- Style search returns 3 results, color search returns 2 — system picks "best match" via scoring but doesn't check **consistency**
- Example: Style recommends "dark mode by default" but color palette is light-optimized
- No cross-domain validation

**AGENT-33 mitigation**: Tool governance needs conflict detection (e.g., tool A requires env var that tool B forbids). Phase 14 security review should include "conflicting constraint" checks.

**8. Persistence creates stale data risk**
- MASTER.md generated once → user iterates on pages → master becomes outdated
- No "refresh master from pages" or "detect divergence" tooling
- Hierarchy assumes master is always canonical but provides no enforcement

**AGENT-33 parallel**: Session-spanning workflows (Phase 21) need staleness detection. If checkpoint is restored but DB schema changed, workflow should detect incompatibility.

## 8) Feature extraction (for master matrix)

| Feature | Implementation | AGENT-33 Status | Priority |
|---------|----------------|-----------------|----------|
| **BM25 text search** | `core.py` BM25 class with IDF + TF scoring over CSV | ❌ RAG is vector-only | HIGH — hybrid search (BM25+embeddings) for tools/agents |
| **CSV knowledge base** | 11 CSV files (styles, colors, reasoning rules, etc.) | ❌ No declarative rule storage | MEDIUM — `tool-rules.csv`, `workflow-patterns.csv` for governance |
| **Hierarchical persistence** | MASTER.md + pages/[name].md (override-only) | ❌ Flat checkpoint storage | LOW — `session/MASTER.md` + `workflows/[id].md` pattern |
| **Auto-domain detection** | Keyword counting across 9 domains → route to correct CSV | ❌ No request routing | LOW — route chat vs. workflow vs. tool requests |
| **Priority keyword injection** | Reasoning rule extracts keywords → re-run search with bias | ❌ No search biasing | MEDIUM — agent selection hints from domain context |
| **Multi-domain parallel search** | 5 concurrent searches (product, style, color, typography, landing) | ✅ Workflow actions support `parallel_group` | ✓ Already supported |
| **Intelligent result scoring** | Exact match (10) > keyword match (3) > general (1) | ❌ Tool/agent matching is binary (allowlist only) | MEDIUM — rank tools by relevance score |
| **Pre-delivery checklists** | Generated validation checklist per design system | ❌ No post-execution validation prompts | HIGH — workflow checklists for human review |
| **CLI-first with skill wrapper** | Standalone `search.py` CLI wrapped by Claude skill | ❌ No CLI for subsystems | LOW — `agent33 memory`, `agent33 workflow`, etc. |
| **Lazy resource loading** | Class-level cache for CSV data (load once per process) | ✅ Agent registry caches at startup | ✓ Already done for agents |
| **Symlink-based distribution** | `src/` canonical, symlinked to `.claude/`, `.cursor/`, etc. | ❌ No multi-platform distribution | N/A — not a packaging concern |
| **Stack-specific guidelines** | 13 framework CSVs in `data/stacks/` with same BM25 search | ❌ No framework-specific tool/agent guidance | LOW — could add React vs. Vue tool recommendations |
| **Template-based output** | Markdown templates in `templates/base/` | ❌ Responses are LLM-generated, not templated | LOW — structured output could use templates |
| **No runtime orchestrator** | Stateless CLI (request → search → response) | ❌ AGENT-33 has DAG executor, state machine, checkpoints | N/A — different architecture |
| **Zero observability** | No logging, metrics, tracing | ❌ Phase 16 planned but not implemented | HIGH — critical gap to address |
| **Human-only evaluation** | No automated quality checks, community reports bugs | ✅ Training system (Phase 21) but no eval gates yet | MEDIUM — Phase 17 eval gates needed |

**Key takeaways for AGENT-33:**
1. **BM25 + CSV pattern** is fast, cheap alternative to vector search for structured knowledge → adopt for tool/agent rules
2. **Hierarchical persistence** reduces duplication in session/workflow state → worth exploring
3. **Pre-delivery checklists** as generated guidance (not enforced checks) → add to workflow outputs
4. **Zero observability = zero debuggability** → validates Phase 16 priority

## 9) Evidence links

**Primary sources:**
- Repository: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- README: https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/README.md
- CLAUDE.md (skill integration guide): https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/CLAUDE.md
- SKILL.md (skill definition): https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/.claude/skills/ui-ux-pro-max/SKILL.md

**Core implementation:**
- search.py (CLI interface): https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/src/ui-ux-pro-max/scripts/search.py
- core.py (BM25 engine): https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/src/ui-ux-pro-max/scripts/core.py
- design_system.py (generator): https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/src/ui-ux-pro-max/scripts/design_system.py

**Knowledge base:**
- ui-reasoning.csv (100 rules): https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/src/ui-ux-pro-max/data/ui-reasoning.csv
- styles.csv (67 patterns): https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/src/ui-ux-pro-max/data/styles.csv
- Data directory listing: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/tree/main/src/ui-ux-pro-max/data

**Distribution:**
- CLI package.json: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/cli/package.json
- Template files: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/tree/main/src/ui-ux-pro-max/templates/base

**Community feedback:**
- Issues page: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/issues
- Issue #133 (installation failures): https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/issues/133
- Issue #135 (file writing errors): https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/issues/135
- Issue #109 (Windows path issues): https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/issues/109

**Stats:** 31.2k stars, 3.1k forks, 36 open issues, 93 commits, MIT license
