# Quick Start Guide

Get AGENT-33 running and send your first chat message, create an agent, and execute a workflow.

## Prerequisites

- **Docker** 24+ and **Docker Compose** 2.20+
- **16 GB RAM** minimum (LLM inference is memory-intensive)
- **GPU recommended** for faster inference (NVIDIA with CUDA drivers)
- **curl** or any HTTP client for testing

## Step 1: Clone and Configure

```bash
git clone https://github.com/mattmre/AGENT33.git
cd AGENT33/engine
cp .env.example .env
```

Edit `.env` if you want to change default ports or model settings. The defaults work out of the box.

## Step 2: Start Services

```bash
docker compose up -d
```

This starts five containers: the AGENT-33 API server, Ollama (local LLM), PostgreSQL with pgvector, Redis, and NATS.

Wait for all services to initialize (usually 30-60 seconds on first run).

## Step 3: Pull a Model

```bash
docker compose exec ollama ollama pull llama3.2
```

This downloads the default language model (~4 GB). You can use any Ollama-supported model — see [Ollama's library](https://ollama.ai/library) for options.

## Step 4: Verify Health

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "services": {
    "ollama": "ok",
    "redis": "ok",
    "postgres": "ok",
    "nats": "ok"
  }
}
```

If any service shows `"degraded"`, check `docker compose logs <service-name>`.

## Step 5: Send a Chat Message

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is AGENT-33?"}'
```

You should receive a streamed response from the local LLM.

## Step 6: Create an Agent

Create a file called `my-agent.json`:

```json
{
  "name": "summarizer",
  "description": "Summarizes text input into key bullet points",
  "model": "llama3.2",
  "system_prompt": "You are a concise summarizer. Given any text, extract the key points as bullet points. Be brief and accurate.",
  "input_schema": {
    "type": "object",
    "properties": {
      "text": {"type": "string", "description": "Text to summarize"}
    },
    "required": ["text"]
  }
}
```

Register it:

```bash
curl -X POST http://localhost:8000/api/v1/agents/ \
  -H "Content-Type: application/json" \
  -d @my-agent.json
```

Invoke it:

```bash
curl -X POST http://localhost:8000/api/v1/agents/summarizer/invoke \
  -H "Content-Type: application/json" \
  -d '{"text": "AGENT-33 is an autonomous AI agent orchestration engine. It runs locally with Ollama, supports multi-agent workflows, and includes security features like JWT auth and encryption."}'
```

## Step 7: Create a Workflow

Create a file called `my-workflow.json`:

```json
{
  "name": "summarize-and-review",
  "description": "Summarizes input text then reviews the summary for quality",
  "steps": [
    {
      "id": "summarize",
      "action": "invoke_agent",
      "agent": "summarizer",
      "inputs": {"text": "{{ inputs.text }}"}
    },
    {
      "id": "review",
      "action": "invoke_agent",
      "agent": "worker",
      "inputs": {"text": "Review this summary for accuracy and completeness: {{ steps.summarize.output }}"},
      "depends_on": ["summarize"]
    }
  ]
}
```

Register and execute:

```bash
# Register the workflow
curl -X POST http://localhost:8000/api/v1/workflows/ \
  -H "Content-Type: application/json" \
  -d @my-workflow.json

# Execute it
curl -X POST http://localhost:8000/api/v1/workflows/summarize-and-review/execute \
  -H "Content-Type: application/json" \
  -d '{"text": "Your long text to summarize and review goes here..."}'
```

## What's Next

| Goal | Guide |
|------|-------|
| Understand the architecture | [Architecture Overview](ARCHITECTURE-OVERVIEW.md) |
| Explore the full API | [API Reference](../engine/docs/api-reference.md) |
| Build complex workflows | [Workflow Guide](../engine/docs/workflow-guide.md) |
| Integrate with your project | [Integration Guide](INTEGRATION-GUIDE.md) |
| Deploy to production | [Deployment Guide](DEPLOYMENT.md) |
| Connect messaging platforms | [Integration Guide (engine)](../engine/docs/integration-guide.md) |
| Learn about security | [Security Guide](../engine/docs/security-guide.md) |
| Browse all documentation | [Documentation Hub](README.md) |
