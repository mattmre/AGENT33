# Phase 9A: Internationalization & Forensic Data Fidelity

## Overview
- **Phase**: 9A (between Phase 9 and Phase 10)
- **Category**: Core Infrastructure Enhancement
- **Release Target**: v0.4.1
- **Estimated Sprints**: 2-3
- **Priority**: CRITICAL - Prerequisite for all subsequent parser phases

## Objectives
Implement comprehensive internationalization (i18n) support and forensic data fidelity guarantees across all parsers. This phase establishes the infrastructure that enables accurate parsing and timestamp handling for messaging data from any locale worldwide.

### Why This Phase is Critical
1. **Forensic Accuracy**: eDiscovery requires timestamps accurate to the second. Incorrect timezone handling can shift evidence by hours.
2. **Global Data**: Organizations collect messaging data from users in 195+ countries using 100+ languages.
3. **Legal Requirements**: Court admissibility requires demonstrable chain of custody and data integrity.
4. **DRY Principle**: Centralizing i18n logic prevents duplication across 15+ parser implementations.

---

## Features (24 items)

### 9A.1 Timezone Infrastructure
**Priority**: P0 | **Complexity**: High
- Universal timezone database integration (IANA/Olson)
- Support all 400+ timezone identifiers
- Historical timezone data (DST changes, political changes)
- Timezone offset parsing: `UTC+8`, `+08:00`, `Asia/Shanghai`
- Automatic DST transition handling
- Timezone ambiguity detection and flagging

### 9A.2 Timestamp Normalization Service
**Priority**: P0 | **Complexity**: High
- Convert any local timestamp to UTC with sub-second precision
- Preserve original timestamp string for forensic audit
- Track source timezone in metadata
- Handle timezone-naive timestamps with configurable defaults
- Support leap seconds (for high-precision forensics)
- Timestamp validation (future dates, unreasonable dates)

### 9A.3 Forensic Metadata Preservation
**Priority**: P0 | **Complexity**: Medium
- Store original raw timestamp string
- Store detected/configured source timezone
- Store conversion confidence level
- Store parsing method used
- Create audit trail for timestamp transformations
- Support RSMF 2.0 custom fields for forensic metadata

### 9A.4 Locale Detection Engine
**Priority**: P0 | **Complexity**: High
- Detect locale from file content patterns
- Detect locale from BOM and encoding
- Detect locale from date format patterns
- Detect locale from system message language
- Confidence scoring for detection
- Manual locale override support

### 9A.5 Date Format Pattern Library
**Priority**: P0 | **Complexity**: High

Support for 50+ date/time format patterns including:

**ISO 8601 Formats:**
- `2024-01-15T10:30:00Z` (UTC)
- `2024-01-15T10:30:00+08:00` (with offset)
- `2024-01-15T10:30:00.123Z` (with milliseconds)

**Regional Formats:**
| Region | Format Example | Pattern |
|--------|----------------|---------|
| US | `1/15/2024 10:30 AM` | `M/D/YYYY h:mm A` |
| US | `01/15/24 10:30:15 AM` | `MM/DD/YY HH:mm:ss A` |
| EU | `15/01/2024 10:30` | `DD/MM/YYYY HH:mm` |
| EU | `15.01.2024 10:30` | `DD.MM.YYYY HH:mm` |
| UK | `15/01/2024 10:30` | `DD/MM/YYYY HH:mm` |
| Japan | `2024/01/15 10:30` | `YYYY/MM/DD HH:mm` |
| China | `2024/1/15 上午10:30` | `YYYY/M/D Ahh:mm` |
| China | `2024年1月15日 10:30` | `YYYY年M月D日 HH:mm` |
| Korea | `2024. 1. 15. 오전 10:30` | `YYYY. M. D. A hh:mm` |
| Germany | `15.01.2024, 10:30` | `DD.MM.YYYY, HH:mm` |
| France | `15/01/2024 10h30` | `DD/MM/YYYY HH\hmm` |
| Spain | `15/01/2024 10:30` | `DD/MM/YYYY HH:mm` |
| Italy | `15/01/2024, 10:30` | `DD/MM/YYYY, HH:mm` |
| Russia | `15.01.2024 10:30` | `DD.MM.YYYY HH:mm` |
| Brazil/Portugal | `15/01/2024 10:30` | `DD/MM/YYYY HH:mm` |
| Arabic | `٢٠٢٤/١/١٥ ١٠:٣٠ ص` | RTL numerals |
| Hebrew | `15/01/2024 10:30` | RTL with LTR dates |
| Hindi | `15/01/2024 10:30` | Devanagari numerals optional |
| Thai | `15/1/2567 10:30` | Buddhist calendar |
| Persian | `۱۴۰۲/۱۰/۲۵ ۱۰:۳۰` | Jalali calendar |

### 9A.6 AM/PM Indicator Patterns
**Priority**: P0 | **Complexity**: Medium

Support AM/PM indicators in 20+ languages:

| Language | AM | PM | Notes |
|----------|----|----|-------|
| English | AM, am, A.M. | PM, pm, P.M. | |
| Chinese (Simplified) | 上午 | 下午 | Placed before time |
| Chinese (Traditional) | 上午 | 下午 | Same as Simplified |
| Japanese | 午前 | 午後 | Placed before time |
| Korean | 오전 | 오후 | Placed before time |
| Arabic | ص | م | Right-to-left |
| Hebrew | לפנה״צ | אחה״צ | Right-to-left |
| Hindi | पूर्वाह्न | अपराह्न | |
| Thai | ก่อนเที่ยง | หลังเที่ยง | |
| Vietnamese | SA | CH | Sáng/Chiều |
| Indonesian | pagi | sore | Morning/Afternoon |
| Turkish | ÖÖ | ÖS | Öğleden önce/sonra |
| Russian | - | - | 24-hour standard |
| German | vorm. | nachm. | Rare, usually 24h |
| French | - | - | 24-hour standard |
| Spanish | a.m. | p.m. | |
| Portuguese | - | - | Usually 24-hour |
| Italian | - | - | Usually 24-hour |
| Dutch | v.m. | n.m. | Rare |
| Polish | - | - | 24-hour standard |

### 9A.7 System Message Pattern Library
**Priority**: P0 | **Complexity**: High

Maintain patterns for system messages in 20+ languages per platform:

**Categories:**
- Encryption/security notices
- Join/leave/add/remove events
- Group creation/modification
- Call events (missed, duration)
- Media omitted indicators
- Message deletion notices
- Read receipts
- Typing indicators
- Location sharing
- Contact sharing

**Implementation:**
```python
class SystemMessagePatterns:
    """Centralized system message pattern registry."""

    ENCRYPTION_NOTICES: dict[str, list[re.Pattern]] = {
        "en": [re.compile(r"messages.*end-to-end encrypted", re.I)],
        "zh-CN": [re.compile(r"此对话及通话内容已加密")],
        "zh-TW": [re.compile(r"此對話及通話內容已加密")],
        "ja": [re.compile(r"メッセージと通話はエンドツーエンドで暗号化")],
        "ko": [re.compile(r"메시지와 통화가 종단 간 암호화")],
        # ... 15+ more languages
    }
```

### 9A.8 Media Omitted Pattern Library
**Priority**: P0 | **Complexity**: Medium

Support "media omitted" patterns in 20+ languages:

| Language | Image | Video | Audio | Media (generic) |
|----------|-------|-------|-------|-----------------|
| English | `<image omitted>` | `<video omitted>` | `<audio omitted>` | `<Media omitted>` |
| Chinese | `<图片已省略>` | `<视频已省略>` | `<音频已省略>` | `<媒体已省略>` |
| Japanese | `<画像は省略されました>` | `<動画は省略されました>` | | |
| Korean | `<이미지 생략됨>` | `<동영상 생략됨>` | | |
| Spanish | `<imagen omitida>` | `<video omitido>` | | `<multimedia omitido>` |
| Portuguese | `<imagem omitida>` | `<vídeo omitido>` | | `<mídia omitida>` |
| German | `<Bild weggelassen>` | `<Video weggelassen>` | | `<Medien weggelassen>` |
| French | `<image non téléchargée>` | `<vidéo non téléchargée>` | | `<fichier multimédia omis>` |
| Italian | `<immagine omessa>` | `<video omesso>` | | `<file multimediale omesso>` |
| Russian | `<изображение пропущено>` | `<видео пропущено>` | | `<медиафайл пропущен>` |
| Arabic | `<تم حذف الصورة>` | `<تم حذف الفيديو>` | | `<تم حذف الوسائط>` |
| Hindi | `<छवि हटा दी गई>` | `<वीडियो हटा दिया गया>` | | |
| Thai | `<ละเว้นรูปภาพ>` | `<ละเว้นวิดีโอ>` | | |
| Turkish | `<görüntü dahil edilmedi>` | `<video dahil edilmedi>` | | |
| Dutch | `<afbeelding weggelaten>` | `<video weggelaten>` | | |
| Polish | `<pominięto obraz>` | `<pominięto wideo>` | | |
| Indonesian | `<gambar dihilangkan>` | `<video dihilangkan>` | | |
| Vietnamese | `<đã bỏ qua hình ảnh>` | `<đã bỏ qua video>` | | |
| Hebrew | `<התמונה הושמטה>` | `<הסרטון הושמט>` | | |

### 9A.9 Join/Leave Event Pattern Library
**Priority**: P0 | **Complexity**: Medium

Support participant change patterns in 20+ languages:

**Join Patterns:**
| Language | Pattern Examples |
|----------|-----------------|
| English | `X joined`, `X was added`, `You added X`, `X joined using this group's invite link` |
| Chinese | `X 已加入`, `X 加入了群组`, `你添加了 X`, `X 通过群组邀请链接加入` |
| Japanese | `X が参加しました`, `X を追加しました` |
| Korean | `X 님이 참여했습니다`, `X 님을 추가했습니다` |
| Spanish | `X se unió`, `Añadiste a X` |
| Portuguese | `X entrou`, `Você adicionou X` |
| German | `X ist beigetreten`, `Du hast X hinzugefügt` |
| French | `X a rejoint`, `Vous avez ajouté X` |

**Leave Patterns:**
| Language | Pattern Examples |
|----------|-----------------|
| English | `X left`, `You removed X`, `X was removed` |
| Chinese | `X 离开了`, `你移除了 X`, `X 退出了群组` |
| Japanese | `X が退出しました` |
| Korean | `X 님이 나갔습니다` |
| Spanish | `X salió`, `Eliminaste a X` |
| Portuguese | `X saiu`, `Você removeu X` |
| German | `X hat die Gruppe verlassen` |
| French | `X est parti`, `Vous avez retiré X` |

### 9A.10 Character Encoding Support
**Priority**: P0 | **Complexity**: Medium
- UTF-8 (with and without BOM)
- UTF-16 LE/BE (with and without BOM)
- UTF-32 LE/BE
- ISO-8859-1 (Latin-1)
- ISO-8859-15 (Latin-9)
- Windows-1252
- GB2312, GBK, GB18030 (Chinese)
- Big5 (Traditional Chinese)
- Shift_JIS, EUC-JP, ISO-2022-JP (Japanese)
- EUC-KR (Korean)
- TIS-620 (Thai)
- Windows-1256 (Arabic)
- Windows-1255 (Hebrew)
- KOI8-R, Windows-1251 (Russian/Cyrillic)

### 9A.11 Right-to-Left (RTL) Language Support
**Priority**: P1 | **Complexity**: Medium
- Arabic script handling
- Hebrew script handling
- Mixed LTR/RTL content (bidirectional text)
- RTL numeral handling (Eastern Arabic numerals)
- Preserve text directionality in RSMF output
- Handle RTL sender names

### 9A.12 Calendar System Support
**Priority**: P1 | **Complexity**: High
- Gregorian (default)
- Buddhist (Thai: 543 year offset)
- Japanese Imperial (Reiwa, Heisei, etc.)
- Persian/Jalali (Solar Hijri)
- Islamic/Hijri (Lunar)
- Hebrew calendar
- Automatic conversion to Gregorian for RSMF

### 9A.13 Numeral System Support
**Priority**: P1 | **Complexity**: Medium
- Western Arabic numerals (0-9)
- Eastern Arabic numerals (٠-٩)
- Persian/Urdu numerals (۰-۹)
- Devanagari numerals (०-९)
- Thai numerals (๐-๙)
- Bengali numerals (০-৯)
- Automatic conversion for timestamp parsing

### 9A.14 ForensicTimestamp Model
**Priority**: P0 | **Complexity**: Medium

New data model for forensic-grade timestamps:

```python
@dataclass(frozen=True)
class ForensicTimestamp:
    """Forensic-grade timestamp with full audit trail."""

    # Normalized UTC timestamp (primary value)
    utc: datetime

    # Original values for forensic audit
    original_string: str
    original_format: str | None

    # Source timezone information
    source_timezone: str | None  # IANA identifier or offset string
    source_timezone_offset: timedelta | None

    # Parsing metadata
    parse_confidence: float  # 0.0 to 1.0
    parse_method: str  # e.g., "regex_pattern_7", "iso8601"
    ambiguous: bool  # True if day/month could be swapped

    # Conversion audit
    conversion_applied: bool
    conversion_note: str | None  # e.g., "DST transition detected"
```

### 9A.15 Locale Configuration
**Priority**: P0 | **Complexity**: Low
- CLI option: `--source-locale` (e.g., `zh-CN`, `ja-JP`, `ar-SA`)
- CLI option: `--source-timezone` (IANA or offset)
- CLI option: `--date-format` (explicit format string)
- Config file support for locale defaults
- Per-source locale overrides
- Environment variable support

### 9A.16 Locale Auto-Detection Heuristics
**Priority**: P1 | **Complexity**: High
- Detect AM/PM language indicator
- Detect date separator (/, ., -)
- Detect date component order (MDY, DMY, YMD)
- Detect year format (2-digit, 4-digit)
- Detect numeral system used
- Detect text directionality
- Machine learning model for confidence scoring (future)

### 9A.17 Forensic Validation Rules
**Priority**: P0 | **Complexity**: Medium
- Timestamp cannot be in the future
- Timestamp cannot be before platform launch date
- Timestamps must be monotonically increasing (with tolerance)
- Flag suspicious timestamp gaps
- Detect clock skew between participants
- Validate timezone consistency within conversation

### 9A.18 Data Fidelity Guarantees
**Priority**: P0 | **Complexity**: Medium
- No data loss during parsing
- Preserve original encoding
- Preserve original line endings
- Preserve whitespace semantics
- Preserve emoji and special characters
- Preserve zero-width characters
- Hash verification of source content

### 9A.19 Parsing Audit Log
**Priority**: P1 | **Complexity**: Medium
- Log every parsing decision
- Log locale detection results
- Log timezone conversions
- Log ambiguity resolutions
- Log fallback behaviors
- Export audit log as JSON

### 9A.20 Unit Conversion Utilities
**Priority**: P2 | **Complexity**: Low
- File size units (KB, MB, GB with locale formatting)
- Duration formatting (locale-aware)
- Number formatting (thousands separator by locale)
- Currency symbols (for payment messages)

### 9A.21 I18n Testing Framework
**Priority**: P0 | **Complexity**: High
- Test fixtures for each supported language
- Automated pattern verification
- Locale-specific edge case tests
- Calendar conversion tests
- RTL rendering tests
- Round-trip encoding tests

### 9A.22 Documentation: Locale Support Matrix
**Priority**: P1 | **Complexity**: Low
- Document supported locales per platform
- Document known limitations
- Document configuration options
- Provide sample data for each locale
- Troubleshooting guide

### 9A.23 Error Messages Localization
**Priority**: P2 | **Complexity**: Medium
- Localized error messages
- Localized validation warnings
- Localized CLI help text
- Support gettext or similar i18n framework

### 9A.24 Performance Optimization
**Priority**: P1 | **Complexity**: Medium
- Lazy loading of locale patterns
- Compiled regex caching
- Locale detection caching
- Memory-efficient pattern storage
- Benchmark suite for i18n overhead

---

## Top 20 Languages Priority List

Based on global usage and eDiscovery relevance:

| Priority | Language | Code | Script | Date Order | Calendar | Notes |
|----------|----------|------|--------|------------|----------|-------|
| 1 | English | en | Latin | MDY/DMY | Gregorian | Primary |
| 2 | Chinese (Simplified) | zh-CN | Han | YMD | Gregorian | 上午/下午 |
| 3 | Chinese (Traditional) | zh-TW | Han | YMD | Gregorian | 上午/下午 |
| 4 | Spanish | es | Latin | DMY | Gregorian | a.m./p.m. |
| 5 | Arabic | ar | Arabic | DMY | Gregorian/Hijri | RTL, ص/م |
| 6 | Portuguese | pt | Latin | DMY | Gregorian | Usually 24h |
| 7 | French | fr | Latin | DMY | Gregorian | Usually 24h |
| 8 | German | de | Latin | DMY | Gregorian | Usually 24h |
| 9 | Japanese | ja | Kanji/Kana | YMD | Gregorian/Imperial | 午前/午後 |
| 10 | Russian | ru | Cyrillic | DMY | Gregorian | 24h standard |
| 11 | Korean | ko | Hangul | YMD | Gregorian | 오전/오후 |
| 12 | Italian | it | Latin | DMY | Gregorian | Usually 24h |
| 13 | Hindi | hi | Devanagari | DMY | Gregorian | Optional numerals |
| 14 | Turkish | tr | Latin | DMY | Gregorian | ÖÖ/ÖS |
| 15 | Vietnamese | vi | Latin | DMY | Gregorian | SA/CH |
| 16 | Thai | th | Thai | DMY | Buddhist (+543) | Thai numerals |
| 17 | Dutch | nl | Latin | DMY | Gregorian | Usually 24h |
| 18 | Polish | pl | Latin | DMY | Gregorian | 24h standard |
| 19 | Indonesian | id | Latin | DMY | Gregorian | pagi/sore |
| 20 | Hebrew | he | Hebrew | DMY | Gregorian/Hebrew | RTL |

---

## Architecture

### Module Structure

```
src/rsmfconverter/
├── i18n/                           # New i18n module
│   ├── __init__.py
│   ├── timezone.py                 # Timezone handling
│   ├── locale.py                   # Locale detection and config
│   ├── patterns/                   # Pattern libraries
│   │   ├── __init__.py
│   │   ├── datetime.py             # Date/time patterns
│   │   ├── ampm.py                 # AM/PM indicators
│   │   ├── system_messages.py      # System message patterns
│   │   ├── media.py                # Media omitted patterns
│   │   └── participants.py         # Join/leave patterns
│   ├── calendars.py                # Calendar conversions
│   ├── numerals.py                 # Numeral system conversions
│   ├── encoding.py                 # Character encoding utilities
│   └── forensic.py                 # ForensicTimestamp model
├── models/
│   └── forensic.py                 # ForensicTimestamp model
└── parsers/
    └── base.py                     # Updated with i18n integration
```

### Integration with Existing Parsers

```python
class AbstractParser:
    """Updated base parser with i18n support."""

    def _parse_timestamp(
        self,
        raw_string: str,
        locale: Locale | None = None,
        source_tz: timezone | None = None,
    ) -> ForensicTimestamp:
        """Parse timestamp with full forensic audit trail."""
        from rsmfconverter.i18n import parse_datetime
        return parse_datetime(raw_string, locale, source_tz)
```

---

## Acceptance Criteria

- [ ] Support all 400+ IANA timezone identifiers
- [ ] Parse date/time formats for top 20 languages
- [ ] Detect AM/PM indicators in 20+ languages
- [ ] Detect system messages in 20+ languages per platform
- [ ] Detect media omitted patterns in 20+ languages
- [ ] Preserve original timestamp strings for forensic audit
- [ ] Convert all timestamps to UTC with sub-second precision
- [ ] Support RTL languages (Arabic, Hebrew)
- [ ] Support non-Gregorian calendars (Buddhist, Persian)
- [ ] Support non-Western numeral systems
- [ ] 95%+ test coverage on i18n module
- [ ] Comprehensive test fixtures for each language
- [ ] Documentation for all supported locales
- [ ] Performance: <1ms overhead per timestamp parse

---

## Dependencies

- **Requires**: Phase 3 (Parser Framework), Phase 9 (WhatsApp Parser base)
- **Python packages**:
  - `pytz` or `zoneinfo` (Python 3.9+ stdlib)
  - `babel` (locale data, optional)
  - `python-dateutil` (parsing utilities)

## Blocks

- Phase 10: Slack Parser
- Phase 11: Teams Parser
- Phase 12-20: All subsequent parsers

---

## Testing Strategy

### Unit Tests
- Test each date format pattern
- Test each AM/PM pattern per language
- Test timezone conversions (including DST transitions)
- Test calendar conversions
- Test numeral system conversions
- Test encoding detection and conversion

### Integration Tests
- Parse real WhatsApp exports in 10+ languages
- Verify forensic metadata preservation
- Verify round-trip accuracy

### Fixtures Required
- Sample messages in each of top 20 languages
- Edge case dates (DST transitions, year boundaries)
- Mixed-locale conversations
- RTL language samples
- Non-Gregorian calendar samples

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Incomplete pattern coverage | High | Medium | Extensible pattern registry, community contributions |
| Timezone edge cases (DST) | High | Medium | Use pytz/zoneinfo with historical data |
| Calendar conversion errors | Medium | Low | Extensive testing, validation rules |
| Performance overhead | Medium | Low | Lazy loading, caching, benchmarks |
| RTL rendering issues | Low | Medium | Preserve directionality markers |

---

## Implementation Priority

### Sprint 1: Core Infrastructure
1. Timezone infrastructure (9A.1)
2. Timestamp normalization service (9A.2)
3. ForensicTimestamp model (9A.14)
4. Locale configuration (9A.15)
5. Basic i18n testing framework (9A.21)

### Sprint 2: Language Patterns
6. Date format pattern library (9A.5)
7. AM/PM indicator patterns (9A.6)
8. System message patterns (9A.7)
9. Media omitted patterns (9A.8)
10. Join/leave patterns (9A.9)

### Sprint 3: Advanced Features
11. Locale detection engine (9A.4)
12. Calendar system support (9A.12)
13. Numeral system support (9A.13)
14. RTL support (9A.11)
15. Character encoding support (9A.10)
16. Forensic metadata preservation (9A.3)

---

## Notes

### Why Not Use Existing i18n Libraries Directly?

1. **Forensic Requirements**: Standard libraries don't preserve original strings or provide audit trails.
2. **Messaging-Specific Patterns**: System messages vary by platform, not just by locale.
3. **Performance**: Generic solutions may be slower than purpose-built pattern matching.
4. **Control**: Need fine-grained control over ambiguity handling and fallbacks.

### Future Enhancements

- Machine learning for locale detection
- Community-contributed pattern packs
- Crowdsourced pattern validation
- Plugin system for custom locales

---

*Last Updated: 2026-01-14*
*Status: PLANNED*
*Prerequisite for: Phases 10-20 (all parser implementations)*
