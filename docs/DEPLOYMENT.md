# Deployment Guide

How to run AGENT-33 in production. For development setup, see the [Quick Start](QUICKSTART.md).

## Pre-Deployment Checklist

- [ ] Change all default secrets (`API_SECRET_KEY`, `JWT_SECRET`, `ENCRYPTION_KEY`)
- [ ] Set strong PostgreSQL credentials (replace default `agent33`/`agent33`)
- [ ] Generate a Fernet encryption key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- [ ] Configure resource limits appropriate for your hardware
- [ ] Set up a reverse proxy with TLS
- [ ] Plan a backup strategy for PostgreSQL data
- [ ] Review tool allowlists before enabling agent tools
- [ ] Test the health endpoint and all external integrations
- [ ] Set up monitoring and alerting

## Production Docker Compose

AGENT-33 ships with a production overlay that applies resource limits, disables exposed ports, and adds health checks:

```bash
cd engine
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### What the production overlay changes

| Service | Changes |
|---------|---------|
| **api** | Restart `always`, 2 CPU / 2 GB RAM, no exposed ports, log level `warning`, health check every 30s |
| **ollama** | Restart `always`, 8 GB RAM, GPU reservation, health check on `/api/tags` |
| **postgres** | Restart `always`, 1 CPU / 1 GB RAM, no exposed ports |
| **redis** | Restart `always`, 0.5 CPU / 256 MB RAM, no exposed ports |
| **nats** | Restart `always`, 0.5 CPU / 256 MB RAM, no exposed ports, health check on `/healthz` |

Adjust these limits based on your available hardware.

## Environment Configuration

Create a production `.env` file:

```bash
# Core settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
ENVIRONMENT=production

# Security (CHANGE THESE)
API_SECRET_KEY=your-very-secure-random-key-minimum-32-chars
JWT_SECRET=another-random-key-minimum-32-chars
ENCRYPTION_KEY=<output-from-fernet-key-generation>
JWT_EXPIRATION_HOURS=24
API_KEY_EXPIRATION_DAYS=90

# Database
DATABASE_URL=postgresql+asyncpg://agent33:strong-password@postgres:5432/agent33?pool_size=20&max_overflow=10
SQLALCHEMY_ECHO=false

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_EXPIRATION_SECONDS=86400

# Ollama
OLLAMA_BASE_URL=http://ollama:11434
DEFAULT_MODEL=llama3.2
MODEL_TIMEOUT_SECONDS=120

# NATS
NATS_URL=nats://nats:4222

# Logging
LOG_LEVEL=warning
LOG_FORMAT=json

# Observability
ENABLE_METRICS=true
METRICS_PORT=9090
ENABLE_TRACING=true
TRACE_SAMPLE_RATE=0.1

# Security
ENABLE_PROMPT_INJECTION_DETECTION=true
MAX_INPUT_TOKENS=4096
RATE_LIMIT_PER_MINUTE=60

# Features
ENABLE_WEBHOOKS=true
ENABLE_RAG=true
ENABLE_PLUGINS=true
```

## Reverse Proxy Setup

Place a reverse proxy in front of the API container for TLS termination. Example with Nginx:

```nginx
upstream agent33_api {
    server localhost:8000;
}

server {
    listen 443 ssl http2;
    server_name agent33.example.com;

    ssl_certificate     /etc/ssl/certs/agent33.pem;
    ssl_certificate_key /etc/ssl/private/agent33.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://agent33_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts for LLM inference
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
        proxy_connect_timeout 10s;

        # Buffering for large responses
        proxy_buffering off;
    }

    # Health check endpoint (no auth required)
    location /health {
        proxy_pass http://agent33_api/health;
        access_log off;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name agent33.example.com;
    return 301 https://$server_name$request_uri;
}
```

## Database Production Configuration

### Connection Pooling

For high-traffic deployments, the production `.env` already configures connection pooling:

```
DATABASE_URL=postgresql+asyncpg://agent33:password@postgres:5432/agent33?pool_size=20&max_overflow=10
```

Tune `pool_size` based on concurrent API workers (typically workers * 2).

### Backups

Set up automated daily backups with `pg_dump`:

```bash
# Create a backup script: /usr/local/bin/backup-agent33.sh
#!/bin/bash
set -e
BACKUP_DIR="/backups/agent33"
mkdir -p "$BACKUP_DIR"

docker compose exec -T postgres pg_dump -U agent33 agent33 | \
    gzip > "$BACKUP_DIR/agent33-$(date +%Y%m%d-%H%M%S).sql.gz"

# Retain 30 days of backups
find "$BACKUP_DIR" -name "agent33-*.sql.gz" -mtime +30 -delete

echo "Backup complete: $(ls -lh "$BACKUP_DIR" | tail -1)"
```

Add to crontab:

```bash
# Run daily at 2 AM
0 2 * * * /usr/local/bin/backup-agent33.sh >> /var/log/agent33-backup.log 2>&1
```

### Pgvector Tuning

For large embedding collections (100k+), create an HNSW index for faster similarity search:

```sql
-- Connect to the database and run this once
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Verify the index
SELECT * FROM pg_indexes WHERE tablename = 'embeddings';
```

## Redis Persistence

Redis is configured with RDB snapshots by default. For production durability, enable AOF:

```bash
# Create a redis.conf override file
echo "appendonly yes" > /path/to/redis-prod.conf
echo "appendfsync everysec" >> /path/to/redis-prod.conf
```

Update `docker-compose.prod.yml`:

```yaml
services:
  redis:
    volumes:
      - /path/to/redis-prod.conf:/usr/local/etc/redis/redis.conf:ro
    command: redis-server /usr/local/etc/redis/redis.conf
```

## NATS Clustering for High Availability

For multi-node deployments, NATS supports clustering. Set up a 3-node cluster:

```yaml
services:
  nats-1:
    image: nats:2-alpine
    command: >
      -c /etc/nats/nats.conf
      --cluster nats://0.0.0.0:6222
      --cluster_name AGENT33
  nats-2:
    image: nats:2-alpine
    command: >
      -c /etc/nats/nats.conf
      --cluster nats://0.0.0.0:6222
      --routes=nats://nats-1:6222
  nats-3:
    image: nats:2-alpine
    command: >
      -c /etc/nats/nats.conf
      --cluster nats://0.0.0.0:6222
      --routes=nats://nats-1:6222
```

See [NATS documentation](https://docs.nats.io/running-a-nats-service/configuration/clustering) for full clustering setup.

## Monitoring and Observability

### Health Endpoint

Poll `/health` for service status:

```bash
curl -s http://localhost:8000/health | jq '.'
```

Returns:

```json
{
  "status": "healthy",
  "timestamp": "2025-02-01T12:34:56Z",
  "services": {
    "ollama": "ok",
    "redis": "ok",
    "postgres": "ok",
    "nats": "ok"
  }
}
```

### Structured Logs

AGENT-33 uses `structlog` for JSON-formatted logs:

```bash
# View API logs
docker compose logs -f api

# Filter by level
docker compose logs api | jq 'select(.level == "error")'

# Filter by component
docker compose logs api | jq 'select(.component == "workflow")'
```

### Metrics

The observability module exposes Prometheus-compatible metrics on port 9090:

```bash
curl http://localhost:9090/metrics
```

Key metrics:

- `agent33_request_count_total` — Total requests by endpoint and method
- `agent33_request_duration_seconds` — Request latency histogram
- `agent33_agent_invocations_total` — Agent executions by agent name
- `agent33_workflow_executions_total` — Workflow executions by workflow name
- `agent33_workflow_duration_seconds` — Workflow execution time
- `agent33_llm_tokens_total` — Total tokens consumed by model

Connect your monitoring stack (Prometheus, Grafana, DataDog, etc.) to scrape these metrics.

### Tracing

Enable distributed tracing to track requests across services:

```bash
# Set in .env
ENABLE_TRACING=true
TRACE_SAMPLE_RATE=0.1
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
```

## Security Hardening

### Secrets Management

Never commit secrets to version control. Use a secrets management solution:

```bash
# Example: Using HashiCorp Vault
VAULT_ADDR=https://vault.example.com
API_SECRET_KEY=$(vault kv get -field=api_secret_key secret/agent33)
```

### Network Isolation

Run AGENT-33 in a private network and restrict access:

```bash
# Allow only your CI/CD and application servers
ufw allow from 10.0.1.0/24 to any port 8000
ufw deny from any to any port 8000
```

### API Key Rotation

Rotate API keys regularly:

```bash
# Generate a new key
curl -X POST http://localhost:8000/api/v1/auth/keys \
  -H "Authorization: Bearer <admin-token>"

# Mark old key as deprecated
curl -X PATCH http://localhost:8000/api/v1/auth/keys/<old-key-id> \
  -H "Content-Type: application/json" \
  -d '{"deprecated": true}'
```

## Scaling Strategies

### Current: Vertical Scaling

Scale up by adding CPU, RAM, and GPU resources to your host. Adjust resource limits in the production overlay accordingly.

### Planned: Horizontal Scaling

Distributed workflow execution across multiple nodes is on the roadmap. For now, use these strategies:

1. **Multiple API instances behind a load balancer** — Share PostgreSQL and Redis across instances
2. **Dedicated Ollama cluster** — Run inference on separate GPU-enabled nodes
3. **Workflow queue sharding** — Use NATS to distribute work across workers

## Troubleshooting

### Service Won't Start

Check logs:

```bash
docker compose logs api
docker compose logs ollama
docker compose logs postgres
```

Common issues:

- **Port conflicts** — Change `API_PORT` if 8000 is in use
- **Insufficient memory** — Allocate more RAM to Docker
- **Database connection** — Verify `DATABASE_URL` and credentials

### High Latency

1. Check GPU availability: `docker compose exec ollama ollama ps`
2. Monitor model size: `docker compose exec ollama ollama list`
3. Switch to smaller model if latency is unacceptable
4. Consider dedicated GPU hardware

### Memory Leaks

Monitor container memory:

```bash
docker stats agent33-api agent33-ollama
```

If memory usage grows unbounded:

1. Check for unclosed connections in logs
2. Increase swap space temporarily to identify the leak
3. File a bug report with reproduction steps

### Database Full

Monitor disk usage:

```bash
docker compose exec postgres df -h /var/lib/postgresql
```

If database is full:

1. Archive old conversation history
2. Delete old checkpoints
3. Expand the volume size

## Further Reading

- [Security Guide](../engine/docs/security-guide.md) — Full security hardening details
- [Integration Guide](INTEGRATION-GUIDE.md) — Connecting external systems
- [Architecture Overview](ARCHITECTURE-OVERVIEW.md) — System design and components
- [Engine README](../engine/README.md) — Docker services, volumes, configuration reference
- [CLAUDE.md](../CLAUDE.md) — Anti-corner-cutting rules and development guidelines
