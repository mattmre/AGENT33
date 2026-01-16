# Phase 17: Magnet Axiom Parser

## Overview
- **Phase**: 17 of 40
- **Category**: Input Parsers (Forensic)
- **Release Target**: v0.7
- **Estimated Sprints**: 2

## Objectives
Implement parser for Magnet Axiom XML export format used in forensic investigations.

---

## Features (12 items)

### 17.1 Axiom Export Detection
**Priority**: P0 | **Complexity**: Medium
- Detect Axiom XML structure
- Identify artifact types
- Handle export versions
- Detect case structure

### 17.2 XML Artifact Parser
**Priority**: P0 | **Complexity**: High
- Parse artifact elements
- Handle fragment structure
- Extract field mappings
- Navigate case hierarchy

### 17.3 Chat Artifact Parsing
**Priority**: P0 | **Complexity**: High
- Parse chat artifacts
- Handle various chat types
- Extract message content
- Build conversations

### 17.4 Field Mapping
**Priority**: P0 | **Complexity**: Medium
- Map Axiom fields to RSMF
- Handle field variations
- Support custom mappings
- Handle missing fields

### 17.5 Contact Resolution
**Priority**: P0 | **Complexity**: Medium
- Extract contact artifacts
- Build participant map
- Handle phone/email
- Resolve display names

### 17.6 Media Artifact Handling
**Priority**: P0 | **Complexity**: Medium
- Parse media artifacts
- Link to messages
- Extract file paths
- Handle embedded content

### 17.7 Multi-Section Support
**Priority**: P1 | **Complexity**: Medium
- Handle multiple sections
- Merge related data
- Handle different schemas
- Track source sections

### 17.8 Timestamp Extraction
**Priority**: P0 | **Complexity**: Medium
- Parse timestamp fields
- Handle various formats
- Convert to ISO 8601
- Handle timezone

### 17.9 Deleted Item Handling
**Priority**: P1 | **Complexity**: Medium
- Detect deleted status
- Mark in RSMF
- Preserve recovery info
- Include deletion time

### 17.10 Case Metadata
**Priority**: P1 | **Complexity**: Low
- Extract case info
- Include examiner data
- Add device info
- Include in RSMF

### 17.11 Axiom Parser Configuration
**Priority**: P1 | **Complexity**: Low
- Artifact type filtering
- Date range filtering
- Custom field mapping file
- Media handling options

### 17.12 Axiom Parser Tests
**Priority**: P0 | **Complexity**: Medium
- Test XML parsing
- Test field mapping
- Test edge cases
- Sample data fixtures

---

## Acceptance Criteria

- [ ] Parses Axiom XML exports
- [ ] Maps fields correctly to RSMF
- [ ] Handles multi-section exports
- [ ] Handles media artifacts
- [ ] Produces valid RSMF output
- [ ] 90%+ test coverage

---

## Technical Notes

### Axiom XML Structure
```xml
<artifacts>
  <artifact type="Chat Message">
    <fragment>
      <field name="From">+15551234567</field>
      <field name="To">+15559876543</field>
      <field name="Body">Message text</field>
      <field name="Timestamp">2024-01-15 09:30:00</field>
      <field name="Application">WhatsApp</field>
    </fragment>
  </artifact>
</artifacts>
```

### Field Mapping Table
| Axiom Field | RSMF Field |
|-------------|------------|
| From | event.participant |
| To | conversation.participants |
| Body | event.body |
| Timestamp | event.timestamp |
| Application | conversation.platform |
