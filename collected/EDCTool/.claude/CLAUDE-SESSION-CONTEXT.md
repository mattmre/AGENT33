# EDCTool - Claude Session Context

**Last Updated**: 2026-01-13
**Primary Repo**: `D:\GITHUB\EDCTool`
**Current Branch**: `master` (after PR #81 and #82 merge)

---

## Project Overview

EDCToolkit is a Windows Forms eDiscovery data processing tool (.NET 8.0) for handling DAT/CSV/DII files, data transformations, and exports.

### Repository Structure
```
D:\GITHUB\EDCTool\
├── WindowsFormsApplication19/     # Main WinForms application
│   ├── Main.cs                    # Main form (954+ lines - refactoring target)
│   ├── Import.cs                  # File import with async methods
│   ├── Export.cs                  # File export with async/silentMode
│   ├── DatFile.cs                 # DAT file processing with silentMode
│   ├── Services/                  # DI services
│   └── MVP/                       # Model-View-Presenter infrastructure
├── EDCToolkit.Tests/              # xUnit test project (154 tests)
│   ├── Phase2_Async/              # Async operation tests
│   ├── Core/                      # Core operation tests
│   └── DataOperations/            # Data operation tests
├── .claude/                       # Claude Code configuration
│   ├── plans/                     # Implementation plans (NEW)
│   │   └── phase3-mvp-architecture.md  # Active Phase 3 plan
│   └── sessions/                  # Session logs
├── .github/workflows/             # CI/CD
└── Documentation (*.md files)
```

---

## Modernization Status

### Phase 1 - Security & Infrastructure (COMPLETE)
- SQL Injection fixed with parameterized queries
- Hardcoded credentials removed (User Secrets)
- Dependency Injection infrastructure
- Logging system (Microsoft.Extensions.Logging)
- PR #77 merged to master

### Phase 2 - Async I/O & Testing (COMPLETE)
- Async methods: ImportCSVAsync, ImportDIIAsync, ExportCSVAsync, ExportExcelAsync
- Application.DoEvents() anti-pattern fixed
- silentMode testability pattern implemented (DatFile + Export)
- DisposeAsync for StreamWriter (PR #81)
- 154 tests passing without UI popups
- PR #79, #81, #82 merged to master

### Phase 3 - MVP Architecture (IN PROGRESS)
- **Plan Document**: `.claude/plans/phase3-mvp-architecture.md`
- Goal: Extract presenters from Main.cs (954 lines → ~300 lines)
- Pattern: Model-View-Presenter (MVP)
- Status: Design phase

---

## Active Plan: Phase 3 MVP Architecture

**Reference**: `.claude/plans/phase3-mvp-architecture.md`

### Implementation Waves

1. **Wave 1 (Design)**: MVP interfaces, analyze Main.cs extraction candidates
2. **Wave 2 (Infrastructure)**: Base classes, services (IProgressReporter, IMessageService)
3. **Wave 3 (Extraction)**: ToolbarPresenter, MenuPresenter, tests
4. **Wave 4 (Forms)**: Combine.cs, ExportDialog.cs, DAT2TXT.cs

### Key Deliverables
- `/Presenters/` folder with MVP infrastructure
- Main.cs reduced from 954 → ~300 lines
- 80%+ test coverage on presenter logic

---

## Current State (2026-01-13)

### Recent Completions
- PR #82 merged: silentMode pattern extended to Export class
- PR #81 merged: DisposeAsync for StreamWriter disposal
- Both PRs rebased cleanly onto master

### Test Status
- **154 tests passing**
- Run with: `rm -rf /tmp/EDCToolkit_Tests && dotnet test EDCToolkit.Tests`

### Branch Status
- `master`: Up to date with all changes
- Old branches cleaned up (pr82-clean, pr81-clean, feature/test-silentmode-improvements)

---

## Key Files Reference

### Main Application
- `WindowsFormsApplication19/Main.cs` - Main form (954 lines - PRIMARY REFACTORING TARGET)
- `WindowsFormsApplication19/Import.cs` - Import operations with async
- `WindowsFormsApplication19/Export.cs` - Export with async + silentMode
- `WindowsFormsApplication19/DatFile.cs` - DAT processing with silentMode
- `WindowsFormsApplication19/Program.cs` - Entry point with DI setup

### Test Files
- `EDCToolkit.Tests/Phase2_Async/*.cs` - Async operation tests
- `EDCToolkit.Tests/Core/*.cs` - Core operation tests
- `EDCToolkit.Tests/DataOperations/*.cs` - Data operation tests

### Documentation & Plans
- `modernization-progress-tracker.md` - Overall roadmap
- `.claude/plans/phase3-mvp-architecture.md` - Active implementation plan
- `MODERNIZATION-CHANGES.md` - Detailed change log
- `SECURITY-SETUP-GUIDE.md` - Security setup

---

## Common Commands

```bash
# Run all tests (clean temp first to avoid encoding test flakiness)
rm -rf /tmp/EDCToolkit_Tests && dotnet test EDCToolkit.Tests

# Build
dotnet build WindowsFormsApplication19

# Check Main.cs line count
wc -l WindowsFormsApplication19/Main.cs

# Create Phase 3 branch
git checkout -b modernization/$(date +%s)-mvp-architecture

# Check git status
git status
```

---

## Session Resume Checklist

When resuming work:
1. Read this file for current context
2. Check `.claude/plans/phase3-mvp-architecture.md` for active plan
3. Run tests: `rm -rf /tmp/EDCToolkit_Tests && dotnet test EDCToolkit.Tests`
4. Check `git status` for current branch
5. Review `modernization-progress-tracker.md` for overall progress

---

## Testability Patterns

### silentMode Pattern
Used in DatFile.cs and Export.cs to suppress MessageBox during tests:
```csharp
public Export(bool silentMode = false)
{
    _silentMode = silentMode;
}

// In methods:
if (!_silentMode)
{
    MessageBox.Show("message");
}
```

All test instantiations use `silentMode: true`.

---

## Notes

- Use main repo at `D:\GITHUB\EDCTool`
- Encoding tests can be flaky if temp files exist from previous runs - clean with `rm -rf /tmp/EDCToolkit_Tests`
- Test files use xUnit with proper async patterns
- Concordance format uses char 20 (delimiter) and char 254 (qualifier)
