# Provider Auth Policy Migration (2026-02-25)

## Why this was needed

PR automation checks were blocked by external AI review auth failures, and we need to reduce account-risk exposure from unsupported auth patterns.

## External guidance reviewed

### Anthropic (official)

- Claude Code legal/compliance guidance states OAuth tokens from Free/Pro/Max are for Claude Code and Claude.ai only, and are not permitted for other products/tools/services.
- Anthropic explicitly recommends API key authentication for developers building products/services around Claude capabilities.

Reference:
- https://code.claude.com/docs/en/legal-and-compliance

### Anthropic action setup docs (official)

- `anthropics/claude-code-action` setup supports both API key and OAuth token configuration in workflow secrets.
- Given current policy direction, this repo should use API key mode only for CI automation and avoid OAuth-token based automation.

Reference:
- https://github.com/anthropics/claude-code-action/blob/main/docs/setup.md

### Gemini Code Assist docs (official)

- Current GitHub review documentation describes normal app setup, quotas, and operation.
- No explicit “ban” statement was identified in official Gemini GitHub review docs reviewed in this pass.

Reference:
- https://developers.google.com/gemini-code-assist/docs/review-github-code

## Decisions applied in this repo

1. **Claude security review is opt-in** via repository variable:
   - `ENABLE_CLAUDE_SECURITY_REVIEW=true`
2. **API key only** for Anthropic action path:
   - requires `ANTHROPIC_API_KEY`
   - no OAuth token path used by workflow logic
3. **If not enabled/configured, job cleanly skips** instead of failing PR checks.
4. **Existing non-AI security scans remain primary gates** (Trivy/CVE/secret scans).

## Operational guidance

- Do not configure `CLAUDE_CODE_OAUTH_TOKEN` for CI automation in this repo.
- If enabling Claude review, set:
  - repo variable: `ENABLE_CLAUDE_SECURITY_REVIEW=true`
  - repo secret: `ANTHROPIC_API_KEY`
- Keep AI reviewer output advisory; preserve deterministic security tooling as required merge gates.
