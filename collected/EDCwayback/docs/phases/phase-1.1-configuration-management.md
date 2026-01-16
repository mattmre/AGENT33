# Phase 1.1: Configuration Management System
**Category**: Core Infrastructure & Architecture
**Priority**: Critical
**Dependencies**: None
**Status**: COMPLETE (100%)

---

## Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| 1.1.1 Config Schema | COMPLETE | `src/config/schema.py` |
| 1.1.2 Config File Loader | COMPLETE | `src/config/loader.py` |
| 1.1.3 Env Variable Mapping | COMPLETE | Legacy + new EDC_* format |
| 1.1.4 Config Validation | COMPLETE | Via Pydantic validators |
| 1.1.5 Config Inheritance | COMPLETE | Deep merge in loader |
| 1.1.6 Default Config Templates | COMPLETE | Via `edc config init` |
| 1.1.7 Config Encryption | COMPLETE | `src/config/encryption.py`, CLI commands |
| 1.1.8 Config Versioning | PARTIAL | Field exists, no migrations |
| 1.1.9 CLI Integration | COMPLETE | Subcommands added |
| 1.1.10 API Integration | COMPLETE | `/config` endpoint in `src/api.py` |
| 1.1.11 Unit Tests | COMPLETE | 42+ tests |
| 1.1.12 Documentation | COMPLETE | `docs/configuration.md` |

---

## Objective
Establish a robust, environment-aware configuration system to replace scattered environment variables and CLI defaults with a unified, typed, validatable configuration framework.

---

## Current State
- Environment variables: `EDC_CAPTURES_DIR`, `EDC_ARTIFACTS_DIR`, `EDC_LOGS_DIR`, `SPN_PROVIDER`, `SPN_DELAY_MIN`, `SPN_DELAY_MAX`, etc.
- CLI flags for overrides
- No config file support
- No validation beyond basic type conversion
- Sensitive values (API keys) stored in plain text env vars

---

## Target State
- Pydantic-based typed configuration models
- Support for YAML, TOML, and JSON config files
- Environment variable mapping with `EDC_` prefix
- Config inheritance: base config → environment overrides → CLI overrides
- Encrypted storage for sensitive values (API keys, credentials)
- Config versioning and migration support

---

## Features (12 total)

### Feature 1.1.1: Config Schema with Pydantic
**File**: `src/config/schema.py`
**Effort**: Medium

```python
# Target structure
from pydantic import BaseModel, Field
from typing import Literal, Optional
from pathlib import Path

class StorageConfig(BaseModel):
    captures_dir: Path = Field(default=Path("captures"))
    artifacts_dir: Path = Field(default=Path("artifacts"))
    logs_dir: Path = Field(default=Path("logs"))

class SPNConfig(BaseModel):
    provider: Literal["waybackpy", "savepagenow"] = "waybackpy"
    delay_min: int = Field(default=120, ge=0)
    delay_max: int = Field(default=240, ge=0)
    access_key: Optional[str] = None
    secret_key: Optional[str] = None

class CaptureConfig(BaseModel):
    default_direction: Literal["closest", "before", "after", "both"] = "closest"
    default_mode: Literal["fetch", "capture", "auto"] = "fetch"
    variance_threshold_days: int = Field(default=30, ge=0)
    threshold_hours: int = Field(default=24, ge=0)

class ForensicConfig(BaseModel):
    enable_chain_of_custody: bool = True
    enable_timestamps: bool = True
    hash_algorithms: list[str] = ["md5", "sha1", "sha256"]

class EDCConfig(BaseModel):
    storage: StorageConfig = StorageConfig()
    spn: SPNConfig = SPNConfig()
    capture: CaptureConfig = CaptureConfig()
    forensic: ForensicConfig = ForensicConfig()
    debug: bool = False
```

**Acceptance Criteria**:
- [ ] All existing env vars mapped to typed fields
- [ ] Sensible defaults for all settings
- [ ] Field validation with constraints
- [ ] JSON schema generation for IDE support

---

### Feature 1.1.2: Config File Loader
**File**: `src/config/loader.py`
**Effort**: Medium

```python
# Target API
from config.loader import load_config

config = load_config(
    config_file="edc.yaml",  # or edc.toml, edc.json
    env_prefix="EDC_"
)
```

**Acceptance Criteria**:
- [ ] YAML loading with PyYAML
- [ ] TOML loading with tomli
- [ ] JSON loading with stdlib
- [ ] Auto-detection based on file extension
- [ ] Error handling with line numbers for parse errors

---

### Feature 1.1.3: Environment Variable Mapping
**File**: `src/config/env.py`
**Effort**: Small

**Mapping Rules**:
- `EDC_STORAGE__CAPTURES_DIR` → `storage.captures_dir`
- `EDC_SPN__PROVIDER` → `spn.provider`
- Double underscore for nested fields

**Acceptance Criteria**:
- [ ] Automatic env var discovery
- [ ] Nested field support with `__` separator
- [ ] Type coercion (string → int, bool, etc.)

---

### Feature 1.1.4: Config Validation
**File**: `src/config/validation.py`
**Effort**: Small

**Acceptance Criteria**:
- [ ] Cross-field validation (e.g., delay_min < delay_max)
- [ ] Path existence validation (optional)
- [ ] Detailed error messages with field paths
- [ ] Validation error collection (not fail-fast)

---

### Feature 1.1.5: Config Inheritance
**File**: `src/config/inheritance.py`
**Effort**: Medium

**Priority Order**:
1. CLI arguments (highest)
2. Environment variables
3. Config file
4. Default values (lowest)

**Acceptance Criteria**:
- [ ] Deep merge for nested objects
- [ ] CLI override syntax: `--config.spn.provider=savepagenow`
- [ ] Explicit unset: `--config.spn.access_key=null`

---

### Feature 1.1.6: Default Config Templates
**Files**: `config/templates/`
**Effort**: Small

Templates:
- `development.yaml` - Local dev with debug enabled
- `production.yaml` - Production settings
- `forensic.yaml` - Full forensic mode enabled
- `minimal.yaml` - Bare minimum config

**Acceptance Criteria**:
- [ ] Template files created with comments
- [ ] `edc init` command to generate from template

---

### Feature 1.1.7: Config Encryption
**File**: `src/config/encryption.py`
**Effort**: Medium

**Approach**: Use `cryptography` library with Fernet symmetric encryption
- Key stored in `~/.edc/key` or env var `EDC_ENCRYPTION_KEY`
- Encrypted fields marked with `ENC[...]` wrapper

**Acceptance Criteria**:
- [ ] Key generation command: `edc config generate-key`
- [ ] Encrypt command: `edc config encrypt-value`
- [ ] Transparent decryption on load
- [ ] Re-encryption on save

---

### Feature 1.1.8: Config Versioning
**File**: `src/config/migration.py`
**Effort**: Medium

**Acceptance Criteria**:
- [ ] `config_version` field in schema
- [ ] Migration functions for version upgrades
- [ ] Automatic migration on load with backup
- [ ] Migration dry-run mode

---

### Feature 1.1.9: CLI Integration
**File**: `src/cli.py` (modify)
**Effort**: Medium

**Acceptance Criteria**:
- [ ] `--config` flag to specify config file
- [ ] Individual config overrides via CLI
- [ ] `edc config show` command to display effective config
- [ ] `edc config validate` command

---

### Feature 1.1.10: API Integration
**File**: `src/api.py` (modify)
**Effort**: Small

**Acceptance Criteria**:
- [ ] Config loaded at startup
- [ ] Config exposed via dependency injection
- [ ] `/config` endpoint (read-only, sensitive fields masked)

---

### Feature 1.1.11: Unit Tests
**File**: `tests/test_config.py`
**Effort**: Medium

**Test Cases**:
- [ ] Schema validation tests
- [ ] Loader tests for each format
- [ ] Env var mapping tests
- [ ] Inheritance priority tests
- [ ] Encryption/decryption tests
- [ ] Migration tests

---

### Feature 1.1.12: Documentation
**File**: `docs/configuration.md`
**Effort**: Small

**Sections**:
- Configuration file format
- Environment variables reference
- CLI overrides
- Encryption setup
- Migration guide
- Troubleshooting

---

## Dependencies to Add

```
# requirements.txt additions
pydantic>=2.0
pyyaml>=6.0
tomli>=2.0  # For Python < 3.11
cryptography>=41.0
```

---

## Verification

1. Create test config file in all formats
2. Verify env var overrides work
3. Test CLI overrides
4. Encrypt and decrypt a value
5. Run full test suite

---

## Rollout Plan

1. Implement schema first (1.1.1)
2. Add loader and env mapping (1.1.2, 1.1.3)
3. Wire into CLI and API (1.1.9, 1.1.10)
4. Add advanced features (1.1.4-1.1.8)
5. Tests and docs (1.1.11, 1.1.12)
