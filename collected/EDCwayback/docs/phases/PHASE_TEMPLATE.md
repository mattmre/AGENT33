# Phase Template for Agent-Driven Development

Use this template to create detailed phase specification files that can drive an agentic orchestration development cycle.

---

## Template Structure

```markdown
# Phase X.Y: [Phase Name]

## Metadata
| Field | Value |
|-------|-------|
| **Phase ID** | X.Y |
| **Category** | [Category Name] |
| **Priority** | Critical/High/Medium/Low |
| **Dependencies** | Phase X.X ([Name]) |
| **Status** | NOT STARTED / IN PROGRESS (X%) / COMPLETE |
| **Estimated Features** | [Number] |

---

## Objective

[1-2 sentence description of what this phase accomplishes]

---

## Prerequisites

Before starting this phase, ensure:
- [ ] [Prerequisite 1]
- [ ] [Prerequisite 2]

Add to `requirements.txt`:
```
[dependency>=version]
```

---

## Features

### Feature X.Y.Z: [Feature Name]
**Target File**: `path/to/file.py` (create/modify)
**Effort**: Small/Medium/Large
**Agent Type**: Implementer/Tester/Documentation/DevOps

[Brief description of what this feature does]

**Implementation**:
```python
# Code example showing target implementation
```

**Acceptance Criteria**:
- [ ] [Criterion 1]
- [ ] [Criterion 2]

**Output Files**:
- `path/to/file1.py`
- `path/to/file2.py`

---

[Repeat for each feature]

---

## Verification Checklist

Before marking this phase complete:
- [ ] All N features implemented
- [ ] [Specific verification item]
- [ ] Tests pass with >90% coverage
- [ ] Documentation complete

---

## Dependencies for Next Phase

Phase X.Z ([Name]) will require:
- [Item from this phase]
- [Item from this phase]
```

---

## Key Elements

### 1. Metadata Table
Always include phase ID, category, priority, dependencies, status, and feature count.

### 2. Prerequisites
List what must be complete before starting and any new dependencies.

### 3. Feature Specification Format

Each feature MUST include:
- **Target File**: Exact path where code should go
- **Effort**: Small (1-2h), Medium (2-4h), Large (4-8h)
- **Agent Type**: Which specialized agent should implement
- **Implementation**: Code example when possible
- **Acceptance Criteria**: Checkable items
- **Output Files**: All files that will be created/modified

### 4. Agent Types

| Agent Type | Use For |
|------------|---------|
| Implementer | Writing new code, features, integrations |
| Tester | Unit tests, integration tests, E2E tests |
| Documentation | Markdown docs, API docs, guides |
| DevOps | CI/CD, deployment, infrastructure |
| Researcher | API analysis, format research, decisions |

### 5. Effort Sizing

| Size | Time | Examples |
|------|------|----------|
| Small | 1-2h | Config options, simple functions, enums |
| Medium | 2-4h | Full modules, integrations, repositories |
| Large | 4-8h | Frameworks, complex features, multi-file |

---

## Best Practices

1. **Be Specific**: Include exact file paths, function signatures, imports
2. **Show Code**: Provide implementation examples where possible
3. **Atomic Features**: Each feature completable in one agent session
4. **Clear Criteria**: Make acceptance criteria checkable (yes/no)
5. **Chain Dependencies**: Note what next phase needs from this one

---

## Example Feature (Good)

```markdown
### Feature 1.2.4: Job Model
**Target File**: `src/db/models/job.py`
**Effort**: Medium
**Agent Type**: Implementer

Define the Job model for tracking capture requests.

**Implementation**:
```python
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[JobStatus] = mapped_column(default=JobStatus.PENDING)
```

**Acceptance Criteria**:
- [ ] JobStatus enum with all states
- [ ] All CSV input fields as columns
- [ ] Indexes on url and status
- [ ] Relationship to artifacts table

**Output Files**:
- `src/db/models/job.py`
```

---

## Example Feature (Bad - Too Vague)

```markdown
### Feature 1.2.4: Job Model
**File**: models.py
**Effort**: Medium

Create a job model with all the fields we need.

**Acceptance Criteria**:
- [ ] Job model works
- [ ] Has necessary fields
```

The bad example lacks:
- Specific file path
- Agent type
- Implementation example
- Specific acceptance criteria
- Output file list
