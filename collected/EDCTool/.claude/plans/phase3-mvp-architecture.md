# Phase 3: MVP Architecture Implementation Plan

**Created**: 2026-01-13
**Status**: In Progress (Wave 1-2 Complete)
**Branch**: `modernization/1768360461-mvp-architecture`
**Priority**: HIGH - Foundational for long-term maintainability

## Progress Summary

### Completed (2026-01-13)
- [x] Wave 1: Design & Research - MVP interfaces designed, Main.cs analyzed
- [x] Wave 2: Infrastructure - Base classes, services created
- [x] First Presenter: ColumnOperationsPresenter extracted with 70 tests
- [x] Test coverage: 224 tests passing (was 154)

### Remaining
- [ ] Wave 3: Extract more presenters (FileOperationsPresenter, DataOperationsPresenter)
- [ ] Wave 4: Refactor forms (Combine.cs, ExportDialog.cs)

## Overview

This plan details the implementation of Model-View-Presenter (MVP) architecture for EDCToolkit, focusing on decoupling UI from business logic to enable testability and maintainability.

## Current State

- **Main.cs**: 954+ lines - God Object handling UI, business logic, data access
- **Test Coverage**: ~20% (154 tests passing)
- **Phase 2 Complete**: Async operations, silentMode testability pattern established

## Goals

1. Reduce Main.cs from 954 → ~300 lines (UI only)
2. Extract business logic to testable presenters
3. Create reusable service infrastructure
4. Achieve 80%+ test coverage on extracted logic
5. Maintain all existing functionality (154+ tests passing)

---

## Architecture Design

### Folder Structure

```
WindowsFormsApplication19/
├── Presenters/
│   ├── Base/
│   │   ├── IPresenter.cs
│   │   ├── IView.cs
│   │   ├── BasePresenter.cs
│   │   └── BaseView.cs
│   ├── Main/
│   │   ├── IMainView.cs
│   │   ├── MainPresenter.cs
│   │   ├── ToolbarPresenter.cs
│   │   └── MenuPresenter.cs
│   ├── Combine/
│   │   ├── ICombineView.cs
│   │   └── CombinePresenter.cs
│   └── Export/
│       ├── IExportView.cs
│       └── ExportPresenter.cs
├── Services/
│   ├── Infrastructure/
│   │   ├── IProgressReporter.cs
│   │   ├── ProgressReportingService.cs
│   │   └── IMessageService.cs
│   ├── Data/
│   │   ├── IDataTableService.cs
│   │   └── DataTableService.cs
│   └── Operations/
│       ├── IColumnOperations.cs
│       └── ColumnOperationsService.cs
```

### Interface Definitions

```csharp
// Base presenter contract
public interface IPresenter : IDisposable
{
    void Initialize();
    void Load();
}

// Base view contract
public interface IView
{
    void Show();
    void Hide();
    void Close();
    bool InvokeRequired { get; }
    object Invoke(Delegate method);
}

// Progress reporting contract
public interface IProgressReporter
{
    void ReportProgress(int percentComplete, string message);
    void ReportStatus(string status);
    CancellationToken CancellationToken { get; }
}
```

---

## Implementation Tasks

### Wave 1: Design & Research (Parallel)

| Task | Agent | Output |
|------|-------|--------|
| Design MVP interfaces | architect | Interface definitions, folder structure |
| Analyze Main.cs | researcher | List of extraction candidates with dependencies |

### Wave 2: Infrastructure (Parallel)

| Task | Agent | Output |
|------|-------|--------|
| Create base classes | implementer | IPresenter, IView, BasePresenter, etc. |
| Create services | implementer | IProgressReporter, IMessageService |
| Update docs | documentation | Architecture documentation |

### Wave 3: Extraction (Sequential)

| Task | Agent | Output | Dependencies |
|------|-------|--------|--------------|
| Extract ToolbarPresenter | refactorer | Toolbar button handlers | Wave 2 |
| Add toolbar tests | tester | ToolbarPresenterTests.cs | ToolbarPresenter |
| Extract MenuPresenter | refactorer | Menu item handlers | Wave 2 |
| Add menu tests | tester | MenuPresenterTests.cs | MenuPresenter |
| Extract column operations | refactorer | Add/Remove/Rename column logic | Wave 2 |
| Review & validate | reviewer | Code review, test verification | Each extraction |

### Wave 4: Form Refactoring (Sequential)

| Task | Agent | Priority |
|------|-------|----------|
| Refactor Combine.cs | refactorer | High |
| Refactor ExportDialog.cs | refactorer | Medium |
| Refactor DAT2TXT.cs | refactorer | Medium |

---

## Extraction Candidates from Main.cs

### High Priority (Toolbar/Common Operations)

1. **Column Operations** (~150 lines)
   - `addColumnToolStripMenuItem_Click`
   - `removeColumnToolStripMenuItem_Click`
   - `renameColumnToolStripMenuItem_Click`
   - `reorderColumnsToolStripMenuItem_Click`

2. **Data Operations** (~200 lines)
   - `trimFieldToolStripMenuItem_Click`
   - `replaceToolStripMenuItem_Click`
   - `findAndReplaceToolStripMenuItem_Click`
   - `tallyToolStripMenuItem_Click`

3. **File Operations** (~150 lines)
   - `openToolStripMenuItem_Click`
   - `saveToolStripMenuItem_Click`
   - `exportToolStripMenuItem_Click`

### Medium Priority (Menu Handlers)

4. **Date Operations** (~100 lines)
   - `parseDatesToolStripMenuItem_Click`
   - `validateDatesToolStripMenuItem_Click`

5. **Hash Operations** (~80 lines)
   - `generateHashToolStripMenuItem_Click`
   - `comboHashToolStripMenuItem_Click`

---

## Testing Strategy

### Presenter Tests

```csharp
public class ToolbarPresenterTests
{
    private Mock<IMainView> _mockView;
    private Mock<IDataService> _mockDataService;
    private ToolbarPresenter _presenter;

    [Fact]
    public void AddColumn_WithValidName_AddsColumnToDataTable()
    {
        // Arrange
        var dataTable = new DataTable();
        _mockDataService.Setup(s => s.GetActiveDataTable()).Returns(dataTable);

        // Act
        _presenter.AddColumn("NewColumn");

        // Assert
        Assert.Contains("NewColumn", dataTable.Columns.Cast<DataColumn>().Select(c => c.ColumnName));
    }
}
```

### Test Coverage Targets

| Component | Current | Target |
|-----------|---------|--------|
| Presenters | 0% | 80% |
| Services | 20% | 70% |
| Overall | 20% | 50% |

---

## DI Registration

```csharp
// Program.cs additions
services.AddTransient<IProgressReporter, ProgressReportingService>();
services.AddTransient<IMessageService, MessageService>();
services.AddTransient<IDataTableService, DataTableService>();
services.AddTransient<ToolbarPresenter>();
services.AddTransient<MenuPresenter>();
services.AddTransient<MainPresenter>();
```

---

## Migration Strategy

1. **Strangler Pattern**: New code uses presenters, old code untouched initially
2. **Incremental Extraction**: One method group at a time
3. **Feature Toggle**: `UseMvpPattern` config option during transition
4. **Validation**: Run all 154+ tests after each extraction

---

## Success Criteria

- [ ] Main.cs reduced to ≤300 lines (UI code only)
- [ ] All toolbar operations extracted to ToolbarPresenter
- [ ] All menu operations extracted to MenuPresenter
- [ ] 80%+ test coverage on presenter logic
- [ ] All 154+ existing tests still passing
- [ ] No regression in functionality
- [ ] DI registration complete for all new components

---

## Session Continuation Notes

### To Resume This Plan

1. Check current progress against tasks above
2. Run `dotnet test` to verify baseline
3. Continue with next uncompleted task
4. Update this document with progress

### Key Files to Reference

- `modernization-progress-tracker.md` - Overall roadmap
- `.claude/CLAUDE-SESSION-CONTEXT.md` - Session context
- `WindowsFormsApplication19/Main.cs` - Primary refactoring target
- `EDCToolkit.Tests/` - Test location

### Commands

```bash
# Verify tests pass
dotnet test EDCToolkit.Tests --verbosity minimal

# Create feature branch
git checkout -b modernization/$(date +%s)-mvp-architecture

# Check Main.cs line count
wc -l WindowsFormsApplication19/Main.cs
```

---

**Last Updated**: 2026-01-13
**Updated By**: Claude Code (Opus 4.5)
