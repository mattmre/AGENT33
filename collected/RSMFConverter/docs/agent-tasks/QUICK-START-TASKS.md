# Quick Start Tasks for AI Agents

## Ready-to-Implement Tasks

These tasks are well-defined and can be implemented immediately by AI agents.

---

## Tier 1: Foundation Tasks (Start Here)

### Task 1.1: Project Structure Setup
**Phase**: 1 | **Priority**: P0 | **Complexity**: Low

```
Description: Create the Python project structure with Poetry
Files to Create:
- pyproject.toml
- src/rsmfconverter/__init__.py
- src/rsmfconverter/core/__init__.py
- src/rsmfconverter/parsers/__init__.py
- src/rsmfconverter/writers/__init__.py
- tests/conftest.py

Acceptance:
- Can install with pip install -e .
- All imports work
- pytest runs successfully
```

### Task 1.2: Data Model - Participant
**Phase**: 2 | **Priority**: P0 | **Complexity**: Medium

```
Description: Create the Participant data model
File: src/rsmfconverter/models/participant.py

Requirements:
- Dataclass with id, display, email, avatar, account_id, custom
- to_dict() method
- from_dict() class method
- Validation for required fields

Test File: tests/models/test_participant.py
```

### Task 1.3: Data Model - Conversation
**Phase**: 2 | **Priority**: P0 | **Complexity**: Medium

```
Description: Create the Conversation data model
File: src/rsmfconverter/models/conversation.py

Requirements:
- Dataclass with id, platform, type, participants, custodian, custom, icon
- Enum for ConversationType
- to_dict() method
- from_dict() class method
- Reference validation

Test File: tests/models/test_conversation.py
```

### Task 1.4: Data Model - Event
**Phase**: 2 | **Priority**: P0 | **Complexity**: High

```
Description: Create the Event data models
File: src/rsmfconverter/models/event.py

Requirements:
- EventType enum
- Base Event class
- MessageEvent subclass
- JoinEvent, LeaveEvent, etc.
- Reaction, Attachment, Edit, ReadReceipt models
- All serialization methods

Test File: tests/models/test_event.py
```

---

## Tier 2: Parser Tasks

### Task 2.1: WhatsApp TXT Parser - Basic
**Phase**: 9 | **Priority**: P0 | **Complexity**: Medium

```
Description: Parse basic WhatsApp TXT exports
File: src/rsmfconverter/parsers/whatsapp.py

Requirements:
- Detect WhatsApp export format
- Parse timestamp (multiple formats)
- Extract sender name
- Extract message content
- Handle system messages

Input Example:
[1/15/24, 9:30:15 AM] John Doe: Hello!

Test File: tests/parsers/test_whatsapp.py
```

### Task 2.2: Slack JSON Parser - Basic
**Phase**: 10 | **Priority**: P0 | **Complexity**: Medium

```
Description: Parse basic Slack JSON exports
File: src/rsmfconverter/parsers/slack.py

Requirements:
- Detect Slack export structure
- Parse users.json
- Parse channels.json
- Parse message JSON files
- Handle basic message types

Test File: tests/parsers/test_slack.py
```

### Task 2.3: CSV Generic Parser
**Phase**: 18 | **Priority**: P0 | **Complexity**: Medium

```
Description: Parse generic CSV message exports
File: src/rsmfconverter/parsers/csv_parser.py

Requirements:
- Configurable column mapping
- Handle various delimiters
- Handle quoted fields
- Support header row

Test File: tests/parsers/test_csv_parser.py
```

---

## Tier 3: Writer Tasks

### Task 3.1: RSMF JSON Manifest Writer
**Phase**: 4 | **Priority**: P0 | **Complexity**: High

```
Description: Generate rsmf_manifest.json from document
File: src/rsmfconverter/writers/manifest.py

Requirements:
- Serialize participants
- Serialize conversations
- Serialize events
- Handle all event types
- Validate JSON output

Test File: tests/writers/test_manifest.py
```

### Task 3.2: RSMF ZIP Creator
**Phase**: 4 | **Priority**: P0 | **Complexity**: Medium

```
Description: Create rsmf.zip container
File: src/rsmfconverter/writers/zip_creator.py

Requirements:
- Create ZIP archive
- Add manifest file
- Add attachment files
- Validate structure

Test File: tests/writers/test_zip_creator.py
```

### Task 3.3: RSMF EML Writer
**Phase**: 4 | **Priority**: P0 | **Complexity**: High

```
Description: Generate RSMF EML file
File: src/rsmfconverter/writers/eml.py

Requirements:
- RFC 5322 compliant output
- X-RSMF headers
- Multipart structure
- ZIP attachment
- 7-bit encoding

Test File: tests/writers/test_eml.py
```

---

## Tier 4: Validation Tasks

### Task 4.1: JSON Schema Validator
**Phase**: 5 | **Priority**: P0 | **Complexity**: Medium

```
Description: Validate JSON against RSMF schema
File: src/rsmfconverter/validation/schema.py

Requirements:
- Load RSMF schemas (1.0, 2.0)
- Validate manifest JSON
- Return detailed errors
- Support both versions

Test File: tests/validation/test_schema.py
```

### Task 4.2: Reference Validator
**Phase**: 5 | **Priority**: P0 | **Complexity**: Medium

```
Description: Validate internal references
File: src/rsmfconverter/validation/references.py

Requirements:
- Validate participant references
- Validate conversation references
- Validate event parent references
- Report orphan references

Test File: tests/validation/test_references.py
```

---

## Tier 5: CLI Tasks

### Task 5.1: Basic CLI Setup
**Phase**: 6 | **Priority**: P0 | **Complexity**: Medium

```
Description: Create basic CLI with Typer
File: src/rsmfconverter/cli/main.py

Requirements:
- Main entry point
- --version flag
- --help flag
- Basic convert command

Test File: tests/cli/test_main.py
```

### Task 5.2: Convert Command
**Phase**: 6 | **Priority**: P0 | **Complexity**: High

```
Description: Implement convert command
File: src/rsmfconverter/cli/commands/convert.py

Requirements:
- Input file argument
- Output path option
- Format option
- Progress display
- Error handling

Test File: tests/cli/test_convert.py
```

---

## Task Selection Guidelines

### For New Agents
Start with Tier 1 tasks in order. These establish the foundation.

### For Parallel Work
- Multiple Tier 2 parser tasks can run simultaneously
- Tier 3 writer tasks depend on Tier 1 models

### Dependencies
```
Tier 1 (Foundation) → Tier 2 (Parsers)
Tier 1 (Foundation) → Tier 3 (Writers)
Tier 3 (Writers) → Tier 4 (Validation)
All → Tier 5 (CLI)
```

---

## Reporting Completion

When completing a task:

1. List all files created/modified
2. Report test coverage
3. Note any deviations from spec
4. Identify related tasks that are now unblocked
