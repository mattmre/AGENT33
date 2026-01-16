# Phase 19: Google Chat/Hangouts Parser

## Overview
- **Phase**: 19 of 40
- **Category**: Input Parsers
- **Release Target**: v0.8
- **Estimated Sprints**: 2

## Objectives
Implement parser for Google Takeout exports of Google Chat and legacy Hangouts data.

---

## Features (12 items)

### 19.1 Google Takeout Detection
**Priority**: P0 | **Complexity**: Medium
- Detect Takeout structure
- Identify Chat vs Hangouts
- Handle export versions
- Parse folder structure

### 19.2 Google Chat Parser
**Priority**: P0 | **Complexity**: Medium
- Parse Chat JSON format
- Extract messages
- Handle spaces/rooms
- Extract DMs

### 19.3 Hangouts Parser (Legacy)
**Priority**: P1 | **Complexity**: Medium
- Parse Hangouts.json
- Handle conversation_state
- Extract participant_data
- Parse events

### 19.4 Participant Resolution
**Priority**: P0 | **Complexity**: Medium
- Extract user profiles
- Map gaia IDs
- Resolve display names
- Handle email addresses

### 19.5 Space/Room Handling
**Priority**: P0 | **Complexity**: Medium
- Identify space type
- Extract space metadata
- Handle membership
- Map to conversations

### 19.6 Message Content Extraction
**Priority**: P0 | **Complexity**: Medium
- Parse message segments
- Handle text content
- Handle formatting
- Handle links

### 19.7 Attachment Handling
**Priority**: P0 | **Complexity**: Medium
- Parse attachment refs
- Handle Drive links
- Download accessible files
- Create placeholders

### 19.8 Reaction Parsing
**Priority**: P1 | **Complexity**: Medium
- Extract reaction data
- Map emoji reactions
- Include reactor info
- Handle reaction removal

### 19.9 Thread Handling
**Priority**: P1 | **Complexity**: Medium
- Detect threaded messages
- Link to parent
- Handle thread spaces
- Preserve thread context

### 19.10 Video/Voice Call Data
**Priority**: P2 | **Complexity**: Low
- Detect call events
- Include call metadata
- Create system events
- Handle Meet links

### 19.11 Google Parser Configuration
**Priority**: P1 | **Complexity**: Low
- Space filtering
- Date range filtering
- Include/exclude calls
- Attachment options

### 19.12 Google Parser Tests
**Priority**: P0 | **Complexity**: Medium
- Test Chat parsing
- Test Hangouts parsing
- Test edge cases
- Sample data fixtures

---

## Acceptance Criteria

- [ ] Parses Google Chat exports
- [ ] Parses legacy Hangouts exports
- [ ] Handles spaces and DMs
- [ ] Handles attachments
- [ ] Produces valid RSMF output
- [ ] 90%+ test coverage

---

## Technical Notes

### Google Chat Structure
```json
{
  "messages": [
    {
      "creator": {
        "name": "John Doe",
        "email": "john@gmail.com"
      },
      "created_date": "2024-01-15T09:30:00.000Z",
      "text": "Hello!"
    }
  ]
}
```

### Hangouts Structure
```json
{
  "conversations": [{
    "conversation_id": {...},
    "conversation": {
      "participant_data": [...],
      "events": [...]
    }
  }]
}
```
