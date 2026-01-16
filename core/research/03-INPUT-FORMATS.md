# Input Format Reference: Source Platforms for RSMF Conversion

## Overview

This document catalogs the various input formats from messaging platforms that can be converted to RSMF. Understanding these formats is critical for building comprehensive parsing capabilities.

---

## 1. Slack

### Export Types

#### Standard Export (Workspace Admin)
- **Format**: JSON files organized by channel/date
- **Structure**:
  ```
  export.zip/
  ├── channels.json
  ├── users.json
  ├── integration_logs.json
  ├── #channel-name/
  │   ├── 2024-01-01.json
  │   ├── 2024-01-02.json
  │   └── ...
  └── ...
  ```

#### Enterprise Grid Export
- Full workspace export including private channels and DMs
- Same JSON structure with expanded scope

### Message JSON Structure
```json
{
  "type": "message",
  "user": "U123ABC",
  "text": "Hello world!",
  "ts": "1234567890.123456",
  "thread_ts": "1234567890.000000",
  "reply_count": 5,
  "reactions": [
    {
      "name": "thumbsup",
      "users": ["U456DEF"],
      "count": 1
    }
  ],
  "files": [
    {
      "id": "F123",
      "name": "document.pdf",
      "url_private": "https://..."
    }
  ]
}
```

### Key Fields
| Slack Field | RSMF Mapping |
|-------------|--------------|
| `user` | participant.id |
| `text` | event.body |
| `ts` | event.timestamp |
| `thread_ts` | event.parent |
| `reactions` | event.reactions |
| `files` | event.attachments |

### Limitations
- Free plan: 90 days, public channels only
- Files are links, not embedded
- Canvases exported separately

---

## 2. Microsoft Teams

### Export Types

#### Purview eDiscovery Export
- **Formats**: PST, HTML, MSG
- **HTML Structure**: Threaded conversation view
- **PST Structure**: Outlook-compatible mailbox

#### Graph API Export
- JSON format via Microsoft Graph
- Real-time access to messages

### HTML Export Structure
```html
<div class="conversation">
  <div class="message">
    <span class="sender">John Doe</span>
    <span class="timestamp">1/15/2024 9:30 AM</span>
    <div class="content">Message text here</div>
  </div>
</div>
```

### Key Challenges
- Embedded images/GIFs as attachments
- Emoji rendering issues
- Thread metadata in separate elements
- Timezone handling complexity

### Metadata Available
- Sender information
- Timestamp
- Channel/Team context
- Reactions (in newer exports)
- Attachments

---

## 3. WhatsApp

### Export Types

#### In-App Export
- **Format**: ZIP containing TXT + media
- **Text Format**: Plain text with timestamps
- **Media**: Separate files in ZIP

#### Text File Format
```
[1/15/24, 9:30:15 AM] John Doe: Hello!
[1/15/24, 9:31:00 AM] Jane Smith: Hi there!
[1/15/24, 9:32:00 AM] John Doe: <Media omitted>
```

#### Database Export (Advanced)
- Encrypted SQLite database (msgstore.db.crypt14)
- Requires decryption key
- Full message history

### Key Fields
| WhatsApp Field | RSMF Mapping |
|----------------|--------------|
| Timestamp | event.timestamp |
| Sender name | participant.display |
| Message text | event.body |
| <Media omitted> | event.attachments |

### Limitations
- 10,000 message limit (Android)
- ~18MB size limit
- No reaction export in basic export
- Media separate from text

---

## 4. iMessage/SMS

### Export Sources

#### iOS Backup (iTunes/Finder)
- SQLite database: `sms.db`
- Located in backup folder structure

#### Forensic Tool Exports
- Cellebrite UFDR
- Axiom XML
- Oxygen XML

### Database Schema (sms.db)
```sql
-- Key tables
message (ROWID, text, date, handle_id, is_from_me, ...)
handle (ROWID, id, service, ...)
attachment (ROWID, filename, mime_type, ...)
message_attachment_join (message_id, attachment_id)
```

### Key Fields
| iOS Field | RSMF Mapping |
|-----------|--------------|
| text | event.body |
| date | event.timestamp (Apple epoch) |
| handle.id | participant.id |
| is_from_me | event.direction |
| attachment | event.attachments |

### Special Considerations
- Apple timestamp epoch (Jan 1, 2001)
- Handle ID normalization
- Reaction messages in iOS 10+
- Tapback/reply encoding

---

## 5. Discord

### Export Types

#### Data Package Request
- **Format**: JSON + media files
- **Structure**: Messages organized by channel

#### Third-Party Tools
- DiscordChatExporter
- Various bots

### Message Structure
```json
{
  "id": "123456789",
  "type": "Default",
  "timestamp": "2024-01-15T09:30:00.000+00:00",
  "content": "Hello Discord!",
  "author": {
    "id": "987654321",
    "name": "username",
    "discriminator": "1234"
  },
  "attachments": [],
  "reactions": []
}
```

### Key Fields
| Discord Field | RSMF Mapping |
|---------------|--------------|
| author.id | participant.id |
| author.name | participant.display |
| content | event.body |
| timestamp | event.timestamp |
| reactions | event.reactions |
| attachments | event.attachments |

---

## 6. Signal

### Export Sources

#### Signal Backup (Android)
- Encrypted SQLite database
- Requires passphrase decryption
- Protocol buffer format

#### iOS (Limited)
- No official export
- Forensic extraction required

### Challenges
- Strong encryption
- Limited export options
- Privacy-focused design

---

## 7. Telegram

### Export Types

#### Desktop Export
- **Formats**: JSON, HTML
- **Options**: Date range, media inclusion

#### JSON Structure
```json
{
  "name": "Chat Name",
  "type": "personal_chat",
  "messages": [
    {
      "id": 1234,
      "type": "message",
      "date": "2024-01-15T09:30:00",
      "from": "John Doe",
      "text": "Hello!"
    }
  ]
}
```

### Key Fields
| Telegram Field | RSMF Mapping |
|----------------|--------------|
| from | participant.display |
| text | event.body |
| date | event.timestamp |
| photo/file | event.attachments |

---

## 8. Facebook Messenger

### Export Types

#### Download Your Information
- **Format**: JSON or HTML
- **Path**: `messages/inbox/{conversation}/`

#### JSON Structure
```json
{
  "participants": [
    {"name": "John Doe"}
  ],
  "messages": [
    {
      "sender_name": "John Doe",
      "timestamp_ms": 1705312200000,
      "content": "Hello!"
    }
  ]
}
```

### Key Fields
| FB Field | RSMF Mapping |
|----------|--------------|
| sender_name | participant.display |
| content | event.body |
| timestamp_ms | event.timestamp |
| photos/files | event.attachments |
| reactions | event.reactions |

### Special Considerations
- UTF-8 encoding issues (mojibake)
- Timestamp in milliseconds
- Reaction names encoded

---

## 9. Google Chat/Hangouts

### Export Types

#### Google Takeout
- **Format**: JSON
- **Structure**: Messages by conversation

#### JSON Structure
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

---

## 10. Bloomberg Chat

### Export Characteristics
- Proprietary format
- Regulatory compliance focus
- Structured message format
- Enterprise-only access

### Key Fields
- Sender UUID
- Timestamp (precise)
- Message content
- Conversation ID
- Compliance metadata

---

## 11. Forensic Tool Exports

### Cellebrite UFDR
- Universal Forensic Data Report
- XML-based structure
- Comprehensive metadata
- Native Relativity support

### Magnet Axiom XML
```xml
<artifact>
  <fragment>
    <field name="From">+15551234567</field>
    <field name="To">+15559876543</field>
    <field name="Body">Message text</field>
    <field name="Timestamp">2024-01-15 09:30:00</field>
  </fragment>
</artifact>
```

### Oxygen Forensic
- XML export format
- Multiple device support
- Rich metadata

### MSAB XRY
- XML-based reports
- Case structure
- Evidence organization

---

## Format Priority Matrix

| Format | Priority | Complexity | Usage Frequency |
|--------|----------|------------|-----------------|
| Slack JSON | High | Medium | Very High |
| Teams HTML | High | High | Very High |
| WhatsApp TXT | High | Low | High |
| iMessage SQLite | High | High | High |
| Discord JSON | Medium | Low | Medium |
| Cellebrite UFDR | High | High | High |
| Axiom XML | High | Medium | High |
| Telegram JSON | Medium | Low | Medium |
| Facebook JSON | Medium | Medium | Medium |
| Signal Backup | Low | Very High | Low |

---

## Implementation Recommendations

### Phase 1: Core Formats
1. Slack JSON (Standard Export)
2. WhatsApp TXT + Media
3. Generic CSV/TSV

### Phase 2: Enterprise
1. Microsoft Teams (HTML/PST)
2. Google Chat (Takeout)
3. Cellebrite UFDR

### Phase 3: Advanced
1. iMessage SQLite
2. Magnet Axiom XML
3. Discord JSON

### Phase 4: Extended
1. Telegram JSON
2. Facebook Messenger
3. Signal (with limitations)
4. Bloomberg (enterprise)
