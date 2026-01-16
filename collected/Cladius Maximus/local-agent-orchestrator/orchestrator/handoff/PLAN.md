# PLAN

## Project
Local multi-agent workflow using:
- Local Ollama Qwen3-Coder 30B (pinned hot model)
- Qwen Code as terminal agent
- Claude Code (subscription) as orchestrator when available
- (Optional) Gemini Pro for second-opinion reviews / test planning

## Objectives
- [ ] Establish repeatable orchestration protocol (PLAN/TASKS/STATUS/DECISIONS)
- [ ] Ensure Qwen workers produce **small diffs**, **tight scope**, **tests**
- [ ] Minimize wasted tokens by using file-based state and concise updates
- [ ] Provide quick “refresh context” entrypoint for any agent

## Constraints
- Single GPU (RTX 3090) → avoid true parallel 16K generations; queue is expected
- Prefer **no extra monthly charges** beyond existing subscriptions
- Keep secrets out of repo; never commit credentials or tokens

## Success Criteria
- One or more tasks completed end-to-end:
  - task picked from TASKS
  - branch created
  - change implemented
  - tests run (or best available checks)
  - diff produced + merged or ready for PR
- Any new agent can open STATUS.md + PLAN.md + TASKS.md and continue in <5 minutes.

## Tools
- Git + branches per task
- Qwen Code for worker execution
- Claude Code for orchestration (when quota allows)
- Optional Gemini for review/alternatives

## Risks / Mitigations
- Token limit hit (Claude/Gemini) → workers continue locally; orchestrator resumes later
- Model cold-start latency → use warm/pin script; avoid container restarts
- Scope creep → enforce task boundaries and acceptance criteria

## Current Priorities (edit me)
1) Wire up router later (optional) *after* local workflow proves stable
2) Add agent launcher scripts (done in this bootstrap)
3) Define “definition of done” checklist for tasks (below)
