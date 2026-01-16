# Phase 24: Deduplication Engine

## Overview
- **Phase**: 24 of 40
- **Category**: Output & Export
- **Release Target**: v1.1
- **Estimated Sprints**: 2

## Objectives
Implement message and conversation deduplication capabilities for handling data from multiple sources.

---

## Features (14 items)

### 24.1 Deduplication Framework
**Priority**: P0 | **Complexity**: High
- Create dedup engine
- Define matching rules
- Support multiple strategies
- Handle large datasets

### 24.2 Exact Match Detection
**Priority**: P0 | **Complexity**: Medium
- Hash-based matching
- Content comparison
- Timestamp matching
- Participant matching

### 24.3 Fuzzy Match Detection
**Priority**: P1 | **Complexity**: High
- Similarity algorithms
- Configurable thresholds
- Handle minor variations
- Time window matching

### 24.4 Cross-Source Deduplication
**Priority**: P0 | **Complexity**: High
- Match across sources
- Handle format differences
- Normalize for comparison
- Track source priority

### 24.5 Conversation-Level Dedup
**Priority**: P1 | **Complexity**: Medium
- Identify same conversation
- Merge conversation data
- Handle ID differences
- Preserve metadata

### 24.6 Message-Level Dedup
**Priority**: P0 | **Complexity**: Medium
- Identify duplicate messages
- Mark duplicates
- Keep best version
- Track duplicates

### 24.7 Attachment Deduplication
**Priority**: P1 | **Complexity**: Medium
- Hash attachment files
- Identify duplicates
- Keep single copy
- Update references

### 24.8 Dedup Configuration
**Priority**: P1 | **Complexity**: Medium
- Match criteria selection
- Threshold settings
- Source priority rules
- Output options

### 24.9 Dedup Report Generation
**Priority**: P1 | **Complexity**: Medium
- Duplicate inventory
- Match confidence scores
- Source distribution
- Statistics

### 24.10 Manual Review Mode
**Priority**: P2 | **Complexity**: Medium
- Flag for review
- Side-by-side compare
- Accept/reject actions
- Bulk actions

### 24.11 Merge Strategy Options
**Priority**: P1 | **Complexity**: Medium
- Keep first
- Keep last
- Keep most complete
- Merge fields

### 24.12 Dedup Index Storage
**Priority**: P1 | **Complexity**: Medium
- Persist dedup index
- Incremental updates
- Query interface
- Cleanup tools

### 24.13 Performance Optimization
**Priority**: P1 | **Complexity**: High
- Bloom filters
- Locality-sensitive hashing
- Batch processing
- Memory management

### 24.14 Deduplication Tests
**Priority**: P0 | **Complexity**: High
- Test all strategies
- Test cross-source
- Test performance
- Edge case coverage

---

## Acceptance Criteria

- [ ] Exact matching works accurately
- [ ] Fuzzy matching is configurable
- [ ] Cross-source dedup functional
- [ ] Reports are comprehensive
- [ ] Performance is acceptable
- [ ] 90%+ test coverage

---

## Technical Notes

### Matching Strategy Interface
```python
class MatchingStrategy(Protocol):
    def calculate_hash(self, event: Event) -> str: ...
    def is_match(self, event1: Event, event2: Event) -> tuple[bool, float]: ...
```

### Hash Calculation
```python
def content_hash(event: Event) -> str:
    """Generate normalized content hash."""
    normalized = normalize_text(event.body)
    timestamp = event.timestamp.strftime("%Y%m%d%H%M")
    return hashlib.sha256(f"{normalized}|{timestamp}".encode()).hexdigest()
```

### Fuzzy Matching Algorithms
- Levenshtein distance
- Jaccard similarity
- SimHash for near-duplicates
- Time-window correlation
