# Phase 1 API Documentation

This document provides comprehensive API documentation for all modules implemented in Phase 1 of RSMFConverter.

**Version**: 1.0.0
**Phase**: 1 - Project Foundation
**Last Updated**: 2026-01-13

---

## Table of Contents

1. [Overview](#overview)
2. [Module Structure](#module-structure)
3. [Core Module](#core-module)
   - [Exceptions](#exceptions)
   - [Types](#types)
4. [Utils Module](#utils-module)
   - [ID Utilities](#id-utilities)
   - [DateTime Utilities](#datetime-utilities)
   - [File Utilities](#file-utilities)
   - [String Utilities](#string-utilities)
5. [Config Module](#config-module)
   - [Settings](#settings)
   - [Loader](#loader)
6. [Logging Module](#logging-module)
   - [Logger](#logger)
   - [Formatters](#formatters)
   - [Handlers](#handlers)
7. [CLI Module](#cli-module)
8. [Exception Hierarchy](#exception-hierarchy)
9. [Usage Examples](#usage-examples)

---

## Overview

Phase 1 establishes the foundational infrastructure for RSMFConverter, including:

- **Core types and exceptions** for consistent error handling
- **Utility functions** for common operations (IDs, dates, files, strings)
- **Configuration management** with environment variable support
- **Structured logging** with JSON and colored console output
- **CLI skeleton** with Typer framework

All modules follow Google-style docstrings and are fully type-annotated.

---

## Module Structure

```
src/rsmfconverter/
|-- __init__.py
|-- core/
|   |-- __init__.py
|   |-- exceptions.py      # Exception hierarchy
|   |-- types.py           # Type definitions, enums, protocols
|-- utils/
|   |-- __init__.py
|   |-- id_utils.py        # ID generation
|   |-- datetime_utils.py  # Date/time handling
|   |-- file_utils.py      # File operations
|   |-- string_utils.py    # String manipulation
|-- config/
|   |-- __init__.py
|   |-- settings.py        # Pydantic settings model
|   |-- loader.py          # Configuration loading
|-- logging/
|   |-- __init__.py
|   |-- logger.py          # Logger setup
|   |-- formatters.py      # Log formatters
|   |-- handlers.py        # Log handlers
|-- cli/
|   |-- __init__.py
|   |-- main.py            # CLI entry point
```

---

## Core Module

### Exceptions

**Module**: `rsmfconverter.core.exceptions`

All custom exceptions inherit from `RSMFConverterError`, enabling catch-all handling while maintaining specific error types.

#### RSMFConverterError

```python
class RSMFConverterError(Exception):
    """Base exception for all RSMFConverter errors."""

    def __init__(self, message: str, cause: Exception | None = None) -> None
```

**Parameters**:
- `message` (str): Human-readable error description
- `cause` (Exception | None): Optional underlying exception

**Attributes**:
- `message`: The error message
- `cause`: The underlying cause (if any)

**Example**:
```python
from rsmfconverter.core.exceptions import RSMFConverterError

try:
    raise RSMFConverterError("Something went wrong")
except RSMFConverterError as e:
    print(e.message)  # "Something went wrong"
```

#### ConfigurationError

```python
class ConfigurationError(RSMFConverterError):
    """Raised when there is a configuration-related error."""
```

**Use for**: Invalid configuration values, missing required config, parsing errors.

#### ParserError

```python
class ParserError(RSMFConverterError):
    """Base exception for all parser-related errors."""

    def __init__(
        self,
        message: str,
        file_path: Path | str | None = None,
        cause: Exception | None = None,
    ) -> None
```

**Additional Attributes**:
- `file_path` (Path | None): Path to the file being parsed

#### ParseError

```python
class ParseError(ParserError):
    """Raised when an error occurs during parsing."""

    def __init__(
        self,
        message: str,
        file_path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
        cause: Exception | None = None,
    ) -> None
```

**Additional Attributes**:
- `line` (int | None): Line number where error occurred
- `column` (int | None): Column number where error occurred

**Example**:
```python
from rsmfconverter.core.exceptions import ParseError

raise ParseError(
    "Unexpected token",
    file_path="chat.txt",
    line=42,
    column=15,
)
# Output: Unexpected token [file: chat.txt, line: 42, column: 15]
```

#### ValidationError

```python
class ValidationError(RSMFConverterError):
    """Base exception for all validation-related errors."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        cause: Exception | None = None,
    ) -> None
```

**Additional Attributes**:
- `field` (str | None): Field name that failed validation
- `value` (Any): Value that failed validation

#### WriterError

```python
class WriterError(RSMFConverterError):
    """Base exception for all writer-related errors."""

    def __init__(
        self,
        message: str,
        output_path: Path | str | None = None,
        cause: Exception | None = None,
    ) -> None
```

**Additional Attributes**:
- `output_path` (Path | None): Path to the output being written

---

### Types

**Module**: `rsmfconverter.core.types`

#### Type Aliases

```python
JsonDict = dict[str, Any]
"""Type alias for a JSON object (dictionary with string keys)."""

JsonValue = str | int | float | bool | None | list[Any] | dict[str, Any]
"""Type alias for any valid JSON value."""

PathLike = str | Path
"""Type alias for path-like input (string or Path object)."""

MessageId = str
"""Type alias for message identifiers."""

ParticipantId = str
"""Type alias for participant identifiers."""

ConversationId = str
"""Type alias for conversation identifiers."""
```

#### Enums

##### Platform

```python
class Platform(StrEnum):
    """Supported messaging platforms."""
    WHATSAPP = "whatsapp"
    SLACK = "slack"
    TEAMS = "teams"
    IMESSAGE = "imessage"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    FACEBOOK = "facebook"
    SMS = "sms"
    GENERIC = "generic"
```

##### EventType

```python
class EventType(StrEnum):
    """Types of events that can occur in a conversation."""
    MESSAGE = "message"
    JOIN = "join"
    LEAVE = "leave"
    REACTION = "reaction"
    ATTACHMENT = "attachment"
    EDIT = "edit"
    DELETE = "delete"
    READ_RECEIPT = "read_receipt"
    CALL = "call"
    SYSTEM = "system"
```

##### ConversationType

```python
class ConversationType(StrEnum):
    """Types of conversations."""
    DIRECT = "direct"
    GROUP = "group"
    CHANNEL = "channel"
```

##### AttachmentType

```python
class AttachmentType(StrEnum):
    """Types of attachments."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    STICKER = "sticker"
    CONTACT = "contact"
    LOCATION = "location"
    LINK = "link"
    OTHER = "other"
```

##### Severity

```python
class Severity(StrEnum):
    """Severity levels for validation results and logging."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
```

#### Protocols

##### Serializable

```python
@runtime_checkable
class Serializable(Protocol):
    """Protocol for objects that can be serialized to/from dictionaries."""

    def to_dict(self) -> JsonDict: ...

    @classmethod
    def from_dict(cls, data: JsonDict) -> Serializable: ...
```

##### Parser

```python
@runtime_checkable
class Parser(Protocol):
    """Protocol for parser implementations."""

    def parse(self, source: Path) -> Any: ...
```

##### Writer

```python
@runtime_checkable
class Writer(Protocol):
    """Protocol for writer implementations."""

    def write(self, document: Any, output: Path) -> None: ...
```

##### Validator

```python
@runtime_checkable
class Validator(Protocol):
    """Protocol for validator implementations."""

    def validate(self, document: Any) -> list[Any]: ...
```

#### TypedDicts

```python
class ParticipantDict(TypedDict, total=False):
    """TypedDict for participant JSON structure."""
    id: str
    display: str
    email: str | None
    avatar: str | None
    account_id: str | None
    custom: dict[str, Any] | None

class ConversationDict(TypedDict, total=False):
    """TypedDict for conversation JSON structure."""
    id: str
    platform: str
    type: str
    participants: list[str]
    custodian: str | None
    custom: dict[str, Any] | None
    icon: str | None

class EventDict(TypedDict, total=False):
    """TypedDict for event JSON structure."""
    id: str
    conversation_id: str
    timestamp: str
    type: str
    sender_id: str | None
    content: str | None
    attachments: list[dict[str, Any]] | None
    reactions: list[dict[str, Any]] | None
    parent_id: str | None
    custom: dict[str, Any] | None

class ManifestDict(TypedDict, total=False):
    """TypedDict for RSMF manifest JSON structure."""
    version: str
    generator: str
    generated_at: str
    participants: list[ParticipantDict]
    conversations: list[ConversationDict]
    events: list[EventDict]
    attachments: list[dict[str, Any]] | None
    custom: dict[str, Any] | None
```

---

## Utils Module

**Module**: `rsmfconverter.utils`

### ID Utilities

**Module**: `rsmfconverter.utils.id_utils`

#### generate_uuid

```python
def generate_uuid() -> str:
    """Generate a random UUID4.

    Returns:
        UUID string in standard format (36 characters with 4 hyphens).
    """
```

**Example**:
```python
from rsmfconverter.utils import generate_uuid

id = generate_uuid()
# e.g., "550e8400-e29b-41d4-a716-446655440000"
```

#### generate_short_id

```python
def generate_short_id(length: int = 8) -> str:
    """Generate a short random ID using cryptographically secure random bytes.

    Args:
        length: Desired length of the ID (must be even, will be rounded up).

    Returns:
        Random hexadecimal string.
    """
```

**Example**:
```python
from rsmfconverter.utils import generate_short_id

id = generate_short_id(8)   # e.g., "a1b2c3d4"
id = generate_short_id(16)  # e.g., "a1b2c3d4e5f6g7h8"
```

#### hash_id

```python
def hash_id(content: str, length: int = 16) -> str:
    """Generate a deterministic ID based on content hash (SHA-256).

    Args:
        content: Content to hash.
        length: Desired length of the ID (max 64 for SHA-256).

    Returns:
        Deterministic hexadecimal string.
    """
```

**Example**:
```python
from rsmfconverter.utils import hash_id

# Same content always produces the same ID
id1 = hash_id("hello world")  # "b94d27b9934d3e08"
id2 = hash_id("hello world")  # "b94d27b9934d3e08"
assert id1 == id2
```

---

### DateTime Utilities

**Module**: `rsmfconverter.utils.datetime_utils`

#### parse_timestamp

```python
def parse_timestamp(
    value: str | float,
    formats: Sequence[str] | None = None,
    default_tz: timezone | None = None,
) -> datetime:
    """Parse a timestamp string into a datetime object.

    Supports ISO 8601, WhatsApp exports, Slack exports, and Unix timestamps.

    Args:
        value: Timestamp string or numeric Unix timestamp.
        formats: Optional list of strptime formats to try.
        default_tz: Timezone to use if the timestamp has no timezone info.

    Returns:
        Parsed datetime object.

    Raises:
        ValueError: If the timestamp cannot be parsed.
    """
```

**Example**:
```python
from rsmfconverter.utils import parse_timestamp

# ISO 8601
dt = parse_timestamp("2024-01-15T10:30:00Z")

# Unix timestamp
dt = parse_timestamp(1705315800)

# Unix timestamp in milliseconds (auto-detected)
dt = parse_timestamp(1705315800000)

# WhatsApp format
dt = parse_timestamp("[1/15/24, 10:30:00 AM]")
```

#### format_iso8601

```python
def format_iso8601(dt: datetime, include_microseconds: bool = False) -> str:
    """Format a datetime object as an ISO 8601 string in UTC.

    Args:
        dt: Datetime object to format.
        include_microseconds: Whether to include microseconds.

    Returns:
        ISO 8601 formatted string ending with 'Z'.
    """
```

**Example**:
```python
from datetime import datetime, timezone
from rsmfconverter.utils import format_iso8601

dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
format_iso8601(dt)  # "2024-01-15T10:30:00Z"
format_iso8601(dt, include_microseconds=True)  # "2024-01-15T10:30:00.000000Z"
```

#### to_utc

```python
def to_utc(dt: datetime) -> datetime:
    """Convert a datetime to UTC.

    If the datetime is naive (no timezone), it is assumed to be UTC.

    Args:
        dt: Datetime object to convert.

    Returns:
        Datetime in UTC.
    """
```

---

### File Utilities

**Module**: `rsmfconverter.utils.file_utils`

#### ensure_directory

```python
def ensure_directory(path: Path | str) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory.

    Returns:
        Path object for the directory.
    """
```

**Example**:
```python
from rsmfconverter.utils import ensure_directory

output_dir = ensure_directory("/tmp/rsmf_output")
assert output_dir.exists()
```

#### safe_filename

```python
def safe_filename(name: str, replacement: str = "_") -> str:
    """Sanitize a string to be safe for use as a filename.

    Removes characters unsafe across operating systems.
    Limited to 200 characters.

    Args:
        name: The original filename.
        replacement: Character to replace unsafe characters with.

    Returns:
        Sanitized filename.
    """
```

**Example**:
```python
from rsmfconverter.utils import safe_filename

safe_filename("file:with*bad<chars>.txt")  # "file_with_bad_chars_.txt"
safe_filename("  spaces  .txt")  # "spaces.txt"
```

#### get_file_hash

```python
def get_file_hash(
    path: Path | str,
    algorithm: Literal["md5", "sha1", "sha256", "sha512"] = "sha256",
) -> str:
    """Calculate the hash of a file.

    Args:
        path: Path to the file to hash.
        algorithm: Hash algorithm (md5, sha1, sha256, sha512).

    Returns:
        Hexadecimal hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
```

**Example**:
```python
from rsmfconverter.utils import get_file_hash

hash_sha256 = get_file_hash("document.pdf")
hash_md5 = get_file_hash("document.pdf", algorithm="md5")
```

#### atomic_write

```python
def atomic_write(
    path: Path | str,
    content: str | bytes,
    mode: Literal["w", "wb"] = "w",
    encoding: str = "utf-8",
) -> None:
    """Write content to a file atomically.

    Uses temp file + rename pattern for atomic operation.
    Parent directories are created automatically.

    Args:
        path: Target file path.
        content: Content to write.
        mode: Write mode ('w' for text, 'wb' for binary).
        encoding: Text encoding (only for text mode).

    Raises:
        OSError: If the file cannot be written.
        PermissionError: If write permission is denied.
    """
```

**Example**:
```python
from rsmfconverter.utils import atomic_write

atomic_write("config.json", '{"key": "value"}')
atomic_write("data.bin", b"binary data", mode="wb")
```

#### detect_encoding

```python
def detect_encoding(path: Path | str, sample_size: int = 8192) -> str:
    """Detect the character encoding of a file.

    Detection order: BOM markers -> UTF-8 validation -> latin-1 fallback.

    Args:
        path: Path to the file to analyze.
        sample_size: Number of bytes to sample.

    Returns:
        Encoding name (utf-8, utf-8-sig, utf-16-le, utf-16-be, latin-1).

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
```

---

### String Utilities

**Module**: `rsmfconverter.utils.string_utils`

#### normalize_whitespace

```python
def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in a string.

    Replaces all whitespace sequences with single space and strips edges.

    Args:
        text: Input string.

    Returns:
        String with normalized whitespace.
    """
```

**Example**:
```python
from rsmfconverter.utils import normalize_whitespace

normalize_whitespace("  hello   world  ")  # "hello world"
```

#### truncate

```python
def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate a string to a maximum length.

    Args:
        text: Input string.
        max_length: Maximum length of the result (including suffix).
        suffix: String to append when truncating.

    Returns:
        Truncated string.
    """
```

**Example**:
```python
from rsmfconverter.utils import truncate

truncate("Hello, World!", 10)  # "Hello, ..."
truncate("Hello", 10)  # "Hello" (no truncation needed)
```

#### strip_html_tags

```python
def strip_html_tags(html: str) -> str:
    """Remove HTML tags from a string.

    Also decodes common HTML entities (&amp;, &lt;, &gt;, &nbsp;, etc.).

    Args:
        html: HTML string.

    Returns:
        Plain text with HTML tags removed.
    """
```

**Example**:
```python
from rsmfconverter.utils import strip_html_tags

strip_html_tags("<p>Hello <b>World</b>!</p>")  # "Hello World!"
strip_html_tags("&lt;script&gt;")  # "<script>"
```

#### normalize_unicode

```python
def normalize_unicode(
    text: str,
    form: Literal["NFC", "NFD", "NFKC", "NFKD"] = "NFC"
) -> str:
    """Normalize Unicode text.

    Args:
        text: Input string.
        form: Unicode normalization form.

    Returns:
        Normalized string.
    """
```

#### slugify

```python
def slugify(text: str, separator: str = "-", lowercase: bool = True) -> str:
    """Convert text to a URL-friendly slug.

    Args:
        text: Input string.
        separator: Character to use between words.
        lowercase: Whether to convert to lowercase.

    Returns:
        URL-friendly slug.
    """
```

**Example**:
```python
from rsmfconverter.utils import slugify

slugify("Hello World!")  # "hello-world"
slugify("Cafe Resume", separator="_")  # "cafe_resume"
```

---

## Config Module

**Module**: `rsmfconverter.config`

### Settings

**Module**: `rsmfconverter.config.settings`

```python
class Settings(BaseSettings):
    """Application settings with Pydantic validation.

    Settings are loaded from (in order, later overrides earlier):
    1. Default values
    2. Configuration file (YAML)
    3. Environment variables (prefixed with RSMFCONVERTER_)

    Attributes:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log output format ("json" or "text")
        log_file: Optional path to log file
        output_dir: Default output directory
        temp_dir: Temporary directory (None for system default)
        rsmf_version: RSMF version to generate ("1.0" or "2.0")
        validation_strict: Enable strict validation mode
        max_workers: Maximum number of worker threads (1-32)
        chunk_size: Processing chunk size for large files (100-100000)
    """
```

**Example**:
```python
from rsmfconverter.config import Settings

# Using defaults
settings = Settings()
print(settings.log_level)  # "INFO"

# Override via environment
import os
os.environ["RSMFCONVERTER_LOG_LEVEL"] = "DEBUG"
settings = Settings()
print(settings.log_level)  # "DEBUG"
```

### Loader

**Module**: `rsmfconverter.config.loader`

#### find_config_file

```python
def find_config_file() -> Path | None:
    """Find a configuration file in standard locations.

    Search order:
    1. ./rsmfconverter.yaml or ./rsmfconverter.yml
    2. ./.rsmfconverter.yaml or ./.rsmfconverter.yml
    3. ~/.config/rsmfconverter/config.yaml or config.yml

    Returns:
        Path to configuration file if found, None otherwise.
    """
```

#### load_config

```python
def load_config(config_path: Path | str | None = None) -> Settings:
    """Load configuration from file and environment.

    Args:
        config_path: Optional explicit path to configuration file.

    Returns:
        Settings object with loaded configuration.
    """
```

**Example**:
```python
from rsmfconverter.config import load_config

# Auto-discover config file
settings = load_config()

# Explicit config file
settings = load_config("custom_config.yaml")
```

---

## Logging Module

**Module**: `rsmfconverter.logging`

### Logger

**Module**: `rsmfconverter.logging.logger`

#### get_logger

```python
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance under the rsmfconverter namespace.

    Args:
        name: Logger name (will be prefixed with 'rsmfconverter.').

    Returns:
        Logger instance.
    """
```

**Example**:
```python
from rsmfconverter.logging import get_logger

logger = get_logger("parsers.whatsapp")
logger.info("Parsing WhatsApp export")
# Logger name: "rsmfconverter.parsers.whatsapp"
```

#### setup_logging

```python
def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Path | str | None = None,
    console: bool = True,
) -> None:
    """Configure logging for the application.

    Call once at application startup.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_format: Use JSON format for structured logging.
        log_file: Optional path to log file (always uses JSON format).
        console: Enable console output.
    """
```

**Example**:
```python
from rsmfconverter.logging import setup_logging

# Basic setup
setup_logging(level="DEBUG")

# JSON logging to file
setup_logging(level="INFO", json_format=True, log_file="app.log")
```

### Formatters

**Module**: `rsmfconverter.logging.formatters`

#### JSONFormatter

```python
class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging.

    Output fields: timestamp, level, logger, message, location, exception.
    """
```

**Example output**:
```json
{
  "timestamp": "2024-01-15T10:30:00+00:00",
  "level": "INFO",
  "logger": "rsmfconverter.parsers",
  "message": "Processing file",
  "location": {
    "file": "/path/to/parser.py",
    "line": 42,
    "function": "parse"
  }
}
```

#### ColoredFormatter

```python
class ColoredFormatter(logging.Formatter):
    """Colored console formatter for human-readable output.

    Color mapping:
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Magenta

    Args:
        use_colors: Force colors on/off. None for auto-detect based on TTY.
    """
```

### Handlers

**Module**: `rsmfconverter.logging.handlers`

#### create_rotating_file_handler

```python
def create_rotating_file_handler(
    path: Path,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    encoding: str = "utf-8",
) -> RotatingFileHandler:
    """Create a rotating file handler with sensible defaults.

    Creates parent directories automatically.

    Args:
        path: Path to the log file.
        max_bytes: Maximum file size before rotation (default 10 MB).
        backup_count: Number of backup files to keep (default 5).
        encoding: File encoding (default UTF-8).

    Returns:
        Configured RotatingFileHandler.
    """
```

---

## CLI Module

**Module**: `rsmfconverter.cli.main`

The CLI is built with Typer and provides the following commands:

### Commands

#### convert

```
rsmfconverter convert INPUT_PATH [OPTIONS]

Convert a messaging export to RSMF format.

Arguments:
  INPUT_PATH  Path to the input file or directory [required]

Options:
  -o, --output PATH       Output path for the RSMF file
  -f, --format TEXT       Input format (auto-detected if not specified)
  --rsmf-version TEXT     RSMF version to generate [default: 2.0]
  --skip-validate         Skip validation after conversion
```

#### validate-rsmf

```
rsmfconverter validate-rsmf INPUT_PATH [OPTIONS]

Validate an RSMF file against the specification.

Arguments:
  INPUT_PATH  Path to the RSMF file to validate [required]

Options:
  --lenient  Use lenient validation rules instead of strict
```

#### info

```
rsmfconverter info INPUT_PATH

Display information about an RSMF file.

Arguments:
  INPUT_PATH  Path to the RSMF file [required]
```

### Global Options

```
--version, -v  Show version and exit
--help         Show help message and exit
```

---

## Exception Hierarchy

```
Exception
|
+-- RSMFConverterError (base for all project exceptions)
    |
    +-- ConfigurationError
    |       Invalid configuration values or parsing errors
    |
    +-- ParserError (base for parser exceptions)
    |   |
    |   +-- UnsupportedFormatError
    |   |       Unknown or unsupported input format
    |   |
    |   +-- ParseError
    |   |       Error during parsing (with line/column info)
    |   |
    |   +-- MalformedInputError
    |           Input file is malformed or corrupted
    |
    +-- ValidationError (base for validation exceptions)
    |   |
    |   +-- SchemaValidationError
    |   |       JSON schema validation failed
    |   |
    |   +-- ReferenceError
    |   |       Invalid reference to participant/conversation
    |   |
    |   +-- IntegrityError
    |           Data integrity issue (e.g., duplicate IDs)
    |
    +-- WriterError (base for writer exceptions)
    |   |
    |   +-- OutputPathError
    |   |       Invalid or inaccessible output path
    |   |
    |   +-- SerializationError
    |           Serialization of data failed
    |
    +-- FileAccessError
    |       File access failed (read/write)
    |
    +-- EncodingError
            Character encoding issues
```

---

## Usage Examples

### Complete Workflow Example

```python
from pathlib import Path
from rsmfconverter.config import load_config
from rsmfconverter.logging import setup_logging, get_logger
from rsmfconverter.utils import (
    generate_uuid,
    parse_timestamp,
    format_iso8601,
    safe_filename,
)
from rsmfconverter.core.types import Platform, EventType
from rsmfconverter.core.exceptions import ParseError

# Setup
config = load_config()
setup_logging(level=config.log_level, json_format=config.log_format == "json")
logger = get_logger("example")

# Use utilities
message_id = generate_uuid()
timestamp = parse_timestamp("2024-01-15T10:30:00Z")
iso_time = format_iso8601(timestamp)
filename = safe_filename("Chat: Project Discussion.txt")

logger.info(
    "Processing message",
    extra={"message_id": message_id, "platform": Platform.WHATSAPP}
)

# Handle errors
try:
    # ... parsing logic ...
    raise ParseError("Unexpected format", file_path="chat.txt", line=10)
except ParseError as e:
    logger.error(f"Parse failed: {e}")
```

### Configuration Example

```yaml
# rsmfconverter.yaml
log_level: DEBUG
log_format: json
log_file: logs/rsmfconverter.log
output_dir: ./output
rsmf_version: "2.0"
validation_strict: true
max_workers: 8
chunk_size: 5000
```

```python
from rsmfconverter.config import load_config

# Load with auto-discovery
config = load_config()

# Or explicit path
config = load_config("rsmfconverter.yaml")
```

---

## See Also

- [PHASE-01-PROJECT-FOUNDATION.md](../phases/PHASE-01-PROJECT-FOUNDATION.md) - Phase 1 implementation details
- [CLAUDE.md](../CLAUDE.md) - Project context and technical decisions
- [00-MASTER-ROADMAP.md](../roadmap/00-MASTER-ROADMAP.md) - Full project roadmap

---

*Generated for RSMFConverter Phase 1*
*Last Updated: 2026-01-13*
