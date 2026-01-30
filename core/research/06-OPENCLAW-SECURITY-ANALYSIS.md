# OpenClaw Platform Security Analysis

## Executive Summary

OpenClaw is a personal AI assistant framework built on Node.js/TypeScript that integrates with over 20 messaging platforms (Telegram, WhatsApp, Discord, Slack, Matrix, and others). It provides a unified interface for interacting with multiple LLM providers while exposing file system access, shell execution, browser automation, and web fetching as agent tools.

This analysis identifies critical security vulnerabilities, information leaking patterns, and third-party dependency risks relevant to AGENT-33 integration planning. The findings are organized by severity and include concrete recommendations for mitigation within the AGENT-33 specification-first framework.

**Risk Rating: HIGH** -- Multiple categories of vulnerability exist across credential storage, data exfiltration surface, authentication design, and dependency provenance.

---

## 1. External Service Communications (CRITICAL)

All user messages, system prompts, tool definitions, tool results (including file contents and shell output), and conversation history are transmitted to external services during normal operation. The following is a comprehensive catalog of external endpoints contacted by OpenClaw.

### 1.1 Model Providers

| Provider | Endpoint | Data Sent | Retention Policy |
|----------|----------|-----------|-----------------|
| Anthropic | `api.anthropic.com` | Messages, system prompts, tool defs, file contents | 30 days (safety), opt-out available |
| OpenAI | `api.openai.com` | Messages, system prompts, tool defs, file contents | 30 days by default, opt-out via API flag |
| Google Gemini | `generativelanguage.googleapis.com` | Messages, system prompts, tool defs, file contents | Varies by plan |
| AWS Bedrock | Regional AWS endpoints | Messages, system prompts, tool defs, file contents | Per AWS data policies |
| GitHub Copilot | `api.individual.githubcopilot.com` | Messages, system prompts, tool defs, file contents | GitHub data policies |
| Groq | `api.groq.com` | Messages, system prompts, tool defs, file contents | Groq data policies |
| MiniMax | `api.minimax.io`, `api.minimax.chat/v1` | Messages, system prompts, tool defs, file contents | **Chinese company -- subject to PRC data laws** |
| Cohere | `api.cohere.ai` | Messages, system prompts, tool defs, file contents | Cohere data policies |

**Key concern**: Every piece of context the agent processes -- including sensitive file contents read via the `read` tool, shell command output, and authentication credentials visible in environment variables -- is transmitted to whichever model provider is configured. Users may not realize that switching providers changes the jurisdictional scope of their data.

### 1.2 Media Processing APIs

| Service | Endpoint | Data Sent | Purpose |
|---------|----------|-----------|---------|
| Deepgram | `api.deepgram.com` | Raw audio files | Speech-to-text |
| ElevenLabs | `api.elevenlabs.io` | All TTS text content | Text-to-speech |
| Google Vision | `vision.googleapis.com` | Image files | Image analysis |
| MiniMax VLM | `api.minimax.io` | Image files | Vision-language model |

**Key concern**: Audio recordings and images are uploaded to third-party servers with no documented data retention limits or deletion guarantees.

### 1.3 Hardcoded Non-Configurable Endpoints

The following endpoints are hardcoded in source and cannot be redirected or proxied:

- **`https://api.chutes.ai`** -- Chutes OAuth flow. The OAuth redirect URI is hardcoded. Users cannot point this at a self-hosted instance or audit proxy.
- **`https://api.minimax.io`** -- MiniMax API base URL is not configurable. All requests to MiniMax go to this endpoint regardless of user configuration.
- **`https://api.minimax.chat/v1`** -- Alternate MiniMax endpoint, also hardcoded.

**AGENT-33 Implication**: Hardcoded endpoints violate the AGENT-33 principle that all external communications must be configurable and auditable. Any integration must wrap or replace these calls.

### 1.4 Telemetry and Usage Tracking

- **OpenTelemetry**: Disabled by default. When enabled, exports session IDs, token counts, cost calculations, message IDs, and full error traces (which may contain file paths, credentials in stack traces, and user content).
- **Usage tracking**: Makes calls to `https://api.anthropic.com/api/oauth/usage` and falls back to `https://claude.ai/api/organizations/{uuid}/usage`. The organization UUID is transmitted, linking usage data to a specific account.

---

## 2. Information Leaking Patterns (CRITICAL)

### 2.1 Plaintext Credential Storage

**Location**: `~/.openclaw/agents/<id>/agent/auth-profiles.json`

This file stores API keys, OAuth access tokens, OAuth refresh tokens, and AWS credentials in **unencrypted plaintext JSON**. Any process running as the same user can read this file. No file permission hardening is applied beyond the default umask (typically `0644`, world-readable).

Contents include:
- LLM provider API keys (Anthropic, OpenAI, Google, etc.)
- OAuth tokens for messaging platforms
- AWS access key ID and secret access key (for Bedrock)
- Custom bearer tokens for self-hosted services

### 2.2 Unencrypted Session Transcripts

**Location**: `~/.openclaw/agents/<id>/sessions/`

Full conversation history is stored as JSONL files with no encryption at rest. Each line contains:
- Complete user messages (may include passwords, credentials, PII shared in conversation)
- Complete assistant responses
- Tool call arguments and results (file contents, shell output, web page content)
- Token counts and cost data

Sessions accumulate indefinitely. There is no automatic rotation, expiration, or deletion mechanism.

### 2.3 Configuration Flag Without Implementation

The configuration schema includes an `encryptionAtRest` section:

```json
{
  "encryptionAtRest": {
    "enabled": false
  }
}
```

**This flag is not implemented.** Setting it to `true` has no effect. Credentials and sessions remain in plaintext regardless of this setting. This creates a false sense of security for users who enable it.

### 2.4 Logging Exposure

The `redactSensitive` configuration option defaults to `"on"` but can be set to `"off"`. When disabled:
- Full API responses (including any credentials in responses) are logged to disk
- File contents read by the agent are logged
- Shell command output (potentially containing secrets) is logged
- Web page content fetched by the agent is logged

Log files use the same default file permissions (umask-inherited, typically `0644`).

### 2.5 Environment Variable Exposure

Secrets configured as environment variables are exposed through multiple vectors:
- `/proc/[pid]/environ` on Linux (readable by same user)
- `ps aux` output on some configurations
- Shell history when set interactively
- Agent tool output when running `env` or `printenv` commands
- Transmitted to LLM providers when captured in tool results

### 2.6 Default File Permissions

No explicit file permission restrictions are applied to any created files. All files inherit the process umask, which is typically `0644` (owner read/write, group read, others read). This means:
- Credential files are world-readable
- Session transcripts are world-readable
- Log files are world-readable
- Configuration files are world-readable

---

## 3. Third-Party Dependency Risks (HIGH)

### 3.1 Critical Risk Dependencies

#### @whiskeysockets/baileys (WhatsApp Web)

| Attribute | Value |
|-----------|-------|
| Purpose | WhatsApp Web reverse-engineering library |
| Maintainer | Community (whiskeysockets) |
| Risk Level | **CRITICAL** |
| Concerns | Violates WhatsApp Terms of Service; reverse-engineered undocumented protocol; accounts may be banned; no official API backing; protocol changes can break silently; potential for credential interception by maintainers |
| AGENT-33 Recommendation | Do not integrate. Use official WhatsApp Business API only. |

#### node-edge-tts

| Attribute | Value |
|-----------|-------|
| Purpose | Text-to-speech via reverse-engineered Microsoft Edge endpoint |
| Maintainer | Community (single author) |
| Risk Level | **HIGH** |
| Concerns | Reverse-engineered unofficial Microsoft endpoint; violates Microsoft ToS; can break without notice; no SLA or support; single maintainer supply chain risk |
| AGENT-33 Recommendation | Use official Azure Cognitive Services TTS API. |

#### playwright-core

| Attribute | Value |
|-----------|-------|
| Purpose | Browser automation for web browsing tool |
| Maintainer | Microsoft |
| Risk Level | **HIGH** |
| Concerns | Controls system browser with access to all stored sessions, cookies, passwords, and local storage; can navigate to any URL; can execute arbitrary JavaScript; no sandboxing from user browser profile by default |
| AGENT-33 Recommendation | If browser automation is required, enforce isolated browser profile with no access to existing sessions. Prefer headless with fresh profile. |

### 3.2 Elevated Risk Dependencies

#### sqlite-vec 0.1.7-alpha.2

| Attribute | Value |
|-----------|-------|
| Purpose | Vector similarity search extension for SQLite |
| Maintainer | Alex Garcia (single author) |
| Risk Level | **MEDIUM-HIGH** |
| Concerns | Pre-release alpha version; limited security review; native code extension (C); single maintainer; API may change without notice |
| AGENT-33 Recommendation | Wait for stable release or use established vector database (pgvector, Qdrant). |

#### linkedom

| Attribute | Value |
|-----------|-------|
| Purpose | Lightweight DOM parser for processing fetched web pages |
| Maintainer | Andrea Giammarchi (single author) |
| Risk Level | **MEDIUM** |
| Concerns | Parses untrusted HTML content from arbitrary web pages; potential XSS surface if output is rendered; not a security-hardened parser |
| AGENT-33 Recommendation | Use DOMPurify in conjunction, or prefer jsdom with security patches. |

#### grammy (Telegram Bot Framework)

| Attribute | Value |
|-----------|-------|
| Purpose | Telegram Bot API framework |
| Maintainer | Community (grammyjs) |
| Risk Level | **MEDIUM** |
| Concerns | Community-maintained; supply chain risk; handles bot tokens and message content; middleware chain could be compromised |
| AGENT-33 Recommendation | Audit dependency tree. Pin exact versions. Verify signatures. |

---

## 4. Attack Vectors

### 4.1 Prompt Injection to Data Exfiltration

**Severity**: CRITICAL

**Vector**: A malicious message (from a messaging platform, web page content, or file) contains prompt injection instructions that cause the agent to:

1. Use the `read` tool to access `~/.openclaw/agents/<id>/agent/auth-profiles.json`
2. Use the `web_fetch` tool to POST the contents to an attacker-controlled server

**Mitigation in OpenClaw**: None documented. No input sanitization, output filtering, or tool-call validation against injection patterns.

**AGENT-33 Mitigation**: Implement per SECURITY_HARDENING.md -- input boundary markers, tool-call anomaly detection, and allowlisted output destinations.

### 4.2 Tool Access to Credential Theft

**Severity**: CRITICAL

**Vector**: The agent's `read` tool has unrestricted file system access. Any conversation that triggers file reading can access:
- `auth-profiles.json` (all API keys and OAuth tokens)
- `~/.ssh/` (SSH private keys)
- `~/.aws/credentials` (AWS credentials)
- `~/.gnupg/` (GPG private keys)
- Environment configuration files with embedded secrets

**Mitigation in OpenClaw**: None. No path restrictions, no allowlists, no sandboxing of file access.

**AGENT-33 Mitigation**: Enforce path-based allowlists per tool. Deny access to known credential paths by default.

### 4.3 Browser Hijacking

**Severity**: HIGH

**Vector**: The Playwright-based browser tool controls a system browser instance. An attacker who can influence agent actions (via prompt injection or compromised tool output) can:
- Navigate to authenticated sessions (banking, email, cloud consoles)
- Extract cookies and session tokens
- Modify account settings
- Exfiltrate stored passwords (if browser has saved passwords)

**Mitigation in OpenClaw**: None documented. Browser uses default profile.

**AGENT-33 Mitigation**: Require isolated browser profiles with no pre-existing sessions. Restrict navigable domains via allowlist.

### 4.4 Shell Injection

**Severity**: HIGH

**Vector**: User input or tool-generated content concatenated into shell commands without proper parameterization. Specially crafted filenames, directory names, or message content can inject arbitrary shell commands.

**Mitigation in OpenClaw**: Partial -- some commands use parameterized execution, but the pattern is inconsistent.

**AGENT-33 Mitigation**: All shell execution must use parameterized invocation (array form, not string concatenation). Per TOOL_GOVERNANCE.md.

### 4.5 Device Command Injection

**Severity**: HIGH

**Vector**: Once a messaging device (phone, tablet, desktop client) is paired with an OpenClaw agent, all commands from that device are executed without per-command authentication. A lost or stolen device grants full agent access with no secondary verification.

**Mitigation in OpenClaw**: None. No per-command auth, no session timeout, no geo-fencing.

**AGENT-33 Mitigation**: Implement per-command confirmation for destructive operations. Session timeouts. Device revocation capability.

---

## 5. Authentication Weaknesses

### 5.1 Gateway Authentication

| Weakness | Description | Severity |
|----------|-------------|----------|
| Shared bearer token | Single token shared across all clients. Compromise of one client compromises all. | HIGH |
| Password mode | Single password for all clients. No per-client identity. | HIGH |
| No rate limiting | No limit on authentication attempts. Brute force feasible. | MEDIUM |
| No TLS enforcement | Gateway can run without TLS. Credentials transmitted in plaintext on LAN. | HIGH |
| No audit logging | No record of authentication attempts (successful or failed). | MEDIUM |

### 5.2 Device Pairing

| Weakness | Description | Severity |
|----------|-------------|----------|
| Non-expiring approval codes | DM pairing approval codes never expire. Intercepted codes remain valid indefinitely. | HIGH |
| No revocation mechanism | Once a device is paired, there is no way to unpair or revoke access. | HIGH |
| No pairing audit log | No record of when devices were paired or by whom. | MEDIUM |
| No device inventory | No way to list currently paired devices. | MEDIUM |

---

## 6. Recommendations for AGENT-33 Integration

The following recommendations are prioritized by risk reduction impact and aligned with existing AGENT-33 specifications.

### Priority 1: CRITICAL (Must implement before any integration)

| # | Recommendation | Rationale | AGENT-33 Spec Reference |
|---|---------------|-----------|------------------------|
| 1 | **Never store credentials in plaintext** | Require OS keyring (macOS Keychain, Windows Credential Manager, libsecret) or HashiCorp Vault integration. Plaintext fallback must be explicitly opted into with warning. | SECURITY_HARDENING.md |
| 2 | **Encrypt session transcripts at rest** | Implement the encryption-at-rest that OpenClaw left as a no-op config flag. Use AES-256-GCM with key derived from user passphrase or hardware key. | SECURITY_HARDENING.md |
| 3 | **Restrict tool file access** | Path-based allowlists for file read/write tools. Deny access to `~/.ssh/`, `~/.aws/`, `~/.gnupg/`, and credential storage paths by default. | TOOL_GOVERNANCE.md |
| 4 | **Block hardcoded external endpoints** | All external endpoints must be configurable. No hardcoded URLs. All outbound connections must pass through a configurable proxy/audit layer. | TOOL_GOVERNANCE.md |

### Priority 2: HIGH (Implement before production use)

| # | Recommendation | Rationale | AGENT-33 Spec Reference |
|---|---------------|-----------|------------------------|
| 5 | **Audit all dependencies** | Complete provenance checklist for every transitive dependency. Reject pre-release, single-maintainer native code, and ToS-violating reverse-engineered libraries. | TOOL_GOVERNANCE.md |
| 6 | **Implement prompt injection defense** | Input boundary markers, tool-call anomaly detection, output destination allowlists. | SECURITY_HARDENING.md |
| 7 | **Per-client authentication** | Unique tokens per client device. No shared secrets. Support for token rotation and revocation. | SECURITY_HARDENING.md |
| 8 | **Session rotation and cleanup** | Automatic expiration of session transcripts. Configurable retention period. Secure deletion (overwrite before unlink). | SECURITY_HARDENING.md |

### Priority 3: MEDIUM (Implement for hardened deployments)

| # | Recommendation | Rationale | AGENT-33 Spec Reference |
|---|---------------|-----------|------------------------|
| 9 | **Mandatory TLS** | No unencrypted gateway connections. Reject self-signed certificates by default. Certificate pinning for known endpoints. | SECURITY_HARDENING.md |
| 10 | **Sandbox by default** | Container isolation (Docker/Podman) enabled by default, not optional. File system, network, and process isolation. | TOOL_GOVERNANCE.md |

---

## 7. Dependency Provenance Matrix

The following matrix catalogs all security-relevant dependencies with provenance assessment.

| Dependency | Version | Maintainer | License | Risk Level | Provenance Status | AGENT-33 Recommendation |
|-----------|---------|------------|---------|------------|-------------------|------------------------|
| @whiskeysockets/baileys | latest | Community (whiskeysockets) | MIT | **CRITICAL** | FAILED -- Reverse-engineered, ToS-violating | **Reject**. Use official WhatsApp Business API. |
| node-edge-tts | latest | Single author | MIT | **HIGH** | FAILED -- Reverse-engineered, ToS-violating | **Reject**. Use Azure Cognitive Services TTS. |
| playwright-core | latest | Microsoft | Apache-2.0 | **HIGH** | PASSED (maintainer) / FAILED (usage pattern) | **Conditional**. Require isolated browser profile. |
| sqlite-vec | 0.1.7-alpha.2 | Alex Garcia | MIT | **MEDIUM-HIGH** | FAILED -- Pre-release alpha, native code | **Defer**. Wait for stable release or use pgvector. |
| linkedom | latest | Andrea Giammarchi | ISC | **MEDIUM** | CAUTION -- Single maintainer, parses untrusted input | **Conditional**. Pair with DOMPurify. |
| grammy | latest | grammyjs community | MIT | **MEDIUM** | CAUTION -- Community maintained, handles secrets | **Conditional**. Pin versions, audit tree. |
| @anthropic-ai/sdk | latest | Anthropic | MIT | LOW | PASSED | **Accept**. Official provider SDK. |
| openai | latest | OpenAI | MIT | LOW | PASSED | **Accept**. Official provider SDK. |
| @google/generative-ai | latest | Google | Apache-2.0 | LOW | PASSED | **Accept**. Official provider SDK. |
| @aws-sdk/* | latest | Amazon | Apache-2.0 | LOW | PASSED | **Accept**. Official provider SDK. |
| @deepgram/sdk | latest | Deepgram | MIT | LOW | PASSED | **Accept**. Official provider SDK. |
| elevenlabs | latest | ElevenLabs | MIT | LOW | PASSED | **Accept**. Official provider SDK. |

### Provenance Status Definitions

- **PASSED**: Maintained by the service provider or a well-established organization with documented security practices.
- **CONDITIONAL**: Maintained by a reputable party but usage pattern introduces risk that must be mitigated.
- **CAUTION**: Single maintainer or small community with limited security review history. Requires version pinning and dependency tree audit.
- **FAILED**: Violates Terms of Service, is pre-release with native code, or has unacceptable supply chain risk. Must not be used without explicit risk acceptance.

---

## Appendix A: Data Flow Summary

```
User Device
    |
    v
Messaging Platform (Telegram/WhatsApp/Discord/...)
    |
    v
OpenClaw Gateway (optional TLS, shared token auth)
    |
    v
OpenClaw Agent Core
    |
    +---> LLM Provider (full conversation + tool results)
    +---> Media APIs (audio/images)
    +---> File System (unrestricted read/write)
    +---> Shell (command execution)
    +---> Browser (full system browser access)
    +---> Web Fetch (arbitrary HTTP requests)
    |
    v
Local Storage (plaintext credentials, unencrypted sessions, logs)
```

---

## Appendix B: Comparison with AGENT-33 Security Requirements

| AGENT-33 Requirement | OpenClaw Status | Gap |
|---------------------|-----------------|-----|
| Encrypted credential storage | Not implemented | CRITICAL gap |
| Encrypted session storage | Config exists, not implemented | CRITICAL gap |
| Configurable endpoints | Partially (some hardcoded) | HIGH gap |
| Tool access restrictions | None | CRITICAL gap |
| Prompt injection defense | None documented | HIGH gap |
| Per-client authentication | Not supported | HIGH gap |
| Dependency provenance | No formal process | MEDIUM gap |
| Audit logging | Not implemented | MEDIUM gap |
| TLS enforcement | Optional | MEDIUM gap |
| Container isolation | Optional | MEDIUM gap |

---

*Document created: 2026-01-30*
*Classification: Internal Research*
*Author: AGENT-33 Security Analysis Team*
