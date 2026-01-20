# Competitive Analysis: Spinnaker Orca

**Date**: 2026-01-20  
**Repository**: https://github.com/spinnaker/orca  
**Analyst**: Competitive Analysis Agent  
**Status**: Complete

---

## Executive Summary

Spinnaker Orca is Netflix's production-grade orchestration engine powering the Spinnaker continuous delivery platform. It represents one of the most battle-tested pipeline orchestration systems in the industry, managing complex multi-stage deployments across diverse cloud providers at massive scale. Orca's architecture centers on a stateless, horizontally scalable design using a distributed queue system (Keiko) and DAG-based execution, enabling resilience to node failures and efficient work distribution.

AGENT-33 can benefit significantly from Orca's mature patterns for execution orchestration, particularly its message-based state machine, synthetic stage composition, and expression language for dynamic pipeline behavior. While AGENT-33 is documentation-first and model-agnostic, Orca's implementation patterns provide valuable blueprints for specifying execution semantics, failure recovery, and composable stage definitions. Key gaps in AGENT-33's current orchestration model include: queue-based message passing, delay scheduling, execution restart/resume semantics, and comprehensive expression evaluation.

This analysis identifies 12 features from Orca that would enhance AGENT-33's orchestration capabilities, ranging from high-priority items like Stage Composition and Context Sharing to medium-priority enhancements like Canary Analysis Integration and Pipeline Templates. The recommended implementation approach emphasizes specification-first design aligned with AGENT-33's philosophy of model-agnostic, evidence-first documentation.

---

## Repository Overview

### Purpose

Orca is the orchestration engine for Spinnaker, responsible for:
- Taking execution definitions (pipelines or orchestrations) and managing stage/task coordination
- Coordinating with other Spinnaker microservices (Clouddriver, Front50, Echo, etc.)
- Persisting execution state to backend stores (Redis/MySQL)
- Distributing work evenly through a queue-based architecture
- Supporting complex delivery workflows with concurrent branching, synthetic stages, and dynamic graph construction

### Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Java/Kotlin |
| Framework | Spring Boot |
| Queue System | Keiko (Redis-backed delay queue) |
| Persistence | Redis (default), MySQL (recommended) |
| Expression Language | Spring Expression Language (SpEL) |
| Build System | Gradle |
| API Gateway | Gate (Spinnaker microservice) |

### Key Concepts

| Concept | Definition |
|---------|------------|
| **Execution** | Primary domain model; either `PIPELINE` (predefined, persistent) or `ORCHESTRATION` (ad-hoc, API-submitted) |
| **Stage** | Higher-order user-friendly actions (e.g., "Deploy", "Bake") organized as a DAG |
| **Task** | Atomic unit of work within a stage; executed sequentially |
| **Synthetic Stage** | Dynamically generated stages that occur BEFORE or AFTER parent stages |
| **StageDefinitionBuilder** | Interface for defining stage behavior, task graphs, and composition |
| **Message/Handler** | Queue-based units of work (StartStage, RunTask, CompleteExecution, etc.) |
| **Context** | Shared state within a stage, queryable across entire execution |
| **Expression** | SpEL-based dynamic values evaluated at stage start time |

---

## Feature Inventory

### Feature 1: DAG-Based Stage Execution

**Description**  
Orca organizes stages as a Directed Acyclic Graph (DAG), enabling concurrent branch execution with defined dependencies. Stages can execute in parallel when they have no dependencies, and the execution engine verifies upstream completion before starting dependent stages.

**How It Applies to AGENT-33**  
AGENT-33's current dependency graph (CA-014) specifies artifact dependencies but lacks explicit DAG execution semantics for workflow stages. Adopting Orca's DAG model would enable:
- Parallel workflow phase execution
- Clear dependency resolution semantics
- Branch synchronization (fan-out/fan-in)

**Implementation Pattern**
```yaml
# workflow.schema.json extension
stage:
  type: object
  properties:
    id: { type: string }
    type: { type: string }
    requisiteStageRefIds:
      type: array
      items: { type: string }
      description: "Stages that must complete before this stage starts"
    parallelWith:
      type: array
      items: { type: string }
      description: "Stages that can execute concurrently"
```

```markdown
## Stage Dependency Resolution

1. Build stage graph from requisiteStageRefIds
2. Identify root stages (no dependencies)
3. Execute roots in parallel
4. On stage completion, check if dependents are unblocked
5. Repeat until all stages complete or failure
```

**Priority**: High  
**Effort**: Medium (2-3 days specification, schema updates)  
**Impact**: Enables complex multi-agent workflows with parallel execution

---

### Feature 2: Synthetic Stage Composition

**Description**  
Orca's `StageDefinitionBuilder` allows stages to dynamically generate "synthetic" stages that run BEFORE or AFTER the parent stage. This enables complex stages (like Canary deployments) to be composed of simpler stages while appearing as a single unit to users.

**How It Applies to AGENT-33**  
AGENT-33 could use synthetic stages to:
- Automatically inject evidence capture before/after workflow phases
- Compose complex workflows from simpler building blocks
- Enable "meta-stages" that expand into implementation-specific steps

**Implementation Pattern**
```yaml
# Stage definition with synthetic stages
stageDefinition:
  type: canary-analysis
  syntheticStages:
    before:
      - type: deploy-baseline
        context: { cluster: "${context.baselineCluster}" }
      - type: deploy-canary  
        context: { cluster: "${context.canaryCluster}" }
    after:
      - type: cleanup
        context: { deleteBaseline: true, deleteCanary: true }
```

```markdown
## Synthetic Stage Injection

When processing a stage with synthetic definitions:
1. Generate BEFORE synthetic stages with parent reference
2. Insert into stage graph before parent tasks
3. Execute parent tasks
4. Generate AFTER synthetic stages
5. Parent marked complete only when all synthetics complete
```

**Priority**: High  
**Effort**: Medium (2-3 days)  
**Impact**: Enables composable, reusable stage definitions

---

### Feature 3: Message-Based State Machine

**Description**  
Orca uses Keiko, a distributed delay queue, to progress executions through atomic messages (`StartStage`, `RunTask`, `CompleteExecution`, etc.). Each message type has a dedicated Handler. This enables:
- Resilience to node failures (work can be picked up by any node)
- Delayed execution (scheduled retries, wait stages)
- Horizontal scaling

**How It Applies to AGENT-33**  
While AGENT-33 is documentation-focused, specifying message-based state machine semantics would:
- Provide a reference architecture for implementers
- Define clear state transition rules
- Enable distributed execution patterns in agent implementations

**Implementation Pattern**
```yaml
# Message types specification
messageTypes:
  - name: StartExecution
    handler: StartExecutionHandler
    redeliverable: false
    fields: [executionId, trigger]
    
  - name: StartStage
    handler: StartStageHandler  
    redeliverable: true
    fields: [executionId, stageId]
    preconditions:
      - "All upstream stages completed"
      
  - name: RunTask
    handler: RunTaskHandler
    redeliverable: true
    fields: [executionId, stageId, taskId]
    timeout: "${task.timeout}"
    
  - name: CompleteStage
    handler: CompleteStageHandler
    redeliverable: true
    fields: [executionId, stageId, status]
```

**Priority**: Medium  
**Effort**: High (4-5 days for full specification)  
**Impact**: Provides reference architecture for distributed execution

---

### Feature 4: Stage Context and Cross-Stage Data Sharing

**Description**  
Orca stages share a common context that can be queried across the entire execution. For example, a `bake` stage publishes image details that a subsequent `deploy` stage consumes. Context is scoped but accessible via expressions.

**How It Applies to AGENT-33**  
AGENT-33's handoff documents (STATUS.md, TASKS.md) provide inter-session context but lack runtime context specification. Orca's model provides:
- Formal context scoping rules
- Cross-phase data passing semantics
- Evidence artifact propagation

**Implementation Pattern**
```yaml
# Context specification
contextModel:
  execution:
    description: "Top-level execution context, accessible everywhere"
    properties:
      - trigger
      - parameters
      - authentication
      
  stage:
    description: "Stage-specific context, accessible within stage and downstream"
    properties:
      - outputs: { description: "Artifacts produced by this stage" }
      - context: { description: "Stage configuration and runtime data" }
      
  task:
    description: "Task-specific context, merged into stage on completion"
    
contextResolution:
  - "Task context merges into stage context on task completion"
  - "Stage outputs are accessible via #stage('name')['outputs']"
  - "Upstream stage data flows downstream but not upstream"
```

**Priority**: High  
**Effort**: Low (1-2 days)  
**Impact**: Enables data flow specification between workflow phases

---

### Feature 5: Pipeline Expression Language

**Description**  
Orca implements a powerful expression language based on SpEL that allows dynamic values throughout pipelines:
- Access trigger data: `${trigger["buildInfo"]["number"]}`
- Reference other stages: `${#stage("Deploy")["status"]}`
- Conditional execution: `${parameters["runTests"] == "true"}`
- Helper functions: `#fromUrl()`, `#toJson()`, `#judgment()`

**How It Applies to AGENT-33**  
AGENT-33 currently uses simple variable substitution. A formal expression language would enable:
- Dynamic workflow branching based on evidence
- Cross-reference between workflow artifacts
- Conditional phase execution

**Implementation Pattern**
```yaml
# Expression language specification
expressionSyntax:
  wrapper: "${ }"
  accessors:
    dot: "object.property"
    bracket: "object['property']"  # Preferred
  operators:
    comparison: ["==", "!=", "<", ">", "<=", ">="]
    logical: ["&&", "||", "!"]
    ternary: "condition ? ifTrue : ifFalse"
    elvis: "value ?: defaultValue"
    
helperFunctions:
  - name: "#stage"
    signature: "#stage(stageName: string)"
    returns: "Stage context object"
    example: "${#stage('Build')['outputs']['artifact']}"
    
  - name: "#stageExists"
    signature: "#stageExists(stageName: string)"
    returns: "boolean"
    example: "${#stageExists('Optional Step') ? 'run' : 'skip'}"
    
  - name: "#toJson"
    signature: "#toJson(object: any)"
    returns: "JSON string"
    
  - name: "#fromUrl"
    signature: "#fromUrl(url: string)"
    returns: "URL contents as string"
    
helperProperties:
  - name: "execution"
    description: "Current pipeline execution"
  - name: "parameters"
    description: "Pipeline parameters (shortcut for trigger.parameters)"
  - name: "trigger"
    description: "Pipeline trigger data"
```

**Priority**: High  
**Effort**: Medium (3-4 days for specification)  
**Impact**: Dramatically increases workflow flexibility and dynamism

---

### Feature 6: Conditional Stage Execution

**Description**  
Orca stages support a "Conditional on Expression" option that skips the stage if the expression evaluates to false. This enables dynamic workflow paths based on runtime conditions.

**How It Applies to AGENT-33**  
AGENT-33's trigger system (CA-009) handles initiation but lacks conditional execution semantics. This would enable:
- Skip phases based on risk assessment
- Conditional evidence capture
- Environment-specific workflow paths

**Implementation Pattern**
```yaml
# Stage schema extension
stage:
  properties:
    stageEnabled:
      type: object
      properties:
        expression:
          type: string
          description: "Expression that must evaluate to true for stage to run"
          example: "${parameters['runSecurityScan'] == 'true'}"
        type:
          enum: [expression]
          
# Example usage
stages:
  - id: security-scan
    type: security-review
    stageEnabled:
      type: expression
      expression: "${trigger['riskLevel'] >= 'medium'}"
```

**Priority**: High  
**Effort**: Low (1 day)  
**Impact**: Enables dynamic workflow execution paths

---

### Feature 7: Execution Pause/Resume/Cancel

**Description**  
Orca supports explicit execution control:
- **Pause**: Halts execution, can be resumed later
- **Resume**: Continues paused execution
- **Cancel**: Terminates execution with cleanup
- **Manual Judgment**: Pauses for human approval

**How It Applies to AGENT-33**  
AGENT-33's session handoff model benefits from formal pause/resume semantics:
- Session boundaries become explicit pause points
- Human review gates for critical decisions
- Graceful cancellation with evidence preservation

**Implementation Pattern**
```yaml
# Execution control specification
executionControl:
  states:
    - RUNNING
    - PAUSED
    - CANCELED
    - TERMINAL  # Completed (success/failure)
    
  transitions:
    pause:
      from: [RUNNING]
      to: PAUSED
      actions:
        - "Complete current task"
        - "Persist execution state"
        - "Record pause reason and timestamp"
        
    resume:
      from: [PAUSED]
      to: RUNNING
      actions:
        - "Restore execution context"
        - "Resume from next pending task"
        
    cancel:
      from: [RUNNING, PAUSED]
      to: CANCELED
      actions:
        - "Mark all running stages as CANCELED"
        - "Execute onFailure stages if defined"
        - "Preserve evidence artifacts"

# Manual judgment stage
manualJudgment:
  type: stage
  behavior:
    - "Pause execution"
    - "Notify configured channels"
    - "Wait for judgment input"
    - "Resume with judgment value in context"
  outputs:
    judgmentValue: { type: string }
    judgedBy: { type: string }
    judgmentTime: { type: timestamp }
```

**Priority**: Medium  
**Effort**: Medium (2-3 days)  
**Impact**: Formalizes session handoff and human-in-the-loop workflows

---

### Feature 8: Failure Handling and Recovery

**Description**  
Orca provides sophisticated failure handling:
- **onFailureStages**: Stages that run on failure (rollback, notifications)
- **failPipeline**: Whether stage failure fails the entire pipeline
- **continuePipeline**: Continue despite stage failure
- **completeOtherBranchesThenFail**: Let parallel branches complete before failing
- **Automatic rollback**: Revert deployments on failure

**How It Applies to AGENT-33**  
AGENT-33's current failure model is implicit. Orca's patterns provide:
- Explicit failure recovery specifications
- Evidence preservation on failure
- Rollback procedure documentation

**Implementation Pattern**
```yaml
# Failure handling specification
failureHandling:
  stageOptions:
    failPipeline:
      type: boolean
      default: true
      description: "If true, stage failure fails entire execution"
      
    continuePipeline:
      type: boolean
      default: false
      description: "If true, continue execution despite failure"
      
    completeOtherBranchesThenFail:
      type: boolean
      default: false
      description: "Allow parallel branches to complete before failing"
      
  onFailureStages:
    description: "Stages to execute when this stage fails"
    schema:
      type: array
      items:
        type: object
        properties:
          type: { type: string }
          context: { type: object }
          
# Example usage
stages:
  - id: deploy-prod
    type: deploy
    failPipeline: true
    onFailureStages:
      - type: notification
        context:
          channel: "#incidents"
          message: "Deployment failed: ${execution.id}"
      - type: rollback
        context:
          targetServerGroup: "${#stage('Deploy')['context']['previousServerGroup']}"
```

**Priority**: High  
**Effort**: Medium (2-3 days)  
**Impact**: Robust error handling and recovery specification

---

### Feature 9: Pipeline Templates

**Description**  
Orca supports pipeline templates that can be parameterized and shared across teams. Templates define the structure while instances customize specific values.

**How It Applies to AGENT-33**  
AGENT-33 already has templates in `core/templates/`. Orca's model adds:
- Formal variable declaration with types and defaults
- Template inheritance and composition
- Version management for templates

**Implementation Pattern**
```yaml
# Pipeline template specification
pipelineTemplate:
  metadata:
    id: "standard-deployment"
    version: "1.0.0"
    description: "Standard deployment pipeline with tests"
    
  variables:
    - name: environment
      type: string
      description: "Target environment"
      enum: [dev, staging, prod]
      
    - name: runTests
      type: boolean
      default: true
      
    - name: testTimeout
      type: integer
      default: 300
      
  stages:
    - id: build
      type: build
      
    - id: test
      type: test
      stageEnabled:
        expression: "${templateVariables.runTests}"
      context:
        timeout: "${templateVariables.testTimeout}"
        
    - id: deploy
      type: deploy
      requisiteStageRefIds: [build, test]
      context:
        environment: "${templateVariables.environment}"

# Template instantiation
pipelineInstance:
  template:
    id: "standard-deployment"
    version: "1.0.0"
  variables:
    environment: "prod"
    runTests: true
    testTimeout: 600
```

**Priority**: Medium  
**Effort**: Medium (2-3 days)  
**Impact**: Improved template reusability and standardization

---

### Feature 10: Execution Windows and Scheduling

**Description**  
Orca supports restricted execution windows that limit when stages can run:
- Time-of-day restrictions
- Day-of-week restrictions
- Timezone-aware scheduling
- Skip window action (skip vs wait)

**How It Applies to AGENT-33**  
AGENT-33's trigger catalog could be enhanced with:
- Execution window specifications
- Time-based workflow constraints
- Business hours enforcement

**Implementation Pattern**
```yaml
# Execution window specification
executionWindow:
  type: object
  properties:
    enabled: { type: boolean, default: false }
    timezone: { type: string, default: "UTC" }
    whitelist:
      type: array
      items:
        type: object
        properties:
          startHour: { type: integer, minimum: 0, maximum: 23 }
          endHour: { type: integer, minimum: 0, maximum: 23 }
    days:
      type: array
      items:
        enum: [MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY]
    skipWindowAction:
      enum: [skip, wait]
      default: wait
      description: "Whether to skip stage or wait for window"

# Example usage
stages:
  - id: deploy-prod
    type: deploy
    restrictedExecutionWindow:
      enabled: true
      timezone: "America/New_York"
      whitelist:
        - startHour: 9
          endHour: 17
      days: [MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY]
      skipWindowAction: wait
```

**Priority**: Low  
**Effort**: Low (1 day)  
**Impact**: Enterprise scheduling compliance

---

### Feature 11: Stage Restart and Recovery

**Description**  
Orca allows restarting failed stages without rerunning the entire pipeline:
- Clean up stage state before restart
- Re-evaluate expressions with current context
- Preserve successful upstream stage outputs

**How It Applies to AGENT-33**  
AGENT-33's session model could benefit from:
- Explicit restart semantics for failed phases
- State cleanup procedures
- Idempotency requirements for restartable phases

**Implementation Pattern**
```yaml
# Stage restart specification
stageRestart:
  preconditions:
    - "Stage is in terminal state (SUCCEEDED, FAILED, CANCELED)"
    - "Execution is not RUNNING"
    
  cleanupActions:
    - "Reset stage status to NOT_STARTED"
    - "Clear stage outputs"
    - "Preserve upstream context"
    - "Call prepareStageForRestart() if defined"
    
  behavior:
    - "Re-evaluate stage expressions"
    - "Regenerate synthetic stages"
    - "Execute from beginning of stage"
    - "Downstream stages re-execute after restart completes"

# Stage definition with restart cleanup
stageDefinition:
  type: deploy
  prepareForRestart:
    actions:
      - "Delete server group if partially created"
      - "Clear cached deployment artifacts"
```

**Priority**: Medium  
**Effort**: Medium (2 days)  
**Impact**: Improved failure recovery and debugging

---

### Feature 12: Trigger Types and Artifacts

**Description**  
Orca supports diverse trigger types with rich artifact handling:
- Jenkins/CI triggers with build artifacts
- Git triggers with commit info
- Docker triggers with image details
- Pipeline triggers (one pipeline triggers another)
- Webhook triggers with payload
- Artifact resolution and binding

**How It Applies to AGENT-33**  
AGENT-33's trigger catalog (CA-009) could be extended with:
- Artifact attachment to triggers
- Trigger type hierarchy
- Artifact resolution semantics

**Implementation Pattern**
```yaml
# Extended trigger specification
triggerTypes:
  git:
    properties:
      source: { enum: [github, gitlab, bitbucket] }
      project: { type: string }
      branch: { type: string }
      hash: { type: string }
    artifacts:
      - type: git/commit
        metadata: [hash, branch, author, message]
        
  docker:
    properties:
      registry: { type: string }
      repository: { type: string }
      tag: { type: string }
    artifacts:
      - type: docker/image
        reference: "${registry}/${repository}:${tag}"
        
  pipeline:
    properties:
      parentExecution: { type: string }
      parentPipelineId: { type: string }
    artifacts:
      - description: "Inherit artifacts from parent pipeline"
        
  webhook:
    properties:
      source: { type: string }
      payload: { type: object }
    artifacts:
      - type: custom
        from: "${trigger.payload.artifacts}"

# Artifact resolution
artifactResolution:
  description: "How artifacts are bound to pipeline context"
  steps:
    - "Extract artifacts from trigger"
    - "Match against expected artifacts"
    - "Apply default artifacts if no match"
    - "Bind resolved artifacts to execution context"
```

**Priority**: Medium  
**Effort**: Medium (2-3 days)  
**Impact**: Rich trigger and artifact handling

---

## Recommendations

### Recommendation 1: Implement DAG Execution Specification

**Description**  
Extend AGENT-33's workflow schema to formally specify DAG-based stage execution with parallel branches and dependency resolution.

**Implementation Pattern**
```yaml
# Add to workflow.schema.json
{
  "definitions": {
    "stageGraph": {
      "type": "object",
      "properties": {
        "stages": {
          "type": "array",
          "items": { "$ref": "#/definitions/stage" }
        },
        "entryPoints": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Stage IDs with no prerequisites"
        }
      }
    },
    "stage": {
      "type": "object",
      "required": ["id", "type"],
      "properties": {
        "id": { "type": "string" },
        "type": { "type": "string" },
        "requisiteStageRefIds": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    }
  }
}
```

**Priority**: High  
**Complexity**: Medium

---

### Recommendation 2: Add Expression Language Specification

**Description**  
Define a model-agnostic expression language specification inspired by SpEL but simpler and implementation-independent.

**Implementation Pattern**
```markdown
## AGENT-33 Expression Language (AEL)

### Syntax
- Wrapper: `${ expression }`
- Property access: `object.property` or `object['property']`
- Default values: `value ?: default`
- Conditionals: `condition ? ifTrue : ifFalse`

### Built-in Properties
| Property | Description |
|----------|-------------|
| `execution` | Current workflow execution |
| `trigger` | Execution trigger data |
| `parameters` | User-provided parameters |
| `phase(name)` | Access phase by name |

### Built-in Functions
| Function | Description |
|----------|-------------|
| `#phaseExists(name)` | Check if phase exists |
| `#artifact(name)` | Get artifact by name |
| `#evidence(type)` | Get evidence of type |
```

**Priority**: High  
**Complexity**: Medium

---

### Recommendation 3: Define Failure Recovery Semantics

**Description**  
Formalize failure handling with onFailure actions, rollback procedures, and continue/fail options.

**Implementation Pattern**
```yaml
# failure-handling.md
## Failure Handling Specification

### Phase Failure Options
- `failWorkflow`: boolean (default: true)
- `continueOnFailure`: boolean (default: false)
- `onFailurePhases`: array of phases to execute on failure

### Recovery Actions
1. Preserve all evidence collected before failure
2. Execute onFailure phases in order
3. Mark workflow status appropriately
4. Notify configured channels
```

**Priority**: High  
**Complexity**: Low

---

### Recommendation 4: Add Synthetic Phase Composition

**Description**  
Enable phases to define "before" and "after" sub-phases that are automatically injected into the execution graph.

**Implementation Pattern**
```yaml
# Phase with synthetic sub-phases
phaseDefinition:
  type: security-review
  syntheticPhases:
    before:
      - type: evidence-capture
        context: { scope: "pre-review" }
    after:
      - type: evidence-capture
        context: { scope: "post-review" }
      - type: notification
```

**Priority**: Medium  
**Complexity**: Medium

---

### Recommendation 5: Specify Execution Control States

**Description**  
Define formal execution states (RUNNING, PAUSED, CANCELED, COMPLETED) with valid transitions.

**Implementation Pattern**
```yaml
# execution-states.md
## Execution State Machine

### States
- NOT_STARTED
- RUNNING
- PAUSED
- CANCELED
- SUCCEEDED
- FAILED

### Transitions
| From | To | Trigger |
|------|----|---------|
| NOT_STARTED | RUNNING | Start command |
| RUNNING | PAUSED | Pause command, Manual judgment |
| PAUSED | RUNNING | Resume command |
| RUNNING | CANCELED | Cancel command |
| RUNNING | SUCCEEDED | All phases complete successfully |
| RUNNING | FAILED | Phase failure with failWorkflow=true |
```

**Priority**: Medium  
**Complexity**: Low

---

### Recommendation 6: Extend Trigger Catalog with Artifacts

**Description**  
Enhance the existing trigger catalog with artifact attachment and resolution semantics.

**Implementation Pattern**
```yaml
# Add to TRIGGER_CATALOG.md
## Trigger Artifacts

Each trigger type can produce artifacts that are available to the workflow:

### Git Trigger Artifacts
- `git/commit`: Commit metadata (hash, author, message)
- `git/files`: Changed files list

### CI Trigger Artifacts  
- `ci/build`: Build number, status, logs
- `ci/artifacts`: Build artifacts (binaries, reports)

### Artifact Resolution
Artifacts are resolved at workflow start and bound to `execution.artifacts`.
```

**Priority**: Medium  
**Complexity**: Low

---

### Recommendation 7: Add Context Sharing Specification

**Description**  
Define how data flows between phases, what's accessible where, and how outputs propagate.

**Implementation Pattern**
```markdown
## Context Sharing Model

### Scope Hierarchy
1. **Execution Context**: Available everywhere
   - trigger, parameters, authentication
   
2. **Phase Context**: Available in phase and downstream
   - inputs, outputs, evidence
   
3. **Task Context**: Merged into phase on completion

### Data Flow Rules
- Phase outputs flow to all downstream phases
- Parallel phases cannot access each other's outputs
- Upstream phase outputs are read-only
```

**Priority**: Medium  
**Complexity**: Low

---

### Recommendation 8: Create Message Type Catalog

**Description**  
Document the message types that orchestrator implementations should support for distributed execution.

**Implementation Pattern**
```markdown
## Orchestrator Message Types

| Message | Purpose | Handler |
|---------|---------|---------|
| StartExecution | Begin workflow | Creates initial phases |
| StartPhase | Begin phase execution | Checks prerequisites |
| RunTask | Execute single task | Performs work |
| CompleteTask | Task finished | Updates phase state |
| CompletePhase | Phase finished | Triggers downstream |
| CompleteExecution | Workflow finished | Final cleanup |
| PauseExecution | Pause workflow | Suspends processing |
| ResumeExecution | Resume workflow | Continues processing |
| CancelExecution | Cancel workflow | Cleanup and terminate |
```

**Priority**: Low  
**Complexity**: Medium

---

## Backlog Items Generated

| ID | Title | Priority | Effort | Impact |
|----|-------|----------|--------|--------|
| CA-017 | DAG-Based Stage Execution Specification | High | 3 days | Enables parallel workflow execution |
| CA-018 | Expression Language Specification | High | 4 days | Dynamic workflow behavior |
| CA-019 | Synthetic Phase Composition | High | 3 days | Composable, reusable phases |
| CA-020 | Stage Context and Data Sharing Model | High | 2 days | Inter-phase data flow |
| CA-021 | Conditional Phase Execution | High | 1 day | Dynamic workflow paths |
| CA-022 | Failure Handling Specification | High | 2 days | Robust error recovery |
| CA-023 | Execution State Machine | Medium | 2 days | Formal state transitions |
| CA-024 | Manual Judgment Stage Type | Medium | 2 days | Human-in-the-loop workflows |
| CA-025 | Pipeline Template Variables | Medium | 2 days | Parameterized templates |
| CA-026 | Trigger Artifact Resolution | Medium | 2 days | Rich trigger handling |
| CA-027 | Stage Restart Semantics | Medium | 2 days | Failure recovery |
| CA-028 | Execution Windows Specification | Low | 1 day | Scheduling constraints |

---

## Summary Matrix

| Capability | Spinnaker Orca | AGENT-33 Current | Gap | Priority |
|------------|----------------|------------------|-----|----------|
| **DAG Execution** | Full support with concurrent branches | Dependency graph for artifacts only | Specify stage-level DAG execution | High |
| **Expression Language** | SpEL with rich functions | Simple variable substitution | Define AEL specification | High |
| **Synthetic Stages** | Before/After stage injection | Not specified | Add synthetic phase composition | High |
| **Context Sharing** | Stage outputs flow downstream | Handoff documents | Formalize context model | High |
| **Conditional Execution** | Expression-based skip | Trigger conditions | Add stage-level conditions | High |
| **Failure Handling** | Rich options (failPipeline, continue, etc.) | Implicit | Specify failure semantics | High |
| **Pause/Resume** | Full support + manual judgment | Session-based | Add execution control states | Medium |
| **Pipeline Templates** | Variables, inheritance, versioning | Basic templates | Enhance template spec | Medium |
| **Trigger Artifacts** | Rich artifact binding | Trigger catalog exists | Add artifact resolution | Medium |
| **Stage Restart** | Restart from failed stage | Not specified | Add restart semantics | Medium |
| **Message Queue** | Keiko delay queue | Not specified | Reference architecture | Low |
| **Execution Windows** | Time-based restrictions | Not specified | Add scheduling spec | Low |

---

## Appendix: Key Orca Source References

| Component | Path | Purpose |
|-----------|------|---------|
| StageDefinitionBuilder | `orca-api/.../StageDefinitionBuilder.java` | Stage composition API |
| RunTaskHandler | `orca-queue/.../RunTaskHandler.kt` | Task execution |
| StartStageHandler | `orca-queue/.../StartStageHandler.kt` | Stage initialization |
| CompleteStageHandler | `orca-queue/.../CompleteStageHandler.kt` | Stage completion |
| ExpressionAware | `orca-queue/.../ExpressionAware.kt` | Expression evaluation |
| PipelineExecutionImpl | `orca-core/.../PipelineExecutionImpl.java` | Execution model |
| StageExecutionImpl | `orca-core/.../StageExecutionImpl.java` | Stage model |

---

## References

- [Spinnaker Orca README](https://github.com/spinnaker/spinnaker/blob/master/orca/README.md)
- [Orca Service Overview](https://spinnaker.io/docs/community/contributing/code/developer-guides/service-overviews/orca/)
- [Pipeline Expressions Guide](https://spinnaker.io/docs/guides/user/pipeline/expressions/)
- [Pipeline Expression Reference](https://spinnaker.io/docs/reference/pipeline/expressions/)
- [Spinnaker Architecture](https://spinnaker.io/docs/reference/architecture/microservices-overview/)
- [Pipeline Templates](https://spinnaker.io/docs/guides/user/pipeline/pipeline-templates/)
