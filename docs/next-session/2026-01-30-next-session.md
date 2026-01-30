# Next Session Briefing

## Session Context

The AGENT-33 engine is now fully implemented (Phases 1-10) and pushed to main. The codebase has ~7,700 lines of Python and ~8,300 lines of documentation.

## Immediate Action Items

### Priority 1: Hygiene

- [ ] Add `.gitignore` to engine/ excluding `__pycache__/`, `*.pyc`, `.env`, `.venv/`, `*.egg-info/`
- [ ] Remove accidentally committed `__pycache__` directories from git tracking
- [ ] Remove the `nul` file from the working directory
- [ ] Verify all `__init__.py` files are present and correct

### Priority 2: Validation

- [ ] Run `pip install -e ".[dev]"` in engine/ and verify installation
- [ ] Run `ruff check src/ tests/` and fix any lint issues
- [ ] Run `mypy src/` and fix type errors
- [ ] Run `pytest tests/` and fix any test failures
- [ ] Run `docker compose up` and verify all 5 services start
- [ ] Pull an Ollama model and test the chat endpoint end-to-end

### Priority 3: Integration Testing

- [ ] Test agent invocation flow end-to-end (create agent, invoke, get response)
- [ ] Test workflow execution with the example pipeline
- [ ] Test the CLI commands (agent33 status, agent33 init, agent33 run)
- [ ] Test the health dashboard at /v1/dashboard

### Priority 4: Enhancements

- [ ] Wire up security middleware to the FastAPI app (currently defined but not added to app)
- [ ] Connect AgentRuntime to workflow executor's invoke-agent action
- [ ] Wire up NATS message bus to messaging adapters in the app lifespan
- [ ] Add database connection pool to app lifespan (for checkpoints, long-term memory)
- [ ] Add Redis connection to app lifespan (for caching)

### Priority 5: Future Development

- [ ] Use feature branches + PRs for all future changes
- [ ] Implement remaining CA features marked as "Partial" in feature-roadmap.md
- [ ] Add more comprehensive unit tests for each module
- [ ] Performance benchmarking with real LLM workloads
- [ ] Horizontal scaling investigation (multiple API instances, NATS-based coordination)

## Key Files to Know

- Entry point: `engine/src/agent33/main.py`
- Config: `engine/src/agent33/config.py`
- All routes: `engine/src/agent33/api/routes/`
- Docker: `engine/docker-compose.yml`
- CLI: `engine/src/agent33/cli/main.py`
- Docs index: `engine/docs/` (12 guides)

## Architecture Quick Reference

```
CLI (typer) --> FastAPI --> Agent Runtime --> LLM Router --> Ollama / OpenAI
                  |
            Workflow Engine --> DAG Builder --> Actions (7 types)
                  |
            Security Middleware (JWT / API Key)
                  |
      PostgreSQL + pgvector | Redis | NATS
```
