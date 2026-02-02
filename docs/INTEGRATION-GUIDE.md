# Integration Guide

How to use AGENT-33 in your projects. Choose the integration pattern that fits your architecture.

For messaging platform integration (Telegram, Discord, Slack, WhatsApp), see the [engine integration guide](../engine/docs/integration-guide.md).

## As a REST API Client

AGENT-33 exposes a full REST API. Any language or tool that speaks HTTP can integrate.

### Authentication

```bash
# Get a JWT token
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Use the token in subsequent requests
curl http://localhost:8000/api/v1/agents/ \
  -H "Authorization: Bearer <your-jwt-token>"

# Or use an API key
curl http://localhost:8000/api/v1/agents/ \
  -H "X-API-Key: your-api-key"
```

### Chat Completions

```python
import httpx

client = httpx.Client(
    base_url="http://localhost:8000",
    headers={"Authorization": "Bearer <token>"}
)

response = client.post("/api/v1/chat", json={
    "message": "Analyze this code for security issues",
    "model": "llama3.2"
})
print(response.json())
```

```javascript
const response = await fetch("http://localhost:8000/api/v1/chat", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer <token>"
  },
  body: JSON.stringify({
    message: "Analyze this code for security issues",
    model: "llama3.2"
  })
});
const data = await response.json();
```

### Agent Invocation

```python
# List available agents
agents = client.get("/api/v1/agents/").json()

# Invoke a specific agent
result = client.post("/api/v1/agents/summarizer/invoke", json={
    "text": "Long document to summarize..."
})
print(result.json())
```

### Workflow Execution

```python
# Create a workflow
client.post("/api/v1/workflows/", json={
    "name": "my-pipeline",
    "steps": [
        {"id": "step1", "action": "invoke_agent", "agent": "worker", "inputs": {"text": "{{ inputs.query }}"}},
        {"id": "step2", "action": "validate", "inputs": {"data": "{{ steps.step1.output }}"}, "depends_on": ["step1"]}
    ]
})

# Execute it
result = client.post("/api/v1/workflows/my-pipeline/execute", json={
    "query": "What are the key risks?"
})
print(result.json())
```

## Via Webhooks

Trigger workflows from external systems like GitHub, CI/CD pipelines, or custom applications.

```bash
# Register a webhook-triggered workflow
curl -X POST http://localhost:8000/api/v1/webhooks/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "on-push",
    "workflow": "code-review-pipeline",
    "secret": "webhook-secret-123",
    "events": ["push"]
  }'
```

AGENT-33 validates webhook signatures, extracts the payload, and passes it as workflow inputs. Dead-letter queuing handles delivery failures.

## As a Docker Sidecar

Add AGENT-33 to an existing Docker Compose stack:

```yaml
# In your existing docker-compose.yml
services:
  your-app:
    image: your-app:latest
    networks:
      - shared

  # Add AGENT-33 services
  agent33-api:
    image: agent33:latest
    environment:
      - DATABASE_URL=postgresql+asyncpg://agent33:agent33@agent33-db:5432/agent33
      - REDIS_URL=redis://agent33-redis:6379/0
      - NATS_URL=nats://agent33-nats:4222
      - OLLAMA_BASE_URL=http://agent33-ollama:11434
    networks:
      - shared
    depends_on:
      - agent33-db
      - agent33-redis
      - agent33-nats
      - agent33-ollama

  agent33-ollama:
    image: ollama/ollama:latest
    networks:
      - shared

  agent33-db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: agent33
      POSTGRES_USER: agent33
      POSTGRES_PASSWORD: agent33
    networks:
      - shared

  agent33-redis:
    image: redis:7-alpine
    networks:
      - shared

  agent33-nats:
    image: nats:2-alpine
    command: ["--jetstream"]
    networks:
      - shared

networks:
  shared:
```

Your application then calls AGENT-33 at `http://agent33-api:8000` within the shared Docker network.

## Plugin Development

Extend AGENT-33 with custom tools and actions using Python entry points.

```python
# my_plugin/tools.py
from agent33.tools.base import Tool, ToolContext, ToolResult

class MyCustomTool(Tool):
    name = "my_tool"
    description = "Does something custom"

    async def execute(self, context: ToolContext) -> ToolResult:
        # Your tool logic here
        return ToolResult(output="Result from my tool")
```

Register via `pyproject.toml`:

```toml
[project.entry-points."agent33.tools"]
my_tool = "my_plugin.tools:MyCustomTool"
```

See the [engine contributing guide](../engine/docs/contributing.md) for full plugin development details.

## Programmatic API (Python)

For Python projects, use the async client library directly:

```python
from agent33.client import AsyncAgent33Client

client = AsyncAgent33Client(base_url="http://localhost:8000", api_key="your-key")

# Execute a workflow
result = await client.execute_workflow(
    workflow_name="summarize-and-review",
    inputs={"text": "Your text here"}
)

# Access results
print(result.output)
print(result.lineage)  # Full trace of all steps
```

## Best Practices

- **Use JWT tokens** for server-to-server communication; API keys for quick scripting
- **Set timeouts** on HTTP clients — LLM inference can take 10-60 seconds for complex prompts
- **Handle streaming** responses for chat endpoints in production to improve perceived latency
- **Monitor /health** — poll the health endpoint to detect service degradation
- **Use webhooks** for event-driven architectures instead of polling
- **Rate limit** client requests to match your hardware capacity (especially with local inference)
- **Cache agent definitions** locally — they rarely change, but querying them repeatedly wastes bandwidth
- **Use dependency injection** to swap between direct API calls and local client library depending on deployment context

## Common Patterns

### Pattern 1: Async Task Queue Integration

Trigger workflows asynchronously and poll for results:

```python
import asyncio
import httpx

async def process_documents(doc_list):
    client = httpx.AsyncClient(base_url="http://localhost:8000")

    # Start workflow
    response = await client.post("/api/v1/workflows/analyze-docs/execute", json={
        "docs": doc_list
    })
    execution_id = response.json()["id"]

    # Poll for completion
    while True:
        status = await client.get(f"/api/v1/workflows/{execution_id}")
        if status.json()["state"] == "completed":
            return status.json()["output"]
        await asyncio.sleep(2)
```

### Pattern 2: Microservice Chain

Decompose your pipeline into microservices, each calling AGENT-33:

```
Data Source → Service A → (calls AGENT-33 Worker) → Service B → (calls AGENT-33 Reviewer) → Database
```

Each service is independently deployable and testable.

### Pattern 3: GenAI Augmentation

Add AI reasoning to existing APIs without rewriting them:

```python
# Your existing FastAPI endpoint
@app.get("/api/articles/{article_id}")
async def get_article(article_id: str):
    article = await db.get_article(article_id)

    # Enrich with AI reasoning
    agent33 = AsyncAgent33Client(...)
    analysis = await agent33.invoke_agent(
        agent_name="analyzer",
        inputs={"text": article.content}
    )

    return {
        "article": article,
        "ai_analysis": analysis.output
    }
```

## Further Reading

- [API Reference](../engine/docs/api-reference.md) — Full endpoint documentation
- [Security Guide](../engine/docs/security-guide.md) — Authentication and encryption details
- [Messaging Integration](../engine/docs/integration-guide.md) — Telegram, Discord, Slack, WhatsApp
- [Deployment Guide](DEPLOYMENT.md) — Production setup and hardening
- [Architecture Overview](ARCHITECTURE-OVERVIEW.md) — System design and components
