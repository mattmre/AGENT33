# Slack Parser User Guide

This guide explains how to convert Slack workspace exports to RSMF format using RSMFConverter.

---

## Table of Contents

1. [Overview](#overview)
2. [Exporting Data from Slack](#exporting-data-from-slack)
3. [Required Files](#required-files)
4. [CLI Command Examples](#cli-command-examples)
5. [Supported Features](#supported-features)
6. [Limitations](#limitations)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The Slack parser converts Slack workspace exports (ZIP archives) to RSMF format for eDiscovery purposes. It supports:

- Public and private channels
- Direct messages (DMs) and group DMs (MPIMs)
- Thread reconstruction
- User mention resolution
- Reactions and file attachments
- Bot and system messages

---

## Exporting Data from Slack

### Standard Workspace Export

Workspace Owners and Admins can export data from Slack:

1. Open your Slack workspace in a web browser
2. Click your workspace name in the top left
3. Select **Settings & administration** > **Workspace settings**
4. Click **Import/Export Data** in the top menu
5. Select the **Export** tab
6. Choose a date range (or export all data)
7. Click **Start Export**
8. Wait for the email notification that your export is ready
9. Download the ZIP file from the provided link

### Enterprise Grid Export (Org Owners)

For Enterprise Grid workspaces:

1. Go to your organization admin dashboard
2. Navigate to **Settings** > **Org Settings** > **Data Exports**
3. Select workspaces to include
4. Choose the date range
5. Start the export and download when ready

### What Gets Exported

| Data Type | Standard Export | Enterprise Export |
|-----------|-----------------|-------------------|
| Public channels | Yes | Yes |
| Private channels | Members only | Yes (with compliance) |
| Direct messages | No | Yes (with compliance) |
| Files | Metadata only | Metadata only |
| User profiles | Yes | Yes |
| Reactions | Yes | Yes |

**Note**: File contents are not included in standard exports. Only file metadata (name, size, type) is preserved.

---

## Required Files

A Slack export ZIP typically contains the following JSON files. The parser can work with exports containing any combination of these files, though having `users.json` and `channels.json` provides the best results:

### Core Files

| File | Description |
|------|-------------|
| `users.json` | All workspace users with profiles |
| `channels.json` | Public channel metadata |

### Optional Files

| File | Description |
|------|-------------|
| `groups.json` | Private channels (if exported) |
| `dms.json` | Direct message metadata |
| `mpims.json` | Multi-party DM (group DM) metadata |
| `integration_logs.json` | App and integration activity |

### Message Files

Messages are stored in channel directories with daily JSON files:

```
slack_export.zip
├── users.json
├── channels.json
├── general/
│   ├── 2024-01-01.json
│   ├── 2024-01-02.json
│   └── 2024-01-03.json
├── engineering/
│   ├── 2024-01-01.json
│   └── 2024-01-02.json
└── random/
    └── 2024-01-01.json
```

Each daily JSON file contains an array of message objects for that channel on that date.

---

## CLI Command Examples

### Basic Conversion

Convert a Slack export to RSMF:

```bash
rsmfconverter convert slack_export.zip -o output.eml
```

### Specifying Format Explicitly

If auto-detection fails, specify the format:

```bash
rsmfconverter convert slack_export.zip -f slack -o output.eml
```

### Verbose Output

See detailed progress information:

```bash
rsmfconverter convert slack_export.zip -o output.eml --verbose
```

### Debug Mode

Enable debug output for troubleshooting:

```bash
rsmfconverter convert slack_export.zip -o output.eml --debug
```

### Overwrite Existing Output

Replace an existing output file:

```bash
rsmfconverter convert slack_export.zip -o output.eml --overwrite
```

### Skip Validation

Skip post-conversion validation (faster but less safe):

```bash
rsmfconverter convert slack_export.zip -o output.eml --skip-validate
```

### Full Example

Complete command with all common options:

```bash
rsmfconverter convert slack_export.zip \
    -o slack_messages.eml \
    -f slack \
    --rsmf-version 2.0 \
    --verbose \
    --overwrite
```

### View Conversion Results

After conversion, inspect the RSMF file:

```bash
rsmfconverter info slack_messages.eml
```

### Validate Output

Verify the RSMF file is valid:

```bash
rsmfconverter validate slack_messages.eml
```

---

## Supported Features

### Message Types

| Feature | Status | Notes |
|---------|--------|-------|
| Standard messages | Supported | Full text content preserved |
| Thread replies | Supported | Linked to parent via thread_ts |
| Broadcast replies | Supported | Included in thread |
| Edited messages | Supported | Edit flag preserved, original not available |
| Deleted messages | Not tracked | Deleted messages not preserved in Slack exports |

### User Features

| Feature | Status | Notes |
|---------|--------|-------|
| User profiles | Supported | Display name, real name, username |
| User mentions | Supported | `<@U123>` resolved to @username |
| Bot users | Supported | Identified and labeled |
| Deleted users | Supported | Marked as deleted |

### Channel Features

| Feature | Status | Notes |
|---------|--------|-------|
| Public channels | Supported | Full message history |
| Private channels | Supported | If included in export |
| Direct messages | Supported | If included in export |
| Group DMs (MPIMs) | Supported | Multi-party conversations |
| Archived channels | Supported | Preserved with archived flag |

### Rich Content

| Feature | Status | Notes |
|---------|--------|-------|
| User mentions | Supported | `<@U123>` -> `@username` |
| Channel mentions | Supported | `<#C123|channel>` -> `#channel` |
| Special mentions | Supported | `@here`, `@channel`, `@everyone` |
| Links | Supported | `<URL|label>` -> label or URL |
| Reactions | Supported | Emoji name and user list |
| File attachments | Metadata only | Name, size, type preserved |

### System Events

| Event | Status | Notes |
|-------|--------|-------|
| Channel join | Supported | Creates JoinEvent |
| Channel leave | Supported | Creates LeaveEvent |
| Channel topic change | Partial | Included as system message |
| Pinned messages | Partial | Included as system message |

---

## Limitations

### Export Limitations

1. **File Contents Not Included**
   - Standard Slack exports only include file metadata
   - Actual file content must be downloaded separately before export
   - Files are represented as attachment references in RSMF

2. **Direct Messages**
   - Standard exports do not include DMs
   - Only Enterprise/Compliance exports include DM content
   - Requires appropriate admin permissions

3. **Private Channel Access**
   - Users can only export private channels they are members of
   - Full private channel export requires Enterprise compliance features

4. **Message History Limits**
   - Free Slack plans have message history limits
   - Older messages may not be available for export

### Parser Limitations

1. **Custom Emoji**
   - Custom emoji are referenced by name only
   - Emoji images are not included in exports

2. **Slack Connect**
   - External user information may be limited
   - Cross-organization metadata may be incomplete

3. **Enterprise Grid**
   - Multi-workspace exports supported but not fully tested
   - Cross-workspace user mapping may require manual verification

4. **Canvases and Lists**
   - Slack Canvases are not included in standard exports
   - Lists and workflows are not exported

5. **Huddles and Clips**
   - Audio/video huddles are not included
   - Clips (video messages) metadata only

### Known Issues

1. **Large Exports**
   - Very large exports (>1GB) may require significant memory
   - Consider splitting by date range if issues occur

2. **Timezone Handling**
   - All Slack timestamps are in UTC
   - No timezone conversion options needed

---

## Troubleshooting

### Common Errors

#### "Could not auto-detect format"

The ZIP file structure was not recognized as a Slack export.

**Solution**: Ensure the ZIP contains `users.json` or `channels.json` at the root level. Use `-f slack` to force format detection.

```bash
rsmfconverter convert export.zip -f slack -o output.eml
```

#### "Invalid ZIP file"

The input file is corrupted or not a valid ZIP archive.

**Solution**: Re-download the export from Slack. Verify the file opens correctly with your system ZIP utility.

#### "users.json not found in export"

The export is missing user information.

**Solution**: This is a warning, not an error. The parser will create placeholder users. For complete user data, ensure you have a full workspace export.

#### "Failed to parse channels.json"

The channels metadata file is malformed.

**Solution**: Check if the export completed successfully in Slack. Re-export if necessary.

#### "Parse error: Invalid JSON in export"

One of the message JSON files is corrupted.

**Solution**: Use `--debug` to identify the specific file causing issues. Re-export or manually fix the JSON.

### Debugging Steps

1. **Enable Debug Mode**
   ```bash
   rsmfconverter convert export.zip -o output.eml --debug
   ```

2. **Check Export Structure**
   Verify your ZIP contains the expected files:
   ```bash
   unzip -l slack_export.zip | head -20
   ```

3. **Validate JSON Files**
   Check that key files are valid JSON:
   ```bash
   python -m json.tool < users.json > /dev/null && echo "Valid"
   ```

4. **Check File Permissions**
   Ensure read access to the export file and write access to output directory.

5. **Memory Issues**
   For large exports, monitor memory usage. Consider processing smaller date ranges.

### Getting Help

If you encounter issues not covered here:

1. Check the [GitHub Issues](https://github.com/agent-33/RSMFConvert/issues) for similar problems
2. Open a new issue with:
   - RSMFConverter version (`rsmfconverter --version`)
   - Slack export size and approximate message count
   - Error message and stack trace (use `--debug`)
   - Steps to reproduce

---

## See Also

- [RSMF Specification](../research/01-RSMF-SPECIFICATION.md) - Technical format details
- [Input Formats](../research/03-INPUT-FORMATS.md) - All supported formats
- [Slack Parser Phase](../phases/PHASE-10-SLACK-PARSER.md) - Technical implementation details
