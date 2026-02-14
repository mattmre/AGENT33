# Repo Dossier: yt-dlp/yt-dlp

**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

yt-dlp is a feature-rich command-line media downloader forked from youtube-dl, supporting 1800+ websites through an extensible extractor architecture. It targets developers, power users, and automation pipelines that need to reliably extract and download audio/video from web sources. The primary interface is CLI with an embeddable Python API (`YoutubeDL` class). Its core orchestration primitive is a three-phase pipeline: URL extraction (parse metadata from any supported site), protocol-specific download (HTTP, HLS, DASH, RTMP, etc.), and ordered post-processor chain (transcode, tag, embed thumbnails, sponsor removal). The project is the de facto standard for programmatic media acquisition, with ~80k GitHub stars and active daily development.

## 2) Core orchestration model

- **Primary primitive:** Three-phase pipeline (extract -> download -> post-process) orchestrated by the `YoutubeDL` singleton. Not a DAG or agent graph -- it is a linear pipeline with plugin points at each phase. Playlist/batch processing adds a loop around the pipeline with per-item error isolation.
- **State model:** Explicit `info_dict` dictionary threaded through every phase. The info_dict accumulates fields across extraction (metadata), download (file paths, format selection), and post-processing (converted paths, embedded metadata). No persistent state between runs; each invocation is stateless. Archive files (`--download-archive`) provide idempotency by recording completed download IDs.
- **Concurrency:** Single-threaded by default. Concurrent fragment downloads for HLS/DASH via `--concurrent-fragments N` (thread pool). No async/await -- uses synchronous I/O with `urllib`/`requests`-style networking. Playlist items processed sequentially.
- **Human-in-the-loop:** No interactive approval modes. All behavior controlled by CLI flags and config files. `--simulate` / `--print` for dry-run inspection. `--cookies-from-browser` for auth delegation. Format selection (`-f`) acts as a declarative constraint system rather than interactive choice.

## 3) Tooling and execution

- **Tool interface:** Internal plugin/extension system based on Python class inheritance. Three extension points: `InfoExtractor` subclasses (in `yt_dlp/extractor/`), `PostProcessor` subclasses (in `yt_dlp/postprocessor/`), and `FileDownloader` subclasses (in `yt_dlp/downloader/`). External plugins discovered via `yt_dlp_plugins/` namespace packages. No JSON-RPC, MCP, or function-calling interface -- pure Python API and CLI.
- **Runtime environment:** Local execution only. Distributed as a standalone binary (PyInstaller), pip package, or native package manager installs. Optional FFmpeg dependency for post-processing. No Docker/Kubernetes official deployment (community-contributed containers exist).
- **Sandboxing / safety controls:** Minimal sandboxing -- runs with user permissions. `--no-exec` prevents post-processor execution of external commands. Filesystem path sanitization prevents directory traversal in output templates. Cookie handling restricted to known browser paths. No formal security model or allowlist system.

## 4) Observability and evaluation

- **Tracing/logging:** Built-in verbose logging via `--verbose` flag. Progress bars for downloads. Debug output includes HTTP request/response details, extractor selection logic, format selection reasoning. No structured log export or OpenTelemetry. Logging is to stderr with configurable verbosity levels.
- **Evaluation harness:** Embedded test cases per extractor via `_TESTS` class attribute -- each extractor carries its own test URLs and expected output fields. Full pytest suite in `test/`. CI runs extractors against live sites (inherently flaky due to site changes). `--test` flag for developer testing of individual extractors. No formal benchmark suite, but the sheer number of extractors (~1800+) provides broad regression coverage.

## 5) Extensibility

- **Where extensions live:** `yt_dlp_plugins/extractor/` for custom extractors, `yt_dlp_plugins/postprocessor/` for custom post-processors. Uses Python namespace packages so plugins can be installed as separate pip packages or dropped into the plugins directory.
- **How to add tools/skills:** Subclass `InfoExtractor` (define `_VALID_URL` regex and `_real_extract()` method) or subclass `PostProcessor` (implement `run()` method). No registration code needed -- class discovery is automatic via module scanning and `__init__.py` imports. Plugin classes just need to exist in the correct namespace package.
- **Config surface:** ~400 CLI options covering format selection, output templates, network behavior, authentication, post-processing, and metadata handling. Config files supported via `--config-location` (one option per line). Environment variable `YT_DLP_CONFIG` for default config path. Per-extractor options via `--extractor-args KEY:VALUE`.

## 6) Notable practices worth adopting in AGENT 33

1. **Extractor pattern as a model for tool/adapter auto-discovery.** Each extractor is a self-contained class with a `_VALID_URL` regex that declares what inputs it handles. The registry scans all subclasses and routes URLs to the matching extractor. AGENT-33 could adopt this pattern for its tool registry: each tool declares an input pattern it handles, and the registry auto-routes based on matching. This eliminates manual registration boilerplate.

2. **Embedded test cases per module (`_TESTS` class attribute).** Every extractor carries its own test data as a class-level list of dictionaries specifying input URL, expected output fields, and skip conditions. This collocates tests with implementation, making it impossible to add an extractor without at least one test. AGENT-33 agent definitions (JSON files in `agent-definitions/`) could adopt this pattern: embed test scenarios directly in the definition.

3. **Structured exception hierarchy with graceful batch degradation.** yt-dlp defines specific exception types (`GeoRestrictedError`, `AgeRestrictedError`, `ExtractError`, `UnsupportedError`) and handles them per-item in batch/playlist operations. One failed item logs the error and continues to the next. AGENT-33 workflow step execution could adopt this: typed step-failure exceptions with per-step error isolation so one failed action does not abort the entire DAG.

4. **Info-dict as an explicit, evolving state object.** The `info_dict` is a plain dictionary that accumulates fields as it flows through extraction, format selection, download, and post-processing. Each phase adds its fields without mutating previous ones. This is a simple, debuggable state model. AGENT-33 workflow state currently uses expression evaluation; adopting an explicit accumulated-dict pattern for step outputs would improve traceability.

5. **Format selection as a declarative constraint language.** The `-f` flag accepts a mini-language: `bestvideo[height<=1080]+bestaudio/best`. This declarative approach lets users express preferences without imperative logic. AGENT-33 could apply this pattern to agent selection or resource allocation: declarative constraints rather than hard-coded routing.

6. **Output template system with field sanitization.** The `%(title)s-%(id)s.%(ext)s` template system supports conditional expressions, default values, and OS-aware path sanitization. This is more robust than simple string interpolation. AGENT-33 workflow expressions could adopt the sanitization and default-value patterns.

7. **Post-processor chain as composable pipeline.** Post-processors are independent, ordered units that each receive and return the state dict. They can be freely composed (extract audio, then embed metadata, then move to folder). AGENT-33 workflow actions already follow a similar pattern but could formalize the "action receives state, returns modified state" contract more explicitly.

## 7) Risks / limitations to account for

- **No async architecture.** yt-dlp is synchronous and single-threaded for most operations. This limits its applicability as a model for AGENT-33's async FastAPI architecture. The patterns (extractor routing, pipeline composition) are transferable, but the implementation style is not.
- **Fragile live-site dependency.** Extractors break frequently when sites change their page structure or API. The project handles this with rapid release cycles (sometimes multiple releases per week). Any AGENT-33 integration that wraps yt-dlp must account for version churn and extractor failures as normal operating conditions, not exceptional errors.
- **No formal security model.** yt-dlp executes user-provided output templates, runs FFmpeg with constructed arguments, and processes untrusted web content. There is minimal input validation beyond path sanitization. If AGENT-33 agents invoke yt-dlp, the command construction must be done through the existing `run_command` action with allowlist enforcement, never by passing unsanitized user input to yt-dlp CLI flags.
- **Large dependency surface.** The project has ~1800+ extractors, meaning the codebase is massive. Importing yt-dlp as a library pulls in significant code. For AGENT-33 integration, CLI invocation via subprocess (matching the existing `CLIAdapter` pattern in `engine/src/agent33/execution/adapters/`) is preferable to library embedding.
- **Cookie and authentication handling.** yt-dlp can read browser cookies and handle various authentication schemes. If AGENT-33 agents use yt-dlp, credential management must go through AGENT-33's vault/encryption layer, not yt-dlp's native cookie handling, to maintain security boundaries.

## 8) Feature extraction (for master matrix)

- **Repo:** yt-dlp/yt-dlp
- **Primary language:** Python 3.8+
- **Interfaces:** CLI (primary), embeddable Python API (`YoutubeDL` class), no REST/gRPC/MCP
- **Orchestration primitives:** Three-phase linear pipeline (extract/download/post-process) with batch loop; no DAG, no agent graph
- **State/persistence:** Ephemeral `info_dict` dictionary per invocation; `--download-archive` file for cross-run idempotency; no database
- **HITL controls:** None at runtime; all behavior configured declaratively via CLI flags and config files; `--simulate` for dry-run
- **Sandboxing:** Minimal; path sanitization for output templates; `--no-exec` to prevent external command execution; no process isolation
- **Observability:** Verbose logging to stderr; progress bars; no structured tracing or metrics export
- **Evaluation:** Embedded `_TESTS` per extractor class; pytest suite; CI against live sites; no formal benchmarks
- **Extensibility:** Namespace package plugin system for extractors and post-processors; class inheritance with auto-discovery; ~400 CLI options; per-extractor args

## 9) Evidence links

- https://github.com/yt-dlp/yt-dlp -- Repository root and README
- https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py -- Core orchestrator class
- https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/common.py -- InfoExtractor base class
- https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/postprocessor/common.py -- PostProcessor base class
- https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/downloader/common.py -- FileDownloader base class
- https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/plugins.py -- Plugin discovery system
- https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/options.py -- CLI option definitions
- https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/networking/ -- Network abstraction layer
- https://github.com/yt-dlp/yt-dlp/wiki/Extractors -- Extractor development guide
- https://github.com/yt-dlp/yt-dlp/wiki/FAQ -- Frequently asked questions
- https://github.com/yt-dlp/yt-dlp/blob/master/CONTRIBUTING.md -- Contribution guidelines
- https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md -- Full list of supported sites
- https://github.com/yt-dlp/yt-dlp/blob/master/README.md#output-template -- Output template documentation

---

## 10) AGENT-33 Adaptation Analysis

> *This section focuses on patterns transferable to AGENT-33's engine architecture.*

### Recommended Adaptations

#### A. Auto-Discovery via Base-Class Scanning (Extractor Pattern)

**Source pattern:** Every `InfoExtractor` subclass defines `_VALID_URL` regex. `YoutubeDL` scans all subclasses and builds a routing table. No manual registration needed.

**AGENT-33 application:** The current `ToolRegistry` in `engine/src/agent33/tools/registry.py` uses YAML-based registration. An alternative auto-discovery mode could scan for `Tool` subclasses with a `handles_pattern` attribute, similar to how the `AgentRegistry` auto-discovers JSON definitions. This would allow tools to be added by simply creating a new Python module conforming to the base class contract.

#### B. Embedded Test Cases in Definitions

**Source pattern:** `_TESTS = [{"url": "...", "info_dict": {"title": "...", "id": "..."}}]` on every extractor class.

**AGENT-33 application:** Agent definitions in `engine/agent-definitions/*.json` could include a `tests` array with input/expected-output pairs. The test harness (`engine/src/agent33/testing/`) could auto-generate test cases from these embedded definitions, ensuring every agent definition ships with at least one behavioral test.

#### C. Typed Exception Hierarchy with Per-Item Isolation

**Source pattern:** `GeoRestrictedError`, `AgeRestrictedError`, `UnsupportedError` all inherit from `DownloadError`. Playlist processing catches per-item and continues.

**AGENT-33 application:** The workflow step executor currently has generic error handling. Defining typed step exceptions (`StepValidationError`, `StepTimeoutError`, `StepDependencyError`, `StepPermissionError`) with per-step catch-and-continue semantics would improve resilience. The existing `retries` and `timeouts` in the step executor could be extended with exception-type-specific retry policies (e.g., retry on timeout, skip on permission error).

#### D. Declarative Constraint Language for Selection

**Source pattern:** Format selection mini-language: `bestvideo[height<=1080]+bestaudio/best` with filters, sorting, and fallback chains.

**AGENT-33 application:** Agent selection for workflow steps could support a declarative constraint syntax rather than hard-coded agent names. Example: `agent[capability=code_execution,load<0.8]/fallback_agent`. This would enable dynamic agent routing based on capabilities and current state, similar to how yt-dlp selects the best available format.

#### E. Pipeline State Accumulation Pattern

**Source pattern:** `info_dict` starts with URL, gains metadata from extractor, gains file paths from downloader, gains processing flags from post-processors. Each phase appends; no phase deletes prior fields.

**AGENT-33 application:** Workflow step outputs currently go through the expression evaluator. Formalizing an "accumulated state dict" that each action appends to (never overwrites) would improve debuggability and enable workflow replay by inspecting the state dict at any checkpoint.

### Implementation Priority

| Adaptation | Impact | Effort | Priority |
|------------|--------|--------|----------|
| C. Typed Exception Hierarchy | High | Low | 1 |
| B. Embedded Test Cases in Definitions | High | Medium | 2 |
| A. Auto-Discovery via Base-Class Scanning | Medium | Medium | 3 |
| E. Pipeline State Accumulation | Medium | Medium | 4 |
| D. Declarative Constraint Language | Medium | High | 5 |

### Non-Applicable Patterns

The following yt-dlp patterns are **excluded** as they do not transfer well to AGENT-33:

- Synchronous I/O model (AGENT-33 is async/FastAPI)
- CLI-first interface design (AGENT-33 is API-first)
- Global singleton `YoutubeDL` instance pattern (AGENT-33 uses dependency injection)
- Browser cookie extraction (AGENT-33 has its own vault/auth layer)
- FFmpeg subprocess orchestration specifics (AGENT-33 has the CLIAdapter abstraction)
