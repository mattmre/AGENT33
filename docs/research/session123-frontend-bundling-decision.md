# Frontend Bundling Decision -- POST-1.3

**Session 123 -- April 2026**
**Status: APPROVED (DevOps panel, POST-P72 plan decision #5)**

## Decision

Build React frontend assets in CI via hatchling build hook; include in pip wheel;
verify via pip smoke test job.

## Context

AGENT-33's frontend is a React app in `frontend/`. The Python package (`engine/`)
does not currently bundle these assets. Users who `pip install agent33` get the
Python engine only, with no UI.

## Options Evaluated

| Option | Pros | Cons | Decision |
|---|---|---|---|
| Commit pre-built assets | Simple | Binary bloat in git; stale builds accumulate | REJECTED |
| Build in CI + include in wheel | Clean; reproducible; attested | Requires CI build step | SELECTED |
| Per-environment rebuild on install | Always fresh | Requires Node.js on every install machine | REJECTED |
| Ship without frontend (API-only) | Minimal | Breaks `agent33 start` + wizard experience | REJECTED |

## Selected Approach: Hatch Build Hook

### Build Process

1. `hatch build` triggers custom build hook in `engine/hatch_build.py`
2. Hook runs `npm ci && npm run build` in `frontend/`
3. Build outputs (Vite default: `frontend/dist/`) copied to `engine/src/agent33/static/ui/`
4. Wheel `[tool.hatch.build.targets.wheel]` includes `src/agent33/static/` automatically
   (it is inside the `src/agent33` package)
5. `agent33 start` / future UI serve endpoint reads from `agent33.static.ui_path()`

### CI

- Existing Docker build already builds frontend
- New `pip-smoke` job: build wheel with `AGENT33_SKIP_FRONTEND_BUILD=1`, install it,
  verify `agent33 --help` and basic import work
- Job runs after lint passes

### Repository Hygiene

- `frontend/dist/` already in `frontend/.gitignore`
- `engine/src/agent33/static/ui/` added to `engine/.gitignore`
- Pre-built assets never committed to git

## Implementation Checklist

- [x] ADR documented (this file)
- [x] `engine/hatch_build.py` -- custom build hook
- [x] `engine/pyproject.toml` -- register hook
- [x] `engine/src/agent33/static/__init__.py` -- `ui_path()` helper
- [x] `.gitignore` updates
- [x] `pip-smoke` CI job in `.github/workflows/ci.yml`
