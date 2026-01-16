# RSMFConverter Project Context

## Project Overview

RSMFConverter is an open-source tool for converting messaging formats to RSMF (Relativity Short Message Format) for eDiscovery. This project aims to match and exceed all commercial competitors.

## Current State

**Status**: Phase 11 COMPLETE + Backlog Regression Tests + Teams i18n Integration

**Test Count**: 2825 tests passing (2 skipped acceptance criteria)

### Completed Work
- Comprehensive research on 6+ competitor tools (Message Crawler, ReadySuite, Cellebrite, Magnet Axiom, Nuix, Relativity)
- Full RSMF 2.0 specification documented
- 40-phase development roadmap with ~600 features
- Agent implementation guides created
- All documentation organized in `docs/` folder
- **Phase 1 Foundation** (2026-01-13):
  - Project structure with Poetry (`pyproject.toml`)
  - Source code structure (`src/rsmfconverter/`)
  - Core modules: exceptions, types, utils, config, logging, CLI
  - Test structure with pytest fixtures
  - Git configuration (.gitignore, .gitattributes, PR templates)
  - CI/CD with GitHub Actions
  - Code quality tools (ruff, pre-commit hooks)
  - Development automation (Makefile)
- **Phase 1 Verification** (2026-01-13):
  - All 416 unit tests passing (90% coverage)
  - Ruff linting: 0 errors
  - Mypy type checking: 0 issues across 22 files
  - CLI commands verified working
  - Code review completed: 0 critical issues, all high-priority fixes applied
  - API documentation created (`docs/api/PHASE-01-API.md`)
- **Phase 2 Data Models** (2026-01-13):
  - 10 Pydantic v2 model classes in `src/rsmfconverter/models/`
  - Participant, Conversation, 6 Event types, Attachment, Reaction, Edit, ReadReceipt, RSMFDocument
  - RSMFDocumentBuilder for fluent document construction
  - 12 factory functions for convenient model creation
  - 270 unit tests (95%+ coverage on models)
  - Security hardening: path traversal prevention in file references
  - Discriminated unions for event type handling
  - Full serialization/deserialization support
  - PR #26: https://github.com/agent-33/RSMFConvert/pull/26 (MERGED)
- **Phase 3 Parser Framework** (2026-01-14):
  - Abstract BaseParser class with parse() method
  - ParserRegistry for format detection and parser management
  - InputSource abstraction (FileSource, ZipArchiveSource, ZipEntrySource)
  - Format detection utilities (WhatsApp, Slack, Teams, Discord, CSV)
  - ParticipantRegistry and ConversationRegistry
  - Timestamp parsing with timezone support
  - EventBuilder for fluent event construction
  - 200+ unit tests (95%+ coverage)
  - PR #27: https://github.com/agent-33/RSMFConvert/pull/27 (MERGED)
- **Phase 4 RSMF Writer** (2026-01-14):
  - RSMFWriter core with multi-format output
  - EML generator (RFC 5322 compliant)
  - Body text generator for searchable content
  - JSON manifest serializer (RSMF 2.0 spec)
  - ZIP archive builder with path traversal security
  - Attachment collector with file validation
  - WriteConfig with version selection (1.0/2.0)
  - 225+ unit tests (95%+ coverage)
  - PR #28: https://github.com/agent-33/RSMFConvert/pull/28 (MERGED)
- **Phase 5 Validation Engine** (2026-01-14):
  - ValidationEngine orchestrator for comprehensive RSMF validation
  - SchemaValidator with embedded RSMF 1.0/2.0 JSON schemas
  - ReferenceValidator for participant/conversation/event integrity
  - AttachmentValidator for file existence and naming validation
  - TimestampValidator for ISO8601 format and ordering checks
  - ZipStructureValidator for ZIP/manifest validation
  - ReportGenerator with text/JSON/HTML output formats
  - ValidationConfig with STRICT/STANDARD/LENIENT levels
  - 40+ error codes (RSMF-EXXX format) with remediation hints
  - 171 unit tests (95%+ coverage)
  - Added jsonschema ^4.20.0 dependency
  - PR #29: https://github.com/agent-33/RSMFConvert/pull/29 (MERGED)
- **Phase 6 CLI Foundation** (2026-01-14):
  - Enhanced CLI with 4 working commands
  - `convert` command with parser/writer integration
  - `validate` command using ValidationEngine
  - `info` command for RSMF file metadata display
  - `formats` command to list supported formats
  - Global options: --verbose, --quiet, --debug, --version
  - Exit codes 0-7 for scripting integration
  - Error handling with user-friendly messages
  - 30 unit tests for CLI commands
  - PR #30: https://github.com/agent-33/RSMFConvert/pull/30 (MERGED)
- **Phase 9 WhatsApp Parser** (2026-01-14, COMPLETE):
  - WhatsApp TXT export parser implementation
  - Multiple date format support (US, EU, iOS brackets)
  - Chinese locale support (上午/下午, YYYY/M/D, 年月日)
  - System message detection (encryption, join/leave, calls)
  - Media reference handling
  - Multi-line message support
  - Participant and conversation extraction
  - `--source-timezone` CLI option for forensic accuracy
  - Timezone conversion from source to UTC
  - 101 unit tests for WhatsApp parser
  - 41 CLI tests (including timezone parsing)
  - PR #31: https://github.com/agent-33/RSMFConvert/pull/31 (MERGED)
- **Phase 9A Sprint 1 - i18n Infrastructure** (2026-01-14, COMPLETE):
  - New `src/rsmfconverter/i18n/` module
  - ForensicTimestamp model with full audit trail for eDiscovery
  - Timezone utilities using zoneinfo (400+ IANA zones, DST-aware)
  - LocaleConfig with 25 regional presets
  - CLI options: `--source-locale`, `--forensic`
  - ParserConfig extensions: `enable_forensic_timestamps`, `source_locale`
  - 125 unit tests for i18n module
  - PR #32: https://github.com/agent-33/RSMFConvert/pull/32 (MERGED)
- **Phase 9A Sprint 2 - Pattern Libraries** (2026-01-14, COMPLETE):
  - Pattern libraries for 20+ languages in `src/rsmfconverter/i18n/patterns/`
  - AM/PM indicators (上午/下午, 午前/午後, 오전/오후, etc.)
  - Date/time format patterns (50+ patterns)
  - System message patterns per platform
  - Media omitted patterns
  - Join/leave event patterns
  - 461 pattern tests
  - PR #33: https://github.com/agent-33/RSMFConvert/pull/33 (MERGED)
  - PR #34: https://github.com/agent-33/RSMFConvert/pull/34 (MERGED) - Integration
- **Phase 9A Sprint 3 - Calendar/Numeral/Detection** (2026-01-14, COMPLETE):
  - **Calendar Systems** (`src/rsmfconverter/i18n/calendars/`):
    - Buddhist calendar (year offset +543)
    - Persian/Jalali calendar (33-year leap cycle)
    - Hebrew calendar (lunisolar with molad/dechiyot rules)
  - **Numeral Systems** (`src/rsmfconverter/i18n/numerals/`):
    - Western Arabic, Arabic-Indic, Persian, Thai, Devanagari, Bengali
    - Bidirectional conversion with O(n) translation tables
  - **Locale Auto-Detection** (`src/rsmfconverter/i18n/detection/`):
    - Signal-based heuristics with confidence scoring
    - Date format, character set, system message analysis
  - 184 new tests
  - PR #37: https://github.com/agent-33/RSMFConvert/pull/37 (MERGED)
- **ForensicTimestamp Integration** (2026-01-14, COMPLETE):
  - ForensicTimestamp wired into WhatsApp parser
  - Exact original timestamp extraction from source lines
  - IANA timezone identifier support
  - Forensic custom fields on events (original_string, format, confidence, etc.)
  - 17 new forensic tests
  - PR #36: https://github.com/agent-33/RSMFConvert/pull/36 (MERGED)
- **jsonschema Fix** (2026-01-14, COMPLETE):
  - Fixed UnboundLocalError in schema validation
  - All 171 validation tests now pass
  - PR #35: https://github.com/agent-33/RSMFConvert/pull/35 (MERGED)
- **Phase 10 Slack Parser** (2026-01-15, COMPLETE):
  - Slack JSON export parser (`src/rsmfconverter/parsers/slack.py`)
  - users.json, channels.json, groups.json, dms.json, mpims.json parsing
  - Daily message JSON files (YYYY-MM-DD.json) processing
  - Thread support with parent/reply linking
  - Reaction and attachment handling
  - Bot message support
  - Channel, DM, and MPIM conversation types
  - PR #38: https://github.com/agent-33/RSMFConvert/pull/38 (MERGED)
  - PR #39: https://github.com/agent-33/RSMFConvert/pull/39 (MERGED) - i18n Integration
- **Post-Phase 10 PRs** (2026-01-15, COMPLETE):
  - PR #40: Slack CLI integration tests (36 tests)
  - PR #41: Slack parser user guide documentation
  - PR #42: Korean iOS dot-separated date format support
  - PR #43: Performance test robustness (statistical methods)
  - PR #44: i18n test fixtures (Thai, Persian, Arabic, Hindi)
  - Centralized `_normalize_ampm()` helper for AM/PM conversion
  - All review comments addressed
- **Phase 11 Microsoft Teams Parser** (2026-01-15, COMPLETE):
  - Teams HTML export parser (`src/rsmfconverter/parsers/teams.py`, 1096 lines)
  - Two HTML formats supported: div-based and table-based
  - ZIP archive handling for multi-file exports
  - System message detection (join/leave events)
  - Attachment extraction with hash-based unique IDs
  - Multiple timestamp formats (US, EU, ISO)
  - Epoch sentinel for failed timestamp parsing (forensic accuracy)
  - Channel, Direct Message, and Meeting chat support
  - 55 unit tests + 14 CLI integration tests
  - PR #45: https://github.com/agent-33/RSMFConvert/pull/45 (MERGED)
- **Backlog Regression Tests Session** (2026-01-15, COMPLETE):
  - Extracted and prioritized follow-ups from session documentation
  - Teams parser regression tests (epoch sentinel, attachment IDs, participant refs)
  - Slack parser edge case tests (orphan threads, missing data, timestamp edge cases)
  - i18n infrastructure verification tests (numeral/calendar systems)
  - **Teams i18n Integration**: Wired numeral and calendar systems into Teams parser
    - Thai/Arabic-Indic/Persian/Devanagari numeral normalization
    - Buddhist/Persian/Hebrew calendar detection and conversion
  - 96 new tests added (2729 -> 2825)
  - Session log: `docs/session-logs/2026-01-15_backlog-regression-tests.md`

### Documentation Structure
```
docs/
├── INDEX.md                    # Master index - START HERE
├── CLAUDE.md                   # Project context (this file)
├── research/                   # Background research
│   ├── 01-RSMF-SPECIFICATION.md
│   ├── 02-COMPETITOR-ANALYSIS.md
│   ├── 03-INPUT-FORMATS.md
│   ├── 04-EDISCOVERY-CHALLENGES.md
│   └── 05-FEATURE-COMPARISON-MATRIX.md
├── roadmap/
│   └── 00-MASTER-ROADMAP.md    # Architecture & release plan
├── phases/                     # 40 detailed phase documents
│   └── PHASE-01 through PHASE-40
├── api/                        # API documentation
│   └── PHASE-01-API.md         # Phase 1 module documentation
├── agent-tasks/                # AI agent orchestration
│   ├── AGENT-IMPLEMENTATION-GUIDE.md
│   └── QUICK-START-TASKS.md
└── claude-session-logs/        # Session logs for continuity
```

## How to Run/Build/Test

```bash
# Install dependencies
poetry install

# Run all tests (2825 tests)
poetry run pytest tests/ -v

# Run specific test modules
poetry run pytest tests/unit/i18n/calendars/ -v    # Calendar tests
poetry run pytest tests/unit/i18n/numerals/ -v     # Numeral tests
poetry run pytest tests/unit/i18n/detection/ -v    # Detection tests
poetry run pytest tests/unit/parsers/test_whatsapp.py -v  # WhatsApp: 118 tests
poetry run pytest tests/unit/cli/test_main.py -v   # CLI tests

# Type checking
poetry run mypy src/rsmfconverter/

# Linting
poetry run ruff check src/

# CLI commands
poetry run rsmfconverter --help
poetry run rsmfconverter formats
poetry run rsmfconverter validate <file.eml>
poetry run rsmfconverter info <file.eml>

# WhatsApp conversion with timezone and locale
poetry run rsmfconverter convert chat.txt -o output.eml --source-timezone "Asia/Shanghai" --source-locale zh-CN

# Forensic timestamp mode (captures audit trail)
poetry run rsmfconverter convert chat.txt -o output.eml --forensic
```

## Current Folder Structure

```
src/rsmfconverter/
├── __init__.py              # Package init with version
├── cli/                     # CLI commands (Phase 6)
│   ├── __init__.py
│   └── main.py              # Typer app with convert/validate/info/formats
├── core/                    # Core utilities (Phase 1)
│   ├── exceptions.py        # Custom exception hierarchy
│   ├── types.py             # Type definitions
│   └── config.py            # Configuration management
├── logging/                 # Logging setup (Phase 1)
│   └── logger.py
├── models/                  # Data models (Phase 2)
│   ├── participant.py
│   ├── conversation.py
│   ├── event.py
│   ├── attachment.py
│   ├── document.py
│   └── factories.py
├── i18n/                    # Internationalization (Phase 9A)
│   ├── __init__.py          # Public API exports
│   ├── forensic.py          # ForensicTimestamp model
│   ├── timezone.py          # Timezone utilities (IANA, DST)
│   ├── locale.py            # LocaleConfig with 25 presets
│   ├── patterns/            # Pattern libraries (Sprint 2)
│   │   ├── __init__.py
│   │   ├── ampm.py          # AM/PM indicators (20+ languages)
│   │   ├── datetime.py      # Date/time format patterns
│   │   ├── system_messages.py
│   │   ├── media.py
│   │   └── participants.py
│   ├── calendars/           # Calendar systems (Sprint 3)
│   │   ├── __init__.py      # Unified API
│   │   ├── buddhist.py      # Buddhist calendar
│   │   ├── persian.py       # Persian/Jalali calendar
│   │   └── hebrew.py        # Hebrew calendar
│   ├── numerals/            # Numeral systems (Sprint 3)
│   │   ├── __init__.py
│   │   └── converters.py    # 6 numeral systems
│   └── detection/           # Locale detection (Sprint 3)
│       ├── __init__.py
│       └── locale_detector.py
├── parsers/                 # Parser framework (Phase 3) + Parsers (Phase 9+)
│   ├── base.py              # Abstract BaseParser
│   ├── registry.py          # ParserRegistry
│   ├── source.py            # InputSource classes
│   ├── detection.py         # Format detection
│   ├── context.py           # ParserContext
│   ├── builders.py          # EventBuilder
│   ├── timestamp.py         # Timestamp parsing
│   ├── config.py            # ParserConfig (timezone, locale, forensic)
│   ├── whatsapp.py          # WhatsApp TXT parser (Phase 9) + ForensicTimestamp
│   ├── slack.py             # Slack JSON parser (Phase 10)
│   └── teams.py             # Microsoft Teams HTML parser (Phase 11)
├── writers/                 # RSMF output (Phase 4)
│   ├── base.py              # RSMFWriter
│   ├── eml.py               # EML generation
│   ├── manifest.py          # JSON manifest
│   ├── zip.py               # ZIP building
│   ├── body.py              # Body text
│   └── config.py            # WriteConfig
└── validation/              # Validation engine (Phase 5)
    ├── engine.py            # ValidationEngine
    ├── schema.py            # SchemaValidator (fixed)
    ├── references.py        # ReferenceValidator
    ├── attachments.py       # AttachmentValidator
    ├── timestamps.py        # TimestampValidator
    ├── reports.py           # ReportGenerator
    ├── config.py            # ValidationConfig
    └── results.py           # ValidationResult, ErrorCodes
```

## AI Agent Orchestration Instructions

### How to Use This Project with AI Agents

1. **Parser Implementation**: Ready to implement parsers (Phase 12+)
   - Read `docs/phases/PHASE-12-IMESSAGE-PARSER.md` for iMessage
   - Each parser is independent
   - i18n infrastructure ready for use

2. **Parallel Work**: Multiple agents can work on independent phases
   - Parser phases (10-20) can run in parallel
   - Use `docs/agent-tasks/QUICK-START-TASKS.md` for ready tasks

3. **Dependencies**: Core infrastructure complete
   ```
   Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 ✓
   (Foundation → Models → Parsers → Writers → Validation → CLI)

   Phase 9 (WhatsApp) + Phase 9A (i18n Sprints 1-3) ✓
   Phase 10 (Slack) ✓
   Phase 11 (Teams) ✓

   Now ready for: Phase 12-20 (More Parsers) in parallel
   ```

4. **Task Assignment**: Each phase document contains:
   - Feature list with priorities
   - Acceptance criteria
   - Technical notes
   - Code examples

### Agent Types for This Project

| Agent Type | Use For |
|------------|---------|
| `implementer` | Writing new code, implementing features |
| `architect` | Design decisions, API design |
| `tester` | Writing tests, validation |
| `debugger` | Fixing bugs, investigating issues |
| `documentation` | Writing docs, comments |
| `reviewer` | Code review, security analysis |
| `researcher` | Understanding codebase, finding patterns |

### Running Agents in Parallel

When implementing multiple independent features:
```
Launch implementer agents for:
- Phase 12: iMessage Parser
- Phase 13: Discord Parser
- Phase 14: Telegram Parser
(These can run simultaneously - core infrastructure is complete)
```

---

## CRITICAL: Agent Orchestration Lessons Learned

**Last Updated**: 2026-01-14

### Background Agent Limitations (IMPORTANT!)

During Phase 1 implementation, we discovered critical issues with background agents:

#### What Happened
- Launched 13 `implementer` agents in parallel via `Task` tool with `run_in_background: true`
- All agents reported "completed" status
- **NO FILES WERE ACTUALLY CREATED** by the background agents
- Agent output files were empty

#### Root Cause Analysis
Background agents appear to have limitations with file system writes. The agents may:
1. Run in a sandboxed environment with restricted write access
2. Lose context or state when running in background mode
3. Not persist changes made during background execution

#### RECOMMENDED APPROACH FOR FUTURE SESSIONS

**DO NOT use background agents for file creation tasks.**

Instead, use one of these approaches:

1. **Direct Implementation (Recommended for file creation)**:
   - Use `Write`, `Edit`, and `Bash` tools directly from the main session
   - Most reliable for creating project structure and code files

2. **Foreground Agents (If parallelization is needed)**:
   - Use `Task` tool WITHOUT `run_in_background: true`
   - Launch sequentially or in small batches
   - Wait for each agent to complete before proceeding

3. **Background Agents (Only for read-only tasks)**:
   - Safe for: code exploration, research, analysis
   - Safe for: reading files, searching patterns
   - NOT safe for: writing files, creating directories

### Branch Tangling Warning (2026-01-14)
When running multiple background agents that modify related code:
- Agents may accidentally merge commits from other branches
- **Recommendation**: Merge PRs in order of least dependencies first
- Verify branch history before merging

## Key Technical Decisions

### Technology Stack
- **Language**: Python 3.11+
- **CLI**: Typer
- **Validation**: jsonschema
- **Testing**: pytest
- **Linting**: ruff
- **Settings**: Pydantic + pydantic-settings
- **Date Parsing**: python-dateutil

### Code Style and Conventions

#### Docstrings
- All public modules, classes, and functions must have docstrings
- Follow Google-style docstring format
- Include Args, Returns, Raises, and Example sections where applicable
- Type hints in function signatures, descriptions in docstrings

#### Type Annotations
- All public APIs fully type-annotated
- Use `from __future__ import annotations` for forward references
- Use `Path | str` union for path parameters (accept both)
- Use `| None` instead of `Optional[]` (Python 3.10+ style)

#### Exception Handling
- All custom exceptions inherit from `RSMFConverterError`
- Include contextual information (file paths, line numbers, field names)
- Use `cause` parameter to chain exceptions

#### Logging
- Use `get_logger(name)` for module-specific loggers
- Structured logging with JSON formatter for production
- Include extra fields for context (message_id, file_path, etc.)

### RSMF Format Summary
- EML wrapper (RFC 5322)
- ZIP container (rsmf.zip)
- JSON manifest (rsmf_manifest.json)
- Version 2.0.0 current spec

### Priority Input Formats
1. WhatsApp TXT exports ✓ (Phase 9)
2. Slack JSON exports ✓ (Phase 10)
3. Microsoft Teams HTML ✓ (Phase 11)
4. iMessage SQLite (Phase 12 - Next)
5. Discord JSON (Phase 13)
6. Telegram JSON (Phase 14)
7. Generic CSV/JSON

## Next Steps

### Phase 12 - iMessage Parser (RECOMMENDED NEXT)
1. Read `docs/phases/PHASE-12-IMESSAGE-PARSER.md` for requirements
2. Implement iMessage SQLite database parser:
   - SQLite database reading (chat.db)
   - Message table extraction
   - Handle table extraction
   - Attachment resolution from MediaDomain
   - Contact/participant mapping
   - Group chat support
   - Reaction (tapback) handling

### Alternative: Additional Parsers
1. Discord JSON Parser (Phase 13)
2. Telegram Parser (Phase 14)
3. Facebook Messenger Parser (Phase 15)
4. Signal Parser (Phase 16)

### Integration Improvements
1. Wire calendar systems into Slack/Teams parsers for non-Gregorian dates
2. Wire numeral systems into Slack/Teams parsers for non-Western numerals
3. Implement auto-locale detection for all parsers
4. Add i18n timestamp support to Teams parser

### Known Issues
- None currently blocking

## Reference Repositories

Located in `reference_repos/`:
- `relativity-rsmf-gen-sample/` - Official RSMF generator sample (C#)
- `rsmf-validator-samples/` - Official RSMF validator with schema

## Commands to Resume Work

```bash
# Check project status
python -m pytest tests/ -q --tb=no              # 2729 pass

# Run parser tests
python -m pytest tests/unit/parsers/test_whatsapp*.py -v  # WhatsApp tests
python -m pytest tests/unit/parsers/test_slack*.py -v     # Slack tests
python -m pytest tests/unit/parsers/test_teams*.py -v     # Teams tests
python -m pytest tests/integration/cli/ -v                 # CLI integration tests

# Run i18n tests
python -m pytest tests/unit/i18n/ -v            # i18n module tests

# Test WhatsApp conversion with timezone and locale
python -m rsmfconverter convert chat.txt -o output.eml --source-timezone "Asia/Shanghai" --source-locale zh-CN

# Test Slack conversion
python -m rsmfconverter convert slack_export.zip -o output.eml -f slack

# Test Teams conversion
python -m rsmfconverter convert teams_export.html -o output.eml -f teams
python -m rsmfconverter convert teams_export.zip -o output.eml -f teams

# Test forensic timestamp mode
python -m rsmfconverter convert chat.txt -o output.eml --forensic
```

## Project Goals

1. **Open Source**: Free, community-driven alternative to expensive tools
2. **Comprehensive**: Support 25+ input formats
3. **Enterprise-Ready**: Validation, performance, security
4. **AI-Powered**: Intelligent processing features (Phase 31+)
5. **Extensible**: Plugin system for custom formats

---

## Session Logging Rules

**IMPORTANT**: All Claude sessions working on this project must follow these logging rules.

### Location
All session logs are stored in: `docs/claude-session-logs/`

### Naming Convention
```
SESSION-YYYY-MM-DD-DESCRIPTION.md
```
Examples:
- `SESSION-2026-01-13-INITIAL-PLANNING.md`
- `SESSION-2026-01-14-PHASE1-IMPLEMENTATION.md`
- `SESSION-2026-01-15-BUGFIX-PARSER.md`

### Required Content
Each session log must include:

1. **Header**
   - Date
   - Session Type (Planning, Implementation, Debugging, etc.)
   - Model used

2. **Session Objectives**
   - What was the user's goal for this session?

3. **Work Completed**
   - List all files created/modified
   - Summarize key accomplishments
   - Note any technical decisions made

4. **Issues Encountered**
   - Any errors or blockers
   - How they were resolved

5. **Next Steps**
   - What should the next session focus on?
   - Any unfinished tasks

6. **Notes for Future Sessions**
   - Important context to preserve
   - Warnings or gotchas discovered

### When to Create Logs
- At the END of every significant session
- Before context window runs out
- When switching to a new task area
- When the user requests session closure

---

*Last Updated: 2026-01-15*
*Status: Phase 11 COMPLETE + Backlog Regression Tests + Teams i18n (2825 tests passing)*
*Next: Phase 12 (iMessage SQLite Parser)*
*Session Log: docs/session-logs/2026-01-15_backlog-regression-tests.md*
*PRs Merged: #26-#45 (20 total)*
