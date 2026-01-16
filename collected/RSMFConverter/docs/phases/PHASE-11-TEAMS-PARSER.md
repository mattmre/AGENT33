# Phase 11: Microsoft Teams Parser

## Overview
- **Phase**: 11 of 40
- **Category**: Input Parsers
- **Release Target**: v0.5
- **Estimated Sprints**: 3

## Objectives
Implement parsers for Microsoft Teams exports from Purview eDiscovery in HTML, PST, and MSG formats.

---

## Features (16 items)

### 11.1 Teams HTML Export Detection
**Priority**: P0 | **Complexity**: Medium
- Detect Teams HTML structure
- Identify conversation files
- Handle folder structure
- Detect export type

### 11.2 HTML Conversation Parser
**Priority**: P0 | **Complexity**: High
- Parse HTML conversation markup
- Extract message elements
- Handle nested structures
- Extract metadata

### 11.3 Teams PST Export Support
**Priority**: P1 | **Complexity**: High
- Parse PST file format
- Navigate folder structure
- Extract Teams items
- Handle attachments

### 11.4 MSG File Parser
**Priority**: P1 | **Complexity**: Medium
- Parse individual MSG files
- Extract message properties
- Handle Teams-specific fields
- Extract embedded content

### 11.5 Participant Extraction
**Priority**: P0 | **Complexity**: Medium
- Extract sender information
- Parse recipient lists
- Handle display names
- Map email to participants

### 11.6 Timestamp Extraction
**Priority**: P0 | **Complexity**: Medium
- Parse timestamp formats
- Handle timezone information
- Normalize to UTC
- Handle missing timestamps

### 11.7 Thread ID Handling
**Priority**: P1 | **Complexity**: High
- Extract thread identifiers
- Reconstruct conversation threads
- Handle reply chains
- Link related messages

### 11.8 Channel/Chat Detection
**Priority**: P1 | **Complexity**: Medium
- Distinguish channels from chats
- Extract team/channel info
- Handle meeting chats
- Handle group chats

### 11.9 Attachment Extraction
**Priority**: P0 | **Complexity**: Medium
- Extract inline images
- Extract file attachments
- Handle OneDrive links
- Download accessible files

### 11.10 Reaction Handling
**Priority**: P1 | **Complexity**: Medium
- Extract reactions from HTML
- Map reaction types
- Handle reaction counts
- Note: Limited in exports

### 11.11 Code Block Handling
**Priority**: P2 | **Complexity**: Medium
- Detect code snippets
- Preserve formatting
- Handle syntax highlighting
- Convert to plain text

### 11.12 Adaptive Card Handling
**Priority**: P2 | **Complexity**: High
- Detect adaptive cards
- Extract text content
- Handle interactive elements
- Create text representation

### 11.13 Meeting Metadata
**Priority**: P2 | **Complexity**: Medium
- Extract meeting info
- Handle recording links
- Include attendance data
- Handle transcripts

### 11.14 GIF/Sticker Handling
**Priority**: P2 | **Complexity**: Medium
- Detect embedded GIFs
- Extract sticker references
- Download if possible
- Create placeholders

### 11.15 Teams Parser Configuration
**Priority**: P1 | **Complexity**: Low
- Export format selection
- Date range filtering
- Channel/chat filtering
- Attachment options

### 11.16 Teams Parser Tests
**Priority**: P0 | **Complexity**: High
- Test HTML parsing
- Test PST parsing
- Test edge cases
- Sample data fixtures

---

## Acceptance Criteria

- [ ] Parses Teams HTML exports
- [ ] Parses Teams PST exports
- [ ] Correctly reconstructs threads
- [ ] Handles attachments properly
- [ ] Produces valid RSMF output
- [ ] 90%+ test coverage

---

## Dependencies
- Phase 3: Parser Framework

## Blocks
- None (parallel with other parsers)

---

## Technical Notes

### Teams HTML Structure
```html
<div class="message">
  <div class="message-header">
    <span class="sender">John Doe</span>
    <span class="timestamp">1/15/2024 9:30 AM</span>
  </div>
  <div class="message-body">
    Message content here
  </div>
</div>
```

### PST Structure
```
Root/
└── Conversation History/
    └── Team Chat/
        ├── [Team Name]/
        │   └── [Channel Name]/
        │       └── messages...
        └── ...
```

### Key Libraries
- beautifulsoup4 for HTML parsing
- pypff or libpff for PST parsing
- extract-msg for MSG files
