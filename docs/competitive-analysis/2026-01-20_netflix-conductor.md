# Competitive Analysis: Netflix Conductor

**Date**: 2026-01-20  
**Repository**: https://github.com/Netflix/conductor  
**Status**: Complete  
**Analyst**: Competitive Analysis System  
**Reference**: CA-0XX Series

---

## Executive Summary

Netflix Conductor is a battle-tested workflow orchestration platform originally developed at Netflix to orchestrate microservices-based workflows. Although Netflix discontinued OSS maintenance in December 2023, the repository remains one of the most comprehensive examples of production-grade workflow orchestration, with 16.3k+ stars and extensive enterprise adoption. The platform's JSON-first workflow definitions, task abstraction model, and system operators (Fork/Join, Decision, SubWorkflow) offer valuable patterns for AGENT-33's documentation-driven orchestration framework.

For AGENT-33, Conductor provides proven patterns in three key areas: (1) workflow definition schemas with versioning and input/output contracts, (2) task lifecycle management with retry policies and timeout handling, and (3) execution operators that support parallel execution, conditional branching, and hierarchical composition. Many of these patterns can be adapted from Conductor's implementation-focused approach to AGENT-33's specification-first philosophy.

The analysis identifies 10 features that would enhance AGENT-33's orchestration capabilities, with recommended adaptations that maintain AGENT-33's core principles: model-agnostic design, evidence-first validation, minimal diffs, and full auditability. Implementation recommendations prioritize documentation specifications over executable code, consistent with AGENT-33's meta-repository architecture.

---

## Repository Overview

### Purpose

Netflix Conductor is a platform for orchestrating workflows that span across microservices. It provides:
- **Workflow orchestration**: Define complex workflows as JSON/code with task dependencies
- **Task abstraction**: Decouple task definition from execution with worker-based polling
- **State management**: Durable execution with persistence to Redis, Cassandra, or SQL databases
- **Event-driven architecture**: Event handlers and queue integrations (SQS, AMQP, NATS)
- **Observability**: Workflow visualization, metrics, and execution logging

### Technology Stack

| Component | Technology |
|-----------|------------|
| Core Runtime | Java 17+, Spring Boot |
| Persistence | Redis, Cassandra, PostgreSQL, MySQL |
| Search/Indexing | Elasticsearch 6.x/7.x |
| API Layer | REST, gRPC |
| Event Queues | AWS SQS, AMQP, NATS |
| External Storage | AWS S3, Azure Blob |
| UI | Node.js (React-based) |
| Build | Gradle |

### Key Concepts

| Concept | Description | AGENT-33 Analog |
|---------|-------------|-----------------|
| **Workflow Definition** | JSON schema defining tasks, operators, inputs/outputs | `workflow.schema.json` |
| **Task Definition** | Reusable task specifications with retry/timeout config | Step definitions in workflow schema |
| **Worker** | External process that executes tasks | Agent invocation |
| **System Task** | Built-in task types (HTTP, Event, SubWorkflow) | Built-in actions (`invoke-agent`, `run-command`) |
| **Operator** | Control flow primitives (Fork, Join, Switch, Loop) | Execution modes, conditional steps |
| **Event Handler** | Respond to external events | Triggers (`on_change`, `on_event`) |
| **Task Domain** | Routing mechanism for task-to-worker assignment | Agent routing maps |

---

## Feature Inventory

### Feature 1: Task Definition with Retry Policies

**Description**  
Conductor separates task definitions from workflow definitions, allowing reusable task specifications with configurable retry logic, timeout handling, and rate limiting.

```json
{
  "name": "verify_email",
  "retryCount": 3,
  "retryLogic": "FIXED",
  "retryDelaySeconds": 10,
  "timeoutSeconds": 3600,
  "timeoutPolicy": "TIME_OUT_WF",
  "responseTimeoutSeconds": 600,
  "pollTimeoutSeconds": 100,
  "inputKeys": ["email"],
  "outputKeys": ["verified", "timestamp"],
  "rateLimitPerFrequency": 50,
  "rateLimitFrequencyInSeconds": 1
}
```

**Application to AGENT-33**  
Enhance the workflow schema to support task-level retry policies, enabling declarative failure handling without runtime-specific implementation.

**Implementation Pattern**
```yaml
# core/schemas/task-definition.schema.json extension
stepDef:
  properties:
    retry:
      type: object
      properties:
        count: { type: integer, minimum: 0, maximum: 10 }
        logic: { enum: ["FIXED", "EXPONENTIAL_BACKOFF", "LINEAR_BACKOFF"] }
        delay_seconds: { type: integer }
        max_delay_seconds: { type: integer }
    timeout:
      type: object
      properties:
        execution_seconds: { type: integer }
        response_seconds: { type: integer }
        policy: { enum: ["RETRY", "TIME_OUT_WF", "ALERT_ONLY"] }
```

**Priority**: High  
**Effort**: 2 days  
**Impact**: Enables robust error handling specifications

---

### Feature 2: Fork-Join Dynamic Parallel Execution

**Description**  
Conductor's `FORK_JOIN_DYNAMIC` operator enables runtime-determined parallel branches. The number of branches is determined at runtime based on task output, enabling data-driven parallelism.

```json
{
  "name": "dynamic_fanout",
  "taskReferenceName": "fanout1",
  "type": "FORK_JOIN_DYNAMIC",
  "inputParameters": {
    "dynamicTasks": "${previous_task.output.dynamicTasks}",
    "input": "${previous_task.output.inputs}"
  },
  "dynamicForkTasksParam": "dynamicTasks",
  "dynamicForkTasksInputParamName": "input"
}
```

**Application to AGENT-33**  
Extend the parallel execution specification to support dynamic task generation, where the number of parallel branches is determined by workflow inputs or prior step outputs.

**Implementation Pattern**
```yaml
# Extension to stepDef in workflow.schema.json
- id: process-files
  action: parallel-group
  parallel_config:
    mode: dynamic  # New mode
    items_expression: "${steps.scan-files.outputs.file_list}"
    task_template:
      action: invoke-agent
      agent: file-processor
      inputs:
        file: "${item}"
    max_concurrency: 8
```

**Priority**: High  
**Effort**: 3 days  
**Impact**: Enables data-driven workflow scaling

---

### Feature 3: Switch/Decision Operator with Expression Evaluation

**Description**  
Conductor's `SWITCH` operator (formerly `DECISION`) evaluates expressions to determine execution paths. Supports JavaScript-like expressions and default cases.

```json
{
  "name": "switch_task",
  "taskReferenceName": "switch_1",
  "type": "SWITCH",
  "evaluatorType": "value-param",
  "expression": "switchCaseValue",
  "inputParameters": {
    "switchCaseValue": "${workflow.input.type}"
  },
  "decisionCases": {
    "PREMIUM": [{ "name": "premium_flow", "type": "SIMPLE" }],
    "STANDARD": [{ "name": "standard_flow", "type": "SIMPLE" }]
  },
  "defaultCase": [{ "name": "default_flow", "type": "SIMPLE" }]
}
```

**Application to AGENT-33**  
Formalize the conditional step specification with explicit evaluator types and expression syntax, enabling complex branching logic in workflow definitions.

**Implementation Pattern**
```yaml
# Enhanced conditional step specification
- id: route-by-type
  action: conditional
  evaluator: value-param  # or "javascript", "jq"
  expression: "${workflow.inputs.artifact_type}"
  cases:
    prompt:
      - id: validate-prompt
        action: invoke-agent
        agent: prompt-validator
    schema:
      - id: validate-schema
        action: invoke-agent
        agent: schema-validator
  default:
    - id: generic-validation
      action: invoke-agent
      agent: generic-validator
```

**Priority**: High  
**Effort**: 2 days  
**Impact**: Enables complex routing specifications

---

### Feature 4: SubWorkflow Composition

**Description**  
Conductor supports hierarchical workflow composition through `SUB_WORKFLOW` tasks, enabling modular workflow design with version pinning.

```json
{
  "name": "sub_workflow_task",
  "taskReferenceName": "subwf1",
  "type": "SUB_WORKFLOW",
  "inputParameters": {
    "input_data": "${workflow.input.data}"
  },
  "subWorkflowParam": {
    "name": "child_workflow",
    "version": 2
  }
}
```

**Application to AGENT-33**  
Add subworkflow invocation to the action enum, allowing workflows to compose other workflows with explicit version references.

**Implementation Pattern**
```yaml
# Extended action enum and subworkflow specification
- id: run-validation-suite
  action: invoke-workflow  # New action type
  workflow:
    name: validation-suite
    version: "1.2.0"  # Semver pinning
  inputs:
    artifacts: "${steps.collect.outputs.artifacts}"
  propagate_failure: true
  async: false  # Wait for completion
```

**Priority**: Medium  
**Effort**: 2 days  
**Impact**: Enables modular workflow composition

---

### Feature 5: Wait Task with External Signals

**Description**  
Conductor's `WAIT` task pauses execution until an external signal or duration elapses. Supports webhook callbacks, event triggers, and timeout-based resumption.

```json
{
  "name": "wait_for_approval",
  "taskReferenceName": "approval_wait",
  "type": "WAIT",
  "inputParameters": {
    "duration": "1d",
    "waitType": "SIGNAL"
  }
}
```

**Application to AGENT-33**  
Extend the `wait` action to support signal-based resumption patterns for human-in-the-loop and external system integration workflows.

**Implementation Pattern**
```yaml
# Enhanced wait action specification
- id: await-human-review
  action: wait
  wait_config:
    type: signal  # or "duration", "event"
    signal_name: "review-complete"
    timeout: "24h"
    timeout_action: escalate  # or "fail", "continue"
    metadata:
      reviewers: ["human-reviewer@example.com"]
      artifact_path: "${steps.prepare.outputs.artifact_path}"
```

**Priority**: Medium  
**Effort**: 2 days  
**Impact**: Enables human-in-the-loop workflows

---

### Feature 6: Event Handlers and Queue Integration

**Description**  
Conductor's event handling system allows workflows to be triggered by external events and to publish events during execution. Supports multiple queue backends (SQS, AMQP, NATS).

```json
{
  "name": "order_event_handler",
  "event": "sqs:orders_queue",
  "condition": "$.status == 'NEW'",
  "actions": [
    {
      "action": "start_workflow",
      "start_workflow": {
        "name": "process_order",
        "input": {
          "orderId": "${event.orderId}"
        }
      }
    }
  ]
}
```

**Application to AGENT-33**  
Formalize event handler specifications with conditional expressions and multiple action types, extending the existing trigger catalog.

**Implementation Pattern**
```yaml
# core/orchestrator/triggers/event-handlers.yaml
event_handlers:
  - name: artifact-created-handler
    event: "agent33:artifact-created"
    condition: "${event.category} == 'prompt'"
    actions:
      - type: start-workflow
        workflow: prompt-validation-workflow
        input_mapping:
          artifact_path: "${event.path}"
          author: "${event.metadata.author}"
      - type: log
        message: "Started validation for ${event.path}"
    active: true
```

**Priority**: Medium  
**Effort**: 3 days  
**Impact**: Enables reactive workflow triggering

---

### Feature 7: Task Input/Output Mapping with JSONPath

**Description**  
Conductor uses JSONPath-like expressions for mapping data between tasks, supporting deep nesting, array operations, and fallback values.

```json
{
  "inputParameters": {
    "id": "${workflow.input.id}",
    "items": "${task1.output.items[*].name}",
    "firstItem": "${task1.output.items[0]}",
    "status": "${task2.output..status}",
    "default": "${task3.output.value|default_value}"
  }
}
```

**Application to AGENT-33**  
Document a formal expression syntax for input/output mapping, supporting JSONPath, fallbacks, and array operations.

**Implementation Pattern**
```yaml
# core/schemas/expression-syntax.md specification
Expression Syntax:
  ${workflow.inputs.<key>}     - Workflow input
  ${steps.<id>.outputs.<key>}  - Step output
  ${env.<var>}                 - Environment variable
  ${<path>[*].<field>}         - Array projection
  ${<path>[0]}                 - Array index
  ${<path>..<field>}           - Recursive descent
  ${<expr>|<default>}          - Fallback value
  ${<expr>:<type>}             - Type coercion
```

**Priority**: High  
**Effort**: 1 day  
**Impact**: Standardizes data flow specifications

---

### Feature 8: Workflow Versioning and Migration

**Description**  
Conductor supports multiple workflow versions running simultaneously, with explicit version references in subworkflow calls and configurable version selection strategies.

```json
{
  "name": "order_workflow",
  "version": 3,
  "tasks": [...],
  "schemaVersion": 2
}
```

Version selection:
- Explicit version in subworkflow reference
- Latest version when version is omitted
- Version-specific deployment and rollback

**Application to AGENT-33**  
Formalize version management specifications with migration strategies and compatibility rules.

**Implementation Pattern**
```yaml
# core/orchestrator/WORKFLOW_VERSIONING.md
Version Management:
  
  1. Version Format: Semantic versioning (MAJOR.MINOR.PATCH)
  
  2. Compatibility Rules:
     - MAJOR: Breaking changes, requires migration
     - MINOR: Backward-compatible additions
     - PATCH: Backward-compatible fixes
  
  3. Reference Strategies:
     - Pinned: "validation-workflow@1.2.0"
     - Range: "validation-workflow@^1.0.0"
     - Latest: "validation-workflow" (implicit latest)
  
  4. Migration Protocol:
     - Deprecation notice in version N
     - Breaking change in version N+1
     - Removal in version N+2
```

**Priority**: Medium  
**Effort**: 2 days  
**Impact**: Enables safe workflow evolution

---

### Feature 9: Do-While Loop Operator

**Description**  
Conductor's `DO_WHILE` operator enables loop execution with termination conditions, supporting iterative processing patterns.

```json
{
  "name": "loop_task",
  "taskReferenceName": "loop_1",
  "type": "DO_WHILE",
  "loopCondition": "if ($.loop_1['iteration'] < 3) { true; } else { false; }",
  "loopOver": [
    { "name": "process_item", "type": "SIMPLE" }
  ]
}
```

**Application to AGENT-33**  
Add loop constructs to the step definition schema for iterative processing specifications.

**Implementation Pattern**
```yaml
# Loop action in workflow.schema.json
- id: retry-until-success
  action: loop
  loop_config:
    type: do-while  # or "for-each", "while"
    condition: "${steps.check-status.outputs.status} != 'complete'"
    max_iterations: 10
    delay_between: "30s"
  steps:
    - id: attempt-process
      action: invoke-agent
      agent: processor
    - id: check-status
      action: invoke-agent
      agent: status-checker
```

**Priority**: Low  
**Effort**: 2 days  
**Impact**: Enables iterative workflow patterns

---

### Feature 10: External Payload Storage

**Description**  
Conductor supports offloading large payloads to external storage (S3, Azure Blob) when they exceed configurable thresholds, keeping the workflow execution lightweight.

```properties
conductor.app.taskInputPayloadSizeThreshold=3072KB
conductor.app.maxTaskInputPayloadSizeThreshold=10240KB
conductor.external-payload-storage.type=s3
conductor.external-payload-storage.s3.bucketName=conductor_payloads
```

**Application to AGENT-33**  
Document payload size governance and external storage patterns for workflows handling large artifacts.

**Implementation Pattern**
```yaml
# core/orchestrator/PAYLOAD_GOVERNANCE.md
Payload Size Limits:
  
  Thresholds:
    task_input_warning: 1MB
    task_input_max: 5MB
    task_output_warning: 1MB  
    task_output_max: 5MB
    workflow_input_max: 10MB
    workflow_output_max: 10MB
  
  Large Payload Handling:
    1. Reference Pattern:
       - Store artifact in external location
       - Pass reference (path/URL) in workflow
       - Agent retrieves on demand
    
    2. Chunking Pattern:
       - Split large payloads into chunks
       - Process chunks in parallel
       - Aggregate results
    
    3. Streaming Pattern:
       - For unbounded data
       - Process as stream, emit incremental results
```

**Priority**: Low  
**Effort**: 1 day  
**Impact**: Prevents workflow bloat

---

## Recommendations

### Recommendation 1: Formalize Task Definition Registry

**Description**  
Create a separate task definition registry that workflows reference, enabling task reuse and centralized configuration.

**Implementation Pattern**
```yaml
# core/orchestrator/TASK_REGISTRY.md
task_definitions:
  validate-prompt:
    description: "Validate a prompt artifact against standards"
    agent: prompt-validator
    retry:
      count: 2
      logic: EXPONENTIAL_BACKOFF
      delay_seconds: 5
    timeout:
      execution_seconds: 300
      policy: RETRY
    rate_limit:
      max_per_minute: 60
    inputs:
      - name: artifact_path
        type: path
        required: true
    outputs:
      - name: valid
        type: boolean
      - name: errors
        type: array

# Referenced in workflow:
- id: validate
  task: validate-prompt  # References registry
  inputs:
    artifact_path: "${workflow.inputs.path}"
```

**Priority**: High  
**Effort**: 3 days

---

### Recommendation 2: Add Execution Lock Specification

**Description**  
Document distributed locking patterns for preventing concurrent execution of the same workflow instance.

**Implementation Pattern**
```yaml
# core/orchestrator/EXECUTION_LOCKING.md
Execution Locking:
  
  Lock Strategies:
    - noop: No locking (default for documentation-only)
    - local: Single-instance lock (file-based)
    - distributed: Multi-instance lock (Redis, Zookeeper)
  
  Lock Configuration:
    lock_type: distributed
    lock_key: "${workflow.name}:${workflow.inputs.artifact_id}"
    lease_duration: 5m
    wait_timeout: 30s
    on_conflict: fail  # or "queue", "skip"
```

**Priority**: Medium  
**Effort**: 1 day

---

### Recommendation 3: Standardize Workflow Definition Validation

**Description**  
Create a validation specification for workflow definitions, including schema validation, reference resolution, and cycle detection.

**Implementation Pattern**
```yaml
# core/orchestrator/WORKFLOW_VALIDATION.md
Validation Stages:
  
  1. Schema Validation:
     - JSON Schema compliance
     - Required field presence
     - Type correctness
  
  2. Reference Resolution:
     - All step references valid
     - All agent references exist in registry
     - All workflow references resolvable
  
  3. Dependency Analysis:
     - No circular dependencies
     - All depends_on targets exist
     - Topological sort possible
  
  4. Expression Validation:
     - All expressions parseable
     - Referenced paths exist in schema
     - Type compatibility
```

**Priority**: High  
**Effort**: 2 days

---

### Recommendation 4: Add Workflow Metrics Specification

**Description**  
Document standard metrics that workflow executions should emit for observability.

**Implementation Pattern**
```yaml
# core/orchestrator/analytics/WORKFLOW_METRICS.md
Standard Metrics:
  
  Counters:
    - workflow_started_total{name, version}
    - workflow_completed_total{name, version, status}
    - task_executed_total{workflow, task, status}
    - task_retried_total{workflow, task}
  
  Gauges:
    - workflow_running_current{name}
    - task_queue_depth{task_type}
  
  Histograms:
    - workflow_duration_seconds{name, version}
    - task_duration_seconds{workflow, task}
    - task_wait_time_seconds{task_type}
  
  Labels:
    - name: Workflow/task name
    - version: Workflow version
    - status: completed, failed, timed_out
    - task: Task reference name
```

**Priority**: Medium  
**Effort**: 1 day

---

### Recommendation 5: Document Task Domain Routing

**Description**  
Add specification for routing tasks to specific agent pools based on domain, enabling workload isolation.

**Implementation Pattern**
```yaml
# core/orchestrator/TASK_DOMAINS.md
Task Domain Routing:
  
  Domain Definition:
    domains:
      default:
        description: "Default agent pool"
        agents: ["*"]
      high-priority:
        description: "Fast-track processing"
        agents: ["priority-agent-*"]
        queue_priority: 1
      batch:
        description: "Bulk processing"
        agents: ["batch-agent-*"]
        rate_limit: 10/minute
  
  Domain Selection:
    - Explicit: task.domain = "high-priority"
    - Rule-based: if artifact.priority == "urgent" then "high-priority"
    - Default: "default" when not specified
```

**Priority**: Low  
**Effort**: 2 days

---

## Backlog Items Generated

| ID | Title | Priority | Effort | Impact |
|----|-------|----------|--------|--------|
| CA-011 | Task Definition Registry with Retry Policies | High | 3 days | Enables reusable task specifications with centralized error handling |
| CA-012 | Dynamic Fork-Join Parallel Specification | High | 3 days | Enables runtime-determined parallelism for data-driven workflows |
| CA-013 | Switch/Decision Operator with Expression Evaluators | High | 2 days | Formalizes complex branching logic in workflow specifications |
| CA-014 | JSONPath Expression Syntax Documentation | High | 1 day | Standardizes input/output mapping across all workflows |
| CA-015 | SubWorkflow Composition Action | Medium | 2 days | Enables modular workflow design with version pinning |
| CA-016 | Wait Task with Signal-Based Resumption | Medium | 2 days | Supports human-in-the-loop and external integration patterns |
| CA-017 | Event Handler Specification | Medium | 3 days | Extends trigger catalog with conditional event handling |
| CA-018 | Workflow Versioning and Migration Protocol | Medium | 2 days | Ensures safe workflow evolution and backward compatibility |
| CA-019 | Workflow Validation Specification | High | 2 days | Prevents invalid workflow definitions from deployment |
| CA-020 | Workflow Metrics Standard | Medium | 1 day | Enables consistent observability across all workflows |
| CA-021 | Do-While Loop Action | Low | 2 days | Enables iterative processing workflow patterns |
| CA-022 | Payload Size Governance | Low | 1 day | Prevents workflow bloat with large artifacts |

---

## Summary Matrix

| Conductor Feature | AGENT-33 Current State | Gap | Recommendation |
|-------------------|------------------------|-----|----------------|
| **Task Definitions** | Step definitions inline | Partial | Add task registry (CA-011) |
| **Retry Policies** | Basic retry in stepDef | Partial | Enhance with policies (CA-011) |
| **Fork/Join** | Parallel mode exists | Partial | Add dynamic fork (CA-012) |
| **Fork/Join Dynamic** | Not specified | Gap | New specification (CA-012) |
| **Switch/Decision** | Conditional action exists | Partial | Enhance evaluators (CA-013) |
| **SubWorkflow** | Not specified | Gap | New action type (CA-015) |
| **Wait Task** | Basic wait action | Partial | Add signal support (CA-016) |
| **Event Handlers** | Trigger catalog exists | Partial | Add event handlers (CA-017) |
| **Versioning** | Semver in schema | Partial | Add protocol (CA-018) |
| **Input Mapping** | Basic expressions | Partial | Formalize syntax (CA-014) |
| **Do-While** | Not specified | Gap | New action (CA-021) |
| **External Storage** | Not specified | Gap | Add governance (CA-022) |
| **Metrics** | Analytics folder exists | Partial | Add standards (CA-020) |
| **Validation** | JSON Schema exists | Partial | Add stages (CA-019) |

### Alignment Summary

| Aspect | Conductor | AGENT-33 | Notes |
|--------|-----------|----------|-------|
| **Philosophy** | Implementation-first | Specification-first | Complementary approaches |
| **Workflow Format** | JSON/Code | JSON Schema | Direct compatibility |
| **Execution** | Runtime system | Documentation | AGENT-33 specifies, implementations execute |
| **Extensibility** | Java plugins | Schema extensions | Both support custom types |
| **Model Coupling** | Neutral (workers) | Model-agnostic | Aligned |
| **Auditability** | Execution logs | Immutable history | Both prioritize audit trails |

---

## Appendix: Conductor Architecture Reference

### Workflow Lifecycle

```
SCHEDULED → RUNNING → COMPLETED
                   ↘ FAILED
                   ↘ TIMED_OUT
                   ↘ TERMINATED
                   ↘ PAUSED → RUNNING
```

### Task Lifecycle

```
SCHEDULED → IN_PROGRESS → COMPLETED
                       ↘ FAILED → SCHEDULED (retry)
                       ↘ TIMED_OUT → SCHEDULED (retry)
                       ↘ CANCELLED
```

### System Task Types

| Type | Description | AGENT-33 Analog |
|------|-------------|-----------------|
| HTTP | Make HTTP requests | `run-command: curl` |
| EVENT | Publish/receive events | `on_event` trigger |
| INLINE | Execute JavaScript | `transform` action |
| JSON_JQ_TRANSFORM | JQ-based transformation | `transform` action |
| KAFKA_PUBLISH | Publish to Kafka | Event action |
| SUB_WORKFLOW | Execute child workflow | `invoke-workflow` |
| WAIT | Pause execution | `wait` action |
| HUMAN | Human task queue | Signal-based wait |

### Operator Types

| Operator | Description | AGENT-33 Analog |
|----------|-------------|-----------------|
| FORK_JOIN | Static parallel branches | `parallel-group` |
| FORK_JOIN_DYNAMIC | Dynamic parallel branches | Dynamic parallel (CA-012) |
| JOIN | Wait for parallel branches | Implicit in parallel-group |
| SWITCH | Conditional branching | `conditional` action |
| DO_WHILE | Loop with condition | Loop action (CA-021) |
| SET_VARIABLE | Set workflow variables | Output mapping |
| TERMINATE | End workflow | Exit with status |

---

*Generated: 2026-01-20*  
*Source: Netflix/conductor @ commit 548f386*
