# Phase 5: Validation Engine

## Overview
- **Phase**: 5 of 40
- **Category**: Core Infrastructure
- **Release Target**: v0.2
- **Estimated Sprints**: 2

## Objectives
Build a comprehensive validation engine that ensures RSMF files conform to the specification and helps identify issues in source data.

---

## Features (15 items)

### 5.1 Validation Framework
**Priority**: P0 | **Complexity**: High
- Create Validator base class
- Define validation interface
- Support validation levels
- Implement result aggregation

### 5.2 JSON Schema Validation
**Priority**: P0 | **Complexity**: Medium
- Implement JSON Schema validator
- Support RSMF 1.0 schema
- Support RSMF 2.0 schema
- Report schema errors

### 5.3 Reference Integrity Validation
**Priority**: P0 | **Complexity**: Medium
- Validate participant references
- Validate conversation references
- Validate parent event references
- Report orphan references

### 5.4 Attachment Validation
**Priority**: P0 | **Complexity**: Medium
- Check attachment file existence
- Validate file names
- Check file sizes
- Report missing files

### 5.5 Timestamp Validation
**Priority**: P1 | **Complexity**: Medium
- Validate ISO8601 format
- Check timestamp ordering
- Detect future timestamps
- Warn on suspicious gaps

### 5.6 EML Structure Validation
**Priority**: P1 | **Complexity**: Medium
- Validate RFC 5322 compliance
- Check required headers
- Validate MIME structure
- Check encoding

### 5.7 ZIP Structure Validation
**Priority**: P0 | **Complexity**: Low
- Validate ZIP integrity
- Check for rsmf_manifest.json
- Validate file structure
- Check for extra files

### 5.8 Validation Result Model
**Priority**: P0 | **Complexity**: Medium
- Create ValidationResult class
- Support errors vs warnings
- Include error locations
- Support severity levels

### 5.9 Error Categorization
**Priority**: P1 | **Complexity**: Low
- Define error categories
- Create error codes
- Include remediation hints
- Support filtering by category

### 5.10 Batch Validation
**Priority**: P1 | **Complexity**: Medium
- Support multiple file validation
- Aggregate results
- Generate summary report
- Support parallel validation

### 5.11 Validation Report Generation
**Priority**: P1 | **Complexity**: Medium
- Generate text reports
- Generate JSON reports
- Generate HTML reports
- Include statistics

### 5.12 Custom Validation Rules
**Priority**: P2 | **Complexity**: Medium
- Support custom validators
- Plugin architecture
- Rule configuration
- Enable/disable rules

### 5.13 Pre-Write Validation
**Priority**: P1 | **Complexity**: Medium
- Validate models before writing
- Catch issues early
- Provide actionable errors
- Support auto-fix options

### 5.14 CLI Validation Command
**Priority**: P1 | **Complexity**: Low
- Add validate command
- Support file/directory input
- Output format options
- Exit codes for CI

### 5.15 Validation Unit Tests
**Priority**: P0 | **Complexity**: Medium
- Test all validators
- Test edge cases
- Test error reporting
- Achieve 90%+ coverage

---

## Acceptance Criteria

- [ ] Validates against official RSMF schema
- [ ] Catches common RSMF errors
- [ ] Produces actionable error messages
- [ ] Supports batch validation
- [ ] Report generation works
- [ ] CLI command functional

---

## Dependencies
- Phase 1: Project Foundation
- Phase 2: Data Models
- Phase 4: RSMF Writer

## Blocks
- Phase 6: CLI Foundation
- All quality-related features

---

## Technical Notes

### Validation Levels
```python
class ValidationLevel(Enum):
    STRICT = "strict"      # All rules, errors on warnings
    STANDARD = "standard"  # All rules, separate warnings
    LENIENT = "lenient"    # Critical rules only
```

### Error Code Format
```
RSMF-E001: Missing required field 'version'
RSMF-E002: Invalid participant reference 'P999'
RSMF-W001: Timestamp appears to be in the future
```

### Schema Location
- Use embedded JSON schemas
- Support custom schema paths
- Auto-detect RSMF version

---

## Agent Implementation Notes

When implementing this phase:
1. Use jsonschema library for JSON validation
2. Provide helpful error messages
3. Support internationalization of messages
4. Consider performance for large files
5. Document all error codes
