# Competitive Analysis: Agency Swarm
**Date**: 2026-01-20  
**Repository**: https://github.com/VRSEN/agency-swarm  
**Analyst**: Automated Competitive Analysis  
**Status**: Complete

---

## Executive Summary

Agency Swarm is a mature, production-ready Python framework for building multi-agent applications, built on top of the OpenAI Agents SDK. The framework emphasizes modeling AI automation after real-world organizational structures—defining agents with roles like CEO, Developer, and Virtual Assistant that communicate through explicit, directional flows.

The framework's core philosophy of treating agent systems as "agencies" with defined hierarchies and communication patterns directly aligns with AGENT-33's orchestration goals. However, Agency Swarm takes an implementation-first approach with Python code, while AGENT-33 maintains a specification/documentation-first stance. This creates complementary opportunities: AGENT-33 can adopt Agency Swarm's proven patterns as model-agnostic specifications while preserving its evidence-first, auditable approach.

Key differentiators from AGENT-33's current capabilities include: (1) explicit communication flow graphs with directional constraints, (2) handoff vs. orchestrator-worker pattern taxonomy, (3) type-safe tool definitions with Pydantic validation, (4) built-in guardrails for input/output validation, (5) MCP server integration, and (6) comprehensive observability hooks. These patterns could significantly enhance AGENT-33's orchestration specifications while maintaining model-agnosticism.

---

## Repository Overview

### Purpose

Agency Swarm provides a framework for building collaborative AI agent systems modeled after real-world organizational structures. The framework abstracts multi-agent coordination through:

- **Agency**: A container for agents with defined communication topologies
- **Agent**: Individual AI entities with specific roles, instructions, and tools
- **Communication Flows**: Explicit, directional paths defining which agents can communicate
- **Tools**: Type-safe, Pydantic-validated functions agents can invoke

### Technology Stack

| Component | Technology |
|-----------|------------|
| Core Language | Python 3.12+ |
| AI SDK | OpenAI Agents SDK / Responses API |
| Type System | Pydantic v2 for tool validation |
| Model Backends | OpenAI native; LiteLLM router for Anthropic, Google, Grok, Azure, OpenRouter |
| Testing | pytest with 92% coverage |
| Build System | Hatch, UV, Makefile |
| Documentation | MDX with Mintlify |

### Key Concepts

| Concept | Description | AGENT-33 Equivalent |
|---------|-------------|---------------------|
| **Agency** | Container orchestrating multiple agents with defined communication flows | Orchestrator context |
| **Agent** | Individual AI entity with role, instructions, tools, model config | Agent definition in `core/orchestrator/agents/` |
| **Communication Flow** | Directional graph of allowed agent-to-agent communication | Handoff protocol (PLAN/TASKS/STATUS) |
| **SendMessage** | Built-in tool for inter-agent communication | Handoff artifacts |
| **Handoff** | Transfer of control to another agent with full context | Role transition |
| **MasterContext** | Shared state accessible across all agents in an agency | Session state (implicit) |
| **Guardrails** | Input/output validation via specialized agents | Two-layer review |
| **Thread** | Isolated conversation state per communication path | Session logs |

---

## Feature Inventory

### Feature 1: Directional Communication Flow Graph

**Description**  
Agency Swarm defines agent communication as a directed graph using the `>` operator. Each edge `(sender > receiver)` creates a `SendMessage` tool on the sender that can invoke the receiver. This prevents arbitrary agent-to-agent chatter and enforces architectural intent.

```python
agency = Agency(
    ceo,  # Entry point
    communication_flows=[
        ceo > developer,     # CEO can send messages to Developer
        ceo > analyst,       # CEO can send messages to Analyst
        developer > qa,      # Developer can send to QA
    ]
)
```

**How it Applies to AGENT-33**  
AGENT-33's handoff protocol (PLAN, TASKS, STATUS) is linear; it lacks a formal graph of allowed transitions. Adding a communication topology specification would:
- Prevent unauthorized role transitions
- Document allowed delegation paths
- Enable static validation of workflow definitions

**Implementation Pattern**
```yaml
# core/schemas/communication-flow.schema.yaml
type: object
properties:
  nodes:
    type: array
    items:
      type: string
      description: Agent role identifier
  edges:
    type: array
    items:
      type: object
      properties:
        from: { type: string }
        to: { type: string }
        mode:
          type: string
          enum: [send_message, handoff]
      required: [from, to, mode]
```

**Priority**: High  
**Effort**: Medium (2-3 days)  
**Impact**: Enables enforcement of orchestration topology; prevents invalid transitions

---

### Feature 2: Handoff vs. Orchestrator-Worker Pattern Taxonomy

**Description**  
Agency Swarm distinguishes two orchestration patterns:

| Pattern | Control Flow | Context Transfer | Use Case |
|---------|--------------|------------------|----------|
| **Handoff** | Full transfer to receiver; sender exits | Full conversation history | Sequential workflows, user-facing transitions |
| **Orchestrator-Worker** | Sender retains control; receives results | Task context only | Parallel delegation, result aggregation |

```python
# Handoff pattern
communication_flows=[
    (triage_agent > specialist, Handoff),
]

# Orchestrator-Worker pattern (default)
communication_flows=[
    portfolio_manager > risk_analyst,
    portfolio_manager > report_generator,
]
```

**How it Applies to AGENT-33**  
AGENT-33's roles (Director, Orchestrator, Worker) imply this taxonomy but don't formalize it. Explicit pattern classification would:
- Clarify when Orchestrator retains control vs. exits
- Document expected return semantics
- Enable pattern-specific validation

**Implementation Pattern**
```markdown
# core/orchestrator/ORCHESTRATION_PATTERNS.md

## Pattern: Handoff
- **Control**: Transfers to receiver; sender terminates
- **Context**: Full session history included
- **Return**: No return to sender expected
- **Trigger**: User-facing escalation, role specialization

## Pattern: Orchestrator-Worker  
- **Control**: Sender retains; awaits response
- **Context**: Task-scoped message only
- **Return**: Structured output expected
- **Trigger**: Parallel decomposition, specialist consultation
```

**Priority**: High  
**Effort**: Low (1 day)  
**Impact**: Clarifies orchestration semantics; reduces ambiguity in role definitions

---

### Feature 3: Type-Safe Tool Definitions with Pydantic

**Description**  
Agency Swarm tools are defined using Pydantic models or the `@function_tool` decorator, providing automatic argument validation, type coercion, and schema generation. Tools can specify structured output types.

```python
from pydantic import BaseModel, Field
from agency_swarm import function_tool

class RiskAssessment(BaseModel):
    risk_level: str = Field(..., description="Low/Moderate/High")
    risk_score: int = Field(..., ge=1, le=10)
    key_risks: list[str]

@function_tool
async def analyze_risk(symbol: str) -> RiskAssessment:
    """Analyze investment risk for a stock symbol."""
    # Implementation
    return RiskAssessment(...)
```

**How it Applies to AGENT-33**  
AGENT-33's `core/schemas/` contains JSON schemas for orchestrator and workflow definitions, but tool schemas are implicit. Formalizing tool interfaces would:
- Enable cross-implementation validation
- Document expected inputs/outputs for tool registry
- Support code generation for implementers

**Implementation Pattern**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Tool Definition",
  "type": "object",
  "properties": {
    "name": { "type": "string" },
    "description": { "type": "string" },
    "parameters": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "type": { "type": "string" },
          "description": { "type": "string" },
          "required": { "type": "boolean" }
        }
      }
    },
    "returns": {
      "type": "object",
      "properties": {
        "type": { "type": "string" },
        "schema": { "$ref": "#/definitions/JsonSchema" }
      }
    }
  }
}
```

**Priority**: High  
**Effort**: Medium (2 days)  
**Impact**: Enables tool registry validation; supports multi-implementation compatibility

---

### Feature 4: Input/Output Guardrails

**Description**  
Agency Swarm supports declarative guardrails—specialized agents or functions that validate input before processing or output before delivery. Guardrails can trigger tripwires to block execution or inject guidance.

```python
from agency_swarm import input_guardrail, GuardrailFunctionOutput

@input_guardrail
async def require_support_topic(context, agent, user_input):
    decision = await guardrail_agent.get_response(user_input)
    if not decision.is_relevant:
        return GuardrailFunctionOutput(
            output_info="Only support questions allowed.",
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(tripwire_triggered=False)

support_agent = Agent(
    name="SupportAgent",
    input_guardrails=[require_support_topic],
    throw_input_guardrail_error=False,  # Return guidance instead of error
)
```

**How it Applies to AGENT-33**  
AGENT-33's `TWO_LAYER_REVIEW.md` describes review gates but lacks executable guardrail specifications. Formalizing guardrails would:
- Enable pre-execution validation specifications
- Document enforcement points in workflow
- Support security hardening patterns

**Implementation Pattern**
```yaml
# core/orchestrator/guardrails/input-guardrail.schema.yaml
type: object
properties:
  name: { type: string }
  type: { enum: [input, output] }
  agent_ref: { type: string, description: "Agent role for validation" }
  tripwire_action:
    type: string
    enum: [block, warn, inject_guidance]
  on_trigger:
    type: object
    properties:
      message: { type: string }
      log_severity: { enum: [info, warning, error] }
```

**Priority**: High  
**Effort**: Medium (2-3 days)  
**Impact**: Formalizes security enforcement; enables automated policy compliance

---

### Feature 5: Shared Context (MasterContext)

**Description**  
Agency Swarm provides `MasterContext`—a typed, shared state object accessible by all agents within an agency. Tools can read/write context to share data across agent boundaries without explicit message passing.

```python
from agency_swarm import MasterContext, RunContextWrapper, function_tool

@function_tool
async def store_data(ctx: RunContextWrapper[MasterContext], key: str, value: str):
    ctx.context.set(key, value)
    return f"Stored {key}"

@function_tool
async def get_data(ctx: RunContextWrapper[MasterContext], key: str):
    return ctx.context.get(key, "Not found")
```

**How it Applies to AGENT-33**  
AGENT-33's handoff protocol passes artifacts explicitly (STATUS, DECISIONS), but lacks a formal shared context specification. Adding context semantics would:
- Document which state persists across handoffs
- Define context isolation boundaries
- Support stateful workflow patterns

**Implementation Pattern**
```markdown
# core/orchestrator/context/CONTEXT_PROTOCOL.md

## Context Scope
- **Session Context**: Persists across all agent interactions in a session
- **Agent Context**: Local to current agent execution
- **Handoff Context**: Transferred on role transition

## Context Operations
| Operation | Scope | Persistence |
|-----------|-------|-------------|
| `set(key, value)` | Session | Until session end |
| `get(key)` | Session | Read-only |
| `handoff_context()` | Handoff | Serialized to recipient |

## Reserved Keys
- `session_id`: Unique session identifier
- `current_role`: Active agent role
- `trace_id`: Observability correlation ID
```

**Priority**: Medium  
**Effort**: Low (1 day)  
**Impact**: Enables stateful workflow specifications; clarifies data flow

---

### Feature 6: Structured Output Types

**Description**  
Agents can declare an `output_type` (Pydantic model) that constrains their response format. The framework enforces schema compliance, enabling reliable downstream processing.

```python
class InvestmentReport(BaseModel):
    executive_summary: str
    risk_analysis: str
    recommendation: str = Field(..., pattern="^(Buy|Hold|Sell)$")

report_agent = Agent(
    name="ReportGenerator",
    output_type=InvestmentReport,
)
```

**How it Applies to AGENT-33**  
AGENT-33's handoff artifacts (PLAN, TASKS, STATUS) have implicit structures but no enforced schemas. Adding output type specifications would:
- Enable validation of handoff content
- Document expected artifact formats
- Support automated handoff parsing

**Implementation Pattern**
```json
{
  "$id": "handoff-status.schema.json",
  "type": "object",
  "required": ["completed", "pending", "blockers"],
  "properties": {
    "completed": {
      "type": "array",
      "items": { "type": "string" }
    },
    "pending": {
      "type": "array",
      "items": { "type": "string" }
    },
    "blockers": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "description": { "type": "string" },
          "severity": { "enum": ["blocker", "major", "minor"] }
        }
      }
    }
  }
}
```

**Priority**: Medium  
**Effort**: Medium (2 days)  
**Impact**: Enables handoff validation; supports automated workflow parsing

---

### Feature 7: MCP Server Integration

**Description**  
Agency Swarm supports Model Context Protocol (MCP) servers—both local (stdio) and remote (SSE)—allowing agents to use externally hosted tools. This enables tool sharing across implementations and organizations.

```python
from agents.mcp.server import MCPServerStdio
from agency_swarm import HostedMCPTool

# Local MCP server
local_server = MCPServerStdio(command="python", args=["server.py"])

# Remote MCP server
remote_tool = HostedMCPTool(
    tool_config={
        "type": "mcp",
        "server_url": "https://tools.example.com/sse",
        "require_approval": "never",
    }
)

agent = Agent(
    mcp_servers=[local_server],
    tools=[remote_tool],
)
```

**How it Applies to AGENT-33**  
AGENT-33's `TOOL_REGISTRY_CHANGE_CONTROL.md` manages tool governance but doesn't specify integration protocols. MCP adoption would:
- Enable cross-system tool federation
- Support external tool providers
- Align with emerging industry standard

**Implementation Pattern**
```markdown
# core/orchestrator/tools/MCP_INTEGRATION.md

## MCP Server Types
| Type | Transport | Use Case |
|------|-----------|----------|
| Stdio | Process pipe | Local tools, CLI wrappers |
| SSE | HTTP streaming | Remote services, shared tools |

## Configuration Schema
```yaml
mcp_servers:
  - name: local-tools
    type: stdio
    command: ["python", "tools/server.py"]
  - name: remote-analytics
    type: sse
    url: https://analytics.example.com/mcp
    auth:
      type: bearer
      token_env: ANALYTICS_TOKEN
```

**Priority**: Medium  
**Effort**: High (3-5 days)  
**Impact**: Enables tool federation; supports ecosystem integration

---

### Feature 8: Observability and Tracing

**Description**  
Agency Swarm provides built-in tracing via OpenAI's native tracing, plus integrations with Langfuse and AgentOps. Traces capture agent interactions, tool calls, and timing for debugging and analytics.

```python
from agency_swarm import trace
from langfuse import observe

# OpenAI native tracing
with trace("Investment Analysis"):
    response = await agency.get_response(message)

# Langfuse integration
@observe()
async def analyze():
    return await agency.get_response(message)
```

**How it Applies to AGENT-33**  
AGENT-33's `TRACE_SCHEMA.md` defines trace structures but lacks integration specifications. Formalizing observability would:
- Document trace correlation patterns
- Specify required trace fields
- Enable vendor-agnostic tracing

**Implementation Pattern**
```json
{
  "$id": "trace-event.schema.json",
  "type": "object",
  "required": ["trace_id", "span_id", "event_type", "timestamp"],
  "properties": {
    "trace_id": { "type": "string", "format": "uuid" },
    "span_id": { "type": "string", "format": "uuid" },
    "parent_span_id": { "type": "string", "format": "uuid" },
    "event_type": {
      "enum": ["agent_start", "agent_end", "tool_call", "handoff", "error"]
    },
    "timestamp": { "type": "string", "format": "date-time" },
    "agent_role": { "type": "string" },
    "duration_ms": { "type": "integer" },
    "metadata": { "type": "object" }
  }
}
```

**Priority**: Medium  
**Effort**: Low (1 day)  
**Impact**: Standardizes trace format; enables analytics integration

---

### Feature 9: Thread Persistence and Session Management

**Description**  
Agency Swarm supports flexible thread persistence via callbacks, enabling conversation state to survive process restarts. Each communication path gets isolated thread state.

```python
agency = Agency(
    agent,
    load_threads_callback=lambda: load_from_db(chat_id),
    save_threads_callback=lambda msgs: save_to_db(chat_id, msgs),
)
```

**How it Applies to AGENT-33**  
AGENT-33's session logs exist as documentation but lack a formal persistence specification. Formalizing persistence would:
- Document session state requirements
- Specify recovery semantics
- Enable cross-session continuity

**Implementation Pattern**
```yaml
# core/orchestrator/sessions/PERSISTENCE_PROTOCOL.md

## Session State Components
| Component | Persistence | Recovery |
|-----------|-------------|----------|
| Message History | Required | Full replay |
| Context Variables | Required | Restore to context |
| Pending Tasks | Required | Resume execution |
| Trace Spans | Optional | Read-only archive |

## Callback Specification
- `load_session(session_id) -> SessionState`
- `save_session(session_id, state) -> void`
- `list_sessions(filter) -> SessionId[]`
```

**Priority**: Low  
**Effort**: Low (1 day)  
**Impact**: Enables stateful workflow recovery; supports long-running sessions

---

### Feature 10: Handoff Reminders and Context Injection

**Description**  
When control transfers via Handoff, Agency Swarm can inject reminder messages into the receiving agent's context. This ensures recipients have role-appropriate guidance.

```python
dev_lead = Agent(
    name="DevLead",
    # Reminder shown when DevLead receives a handoff
    handoff_reminder="Compliance review complete. Confirm deployment steps.",
)

# Custom handoff with no reminder
class NoReminderHandoff(Handoff):
    add_reminder = False
```

**How it Applies to AGENT-33**  
AGENT-33's handoff protocol includes PRIORITIES but lacks recipient-specific context injection. Adding reminder specifications would:
- Document role transition context
- Enable context-aware handoffs
- Reduce recipient confusion

**Implementation Pattern**
```markdown
# Handoff Reminder Specification

## Default Reminder Template
```
Transfer completed. You are {recipient_role}.
Previous context: {summary}
Your immediate priorities: {priorities}
```

## Reminder Configuration
| Option | Default | Description |
|--------|---------|-------------|
| add_reminder | true | Include system reminder on handoff |
| reminder_template | (default) | Custom reminder format |
| include_summary | true | Auto-summarize prior context |
```

**Priority**: Low  
**Effort**: Low (0.5 days)  
**Impact**: Improves handoff clarity; reduces context loss

---

### Feature 11: Agency Visualization

**Description**  
Agency Swarm can generate visual representations of agent topologies, showing communication flows and agent relationships. This aids debugging and documentation.

```python
# Generate Mermaid diagram
agency.get_visualization(format="mermaid")

# Outputs:
# graph TD
#     CEO --> Developer
#     CEO --> Analyst
#     Developer --> QA
```

**How it Applies to AGENT-33**  
AGENT-33's orchestration documentation is text-based. Adding visualization specifications would:
- Enable automated diagram generation
- Improve documentation accessibility
- Support topology validation

**Implementation Pattern**
```markdown
# core/orchestrator/viz/VISUALIZATION_SPEC.md

## Output Formats
| Format | Use Case | Tool |
|--------|----------|------|
| Mermaid | Markdown docs | Native render |
| DOT | Advanced layout | Graphviz |
| JSON | Programmatic use | D3.js, etc. |

## Diagram Elements
- Nodes: Agent roles (rectangle)
- Edges: Communication flows (arrow)
- Edge Labels: Pattern type (handoff/send)
- Node Color: Entry point (green), worker (blue)
```

**Priority**: Low  
**Effort**: Low (1 day)  
**Impact**: Improves documentation; aids topology debugging

---

### Feature 12: OpenAPI Schema Import for Tools

**Description**  
Agency Swarm can auto-generate tools from OpenAPI specifications, enabling rapid integration with existing APIs.

```python
from agency_swarm.tools import ToolFactory

tools = ToolFactory.from_openapi_schema(
    requests.get("https://api.example.com/openapi.json").json()
)

agent = Agent(tools=tools)
```

**How it Applies to AGENT-33**  
AGENT-33's tool governance could benefit from standardized import specifications. OpenAPI integration would:
- Enable automated tool onboarding
- Ensure API compatibility
- Reduce manual tool definition effort

**Implementation Pattern**
```markdown
# core/orchestrator/tools/OPENAPI_IMPORT.md

## Import Process
1. Fetch OpenAPI spec (JSON or YAML)
2. Extract operation definitions
3. Generate tool schemas with:
   - Name: `{operationId}` or `{path}_{method}`
   - Parameters: From path/query/body params
   - Returns: From response schema
4. Register in tool registry with source reference

## Validation Requirements
- Schema version: OpenAPI 3.0+
- Required: operationId or unique path+method
- Security: Document auth requirements
```

**Priority**: Low  
**Effort**: Medium (2 days)  
**Impact**: Accelerates tool onboarding; supports API ecosystem

---

## Recommendations

### Recommendation 1: Adopt Communication Flow Graph Specification

**Rationale**: Agency Swarm's directed graph model for agent communication is more expressive than AGENT-33's implicit role transitions. A formal graph specification enables static validation, visualization, and enforcement.

**Implementation Steps**:
1. Create `core/schemas/communication-flow.schema.json`
2. Update `core/orchestrator/README.md` with flow syntax
3. Add validation script in `scripts/`
4. Document in `core/orchestrator/COMMUNICATION_FLOWS.md`

**Example**:
```yaml
# workflows/code-review.flow.yaml
name: code-review-workflow
entry_point: Director
nodes:
  - Director
  - Orchestrator
  - Implementer
  - Reviewer
edges:
  - { from: Director, to: Orchestrator, mode: handoff }
  - { from: Orchestrator, to: Implementer, mode: send_message }
  - { from: Orchestrator, to: Reviewer, mode: send_message }
  - { from: Reviewer, to: Orchestrator, mode: send_message }
```

---

### Recommendation 2: Formalize Orchestration Pattern Taxonomy

**Rationale**: Explicit pattern classification (Handoff vs. Orchestrator-Worker) removes ambiguity from role transitions and enables pattern-specific tooling.

**Implementation Steps**:
1. Create `core/orchestrator/ORCHESTRATION_PATTERNS.md`
2. Update role definitions with pattern annotations
3. Add pattern field to workflow schema
4. Document decision criteria

---

### Recommendation 3: Add Guardrail Specification Framework

**Rationale**: Agency Swarm's guardrails map directly to AGENT-33's review-driven philosophy. Formalizing guardrails as specifications enables automated enforcement.

**Implementation Steps**:
1. Create `core/orchestrator/guardrails/` directory
2. Define `guardrail.schema.json`
3. Add guardrail references to workflow definitions
4. Document integration with `TWO_LAYER_REVIEW.md`

---

### Recommendation 4: Enhance Tool Schema with Return Types

**Rationale**: Current tool definitions lack output specifications. Adding return type schemas enables end-to-end validation.

**Implementation Steps**:
1. Extend `core/schemas/tool.schema.json` with `returns` property
2. Update tool registry entries
3. Add validation for tool outputs
4. Document in `core/orchestrator/TOOL_GOVERNANCE.md`

---

### Recommendation 5: Standardize Trace Event Schema

**Rationale**: Agency Swarm's observability integrations demonstrate the value of standardized tracing. A formal trace schema enables vendor-agnostic analytics.

**Implementation Steps**:
1. Update `core/orchestrator/TRACE_SCHEMA.md` with JSON schema
2. Define required vs. optional fields
3. Add correlation ID requirements
4. Document integration patterns

---

### Recommendation 6: Add Context Sharing Protocol

**Rationale**: Explicit context semantics clarify data flow across agent boundaries, reducing handoff confusion.

**Implementation Steps**:
1. Create `core/orchestrator/context/CONTEXT_PROTOCOL.md`
2. Define context scope levels
3. Add context requirements to handoff artifacts
4. Document reserved context keys

---

### Recommendation 7: Document MCP Integration Path

**Rationale**: MCP is an emerging standard for tool federation. Early specification positions AGENT-33 for ecosystem integration.

**Implementation Steps**:
1. Research MCP specification
2. Create `core/orchestrator/tools/MCP_INTEGRATION.md`
3. Define configuration schema
4. Add to future roadmap

---

### Recommendation 8: Add Workflow Visualization Specification

**Rationale**: Visual representations improve documentation accessibility and enable automated diagram generation.

**Implementation Steps**:
1. Define Mermaid output format for workflows
2. Add visualization section to workflow documentation
3. Create example diagrams for existing workflows
4. Document generation process

---

## Backlog Items Generated

| ID | Title | Priority | Effort | Impact |
|----|-------|----------|--------|--------|
| CA-001 | Define communication flow graph schema | High | 2d | Enables topology validation and enforcement |
| CA-002 | Document Handoff vs Orchestrator-Worker patterns | High | 1d | Clarifies orchestration semantics |
| CA-003 | Add guardrail specification framework | High | 3d | Formalizes security enforcement points |
| CA-004 | Extend tool schema with return types | High | 2d | Enables end-to-end validation |
| CA-005 | Standardize trace event JSON schema | Medium | 1d | Enables vendor-agnostic observability |
| CA-006 | Create context sharing protocol | Medium | 1d | Clarifies state across handoffs |
| CA-007 | Add structured output schemas for handoff artifacts | Medium | 2d | Enables automated handoff parsing |
| CA-008 | Document MCP integration specification | Medium | 3d | Positions for tool federation |
| CA-009 | Add session persistence specification | Low | 1d | Enables stateful workflow recovery |
| CA-010 | Define handoff reminder templates | Low | 0.5d | Improves handoff context transfer |
| CA-011 | Create workflow visualization specification | Low | 1d | Improves documentation accessibility |
| CA-012 | Add OpenAPI import specification for tools | Low | 2d | Accelerates tool onboarding |

---

## Summary Matrix

| Dimension | Agency Swarm | AGENT-33 | Gap | Priority |
|-----------|--------------|----------|-----|----------|
| **Communication Model** | Directed graph with `>` operator | Implicit role transitions | Formalize graph schema | High |
| **Orchestration Patterns** | Handoff vs Orchestrator-Worker taxonomy | Implied but not formalized | Document patterns | High |
| **Tool Definitions** | Pydantic with full type safety | JSON schemas (no return types) | Add return type specs | High |
| **Guardrails** | First-class input/output validation | Two-layer review (manual) | Add guardrail specs | High |
| **Shared Context** | MasterContext with typed access | Handoff artifacts only | Add context protocol | Medium |
| **Output Schemas** | Pydantic output_type enforcement | Implicit artifact structure | Add artifact schemas | Medium |
| **Observability** | Multi-vendor tracing integrations | TRACE_SCHEMA.md (partial) | Complete trace schema | Medium |
| **Tool Federation** | MCP server integration | None | Research and document | Medium |
| **Session Persistence** | Callback-based persistence | Session logs (informal) | Add persistence spec | Low |
| **Visualization** | Mermaid/DOT generation | Text-only documentation | Add viz specification | Low |
| **Model Agnosticism** | LiteLLM router for multi-model | Core principle | ✓ Aligned | - |
| **Evidence Capture** | Via observability integrations | Core principle | ✓ Aligned | - |

---

## Appendix: Key Source Files Analyzed

| File | Purpose |
|------|---------|
| `README.md` | Framework overview and getting started |
| `AGENTS.md` | AI coding agent guidance (comprehensive) |
| `examples/multi_agent_workflow.py` | Orchestrator-Worker pattern |
| `examples/handoffs.py` | Handoff pattern with reminders |
| `examples/guardrails_input.py` | Input validation guardrails |
| `examples/agency_context.py` | Shared context usage |
| `examples/mcp_servers.py` | MCP integration patterns |
| `examples/observability.py` | Tracing integrations |
| `examples/custom_persistence.py` | Thread persistence |
| `docs/core-framework/agencies/communication-flows.mdx` | Flow documentation |
| `src/agency_swarm/` | Core module structure |

---

*This analysis was generated to inform AGENT-33's competitive positioning and identify integration opportunities. Recommendations prioritize model-agnostic specifications aligned with AGENT-33's documentation-first philosophy.*
