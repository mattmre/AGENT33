# Competitive Analysis: OpenAI Swarm

**Date**: 2026-01-20  
**Repository**: https://github.com/openai/swarm  
**Analyst**: AGENT-33 System  
**Status**: Complete

---

## Executive Summary

OpenAI Swarm is an experimental, educational framework for lightweight multi-agent orchestration. The project has been superseded by the production-ready OpenAI Agents SDK, but its core design patterns remain highly instructive. Swarm's philosophy emphasizes minimal primitives (Agents and Handoffs), stateless execution, and composable workflows—principles that align strongly with AGENT-33's model-agnostic, evidence-first approach.

The most valuable patterns for AGENT-33 are Swarm's handoff mechanism (agent-to-agent delegation via function returns), context variable propagation, automatic function-to-JSON schema conversion, and streaming with agent boundary delimiters. These patterns provide concrete implementation specifications that can enhance AGENT-33's orchestration documentation without coupling to any specific model provider.

Adopting Swarm patterns would strengthen AGENT-33's specifications in three key areas: (1) formalizing agent handoff protocols with explicit state transfer, (2) adding triage/routing patterns as a first-class workflow primitive, and (3) establishing evaluation frameworks for multi-agent systems. The effort required is moderate since AGENT-33 is documentation-only—the task is specification, not implementation.

---

## Repository Overview

### Purpose

Swarm is designed to teach multi-agent patterns through working code. Key goals:
- **Coordination**: Enable multiple agents to collaborate on complex tasks
- **Execution**: Lightweight runtime with minimal dependencies
- **Testability**: Stateless design enables deterministic unit testing
- **Customizability**: Simple primitives allow flexible composition

### Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| LLM Client | OpenAI Python SDK |
| Type System | Pydantic BaseModel |
| Execution | Synchronous + Streaming |
| State | Stateless between calls |

### Key Concepts

1. **Agent**: A composable unit with instructions (system prompt), functions (tools), and model configuration
2. **Handoff**: A function that returns another Agent, triggering context switch
3. **Context Variables**: Shared mutable state passed through the execution chain
4. **Result**: A structured return type carrying value, agent, and context updates
5. **Function-to-JSON**: Automatic schema generation from Python type hints

---

## Feature Inventory

### F-01: Agent Primitive Definition

**Description**  
An Agent is defined with minimal fields: name, model, instructions, functions, tool_choice, and parallel_tool_calls. Instructions can be static strings or callable functions that receive context variables.

**How It Applies to AGENT-33**  
AGENT-33 defines roles (Director, Orchestrator, Worker, etc.) but lacks a formal Agent schema. Swarm's primitive provides a concrete specification for agent definition that is model-agnostic when abstracted from OpenAI specifics.

**Implementation Pattern**
```yaml
# core/schemas/agent.schema.yaml
Agent:
  type: object
  required: [name, instructions]
  properties:
    name:
      type: string
      description: Unique agent identifier
    instructions:
      oneOf:
        - type: string
        - type: object
          properties:
            template: { type: string }
            context_params: { type: array, items: { type: string } }
    functions:
      type: array
      items: { $ref: '#/Function' }
    model:
      type: string
      default: "model-agnostic"
    parallel_tool_calls:
      type: boolean
      default: true
```

**Priority**: High  
**Effort**: 2 days

---

### F-02: Handoff Protocol (Agent-to-Agent Delegation)

**Description**  
When a function returns an Agent object, execution transfers to that agent. The system prompt switches, but conversation history is preserved. This enables dynamic routing without explicit orchestration code.

**How It Applies to AGENT-33**  
AGENT-33's handoff protocol (PLAN, TASKS, STATUS, DECISIONS, PRIORITIES) is procedural. Swarm's functional handoff pattern provides a cleaner specification for agent transitions that can be documented as a workflow primitive.

**Implementation Pattern**
```yaml
# core/schemas/handoff.schema.yaml
Handoff:
  type: object
  required: [from_agent, to_agent]
  properties:
    from_agent: { type: string }
    to_agent: { type: string }
    trigger:
      type: string
      enum: [function_return, explicit_transfer, error_escalation]
    context_transfer:
      type: object
      properties:
        preserve_history: { type: boolean, default: true }
        merge_context: { type: boolean, default: true }
        clear_instructions: { type: boolean, default: true }
```

**Documentation Pattern**
```markdown
## Handoff Execution Flow
1. Agent A calls function `transfer_to_B()`
2. Function returns Agent B object
3. Runtime updates active_agent to Agent B
4. System prompt switches to Agent B's instructions
5. Conversation history remains intact
6. Next completion uses Agent B's configuration
```

**Priority**: High  
**Effort**: 3 days

---

### F-03: Context Variable Propagation

**Description**  
Context variables are a shared dictionary passed to all agents and functions. Functions can read context_variables as a parameter and update them via Result objects. Variables persist across handoffs and agent switches.

**How It Applies to AGENT-33**  
AGENT-33's evidence capture and state tracking could benefit from a formal context variable specification. This pattern enables traceability of shared state across agent boundaries.

**Implementation Pattern**
```yaml
# core/schemas/context.schema.yaml
ContextVariables:
  type: object
  additionalProperties: true
  description: |
    Mutable shared state accessible to all agents and functions.
    Updates via Result.context_variables are merged, not replaced.
  examples:
    - user_name: "John"
      session_id: "abc123"
      permissions: ["read", "write"]
```

**Function Access Pattern**
```python
# Documentation example: how functions receive context
def my_function(context_variables, other_param):
    """
    When a function declares context_variables as a parameter,
    the runtime injects the current context automatically.
    The parameter is hidden from the LLM's function schema.
    """
    user = context_variables.get("user_name", "unknown")
    return f"Hello, {user}"
```

**Priority**: High  
**Effort**: 2 days

---

### F-04: Result Object for Composite Returns

**Description**  
The Result class encapsulates function returns with three optional fields: value (string response), agent (handoff target), and context_variables (state updates). This allows a single function call to perform multiple state transitions.

**How It Applies to AGENT-33**  
AGENT-33 could adopt Result as the standard return type for workflow steps, ensuring consistent structure for value returns, agent transitions, and context updates.

**Implementation Pattern**
```yaml
# core/schemas/result.schema.yaml
Result:
  type: object
  properties:
    value:
      type: string
      description: The response value to append to conversation
    agent:
      $ref: '#/Agent'
      description: Optional handoff target
    context_variables:
      type: object
      description: Context updates to merge with current state
  anyOf:
    - required: [value]
    - required: [agent]
    - required: [context_variables]
```

**Priority**: Medium  
**Effort**: 1 day

---

### F-05: Function-to-JSON Schema Conversion

**Description**  
Swarm automatically converts Python functions into JSON schemas for tool calling. It extracts: function name, docstring (as description), parameter types (from type hints), required parameters (those without defaults), and hides internal parameters like context_variables.

**How It Applies to AGENT-33**  
AGENT-33 could document a standard specification for function schema generation, enabling consistent tool definitions across implementations regardless of runtime language.

**Implementation Pattern**
```yaml
# core/schemas/function-schema.schema.yaml
FunctionSchema:
  type: object
  required: [type, function]
  properties:
    type:
      const: "function"
    function:
      type: object
      required: [name, parameters]
      properties:
        name: { type: string }
        description: { type: string }
        parameters:
          type: object
          required: [type, properties, required]
          properties:
            type: { const: "object" }
            properties:
              type: object
              additionalProperties:
                type: object
                properties:
                  type: { type: string }
            required:
              type: array
              items: { type: string }
```

**Type Mapping**
```yaml
TypeMapping:
  string: ["str", "String", "text"]
  integer: ["int", "Integer", "i32", "i64"]
  number: ["float", "double", "Number"]
  boolean: ["bool", "Boolean"]
  array: ["list", "List", "Array", "[]"]
  object: ["dict", "Dict", "object", "{}"]
  null: ["None", "null", "nil"]
```

**Priority**: High  
**Effort**: 2 days

---

### F-06: Triage Agent Pattern

**Description**  
A triage agent acts as an intelligent router that analyzes user intent and transfers to specialized agents. Swarm's examples show triage agents with transfer functions to sales, refunds, support, and other domain-specific agents.

**How It Applies to AGENT-33**  
AGENT-33's Orchestrator role performs similar routing. Documenting the triage pattern formally would provide a reusable workflow template for multi-domain agent systems.

**Implementation Pattern**
```yaml
# core/workflows/triage-pattern.yaml
TriageWorkflow:
  entry_agent: triage
  agents:
    triage:
      instructions: |
        Analyze the user's request and determine which specialist 
        is best suited to handle it. Transfer the conversation 
        to the appropriate agent.
      functions:
        - transfer_to_sales
        - transfer_to_refunds
        - transfer_to_support
    sales:
      instructions: "Handle sales inquiries..."
      functions: [transfer_back_to_triage]
    refunds:
      instructions: "Handle refund requests..."
      functions: [process_refund, transfer_back_to_triage]
    support:
      instructions: "Handle support issues..."
      functions: [escalate_to_human, transfer_back_to_triage]
  routing:
    bidirectional: true
    fallback: triage
```

**Priority**: High  
**Effort**: 3 days

---

### F-07: Streaming with Agent Boundary Delimiters

**Description**  
Swarm's streaming mode emits special delimiter events (`{"delim":"start"}` and `{"delim":"end"}`) to mark agent message boundaries. A final `{"response": Response}` event provides the complete aggregated response.

**How It Applies to AGENT-33**  
AGENT-33's logging and evidence capture would benefit from standardized stream event schemas. Delimiter events enable real-time UI updates and audit logging of agent boundaries.

**Implementation Pattern**
```yaml
# core/schemas/stream-events.schema.yaml
StreamEvent:
  oneOf:
    - $ref: '#/DelimiterEvent'
    - $ref: '#/DeltaEvent'
    - $ref: '#/ResponseEvent'

DelimiterEvent:
  type: object
  required: [delim]
  properties:
    delim:
      type: string
      enum: [start, end]
    agent_name:
      type: string

DeltaEvent:
  type: object
  properties:
    content: { type: string }
    role: { type: string }
    sender: { type: string }
    tool_calls: { type: array }

ResponseEvent:
  type: object
  required: [response]
  properties:
    response:
      $ref: '#/Response'
```

**Priority**: Medium  
**Effort**: 2 days

---

### F-08: Evaluation Framework

**Description**  
Swarm includes example evaluation patterns where test cases define input conversations and expected function calls. Evals run N iterations per case and measure success rates. Results are stored in structured files.

**How It Applies to AGENT-33**  
AGENT-33's evidence-first principle requires verification. A formal evaluation specification would enable consistent testing of agent behaviors across implementations.

**Implementation Pattern**
```yaml
# core/schemas/evaluation.schema.yaml
EvaluationCase:
  type: object
  required: [conversation, expected]
  properties:
    conversation:
      type: array
      items:
        type: object
        properties:
          role: { type: string, enum: [user, assistant, system] }
          content: { type: string }
    expected:
      oneOf:
        - type: object
          properties:
            function: { type: string }
        - type: object
          properties:
            response_contains: { type: string }
        - type: object
          properties:
            agent_name: { type: string }

EvaluationConfig:
  type: object
  properties:
    iterations: { type: integer, default: 5 }
    success_threshold: { type: number, default: 0.8 }
    model_override: { type: string }
```

**Example Case**
```json
{
  "conversation": [
    { "role": "user", "content": "My bag was not delivered!" }
  ],
  "expected": {
    "function": "transfer_to_lost_baggage"
  }
}
```

**Priority**: High  
**Effort**: 4 days

---

### F-09: Max Turns Safety Limit

**Description**  
The `max_turns` parameter limits the number of agent turns before forcing termination. Default is infinity, but production systems should set reasonable limits to prevent runaway loops.

**How It Applies to AGENT-33**  
AGENT-33's risk triggers (security, schema, API, CI/CD, large refactors) could include turn limits as a safety mechanism documented in orchestrator guidance.

**Implementation Pattern**
```yaml
# core/orchestrator/safety-limits.yaml
SafetyLimits:
  max_turns:
    default: 10
    production: 25
    development: 50
    unlimited: false  # Never allow in production
  max_tokens_per_turn:
    default: 4096
  max_function_calls_per_turn:
    default: 5
  timeout_seconds:
    default: 300
```

**Priority**: Medium  
**Effort**: 1 day

---

### F-10: Execute Tools Toggle

**Description**  
The `execute_tools` parameter allows interrupting execution before tool calls are made. When false, the system returns tool_calls immediately for external handling. This enables human-in-the-loop and approval workflows.

**How It Applies to AGENT-33**  
AGENT-33's review-driven improvement principle could leverage this pattern for risk trigger workflows where human approval is required before high-impact actions.

**Implementation Pattern**
```yaml
# core/workflows/approval-workflow.yaml
ApprovalWorkflow:
  triggers:
    - function_category: [security, deployment, data_deletion]
    - estimated_impact: [high, critical]
  behavior:
    execute_tools: false
    return_tool_calls: true
    await_approval: true
  approval:
    channels: [pr_comment, slack, email]
    timeout_hours: 24
    auto_reject_on_timeout: true
```

**Priority**: Medium  
**Effort**: 2 days

---

### F-11: Model Override Injection

**Description**  
The `model_override` parameter allows runtime substitution of the agent's configured model. This enables A/B testing, cost optimization, and graceful degradation without code changes.

**How It Applies to AGENT-33**  
AGENT-33's model-agnostic principle is strengthened by documenting model override patterns. This allows implementations to swap models based on context, cost, or availability.

**Implementation Pattern**
```yaml
# core/schemas/model-selection.schema.yaml
ModelSelection:
  type: object
  properties:
    default: { type: string }
    override_rules:
      type: array
      items:
        type: object
        properties:
          condition:
            type: string
            description: "Expression evaluating context_variables"
          model: { type: string }
          priority: { type: integer }
    fallback_chain:
      type: array
      items: { type: string }
      description: "Models to try if primary fails"
```

**Priority**: Low  
**Effort**: 1 day

---

### F-12: REPL Demo Loop

**Description**  
Swarm provides `run_demo_loop()` for interactive testing. It maintains conversation state, handles streaming, and provides a command-line interface for rapid prototyping.

**How It Applies to AGENT-33**  
AGENT-33 could document a standard REPL specification for testing agent configurations, enabling implementations to provide consistent interactive debugging experiences.

**Implementation Pattern**
```yaml
# core/templates/repl-specification.yaml
REPLSpecification:
  required_commands:
    - input: "User message"
      action: "Send to active agent"
    - input: "/agent"
      action: "Show current agent name"
    - input: "/context"
      action: "Show context variables"
    - input: "/history"
      action: "Show conversation history"
    - input: "/clear"
      action: "Reset session"
    - input: "/quit"
      action: "Exit REPL"
  streaming:
    enabled: true
    delimiter_display: "[Agent: {name}]"
  output:
    format: "markdown"
    syntax_highlighting: true
```

**Priority**: Low  
**Effort**: 1 day

---

## Recommendations

### R-01: Formalize Agent Schema (High Priority)

**Recommendation**: Create `core/schemas/agent.schema.yaml` with Swarm-inspired fields.

**Rationale**: AGENT-33 defines roles textually but lacks formal schemas. A machine-readable agent definition enables validation, tooling, and cross-implementation consistency.

**Implementation Pattern**
```yaml
# core/schemas/agent.schema.yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
$id: "agent-33/agent"
title: "AGENT-33 Agent Definition"
type: object
required: [name, instructions]
properties:
  name:
    type: string
    pattern: "^[A-Za-z][A-Za-z0-9_-]*$"
  instructions:
    $ref: "#/$defs/Instructions"
  functions:
    type: array
    items: { $ref: "function.schema.yaml" }
  model:
    type: string
    default: "model-agnostic"
  parallel_tool_calls:
    type: boolean
    default: true
  handoff_targets:
    type: array
    items: { type: string }

$defs:
  Instructions:
    oneOf:
      - type: string
      - type: object
        required: [template]
        properties:
          template: { type: string }
          context_params: 
            type: array
            items: { type: string }
```

---

### R-02: Document Handoff Protocol Specification (High Priority)

**Recommendation**: Add `core/orchestrator/handoff-specification.md` with executable examples.

**Rationale**: Swarm's handoff pattern is elegant and powerful. Documenting it formally allows AGENT-33 consumers to implement consistent agent transitions.

**Implementation Pattern**
```markdown
# Handoff Specification

## Mechanism
Handoff occurs when a function returns an Agent object instead of a string.

## State Transfer
| State Component | Preserved | Cleared | Merged |
|-----------------|-----------|---------|--------|
| Conversation history | ✓ | | |
| System prompt | | ✓ | |
| Context variables | | | ✓ |
| Active agent | | ✓ | |

## Function Signature
\`\`\`
def transfer_to_agent_name() -> Agent:
    """Transfer conversation to Agent Name."""
    return agent_name_instance
\`\`\`

## Bidirectional Handoff
Agents may hand back to triage using `transfer_back_to_triage()`.
```

---

### R-03: Create Evaluation Specification (High Priority)

**Recommendation**: Add `core/schemas/evaluation.schema.yaml` and example templates.

**Rationale**: AGENT-33's evidence-first principle requires formal verification patterns. Swarm's evaluation approach provides a proven template.

**Implementation Pattern**
```yaml
# core/templates/evaluation-template.yaml
EvaluationSuite:
  name: "Agent Routing Evaluation"
  cases:
    - id: "route-refund-01"
      conversation:
        - role: user
          content: "I want my money back"
      expected:
        function: "transfer_to_refunds"
      tags: [routing, refunds]
    - id: "route-sales-01"
      conversation:
        - role: user
          content: "Tell me about your products"
      expected:
        function: "transfer_to_sales"
      tags: [routing, sales]
  config:
    iterations: 10
    pass_threshold: 0.9
    model: "model-agnostic"
```

---

### R-04: Add Context Variable Documentation (Medium Priority)

**Recommendation**: Add `core/orchestrator/context-variables.md` with propagation rules.

**Rationale**: Context variables are critical for state management across agent boundaries. Formal documentation prevents inconsistent implementations.

---

### R-05: Create Triage Workflow Template (Medium Priority)

**Recommendation**: Add `core/workflows/triage-agent.yaml` as a canonical pattern.

**Rationale**: Triage is a common pattern in multi-agent systems. A documented template accelerates adoption and ensures consistency.

---

### R-06: Document Safety Limits (Medium Priority)

**Recommendation**: Add `core/orchestrator/safety-limits.md` with production defaults.

**Rationale**: Unbounded execution is a production risk. Documenting turn limits, timeouts, and approval workflows is essential for reliable systems.

---

### R-07: Add Streaming Event Schema (Low Priority)

**Recommendation**: Add `core/schemas/stream-events.schema.yaml` for real-time UIs.

**Rationale**: Agent boundary events enable rich debugging and user experiences. Standardizing event formats ensures interoperability.

---

### R-08: Create Function Schema Specification (Medium Priority)

**Recommendation**: Add `core/schemas/function.schema.yaml` with type mapping rules.

**Rationale**: Automatic function-to-schema conversion is valuable. Documenting the mapping enables polyglot implementations.

---

## Backlog Items Generated

| ID | Title | Priority | Effort | Impact |
|----|-------|----------|--------|--------|
| CA-001 | Create formal Agent schema (agent.schema.yaml) | High | 2d | Enables validation and tooling for agent definitions |
| CA-002 | Document handoff protocol specification | High | 3d | Formalizes agent-to-agent delegation pattern |
| CA-003 | Create evaluation schema and templates | High | 4d | Enables evidence-first testing of agent behaviors |
| CA-004 | Add context variable propagation rules | High | 2d | Ensures consistent state management across agents |
| CA-005 | Create function-to-schema specification | High | 2d | Enables polyglot tool definition generation |
| CA-006 | Add triage agent workflow template | High | 3d | Provides canonical routing pattern for multi-domain systems |
| CA-007 | Create Result object schema | Medium | 1d | Standardizes composite function returns |
| CA-008 | Document streaming event schemas | Medium | 2d | Enables real-time UI and logging integrations |
| CA-009 | Add safety limits documentation | Medium | 1d | Prevents unbounded execution in production |
| CA-010 | Create approval workflow pattern | Medium | 2d | Enables human-in-the-loop for high-risk actions |
| CA-011 | Add model override specification | Low | 1d | Supports runtime model switching |
| CA-012 | Create REPL testing specification | Low | 1d | Standardizes interactive debugging interface |

---

## Summary Matrix

| Aspect | OpenAI Swarm | AGENT-33 | Gap | Recommendation |
|--------|--------------|----------|-----|----------------|
| **Agent Definition** | Pydantic BaseModel with fields | Textual role descriptions | Schema needed | CA-001 |
| **Handoff Mechanism** | Function returns Agent object | Procedural handoff protocol | Functional pattern | CA-002 |
| **State Management** | context_variables dict | Evidence capture | Formal propagation rules | CA-004 |
| **Tool Definition** | Auto-generated from Python | Manual specification | Type mapping spec | CA-005 |
| **Routing** | Triage agent pattern | Orchestrator role | Template needed | CA-006 |
| **Evaluation** | JSON test cases with evals | Evidence-first principle | Eval framework | CA-003 |
| **Streaming** | Delimiter events | Logging capture | Event schema | CA-008 |
| **Safety** | max_turns parameter | Risk triggers | Limit documentation | CA-009 |
| **Model Selection** | model_override parameter | Model-agnostic principle | Override spec | CA-011 |
| **Approval Workflow** | execute_tools toggle | Review-driven improvement | Approval pattern | CA-010 |

---

## Appendix A: Swarm Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Swarm Client                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Agent A  │───▶│ Agent B  │───▶│ Agent C  │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │                     │
│       ▼               ▼               ▼                     │
│  ┌──────────────────────────────────────────┐              │
│  │           Context Variables              │              │
│  │  { user_id, session, permissions, ... }  │              │
│  └──────────────────────────────────────────┘              │
│                       │                                     │
│                       ▼                                     │
│  ┌──────────────────────────────────────────┐              │
│  │              Response                    │              │
│  │  { messages, agent, context_variables }  │              │
│  └──────────────────────────────────────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Appendix B: Core Loop Pseudocode

```
function run(agent, messages, context_variables, max_turns):
    active_agent = agent
    history = copy(messages)
    
    while turns < max_turns:
        # 1. Get completion from current agent
        completion = get_chat_completion(
            agent=active_agent,
            history=history,
            context=context_variables
        )
        
        # 2. Append response to history
        history.append(completion.message)
        
        # 3. If no tool calls, return
        if not completion.tool_calls:
            break
        
        # 4. Execute tool calls
        for tool_call in completion.tool_calls:
            result = execute_function(tool_call, context_variables)
            
            # 5. Handle handoff
            if result.agent:
                active_agent = result.agent
            
            # 6. Merge context updates
            context_variables.update(result.context_variables)
            
            # 7. Append tool result to history
            history.append(result.to_message())
    
    return Response(history, active_agent, context_variables)
```

---

## Appendix C: References

- OpenAI Swarm Repository: https://github.com/openai/swarm
- OpenAI Agents SDK (successor): https://github.com/openai/openai-agents-python
- Chat Completions API: https://platform.openai.com/docs/api-reference/chat
- AGENT-33 Orchestration Index: core/ORCHESTRATION_INDEX.md

---

*Analysis generated by AGENT-33 competitive analysis workflow.*
