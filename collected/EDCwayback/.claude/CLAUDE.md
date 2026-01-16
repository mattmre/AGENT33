# EDCwayback Project Context

## Project Overview

**EDCwayback** is being transformed from a batch Wayback Machine archival tool into a best-in-class forensic web archive collection platform for e-discovery and legal production.

## Current Development Phase

**Phase 1.1: Configuration Management** - COMPLETE (100%)
**Next Phase**: Phase 1.2: Database Layer

### Phase 1.1 Deliverables (All Complete)
- Pydantic configuration schema (`src/config/schema.py`)
- Config file loader for YAML/JSON/TOML (`src/config/loader.py`)
- Environment variable mapping with backwards compatibility
- CLI integration with subcommands (`edc run`, `edc config show/validate/init/generate-key/encrypt-value`)
- Config templates (development, production, forensic, minimal)
- API integration (`/config` endpoint in `src/api.py`)
- Config encryption (`src/config/encryption.py`)
- Documentation (`docs/configuration.md`)
- 120+ unit tests

## Development Roadmap

### Wave 1: Foundation + Forensic Core (Current)
1. **Phase 1.1**: Configuration Management ← COMPLETE
2. **Phase 1.2**: Database Layer ← NEXT
3. **Phase 2.1**: Chain of Custody
4. **Phase 2.2**: Cryptographic Verification
5. **Phase 2.3**: Audit Logging

### Full Plan
- 45 phases across 15 categories
- 550+ atomic features
- See `docs/architecture/development-phases.md` for full roadmap

## Key Files

### Configuration System (Phase 1.1)
- `src/config/__init__.py` - Module entry point, exports
- `src/config/schema.py` - Pydantic models (EDCConfig, StorageConfig, etc.)
- `src/config/loader.py` - File/env loading, deep merge, auto-decryption
- `src/config/encryption.py` - Fernet encryption for sensitive values

### Core Application
- `src/cli.py` - Command-line interface with subcommands
- `src/api.py` - FastAPI REST endpoint with `/config` and `/capture`
- `src/artifacts.py` - HTML/PDF/PNG/WARC generation
- `src/mode.py` - fetch/capture/auto strategies

### Testing
- `tests/test_config.py` - Config schema and loader tests (42+ tests)
- `tests/test_encryption.py` - Encryption module tests (71 tests)
- `tests/test_api_config.py` - API /config endpoint tests (23 tests)
- `tests/conftest.py` - Pytest fixtures (playwright optional)

### Documentation
- `docs/configuration.md` - Configuration guide
- `docs/session-logs/` - Session logs
- `docs/phases/` - Detailed phase specifications
- `docs/architecture/` - High-level design documents

## CLI Usage

```bash
# Run capture jobs
edc run jobs.csv --direction closest --mode fetch

# With config file
edc --config edc.yaml run jobs.csv

# Config management
edc config show [--format yaml|json] [--show-secrets]
edc config validate
edc config init --template development|production|forensic|minimal

# Encryption
edc config generate-key [--output path] [--force]
edc config encrypt-value <value> [--key path]
```

## Config Priority Chain

1. CLI arguments (highest)
2. Environment variables (EDC_*, SPN_*, etc.)
3. Config file (--config or auto-discovered edc.yaml)
4. Default values (lowest)

## Testing

```bash
# Run config and encryption tests (no playwright required)
python -m pytest tests/test_config.py tests/test_encryption.py tests/test_api_config.py -v

# Full test suite (requires playwright browser installation)
python -m pytest tests/ -v
```

## Environment Setup

```bash
# Required
pip install pydantic pyyaml cryptography fastapi uvicorn

# For testing
pip install pytest pytest-cov

# For browser tests (optional)
pip install playwright
playwright install chromium
```

## Known Issues

1. **Windows key permissions**: Encryption key files use Unix chmod; Windows requires manual ACL setup
2. **Duplicated code**: `_mask_sensitive` exists in both `cli.py` and `api.py`
3. **Long function**: `cmd_run` in `cli.py` is 480+ lines (refactoring opportunity)
4. **Silent decryption**: If no encryption key, decryption silently skips (should log warning)

## Recent Session (2026-01-13)

Completed Phase 1.1 via agentic orchestration:
- Created encryption module with CLI commands
- Added /config API endpoint
- Fixed ENC_PATTERN regex bug (URL-safe base64)
- Fixed API legacy code (use config instead of os.getenv)
- Created 120+ tests
- Code review: 8.5/10

See `docs/session-logs/2026-01-13_session-003.md` for details.

## Next Steps

1. Begin Phase 1.2 (Database Layer) per `docs/phases/phase-1.2-database-layer.md`
2. Start with Feature 1.2.1: DatabaseConfig in schema.py
