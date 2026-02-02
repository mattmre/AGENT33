# Troubleshooting

Common issues and solutions when running AGENT-33.

## Docker Issues

### Services won't start

```bash
# Check container status
docker compose ps

# View logs for a specific service
docker compose logs api
docker compose logs ollama
```

**Common causes:**
- Port conflicts: Another service is using port 8000, 5432, 6379, 4222, or 11434. Change ports in `.env`.
- Insufficient memory: Ollama needs at least 8 GB RAM for most models. Check with `docker stats`.
- Docker not running: Ensure Docker Desktop or dockerd is active.

### Volume permission errors

On Linux, Docker volumes may have root ownership. Fix with:

```bash
sudo chown -R $(id -u):$(id -g) ./agent-definitions ./workflow-definitions
```

### GPU not detected by Ollama

Ensure NVIDIA drivers and the NVIDIA Container Toolkit are installed:

```bash
nvidia-smi                    # Should show your GPU
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi  # Should work inside Docker
```

If using the production overlay, verify the GPU reservation in `docker-compose.prod.yml`.

## Ollama Issues

### Model download fails

```bash
# Retry the pull
docker compose exec ollama ollama pull llama3.2

# Check Ollama logs
docker compose logs ollama
```

If downloads are slow, ensure your network allows connections to `registry.ollama.ai`.

### Out of memory (OOM)

Larger models need more RAM. Approximate requirements:

| Model | RAM Required |
|-------|-------------|
| llama3.2 (3B) | ~4 GB |
| llama3.2 (7B) | ~8 GB |
| llama3.1 (70B) | ~48 GB |

Switch to a smaller model or increase Docker's memory limit.

### Slow inference on CPU

Without a GPU, inference is significantly slower. Options:
- Use a smaller model (3B parameters or less)
- Add a GPU to your system
- Use an OpenAI-compatible cloud provider as fallback (set `OPENAI_API_KEY` and `OPENAI_BASE_URL`)

## PostgreSQL Issues

### Connection refused

```bash
# Check if postgres is running
docker compose ps postgres

# View postgres logs
docker compose logs postgres
```

**Common causes:**
- Container still starting (wait 10-15 seconds after `docker compose up`)
- Wrong credentials in `.env`
- Port 5432 occupied by a local PostgreSQL installation

### pgvector extension missing

The `pgvector/pgvector:pg16` image includes pgvector. If using a custom PostgreSQL image:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Migration errors

```bash
# Check current migration state
docker compose exec api python -m alembic current

# Run pending migrations
docker compose exec api python -m alembic upgrade head
```

## Redis and NATS Issues

### Redis connection timeout

```bash
docker compose logs redis
```

Check that Redis has enough memory. The default 256 MB limit in the production overlay may be too low for heavy usage.

### NATS connection issues

```bash
# Check NATS health
curl http://localhost:8222/healthz

# View NATS logs
docker compose logs nats
```

Ensure JetStream is enabled (the default compose config includes `--jetstream`).

## API Issues

### 503 Service Unavailable

The API server is running but one or more backend services are down. Check `/health` for details:

```bash
curl http://localhost:8000/health
```

Fix the degraded service before retrying.

### 401 Unauthorized

Authentication failed. Common causes:
- Expired JWT token — request a new token from `/api/v1/auth/token`
- Invalid API key — verify the key is correct and active
- Missing auth header — include `Authorization: Bearer <token>` or `X-API-Key: <key>`

### JWT errors

```
"detail": "Token has expired"
```

Tokens expire after `JWT_EXPIRE_MINUTES` (default: 60). Request a fresh token.

```
"detail": "Invalid token"
```

The `JWT_SECRET` may have changed since the token was issued. Request a new token.

### Request timeouts

LLM inference can be slow, especially on CPU. Increase client timeouts:

```python
client = httpx.Client(base_url="http://localhost:8000", timeout=120.0)
```

## Performance Issues

### Slow workflows

- Check which steps are bottlenecks in the workflow execution logs
- Use parallel execution for independent steps (`depends_on` only where needed)
- Use a smaller/faster model for less critical steps
- Enable GPU acceleration for Ollama

### High memory usage

```bash
docker stats
```

- Reduce model size if Ollama uses too much memory
- Limit PostgreSQL shared buffers if the database is consuming excess RAM
- Set Redis `maxmemory` to cap cache usage

## Debug Tools

### Enable debug logging

```bash
API_LOG_LEVEL=debug docker compose up -d api
docker compose logs -f api
```

### Check service health

```bash
curl http://localhost:8000/health | python -m json.tool
```

### Inspect workflow state

```bash
curl http://localhost:8000/api/v1/workflows/<workflow-id>/status \
  -H "Authorization: Bearer <token>"
```

### View NATS monitoring

```bash
curl http://localhost:8222/varz    # Server info
curl http://localhost:8222/jsz     # JetStream info
```

## Getting Help

When reporting issues, include:

1. **System info**: OS, Docker version, GPU (if any), RAM
2. **Steps to reproduce**: Commands you ran
3. **Logs**: Relevant output from `docker compose logs <service>`
4. **Health check output**: Result of `curl http://localhost:8000/health`
5. **Configuration**: Relevant `.env` settings (redact secrets)

File issues at [github.com/mattmre/AGENT33/issues](https://github.com/mattmre/AGENT33/issues).
