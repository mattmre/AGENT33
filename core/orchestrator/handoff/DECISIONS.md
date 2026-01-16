# DECISIONS (Architecture Decision Log)

## 2026-01-10: Separate repo + separate Ollama stack
**Decision:** Keep a dedicated qwen_ollama container + volume and expose on port 11435.
**Why:** Isolation from other projects; reproducible setup; easy to push to GitHub.
**Consequences:** Two Ollama instances can compete for one GPU if both active; manage via usage discipline.

## 2026-01-10: Worker model pinned hot
**Decision:** Pin Qwen model in memory during active sessions to avoid cold-start latency.
**Why:** 30B model cold load can take ~60s; pinned hot keeps responses fast.
**Consequences:** VRAM remains allocated; may interfere with other local LLM workloads.

## Example (Template)
**Decision:** <short decision title>
**Why:** <rationale>
**Consequences:** <tradeoffs>

## Decision Types
- Architecture
- Process/Policy
- Tooling/Runtime
- Security/Compliance
