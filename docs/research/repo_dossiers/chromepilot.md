# Repo Dossier: Varun-Patkar/ChromePilot

**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

ChromePilot is a Chrome extension implementing AI-powered browser automation through a dual-LLM architecture where a vision-capable orchestrator (qwen3-vl-32k) analyzes screenshots and HTML to generate plain-English step plans, while a lightweight executor (llama3.1-8b-32k) translates those steps into browser actions with execution history context. The system uses accessibility tree extraction instead of CSS selectors for robust element identification, requires explicit user approval before execution, and processes everything locally via Ollama to preserve privacy. The architecture prioritizes token efficiency through selective context inclusion (last 4 conversation messages, latest schema only, screenshot reuse), implements graceful failure recovery with retry mechanisms, and surfaces each step's status to users for transparency.

## 2) Core orchestration model

**Two-stage separation of concerns:**

1. **Orchestrator phase:** Vision-capable model receives base64 screenshot, HTML structure, recent conversation history (last 4 messages max), and user query. Returns JSON with `{needs_steps: bool, steps: ["step 1", "step 2"], message: "..."}`. Steps are plain English descriptions, not tool calls. This runs once per user request, minimizing vision model overhead.

2. **Executor phase:** Lightweight text model receives individual step descriptions sequentially with execution history context (previous inputs/outputs). Returns JSON with `{tool: "click", inputs: {a11yId: "..."}, reasoning: "..."}`. Each step sees outputs from prior steps, enabling reference-based instructions ("use tab ID from step 1").

**Approval gate:** After orchestrator generates plan, UI displays all steps with "Awaiting Approval" status. User must explicitly approve before execution begins. Rejection triggers correction flow where user provides feedback and orchestrator regenerates plan (reusing prior screenshot to save tokens).

**Progressive execution:** Steps transition Pending → Executing → Completed/Failed. Failed steps halt execution immediately. Up to 2 retries allowed; after max retries, user must provide new instructions.

**Token budgeting:** Estimated via `(prompt.length + html.length) / 4 + 1500 (image buffer)`. 32,000 token ceiling enforced. Context optimization: older getSchema outputs replaced with `[X elements - see Step N]` placeholders, screenshots never stored in conversation history, only latest 4 messages retained.

## 3) Tooling and execution

**10 browser tools with accessibility-first element identification:**

- **Interactive:** `click`, `type`, `select` — operate on `a11yId` (data-agent-id attributes) rather than CSS selectors
- **Navigation:** `navigate`, `manageTabs`, `pressKey` — URL navigation, tab control, keyboard shortcuts
- **Context:** `getSchema` (extracts ~100-150 filtered interactive elements), `getHTML` (full content), `waitFor`
- **Scroll:** Directional with configurable amount

**Accessibility tree filtering system:**

- Raw DOM (~387 elements) → Filtered actionable elements (~100-150)
- Skips elements with no label AND no placeholder (noise reduction)
- Assigns `data-agent-id` attributes for semantic identification
- Selection via partial string matching against accessible names (matches screen reader semantics)
- Prevents executor confusion from CSS selector fragility

**Implementation architecture:**

- **Background script** (`background_tools.js`) — Tool implementations using Chrome extension APIs
- **Content script** (`content.js`) — Injected into pages for DOM manipulation via IPC messaging
- **Dual-lookup system:** Primary = a11yId attribute, Fallback = stored element map, Last resort = CSS selector

**Safety mechanisms:**

- `getActiveTab()` validation: tab exists, URL not internal (blocks chrome://, chrome-extension://, edge://)
- Content script injection with error suppression for already-injected scripts
- Element existence verification before manipulation
- Timeout mechanisms on wait operations
- Artificial delays (300-500ms) for browser processing time

**Notable gaps:**

- Minimal text input sanitization (no escaping, no size limits)
- No CSP settings in manifest
- Broad permissions (`<all_urls>`, debugger access)
- Tool inputs validated against schema but not deeply sanitized

## 4) Observability and evaluation

**Step-level execution tracking:**

- UI displays step cards with collapsible outputs
- Console logs format: `[TOOL:name] Action`, `[TOOL:name] Result`, `[TOOL:name] FAILED`
- Full error details captured with timestamps and stack traces
- Click/Type/Select failures throw descriptive errors: "Element a11yId=X not found"

**Verification prompt pattern:**

After all steps complete, system captures fresh screenshot and asks: "task_completed: true/false". This validates whether the automation achieved its intended outcome.

**Conversation persistence:**

- Stored in `chrome.storage.local`
- Only user/assistant text messages retained (HTML/screenshots excluded)
- Last 4 messages provide continuity while limiting token growth

**Limitations:**

- No metrics collection (execution time, success rates, token consumption)
- No structured logging for debugging post-execution
- No performance profiling or bottleneck analysis
- No A/B testing framework for prompt variations
- No user feedback collection on step quality

## 5) Extensibility

**Modular tool architecture:**

Each tool follows consistent specification pattern: description, required/optional inputs, outputs, use cases. Adding new tools requires:

1. Define tool schema in system prompt
2. Implement handler in background script
3. Add validation in content script (if DOM interaction required)
4. Update `_VALID_ACTIONS` enum

**Model swapping:**

Orchestrator and executor models are configurable. System supports any Ollama-compatible models with sufficient context windows (32k tokens minimum). Vision capability only required for orchestrator.

**Planned v3 enhancements (from README):**

- Dynamic re-planning during execution
- Step-by-step evaluation and adaptation
- Conversational clarification requests
- Intelligent error recovery
- Move toward "true agentic behavior with iterative adaptation"

**Extension limitations:**

- Chrome extension boundary constrains deployment (cannot run as standalone service)
- Local Ollama dependency prevents cloud deployment
- No API for programmatic access
- No plugin system for custom tool injection

## 6) Notable practices worth adopting in AGENT-33

### 1. Accessibility-first element identification

**ChromePilot pattern:** Uses semantic `data-agent-id` attributes with accessibility tree filtering instead of CSS selectors. Reduces ~387 raw elements to ~100-150 actionable ones. Selection via partial string matching against accessible names.

**AGENT-33 gap:** `browser.py:207-253` uses raw CSS selectors exclusively. No accessibility tree extraction, no semantic filtering, no noise reduction.

**Adoption path:**

- Add `getSchema` action that extracts accessibility tree (role, label, placeholder)
- Filter to interactive elements only (buttons, inputs, links, selects)
- Assign data-attributes for stable identification
- Update prompts to encourage schema inspection before actions

**Impact:** Reduces brittle selector failures, improves reliability for dynamic pages, matches screen reader semantics.

### 2. Dual-LLM token optimization strategy

**ChromePilot pattern:** Vision model runs once to generate plan, lightweight executor translates steps. Screenshot captured once and reused during correction flow. Older context replaced with placeholders.

**AGENT-33 gap:** Single LLM processes all steps. No screenshot reuse, no context compression, no plan-execute separation.

**Adoption path:**

- Separate workflow planning from execution in `workflows/executor.py`
- Cache visual context (screenshots, schemas) at workflow level
- Compress historical outputs with `[N results - see Step X]` pattern
- Consider cheaper model for deterministic translation steps

**Impact:** 3-5x token reduction for multi-step browser workflows.

### 3. Explicit approval gates for automation

**ChromePilot pattern:** Displays all planned steps before execution. User clicks "Approve & Execute" or "Reject". Rejection triggers correction flow with feedback.

**AGENT-33 gap:** Workflows execute immediately on submission. No plan preview, no approval checkpoint, no correction flow.

**Adoption path:**

- Add `approval_required: bool` to workflow definitions
- Implement `/v1/workflows/{id}/preview` endpoint returning step list
- Add `/v1/workflows/{id}/approve` and `/v1/workflows/{id}/reject` routes
- Store rejection feedback for orchestrator re-planning

**Impact:** Critical for production browser automation. Prevents runaway executions, enables user guidance.

### 4. Progressive disclosure of execution state

**ChromePilot pattern:** Step cards transition Pending → Executing → Completed/Failed with collapsible outputs. Each tool result visible. Retry buttons for failed steps.

**AGENT-33 gap:** Workflow checkpoints exist but no real-time step visibility. Outputs only available after workflow completes.

**Adoption path:**

- Add SSE endpoint `/v1/workflows/{id}/stream` for step updates
- Update `workflows/executor.py` to emit events on step transitions
- Store outputs in Redis for immediate retrieval
- Add retry mechanism at step level (currently only workflow-level)

**Impact:** Transparency for debugging, better UX for long-running workflows.

### 5. Screenshot-driven verification prompts

**ChromePilot pattern:** After automation completes, captures fresh screenshot and asks "task_completed: true/false" to validate outcome.

**AGENT-API gap:** No post-execution validation. Workflow success determined by error absence, not outcome verification.

**Adoption path:**

- Add final validation step to browser workflows
- Capture screenshot after last action
- Prompt: "Based on this screenshot, did the automation achieve [original goal]?"
- Store validation result in workflow metadata

**Impact:** Catches silent failures where steps execute but wrong outcome occurs.

## 7) Risks / limitations to account for

### 1. Minimal input sanitization

**Risk:** Text inputs passed directly to DOM without escaping. No size limits except storage truncation. Malicious step descriptions could inject scripts or overflow buffers.

**Mitigation for AGENT-33:**

- Add HTML escaping before DOM insertion
- Enforce max text length (e.g., 10k chars) on type_text action
- Validate selector syntax before execution
- Sanitize keyboard shortcut combinations (prevent system key combos)

### 2. Broad permission model

**Risk:** `<all_urls>` host permission + content script injection across all sites + debugger access = wide security surface. Extension can inspect/modify any page user visits.

**Mitigation for AGENT-33:**

- Playwright runs in isolated subprocess with no persistent page access
- Sessions auto-close after 5-minute TTL
- No cross-session state leakage
- Already better isolated than extension model

### 3. No rate limiting or resource bounds

**Risk:** Infinite scroll loops, recursive tab spawning, or screenshot spam could exhaust memory/CPU.

**Mitigation for AGENT-33:**

- Add action count limit per workflow (e.g., 50 actions max)
- Track resource usage per session (screenshot count, navigation count)
- Enforce timeout on entire workflow, not just individual actions
- Auto-close sessions consuming >500MB memory

### 4. Token limit cliff edge

**Risk:** 32,000 token ceiling enforced but estimated via heuristic `(text.length / 4) + 1500`. Actual tokenization may differ. Requests rejected without graceful degradation.

**Mitigation for AGENT-33:**

- Use actual tokenizer for precise counting (tiktoken for OpenAI, sentencepiece for Llama)
- Implement graceful context pruning (drop oldest schemas first, then messages)
- Warn user when approaching 80% of limit
- Offer "compress history" action to summarize prior outputs

### 5. No rollback mechanism

**Risk:** Failed automation may leave page in inconsistent state. Retries start from failure point without undo. User must manually clean up.

**Mitigation for AGENT-33:**

- Capture page state before each destructive action (screenshot + HTML snapshot)
- Offer "restore to step N" rollback via browser back/forward navigation
- Store navigation history in session for replay
- Implement checkpoint/restore pattern from workflow engine

### 6. Single point of failure for orchestrator

**Risk:** If orchestrator generates bad plan, entire automation fails. No dynamic re-planning during execution.

**Mitigation for AGENT-33:**

- Implement "step validation" LLM call before each action (verify preconditions met)
- Allow executor to request re-planning if step impossible ("element not found, need new approach")
- Track step failure patterns and adjust orchestrator prompt
- Already have workflow retry logic; extend to step-level re-planning

### 7. Local-only deployment constraint

**Risk:** Chrome extension + local Ollama = cannot scale horizontally, cannot deploy to cloud, limited to developer machines.

**AGENT-33 advantage:** FastAPI service model supports cloud deployment, container orchestration, distributed execution. Browser tool uses Playwright which runs server-side.

## 8) Feature extraction (for master matrix)

| Feature | ChromePilot | AGENT-33 | Notes |
|---------|-------------|----------|-------|
| **Architecture** |
| Dual-LLM orchestration | ✅ Orchestrator + Executor | ❌ Single LLM per agent | ChromePilot separates planning from execution |
| Vision model support | ✅ qwen3-vl for screenshots | ❌ Text-only | AGENT-33 LLM abstraction could add vision |
| Approval gates | ✅ Explicit user approval | ❌ Auto-execution | Critical for production automation |
| Step-level retry | ✅ Up to 2 retries per step | ❌ Workflow-level only | Granular failure recovery |
| **Browser Automation** |
| Element identification | ✅ Accessibility tree + a11yId | ❌ CSS selectors only | ChromePilot more robust |
| Persistent sessions | ✅ Session ID reuse | ✅ Session ID reuse | Both support multi-step |
| Screenshot capture | ✅ Base64 output | ✅ Base64 output | Equivalent |
| Interactive actions | ✅ 10 tools | ✅ 9 tools | Similar coverage |
| Schema extraction | ✅ getSchema (filtered elements) | ❌ None | AGENT-33 has get_elements (unfiltered) |
| HTML extraction | ✅ getHTML | ✅ extract_text | AGENT-33 truncates at 100k chars |
| Tab management | ✅ Open/close/switch tabs | ❌ Single page only | ChromePilot richer |
| Keyboard shortcuts | ✅ Modifier keys supported | ❌ None | ChromePilot only |
| **Token Optimization** |
| Context compression | ✅ Placeholder replacement | ❌ None | ChromePilot replaces old schemas |
| Screenshot reuse | ✅ Correction flow reuses | ❌ None | Saves tokens on retry |
| Conversation limiting | ✅ Last 4 messages only | ❌ Full history | AGENT-33 memory unbounded |
| Token budget enforcement | ✅ 32k hard limit | ❌ No limit | AGENT-33 delegates to LLM provider |
| **Observability** |
| Step visualization | ✅ Real-time status cards | ❌ Post-execution only | ChromePilot UI shows progress |
| Execution logging | ✅ Console logs per tool | ✅ structlog framework | AGENT-33 more structured |
| Error details | ✅ Full stack traces | ✅ Exception capture | Equivalent |
| Outcome verification | ✅ Screenshot validation prompt | ❌ None | ChromePilot checks task completion |
| **Safety** |
| Input sanitization | ❌ Minimal (selector/text unchecked) | ❌ Minimal (selector validated) | Both need improvement |
| URL allowlisting | ❌ None | ✅ Security allowlist system | AGENT-33 has governance layer |
| Action count limits | ❌ None | ❌ None | Both need resource bounds |
| Session TTL | ❌ None | ✅ 5-minute idle timeout | AGENT-33 better resource mgmt |
| Internal page blocking | ✅ chrome://, edge:// blocked | ✅ Playwright isolated subprocess | Different models, both safe |
| **Extensibility** |
| Tool schema format | ✅ JSON with examples | ✅ Pydantic models | AGENT-33 more formal |
| Plugin system | ❌ Extension-only | ✅ Tool registry | AGENT-33 more flexible |
| Model swapping | ✅ Any Ollama model | ✅ Provider abstraction | Both support |
| API access | ❌ Extension-only | ✅ REST API | AGENT-33 service model |
| **Deployment** |
| Runtime environment | ❌ Chrome extension + local Ollama | ✅ FastAPI + Docker | AGENT-33 cloud-ready |
| Horizontal scaling | ❌ Single user only | ✅ Multi-tenant | AGENT-33 production-grade |
| Privacy model | ✅ Local processing only | ⚠️ Depends on LLM provider | ChromePilot advantage for sensitive data |

## 9) Evidence links

### Repository & Documentation
- **Main repo:** https://github.com/Varun-Patkar/ChromePilot
- **README:** https://github.com/Varun-Patkar/ChromePilot/blob/main/README.md
- **Architecture doc:** https://github.com/Varun-Patkar/ChromePilot/blob/main/ARCHITECTURE.md
- **License:** MIT

### Source Code Analysis
- **Tool implementations:** https://github.com/Varun-Patkar/ChromePilot/blob/main/background_tools.js
  - Lines 1-50: Input validation, active tab checks, internal URL blocking
  - Lines 51-150: Click/type/select/scroll implementations
  - Lines 151-200: Navigation and tab management
- **Content script:** https://github.com/Varun-Patkar/ChromePilot/blob/main/content.js
  - Lines 1-100: Dual-lookup element identification (a11yId → map → selector)
  - Lines 101-200: Click/type/select handlers with scroll-into-view
  - Lines 201-300: Accessibility tree extraction and filtering
- **Orchestrator workflow:** https://github.com/Varun-Patkar/ChromePilot/blob/main/sidebar.js
  - Lines 1-150: Prompt construction, context management (screenshot/HTML toggles)
  - Lines 151-300: Approval flow, execution loop, retry logic
  - Lines 301-400: Token budgeting, context compression (placeholder replacement)
  - Lines 401-500: Error handling, response parsing, connection management
- **Manifest:** https://github.com/Varun-Patkar/ChromePilot/blob/main/manifest.json
  - Permissions: activeTab, tabs, scripting, sidePanel, storage, debugger
  - Host permissions: `<all_urls>`

### AGENT-33 Comparison
- **Browser tool:** `D:\GITHUB\AGENT33\engine\src\agent33\tools\builtin\browser.py`
  - Lines 75-79: Valid actions enum (9 tools vs ChromePilot's 10)
  - Lines 101-153: Execute method with session management
  - Lines 204-253: Interactive actions using raw CSS selectors
  - Missing: Accessibility tree extraction, schema filtering, tab management, keyboard shortcuts

### Key Architectural Differences

**Element Identification:**
- ChromePilot: `data-agent-id` attributes → accessibility tree filtering → ~100-150 actionable elements
- AGENT-33: Raw CSS selectors → no filtering → full DOM exposed to LLM

**Orchestration Model:**
- ChromePilot: Vision orchestrator (plan) → Text executor (execute) → 2 LLM calls per task
- AGENT-33: Single agent → N LLM calls per workflow

**Approval Pattern:**
- ChromePilot: Display plan → User approval → Execute → Verify outcome
- AGENT-33: Execute immediately → No verification

**Token Management:**
- ChromePilot: 32k hard limit, placeholder compression, screenshot reuse, 4-message history
- AGENT-33: No token budgeting, full history retention, no compression

**Privacy Model:**
- ChromePilot: 100% local (Ollama), no cloud transmission
- AGENT-33: Depends on LLM provider (Ollama/OpenAI/etc.)

### Recommendations for AGENT-33

**Immediate wins (Phase 14-16):**

1. **Add accessibility tree extraction to browser tool** (2-4 hours)
   - Implement `getSchema` action in `browser.py`
   - Filter to interactive elements with labels
   - Return JSON array of {id, role, label, placeholder}
   - Update browser-agent prompts to call getSchema before actions

2. **Implement step-level approval for browser workflows** (4-6 hours)
   - Add `approval_required` flag to workflow definitions
   - Create `/v1/workflows/{id}/preview` endpoint
   - Store plan in Redis, wait for user approval
   - Emit SSE events for real-time step status

3. **Add post-automation verification prompts** (2-3 hours)
   - Extend browser workflows with final validation step
   - Capture screenshot after last action
   - Prompt: "Did this achieve [goal]? true/false"
   - Store validation result in workflow metadata

**Medium-term enhancements (Phase 17-19):**

4. **Token budgeting for long workflows** (6-8 hours)
   - Add tokenizer to memory subsystem (tiktoken/sentencepiece)
   - Track running token count per workflow
   - Prune oldest observations when approaching limit
   - Warn at 80% capacity

5. **Context compression for repeated structures** (4-6 hours)
   - Store full getSchema output once per workflow
   - Replace subsequent schemas with `[N elements - see Step X]`
   - Implement in `memory/buffer.py` as compression strategy

6. **Resource bounds for browser sessions** (3-4 hours)
   - Add action counter per workflow (max 50)
   - Track screenshot count, navigation count
   - Auto-terminate sessions consuming >500MB
   - Emit alerts when approaching limits

**Long-term research (Phase 20+):**

7. **Dual-LLM workflow architecture** (investigation)
   - Evaluate token savings from plan-execute separation
   - Compare cost: 1 vision call + N cheap executor calls vs N unified calls
   - Consider for workflows where visual context static across steps

8. **Dynamic re-planning on step failure** (investigation)
   - Currently retry same step up to workflow max_retries
   - Investigate: call orchestrator for new plan when step fails
   - Track failure patterns to improve orchestrator prompts

9. **Vision model integration** (blocked on provider support)
   - AGENT-33 LLM abstraction supports vision-capable models
   - Requires provider implementing image input (Ollama llava, OpenAI gpt-4-vision)
   - Unlock screenshot-driven automation without browser tool
