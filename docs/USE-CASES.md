# Use Cases

Real-world scenarios where AGENT-33 excels. Each category includes key components used and links to detailed examples.

For implementation examples with code, see the [engine use cases guide](../engine/docs/use-cases.md).

## DevOps Automation

### Code Review Pipeline

An orchestrator receives a pull request, assigns a code reviewer agent to analyze changes, a security agent to scan for vulnerabilities, and a documentation agent to check for missing docs. Results are aggregated and posted as a review.

**Key components:** Workflows, agent invocation, webhooks, parallel execution

### Deployment Orchestration

A workflow monitors a release branch, runs tests, builds containers, deploys to staging, executes smoke tests, and promotes to production — with human approval gates at critical steps.

**Key components:** Workflows, sensors, conditional steps, automation scheduler

## Content Generation

### Multi-Agent Writing

A research agent gathers source material, a writer agent produces a draft, an editor agent refines tone and structure, and a fact-checker agent validates claims. Each agent has a specialized system prompt.

**Key components:** Agents with specialized roles, sequential workflow, memory/RAG

### Research Synthesis

Ingest multiple documents via the RAG pipeline, then use an analyst agent to synthesize findings, identify contradictions, and produce a structured report.

**Key components:** Document ingestion, RAG, long-term memory, agent invocation

## Research and Analysis

### Repository Intake

The `agent33 intake` command analyzes an external repository: structure, dependencies, patterns, and architecture. Results are stored in `collected/` for downstream agents to use.

**Key components:** CLI, tools (file operations), memory, agent runtime

### Competitive Analysis

A research workflow fetches competitor information, compares features against AGENT-33, identifies gaps, and produces a structured comparison.

**Key components:** Web fetch tool, workflows, agent roles, document generation

## Customer Support

### Multi-Platform Bot

A single agent handles customer queries across Telegram, Discord, Slack, and WhatsApp. Channel pairing routes conversations to the right agent. RAG retrieves relevant documentation for answers.

**Key components:** Messaging adapters, channel pairing, RAG, session memory

### Knowledge Retrieval

Ingest product documentation, FAQs, and support tickets into the vector store. A support agent retrieves relevant context before answering, reducing hallucination.

**Key components:** Document ingestion, pgvector, RAG pipeline, context assembly

## Data Processing

### ETL Pipelines

Workflows define extraction, transformation, and loading steps as a DAG. Each step can invoke specialized agents or run commands. Checkpoints enable resume after failure.

**Key components:** Workflow DAG, run_command action, checkpoints, error handling

### Document Ingestion

Bulk-ingest documents (PDF, markdown, text) into the vector store with chunking, embedding, and metadata tagging. Use retention policies to manage storage.

**Key components:** Ingestion pipeline, embeddings, long-term memory, retention

## Security and Compliance

### Audit Workflows

Every agent invocation and workflow execution produces lineage records. Audit workflows can query these records to verify compliance with policies.

**Key components:** Observability, lineage tracking, replay, structured logging

### Policy Enforcement

Governance rules constrain what agents can do: allowlists restrict commands and domains, autonomy budgets limit scope, and review protocols require approval for sensitive operations.

**Key components:** Allowlists, RBAC, governance policies, tool governance

## Knowledge Management

### RAG-Powered Q&A

Build an internal knowledge base by ingesting company documents, then deploy a Q&A agent that retrieves relevant context before answering. Sessions maintain conversation history.

**Key components:** RAG, document ingestion, session memory, context windowing

### Session-Spanning Memory

Agents remember context across sessions. Long-term memory stores important facts and decisions. When a user returns, the agent retrieves relevant history.

**Key components:** Long-term memory, session management, context assembly

## Design Your Own

AGENT-33's building blocks combine to support custom use cases:

1. **Define agents** with specialized system prompts and schemas
2. **Build workflows** as DAGs of agent invocations and actions
3. **Connect triggers** via webhooks, cron schedules, or sensors
4. **Add memory** with document ingestion and RAG retrieval
5. **Enforce governance** with allowlists, budgets, and review gates

See the [Workflow Guide](../engine/docs/workflow-guide.md) and [Agent Guide](../engine/docs/agent-guide.md) for building custom solutions.
