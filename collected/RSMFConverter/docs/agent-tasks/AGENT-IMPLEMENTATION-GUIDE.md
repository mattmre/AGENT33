# AI Agent Implementation Guide

## Overview

This guide provides instructions for AI agents implementing features from the RSMFConverter roadmap. Each phase has been broken down into discrete, implementable features that agents can work on independently.

---

## How to Use This Guide

### 1. Select a Phase
Choose a phase from the roadmap based on:
- Current project status
- Dependencies (earlier phases must be complete)
- Priority level

### 2. Review Phase Document
Each phase document (`docs/phases/PHASE-XX-*.md`) contains:
- Feature list with priorities
- Acceptance criteria
- Technical notes
- Dependencies

### 3. Implement Features
For each feature:
1. Read the feature description
2. Review technical notes
3. Write code following project standards
4. Write comprehensive tests
5. Update documentation

### 4. Verify Completion
- All acceptance criteria met
- Tests pass
- Documentation updated
- Code reviewed

---

## Implementation Standards

### Code Quality
```python
# All code must:
# 1. Have type hints
# 2. Have docstrings
# 3. Follow PEP 8
# 4. Pass linting (ruff)
# 5. Be formatted (black)
```

### Test Coverage
- Minimum 90% coverage for core code
- Minimum 85% for integrations
- 100% coverage for public APIs

### Documentation
- All public functions must have docstrings
- Include examples in docstrings
- Update relevant docs files

---

## Feature Implementation Template

When implementing a feature, follow this structure:

### 1. Understand the Feature
```
Feature: [Feature Name]
Phase: [Phase Number]
Priority: [P0/P1/P2]
Complexity: [Low/Medium/High]

Description: [What the feature does]
```

### 2. Design the Solution
- Review existing code
- Identify affected modules
- Plan the implementation
- Document design decisions

### 3. Implement
```python
# File: src/rsmfconverter/[module]/[file].py

"""Module description."""

from typing import ...

class FeatureName:
    """Feature implementation.

    Attributes:
        ...

    Example:
        >>> feature = FeatureName()
        >>> feature.do_something()
    """

    def method(self) -> ReturnType:
        """Method description."""
        ...
```

### 4. Test
```python
# File: tests/[module]/test_[file].py

import pytest
from rsmfconverter.[module] import FeatureName

class TestFeatureName:
    def test_basic_functionality(self):
        ...

    def test_edge_cases(self):
        ...

    def test_error_handling(self):
        ...
```

### 5. Document
- Update API reference
- Add to user guide if user-facing
- Update changelog

---

## Priority Definitions

### P0 - Critical
- Must be implemented for the phase to be complete
- Core functionality that blocks other features
- Security-critical features

### P1 - High
- Important for full functionality
- Significant user value
- Should be in the release

### P2 - Nice to Have
- Enhances user experience
- Can be deferred if needed
- Lower impact if missing

---

## Dependency Graph

### Foundation (Must be first)
1. Phase 1: Project Foundation
2. Phase 2: Data Models
3. Phase 3: Parser Framework
4. Phase 4: RSMF Writer
5. Phase 5: Validation Engine

### Core Functionality
- Parsers (9-20) can be parallel after Phase 3
- Output (21-24) needs Phase 4
- CLI (6, 28) needs core ready

### Advanced Features
- API (25) needs core functionality
- Web UI (26-27) needs API
- AI (31-32) can be parallel
- Enterprise (36) needs most features

---

## Common Patterns

### Parser Implementation
```python
from rsmfconverter.parsers.base import AbstractParser

@parser_registry.register
class NewFormatParser(AbstractParser):
    name = "new_format"
    supported_formats = ["newformat", "nf"]

    @classmethod
    def can_parse(cls, source: InputSource) -> bool:
        # Detection logic
        ...

    def parse(self, source: InputSource, config: ParserConfig) -> RSMFDocument:
        # Parsing logic
        ...
```

### Exporter Implementation
```python
from rsmfconverter.exporters.base import AbstractExporter

@exporter_registry.register
class NewFormatExporter(AbstractExporter):
    name = "new_format"
    file_extension = ".nf"

    def export(self, document: RSMFDocument, output: Path, config: ExportConfig) -> None:
        # Export logic
        ...
```

### Validator Implementation
```python
from rsmfconverter.validation.base import ValidationRule

@validator_registry.register
class CustomValidationRule(ValidationRule):
    code = "CUSTOM-001"
    severity = Severity.ERROR

    def validate(self, document: RSMFDocument) -> list[ValidationError]:
        # Validation logic
        ...
```

---

## Testing Patterns

### Unit Test
```python
class TestFeature:
    @pytest.fixture
    def feature(self):
        return Feature()

    def test_happy_path(self, feature):
        result = feature.process(valid_input)
        assert result.success

    def test_edge_case(self, feature):
        result = feature.process(edge_input)
        assert result.handled_correctly

    def test_error_case(self, feature):
        with pytest.raises(FeatureError):
            feature.process(invalid_input)
```

### Integration Test
```python
class TestFeatureIntegration:
    def test_end_to_end(self, tmp_path):
        # Setup
        input_file = create_test_input(tmp_path)
        output_file = tmp_path / "output.rsmf"

        # Execute
        result = convert(input_file, output_file)

        # Verify
        assert output_file.exists()
        assert validate(output_file).valid
```

---

## Agent Communication

When working on features:

1. **Start**: Announce which feature you're implementing
2. **Progress**: Report significant milestones
3. **Blockers**: Report any blockers immediately
4. **Complete**: Announce completion with summary

### Example Status Update
```
Feature: WhatsApp TXT Parser
Phase: 9
Status: In Progress

Completed:
- [x] Message line parsing
- [x] Timestamp handling
- [ ] Media file matching (in progress)
- [ ] Reply detection

Blockers: None
ETA: [Next milestone]
```

---

## Resources

### Reference Documentation
- [RSMF Specification](../research/01-RSMF-SPECIFICATION.md)
- [Input Formats](../research/03-INPUT-FORMATS.md)
- [Competitor Analysis](../research/02-COMPETITOR-ANALYSIS.md)

### Code Examples
- Reference implementations in `reference_repos/`
- Test fixtures in `tests/fixtures/`

### External Resources
- [Relativity RSMF Documentation](https://help.relativity.com)
- [Python Best Practices](https://docs.python-guide.org)
