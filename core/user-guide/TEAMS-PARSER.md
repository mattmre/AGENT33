# Microsoft Teams Parser User Guide

This guide explains how to convert Microsoft Teams eDiscovery exports to RSMF format using RSMFConverter.

---

## Table of Contents

1. [Overview](#overview)
2. [Exporting Data from Teams](#exporting-data-from-teams)
3. [Supported Export Formats](#supported-export-formats)
4. [CLI Command Examples](#cli-command-examples)
5. [Internationalization (i18n)](#internationalization-i18n)
6. [Supported Features](#supported-features)
7. [Limitations](#limitations)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Teams parser converts Microsoft Teams exports from Purview eDiscovery to RSMF format. It supports:

- Channel conversations (public and private)
- Direct messages (1:1 chats)
- Group chats
- Meeting chat transcripts
- Attachment metadata
- System messages (join/leave events)
- Multiple HTML export formats (div-based and table-based)
- Multiple locale/language support via i18n patterns

---

## Exporting Data from Teams

### Microsoft Purview eDiscovery

Teams chat data is exported through Microsoft Purview Compliance Portal:

1. Navigate to the [Microsoft Purview Compliance Portal](https://compliance.microsoft.com)
2. Go to **eDiscovery** > **Content search** or **eDiscovery (Premium)**
3. Create a new search targeting Teams content
4. Select the users/groups and date range
5. Run the search and preview results
6. Export the search results in HTML format
7. Download the export ZIP when ready

### Admin Center Export (Alternative)

For basic exports:

1. Go to the Microsoft Teams Admin Center
2. Navigate to **Analytics & reports** > **Usage reports**
3. Select conversation history export options
4. Download the exported data

### What Gets Exported

| Data Type | eDiscovery Export | Notes |
|-----------|-------------------|-------|
| Channel messages | Yes | Full content |
| Private channels | Yes (with permissions) | Requires eDiscovery |
| Direct messages | Yes (with compliance) | Requires eDiscovery |
| Group chats | Yes | Full content |
| Meeting chats | Yes | Transcript format |
| File attachments | Metadata only | Links preserved |
| Reactions | Partial | May not be exported |
| Read receipts | No | Not included in exports |

---

## Supported Export Formats

The Teams parser supports two HTML formats commonly produced by Microsoft Purview:

### Div-Based Format

The modern format uses `<div class="message">` structure:

```html
<div class="message">
    <div class="message-header">
        <span class="sender">John Doe</span>
        <span class="timestamp">1/15/2024 9:30 AM</span>
    </div>
    <div class="message-body">Hello team!</div>
</div>
```

### Table-Based Format

Older exports may use table structure:

```html
<tr>
    <td>1/15/2024 9:30 AM</td>
    <td>John Doe</td>
    <td>Hello team!</td>
</tr>
```

Both formats are automatically detected and parsed.

### ZIP Archives

Teams exports may contain multiple HTML files in a ZIP archive:

```
teams_export.zip
├── Conversations/
│   ├── Chat_001.html
│   ├── Chat_002.html
│   └── Channel_General.html
└── metadata.json
```

---

## CLI Command Examples

### Basic Conversion

Convert a Teams HTML export to RSMF:

```bash
rsmfconverter convert teams_export.html -o output.eml
```

### Converting ZIP Archive

Convert a ZIP containing multiple Teams exports:

```bash
rsmfconverter convert teams_export.zip -o output.eml
```

### Specifying Format Explicitly

If auto-detection fails, specify the format:

```bash
rsmfconverter convert teams_export.html -f teams -o output.eml
```

### With Source Locale

Specify the source locale for non-English exports:

```bash
rsmfconverter convert teams_export.html -o output.eml --source-locale es
```

### Verbose Output

See detailed progress information:

```bash
rsmfconverter convert teams_export.html -o output.eml --verbose
```

### Debug Mode

Enable debug output for troubleshooting:

```bash
rsmfconverter convert teams_export.html -o output.eml --debug
```

### Full Example

Complete command with all common options:

```bash
rsmfconverter convert teams_export.zip \
    -o teams_messages.eml \
    -f teams \
    --source-locale de \
    --rsmf-version 2.0 \
    --verbose \
    --overwrite
```

### View Conversion Results

After conversion, inspect the RSMF file:

```bash
rsmfconverter info teams_messages.eml
```

### Validate Output

Verify the RSMF file is valid:

```bash
rsmfconverter validate teams_messages.eml
```

---

## Internationalization (i18n)

The Teams parser includes comprehensive internationalization support for parsing exports in multiple languages.

### Supported Languages

The parser supports join/leave detection and system messages in 20+ languages:

- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Chinese Simplified (zh-CN)
- Chinese Traditional (zh-TW)
- Japanese (ja)
- Korean (ko)
- Russian (ru)
- Arabic (ar)
- Hindi (hi)
- Turkish (tr)

### Locale Auto-Detection

The parser automatically detects the locale from content when not specified:

```bash
# Auto-detect locale from content
rsmfconverter convert teams_export.html -o output.eml
```

### Explicit Locale

For best results, specify the source locale explicitly:

```bash
# Spanish export
rsmfconverter convert teams_es.html -o output.eml --source-locale es

# German export
rsmfconverter convert teams_de.html -o output.eml --source-locale de

# Chinese export
rsmfconverter convert teams_zh.html -o output.eml --source-locale zh-CN
```

### Non-Western Numerals

The parser handles non-Western numeral systems in timestamps:

- Thai numerals (๐-๙)
- Arabic-Indic numerals (٠-٩)
- Persian numerals (۰-۹)
- Devanagari numerals (०-९)
- Bengali numerals (০-৯)

### Non-Gregorian Calendars

The parser supports calendar systems used in different regions:

- Buddhist calendar (Thailand, common in Thai exports)
- Persian/Jalali calendar (Iran)
- Hebrew calendar (Israel)

---

## Supported Features

### Message Types

| Feature | Status | Notes |
|---------|--------|-------|
| Standard messages | Supported | Full text content preserved |
| System messages | Supported | Join/leave events detected |
| Edited messages | Partial | Flag preserved if in export |
| Deleted messages | Not tracked | Typically not in exports |

### Participant Features

| Feature | Status | Notes |
|---------|--------|-------|
| Display names | Supported | From message headers |
| Email addresses | Partial | If included in export |
| Metadata participants | Supported | From HTML comments |

### Conversation Features

| Feature | Status | Notes |
|---------|--------|-------|
| Channels | Supported | Public and private |
| Direct messages | Supported | 1:1 conversations |
| Group chats | Supported | Multi-party conversations |
| Meeting chats | Supported | Detected via metadata |

### Attachment Features

| Feature | Status | Notes |
|---------|--------|-------|
| File references | Supported | URL and name preserved |
| Hash-based IDs | Supported | Unique, deterministic IDs |
| File content | Not included | Only metadata in exports |

### System Events

| Event | Status | Notes |
|-------|--------|-------|
| User joined | Supported | Creates JoinEvent (20+ languages) |
| User left | Supported | Creates LeaveEvent (20+ languages) |
| User added | Supported | Via i18n patterns |
| User removed | Supported | Via i18n patterns |

---

## Limitations

### Export Limitations

1. **File Contents Not Included**
   - Teams eDiscovery exports only include file metadata
   - File URLs are preserved but content not embedded
   - Files must be downloaded separately if needed

2. **Reactions Not Exported**
   - Teams reactions are often not included in Purview exports
   - May be available in some export configurations

3. **Thread/Reply Context**
   - Thread relationships are not preserved in current HTML format
   - Messages are parsed as independent events

4. **Read Receipts**
   - Read receipt information is not included in exports

### Parser Limitations

1. **Timestamp Parsing**
   - Unparseable timestamps return epoch (1970-01-01)
   - This is intentional for forensic reproducibility
   - Check for epoch dates to identify parsing issues

2. **Threading Not Supported**
   - HTML exports don't include thread context
   - All messages are parsed without parent references
   - This is a limitation of the export format, not the parser

3. **Locale Detection**
   - Auto-detection may not always be accurate
   - Best results with explicit `--source-locale` option

4. **Large Files**
   - Very large HTML files (>100MB) may require significant memory
   - Consider splitting large exports

### Known Issues

1. **Mixed Language Content**
   - If content mixes multiple languages, specify the dominant locale
   - System messages in non-specified languages may not be detected

2. **Custom Date Formats**
   - Non-standard date formats may not parse correctly
   - Will return epoch timestamp if format is unrecognized

---

## Troubleshooting

### Common Errors

#### "Could not auto-detect format"

The HTML structure was not recognized as a Teams export.

**Solution**: Ensure the HTML contains Teams-specific markers. Use `-f teams` to force format detection.

```bash
rsmfconverter convert export.html -f teams -o output.eml
```

#### "Invalid ZIP file"

The input file is corrupted or not a valid ZIP archive.

**Solution**: Re-download the export from Microsoft Purview. Verify the file opens correctly.

#### "Timestamp parsing failed - using epoch"

A timestamp in the export could not be parsed.

**Solution**: This is expected for malformed timestamps. The parser returns epoch (1970-01-01) as a deterministic fallback. Use `--debug` to see which timestamps failed.

#### "No messages found in export"

The HTML file contains no recognizable message elements.

**Solution**: Verify the HTML contains `<div class="message">` elements or `<tr>` table rows with message data.

### Debugging Steps

1. **Enable Debug Mode**
   ```bash
   rsmfconverter convert export.html -o output.eml --debug
   ```

2. **Check HTML Structure**
   Verify your HTML contains expected elements:
   ```bash
   grep -c "class=\"message\"" teams_export.html
   ```

3. **Verify Encoding**
   Ensure the HTML is UTF-8 encoded:
   ```bash
   file -i teams_export.html
   ```

4. **Check ZIP Contents**
   For ZIP archives:
   ```bash
   unzip -l teams_export.zip | head -20
   ```

5. **Memory Issues**
   For large exports, monitor memory usage. Consider processing individual HTML files.

### Getting Help

If you encounter issues not covered here:

1. Check the [GitHub Issues](https://github.com/<owner>/RSMFConvert/issues) for similar problems
2. Open a new issue with:
   - RSMFConverter version (`rsmfconverter --version`)
   - Teams export source (Purview, Admin Center, etc.)
   - Error message and stack trace (use `--debug`)
   - Sample of the problematic HTML (anonymized)

---

## See Also

- [RSMF Specification](../research/01-RSMF-SPECIFICATION.md) - Technical format details
- [Input Formats](../research/03-INPUT-FORMATS.md) - All supported formats
- [Teams Parser Phase](../phases/PHASE-11-TEAMS-PARSER.md) - Technical implementation details
- [i18n CLI Options Guide](./I18N-CLI-OPTIONS.md) - Detailed i18n options reference
