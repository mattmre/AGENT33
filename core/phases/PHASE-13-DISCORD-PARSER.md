# Phase 13: Discord Parser

## Overview
- **Phase**: 13 of 40
- **Category**: Input Parsers
- **Release Target**: v0.6
- **Estimated Sprints**: 2

## Objectives
Implement parser for Discord data package exports and third-party export tools.

---

## Features (14 items)

### 13.1 Discord Data Package Detection
**Priority**: P0 | **Complexity**: Medium
- Detect Discord export structure
- Identify messages folder
- Parse index.json
- Handle package versions

### 13.2 Message JSON Parser
**Priority**: P0 | **Complexity**: Medium
- Parse message JSON files
- Extract message content
- Handle message types
- Parse timestamps

### 13.3 User/Server Resolution
**Priority**: P0 | **Complexity**: Medium
- Parse user data
- Resolve server info
- Map user IDs
- Handle display names

### 13.4 Channel Mapping
**Priority**: P0 | **Complexity**: Medium
- Identify channel types
- Handle DMs vs servers
- Map channel names
- Handle categories

### 13.5 Thread Handling
**Priority**: P1 | **Complexity**: High
- Detect threaded messages
- Parse thread metadata
- Link replies
- Handle forum channels

### 13.6 Reaction Parsing
**Priority**: P0 | **Complexity**: Medium
- Parse reaction data
- Handle custom emoji
- Map standard emoji
- Include user lists

### 13.7 Attachment Handling
**Priority**: P0 | **Complexity**: Medium
- Parse attachment URLs
- Download if accessible
- Handle CDN links
- Create placeholders

### 13.8 Embed Handling
**Priority**: P1 | **Complexity**: Medium
- Parse embed objects
- Extract embed content
- Handle link previews
- Handle rich embeds

### 13.9 Message Reference Handling
**Priority**: P1 | **Complexity**: Medium
- Detect reply references
- Link to original messages
- Handle cross-channel refs
- Handle deleted refs

### 13.10 DiscordChatExporter Support
**Priority**: P1 | **Complexity**: Medium
- Support DCE JSON format
- Support DCE HTML format
- Handle format variations
- Maintain compatibility

### 13.11 Bot Message Handling
**Priority**: P2 | **Complexity**: Low
- Identify bot messages
- Extract bot names
- Handle webhook messages
- Handle system messages

### 13.12 Sticker Handling
**Priority**: P2 | **Complexity**: Medium
- Detect sticker messages
- Extract sticker info
- Download sticker images
- Create fallback text

### 13.13 Discord Parser Configuration
**Priority**: P1 | **Complexity**: Low
- Server/channel filtering
- Date range filtering
- Attachment options
- Bot inclusion toggle

### 13.14 Discord Parser Tests
**Priority**: P0 | **Complexity**: Medium
- Test data package parsing
- Test DCE format
- Test edge cases
- Sample data fixtures

---

## Acceptance Criteria

- [ ] Parses Discord data packages
- [ ] Supports DiscordChatExporter output
- [ ] Handles reactions and threads
- [ ] Handles attachments properly
- [ ] Produces valid RSMF output
- [ ] 90%+ test coverage

---

## Dependencies
- Phase 3: Parser Framework

---

## Technical Notes

### Discord Data Package Structure
```
package/
├── account/
│   └── user.json
├── messages/
│   └── c123456789/
│       ├── channel.json
│       └── messages.json
└── servers/
    └── index.json
```

### Message Format
```json
{
  "ID": "123456789",
  "Timestamp": "2024-01-15T09:30:00.000+00:00",
  "Contents": "Hello!",
  "Author": {
    "ID": "987654321",
    "Username": "user",
    "Discriminator": "1234"
  },
  "Attachments": [],
  "Reactions": []
}
```
