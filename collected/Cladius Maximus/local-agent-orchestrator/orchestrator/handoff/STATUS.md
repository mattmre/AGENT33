# STATUS (quick refresh)

## Repo Purpose
Runs a dedicated Ollama instance for Qwen3-Coder on port 11435, with a pinned 16K context model qwen3c-30b-16k:latest.

## Running Services
- qwen_ollama on localhost:11435 → container port 11434
- Volume: qwen_ollama_data stores models persistently

## Key Commands
Start:
- docker compose up -d --pull always

Bootstrap/pin model:
- powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-qwen.ps1
Warm/pin model:
- powershell -ExecutionPolicy Bypass -File .\scripts\warmup-pin.ps1

Test:
- Invoke-RestMethod GET http://localhost:11435/api/tags
- POST generate to /api/generate

## Agent Protocol
- Orchestrator edits: PLAN.md, TASKS.md, DECISIONS.md
- Workers take tasks, make branches, keep diffs small, run checks, update TASKS.

## Known Constraints
- Single GPU: generation is effectively serialized (queued). Use multiple agents to parallelize I/O + testing + review, not simultaneous token generation.
