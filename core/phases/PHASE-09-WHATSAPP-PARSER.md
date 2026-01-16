# Phase 9: WhatsApp Parser

## Overview
- **Phase**: 9 of 40
- **Category**: Input Parsers
- **Release Target**: v0.4
- **Estimated Sprints**: 2

## Objectives
Implement a comprehensive WhatsApp export parser supporting the standard text export format with media files.

---

## Features (16 items)

### 9.1 WhatsApp TXT Format Detection
**Priority**: P0 | **Complexity**: Medium
- Detect WhatsApp export format
- Handle ZIP vs folder input
- Identify chat.txt file
- Support multiple naming conventions

### 9.2 Message Line Parser
**Priority**: P0 | **Complexity**: High
- Parse timestamp formats
- Handle multiple date formats
- Extract sender name
- Extract message content
- Handle multi-line messages

### 9.3 Timestamp Format Handling
**Priority**: P0 | **Complexity**: Medium
- Support MM/DD/YY format
- Support DD/MM/YY format
- Support 12-hour time
- Support 24-hour time
- Handle locale variations

### 9.4 Participant Extraction
**Priority**: P0 | **Complexity**: Medium
- Extract unique senders
- Handle phone number formats
- Handle contact names
- Detect self (custodian)

### 9.5 System Message Handling
**Priority**: P1 | **Complexity**: Medium
- Detect system messages
- Handle "X joined" messages
- Handle "X left" messages
- Handle encryption notices
- Handle call notifications

### 9.6 Media Reference Extraction
**Priority**: P0 | **Complexity**: Medium
- Detect "<Media omitted>"
- Detect "image omitted"
- Detect "video omitted"
- Detect "audio omitted"
- Detect "document omitted"

### 9.7 Media File Matching
**Priority**: P0 | **Complexity**: High
- Match media files to messages
- Handle naming patterns
- Support IMG-/VID-/AUD- prefixes
- Handle timestamp-based names
- Handle sequence numbers

### 9.8 Voice Message Handling
**Priority**: P1 | **Complexity**: Medium
- Detect voice messages (PTT)
- Extract audio files
- Include duration metadata
- Create placeholder text

### 9.9 Location Message Parsing
**Priority**: P2 | **Complexity**: Medium
- Detect location shares
- Extract coordinates
- Create custom field
- Generate display text

### 9.10 Contact Card Parsing
**Priority**: P2 | **Complexity**: Medium
- Detect shared contacts
- Extract vCard data
- Include as attachment
- Generate display text

### 9.11 Reply Detection
**Priority**: P1 | **Complexity**: High
- Detect quoted replies
- Extract original message
- Attempt parent linking
- Handle nested quotes

### 9.12 Emoji Handling
**Priority**: P1 | **Complexity**: Medium
- Preserve Unicode emoji
- Handle emoji-only messages
- Support skin tone modifiers
- Handle custom reactions

### 9.13 Group Chat Support
**Priority**: P0 | **Complexity**: Medium
- Handle group conversations
- Track all participants
- Handle participant changes
- Support large groups

### 9.14 Encoding Handling
**Priority**: P1 | **Complexity**: Medium
- Detect file encoding
- Handle UTF-8/UTF-16
- Handle encoding errors
- Support BOM detection

### 9.15 WhatsApp Parser Configuration
**Priority**: P1 | **Complexity**: Low
- Configurable date format
- Configurable custodian
- Media inclusion options
- Timezone settings

### 9.16 WhatsApp Parser Tests
**Priority**: P0 | **Complexity**: High
- Test various formats
- Test edge cases
- Test media handling
- Test error recovery
- Sample data fixtures

---

## Acceptance Criteria

- [ ] Parses standard WhatsApp exports
- [ ] Handles multiple date formats
- [ ] Correctly matches media files
- [ ] Handles system messages
- [ ] Produces valid RSMF output
- [ ] 90%+ test coverage

---

## Dependencies
- Phase 3: Parser Framework

## Blocks
- None (parallel with other parsers)

---

## Technical Notes

### WhatsApp Export Formats
```
# Format 1 (US, 12-hour)
[1/15/24, 9:30:15 AM] John Doe: Hello!

# Format 2 (EU, 24-hour)
[15/01/2024, 09:30:15] John Doe: Hello!

# Format 3 (No seconds)
[1/15/24, 9:30 AM] John Doe: Hello!
```

### Media File Patterns
```
IMG-20240115-WA0001.jpg
VID-20240115-WA0002.mp4
AUD-20240115-WA0003.opus
PTT-20240115-WA0004.opus
DOC-20240115-WA0005.pdf
```

### System Message Patterns
```
Messages and calls are end-to-end encrypted.
John Doe joined using this group's invite link
You added Jane Smith
```
