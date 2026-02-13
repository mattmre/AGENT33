# Next Session Briefing

Last updated: 2026-02-13T18:00

## Current State
- **Branch**: `feat/phase-13-code-execution` (working branch, has uncommitted cleanup changes)
- **Main**: clean, 143 tests passing
- **Open PRs**: 1
  - #27: Phase 13 — Code execution layer and tools-as-code (197 tests, 0 lint errors)
- **Phases 1-13, 21**: Complete (Phase 13 pending merge via PR #27)
- **Phases 14-20**: Planned (see `docs/phases/`)

## What Was Done This Session (2026-02-13, Session 3)
1. **CLAUDE.md overhaul** — Added required prefix, common commands, architecture overview, tool config, phase dependency chain, Windows platform notes
2. **RSMFConverter cleanup** — Deleted `core/phases/` (40 phase files + README) and `core/user-guide/` (4 stub files) — all leftover from a different project
3. **Full repo security scan** (4 parallel agents) — scanned for credentials, PII, internal project refs, infrastructure exposure
4. **Sensitive data remediation**:
   - Removed `agent-33` GitHub handle from 6 tool definition YAMLs
   - Removed `agent-33.dev` unregistered domain from 11 files (schemas, agent defs, plugin spec)
   - Normalized `<owner>` placeholders to `agent-33` in 3 files
   - Removed `EDCTool` internal project reference from `RELATIONSHIP_TYPES.md`
   - Fixed stale `core/phases/` references in `templates.md` and `refinement.mdc` → `docs/phases/`
5. **Verified clean**: zero remaining references to `agent-33`, `agent-33.dev`, `<owner>` URLs, or any private repos

### Security Scan Findings (for Phase 14 scope)
The infrastructure scan also flagged code security issues (not data leaks):
- SHA-256 password hashing without salt in `auth.py:64` — needs bcrypt/argon2
- `change-me-in-production` defaults warn but don't block startup
- NATS monitoring port 8222 exposed without auth
- CORS `allow_methods=["*"]`, `allow_headers=["*"]`
- `run_command.py` env replacement drops PATH on Windows
- Auth bypass for all paths starting with `/docs` (prefix too broad)
These are tracked for Phase 14 implementation.

## Priority 1: Research & Analysis Sprint

Analyze the following repos and papers for patterns, techniques, and features to integrate into AGENT-33. Use the `agent33 intake` workflow or research dossier templates in `docs/research/templates/`.

### Research Papers
| Resource | Focus Area | URL |
|----------|-----------|-----|
| Multi-Agent RL Survey | Multi-agent coordination, RL for agent orchestration | https://arxiv.org/abs/2602.11865 |
| Building Skills for Claude (Anthropic) | Claude skill architecture, plugin patterns | https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf |

### Repos — Agent Frameworks & Orchestration
| Repo | Focus Area | URL |
|------|-----------|-----|
| openai/swarm | Multi-agent orchestration patterns, handoffs | https://github.com/openai/swarm |
| agent0ai/agent-zero | Autonomous agent framework | https://github.com/agent0ai/agent-zero |
| parcadei/Continuous-Claude-v3 | Continuous Claude patterns | https://github.com/parcadei/Continuous-Claude-v3 |
| anthropics/claude-code | Claude Code CLI, agent SDK | https://github.com/anthropics/claude-code |
| anomalyco/opencode | Open-source code agent | https://github.com/anomalyco/opencode |
| alexzhang13/rlm | RL for language models | https://github.com/alexzhang13/rlm |
| Tencent/WeKnora | Knowledge-augmented agents | https://github.com/Tencent/WeKnora |
| HKUDS/AI-Researcher | AI research agent | https://github.com/HKUDS/AI-Researcher |

### Repos — Skills, Plugins & Workflows
| Repo | Focus Area | URL |
|------|-----------|-----|
| anthropics/claude-plugins-official | Official Claude plugin patterns | https://github.com/anthropics/claude-plugins-official |
| ComposioHQ/awesome-claude-skills | Claude skill catalog | https://github.com/ComposioHQ/awesome-claude-skills |
| nextlevelbuilder/ui-ux-pro-max-skill | UI/UX skill for Claude | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill |
| triggerdotdev/trigger.dev | Background job orchestration, workflow patterns | https://github.com/triggerdotdev/trigger.dev |
| breaking-brake/cc-wf-studio | Claude Code workflow studio | https://github.com/breaking-brake/cc-wf-studio/ |
| Zie619/n8n-workflows | N8N workflow patterns | https://github.com/Zie619/n8n-workflows |

### Repos — Tools & Capabilities
| Repo | Focus Area | URL |
|------|-----------|-----|
| raphaelmansuy/edgequake | Edge AI patterns | https://github.com/raphaelmansuy/edgequake |
| LaurieWired/GhidraMCP | MCP server for reverse engineering | https://github.com/LaurieWired/GhidraMCP |
| katanaml/sparrow | Document processing, OCR pipeline | https://github.com/katanaml/sparrow |
| PaddlePaddle/PaddleOCR | OCR engine | https://github.com/PaddlePaddle/PaddleOCR |
| Varun-Patkar/ChromePilot | Browser automation agent | https://github.com/Varun-Patkar/ChromePilot |
| HKUDS/RAG-Anything | RAG pipeline patterns | https://github.com/HKUDS/RAG-Anything |
| livekit/livekit | Real-time communication, voice/video | https://github.com/livekit/livekit |
| yt-dlp/yt-dlp | Media download/processing | https://github.com/yt-dlp/yt-dlp |

### Repos — Security & DevOps
| Repo | Focus Area | URL |
|------|-----------|-----|
| aquasecurity/trivy | Security scanning, vulnerability detection | https://github.com/aquasecurity/trivy |
| madster456/envhush-cli | Secret/env management | https://github.com/madster456/envhush-cli |
| makeplane/plane | Project management, issue tracking | https://github.com/makeplane/plane |
| x1xhlol/system-prompts-and-models-of-ai-tools | System prompt patterns | https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools |

### Suggested Analysis Approach
1. **Triage**: Quickly assess each repo's relevance to AGENT-33 (skip if minimal overlap)
2. **Dossier**: For high-relevance repos, create research dossiers in `docs/research/repo_dossiers/`
3. **Extract patterns**: Identify specific patterns, architectures, or features to adopt
4. **Integration report**: Write a summary mapping findings to AGENT-33 phases/components
5. **Phase updates**: Update relevant phase docs with new insights

### Key Questions to Answer
- What orchestration patterns from swarm/agent-zero can improve our workflow engine?
- What skill/plugin architecture from Claude's ecosystem should we adopt?
- What RAG patterns from RAG-Anything can improve our memory/RAG pipeline?
- What security scanning from trivy can inform Phase 14?
- What browser automation patterns from ChromePilot/GhidraMCP can improve our browser tool?
- What workflow patterns from trigger.dev/n8n can improve our automation layer?

## Priority 2: Review & Merge PR #27 (Phase 13)
- Review the PR, then merge to main
- After merge, delete the `feat/phase-13-code-execution` branch
- Verify 197 tests still pass on main

## Priority 3: Phase 14 — Security Hardening & Prompt Injection Defense

Per `docs/phases/PHASE-14-SECURITY-HARDENING-AND-PROMPT-INJECTION-DEFENSE.md`:
- **Depends on**: Phase 13 (PR #27)
- **Blocks**: Phase 15
- **Owner**: Security Agent (T22)

### Remaining Engine Security Gaps (from `docs/sessions/research-security-gaps.md`)

**IDOR ownership validation** — 8 endpoints with no access control:
| Endpoint | File | Issue |
|----------|------|-------|
| GET /v1/memory/sessions/{id}/observations | memory_search.py:53-76 | No ownership check |
| POST /v1/memory/sessions/{id}/summarize | memory_search.py:79-98 | No ownership check |
| GET /v1/agents/by-id/{id} | agents.py:115-127 | No access control |
| GET /v1/agents/{name} | agents.py:138-147 | No access control |
| POST /v1/agents/{name}/invoke | agents.py:160-190 | No ownership check |
| GET /v1/workflows/{name} | workflows.py:68-74 | No access control |
| POST /v1/workflows/{name}/execute | workflows.py:102-132 | No ownership check |
| DELETE /v1/auth/api-keys/{key_id} | auth.py:79-84 | No ownership check |

**Code security issues from this session's scan:**
- SHA-256 password hashing → bcrypt/argon2 (`auth.py:64`)
- Default secrets warn-only → enforce in production mode (`config.py:16,33`)
- NATS port 8222 exposed without auth (`docker-compose.yml:77-79`)
- Overly permissive CORS methods/headers (`main.py:261-262`)
- `run_command.py` env replacement drops PATH on Windows (`:49-58`)
- Auth bypass prefix too broad for `/docs` (`middleware.py:18`)

## Key Files to Know
| Purpose | Path |
| --- | --- |
| Entry point | `engine/src/agent33/main.py` |
| Config | `engine/src/agent33/config.py` |
| Agent registry | `engine/src/agent33/agents/registry.py` |
| Agent definitions | `engine/agent-definitions/*.json` |
| Tool registry | `engine/src/agent33/tools/registry.py` |
| Tool registry entry | `engine/src/agent33/tools/registry_entry.py` |
| Tool definitions | `engine/tool-definitions/*.yml` |
| **Execution layer** | `engine/src/agent33/execution/` |
| **CodeExecutor** | `engine/src/agent33/execution/executor.py` |
| **Execution models** | `engine/src/agent33/execution/models.py` |
| **Input validation** | `engine/src/agent33/execution/validation.py` |
| **CLI adapter** | `engine/src/agent33/execution/adapters/cli.py` |
| Security: injection | `engine/src/agent33/security/injection.py` |
| Security: middleware | `engine/src/agent33/security/middleware.py` |
| Security: allowlists | `engine/src/agent33/security/allowlists.py` |
| Security spec | `core/orchestrator/SECURITY_HARDENING.md` |
| Phase plans | `docs/phases/` |
| Phase dependency chain | `docs/phases/PHASE-11-20-WORKFLOW-PLAN.md` |
| Session logs | `docs/sessions/` |
| Research dossiers | `docs/research/repo_dossiers/` |
| CHANGELOG | `core/CHANGELOG.md` |

## Test Commands
```bash
cd engine
python -m pytest tests/ -q               # full suite (~9 min, 197 tests)
python -m pytest tests/ -x -q            # stop on first failure
python -m pytest tests/test_execution_*.py -x -q  # Phase 13 tests only (54 tests)
python -m ruff check src/ tests/         # lint (0 errors)
```
