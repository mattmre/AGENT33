# Internationalization (i18n) CLI Options Guide

This guide covers the internationalization options available in RSMFConverter for processing non-English message exports.

---

## Table of Contents

1. [Overview](#overview)
2. [Locale Options](#locale-options)
3. [Timezone Options](#timezone-options)
4. [Forensic Mode](#forensic-mode)
5. [Supported Locales](#supported-locales)
6. [Numeral Systems](#numeral-systems)
7. [Calendar Systems](#calendar-systems)
8. [Usage Examples](#usage-examples)
9. [Best Practices](#best-practices)

---

## Overview

RSMFConverter includes comprehensive internationalization support for:

- **Locales**: Parse messages in 20+ languages
- **Timezones**: Convert from source timezone to UTC
- **Numerals**: Handle Thai, Arabic-Indic, Persian, and other numeral systems
- **Calendars**: Support for Buddhist, Persian/Jalali, and Hebrew calendars
- **Forensic Mode**: Preserve original timestamp strings for audit trails

---

## Locale Options

### `--source-locale`

Specifies the locale of the source messages. This affects:
- System message detection (join/leave events)
- AM/PM indicator parsing
- Date format interpretation

**Syntax:**
```bash
rsmfconverter convert input.txt -o output.eml --source-locale <locale>
```

**Examples:**
```bash
# Spanish messages
rsmfconverter convert chat_es.txt -o output.eml --source-locale es

# German messages
rsmfconverter convert chat_de.txt -o output.eml --source-locale de

# Chinese (Simplified) messages
rsmfconverter convert chat_zh.txt -o output.eml --source-locale zh-CN

# Japanese messages
rsmfconverter convert chat_ja.txt -o output.eml --source-locale ja
```

### Locale Format

Use BCP 47 locale tags:
- Language only: `en`, `es`, `de`, `fr`, `zh`, `ja`, `ko`
- Language + Region: `en-US`, `en-GB`, `zh-CN`, `zh-TW`, `pt-BR`

---

## Timezone Options

### `--source-timezone`

Specifies the timezone of timestamps in the source file. Timestamps are converted to UTC in the output.

**Syntax:**
```bash
rsmfconverter convert input.txt -o output.eml --source-timezone <tz>
```

**Examples:**
```bash
# US Eastern Time
rsmfconverter convert chat.txt -o output.eml --source-timezone "America/New_York"

# Central European Time
rsmfconverter convert chat.txt -o output.eml --source-timezone "Europe/Berlin"

# Japan Standard Time
rsmfconverter convert chat.txt -o output.eml --source-timezone "Asia/Tokyo"

# China Standard Time
rsmfconverter convert chat.txt -o output.eml --source-timezone "Asia/Shanghai"
```

### Supported Timezones

Uses IANA timezone database (400+ zones). Common zones:

| Region | Timezone ID |
|--------|------------|
| US Eastern | `America/New_York` |
| US Pacific | `America/Los_Angeles` |
| UK | `Europe/London` |
| Germany | `Europe/Berlin` |
| India | `Asia/Kolkata` |
| Japan | `Asia/Tokyo` |
| China | `Asia/Shanghai` |
| Australia | `Australia/Sydney` |

**Full List**: [IANA Time Zone Database](https://www.iana.org/time-zones)

---

## Forensic Mode

### `--forensic`

Enables forensic timestamp mode, which:
- Preserves the original timestamp string from source
- Records the detected format and locale
- Includes confidence scores
- Maintains full audit trail in RSMF custom fields

**Syntax:**
```bash
rsmfconverter convert input.txt -o output.eml --forensic
```

**Example:**
```bash
# Full forensic mode with locale and timezone
rsmfconverter convert chat.txt -o output.eml \
    --forensic \
    --source-locale zh-CN \
    --source-timezone "Asia/Shanghai"
```

### Forensic Custom Fields

When forensic mode is enabled, events include:
- `original_timestamp`: Raw string from source
- `format_detected`: Parsed format pattern
- `locale_detected`: Detected/configured locale
- `confidence`: Parse confidence (0.0-1.0)

---

## Supported Locales

### Full Support (System Messages + Date Patterns)

| Locale | Language | Notes |
|--------|----------|-------|
| `en` | English | Default, US/UK variants |
| `es` | Spanish | Spain + Latin America |
| `de` | German | Germany, Austria, Switzerland |
| `fr` | French | France, Canada, Belgium |
| `it` | Italian | Italy |
| `pt` | Portuguese | Portugal + Brazil |
| `zh-CN` | Chinese (Simplified) | Mainland China |
| `zh-TW` | Chinese (Traditional) | Taiwan, Hong Kong |
| `ja` | Japanese | Japan |
| `ko` | Korean | South Korea |
| `ru` | Russian | Russia |
| `ar` | Arabic | RTL support |
| `hi` | Hindi | India |
| `tr` | Turkish | Turkey |

### Date Pattern Support

| Locale | AM/PM | Date Format |
|--------|-------|-------------|
| `en` | AM/PM | M/D/Y, D/M/Y |
| `zh` | 上午/下午 | Y年M月D日 |
| `ja` | 午前/午後 | Y/M/D |
| `ko` | 오전/오후 | Y. M. D. |
| `ar` | ص/م | D/M/Y (RTL) |
| `hi` | पूर्वाह्न/अपराह्न | D/M/Y |
| `th` | ก่อนเที่ยง/หลังเที่ยง | Thai numerals |

---

## Numeral Systems

The parser automatically converts non-Western numerals in timestamps.

### Supported Systems

| System | Example | Locale |
|--------|---------|--------|
| Western Arabic | 0-9 | Default |
| Arabic-Indic | ٠-٩ | Arabic |
| Persian | ۰-۹ | Persian/Farsi |
| Thai | ๐-๙ | Thai |
| Devanagari | ०-९ | Hindi |
| Bengali | ০-৯ | Bengali |

### Example

Thai numerals are automatically converted:
```
Input:  ๑๕/๐๑/๒๕๖๗ ๑๐:๓๐
Parsed: 15/01/2567 10:30 (Buddhist year)
Output: 2024-01-15T10:30:00Z (Gregorian)
```

---

## Calendar Systems

### Buddhist Calendar (Thailand)

Thai exports often use Buddhist Era (BE = CE + 543).

```bash
# Thai Buddhist calendar
rsmfconverter convert thai_chat.txt -o output.eml \
    --source-locale th \
    --source-timezone "Asia/Bangkok"
```

Example conversion:
- Input: `2567-01-15` (Buddhist)
- Output: `2024-01-15` (Gregorian)

### Persian Calendar (Jalali)

Iranian exports use the Solar Hijri calendar.

```bash
# Persian calendar
rsmfconverter convert persian_chat.txt -o output.eml \
    --source-locale fa \
    --source-timezone "Asia/Tehran"
```

Example conversion:
- Input: `1402-10-25` (Jalali)
- Output: `2024-01-15` (Gregorian)

### Hebrew Calendar

Some Israeli exports use the Hebrew calendar.

```bash
# Hebrew calendar
rsmfconverter convert hebrew_chat.txt -o output.eml \
    --source-locale he \
    --source-timezone "Asia/Jerusalem"
```

---

## Usage Examples

### WhatsApp Chinese Export

```bash
rsmfconverter convert whatsapp_zh.txt -o output.eml \
    --source-locale zh-CN \
    --source-timezone "Asia/Shanghai"
```

### Teams German Export

```bash
rsmfconverter convert teams_de.html -o output.eml \
    -f teams \
    --source-locale de \
    --source-timezone "Europe/Berlin"
```

### Slack Japanese Export

```bash
rsmfconverter convert slack_jp.zip -o output.eml \
    -f slack \
    --source-locale ja \
    --source-timezone "Asia/Tokyo"
```

### Full Forensic Mode

```bash
rsmfconverter convert chat.txt -o output.eml \
    --forensic \
    --source-locale ko \
    --source-timezone "Asia/Seoul" \
    --verbose
```

### Thai Buddhist Calendar

```bash
rsmfconverter convert thai_whatsapp.txt -o output.eml \
    --source-locale th \
    --source-timezone "Asia/Bangkok" \
    --forensic
```

---

## Best Practices

### 1. Always Specify Locale

While auto-detection works in many cases, explicit locale provides best results:

```bash
# Recommended
rsmfconverter convert chat.txt -o output.eml --source-locale es

# Not recommended (relies on auto-detection)
rsmfconverter convert chat.txt -o output.eml
```

### 2. Use Correct Timezone

Specify the timezone where messages were created:

```bash
# User was in Tokyo when sending messages
rsmfconverter convert chat.txt -o output.eml --source-timezone "Asia/Tokyo"
```

### 3. Enable Forensic Mode for Legal Use

For eDiscovery and legal matters, enable forensic mode:

```bash
rsmfconverter convert evidence.txt -o evidence.eml --forensic
```

### 4. Verify Output Timestamps

After conversion, spot-check timestamps:

```bash
rsmfconverter info output.eml | grep timestamp
```

### 5. Handle Mixed Content

For exports with multiple languages, use the dominant language:

```bash
# Mostly Spanish with some English
rsmfconverter convert chat.txt -o output.eml --source-locale es
```

### 6. Debug Parsing Issues

If timestamps aren't parsing correctly:

```bash
rsmfconverter convert chat.txt -o output.eml --debug
```

Look for "Failed to parse timestamp" warnings in the output.

---

## See Also

- [WhatsApp Parser Guide](./WHATSAPP-PARSER.md) - WhatsApp-specific i18n notes
- [Slack Parser Guide](./SLACK-PARSER.md) - Slack export handling
- [Teams Parser Guide](./TEAMS-PARSER.md) - Teams export handling
- [Phase 9A: Internationalization](../phases/PHASE-09A-INTERNATIONALIZATION.md) - Technical details
