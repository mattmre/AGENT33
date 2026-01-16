# Phase 23: Additional Export Formats

## Overview
- **Phase**: 23 of 40
- **Category**: Output & Export
- **Release Target**: v1.1
- **Estimated Sprints**: 2

## Objectives
Implement additional export formats beyond RSMF and PDF for various use cases.

---

## Features (12 items)

### 23.1 HTML Export
**Priority**: P0 | **Complexity**: Medium
- Self-contained HTML
- Embedded CSS/images
- Interactive features
- Mobile responsive

### 23.2 Static HTML Generation
**Priority**: P0 | **Complexity**: Medium
- Generate HTML pages
- Include navigation
- Support multi-file
- Print-friendly CSS

### 23.3 CSV Export
**Priority**: P0 | **Complexity**: Low
- Configurable columns
- Handle multiline text
- Proper escaping
- UTF-8 BOM option

### 23.4 Excel Export
**Priority**: P1 | **Complexity**: Medium
- XLSX format
- Multiple worksheets
- Formatted cells
- Include metadata sheet

### 23.5 JSON Export
**Priority**: P1 | **Complexity**: Low
- Full data export
- Formatted/compact options
- Include metadata
- Stream large files

### 23.6 XML Export
**Priority**: P2 | **Complexity**: Medium
- Custom schema
- Configurable structure
- Include attachments
- Validate output

### 23.7 Load File Export
**Priority**: P1 | **Complexity**: Medium
- Concordance DAT format
- Opticon OPT format
- Relativity load file
- Custom delimiters

### 23.8 EML Export (Individual)
**Priority**: P1 | **Complexity**: Medium
- One EML per message
- Include attachments
- Proper threading
- Email-compatible

### 23.9 Plaintext Export
**Priority**: P1 | **Complexity**: Low
- Simple text format
- Configurable layout
- Include timestamps
- Handle media refs

### 23.10 Export Format Plugin System
**Priority**: P2 | **Complexity**: Medium
- Custom format plugins
- Plugin interface
- Registration system
- Documentation

### 23.11 Bulk Export Manager
**Priority**: P1 | **Complexity**: Medium
- Multi-format export
- Shared configuration
- Progress tracking
- Output organization

### 23.12 Export Format Tests
**Priority**: P0 | **Complexity**: Medium
- Test all formats
- Validate outputs
- Edge case coverage
- Round-trip tests

---

## Acceptance Criteria

- [ ] All export formats functional
- [ ] Output is valid for format
- [ ] Handles large files
- [ ] Bulk export works
- [ ] Documentation complete
- [ ] 90%+ test coverage

---

## Technical Notes

### Export Interface
```python
class Exporter(Protocol):
    format_name: str
    file_extension: str

    def export(self, document: RSMFDocument, output_path: Path, config: ExportConfig) -> None: ...
```

### Load File Format (DAT)
```
þDOCIDþþBEGATTþþENDATTþþTEXTPATHþþNATIVEPATHþ
þDOC001þþIMG001þþIMG005þþTEXT\DOC001.txtþþNATIVE\DOC001.rsmfþ
```

### HTML Template Features
- Collapsible threads
- Search functionality
- Filter by participant
- Date navigation
