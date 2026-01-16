# Phase 15: Facebook Messenger Parser

## Overview
- **Phase**: 15 of 40
- **Category**: Input Parsers
- **Release Target**: v0.6
- **Estimated Sprints**: 2

## Objectives
Implement parser for Facebook "Download Your Information" Messenger exports.

---

## Features (14 items)

### 15.1 Facebook Export Detection
**Priority**: P0 | **Complexity**: Medium
- Detect FB export structure
- Identify messages folder
- Handle ZIP vs folder
- Detect export version

### 15.2 Conversation Folder Parser
**Priority**: P0 | **Complexity**: Medium
- Parse inbox structure
- Identify conversation folders
- Handle archived messages
- Handle filtered messages

### 15.3 Message JSON Parser
**Priority**: P0 | **Complexity**: Medium
- Parse message_X.json files
- Handle multiple files per chat
- Extract messages array
- Handle pagination

### 15.4 Participant Extraction
**Priority**: P0 | **Complexity**: Medium
- Parse participants array
- Extract sender_name
- Handle Facebook IDs
- Map to participants

### 15.5 Encoding Fix (Mojibake)
**Priority**: P0 | **Complexity**: High
- Detect encoding issues
- Fix UTF-8 mojibake
- Handle special characters
- Preserve emoji correctly

### 15.6 Timestamp Handling
**Priority**: P0 | **Complexity**: Medium
- Parse timestamp_ms
- Convert milliseconds
- Handle timezone
- Normalize format

### 15.7 Photo/Video Handling
**Priority**: P0 | **Complexity**: Medium
- Parse photos array
- Parse videos array
- Locate media files
- Include as attachments

### 15.8 Audio Handling
**Priority**: P1 | **Complexity**: Medium
- Parse audio_files array
- Handle voice messages
- Include duration
- Locate audio files

### 15.9 Reaction Parsing
**Priority**: P0 | **Complexity**: Medium
- Parse reactions array
- Map reaction types
- Handle encoded emoji
- Include actor names

### 15.10 Sticker Handling
**Priority**: P2 | **Complexity**: Medium
- Parse sticker field
- Extract sticker URI
- Handle sticker images
- Create fallback text

### 15.11 Share/Link Handling
**Priority**: P1 | **Complexity**: Medium
- Parse share objects
- Extract shared links
- Handle link previews
- Include share text

### 15.12 Call Log Handling
**Priority**: P2 | **Complexity**: Low
- Detect call entries
- Include call metadata
- Create system events
- Handle duration

### 15.13 Facebook Parser Configuration
**Priority**: P1 | **Complexity**: Low
- Conversation filtering
- Date range filtering
- Media options
- Encoding fix toggle

### 15.14 Facebook Parser Tests
**Priority**: P0 | **Complexity**: Medium
- Test JSON parsing
- Test encoding fixes
- Test media handling
- Sample data fixtures

---

## Acceptance Criteria

- [ ] Parses Facebook Messenger exports
- [ ] Fixes encoding issues (mojibake)
- [ ] Handles media attachments
- [ ] Handles reactions properly
- [ ] Produces valid RSMF output
- [ ] 90%+ test coverage

---

## Technical Notes

### Facebook Export Structure
```
messages/
├── inbox/
│   ├── JohnDoe_abc123/
│   │   ├── message_1.json
│   │   ├── photos/
│   │   └── videos/
│   └── GroupChat_def456/
└── archived_threads/
```

### Mojibake Fix
```python
def fix_encoding(text):
    """Fix Facebook's encoding issues."""
    try:
        return text.encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text
```

### Reaction Emoji Mapping
```python
# Facebook encodes reactions as escaped Unicode
REACTION_MAP = {
    "\\u00f0\\u009f\\u0091\\u008d": "thumbsup",
    "\\u00e2\\u009d\\u00a4": "heart",
    # ...
}
```
