# Session 127 Research Memo — POST-CLUSTER P-ENV v2

## Decision

Implement P-ENV v2 as a **first-run environment bootstrap upgrade** centered on the existing CLI wizard and local development flow.

## Locked implementation surface

1. Refresh environment detection during the wizard so model recommendations are based on current hardware/tooling, not stale cached state.
2. When the user chooses Ollama in `agent33 wizard`, attempt zero-touch local setup in this order:
   - use a reachable local Ollama service if one already exists
   - start `ollama serve` automatically when the local binary exists but the service is not running
   - otherwise start the existing bundled Docker Compose Ollama service (`--profile local-ollama`) when available
3. Automatically inspect available Ollama models and download the recommended model when it is missing.
4. Standardize the generated env output on `OLLAMA_DEFAULT_MODEL`, which is the runtime config key already used by the engine.
5. Update setup docs so they describe the automated path and keep manual pull commands as fallback/operator guidance.

## Why this scope

The repo already contains all the pieces needed for a safe local/bootstrap automation path:

- `agent33.env.detect` already computes hardware-aware model recommendations
- `agent33.cli.wizard` is the first-run UX surface
- `engine/docker-compose.yml` already ships a bundled Ollama service behind `local-ollama`
- the runtime already consumes `OLLAMA_DEFAULT_MODEL`

That makes wizard/bootstrap automation the smallest complete implementation that upgrades the actual user experience without inventing new deployment surfaces.

## Non-goals

- No OS-level package-manager installers (`winget`, `brew`, `curl | sh`) in this slice
- No production/k8s model lifecycle automation
- No marketplace/community-submission work in this PR

## Required message to future sessions

Treat this PR as the local bootstrap foundation for model-aware setup. Follow-on POST-CLUSTER work should build on this path instead of reopening first-run Ollama provisioning from scratch.
