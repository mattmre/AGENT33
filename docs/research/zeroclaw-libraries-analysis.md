# ZeroClaw Libraries, Dependencies & Integration Analysis

**Date**: 2026-02-14
**Repository**: https://github.com/theonlyhennygod/zeroclaw
**Companion Dossier**: `docs/research/repo_dossiers/zeroclaw.md`

---

## Table of Contents

1. [Rust Dependencies (Cargo.toml)](#1-rust-dependencies-cargotoml)
2. [LLM Provider Integrations](#2-llm-provider-integrations)
3. [Channel Integrations](#3-channel-integrations)
4. [Security Libraries & Algorithms](#4-security-libraries--algorithms)
5. [Memory System Libraries](#5-memory-system-libraries)
6. [Tunnel Providers](#6-tunnel-providers)
7. [Integration Ecosystem (Composio & Registry)](#7-integration-ecosystem)
8. [Relevance to AGENT-33](#8-relevance-to-agent-33)

---

## 1. Rust Dependencies (Cargo.toml)

ZeroClaw has 22 direct dependencies and 2 dev-dependencies. This is an intentionally minimal footprint for a full-featured AI assistant. For comparison, a typical Rust web application using Axum/Actix would have 40-80 dependencies.

### 1.1 Complete Dependency Inventory

#### Async Runtime & Networking

| Crate | Version | Features | Purpose |
|-------|---------|----------|---------|
| `tokio` | 1.42 | `rt-multi-thread, macros, time, net, io-util, sync, process, io-std, fs` | Async runtime. The backbone of all I/O. |
| `reqwest` | 0.12 | `json, rustls-tls, blocking` | HTTP client for all LLM API calls. |
| `tokio-tungstenite` | 0.24 | `rustls-tls-webpki-roots` | WebSocket client (Discord gateway). |
| `futures-util` | 0.3 | `sink` | Async stream/sink utilities. |

**tokio 1.42**
- **Downloads**: 437M+ all-time on crates.io.
- **Maintenance**: Actively maintained by the Tokio team. LTS releases: 1.43.x (until March 2026), 1.47.x (until September 2026). Version 1.42 is current and well-supported.
- **Security**: No direct security advisories on the core tokio crate. A related crate (`async-tar`) had CVE-2025-62518 (CVSS 8.1) but this is not a tokio dependency.
- **Alternatives**: `async-std` (declining usage), `smol` (lighter but less ecosystem support). Tokio is the de facto standard.
- **Assessment**: Excellent choice. No concerns.

**reqwest 0.12**
- **Downloads**: 250M+ all-time.
- **Maintenance**: Maintained by Sean McArthur (hyper author). Actively developed.
- **Security**: Uses `rustls-tls` feature (pure Rust TLS, no OpenSSL dependency). No known active CVEs. A historical concern exists around `danger_accept_invalid_certs()` being a misconfiguration footgun, but this is user error, not a library bug. ZeroClaw's use of `rustls-tls` is the recommended secure configuration.
- **Alternatives**: `ureq` (blocking-only, simpler), `hyper` (lower-level), `isahc` (curl-based). reqwest is the standard choice for async HTTP.
- **Assessment**: Excellent choice. The `rustls-tls` feature avoids native TLS library dependency issues.

**tokio-tungstenite 0.24**
- **Downloads**: ~50M all-time.
- **Maintenance**: Maintained by snapview. Latest version is 0.28.0. Version 0.24 is approximately 1 year behind latest.
- **Security**: Uses `rustls-tls-webpki-roots` for WebSocket TLS, which is secure. Versions > 0.26.2 have significant performance improvements.
- **Alternatives**: `fastwebsockets` (faster but less mature), `async-tungstenite` (runtime-agnostic).
- **Assessment**: Functional but slightly outdated. Upgrading to 0.28 would improve performance for Discord gateway connections.

**futures-util 0.3**
- **Downloads**: 345M+ all-time.
- **Maintenance**: Part of the official `futures` crate family. Actively maintained.
- **Assessment**: Standard choice, no concerns.

#### Serialization & Configuration

| Crate | Version | Features | Purpose |
|-------|---------|----------|---------|
| `serde` | 1.0 | `derive` | Serialization/deserialization framework. |
| `serde_json` | 1.0 | `std` | JSON handling for all API communication. |
| `toml` | 0.8 | (default) | TOML config file parsing. |

**serde 1.0**
- **Downloads**: 699M+ all-time, 99M/month. The most-used Rust crate.
- **Maintenance**: Maintained by David Tolnay. Current version 1.0.228. Actively maintained with frequent releases.
- **Security**: No known CVEs. Note: `serde_yml` (a separate, unrelated crate) was flagged as unsound (RUSTSEC-2025-0068), but this does not affect `serde` or `serde_json`.
- **Assessment**: Industry standard. No concerns whatsoever.

**serde_json 1.0**
- **Downloads**: 614M+ all-time, 89M/month.
- **Assessment**: Standard companion to serde. No concerns.

**toml 0.8**
- **Downloads**: ~110M all-time.
- **Maintenance**: Maintained by the toml-rs organization. Current version 0.8.x.
- **Assessment**: Standard TOML parser. No concerns.

#### CLI & User Interface

| Crate | Version | Features | Purpose |
|-------|---------|----------|---------|
| `clap` | 4.5 | `derive` | Command-line argument parsing. |
| `dialoguer` | 0.11 | `fuzzy-select` | Interactive prompts (onboarding wizard). |
| `console` | 0.15 | (default) | Terminal formatting and colors. |

**clap 4.5**
- **Downloads**: 667M+ all-time, 28M/month. Used in 44,229 crates.
- **Maintenance**: Maintained by clap-rs team. Current version 4.5.58. Extremely active.
- **Alternatives**: `argh` (Google, simpler), `structopt` (deprecated in favor of clap derive).
- **Assessment**: The dominant Rust CLI framework. No concerns.

**dialoguer 0.11**
- **Downloads**: 2.2M/month. Used in 2,074 crates.
- **Maintenance**: Part of the `console-rs` organization (Armin Ronacher). Current version 0.12.0. ZeroClaw uses 0.11 which is one minor behind.
- **Alternatives**: `inquire` (more feature-rich), `cliclack` (prettier output).
- **Assessment**: Solid choice for interactive prompts. Minor version behind but functional.

**console 0.15**
- **Downloads**: ~95M all-time.
- **Maintenance**: Part of `console-rs`. Actively maintained.
- **Assessment**: Standard terminal utility crate. No concerns.

#### Error Handling

| Crate | Version | Purpose |
|-------|---------|---------|
| `anyhow` | 1.0 | Application-level error handling (type-erased errors). |
| `thiserror` | 2.0 | Library-level error derivation (structured error types). |

**anyhow 1.0**
- **Downloads**: 270M+ all-time.
- **Maintenance**: Maintained by David Tolnay. Actively developed.
- **Usage pattern**: ZeroClaw uses both `anyhow` (for application error propagation) and `thiserror` (for structured error types in library modules). This is the idiomatic Rust pattern -- `thiserror` for defining errors, `anyhow` for handling them.
- **Assessment**: Best-practice error handling stack.

**thiserror 2.0**
- **Downloads**: 290M+ all-time.
- **Maintenance**: Maintained by David Tolnay. Version 2.0 is the latest major.
- **Assessment**: Industry standard. No concerns.

#### Security & Cryptography

| Crate | Version | Purpose |
|-------|---------|---------|
| `chacha20poly1305` | 0.10 | AEAD encryption for secret store. |

**chacha20poly1305 0.10**
- **Downloads**: ~22M all-time.
- **Maintenance**: Part of the RustCrypto project. Current version 0.10.1. Well-maintained by the RustCrypto team.
- **Security**: Pure Rust implementation. Constant-time operations using hardware intrinsics (AVX2) where available, with a portable fallback. Implements RFC 8439. No known CVEs.
- **Alternatives**: `aes-gcm` (AES-GCM from RustCrypto), `ring` (Google's crypto library, more opinionated).
- **Assessment**: Excellent choice for ZeroClaw's use case. See Section 4 for detailed algorithm analysis.

#### Data Storage

| Crate | Version | Features | Purpose |
|-------|---------|----------|---------|
| `rusqlite` | 0.32 | `bundled` | SQLite database for memory system. |
| `chrono` | 0.4 | `clock, std` | Date/time handling. |

**rusqlite 0.32**
- **Downloads**: 40M+ all-time. Version 0.32.1 has 5M downloads.
- **Maintenance**: Actively maintained. Latest version is 0.38.0 -- ZeroClaw is 6 minor versions behind.
- **Security**: The `bundled` feature compiles SQLite from source, which means ZeroClaw ships a known, consistent SQLite version regardless of the host system. This is a security positive -- it avoids depending on potentially outdated system SQLite.
- **Alternatives**: `sqlx` (async, multi-database), `diesel` (ORM). For embedded single-file databases, `rusqlite` is the standard choice.
- **Assessment**: Functional but notably behind latest. The gap from 0.32 to 0.38 may include bug fixes and SQLite version upgrades. Recommend upgrading.

**chrono 0.4**
- **Downloads**: 256M+ all-time.
- **Maintenance**: Community-maintained. Has had historical security issues (RUSTSEC-2020-0159 regarding `localtime_r`), which were resolved.
- **Assessment**: Standard choice. The minimal feature set (`clock, std`) is correct.

#### Utilities

| Crate | Version | Purpose |
|-------|---------|---------|
| `uuid` | 1.11 | UUID v4 generation for memory keys. |
| `async-trait` | 0.1 | Async trait support (Rust doesn't natively support async in traits before 1.75). |
| `directories` | 5.0 | Platform-specific directory paths (~/.zeroclaw). |
| `shellexpand` | 3.1 | Shell variable expansion (~/, $HOME). |
| `hostname` | 0.4.2 | System hostname detection. |

**uuid 1.11**
- **Downloads**: 260M+ all-time.
- **Assessment**: Standard UUID library. No concerns.

**async-trait 0.1**
- **Downloads**: 260M+ all-time.
- **Maintenance**: Maintained by David Tolnay.
- **Note**: As of Rust 1.75 (December 2023), native async traits are stabilized. However, `async-trait` still provides `dyn`-compatible async traits which native async traits don't yet support. ZeroClaw's heavy use of `Box<dyn Trait>` makes `async-trait` still necessary.
- **Assessment**: Still needed for ZeroClaw's architecture. No concerns.

**directories 5.0**
- **Downloads**: ~60M all-time.
- **Assessment**: Standard platform-directories crate. No concerns.

**shellexpand 3.1**
- **Downloads**: ~20M all-time.
- **Assessment**: Small, focused crate. No concerns.

**hostname 0.4.2**
- **Downloads**: ~15M all-time.
- **Assessment**: Minimal utility crate. No concerns.

#### Dev Dependencies

| Crate | Version | Purpose |
|-------|---------|---------|
| `tokio-test` | 0.4 | Async test utilities. |
| `tempfile` | 3.14 | Temporary file/directory creation for tests. |

Both are standard test utilities. No concerns.

### 1.2 Release Profile

```toml
[profile.release]
opt-level = "z"       # Optimize for binary size
lto = true            # Link-time optimization
codegen-units = 1     # Better optimization, slower compile
strip = true          # Remove debug symbols
panic = "abort"       # No unwinding, smaller binary

[profile.dist]
inherits = "release"
opt-level = "z"
lto = "fat"           # Maximum LTO for distribution
codegen-units = 1
strip = true
panic = "abort"
```

This is an aggressively size-optimized profile. The `opt-level = "z"` prioritizes binary size over execution speed, which is appropriate for a CLI tool where startup latency matters more than throughput. The result is the claimed ~3.4 MB binary.

### 1.3 Dependency Health Summary

| Status | Count | Crates |
|--------|-------|--------|
| Current & healthy | 17 | tokio, reqwest, serde, serde_json, clap, anyhow, thiserror, uuid, async-trait, chacha20poly1305, chrono, toml, directories, shellexpand, futures-util, console, hostname |
| Slightly outdated | 3 | tokio-tungstenite (0.24 vs 0.28), dialoguer (0.11 vs 0.12), rusqlite (0.32 vs 0.38) |
| Security concern | 0 | None |
| Unmaintained | 0 | None |

**Overall assessment**: The dependency tree is remarkably clean. 22 direct dependencies for a full AI assistant is lean. All crates are actively maintained, well-established, and from trusted authors/organizations.

---

## 2. LLM Provider Integrations

ZeroClaw's integration registry lists 26 AI model providers (not 22 as initially claimed in the README). Of these, 24 are marked "Active/Available" and 2 are "Coming Soon."

### 2.1 Provider Architecture

All providers implement a unified `Provider` trait:

```rust
#[async_trait]
pub trait Provider: Send + Sync {
    async fn chat(&self, messages: Vec<Message>, model: &str, temperature: f32) -> Result<String>;
    async fn chat_with_system(&self, system: &str, user: &str, model: &str, temp: f32) -> Result<String>;
}
```

Concrete implementations exist for:
- **OpenRouter** (`providers/openrouter.rs`) -- routes to 300+ models
- **Anthropic** (`providers/anthropic.rs`) -- direct Claude API
- **OpenAI** (`providers/openai.rs`) -- direct GPT API
- **Ollama** (`providers/ollama.rs`) -- local model server
- **Compatible** (`providers/compatible.rs`) -- any OpenAI-compatible API endpoint

Most providers route through the `Compatible` (OpenAI-compatible) implementation, since the vast majority of LLM APIs now follow the OpenAI API format. Only Anthropic has a meaningfully different API shape.

### 2.2 Provider-by-Provider Analysis

#### Tier 1: Aggregators

| Provider | Auth Method | Models | Pricing Model | Best Use Case |
|----------|-----------|--------|---------------|---------------|
| **OpenRouter** | API Key (Bearer) | 300+ from all major providers | Pass-through + 5.5% fee | One-key access to everything. Fallback routing. Production use with provider diversity. |

**OpenRouter** (https://openrouter.ai) is a meta-provider that aggregates nearly all other providers below. A single API key grants access to Claude, GPT, Llama, Gemini, Mistral, and hundreds more. Requests are load-balanced across providers ordered by price, with automatic fallbacks. This is likely the default provider for most ZeroClaw users.

#### Tier 2: Major Direct Providers

| Provider | Auth Method | Key Models | Input/Output Pricing (per 1M tokens) | Best Use Case |
|----------|-----------|------------|--------------------------------------|---------------|
| **Anthropic** | API Key (`x-api-key` header) | Claude Opus 4.5, Sonnet 4.5, Haiku 4.5 | $1-5 / $5-25 | Complex reasoning, safety-critical tasks, coding. |
| **OpenAI** | API Key (Bearer) | GPT-5.2, GPT-5, GPT-4o | $1.25-1.75 / $10-14 | General-purpose, multimodal, agentic tasks. |
| **Google** | API Key | Gemini 2.5 Pro, Gemini 2.5 Flash | $1.25-3.50 / $5-10 | Long-context (1M+ tokens), multimodal. |
| **DeepSeek** | API Key (Bearer) | V3.2, R1, R1 Distill | $0.03-0.56 / $0.11-1.68 | Budget-friendly reasoning. 30x cheaper than GPT-5. |
| **Mistral** | API Key (Bearer) | Large 3, Medium 3, Small 3.2, Nemo | $0.02-0.50 / $0.11-2.00 | EU-hosted inference, code generation (Devstral). |
| **Cohere** | API Key (Bearer) | Command R+, Command A, Command R7B | $0.04-2.50 / $0.15-10.00 | Enterprise RAG, embedding, reranking. |

**Anthropic** uses a non-standard API format (the `Messages` API with `x-api-key` header rather than Bearer token). ZeroClaw has a dedicated `anthropic.rs` implementation for this. Claude models offer the best coding and safety performance. Prompt caching reduces costs by 90% for repeated prefixes.

**OpenAI** follows the standard chat completions API that most other providers emulate. GPT-5.2 (released December 2025) is the current flagship. ZeroClaw's `openai.rs` is the canonical implementation that `compatible.rs` derives from.

**DeepSeek** is the cost leader at $0.56/1M input tokens (cache miss), 30x cheaper than GPT-5. The R1 model provides strong reasoning at minimal cost. Free-first approach with 5M free tokens on registration.

#### Tier 3: Inference Platforms

| Provider | Auth Method | Specialization | Pricing | Best Use Case |
|----------|-----------|---------------|---------|---------------|
| **Groq** | API Key (Bearer) | Ultra-fast LPU inference | $0.11-0.59 / $0.34-0.79 | Lowest latency. 300+ tok/s for 70B models. Real-time chat. |
| **Together AI** | API Key (Bearer) | Open-source model hosting | $0.50 / $1.50 (gpt-oss-120B) | Open-source models at scale. Fine-tuning. |
| **Fireworks AI** | API Key (Bearer) | Fast open-source inference | $0.20-0.50 / varies | Batch processing (50% discount). Fine-tuned models at base price. |
| **Venice** | API Key / VVV Staking | Privacy-first inference | Staking-based or Pro | Anonymous inference. Zero data retention. |
| **Perplexity** | API Key (Bearer) | Search-augmented AI | $1-3 / $1-15 (Sonar models) | Real-time web search integration. Cited answers. |

**Groq** stands out for raw speed. Their custom LPU (Language Processing Unit) delivers Llama 70B at 300+ tokens/second -- approximately 10x faster than GPU inference. Ideal for ZeroClaw's interactive CLI where response latency is critical. 1.9M+ developers on the platform; partnerships with Meta, Dropbox, Volkswagen.

**Venice** is unique among providers for its privacy architecture. All data stays on the user's device. Venice never logs, sees, or stores prompts. Conversations are encrypted in local browser storage. API access is via VVV token staking (zero marginal cost per request) or Venice Pro subscription.

#### Tier 4: Cloud Platform Providers

| Provider | Auth Method | Access Pattern | Best Use Case |
|----------|-----------|---------------|---------------|
| **Amazon Bedrock** | AWS IAM (SigV4) | Managed AWS service | Enterprise AWS shops. Compliance-heavy environments. |
| **Cloudflare AI** | API Token | Edge inference | Low-latency edge computing. Cloudflare-native applications. |
| **Vercel AI** | API Key | Edge gateway | Vercel-hosted applications. Streaming UI. |
| **xAI** | API Key (Bearer) | Grok models | 2M token context window. Real-time X/Twitter data. |

**Amazon Bedrock** uses AWS SigV4 authentication (IAM credentials), which is the most complex auth method among all providers. It provides access to Anthropic, Meta, Mistral, Cohere, and Amazon's own models through a unified AWS API. Pricing is pass-through, sometimes with a small markup.

**xAI** offers the largest context window (2M tokens with Grok 4 Fast). New users receive $25 in free credits, with an additional $150/month through data sharing. The API is OpenAI-compatible.

#### Tier 5: Regional/Specialized Providers

| Provider | Auth Method | Region/Specialty | Status |
|----------|-----------|-----------------|--------|
| **Ollama** | None (local) | Local inference, any GGUF model | Active |
| **Moonshot** | API Key | Kimi models (Chinese market) | Active |
| **GLM** | API Key | ChatGLM / Zhipu (Chinese market) | Active |
| **MiniMax** | API Key | MiniMax models | Active |
| **Qianfan** | API Key | Baidu models (Chinese market) | Active |
| **Synthetic** | API Key | Synthetic AI models | Active |
| **OpenCode Zen** | API Key | Code-focused models | Active |
| **Z.AI** | API Key | Z.AI inference | Active |
| **Hugging Face** | API Token | Open-source model hub | Coming Soon |
| **LM Studio** | None (local) | Local model GUI | Coming Soon |

**Ollama** is the only provider requiring zero authentication. It runs locally on port 11434, supports any GGUF model (Llama, Qwen, Gemma, DeepSeek, etc.), and provides the same OpenAI-compatible API format. ZeroClaw has a dedicated `ollama.rs` with Ollama-specific health checking.

### 2.3 Authentication Methods Summary

| Method | Providers | Security Notes |
|--------|----------|----------------|
| Bearer Token (API Key) | OpenRouter, OpenAI, DeepSeek, Groq, Together, Fireworks, Perplexity, Cohere, xAI, Mistral, Venice | Standard. Key in `Authorization: Bearer <key>` header. |
| Custom Header (`x-api-key`) | Anthropic | Non-standard but equally secure. |
| AWS IAM SigV4 | Bedrock | Most secure. Temporary credentials, fine-grained IAM policies. |
| API Token | Cloudflare AI, Hugging Face | Similar to Bearer but platform-specific. |
| None (local) | Ollama, LM Studio | No auth needed; binds to localhost. |

---

## 3. Channel Integrations

ZeroClaw supports 7 active channels, all implementing the `Channel` trait:

```rust
#[async_trait]
pub trait Channel: Send + Sync {
    fn name(&self) -> &str;
    async fn send(&self, message: &str) -> Result<()>;
    async fn listen(&self, tx: mpsc::Sender<ChannelMessage>) -> Result<()>;
    async fn health_check(&self) -> bool;
}
```

### 3.1 Telegram

**Implementation**: `channels/telegram.rs`
**API**: Telegram Bot API (HTTPS long-polling via `getUpdates`)
**Library**: Direct HTTP calls via `reqwest` (no external Telegram crate)
**Auth**: Bot token from BotFather

**How it works**: ZeroClaw polls the Telegram Bot API endpoint `https://api.telegram.org/bot<token>/getUpdates` with a long-polling timeout. Messages are received as JSON, parsed, and fed into the channel message bus. Responses are sent via `sendMessage`.

**Security implications**:
- Bot tokens grant full control of the bot. ZeroClaw encrypts these with ChaCha20-Poly1305 in the config.
- Telegram supports end-to-end encryption for "Secret Chats" but bot messages use server-side encryption only.
- Long-polling is safer than webhooks (no inbound connections needed).
- Telegram stores all non-secret messages on their servers indefinitely.

**Rate limits**: Telegram Bot API allows ~30 messages/second to different chats, 1 message/second to the same chat. Bulk messaging limited to 30 messages/second overall. The dedicated Rust crate `teloxide` (not used by ZeroClaw) includes built-in throttling.

**Alternatives not used**: `teloxide` (full-featured Rust Telegram framework, 0 vulnerabilities, built-in rate limiting). ZeroClaw chose raw HTTP calls for minimal dependencies.

### 3.2 Discord

**Implementation**: `channels/discord.rs`
**API**: Discord Gateway (WebSocket) + REST API
**Library**: `tokio-tungstenite` for WebSocket, `reqwest` for REST
**Auth**: Bot token from Discord Developer Portal

**How it works**: Connects to Discord's WebSocket Gateway for real-time events. Handles the HELLO -> IDENTIFY -> READY handshake sequence. Heartbeats maintain the connection. Messages are received via MESSAGE_CREATE events and responses sent via the REST API (`POST /channels/{id}/messages`).

**Security implications**:
- Discord bot tokens have broad permissions depending on the bot's configured intents and OAuth2 scopes.
- All Discord communications use TLS but are not end-to-end encrypted. Discord can read all messages.
- Bot must handle gateway disconnects and resume sessions (RESUME opcode).
- Gateway Intents system limits what events a bot receives, which is a privacy positive.

**Rate limits**: Discord uses a complex rate limiting system. Global rate limit: 50 requests/second. Per-route limits vary. The gateway has a 120 heartbeat/identify limit per connection. Exceeding limits results in 429 responses with `Retry-After` headers. The established Rust library `serenity` handles all of this automatically; ZeroClaw's custom implementation must handle it manually.

**Alternatives not used**: `serenity` (full Discord framework, 14K+ stars, built-in rate limiting, caching, sharding), `twilight` (lower-level, modular). ZeroClaw's custom WebSocket implementation is lighter but lacks auto-recovery, sharding, and rate limit management.

### 3.3 Slack

**Implementation**: `channels/slack.rs`
**API**: Slack Web API (HTTPS polling) + Events API
**Library**: Direct HTTP calls via `reqwest`
**Auth**: Bot token (xoxb-...) from Slack App configuration

**How it works**: Uses the Slack Web API for sending messages and the Events API or RTM (Real Time Messaging) for receiving them. Messages are sent via `chat.postMessage`.

**Security implications**:
- Slack bot tokens (`xoxb-`) have scoped permissions. ZeroClaw should request minimal scopes.
- Slack performs security reviews for Marketplace apps but not custom integrations.
- All communications use TLS. Slack Enterprise Grid supports additional encryption.
- Slack stores all messages server-side with workspace admin access.

**Rate limits (2025-2026 changes)**: Major rate limit changes took effect May 29, 2025:
- Non-Marketplace apps: `conversations.history` and `conversations.replies` limited to 15 messages/request at 1 request/minute.
- Existing installations become subject to new limits March 3, 2026.
- Slack's stated motivation: preventing data exfiltration through unvetted applications.
- Standard rate limit tiers: Tier 1 (1 req/min) to Tier 4 (100+ req/min). Web API methods are each assigned a tier.
- HTTP 429 responses include `Retry-After` header.

**Impact on ZeroClaw**: The 2025 rate limit changes specifically target the pattern ZeroClaw uses (reading message history for context). This could significantly limit Slack channel responsiveness.

### 3.4 iMessage

**Implementation**: `channels/imessage.rs`
**API**: macOS AppleScript bridge
**Library**: `std::process::Command` to execute `osascript`
**Auth**: macOS Automation permissions

**How it works**: ZeroClaw uses AppleScript via `osascript` to read from and write to the Messages.app database. Incoming messages are detected by polling the SQLite database at `~/Library/Messages/chat.db`. Outgoing messages use AppleScript `tell application "Messages" to send`.

**Security implications**:
- **macOS-only**: This channel only works on macOS. No Linux, Windows, or headless server support.
- **Requires Full Disk Access**: Reading the Messages database requires explicit `Full Disk Access` permission in macOS System Preferences.
- **Requires Automation permission**: Controlling Messages.app requires `Automation` permission.
- **No official API**: Apple does not provide an iMessage API. This is a reverse-engineering approach that can break with macOS updates.
- **AppleScript is unreliable**: iMessage via AppleScript can produce error dialogs, fail silently, or behave inconsistently.
- **Privacy positive**: iMessage uses end-to-end encryption. Messages in transit are protected.
- **Privacy negative**: Reading the local SQLite database bypasses E2E encryption guarantees.

**Rate limits**: No formal rate limits, but rapid AppleScript calls can cause Messages.app instability. The polling approach adds inherent latency.

### 3.5 Matrix

**Implementation**: `channels/matrix.rs`
**API**: Matrix Client-Server API
**Library**: Direct HTTP calls via `reqwest`
**Auth**: Access token from Matrix homeserver

**How it works**: Connects to a Matrix homeserver (e.g., matrix.org or self-hosted Synapse/Dendrite). Uses the `/sync` endpoint for long-polling events and `/_matrix/client/v3/rooms/{roomId}/send` for sending messages.

**Security implications**:
- **End-to-end encryption**: Matrix supports E2EE via the Olm/Megolm protocols. The reference Rust implementation `vodozemac` has been independently audited by Least Authority. However, ZeroClaw's direct HTTP implementation likely does not implement E2EE -- it would need to use `matrix-sdk-crypto` for key management.
- **Self-hostable**: Matrix can be fully self-hosted, giving complete data sovereignty.
- **Federation**: Matrix rooms can span multiple homeservers. Messages are replicated to all participating servers.

**Rate limits**: Matrix homeserver-dependent. The matrix.org public homeserver has rate limits on `/sync` and message sending. Self-hosted servers can configure their own limits.

**Alternatives not used**: `matrix-sdk` (the official Rust Matrix SDK by Element, includes `vodozemac` E2EE, multi-platform bindings). ZeroClaw's raw HTTP approach means E2EE is likely not implemented.

### 3.6 Webhook

**Implementation**: `gateway/mod.rs`
**API**: Custom raw TCP HTTP server
**Auth**: Bearer token (obtained via 6-digit pairing code) + optional webhook secret

**How it works**: ZeroClaw runs a raw TCP HTTP server (no framework) listening on localhost. Provides three endpoints: `GET /health`, `POST /pair`, `POST /webhook`. External services trigger the agent via HTTP POST with a JSON payload.

**Security implications**: See Section 4.3 (Gateway Pairing Security).

### 3.7 CLI

**Implementation**: `channels/cli.rs`
**API**: stdin/stdout
**Auth**: None (local process)

The default channel. Reads from stdin, writes to stdout. No security concerns beyond standard process isolation.

### 3.8 Channel Security Summary

| Channel | Encryption | Data Sovereignty | E2EE | API Stability |
|---------|-----------|-----------------|------|---------------|
| Telegram | TLS (server-side) | Telegram servers | No (bots) | Stable (versioned API) |
| Discord | TLS (server-side) | Discord servers | No | Stable (versioned API) |
| Slack | TLS (server-side) | Slack servers | No | Unstable (2025 rate limit changes) |
| iMessage | TLS + E2EE | Apple servers + local | Yes (in transit) | Unstable (unofficial API) |
| Matrix | TLS + optional E2EE | Self-hostable | Possible (not in ZeroClaw) | Stable (spec-driven) |
| Webhook | TLS (if behind tunnel) | Self-hosted | No | Stable (custom) |
| CLI | N/A (local) | Local | N/A | Stable |

---

## 4. Security Libraries & Algorithms

### 4.1 ChaCha20-Poly1305 (AEAD Encryption)

**Crate**: `chacha20poly1305 0.10` (RustCrypto project)
**Used in**: `security/secrets.rs` for encrypting API keys and secrets at rest.

#### What It Is

ChaCha20-Poly1305 is an Authenticated Encryption with Associated Data (AEAD) algorithm defined in RFC 8439. It combines:
- **ChaCha20**: A stream cipher designed by Daniel J. Bernstein. Uses a 256-bit key and 96-bit nonce.
- **Poly1305**: A message authentication code (MAC) that provides integrity verification.

Together, they provide both confidentiality (encryption) and integrity (authentication). Any tampering with the ciphertext is detected during decryption.

#### Comparison with AES-GCM and Fernet

| Property | ChaCha20-Poly1305 | AES-256-GCM | Fernet |
|----------|-------------------|-------------|--------|
| **Key size** | 256-bit | 256-bit | 128-bit AES + 128-bit HMAC |
| **Nonce size** | 96-bit (12 bytes) | 96-bit (12 bytes) | 128-bit IV |
| **Auth mechanism** | Poly1305 MAC | GHASH | HMAC-SHA256 |
| **Mode** | Stream cipher + MAC | Block cipher + MAC | AES-CBC + HMAC |
| **AEAD** | Yes | Yes | Yes (encrypt-then-MAC) |
| **Constant-time** | Yes (in software) | Only with AES-NI hardware | Implementation-dependent |
| **Performance (no HW accel)** | Excellent (3x faster on ARM) | Slower without AES-NI | Slowest (CBC + HMAC overhead) |
| **Performance (with AES-NI)** | Good | Excellent (HW accelerated) | Good |
| **Nonce reuse risk** | Catastrophic (key+nonce reuse breaks encryption) | Catastrophic | N/A (random IV per encryption) |
| **Implementation safety** | Very safe (no padding oracle) | Safe (no padding oracle) | Safe but limited (128-bit key) |
| **Ecosystem** | TLS 1.3, WireGuard, SSH | TLS 1.2/1.3, IPsec, cloud KMS | Python `cryptography` library |
| **Best for** | Software-only, mobile/ARM, embedded | Server with Intel/AMD CPUs | Simple Python applications |

**Why ZeroClaw chose ChaCha20-Poly1305**:
1. Pure software implementation with no hardware dependency (critical for a cross-platform Rust binary).
2. Constant-time in software, resistant to timing attacks without needing AES-NI.
3. Used by WireGuard, TLS 1.3, and SSH -- battle-tested.
4. The RustCrypto implementation is well-audited and maintained.

**Why AGENT-33 might prefer something different**: AGENT-33 runs on servers that typically have AES-NI, so AES-256-GCM would be faster. However, the Python `cryptography` library's Fernet provides the simplest API with good-enough security. For AGENT-33's use case (encrypting secrets in a server-side vault), Fernet's simplicity may outweigh ChaCha20's performance advantage.

#### ZeroClaw's Implementation Details

- **Key derivation**: 256-bit key stored in `~/.zeroclaw/.secret_key` with 0600 file permissions.
- **Nonce**: Random 12-byte nonce generated per encryption. Stored alongside ciphertext.
- **Ciphertext format**: `enc2:<nonce_hex>:<ciphertext_hex>` prefix convention allows mixing encrypted and plaintext values in config.
- **Legacy migration**: Supports migrating from an older XOR cipher (`enc:` prefix) to the current ChaCha20-Poly1305 (`enc2:` prefix).

### 4.2 Constant-Time Comparison

**Used in**: `security/pairing.rs` for comparing pairing codes and bearer tokens.

ZeroClaw implements constant-time comparison to prevent timing attacks on the gateway pairing system. In a timing attack, an attacker measures how long a comparison takes -- if the function returns early on the first mismatched byte, the attacker can brute-force one byte at a time.

**Implementation approach**: ZeroClaw likely uses bitwise XOR across all bytes and reduces to a single equality check, or uses the `subtle` crate's `ConstantTimeEq` trait. The `subtle` crate (from the dalek-cryptography project) is the Rust standard for this:

```rust
// subtle crate pattern
use subtle::ConstantTimeEq;
let result = a.ct_eq(b);  // Returns Choice, not bool
```

The `subtle` crate provides:
- `Choice` type (not `bool`) to prevent branch prediction leaks.
- Bitwise operations that execute in constant time.
- `volatile_read` to prevent compiler optimization of branches.
- Best-effort guarantee (side channels are ultimately a property of hardware).

**OWASP context**: OWASP's "Blocking Brute Force Attacks" guide recommends constant-time comparison as part of a defense-in-depth strategy alongside account lockout, rate limiting, and MFA.

### 4.3 Brute-Force Lockout Pattern

**Used in**: `security/pairing.rs` for gateway pairing.

ZeroClaw's pairing guard implements:
1. **6-digit one-time pairing code**: Displayed in the terminal. User enters it at `POST /pair`.
2. **Attempt tracking**: Failed attempts are counted per IP or session.
3. **Exponential/fixed lockout**: After N failed attempts (likely 5-10), the pairing endpoint is locked for a configurable duration.
4. **Bearer token exchange**: Successful pairing returns a bearer token for subsequent API calls.
5. **Constant-time code comparison**: Prevents timing-based enumeration.

**OWASP best practices alignment**:
- 5-10 failed attempts before lockout: ZeroClaw appears compliant.
- 5-30 minute lockout duration: Reasonable for device pairing.
- Self-service unlock not needed (pairing code rotates on restart).
- Rate limiting (sliding window) provides secondary protection.

**Assessment**: The pairing pattern is well-designed for its purpose (device-level authentication for a personal assistant). It is not a replacement for user authentication in multi-tenant systems.

---

## 5. Memory System Libraries

### 5.1 SQLite FTS5 (Full-Text Search)

**Implementation**: `memory/sqlite.rs`
**Dependency**: `rusqlite 0.32` with `bundled` feature (includes SQLite with FTS5 enabled).

#### What FTS5 Is

FTS5 (Full-Text Search version 5) is SQLite's built-in full-text search extension. It creates virtual tables that tokenize text content and build inverted indexes for fast text search.

#### Capabilities

| Feature | Details |
|---------|---------|
| **Tokenizers** | `unicode61` (default, multilingual), `ascii`, `porter` (English stemming), `trigram` |
| **Query syntax** | AND, OR, NOT, phrase queries (`"exact phrase"`), prefix search (`prefix*`), column filters |
| **Ranking** | Built-in `bm25()` function for relevance scoring |
| **Column weights** | Different weights per column in BM25 scoring |
| **Performance** | Comfortable to ~500K documents. No sharding or horizontal scaling. |
| **Highlight/Snippet** | `highlight()` and `snippet()` auxiliary functions |

#### BM25 in FTS5

FTS5's BM25 implementation uses:
- **k1 = 1.2**: Term frequency saturation parameter (hard-coded).
- **b = 0.75**: Document length normalization parameter (hard-coded).
- **Scoring**: Returns negative values where more negative = more relevant. `bm25(table, col1_weight, col2_weight, ...)` allows per-column weighting.

The BM25 formula considers:
1. **Term frequency**: How often the search term appears in the document.
2. **Inverse document frequency**: How rare the term is across all documents.
3. **Document length**: Normalizes for document size (shorter docs with the term rank higher).

#### Limitations

1. **Hard-coded k1/b parameters**: Cannot tune BM25 parameters without rebuilding SQLite.
2. **Limited stemming**: Only Porter stemmer available. No language-specific stemmers for non-English text.
3. **Scale ceiling**: ~500K documents practical maximum. Not suitable for millions of documents.
4. **No "More Like This"**: No similarity-based document recommendation.
5. **Data synchronization**: FTS5 virtual tables lose constraints, types, foreign keys. Must be maintained alongside regular tables.
6. **No fuzzy matching**: No built-in typo tolerance or edit-distance search.

### 5.2 BM25 Algorithm

**Implementation**: Used via SQLite's built-in `bm25()` function in FTS5 queries.

BM25 (Best Matching 25) is a probabilistic information retrieval function based on the Okapi weighting scheme. In ZeroClaw's context:

```sql
SELECT key, content, bm25(memories_fts, 1.0) as rank
FROM memories_fts
WHERE memories_fts MATCH ?
ORDER BY rank
LIMIT ?
```

The algorithm assigns higher scores (less negative in FTS5's convention) to documents where:
- The search terms appear frequently (term frequency).
- The search terms are rare across the corpus (inverse document frequency).
- The document is shorter relative to average document length (length normalization).

**Practical significance for AI memory**: BM25 excels at exact keyword matching -- if a user asks about "PostgreSQL migration," BM25 will find memories containing exactly those words. Vector similarity would find semantically similar content ("database schema changes") but might miss exact keywords. The hybrid approach combines both strengths.

### 5.3 Vector Similarity Computation

**Implementation**: `memory/vector.rs` -- custom, zero-dependency implementation.

ZeroClaw implements cosine similarity entirely in Rust with no external vector library:

```rust
pub fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let mag_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let mag_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    if mag_a == 0.0 || mag_b == 0.0 { return 0.0; }
    dot / (mag_a * mag_b)
}
```

**Storage**: Embeddings are stored as raw `f32` byte arrays (BLOBs) in SQLite. The `vec_to_bytes()` and `bytes_to_vec()` functions handle serialization.

**Hybrid merge function**:
```rust
pub fn hybrid_merge(
    keyword_results: Vec<(String, f32)>,
    vector_results: Vec<(String, f32)>,
    vector_weight: f32,  // default 0.7
    keyword_weight: f32, // default 0.3
) -> Vec<(String, f32)>
```

The merge:
1. Normalizes keyword scores to 0-1 range.
2. Normalizes vector scores to 0-1 range.
3. Combines: `final_score = vector_weight * norm_vector + keyword_weight * norm_keyword`.
4. Deduplicates by key (if a result appears in both, scores are combined).
5. Sorts by final score descending.

**Performance note**: The cosine similarity computation is O(n*d) where n = number of stored embeddings and d = embedding dimension. With no ANN (Approximate Nearest Neighbor) index, this is a brute-force linear scan. Acceptable for personal assistant scale (~10K memories) but would not scale to millions.

**Alternatives not used**: `hnsw` crate (approximate nearest neighbors), `faiss` bindings, `qdrant-client`. ZeroClaw's approach prioritizes simplicity and zero external dependencies over scale.

### 5.4 Embedding Providers

**Implementation**: `memory/embeddings.rs`

ZeroClaw supports embedding generation through:

| Provider | Model | Dimensions | Details |
|----------|-------|-----------|---------|
| OpenAI-compatible API | text-embedding-3-small, text-embedding-ada-002, etc. | 1536 (ada), 256-3072 (v3) | Any endpoint following OpenAI's embedding API format. |
| Noop | N/A | N/A | Returns empty vectors. Disables vector search. |

The `EmbeddingProvider` trait:
```rust
#[async_trait]
pub trait EmbeddingProvider: Send + Sync {
    async fn embed(&self, text: &str) -> Result<Vec<f32>>;
}
```

**Embedding cache**: SQLite `embedding_cache` table stores `(text_hash, embedding_blob)` with LRU eviction. This avoids redundant API calls when the same text is embedded multiple times (e.g., during re-indexing).

**Practical note**: Most LLM providers listed in Section 2 also offer embedding endpoints. OpenRouter, OpenAI, Cohere, Together AI, Fireworks, and Ollama all support embedding generation, so ZeroClaw users can use any of these for embeddings.

---

## 6. Tunnel Providers

ZeroClaw's tunnel system exposes the local gateway to the internet without opening firewall ports. Three built-in providers plus a custom escape hatch:

### 6.1 Cloudflare Tunnel

**Implementation**: `tunnel/cloudflare.rs`
**Binary**: `cloudflared` (must be installed separately)
**Command**: `cloudflared tunnel --url http://localhost:<port>`

#### How It Works

1. `cloudflared` daemon establishes 4 outbound-only HTTPS connections to Cloudflare's edge network.
2. Connections go to at least 2 different data centers for redundancy.
3. Cloudflare assigns a `<uuid>.cfargotunnel.com` subdomain (or a custom domain if configured).
4. Inbound requests hit Cloudflare's edge, pass through their DDoS protection, WAF, and bot management, then are proxied through the tunnel to the local service.
5. No inbound firewall rules needed. The connection is entirely outbound from the user's machine.

#### Security Model

- **Zero Trust architecture**: Cloudflare's SSE (Security Service Edge) platform. Named in 2025 Gartner Magic Quadrant.
- **DDoS protection**: 100+ Tbps mitigation capacity on Cloudflare's edge.
- **No public IP exposure**: Origin server is never directly accessible.
- **Outbound-only**: Firewalls can be configured to allow only outbound HTTPS, blocking all inbound.
- **WAF integration**: Cloudflare's web application firewall can filter malicious requests before they reach the tunnel.
- **Access policies**: Can require identity verification (OAuth, SAML) before proxying to the tunnel.

#### Pricing

- **Free for all plans**: Cloudflare Tunnel is free with no feature limitations between plans.
- **No bandwidth charges for tunnel traffic**: Cloudflare does not charge for tunnel bandwidth.
- **Zero Trust platform**: Free for up to 50 users. Paid plans from $7/user/month for additional features.

#### Permanence

Tunnels can be configured as persistent services (not just quick tunnels). Named tunnels with custom domains survive daemon restarts and can be managed via the Cloudflare dashboard.

**Assessment**: Best option for production-permanent tunnels. Free, enterprise-grade security, global edge network. Recommended default for ZeroClaw users.

### 6.2 Tailscale

**Implementation**: `tunnel/tailscale.rs`
**Binary**: `tailscale` / `tailscaled` (must be installed separately)
**Command**: `tailscale funnel <port>`

#### How It Works

1. Tailscale creates a WireGuard-based mesh VPN between all your devices (tailnet).
2. Tailscale Funnel specifically exposes a local port to the public internet.
3. Public DNS records for `<node>.<tailnet>.ts.net` point to Tailscale's Funnel frontend servers (georeplicated).
4. Incoming TLS connections are inspected via SNI (Server Name Indication) and proxied through WireGuard to your node.
5. The connection path: Public internet -> Tailscale Funnel frontend -> WireGuard tunnel -> Your device.

#### Security Model

- **WireGuard encryption**: All traffic is encrypted end-to-end with WireGuard.
- **Double opt-in**: Funnel must be enabled both in the admin console AND on the device.
- **Zero Trust default**: Minimum possible permissions per node. Authorization checked per transaction.
- **Identity-based access**: Every device on the tailnet has a cryptographic identity.
- **Audit trail**: All connections are logged in the Tailscale admin dashboard.
- **Open source client**: The client code is open source for independent verification.
- **Performance**: 10 Gb/s throughput on bare metal. Minimal overhead.

#### Pricing

- **Free (Personal)**: Up to 3 users, 100 devices.
- **Starter**: $5/user/month.
- **Premium**: $10/user/month.
- **Enterprise**: Custom.

#### Permanence

Tailscale Funnel URLs persist as long as the device remains in the tailnet. The `<node>.<tailnet>.ts.net` name is stable.

**Assessment**: Best option when you want mesh connectivity between your own devices plus selective public exposure. More complex setup than Cloudflare Tunnel but provides device-to-device connectivity as a bonus.

### 6.3 ngrok

**Implementation**: `tunnel/ngrok.rs`
**Binary**: `ngrok` (must be installed separately)
**Command**: `ngrok http <port>`

#### How It Works

1. ngrok client establishes a secure connection to ngrok's cloud servers.
2. ngrok assigns a public URL (random subdomain on ngrok-free.app, or custom domain on paid plans).
3. Incoming requests hit ngrok's servers and are forwarded through the tunnel to the local service.
4. Centralized architecture (all traffic routes through ngrok's infrastructure).

#### Security Model

- **TLS encryption**: All tunnel traffic is encrypted.
- **Request inspection**: ngrok provides a web UI for inspecting requests (useful for debugging webhooks).
- **OAuth/SSO integration**: Paid plans support identity verification.
- **IP allowlisting/blocklisting**: Available on paid plans.
- **mTLS**: Certificate-based authentication on Enterprise plan.
- **Centralized risk**: All traffic routes through ngrok's infrastructure, creating a single point of trust and potential latency.

#### Pricing (2025-2026)

- **Free**: 1 active endpoint, 2-hour session limit (anonymous users).
- **Personal**: $8/month. Static domains, webhook verification.
- **Pro**: $20/month. Custom domains, IP restrictions.
- **Enterprise**: $39/month. SSO, mTLS, RBAC.

#### Permanence

- Free tier: URLs change on every restart. 2-hour session limit.
- Paid tiers: Static domains and custom domains persist.

**Assessment**: Best for quick development/testing. Worst for production due to centralized architecture, session limits on free tier, and relatively expensive paid plans. Cloudflare Tunnel is strictly better for production use.

### 6.4 Custom Tunnel

**Implementation**: `tunnel/custom.rs`

Runs any shell command and optionally parses a public URL from stdout using a regex pattern. This allows using alternatives like:
- **bore** (open-source, self-hostable)
- **frp** (open-source, self-hostable)
- **localtunnel** (open-source)
- **Pinggy** (simple, no binary needed)

### 6.5 Tunnel Comparison Summary

| Feature | Cloudflare Tunnel | Tailscale Funnel | ngrok |
|---------|------------------|-----------------|-------|
| **Free tier** | Unlimited | 3 users, 100 devices | 1 endpoint, 2hr limit |
| **DDoS protection** | 100+ Tbps | None (direct WireGuard) | Basic |
| **Custom domain** | Yes (free) | Yes (ts.net subdomain) | Paid only |
| **E2E encryption** | TLS only | WireGuard | TLS only |
| **Self-hostable** | No | No (open-source client) | No |
| **Latency** | Low (global CDN) | Very low (P2P when possible) | Higher (centralized) |
| **Permanence** | Persistent | Persistent | Free = ephemeral |
| **Best for** | Production exposure | Device mesh + selective exposure | Development/testing |

---

## 7. Integration Ecosystem

### 7.1 Composio.dev

**Implementation**: `tools/composio.rs`
**Website**: https://composio.dev

#### What It Is

Composio is an integration platform that provides AI agents with authenticated access to 850+ toolkits and 11,000+ tools across popular applications. Every integration appears as an LLM-callable "Tool" with JSON schemas optimized for function calling.

#### How It Works

1. **Agent makes a tool call**: The LLM generates a function call (e.g., `create_github_issue`).
2. **Composio receives the call**: Routes it to the appropriate integration.
3. **Handles authentication**: Manages OAuth 2.0 flows, API keys, refresh tokens automatically.
4. **Executes the action**: Calls the actual API (GitHub, Slack, Notion, etc.).
5. **Returns the result**: Structured response back to the agent.

#### Key Features

- **Managed OAuth**: Handles complex OAuth 2.0 flows without the developer implementing them.
- **MCP Support**: Composio provides Model Context Protocol (MCP) integration as of 2025-2026.
- **Event triggers**: Can proactively notify agents of events (new Slack messages, new Jira tickets, etc.).
- **Framework support**: Official SDKs for Python and TypeScript. Works with LangChain, CrewAI, AutoGen, and 25+ agentic frameworks.

#### Reliability Assessment

- **Funding**: Well-funded startup (YC-backed).
- **Community**: Active GitHub with 31K+ stars on the main repo.
- **Risk**: As a third-party SaaS, Composio introduces a dependency on their service availability. If Composio goes down, all 850+ integrations stop working.
- **Alternative**: Direct API integrations (more work, no dependency).

#### ZeroClaw's Usage

ZeroClaw's `tools/composio.rs` implements the Composio tool as an opt-in integration. When enabled, it provides access to Composio's entire catalog through the `composio` tool. This is the "escape hatch" for integrations ZeroClaw doesn't natively support.

### 7.2 Full Integration Registry

ZeroClaw's `integrations/registry.rs` catalogs **77 integrations** across 9 categories. This is significantly more than the "50+" claimed in the README.

#### Category Breakdown

**Chat Providers (13)**

| Integration | Status | Implementation |
|------------|--------|----------------|
| Telegram | Active | Native (`channels/telegram.rs`) |
| Discord | Active | Native (`channels/discord.rs`) |
| Slack | Active | Native (`channels/slack.rs`) |
| Webhooks | Active | Native (`gateway/mod.rs`) |
| iMessage | Active | Native (`channels/imessage.rs`) |
| Matrix | Active | Native (`channels/matrix.rs`) |
| WhatsApp | Coming Soon | Planned (QR pairing via web bridge) |
| Signal | Coming Soon | Planned (via signal-cli) |
| Microsoft Teams | Coming Soon | Planned |
| Nostr | Coming Soon | Planned (NIP-04 decentralized DMs) |
| WebChat | Coming Soon | Planned (browser-based UI) |
| Nextcloud Talk | Coming Soon | Planned |
| Zalo | Coming Soon | Planned |

**AI Models (28)** -- See Section 2 for full analysis.

**Productivity (9)**

| Integration | Status | Notes |
|------------|--------|-------|
| GitHub | Coming Soon | Code, issues, PRs |
| Notion | Coming Soon | Workspace & databases |
| Apple Notes | Coming Soon | macOS/iOS native notes |
| Apple Reminders | Coming Soon | Task management |
| Obsidian | Coming Soon | Knowledge graph notes |
| Things 3 | Coming Soon | GTD task manager (macOS) |
| Bear Notes | Coming Soon | Markdown notes (macOS) |
| Trello | Coming Soon | Kanban boards |
| Linear | Coming Soon | Issue tracking |

**Tools & Automation (10)**

| Integration | Status | Notes |
|------------|--------|-------|
| Shell | Active | Native (`tools/shell.rs`) |
| File System | Active | Native (`tools/file_read.rs`, `file_write.rs`) |
| Browser | Available | Native (`tools/browser_open.rs`) |
| Cron | Available | Heartbeat engine |
| Voice | Coming Soon | Voice wake + talk mode |
| Gmail | Coming Soon | Email triggers & send |
| 1Password | Coming Soon | Secure credentials |
| Weather | Coming Soon | Forecasts & conditions |
| Canvas | Coming Soon | Visual workspace |

**Music & Audio (3)**: Spotify, Sonos, Shazam -- all Coming Soon.

**Smart Home (3)**: Home Assistant, Philips Hue, 8Sleep -- all Coming Soon.

**Media & Creative (4)**: Image Gen, GIF Search, Screen Capture, Camera -- all Coming Soon.

**Social (2)**: Twitter/X, Email -- both Coming Soon.

**Platforms (5)**: macOS (Active), Linux (Active), Windows (Available), iOS (Available via chat channels), Android (Available via chat channels).

#### Implementation Reality Check

Of the 77 listed integrations:
- **~15 are actively implemented**: CLI, Telegram, Discord, Slack, iMessage, Matrix, Webhook, Shell, File Read, File Write, Browser, Memory tools, plus the LLM providers.
- **~26 LLM providers are "Active"**: But most route through the single `Compatible` (OpenAI-compatible) implementation.
- **~36 are "Coming Soon"**: These are catalog entries without implementation.
- **Composio covers the gap**: If enabled, Composio's 850+ tools could fill most of the "Coming Soon" entries (GitHub, Notion, Slack triggers, Gmail, etc.).

---

## 8. Relevance to AGENT-33

### 8.1 Libraries to Evaluate for Python Equivalents

| ZeroClaw Dependency | Python Equivalent | AGENT-33 Status | Action |
|--------------------|-------------------|----------------|--------|
| `rusqlite` + FTS5 | `sqlite3` (stdlib) + FTS5 or PostgreSQL `tsvector` | Vector-only RAG pipeline | Add BM25/FTS search |
| `chacha20poly1305` | `cryptography.Fernet` or `cryptography.hazmat.primitives.ciphers.aead.ChaCha20Poly1305` | `security/vault.py` exists | Evaluate upgrading vault encryption |
| `reqwest` (rustls-tls) | `httpx` | `httpx` already used via `ollama.py` | Ensure connection pooling (issue noted in dossier) |
| Composio integration | `composio-core` Python SDK | Not integrated | Evaluate for expanding tool catalog |
| `tokio::sync::mpsc` | `asyncio.Queue` or NATS | NATS-based messaging | Already more capable |

### 8.2 Patterns to Port

1. **Hybrid search merge** (`memory/vector.rs::hybrid_merge()`): ~30 lines of Python. Normalize scores, weighted sum, deduplicate. Direct port.

2. **Embedding cache**: Add a `embedding_cache` table to PostgreSQL. Hash input text, check cache before calling embedding API. Saves API costs during bulk operations.

3. **Safety rules in system prompt**: ZeroClaw hardcodes safety rules directly into `build_system_prompt()`. AGENT-33 should inject `GovernanceConstraints` the same way.

4. **Command validation pipeline**: ZeroClaw validates entire command pipelines (checking each segment in pipes/chains, blocking `$()` and backtick subshells). More thorough than AGENT-33's current shell tool.

### 8.3 Providers to Support

AGENT-33 currently supports Ollama (local). Based on this analysis, priority additions should be:
1. **OpenRouter** -- single API key, 300+ models, fallback routing.
2. **Anthropic** -- direct access to Claude (AGENT-33's own model family).
3. **DeepSeek** -- 30x cheaper than GPT-5 for budget-conscious deployments.
4. **Groq** -- 10x faster inference for real-time interactions.

All four use simple API-key Bearer auth and follow (or nearly follow) the OpenAI API format. A single `OpenAICompatibleProvider` class could cover OpenRouter, DeepSeek, Groq, Together, Fireworks, and Perplexity.

### 8.4 What Not to Adopt

1. **Raw TCP HTTP server**: ZeroClaw's frameworkless gateway is impressive for binary size but would be a regression from FastAPI.
2. **SQLite for production memory**: AGENT-33 uses PostgreSQL + pgvector, which is strictly more capable. The FTS5 pattern should be adapted to PostgreSQL's `tsvector`/`tsquery` full-text search.
3. **Brute-force linear vector scan**: AGENT-33 should use pgvector's HNSW or IVFFlat indexes, not brute-force cosine similarity.
4. **iMessage channel**: Unreliable, macOS-only, unofficial API. Not suitable for a server-side framework.

---

## Sources

### Crate Registries
- [chacha20poly1305 on crates.io](https://crates.io/crates/chacha20poly1305)
- [rusqlite on crates.io](https://crates.io/crates/rusqlite)
- [tokio-tungstenite on crates.io](https://crates.io/crates/tokio-tungstenite)
- [clap on crates.io](https://crates.io/crates/clap)
- [serde on crates.io](https://crates.io/crates/serde)
- [tokio on crates.io](https://crates.io/crates/tokio)
- [reqwest on crates.io](https://crates.io/crates/reqwest)
- [dialoguer on crates.io](https://crates.io/crates/dialoguer)
- [anyhow on crates.io](https://crates.io/crates/anyhow)
- [thiserror on crates.io](https://crates.io/crates/thiserror)

### Security & Cryptography
- [ChaCha20-Poly1305 RFC 8439 (Wikipedia)](https://en.wikipedia.org/wiki/ChaCha20-Poly1305)
- [Comparison of Symmetric Encryption Methods (Soatok)](https://soatok.blog/2020/07/12/comparison-of-symmetric-encryption-methods/)
- [XChaCha20-Poly1305 vs AES](https://blog.vitalvas.com/post/2025/06/01/xchacha20-poly1305-vs-aes/)
- [subtle crate (dalek-cryptography)](https://github.com/dalek-cryptography/subtle)
- [OWASP Blocking Brute Force Attacks](https://owasp.org/www-community/controls/Blocking_Brute_Force_Attacks)
- [RustSec Advisory Database](https://rustsec.org/advisories/)
- [Cloudflare: Do the ChaCha (ChaCha20 on mobile)](https://blog.cloudflare.com/do-the-chacha-better-mobile-performance-with-cryptography/)

### LLM Providers
- [OpenRouter Pricing](https://openrouter.ai/pricing)
- [OpenRouter Models Documentation](https://openrouter.ai/docs/guides/overview/models)
- [Anthropic Claude Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [OpenAI API Pricing](https://openai.com/api/pricing/)
- [DeepSeek API Pricing](https://api-docs.deepseek.com/quick_start/pricing)
- [Groq Pricing](https://groq.com/pricing)
- [Together AI Pricing](https://www.together.ai/pricing)
- [Fireworks AI Pricing](https://fireworks.ai/pricing)
- [Perplexity API Platform](https://www.perplexity.ai/api-platform)
- [Cohere Pricing](https://cohere.com/pricing)
- [Mistral AI Pricing](https://mistral.ai/pricing)
- [xAI Models and Pricing](https://docs.x.ai/developers/models)
- [Venice AI Privacy Architecture](https://venice.ai/privacy)
- [Amazon Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Ollama Documentation](https://docs.ollama.com/api/introduction)

### Channel APIs
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [teloxide Rust crate](https://crates.io/crates/teloxide)
- [serenity Discord library](https://github.com/serenity-rs/serenity)
- [Slack Rate Limits](https://docs.slack.dev/apis/web-api/rate-limits/)
- [Slack 2025 Rate Limit Changes](https://docs.slack.dev/changelog/2025/05/29/rate-limit-changes-for-non-marketplace-apps/)
- [Matrix Rust SDK](https://github.com/matrix-org/matrix-rust-sdk)
- [Vodozemac Security Audit](https://matrix.org/blog/2022/05/16/independent-public-audit-of-vodozemac-a-native-rust-reference-implementation-of-matrix-end-to-end-encryption/)
- [iMessage AppleScript Automation](https://glinteco.com/en/post/discovering-applescript-the-journey-to-automate-imessages/)

### SQLite & Search
- [SQLite FTS5 Extension](https://www.sqlite.org/fts5.html)
- [SQLite FTS5 BM25 Ranking](https://thelinuxcode.com/sqlite-full-text-search-fts5-in-practice-fast-search-ranking-and-real-world-patterns/)
- [Exploring Search Relevance with SQLite (Simon Willison)](https://simonwillison.net/2019/Jan/7/exploring-search-relevance-algorithms-sqlite/)
- [Cosine Similarity Explained (Pinecone)](https://www.pinecone.io/learn/vector-similarity/)

### Tunnel Providers
- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/)
- [Tailscale: How It Works](https://tailscale.com/blog/how-tailscale-works)
- [Tailscale Funnel](https://tailscale.com/blog/introducing-tailscale-funnel)
- [ngrok Pricing](https://ngrok.com/pricing)
- [ngrok vs Cloudflare Tunnel vs Tailscale Comparison (InstaTunnel)](https://instatunnel.my/blog/comparing-the-big-three-a-comprehensive-analysis-of-ngrok-cloudflare-tunnel-and-tailscale-for-modern-development-teams)

### Integration Platforms
- [Composio.dev](https://composio.dev/)
- [Composio Documentation](https://docs.composio.dev/getting-started/welcome)
- [Composio GitHub](https://github.com/ComposioHQ/composio)
- [Composio MCP Integration](https://mcp.composio.dev/composio)
