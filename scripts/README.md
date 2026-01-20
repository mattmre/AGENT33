# Scripts

Utility scripts for AGENT-33 orchestration maintenance and diagnostics.

## validate-orchestration.ps1

Validates the orchestration index and cross-references in core documentation.

### Usage

```powershell
# Text output (human-readable)
.\scripts\validate-orchestration.ps1

# JSON output (machine-readable)
.\scripts\validate-orchestration.ps1 -Json

# Custom repo root
.\scripts\validate-orchestration.ps1 -RepoRoot "C:\path\to\repo"
```

### What It Checks

1. **Index File Existence**: Verifies all files listed in `core/ORCHESTRATION_INDEX.md` exist
2. **Cross-Reference Validation**: Checks markdown links `[text](path.md)` in core docs resolve to existing files
3. **Orphaned Files**: Reports `.md` files in `core/` not listed in the orchestration index

### Exit Codes

- `0`: All validations pass (healthy)
- `1`: One or more issues found

### Output Fields (JSON)

| Field | Description |
|-------|-------------|
| `timestamp` | ISO 8601 timestamp of validation run |
| `orchestrationIndex` | Path to the index file checked |
| `totalFiles` | Count of files referenced in index |
| `existingFiles` | Count of files that exist |
| `missingFiles` | Array of missing file paths |
| `brokenCrossRefs` | Array of `{source, target}` broken links |
| `orphanedFiles` | Array of files not in index |
| `healthy` | Boolean overall health status |
