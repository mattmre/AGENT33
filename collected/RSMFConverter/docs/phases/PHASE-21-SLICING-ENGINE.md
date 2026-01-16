# Phase 21: RSMF Slicing Engine

## Overview
- **Phase**: 21 of 40
- **Category**: Output & Export
- **Release Target**: v1.0
- **Estimated Sprints**: 2

## Objectives
Implement intelligent slicing capabilities to break large conversations into manageable RSMF files.

---

## Features (14 items)

### 21.1 Slicing Framework
**Priority**: P0 | **Complexity**: High
- Create Slicer base class
- Define slicing interface
- Support multiple strategies
- Handle dependencies

### 21.2 Time-Based Slicing
**Priority**: P0 | **Complexity**: Medium
- Slice by day
- Slice by week
- Slice by month
- Slice by custom duration

### 21.3 Event Count Slicing
**Priority**: P0 | **Complexity**: Medium
- Slice by message count
- Configurable limits
- Handle overflow
- Maintain thread context

### 21.4 File Size Slicing
**Priority**: P1 | **Complexity**: Medium
- Slice by file size
- Estimate attachment sizes
- Configurable limits
- Handle large attachments

### 21.5 Conversation-Based Slicing
**Priority**: P0 | **Complexity**: Medium
- One RSMF per conversation
- Handle multiple conversations
- Preserve conversation integrity
- Handle conversation metadata

### 21.6 Participant-Based Slicing
**Priority**: P1 | **Complexity**: Medium
- Slice by custodian
- Slice by participant set
- Handle overlapping
- Maintain context

### 21.7 Platform-Based Slicing
**Priority**: P1 | **Complexity**: Low
- Slice by platform
- Handle multi-platform sources
- Preserve platform metadata
- Organize output

### 21.8 Thread Context Preservation
**Priority**: P0 | **Complexity**: High
- Keep thread context
- Include parent messages
- Handle long threads
- Configurable context depth

### 21.9 Event Collection ID Management
**Priority**: P0 | **Complexity**: Medium
- Generate collection IDs
- Link related slices
- Support manual IDs
- Ensure uniqueness

### 21.10 Slice Naming Convention
**Priority**: P1 | **Complexity**: Low
- Configurable naming
- Include slice metadata
- Support templates
- Prevent collisions

### 21.11 Slice Manifest Generation
**Priority**: P1 | **Complexity**: Medium
- Generate slice inventory
- Include slice metadata
- Track relationships
- Export as CSV/JSON

### 21.12 Multi-Strategy Combination
**Priority**: P1 | **Complexity**: High
- Combine slicing strategies
- Priority-based resolution
- Handle conflicts
- Configurable behavior

### 21.13 Slice Preview Mode
**Priority**: P2 | **Complexity**: Medium
- Preview without writing
- Show slice breakdown
- Statistics display
- Estimate output

### 21.14 Slicing Engine Tests
**Priority**: P0 | **Complexity**: High
- Test all strategies
- Test combinations
- Test edge cases
- Performance tests

---

## Acceptance Criteria

- [ ] All slicing strategies functional
- [ ] Thread context preserved
- [ ] Event collection IDs managed
- [ ] Slice manifest generated
- [ ] Output is valid RSMF
- [ ] 90%+ test coverage

---

## Technical Notes

### Slicing Strategy Interface
```python
class SlicingStrategy(Protocol):
    def should_slice(self, document: RSMFDocument, event: Event) -> bool: ...
    def get_slice_name(self, index: int, metadata: dict) -> str: ...
```

### Output Structure
```
output/
├── conversation_001_2024-01.rsmf
├── conversation_001_2024-02.rsmf
├── conversation_002_2024-01.rsmf
└── slice_manifest.json
```

### Slice Manifest Format
```json
{
  "slices": [
    {
      "filename": "conversation_001_2024-01.rsmf",
      "event_collection_id": "conv_001_2024",
      "conversation_id": "001",
      "date_range": {"start": "...", "end": "..."},
      "event_count": 500
    }
  ]
}
```
