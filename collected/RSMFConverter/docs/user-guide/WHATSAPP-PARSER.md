# WhatsApp Parser User Guide

This guide explains how to convert WhatsApp chat exports to RSMF format using RSMFConverter, including comprehensive i18n (internationalization) support for global users.

---

## Table of Contents

1. [Overview](#overview)
2. [Exporting Chats from WhatsApp](#exporting-chats-from-whatsapp)
3. [CLI Command Examples](#cli-command-examples)
4. [Internationalization (i18n) Support](#internationalization-i18n-support)
5. [Supported Date/Time Formats](#supported-datetime-formats)
6. [Supported Languages](#supported-languages)
7. [Calendar Systems](#calendar-systems)
8. [Numeral Systems](#numeral-systems)
9. [Forensic Timestamp Mode](#forensic-timestamp-mode)
10. [Limitations](#limitations)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The WhatsApp parser converts WhatsApp text exports (.txt files) to RSMF format for eDiscovery purposes. It supports:

- Individual and group chat exports
- 20+ languages and regional date formats
- Multiple calendar systems (Gregorian, Buddhist, Persian, Hebrew)
- Non-Western numeral systems (Thai, Arabic-Indic, Persian, Devanagari, Bengali)
- System message detection (encryption notices, join/leave events, calls)
- Media attachment references
- Multi-line messages
- Forensic timestamp preservation

---

## Exporting Chats from WhatsApp

### iOS Export

1. Open WhatsApp and navigate to the chat you want to export
2. Tap the contact/group name at the top
3. Scroll down and tap **Export Chat**
4. Choose **Without Media** (for text-only) or **Attach Media**
5. Select a sharing method (Files, AirDrop, Email, etc.)
6. Save the resulting `.txt` file (and ZIP if media included)

### Android Export

1. Open WhatsApp and navigate to the chat
2. Tap the three-dot menu (top right)
3. Select **More** > **Export chat**
4. Choose **Without Media** or **Include Media**
5. Select where to save the export
6. Save the resulting `.txt` file

### Export File Format

WhatsApp exports are plain text files with timestamps and messages:

```
1/15/24, 9:30 AM - Alice: Hello!
1/15/24, 9:31 AM - Bob: Hi there!
1/15/24, 9:32 AM - Alice: <Media omitted>
```

The exact format varies by language and region.

---

## CLI Command Examples

### Basic Conversion

```bash
# Convert a WhatsApp chat to RSMF
rsmfconverter convert chat.txt -o output.eml

# Specify the format explicitly
rsmfconverter convert chat.txt -o output.eml -f whatsapp
```

### With Timezone

```bash
# Specify the source timezone for accurate UTC conversion
rsmfconverter convert chat.txt -o output.eml --source-timezone "America/New_York"

# Asian timezone
rsmfconverter convert chat.txt -o output.eml --source-timezone "Asia/Tokyo"
```

### With Locale

```bash
# Chinese export
rsmfconverter convert chat.txt -o output.eml --source-locale zh-CN

# German export
rsmfconverter convert chat.txt -o output.eml --source-locale de-DE

# Arabic export
rsmfconverter convert chat.txt -o output.eml --source-locale ar-SA
```

### Combined Options

```bash
# Full specification for a Spanish export from Mexico
rsmfconverter convert chat.txt -o output.eml \
    --source-locale es-MX \
    --source-timezone "America/Mexico_City" \
    --forensic

# Thai Buddhist calendar export
rsmfconverter convert chat.txt -o output.eml \
    --source-locale th-TH \
    --source-timezone "Asia/Bangkok" \
    --forensic
```

### Forensic Mode

```bash
# Enable forensic timestamp preservation
rsmfconverter convert chat.txt -o output.eml --forensic

# Forensic mode with verbose output
rsmfconverter convert chat.txt -o output.eml --forensic --verbose
```

---

## Internationalization (i18n) Support

RSMFConverter provides comprehensive i18n support for WhatsApp exports from around the world.

### Auto-Detection

The parser automatically detects:
- Date format order (MDY, DMY, YMD)
- Character set (Latin, CJK, Arabic, Hebrew, etc.)
- AM/PM indicators in various languages
- System message language
- Numeral systems

```bash
# Auto-detection (usually sufficient for most exports)
rsmfconverter convert chat.txt -o output.eml
```

### Manual Override

For ambiguous cases, specify the locale explicitly:

```bash
# When auto-detection is uncertain
rsmfconverter convert chat.txt -o output.eml --source-locale ja-JP
```

---

## Supported Date/Time Formats

### US Format (en-US)

```
1/15/24, 9:30 AM - Alice: Hello
01/15/2024, 9:30:45 AM - Bob: Hi
```

### European Format (en-GB, de-DE, fr-FR, etc.)

```
15/01/24, 09:30 - Alice: Hello
15.01.2024, 09:30:45 - Bob: Hi
```

### ISO/Asian Format (ja-JP, ko-KR, zh-CN)

```
2024/1/15, 9:30 - Alice: Hello
2024-01-15, 09:30:45 - Bob: Hi
```

### Chinese Format (zh-CN)

```
2024年1月15日 上午9:30 - 爱丽丝: 你好
2024/1/15 下午3:30 - 鲍勃: 嗨
```

### Japanese Format (ja-JP)

```
2024/1/15 午前9:30 - アリス: こんにちは
2024年1月15日 午後3:30 - ボブ: やあ
```

### Korean Format (ko-KR)

```
2024. 1. 15. 오전 9:30 - 앨리스: 안녕하세요
2024.1.15 오후 3:30 - 밥: 안녕
```

### iOS Bracket Format

```
[1/15/24, 9:30:45 AM] Alice: Hello
[15/01/2024, 09:30:45] Bob: Hi
```

---

## Supported Languages

### Tier 1: Full Support

| Language | Locale | Date Order | AM/PM |
|----------|--------|------------|-------|
| English (US) | en-US | MDY | AM/PM |
| English (UK) | en-GB | DMY | am/pm |
| Chinese (Simplified) | zh-CN | YMD | 上午/下午 |
| Chinese (Traditional) | zh-TW | YMD | 上午/下午 |
| Japanese | ja-JP | YMD | 午前/午後 |
| Korean | ko-KR | YMD | 오전/오후 |
| Spanish | es-ES | DMY | a.m./p.m. |
| German | de-DE | DMY | - |
| French | fr-FR | DMY | - |
| Portuguese (Brazil) | pt-BR | DMY | - |

### Tier 2: Good Support

| Language | Locale | Date Order | Notes |
|----------|--------|------------|-------|
| Arabic | ar-SA | DMY | RTL, Arabic-Indic numerals |
| Hebrew | he-IL | DMY | RTL, Hebrew calendar option |
| Hindi | hi-IN | DMY | Devanagari numerals |
| Thai | th-TH | DMY | Thai numerals, Buddhist calendar |
| Russian | ru-RU | DMY | Cyrillic |
| Turkish | tr-TR | DMY | - |
| Italian | it-IT | DMY | - |
| Dutch | nl-NL | DMY | - |
| Polish | pl-PL | DMY | - |
| Persian/Farsi | fa-IR | YMD | Persian calendar, Persian numerals |

---

## Calendar Systems

### Buddhist Calendar (th-TH)

Thai exports often use Buddhist Era (BE) years, which are 543 years ahead of Gregorian:

```
# Thai Buddhist year 2567 = Gregorian 2024
15/1/2567, 09:30 - สมชาย: สวัสดี
```

The parser automatically detects and converts Buddhist years.

### Persian/Jalali Calendar (fa-IR)

Persian exports may use the Solar Hijri calendar:

```
# Persian year 1402 = Gregorian 2023-2024
۲۵/۱۰/۱۴۰۲، ۰۹:۳۰ - علی: سلام
```

### Hebrew Calendar (he-IL)

Hebrew dates are supported with automatic conversion:

```
15 Tevet 5784 = approximately January 2024
```

### Automatic Conversion

Calendar conversion is automatic when:
- Locale is specified (e.g., `--source-locale th-TH`)
- Year values indicate non-Gregorian calendar (e.g., 2567, 1402)

```bash
# Buddhist calendar export
rsmfconverter convert thai_chat.txt -o output.eml --source-locale th-TH

# Persian calendar export
rsmfconverter convert persian_chat.txt -o output.eml --source-locale fa-IR
```

---

## Numeral Systems

The parser supports automatic detection and conversion of non-Western numerals.

### Supported Systems

| System | Digits | Locale |
|--------|--------|--------|
| Western Arabic | 0123456789 | Default |
| Arabic-Indic | ٠١٢٣٤٥٦٧٨٩ | ar-SA |
| Persian | ۰۱۲۳۴۵۶۷۸۹ | fa-IR |
| Thai | ๐๑๒๓๔๕๖๗๘๙ | th-TH |
| Devanagari | ०१२३४५६७८९ | hi-IN |
| Bengali | ০১২৩৪৫৬৭৮৯ | bn-BD |

### Example: Thai Numerals

```
# Original (Thai numerals)
๑๕/๑/๒๕๖๗, ๐๙:๓๐ - สมชาย: สวัสดี

# Automatically converted to:
15/1/2567, 09:30 - สมชาย: สวัสดี
# Then Buddhist year converted to Gregorian 2024
```

### Example: Arabic-Indic Numerals

```
# Original (Arabic-Indic numerals)
١٥/١/٢٠٢٤، ٠٩:٣٠ - أحمد: مرحبا

# Automatically converted to:
15/1/2024, 09:30 - أحمد: مرحبا
```

---

## Forensic Timestamp Mode

Forensic mode preserves the complete audit trail for eDiscovery:

```bash
rsmfconverter convert chat.txt -o output.eml --forensic
```

### What's Captured

| Field | Description |
|-------|-------------|
| `original_string` | Exact timestamp as it appeared in source |
| `detected_format` | The format pattern that matched |
| `parse_confidence` | HIGH, MEDIUM, or LOW |
| `timezone_source` | Where timezone info came from |
| `ambiguities` | Any parsing ambiguities detected |
| `calendar_system` | If non-Gregorian calendar was detected |
| `numeral_system` | If non-Western numerals were detected |

### Example Output (JSON manifest)

```json
{
  "timestamp": "2024-01-15T09:30:00+07:00",
  "forensic": {
    "original_string": "๑๕/๑/๒๕๖๗, ๐๙:๓๐",
    "detected_format": "DMY",
    "parse_confidence": "HIGH",
    "calendar_system": "BUDDHIST",
    "numeral_system": "THAI",
    "conversion_notes": "Buddhist year 2567 converted to Gregorian 2024"
  }
}
```

---

## Limitations

### Not Supported

| Feature | Status | Notes |
|---------|--------|-------|
| Media file extraction | Metadata only | File references preserved, not content |
| End-to-end encryption | N/A | Export is decrypted by WhatsApp |
| Deleted messages | Not visible | Only exported messages included |
| Message reactions | Not in export | WhatsApp doesn't include reactions in TXT export |
| Voice messages | Reference only | Duration shown, audio not included |
| Polls | Partial | Poll question shown, votes may be partial |

### Known Limitations

1. **Ambiguous dates**: Dates like `1/2/24` could be Jan 2 (US) or Feb 1 (EU). Use `--source-locale` to resolve.

2. **Multi-day exports**: Very large exports spanning months may have slight timezone drift.

3. **Group member names**: Names shown as they appear to the exporter; may differ from actual display names.

4. **Edited messages**: Edit history is not preserved in WhatsApp exports.

---

## Troubleshooting

### Wrong Date Order

**Symptom**: Dates appear swapped (e.g., January showing as October)

**Solution**: Specify the correct locale:
```bash
# For European date format (day/month/year)
rsmfconverter convert chat.txt -o output.eml --source-locale en-GB

# For US format (month/day/year)
rsmfconverter convert chat.txt -o output.eml --source-locale en-US
```

### Garbled Characters

**Symptom**: Non-Latin characters appear as `???` or boxes

**Solution**: Ensure the export file is UTF-8 encoded. If not:
```bash
# Convert encoding first (Linux/Mac)
iconv -f ISO-8859-1 -t UTF-8 chat.txt > chat_utf8.txt
rsmfconverter convert chat_utf8.txt -o output.eml
```

### Timestamps Off by Hours

**Symptom**: All timestamps are shifted by a fixed number of hours

**Solution**: Specify the correct source timezone:
```bash
rsmfconverter convert chat.txt -o output.eml --source-timezone "Europe/London"
```

### Buddhist/Persian Year Not Converting

**Symptom**: Year shows as 2567 or 1402 instead of 2024

**Solution**: Specify the locale with calendar system:
```bash
# Thai Buddhist
rsmfconverter convert chat.txt -o output.eml --source-locale th-TH

# Persian
rsmfconverter convert chat.txt -o output.eml --source-locale fa-IR
```

### Parser Not Detecting Format

**Symptom**: "No supported format detected" error

**Possible causes**:
1. File is not a WhatsApp export (check format)
2. Unusual date format not yet supported
3. File encoding issues

**Solution**: Use verbose mode to diagnose:
```bash
rsmfconverter convert chat.txt -o output.eml --verbose
```

### Empty Output

**Symptom**: RSMF output has 0 messages

**Possible causes**:
1. Export file contains only system messages
2. Timestamp format not recognized
3. Encoding issues

**Solution**:
1. Check export has actual messages
2. Try specifying locale explicitly
3. Check file encoding

---

## Best Practices

### For eDiscovery

1. **Always use `--forensic` mode** to preserve original timestamps
2. **Document the source timezone** in your case notes
3. **Keep the original export file** alongside the RSMF output
4. **Verify message counts** match between source and output

### For International Exports

1. **Identify the locale first** by examining date formats and language
2. **Specify locale explicitly** for ambiguous cases
3. **Use forensic mode** to capture calendar/numeral conversions
4. **Verify a sample of timestamps** after conversion

### For Large Exports

1. **Use verbose mode** to monitor progress
2. **Consider splitting** very large exports by date
3. **Check for warnings** about parsing failures

---

## Related Documentation

- [I18N CLI Options Guide](./I18N-CLI-OPTIONS.md) - Detailed i18n configuration
- [Slack Parser Guide](./SLACK-PARSER.md) - For Slack exports
- [Teams Parser Guide](./TEAMS-PARSER.md) - For Microsoft Teams exports
- [Phase 9 Specification](../phases/PHASE-09-WHATSAPP-PARSER.md) - Technical details

---

*Last Updated: 2026-01-16*
*RSMFConverter Version: 0.1.0*
