# RSMF (Relativity Short Message Format) Technical Specification

## Overview

RSMF (Relativity Short Message Format) is an RFC 5322 (Internet Message Format) standards-compliant file format that encapsulates normalized short message data for eDiscovery purposes. It was developed by Relativity to standardize the processing and review of communications from various messaging platforms.

## Current Version: 2.0.0

### Version History
- **1.0**: Original specification with basic message, participant, and conversation support
- **2.0.0**: Added read receipts, message direction, history events, reactions, custom platform icons, and event collection IDs

## File Structure

An RSMF file consists of three layers:

### 1. EML Layer (Outer Container)
- RFC 5322 compliant email message format
- Contains RSMF-specific headers
- Wraps the ZIP attachment

### 2. ZIP Layer (rsmf.zip)
- Must be named exactly `rsmf.zip`
- Contains the manifest and all referenced files
- All files must be at the root level

### 3. JSON Layer (rsmf_manifest.json)
- Core data structure
- Defines participants, conversations, and events
- References attachments and avatars

## Required EML Headers

| Header | Description | Required |
|--------|-------------|----------|
| `X-RSMF-Version` | RSMF specification version (e.g., "2.0.0") | Yes |
| `X-RSMF-Generator` | Tool that generated the file | No |
| `X-RSMF-BeginDate` | ISO8601 timestamp of first event | No |
| `X-RSMF-EndDate` | ISO8601 timestamp of last event | No |
| `X-RSMF-EventCount` | Number of events in manifest | No |
| `From` | Custodian information | No |
| `To` | Participant list | No |

## JSON Manifest Schema (rsmf_manifest.json)

### Root Structure
```json
{
  "version": "2.0.0",
  "participants": [...],
  "conversations": [...],
  "events": [...],
  "eventcollectionid": "optional-collection-id"
}
```

### Required Root Properties
- `version` (string): RSMF specification version
- `participants` (array): List of participant objects
- `conversations` (array): List of conversation objects
- `events` (array): List of event objects

### Optional Root Properties
- `eventcollectionid` (string): Unique ID to group related RSMFs from a single conversation

---

## Participants Object

### Required Properties
| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique identifier within the manifest |

### Optional Properties
| Property | Type | Description |
|----------|------|-------------|
| `display` | string | Display name for the participant |
| `email` | string | Email address (IDN format supported) |
| `avatar` | string | Filename of avatar image in rsmf.zip |
| `account_id` | string | Platform-specific account ID |
| `custom` | array | Custom metadata key-value pairs |

### Example
```json
{
  "id": "P1",
  "display": "John Smith",
  "email": "john.smith@example.com",
  "avatar": "john_avatar.png",
  "account_id": "U123456",
  "custom": [
    {"name": "Phone Number", "value": "555-123-4567"},
    {"name": "Department", "value": "Legal"}
  ]
}
```

---

## Conversations Object

### Required Properties
| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique identifier within the manifest |
| `platform` | string | Platform name (e.g., "slack", "sms", "teams") |
| `participants` | array | Array of participant IDs |

### Optional Properties
| Property | Type | Description |
|----------|------|-------------|
| `display` | string | Display name for the conversation |
| `type` | enum | "direct" or "channel" |
| `custodian` | string | ID of the data source owner |
| `custom` | array | Custom metadata key-value pairs |
| `icon` | string | Filename of platform icon in rsmf.zip |

### Conversation Types
- **direct**: Participants do not change during conversation
- **channel**: Participants may join/leave during conversation

### Example
```json
{
  "id": "C1",
  "display": "Project Alpha Discussion",
  "platform": "slack",
  "type": "channel",
  "participants": ["P1", "P2", "P3"],
  "custodian": "P1",
  "icon": "slack_icon.png",
  "custom": [
    {"name": "Channel ID", "value": "C0123456789"},
    {"name": "Workspace", "value": "acme-corp"}
  ]
}
```

---

## Events Object

### Required Properties
| Property | Type | Description |
|----------|------|-------------|
| `type` | enum | Event type (see below) |

### Event Types
| Type | Description |
|------|-------------|
| `message` | A standard message |
| `disclaimer` | System disclaimer message |
| `join` | Participant joined conversation |
| `leave` | Participant left conversation |
| `history` | History review indicator |
| `unknown` | Unclassified event |

### Optional Event Properties
| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique event ID (required for threading) |
| `parent` | string | Parent event ID for threaded replies |
| `body` | string | Message content |
| `participant` | string | ID of event source |
| `conversation` | string | ID of containing conversation |
| `timestamp` | string | ISO8601 date-time |
| `deleted` | boolean | Whether event was deleted |
| `importance` | enum | "normal" or "high" |
| `direction` | enum | "incoming" or "outgoing" |
| `reactions` | array | Reaction objects |
| `attachments` | array | Attachment objects |
| `edits` | array | Edit history objects |
| `read_receipts` | array | Read receipt objects |
| `custom` | array | Custom metadata |

### Example Message Event
```json
{
  "id": "M001",
  "type": "message",
  "body": "Has everyone reviewed the contract?",
  "participant": "P1",
  "conversation": "C1",
  "timestamp": "2024-01-15T09:30:00Z",
  "direction": "outgoing",
  "importance": "normal",
  "reactions": [
    {
      "value": "thumbsup",
      "count": 2,
      "participants": ["P2", "P3"]
    }
  ],
  "attachments": [
    {
      "id": "contract_v2.pdf",
      "display": "Contract Draft v2.pdf",
      "size": 245678
    }
  ]
}
```

---

## Reactions Object

### Required Properties
| Property | Type | Description |
|----------|------|-------------|
| `value` | string | Reaction identifier (max 30 chars) |

### Optional Properties
| Property | Type | Description |
|----------|------|-------------|
| `count` | integer | Number of times reaction was added |
| `participants` | array | IDs of participants who reacted |

### Supported Visual Reactions
Common reactions with visual support include:
- thumbsup, thumbsdown
- heart, broken_heart
- smile, laughing, joy
- thinking, confused
- clap, fire, rocket
- check, x

---

## Attachments Object

### Required Properties
| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Filename in rsmf.zip (with extension) |

### Optional Properties
| Property | Type | Description |
|----------|------|-------------|
| `display` | string | Display name for attachment |
| `size` | integer | File size in bytes |

### Inline Image Support
Attachments with display names ending in `.png`, `.jpg`, `.jpeg`, or `.gif` are displayed inline in the viewer.

---

## Edits Object

### Required Properties
| Property | Type | Description |
|----------|------|-------------|
| `participant` | string | ID of editor |

### Optional Properties
| Property | Type | Description |
|----------|------|-------------|
| `timestamp` | string | ISO8601 edit timestamp |
| `previous` | string | Previous message body |
| `new` | string | New message body |

---

## Read Receipts Object (RSMF 2.0)

### Required Properties
| Property | Type | Description |
|----------|------|-------------|
| `participant` | string | ID of recipient |

### Optional Properties
| Property | Type | Description |
|----------|------|-------------|
| `timestamp` | string | ISO8601 timestamp |
| `action` | enum | "read" or "delivered" |

---

## Timestamp Format

All timestamps must conform to ISO8601 standard:
- Format: `YYYY-MM-DDTHH:MM:SS` or `YYYY-MM-DDTHH:MM:SSZ`
- Timezone handling varies by platform
- UTC recommended for consistency

---

## Supported Platforms

Over 75 messaging platforms can be converted to RSMF, including:

### Enterprise Chat
- Slack
- Microsoft Teams
- Google Chat/Hangouts
- Bloomberg Chat
- Symphony
- Zoom Chat

### Mobile Messaging
- SMS/MMS
- iMessage
- WhatsApp
- Signal
- Telegram
- WeChat
- Facebook Messenger
- Instagram DM

### Social/Other
- Discord
- Skype
- LinkedIn Messages
- Twitter/X DMs

---

## Validation

Relativity provides official RSMF validators:
- **Relativity.RSMFU.Validator.dll**: .NET library for validation
- **ValidatorGui**: GUI application for validation

### Validation Checks
1. JSON schema compliance
2. Required fields presence
3. ID reference integrity
4. Attachment file existence
5. Timestamp format validation

---

## Best Practices

### File Organization
1. Keep all files at ZIP root level
2. Use unique, descriptive filenames for attachments
3. Include avatar images when available

### Data Quality
1. Always include participant display names when known
2. Use consistent participant IDs across events
3. Include timestamps for all events
4. Preserve edit history when available

### Performance
1. Slice large conversations by time period
2. Use meaningful event collection IDs
3. Optimize attachment file sizes

---

## References

- [Relativity RSMF Documentation](https://help.relativity.com/RelativityOne/Content/System_Guides/Relativity_Short_Message_Format/Relativity_short_message_format.htm)
- [RSMF Schema Repository](https://github.com/relativitydev/rsmf-validator-samples)
- [RFC 5322 - Internet Message Format](https://tools.ietf.org/html/rfc5322)
