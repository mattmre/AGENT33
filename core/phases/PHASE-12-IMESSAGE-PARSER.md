# Phase 12: iMessage/SMS Parser

## Overview
- **Phase**: 12 of 40
- **Category**: Input Parsers
- **Release Target**: v0.5
- **Estimated Sprints**: 3

## Objectives
Implement parser for iOS iMessage and SMS data from backup databases and forensic exports.

---

## Features (15 items)

### 12.1 iOS Backup Database Detection
**Priority**: P0 | **Complexity**: Medium
- Detect sms.db/chat.db
- Handle backup folder structure
- Support iTunes/Finder backups
- Detect database version

### 12.2 SQLite Database Parser
**Priority**: P0 | **Complexity**: High
- Open SQLite database
- Parse message table
- Parse handle table
- Parse attachment table
- Handle schema versions

### 12.3 Message Table Parsing
**Priority**: P0 | **Complexity**: High
- Extract message content
- Parse ROWID relationships
- Handle attributedBody blob
- Parse message flags

### 12.4 Handle/Contact Resolution
**Priority**: P0 | **Complexity**: Medium
- Parse handle table
- Resolve phone numbers
- Handle email addresses
- Map to participants

### 12.5 Apple Timestamp Conversion
**Priority**: P0 | **Complexity**: Medium
- Convert Apple epoch timestamps
- Handle nanosecond precision
- Handle timezone
- Handle date column variations

### 12.6 Conversation Threading
**Priority**: P0 | **Complexity**: High
- Identify conversation groups
- Link messages to conversations
- Handle group chats
- Preserve ordering

### 12.7 Attachment Extraction
**Priority**: P0 | **Complexity**: High
- Parse attachment table
- Locate attachment files
- Handle file paths
- Copy attachment files
- Handle missing attachments

### 12.8 iMessage Feature Support
**Priority**: P1 | **Complexity**: Medium
- Detect iMessage vs SMS
- Handle read receipts
- Handle delivered status
- Detect typing indicators

### 12.9 Reaction (Tapback) Parsing
**Priority**: P1 | **Complexity**: High
- Detect tapback messages
- Parse associated_message_guid
- Map tapback types
- Handle tapback removal

### 12.10 Reply Handling
**Priority**: P1 | **Complexity**: High
- Detect threaded replies
- Parse thread_originator_guid
- Link to parent messages
- Handle inline replies

### 12.11 Group Chat Handling
**Priority**: P0 | **Complexity**: Medium
- Identify group conversations
- Extract all participants
- Handle participant changes
- Handle group naming

### 12.12 Deleted Message Detection
**Priority**: P2 | **Complexity**: Medium
- Detect deleted flag
- Handle recently deleted
- Include deletion metadata

### 12.13 Effects and Formatting
**Priority**: P2 | **Complexity**: Medium
- Detect bubble effects
- Handle screen effects
- Preserve rich formatting
- Handle mentions

### 12.14 iMessage Parser Configuration
**Priority**: P1 | **Complexity**: Low
- Database path option
- Conversation filtering
- Date range filtering
- Attachment handling

### 12.15 iMessage Parser Tests
**Priority**: P0 | **Complexity**: High
- Test database parsing
- Test attachment handling
- Test tapback parsing
- Sample database fixtures

---

## Acceptance Criteria

- [ ] Parses iOS backup sms.db
- [ ] Correctly extracts attachments
- [ ] Handles tapback reactions
- [ ] Supports group chats
- [ ] Produces valid RSMF output
- [ ] 90%+ test coverage

---

## Dependencies
- Phase 3: Parser Framework

## Blocks
- None (parallel with other parsers)

---

## Technical Notes

### Key Database Tables
```sql
-- message table
ROWID, text, handle_id, date, is_from_me,
cache_has_attachments, associated_message_guid,
thread_originator_guid, reply_to_guid

-- handle table
ROWID, id, service

-- attachment table
ROWID, filename, mime_type, transfer_name

-- message_attachment_join
message_id, attachment_id
```

### Apple Epoch Conversion
```python
# Apple epoch: Jan 1, 2001 00:00:00 UTC
APPLE_EPOCH = 978307200

def convert_apple_timestamp(ts):
    # Handle nanoseconds (iOS 11+)
    if ts > 1e15:
        ts = ts / 1e9
    return datetime.utcfromtimestamp(ts + APPLE_EPOCH)
```

### Tapback Types
```python
TAPBACK_TYPES = {
    2000: "love",
    2001: "like",
    2002: "dislike",
    2003: "laugh",
    2004: "emphasis",
    2005: "question"
}
```
