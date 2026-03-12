# Session 74 Slice S4 Scope Lock

Date: 2026-03-12
Slice: S4 - OpenClaw Track 5A `apply_patch` runtime foundation
Worktree: `D:\GITHUB\AGENT33\worktrees\session74-s4-apply-patch-foundation`
Branch: `codex/session74-s4-apply-patch-foundation`

## Baseline

- `main` has tool governance, approvals, approval tokens, and basic shell/file tools.
- `main` does not have a first-class `apply_patch` tool.
- `main` does not persist a structured mutation audit trail.
- MCP `execute_tool` currently bypasses governance by calling the tool directly.

## Included In This Slice

- Builtin `apply_patch` tool with:
  - Codex-style patch envelope parsing
  - workspace/path containment enforcement
  - dry-run preview mode
  - add, update, delete, and move support
- Persisted mutation audit store and read API for operators
- Governance alignment:
  - `apply_patch` treated as destructive only for real apply mode
  - supervised/tool-policy approvals continue to work
  - MCP `execute_tool` now goes through governance and validated execution
- Backend tests for tool behavior, approvals, MCP governance, and audit routes

## Explicit Non-Goals

- Process manager or long-running shell session UX
- Frontend mutation UI
- Rich diff rendering beyond JSON/text previews
- Bulk multi-workspace editing semantics
