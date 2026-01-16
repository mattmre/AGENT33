# Phase 2: Data Models

## Overview
- **Phase**: 2 of 40
- **Category**: Core Infrastructure
- **Release Target**: v0.1
- **Estimated Sprints**: 2

## Objectives
Define the core data models that represent RSMF concepts internally, providing a consistent interface between parsers and writers.

---

## Features (18 items)

### 2.1 Base Model Framework
**Priority**: P0 | **Complexity**: Medium
- Create BaseModel class with common methods
- Implement serialization/deserialization
- Add validation hooks
- Support immutability options

### 2.2 Participant Model
**Priority**: P0 | **Complexity**: Medium
- Define Participant dataclass
- Include id, display, email fields
- Support avatar reference
- Support account_id field
- Implement custom fields support

### 2.3 Conversation Model
**Priority**: P0 | **Complexity**: Medium
- Define Conversation dataclass
- Include id, platform, type fields
- Support participant list
- Support custodian reference
- Implement custom fields support

### 2.4 Event Base Model
**Priority**: P0 | **Complexity**: Medium
- Create Event base class
- Define common event properties
- Support timestamp handling
- Support participant reference

### 2.5 Message Event Model
**Priority**: P0 | **Complexity**: Medium
- Create MessageEvent subclass
- Include body field
- Support threading (parent_id)
- Support direction enum

### 2.6 System Event Models
**Priority**: P1 | **Complexity**: Low
- Create JoinEvent model
- Create LeaveEvent model
- Create HistoryEvent model
- Create DisclaimerEvent model
- Create UnknownEvent model

### 2.7 Reaction Model
**Priority**: P0 | **Complexity**: Low
- Define Reaction dataclass
- Include value, count fields
- Support participant list
- Implement emoji mapping

### 2.8 Attachment Model
**Priority**: P0 | **Complexity**: Medium
- Define Attachment dataclass
- Include id, display, size fields
- Support file reference
- Track MIME type
- Support inline display flag

### 2.9 Edit Model
**Priority**: P1 | **Complexity**: Low
- Define Edit dataclass
- Include previous, new fields
- Support timestamp
- Support participant reference

### 2.10 Read Receipt Model
**Priority**: P1 | **Complexity**: Low
- Define ReadReceipt dataclass
- Support participant reference
- Include timestamp
- Support action enum (read/delivered)

### 2.11 Custom Field Model
**Priority**: P1 | **Complexity**: Low
- Define CustomField dataclass
- Support name/value pairs
- Type coercion support
- Validation rules

### 2.12 RSMF Document Model
**Priority**: P0 | **Complexity**: High
- Create RSMFDocument container class
- Hold participants, conversations, events
- Support version specification
- Include event collection ID
- Implement iteration methods

### 2.13 Model Validation
**Priority**: P0 | **Complexity**: High
- Implement reference validation
- Check participant ID consistency
- Validate conversation references
- Ensure timestamp ordering

### 2.14 Model Serialization
**Priority**: P1 | **Complexity**: Medium
- Implement to_dict() methods
- Implement from_dict() class methods
- Support JSON serialization
- Handle datetime serialization

### 2.15 Model Comparison
**Priority**: P2 | **Complexity**: Medium
- Implement __eq__ methods
- Implement __hash__ where appropriate
- Support model diffing
- Create comparison utilities

### 2.16 Model Factories
**Priority**: P1 | **Complexity**: Medium
- Create participant factory
- Create conversation factory
- Create event factories
- Support builder pattern

### 2.17 Enum Definitions
**Priority**: P0 | **Complexity**: Low
- Define EventType enum
- Define ConversationType enum
- Define Direction enum
- Define Importance enum
- Define ReadReceiptAction enum

### 2.18 Model Unit Tests
**Priority**: P0 | **Complexity**: Medium
- Test all model creation
- Test validation rules
- Test serialization
- Test edge cases
- Achieve 95%+ coverage

---

## Acceptance Criteria

- [ ] All RSMF 2.0 concepts are modeled
- [ ] Models can round-trip through JSON
- [ ] Validation catches invalid references
- [ ] Type hints are complete
- [ ] 95%+ test coverage on models
- [ ] Documentation complete for all models

---

## Dependencies
- Phase 1: Project Foundation

## Blocks
- Phase 3: Parser Framework
- Phase 4: RSMF Writer
- All parser phases

---

## Technical Notes

### Model Example
```python
@dataclass
class Participant:
    id: str
    display: str | None = None
    email: str | None = None
    avatar: str | None = None
    account_id: str | None = None
    custom: list[CustomField] = field(default_factory=list)

    def to_dict(self) -> dict:
        ...

    @classmethod
    def from_dict(cls, data: dict) -> "Participant":
        ...
```

### Validation Strategy
- Use Pydantic v2 for validation
- Custom validators for RSMF rules
- Lazy validation option for performance

---

## Agent Implementation Notes

When implementing this phase:
1. Use Python dataclasses or Pydantic
2. Implement __repr__ for debugging
3. Make models immutable where practical
4. Document all fields with docstrings
5. Include examples in documentation
