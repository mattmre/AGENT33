# Phase 18: Generic Format Parsers

## Overview
- **Phase**: 18 of 40
- **Category**: Input Parsers
- **Release Target**: v0.8
- **Estimated Sprints**: 2

## Objectives
Implement parsers for generic formats (CSV, JSON, XML) with configurable field mapping.

---

## Features (14 items)

### 18.1 CSV Parser Framework
**Priority**: P0 | **Complexity**: Medium
- Parse CSV files
- Handle various delimiters
- Support quoted fields
- Handle encoding issues

### 18.2 CSV Field Mapper
**Priority**: P0 | **Complexity**: Medium
- Configurable column mapping
- Header detection
- Index-based mapping
- Default values

### 18.3 Generic JSON Parser
**Priority**: P0 | **Complexity**: Medium
- Parse JSON files
- Handle arrays/objects
- Support nested paths
- Handle large files

### 18.4 JSON Path Mapper
**Priority**: P0 | **Complexity**: Medium
- JSONPath expressions
- Nested field access
- Array handling
- Transform functions

### 18.5 Generic XML Parser
**Priority**: P1 | **Complexity**: Medium
- Parse XML files
- XPath expressions
- Handle namespaces
- Streaming support

### 18.6 XML Element Mapper
**Priority**: P1 | **Complexity**: Medium
- XPath field mapping
- Attribute extraction
- Element content
- Default values

### 18.7 Mapping Configuration Format
**Priority**: P0 | **Complexity**: Medium
- YAML mapping files
- Field definitions
- Transform rules
- Validation rules

### 18.8 Built-in Transformations
**Priority**: P1 | **Complexity**: Medium
- Date parsing
- String manipulation
- Number formatting
- Conditional logic

### 18.9 Participant Auto-Detection
**Priority**: P1 | **Complexity**: High
- Detect sender fields
- Identify recipient fields
- Build participant list
- Handle variations

### 18.10 Conversation Grouping
**Priority**: P1 | **Complexity**: High
- Auto-group by thread ID
- Group by participants
- Time-window grouping
- Manual grouping

### 18.11 Sample Mapping Templates
**Priority**: P1 | **Complexity**: Low
- Common CSV formats
- Generic chat JSON
- Common XML schemas
- Custom template examples

### 18.12 Mapping Validation
**Priority**: P1 | **Complexity**: Medium
- Validate mapping config
- Check required fields
- Test against samples
- Report errors

### 18.13 Interactive Mapping Mode
**Priority**: P2 | **Complexity**: High
- Show sample data
- Suggest mappings
- Preview results
- Save configuration

### 18.14 Generic Parser Tests
**Priority**: P0 | **Complexity**: Medium
- Test CSV parsing
- Test JSON parsing
- Test XML parsing
- Test field mapping

---

## Acceptance Criteria

- [ ] Parses CSV with configurable mapping
- [ ] Parses JSON with JSONPath
- [ ] Parses XML with XPath
- [ ] Mapping configuration is flexible
- [ ] Produces valid RSMF output
- [ ] 90%+ test coverage

---

## Technical Notes

### Mapping Configuration Example
```yaml
format: csv
options:
  delimiter: ","
  encoding: utf-8
  skip_header: true

fields:
  participant:
    source: column:0
    transform: trim
  body:
    source: column:3
  timestamp:
    source: column:1
    transform: parse_date
    format: "%Y-%m-%d %H:%M:%S"

conversation:
  platform: "custom"
  group_by: column:2
```

### JSONPath Examples
```yaml
format: json
root: "$.messages[*]"

fields:
  participant:
    source: "$.sender.name"
  body:
    source: "$.content"
  timestamp:
    source: "$.created_at"
```
