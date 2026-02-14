# Repo Dossier: openai/swarm
**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

Swarm is an educational, experimental framework from OpenAI's Solution team that demonstrates lightweight multi-agent coordination using only two core abstractions: `Agent` objects and handoffs between them. Built as a thin wrapper over the Chat Completions API (not the Assistants API), Swarm implements a stateless client-side execution loop where agents can dynamically transfer conversations to other agents by returning Agent instances from tool functions. The framework emphasizes ergonomic design, testability, and maintainability through a minimal API surface (`Swarm`, `Agent`, `Response`) and explicit state passing via `context_variables`. **Important caveat**: The README states Swarm has been "replaced by the OpenAI Agents SDK, which is a production-ready evolution of Swarm" and recommends migration for all production use cases, though the Agents SDK does not appear to be publicly available as of this snapshot.

## 2) Core orchestration model

**Primary primitive**: The `Agent` class is a Pydantic model containing:
- `name` (str): Agent identifier
- `model` (str): LLM model, defaults to "gpt-4o"
- `instructions` (str | Callable): System prompt or dynamic function receiving `context_variables`
- `functions` (List[AgentFunction]): Tools the agent can invoke
- `tool_choice` (str, optional): Constraint on tool selection
- `parallel_tool_calls` (bool): Enables concurrent function execution, defaults to True

Agents are **stateless primitives** built on Chat Completions, not Assistants API. They do not persist state between calls.

**State model**: Completely stateless—all state passes explicitly between `client.run()` calls via:
- `messages`: Full conversation history (OpenAI Chat Completions format)
- `context_variables`: Dict of runtime state that persists across agent handoffs
- `agent`: The currently active agent instance

Context variables support two access patterns:
1. **Dynamic instructions**: Agent instructions can be functions like `lambda ctx: f"Help user {ctx['user_name']}"`
2. **Function parameters**: Functions with `context_variables` parameter receive current state and can return updated dicts via `Result` objects

**Concurrency**: The execution loop is purely sequential with a `max_turns` limit (default 10). Tools can execute in parallel if `parallel_tool_calls=True`, but the overall agent conversation is single-threaded. The `client.run()` method cycles through:
1. Get completion from current agent
2. Execute tool calls (all in sequence or parallel depending on config)
3. Switch agents if a tool returned an Agent
4. Update context variables from function results
5. Append results and repeat until no new tool calls

**Critical limitation**: When multiple functions execute in one turn and multiple return Agent objects, "only the last handoff function will be used."

**Human-in-the-loop**: Fully manual—Swarm provides no automatic HITL controls. The `/swarm/repl/repl.py` module implements a basic interactive loop (`run_demo_loop`) that:
- Prompts user for input
- Appends to message history
- Calls `client.run()` with current agent
- Displays response
- Repeats with potentially new agent

Any HITL gating (approvals, confirmations, escalations) must be implemented as explicit tools or in application code wrapping Swarm.

## 3) Tooling and execution

**Tool interface**: Swarm converts Python functions to OpenAI tool schemas automatically via `function_to_json()` utility:
- Uses `inspect` module to extract function signature
- Maps Python types to JSON schema types (str→"string", int→"integer", etc.)
- Identifies required parameters by detecting missing defaults
- Returns dict with name, description (from docstring), and parameters

Tools are ordinary Python callables with type `AgentFunction = Callable[[], Union[str, Agent, dict]]`. Functions can:
- Return strings for direct results
- Return Agent instances to trigger handoffs
- Return `Result` objects containing `value`, `agent`, and `context_variables`
- Access `context_variables` parameter if present in signature (auto-injected)

**Handoff mechanism**: When a function returns an Agent, `handle_tool_calls()` converts it to `Result(value=json.dumps({'assistant': agent.name}), agent=agent)`. The run loop detects this and switches `active_agent` for the next iteration. Context variables merge automatically from all Result objects.

**Runtime environment**: Pure Python client-side execution. Tools run in the same process as the Swarm client with no isolation. The framework imports `openai` for LLM calls and uses standard library (`inspect`, `json`, `copy`) for everything else. Async support exists but is not emphasized in examples.

**Sandboxing/safety**: **None**. Swarm provides zero sandboxing or safety controls. All tools execute directly in the client process with full Python capabilities. There are no:
- Allowlists or blocklists for tools/agents
- Resource limits (time, memory, network)
- Permission systems
- Input validation beyond Python type hints
- Output sanitization
- Execution isolation

The framework explicitly delegates all safety to the calling application. Example code includes arbitrary file system access and external API calls with no guardrails.

## 4) Observability and evaluation

**Observability**: Minimal built-in observability:
- `debug_print()` utility emits timestamped ANSI-colored logs when debugging enabled
- Streaming mode emits delimiter events `{"delim":"start"}` and `{"delim":"end"}` to mark agent transitions
- `Response` object returns full message history, final agent, and merged context variables
- No tracing, metrics, lineage tracking, or structured logging

The `/swarm/repl/repl.py` module provides colored pretty-printing of messages and tool calls for interactive demos but this is purely display logic.

**Evaluation**: The examples include an evaluation pattern:
- **Triage Agent**: Has `evals.py` and `evals_util.py` with pytest-based tests that validate routing decisions
- **Airline**: Has `evals/` directory with JSON test cases specifying expected function calls and conversation outcomes
- Test runner stores results in `evals/eval_results/`

The eval structure checks:
- Which agent handled a request (routing correctness)
- Which functions were invoked (behavioral verification)
- Conversation quality (manual inspection)

However, the README warns these "will have to be updated and catered to your particular use case" and provides no generic eval framework. Evaluation is purely example code, not a framework feature.

## 5) Extensibility

Swarm is **extremely minimal by design** with only three public exports (`Swarm`, `Agent`, `Response`). Extensibility comes from:

**Function-first design**: Any Python callable can be a tool. No base classes, decorators, or registration required—just pass functions to `Agent(functions=[...])`. Functions returning Agent trigger handoffs, enabling arbitrary orchestration graphs.

**Dynamic instructions**: Agent instructions can be static strings or callables receiving context variables, enabling runtime prompt customization without subclassing.

**Context variables**: The `context_variables` dict is completely unstructured, allowing applications to pass arbitrary state. Functions can read/write any keys they need.

**No framework lock-in**: Swarm is a ~300-line wrapper over OpenAI Chat Completions. The entire execution model is transparent and could be replicated or customized. The stateless design means you can snapshot conversation state at any point and resume elsewhere (distributed systems, serverless, etc.).

**Limitations**:
- No plugin system or middleware hooks
- No custom LLM providers (hardcoded to OpenAI client)
- No execution lifecycle hooks (pre/post tool execution, agent switch events)
- No agent discovery or registry—all agents must be instantiated in code

The philosophy is "reference implementation, not framework"—developers fork or reimplement rather than extend.

## 6) Notable practices worth adopting in AGENT-33

### 1. **LLM-driven agent routing via function returns**
Swarm's killer feature is that **the LLM decides which agent to route to** by invoking a `transfer_to_X()` function that returns an Agent instance. This is far more flexible than static DAG workflows:

```python
def transfer_to_sales() -> Agent:
    """Call when user asks about products or pricing."""
    return sales_agent

def transfer_to_refunds() -> Agent:
    """Call when user wants a refund or is upset about cost."""
    return refunds_agent

triage_agent = Agent(
    name="Triage",
    instructions="Route users to the right specialist",
    functions=[transfer_to_sales, transfer_to_refunds]
)
```

The LLM reads the docstrings and decides which transfer function to call based on user intent. **AGENT-33 should implement this pattern** as a new workflow action type `invoke_agent_dynamic` that lets an agent choose the next agent via tool call rather than static DAG edges.

### 2. **Hub-and-spoke escalation pattern**
The triage example demonstrates a clean pattern: specialized agents can escalate back to the triage hub when they encounter out-of-scope requests:

```python
sales_agent = Agent(
    name="Sales",
    instructions="Sell bees enthusiastically",
    functions=[process_sale, transfer_back_to_triage]
)
```

This prevents dead-ends where an agent gets stuck on an irrelevant question. AGENT-33's workflow engine should support bi-directional handoffs, not just forward delegation.

### 3. **Context variables as persistent session state**
Swarm's `context_variables` dict is simple but powerful:
- Passed explicitly to every `client.run()` call
- Auto-injected into functions that declare `context_variables` parameter
- Updated via `Result` objects that merge new values
- Survives agent handoffs automatically

AGENT-33's workflow `step.input` expressions could reference a `context` namespace that persists across steps, reducing the need to thread data through every step's output.

### 4. **Dynamic instructions from context**
Agent instructions can be functions:
```python
instructions=lambda ctx: f"Help user {ctx['user_name']} with {ctx['intent']}"
```

This enables personalization, A/B testing, and context-aware behavior without spawning new agent definitions. AGENT-33 could support `{{ }}` template variables in agent prompts that resolve from workflow state.

### 5. **Minimal API surface**
Swarm exposes exactly three classes and enforces statelessness. This makes testing trivial:
```python
response = client.run(agent=my_agent, messages=[{"role": "user", "content": "test"}])
assert response.messages[-1]["content"] == expected
```

No database setup, no async lifecycle, no service dependencies. AGENT-33 should provide a `TestWorkflow` harness that similarly isolates execution from infrastructure.

### 6. **Streaming with agent transition events**
Swarm's streaming mode emits `{"delim":"start"}` and `{"delim":"end"}` to mark when each agent processes a message. This enables UIs to show "Now talking to Sales Agent..." transitions in real-time. AGENT-33's SSE streaming should emit workflow step boundaries and agent switches.

### 7. **Evaluation as JSON test cases**
The airline example stores eval cases as JSON with `conversation` (messages array) and `expected_functions` (list of tools that should be called). A pytest runner executes conversations and asserts on function invocation. AGENT-33 could adopt this for workflow regression tests—store input/output pairs as JSON fixtures and auto-generate test cases.

## 7) Risks / limitations to account for

### 1. **Project is deprecated/educational only**
The README explicitly states Swarm is "replaced by the OpenAI Agents SDK" and recommends migration for "all production use cases." However, the Agents SDK does not appear to be publicly released as of 2026-02-14. This means:
- Swarm may not receive updates or bug fixes
- Community support may dwindle as users wait for the SDK
- Patterns shown may not reflect OpenAI's current best practices

**AGENT-33 implication**: Adopt the *patterns* (LLM-driven routing, function-based handoffs) but don't depend on Swarm as a library. Implement the concepts natively in our workflow engine.

### 2. **No sandboxing = critical security gap**
Swarm executes all tools in-process with zero isolation. An LLM hallucination or prompt injection could invoke arbitrary Python code:
```python
def dangerous_tool(cmd: str):
    """Execute shell command"""
    subprocess.run(cmd, shell=True)  # No restrictions!
```

**AGENT-33 implication**: Our Phase 13 code execution layer already addresses this with validation, allowlists, and subprocess isolation. We must ensure any Swarm-style dynamic routing still flows through governance checks.

### 3. **Single handoff per turn = conversation modeling limitation**
Swarm's "only the last handoff will be used" rule means you can't model parallel consultations or split conversations. If an agent wants to consult two specialists before responding, it must serialize the handoffs across multiple turns.

**AGENT-33 implication**: Our workflow engine should support `parallel_group` actions that can invoke multiple agents concurrently and merge results, going beyond Swarm's sequential model.

### 4. **No built-in memory or RAG**
Swarm is purely conversational—no long-term memory, no vector search, no knowledge retrieval. Context is limited to what fits in the message history.

**AGENT-33 implication**: When implementing LLM-driven routing, ensure agents can still access our memory subsystem (`memory/rag_pipeline.py`) and observation capture. Don't regress to pure stateless execution.

### 5. **No cost/latency tracking**
Swarm makes one LLM call per turn with no budgeting, rate limiting, or cost tracking. A runaway handoff loop could consume tokens indefinitely until `max_turns` is hit.

**AGENT-33 implication**: The workflow engine should track LLM calls per workflow run and enforce limits (`observability/metrics.py` already has placeholders for this). Add a `max_llm_calls` workflow-level config.

### 6. **Hardcoded to OpenAI**
Swarm uses `openai.OpenAI()` directly with no abstraction layer. You cannot use Anthropic, local models, or custom LLM providers without forking.

**AGENT-33 implication**: Our `llm/router.py` already abstracts providers. Ensure dynamic agent routing uses `ModelRouter` not a hardcoded client.

### 7. **No governance or compliance tracking**
Swarm has no concept of audit logs, approval workflows, or policy enforcement. Every agent has full access to every tool in its function list.

**AGENT-33 implication**: The governance layer (`GovernanceConstraints`, `tools/governance.py`) must integrate with dynamic routing. If an LLM tries to route to a restricted agent or invoke a blocked tool, the governance layer should intercept and deny with an explanation.

### 8. **Stateless design limits workflow complexity**
Swarm's statelessness is great for testing but makes complex workflows harder. There's no concept of "this agent is waiting for approval" or "retry this step tomorrow"—you'd have to persist that state externally and reconstruct the conversation.

**AGENT-33 implication**: Our workflow checkpointing (`workflows/checkpointing.py`) and state machine should complement Swarm-style routing, not replace it. Dynamic routing is for *conversational* decisions; DAGs are still the right model for scheduled/long-running processes.

## 8) Feature extraction (for master matrix)

| Category | Features |
|----------|----------|
| **Interfaces** | • Python function-based tools with auto-schema generation<br>• Streaming SSE with agent transition delimiters<br>• Interactive REPL (`run_demo_loop`)<br>• Stateless API: `client.run(agent, messages, context_variables)` |
| **Orchestration primitives** | • Agent-to-agent handoffs via function returns (LLM-driven routing)<br>• Sequential turn-based execution with `max_turns` limit<br>• Hub-and-spoke escalation pattern (specialists return to triage)<br>• No DAG/workflow engine—pure conversational flow<br>• Single active agent per turn (no parallel agent execution) |
| **State/persistence** | • **Completely stateless** between calls<br>• Explicit state passing via `messages` + `context_variables` dict<br>• Context variables merge across agent handoffs<br>• Dynamic instructions from context (functions receiving `context_variables`)<br>• No database, no sessions, no checkpointing |
| **HITL controls** | • **None**—fully manual wrapping required<br>• Example REPL shows basic user-in-loop pattern<br>• No approval gates, confirmations, or escalation mechanisms<br>• Applications must implement HITL as custom tools |
| **Sandboxing** | • **None**—all tools execute in-process<br>• No resource limits, allowlists, or permission systems<br>• No input validation beyond type hints<br>• Zero execution isolation |
| **Observability** | • Minimal: `debug_print()` utility for timestamped logs<br>• Streaming delimiter events mark agent transitions<br>• Response object returns full message history<br>• No tracing, metrics, lineage, or structured logging<br>• Example code includes colored pretty-printing for demos |
| **Evaluation** | • Example-based: JSON test cases with expected function calls<br>• Pytest runner compares actual vs. expected tool invocations<br>• Conversation quality via manual inspection<br>• No generic eval framework—purely example code |
| **Extensibility** | • Function-first: any callable can be a tool<br>• Dynamic instructions via callable receiving context<br>• Unstructured `context_variables` dict<br>• No plugin system, middleware, or lifecycle hooks<br>• Hardcoded to OpenAI (no provider abstraction)<br>• 300-line reference implementation meant to be forked |

## 9) Evidence links

- **Repository**: https://github.com/openai/swarm (21k stars, MIT license)
- **Core implementation**: https://github.com/openai/swarm/blob/main/swarm/core.py
- **Type definitions**: https://github.com/openai/swarm/blob/main/swarm/types.py
- **Utilities (schema conversion)**: https://github.com/openai/swarm/blob/main/swarm/util.py
- **REPL implementation**: https://github.com/openai/swarm/blob/main/swarm/repl/repl.py
- **Triage example**: https://github.com/openai/swarm/tree/main/examples/triage_agent
- **Airline example** (hierarchical handoffs): https://github.com/openai/swarm/tree/main/examples/airline
- **Orchestration cookbook**: https://cookbook.openai.com/examples/orchestrating_agents
- **README**: https://raw.githubusercontent.com/openai/swarm/main/README.md
