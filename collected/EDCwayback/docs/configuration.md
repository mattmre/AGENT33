# EDCwayback Configuration Guide

EDCwayback uses a layered configuration system that supports multiple sources and formats. This guide covers all aspects of configuration management.

## Table of Contents

1. [Configuration Priority](#configuration-priority)
2. [Configuration File Formats](#configuration-file-formats)
3. [Configuration Sections](#configuration-sections)
4. [Environment Variables](#environment-variables)
5. [CLI Overrides](#cli-overrides)
6. [Configuration Templates](#configuration-templates)
7. [Encryption Setup](#encryption-setup)
8. [API Access](#api-access)
9. [Troubleshooting](#troubleshooting)

---

## Configuration Priority

Configuration values are loaded from multiple sources, with later sources overriding earlier ones:

1. **Default values** (lowest priority)
2. **Configuration file** (edc.yaml, edc.toml, or edc.json)
3. **Environment variables** (EDC_* prefix)
4. **CLI arguments** (highest priority)

This allows you to set defaults in a config file, override them per-environment with env vars, and further override per-invocation with CLI flags.

---

## Configuration File Formats

EDCwayback supports three configuration file formats:

### YAML (Recommended)

```yaml
# edc.yaml
storage:
  captures_dir: ./captures
  artifacts_dir: ./artifacts
  logs_dir: ./logs

spn:
  provider: waybackpy
  delay_min: 120
  delay_max: 240
  # access_key: your_access_key
  # secret_key: your_secret_key

capture:
  direction: closest
  mode: fetch
  threshold_hours: 12
  variance_threshold_days: 30
  default_timezone: UTC

config_version: 1
```

### TOML

```toml
# edc.toml
config_version = 1

[storage]
captures_dir = "./captures"
artifacts_dir = "./artifacts"
logs_dir = "./logs"

[spn]
provider = "waybackpy"
delay_min = 120
delay_max = 240

[capture]
direction = "closest"
mode = "fetch"
threshold_hours = 12
```

### JSON

```json
{
  "config_version": 1,
  "storage": {
    "captures_dir": "./captures",
    "artifacts_dir": "./artifacts"
  },
  "spn": {
    "provider": "waybackpy"
  }
}
```

### Auto-Discovery

EDCwayback automatically searches for configuration files in this order:

1. `./edc.yaml`, `./edc.yml`, `./edc.toml`, `./edc.json` (current directory)
2. `~/.config/edc/config.yaml` (user config directory)
3. `/etc/edc/config.yaml` (system config directory, Unix-like)

Use `--config` to specify an explicit path:

```bash
edc --config /path/to/custom.yaml run jobs.csv
```

---

## Configuration Sections

### Storage

Controls where files are saved.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `captures_dir` | Path | `captures` | Directory for archived HTML captures |
| `artifacts_dir` | Path | `artifacts` | Directory for generated artifacts (PDF, PNG, WARC) |
| `logs_dir` | Path | `logs` | Directory for run logs |

### SPN (Save Page Now)

Controls interaction with Internet Archive's Save Page Now service.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `provider` | String | `waybackpy` | Implementation: `waybackpy` or `savepagenow` |
| `delay_min` | Float | `120` | Minimum delay (seconds) before SPN jobs |
| `delay_max` | Float | `240` | Maximum delay (seconds) before SPN jobs |
| `access_key` | String | None | Internet Archive access key |
| `secret_key` | String | None | Internet Archive secret key |
| `authenticate` | Bool | None | Force authenticated (`true`) or anonymous (`false`) requests |

### Capture

Controls snapshot selection and capture behavior.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `direction` | String | `closest` | Selection direction: `closest`, `before`, `after`, `both` |
| `mode` | String | `fetch` | Operation mode: `fetch`, `capture`, `auto` |
| `threshold_hours` | Float | `12` | Hours threshold for auto mode before triggering new capture |
| `variance_threshold_days` | Float | `30` | Warn if snapshot deviates more than this many days |
| `default_timezone` | String | `UTC` | Default timezone for date-only 'when' values |

### Outlinks

Controls outlink discovery and crawling.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | Bool | `false` | Queue outlink captures for each URL |
| `scope` | String | `same-domain` | Scope: `any`, `same-host`, `same-domain` |
| `max_per_page` | Int | None | Limit outlinks per page (None = unlimited) |
| `depth` | Int | `1` | Recursion depth for outlink crawling |
| `allowlist` | String | None | Regex pattern outlinks must match |
| `blocklist` | String | None | Regex pattern outlinks must not match |

### Artifacts

Controls artifact generation.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `save_raw` | Bool | `false` | Save raw HTML artifacts |
| `save_pdf` | Bool | `false` | Save PDF screenshots |
| `save_png` | Bool | `false` | Save PNG screenshots |
| `save_warc` | Bool | `false` | Save WARC response files |
| `save_headers` | Bool | `false` | Persist HTTP headers |
| `raw_source` | String | `archived` | Source for raw HTML: `archived`, `live`, `both` |
| `pdf_source` | String | `archived` | Source for PDF: `archived`, `live`, `both` |
| `png_source` | String | `archived` | Source for PNG: `archived`, `live`, `both` |

### Forensic

Controls forensic integrity features.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enable_chain_of_custody` | Bool | `true` | Enable chain of custody tracking |
| `enable_timestamps` | Bool | `true` | Enable cryptographic timestamps (RFC 3161) |
| `hash_algorithms` | List | `["md5", "sha1", "sha256"]` | Hash algorithms for artifacts |
| `enable_signatures` | Bool | `false` | Enable digital signatures |
| `signing_key_path` | Path | None | Path to private key for signing |

### Logging

Controls logging behavior.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `level` | String | `INFO` | Console level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `debug` | Bool | `false` | Enable debug mode (sets level to DEBUG) |
| `file_max_bytes` | Int | `1000000` | Maximum size of log files |
| `file_backup_count` | Int | `5` | Number of backup log files |

---

## Environment Variables

Environment variables use the `EDC_` prefix with double underscores for nesting:

```bash
# Storage settings
export EDC_STORAGE__CAPTURES_DIR=/data/captures
export EDC_STORAGE__ARTIFACTS_DIR=/data/artifacts

# SPN settings
export EDC_SPN__PROVIDER=savepagenow
export EDC_SPN__DELAY_MIN=60

# Capture settings
export EDC_CAPTURE__DIRECTION=both
export EDC_CAPTURE__MODE=auto

# Debug mode
export EDC_LOGGING__DEBUG=true
```

### Legacy Variables

For backwards compatibility, these legacy variables are also supported:

| Legacy Variable | Maps To |
|-----------------|---------|
| `EDC_CAPTURES_DIR` | `storage.captures_dir` |
| `EDC_ARTIFACTS_DIR` | `storage.artifacts_dir` |
| `EDC_LOGS_DIR` | `storage.logs_dir` |
| `EDC_DEBUG` | `logging.debug` |
| `SPN_PROVIDER` | `spn.provider` |
| `SPN_DELAY_MIN` | `spn.delay_min` |
| `SPN_DELAY_MAX` | `spn.delay_max` |
| `SAVEPAGENOW_ACCESS_KEY` | `spn.access_key` |
| `SAVEPAGENOW_SECRET_KEY` | `spn.secret_key` |

---

## CLI Overrides

Many configuration values can be overridden via CLI flags:

```bash
# Override direction and mode
edc run jobs.csv --direction both --mode auto

# Override SPN settings
edc run jobs.csv --spn-provider savepagenow --spn-delay-min 60

# Override thresholds
edc run jobs.csv --threshold-hours 24 --variance-threshold-days 7

# Enable outlinks
edc run jobs.csv --outlinks --outlinks-scope same-domain --outlinks-depth 2

# Artifact options
edc run jobs.csv --save-warc --save-headers --raw-source both
```

---

## Configuration Templates

Generate a configuration file from a template:

```bash
# Development template (debug enabled, shorter delays)
edc config init --template development

# Production template (full artifacts, longer delays)
edc config init --template production

# Forensic template (all forensic features enabled)
edc config init --template forensic

# Minimal template (bare essentials)
edc config init --template minimal

# Specify output file
edc config init --template production --output /etc/edc/config.yaml

# Overwrite existing file
edc config init --template development --force
```

---

## Encryption Setup

Sensitive configuration values (API keys, secrets) can be encrypted in config files.

### Generate an Encryption Key

```bash
# Generate key at default location (~/.edc/key)
edc config generate-key

# Generate key at custom location
edc config generate-key --output /path/to/key

# Overwrite existing key
edc config generate-key --force
```

### Encrypt a Value

```bash
# Encrypt a value (outputs ENC[...] wrapped string)
edc config encrypt-value "my-secret-api-key"
# Output: ENC[gAAAAABk...]

# Use custom key file
edc config encrypt-value "my-secret" --key /path/to/key
```

### Use Encrypted Values in Config

```yaml
# edc.yaml
spn:
  provider: savepagenow
  access_key: ENC[gAAAAABk1234...]
  secret_key: ENC[gAAAAABk5678...]
```

Encrypted values are automatically decrypted when the config is loaded.

### Key Storage Options

1. **Default file**: `~/.edc/key` (recommended for single-user systems)
2. **Environment variable**: `EDC_ENCRYPTION_KEY` (recommended for CI/CD)
3. **Custom file**: Specify via `--key` flag

### Security Notes

- The key file is created with restricted permissions (owner-only)
- Never commit encryption keys to version control
- Use environment variables for keys in containerized deployments
- Rotate keys periodically for sensitive deployments

---

## API Access

The REST API exposes configuration at the `/config` endpoint:

```bash
# Get current configuration (sensitive values masked)
curl http://localhost:8000/config
```

Response:

```json
{
  "config": {
    "storage": {
      "captures_dir": "captures",
      "artifacts_dir": "artifacts",
      "logs_dir": "logs"
    },
    "spn": {
      "provider": "waybackpy",
      "access_key": "***MASKED***",
      "secret_key": "***MASKED***"
    }
  },
  "config_file": "edc.yaml",
  "version": 1
}
```

---

## Troubleshooting

### View Effective Configuration

```bash
# Show current config (YAML format)
edc config show

# Show as JSON
edc config show --format json

# Show with secrets visible (use with caution)
edc config show --show-secrets
```

### Validate Configuration

```bash
# Validate config file syntax and values
edc config validate
```

### Common Issues

**Config file not found**

EDCwayback searches standard locations automatically. Use `--config` to specify an explicit path.

**Environment variable not applying**

- Check the variable name matches the expected pattern: `EDC_SECTION__FIELD`
- Use double underscores (`__`) for nested fields
- Verify the variable is exported in your shell

**Encryption key not found**

```
Encryption error: No encryption key found...
```

Generate a key with `edc config generate-key` or set `EDC_ENCRYPTION_KEY`.

**Invalid config value**

Pydantic validation will show the field path and expected type:

```
1 validation error for EDCConfig
spn -> delay_min
  Input should be greater than or equal to 0 [type=greater_than_equal]
```

**Type coercion issues**

Environment variables are strings. EDCwayback automatically converts:
- `"true"`, `"yes"`, `"1"` → `True`
- `"false"`, `"no"`, `"0"` → `False`
- Numeric strings → `int` or `float`

---

## Migration

### From Environment-Only Configuration

If you're currently using only environment variables, create a config file to document your settings:

```bash
# Start with development template
edc config init --template development

# Edit the generated edc.yaml with your settings
# Then remove redundant environment variables
```

### Config Version Upgrades

The `config_version` field tracks schema versions. Future releases may include automatic migration for breaking changes.

---

## Examples

### Development Setup

```yaml
# edc.yaml
storage:
  captures_dir: ./dev_captures
  artifacts_dir: ./dev_artifacts

spn:
  provider: waybackpy
  delay_min: 30
  delay_max: 60

capture:
  direction: closest
  mode: fetch

logging:
  level: DEBUG
  debug: true

config_version: 1
```

### Production Setup

```yaml
# edc.yaml
storage:
  captures_dir: /var/lib/edcwayback/captures
  artifacts_dir: /var/lib/edcwayback/artifacts
  logs_dir: /var/log/edcwayback

spn:
  provider: savepagenow
  delay_min: 120
  delay_max: 240
  access_key: ENC[gAAAAABk...]
  secret_key: ENC[gAAAAABk...]

capture:
  direction: closest
  mode: fetch
  threshold_hours: 24

artifacts:
  save_raw: true
  save_pdf: true
  save_warc: true
  save_headers: true

forensic:
  enable_chain_of_custody: true
  enable_timestamps: true
  hash_algorithms:
    - sha256
    - sha512

logging:
  level: INFO

config_version: 1
```

### E-Discovery / Forensic Setup

```yaml
# edc.yaml
storage:
  captures_dir: ./evidence/captures
  artifacts_dir: ./evidence/artifacts
  logs_dir: ./evidence/logs

capture:
  direction: both
  variance_threshold_days: 7

artifacts:
  save_raw: true
  save_pdf: true
  save_png: true
  save_warc: true
  save_headers: true
  raw_source: both
  pdf_source: both
  png_source: both

forensic:
  enable_chain_of_custody: true
  enable_timestamps: true
  hash_algorithms:
    - md5
    - sha1
    - sha256
    - sha512
  enable_signatures: true
  signing_key_path: /path/to/signing_key.pem

outlinks:
  enabled: true
  scope: same-domain
  depth: 2

config_version: 1
```
