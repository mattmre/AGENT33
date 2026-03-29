# Session 116 P11 / Phase 52 Scope Lock

## Objective

Close the remaining honest Phase 52 leak path on current `main` by applying the
existing secret-redaction pipeline to the managed-process surface.

## Why This Slice

The core Phase 52 primitives are already shipped on `main`:

- `agent33.security.redaction.redact_secrets()`
- structlog secret redaction
- tool-loop output redaction
- trajectory, observation, summarizer, shared-memory, and RAG persistence hooks

The remaining concrete operator-visible gap is the managed-process path:

- raw process commands are persisted in `ManagedProcessRecord.command`
- raw subprocess output is written to process log files and returned by
  `/v1/processes/{process_id}/log`
- persisted process state can retain unsanitized command / error strings from
  older records

## PR Boundary

Keep the PR limited to the process-registry execution path:

1. extend the pattern bank for CLI-style secret flags
2. redact managed-process commands, log chunks, and persisted process metadata
3. document the redacted process-registry contract
4. add focused tests only for redaction patterns and process manager / API docs

## Non-Goals

- broad repo-wide persistence audits beyond the process-manager surface
- process UX redesign, PTY support, or reattachment changes
- secret storage / vault redesign

## Review Focus

- false-negative risk for common CLI-style secret flags
- no raw secret values survive in process records, state-store payloads, or log
  tails
- docs clearly explain that command / log surfaces are redacted by design
