# Phase 4: RSMF Writer Core

## Overview
- **Phase**: 4 of 40
- **Category**: Core Infrastructure
- **Release Target**: v0.2
- **Estimated Sprints**: 3

## Objectives
Implement the core RSMF file generation capability, producing valid RSMF 1.0 and 2.0 output files.

---

## Features (20 items)

### 4.1 RSMF Writer Base Class
**Priority**: P0 | **Complexity**: High
- Create RSMFWriter class
- Define write interface
- Support version selection
- Implement output options

### 4.2 JSON Manifest Generator
**Priority**: P0 | **Complexity**: High
- Generate rsmf_manifest.json
- Serialize all model types
- Handle special characters
- Validate JSON output

### 4.3 Participant Serialization
**Priority**: P0 | **Complexity**: Medium
- Serialize participant objects
- Handle optional fields
- Include custom fields
- Validate participant IDs

### 4.4 Conversation Serialization
**Priority**: P0 | **Complexity**: Medium
- Serialize conversation objects
- Handle participant references
- Include platform info
- Handle conversation types

### 4.5 Event Serialization
**Priority**: P0 | **Complexity**: High
- Serialize all event types
- Handle message events
- Handle system events
- Preserve event ordering

### 4.6 Reaction Serialization
**Priority**: P1 | **Complexity**: Low
- Serialize reaction arrays
- Validate reaction values
- Include participant refs
- Handle emoji mapping

### 4.7 Attachment Serialization
**Priority**: P0 | **Complexity**: Medium
- Serialize attachment metadata
- Validate file references
- Handle size information
- Support inline flags

### 4.8 ZIP Archive Creation
**Priority**: P0 | **Complexity**: Medium
- Create rsmf.zip container
- Add manifest file
- Include attachments
- Maintain file structure

### 4.9 EML Wrapper Generation
**Priority**: P0 | **Complexity**: High
- Generate RFC 5322 compliant EML
- Add RSMF headers
- Attach ZIP file
- Handle encoding (7-bit)

### 4.10 Header Generation
**Priority**: P0 | **Complexity**: Medium
- Generate X-RSMF-Version
- Generate X-RSMF-Generator
- Calculate X-RSMF-BeginDate
- Calculate X-RSMF-EndDate
- Calculate X-RSMF-EventCount

### 4.11 From/To Header Generation
**Priority**: P1 | **Complexity**: Medium
- Generate From header (custodian)
- Generate To header (participants)
- Handle email formatting
- Handle display names

### 4.12 Body Text Generation
**Priority**: P1 | **Complexity**: Medium
- Generate searchable body text
- Include participant names
- Include message content
- Include reactions
- Optimize for search

### 4.13 RSMF 1.0 Compatibility
**Priority**: P1 | **Complexity**: Medium
- Support 1.0 schema subset
- Omit 2.0-only fields
- Handle version detection
- Validate output

### 4.14 RSMF 2.0 Full Support
**Priority**: P0 | **Complexity**: Medium
- Include read receipts
- Include direction
- Include history events
- Support event collection ID

### 4.15 Attachment File Handling
**Priority**: P0 | **Complexity**: Medium
- Copy attachment files
- Rename if necessary
- Handle missing files
- Log warnings

### 4.16 Avatar File Handling
**Priority**: P1 | **Complexity**: Low
- Copy avatar files
- Generate placeholders
- Handle missing avatars
- Support multiple formats

### 4.17 Output Path Management
**Priority**: P1 | **Complexity**: Low
- Support custom output paths
- Handle filename generation
- Prevent overwrites
- Create directories

### 4.18 Write Options Configuration
**Priority**: P1 | **Complexity**: Medium
- Configure version
- Configure body generation
- Configure attachment handling
- Configure validation level

### 4.19 Post-Write Validation
**Priority**: P0 | **Complexity**: Medium
- Validate generated output
- Check ZIP integrity
- Verify file references
- Report validation results

### 4.20 Writer Unit Tests
**Priority**: P0 | **Complexity**: High
- Test all serialization
- Test ZIP creation
- Test EML generation
- Test round-trip conversion
- Achieve 90%+ coverage

---

## Acceptance Criteria

- [ ] Generated RSMF files pass Relativity validator
- [ ] Both 1.0 and 2.0 versions supported
- [ ] All attachment files correctly included
- [ ] Headers properly formatted
- [ ] Body text is searchable
- [ ] 90%+ test coverage

---

## Dependencies
- Phase 1: Project Foundation
- Phase 2: Data Models
- Phase 3: Parser Framework

## Blocks
- Phase 5: Validation Engine
- Phase 21: Slicing Engine
- All output-related phases

---

## Technical Notes

### EML Structure
```
X-RSMF-Version: 2.0.0
X-RSMF-Generator: RSMFConverter v1.0
X-RSMF-BeginDate: 2024-01-01T00:00:00Z
X-RSMF-EndDate: 2024-01-31T23:59:59Z
X-RSMF-EventCount: 1000
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="..."

--boundary
Content-Type: text/plain

[Searchable body text]

--boundary
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="rsmf.zip"
Content-Transfer-Encoding: base64

[Base64 encoded ZIP]
--boundary--
```

### Libraries
- email.mime for EML generation
- zipfile for ZIP creation
- json for manifest

---

## Agent Implementation Notes

When implementing this phase:
1. Use MimeKit patterns from reference code
2. Ensure 7-bit encoding for EML
3. Validate output with Relativity validator
4. Handle Unicode in filenames carefully
5. Maintain strict RFC 5322 compliance
