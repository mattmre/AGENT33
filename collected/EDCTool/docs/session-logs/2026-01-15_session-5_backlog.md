# Sequenced Backlog: 2026-01-15 Session 5

**Generated**: 2026-01-15
**Source**: Refinement Cycle Analysis (72 findings from 7 agents)
**Total Items**: 34 actionable items

---

## Execution Summary

| Phase | Focus | Items | Estimated Effort |
|-------|-------|-------|------------------|
| Phase 1 | Critical Security & Cleanup | 5 | 1-2 hours |
| Phase 2 | High Priority Quick Wins | 8 | 2-3 hours |
| Phase 3 | Testing Infrastructure | 8 | 3-4 hours |
| Phase 4 | Medium Priority Improvements | 8 | 4-6 hours |
| Phase 5 | Low Priority Backlog | 5 | 2-3 hours |

---

## Phase 1: Critical Security & Cleanup

*Execute first - security vulnerabilities and dead code removal*

### [Critical] Remove Hardcoded Credentials from Settings.Designer.cs (Effort: S)
**Type**: Security
**Location**: `WindowsFormsApplication19/Settings.Designer.cs`
**Acceptance Criteria**:
- [ ] No hardcoded usernames in source code
- [ ] No hardcoded passwords in source code
- [ ] Credentials moved to environment variables or secure store
- [ ] Build succeeds with no errors
- [ ] Application still functions with credential input
**Blocked By**: None

---

### [Critical] Delete Duplicate MVP/ Folder (Effort: S)
**Type**: Code
**Location**: `WindowsFormsApplication19/MVP/` (4 files)
**Acceptance Criteria**:
- [ ] `WindowsFormsApplication19/MVP/BasePresenter.cs` deleted
- [ ] `WindowsFormsApplication19/MVP/BaseForm.cs` deleted
- [ ] `WindowsFormsApplication19/MVP/IPresenter.cs` deleted
- [ ] `WindowsFormsApplication19/MVP/IView.cs` deleted
- [ ] No references to `EDCTOOLKIT.MVP` namespace exist
- [ ] Build succeeds with 0 errors
- [ ] All 453 tests pass
**Blocked By**: None

---

### [High] Remove Hardcoded Credentials from Importer.cs (Effort: S)
**Type**: Security
**Location**: `WindowsFormsApplication19/Importer.cs`
**Acceptance Criteria**:
- [ ] Default credentials removed from source
- [ ] Credential prompting or secure configuration implemented
- [ ] No plaintext passwords in codebase
- [ ] Build succeeds
**Blocked By**: None

---

### [High] Update System.Data.OleDb to Stable Version (Effort: S)
**Type**: Security
**Location**: `WindowsFormsApplication19/WindowsFormsApplication19.csproj`
**Acceptance Criteria**:
- [ ] System.Data.OleDb updated from preview to stable release
- [ ] No preview package warnings in build output
- [ ] Excel import/export functionality verified
- [ ] All tests pass
**Blocked By**: None

---

### [Low] Delete Legacy Backup Files (Effort: S)
**Type**: Code
**Location**: `WindowsFormsApplication19/Copy of PropagationDialog.*`
**Acceptance Criteria**:
- [ ] `Copy of PropagationDialog.cs` deleted
- [ ] `Copy of PropagationDialog.Designer.cs` deleted
- [ ] Build succeeds
- [ ] No orphaned references
**Blocked By**: None

---

## Phase 2: High Priority Quick Wins

*Documentation and simple improvements with immediate value*

### [High] Create README.md (Effort: S)
**Type**: Docs
**Location**: `README.md` (new file)
**Acceptance Criteria**:
- [ ] Project description and purpose documented
- [ ] Build instructions included
- [ ] Test instructions included
- [ ] Prerequisites listed (.NET 8.0, Windows)
- [ ] Basic usage examples provided
- [ ] License information if applicable
**Blocked By**: None

---

### [High] Update CLAUDE.md with Accurate Information (Effort: S)
**Type**: Docs
**Location**: `CLAUDE.md`
**Acceptance Criteria**:
- [ ] CI workflow fix removed from "Deferred Items" (already done)
- [ ] Test count updated to 453
- [ ] MVP Progress table shows all presenters complete
- [ ] Session 5 information added
- [ ] All status references are current
**Blocked By**: None

---

### [High] Reuse OleDbCommand in Excel Export (Effort: S)
**Type**: Performance
**Location**: `WindowsFormsApplication19/Export.cs`
**Acceptance Criteria**:
- [ ] OleDbCommand created once and reused per export
- [ ] Parameters cleared and re-added per row (not command recreation)
- [ ] Export performance improved (measure before/after)
- [ ] All export tests pass
**Blocked By**: None

---

### [Medium] Wire Empty Menu Handlers to ToolsPresenter (Effort: S)
**Type**: Code
**Location**: `WindowsFormsApplication19/Main.cs` (lines 618, 815, 1046, 1051)
**Acceptance Criteria**:
- [ ] `manipulationToolStripMenuItem_Click` calls `ShowFeatureDisabled()`
- [ ] `parseDatesToolStripMenuItem_Click` calls `ShowFeatureDisabled()`
- [ ] `nUIXToolStripMenuItem_Click` calls `ShowFeatureDisabled()`
- [ ] `ecaptureDatAndImageExportErrorCombinerToolStripMenuItem_Click` calls `ShowFeatureDisabled()`
- [ ] Users see feedback when clicking disabled features
**Blocked By**: None

---

### [Medium] BasePresenter Unit Tests (Effort: S)
**Type**: Test
**Location**: `EDCToolkit.Tests/Presenters/BasePresenterTests.cs` (new file)
**Acceptance Criteria**:
- [ ] Constructor injection tested
- [ ] View property access tested
- [ ] Initialize() method tested
- [ ] Dispose() method tested
- [ ] All tests pass
**Blocked By**: None

---

### [Medium] Missing Tests for IMainView.DataGrid Property (Effort: S)
**Type**: Test
**Location**: `EDCToolkit.Tests/Presenters/` (existing files)
**Acceptance Criteria**:
- [ ] DataGrid property access tested in MockMainView
- [ ] Null DataGrid handling tested
- [ ] Property modification scenarios tested
**Blocked By**: None

---

### [Low] Missing Tests for Constructor Null Logger (Effort: S)
**Type**: Test
**Location**: `EDCToolkit.Tests/Presenters/` (existing files)
**Acceptance Criteria**:
- [ ] Each presenter tested with null logger parameter
- [ ] Expected ArgumentNullException verified
- [ ] Error messages are descriptive
**Blocked By**: None

---

### [Low] CI Workflow actions/cache@v3 Should Be v4 (Effort: S)
**Type**: CI
**Location**: `.github/workflows/dotnet-build.yml`
**Acceptance Criteria**:
- [ ] `actions/cache@v3` updated to `actions/cache@v4`
- [ ] CI workflow runs successfully
- [ ] Cache functionality verified
**Blocked By**: None

---

## Phase 3: Testing Infrastructure

*Test coverage expansion and mock consolidation*

### [High] Consolidate Mock Classes to Shared Location (Effort: M)
**Type**: Test
**Location**: `EDCToolkit.Tests/Mocks/` (new folder)
**Acceptance Criteria**:
- [ ] `EDCToolkit.Tests/Mocks/` folder created
- [ ] `MockMainView.cs` extracted to shared location
- [ ] `MockDataService.cs` extracted to shared location
- [ ] `MockColumnOperationsService.cs` extracted
- [ ] `MockFileOperationsService.cs` extracted
- [ ] `MockDataOperationsService.cs` extracted
- [ ] All presenter test files updated to use shared mocks
- [ ] No duplicate mock definitions remain
- [ ] All 453+ tests pass
**Blocked By**: None

---

### [High] Add Integration Tests for Presenter-Service Interaction (Effort: M)
**Type**: Test
**Location**: `EDCToolkit.Tests/Integration/` (new folder)
**Acceptance Criteria**:
- [ ] Integration test folder created
- [ ] Real service instances used (not mocks)
- [ ] FileOperationsPresenter + FileOperationsService tested end-to-end
- [ ] DataOperationsPresenter + DataOperationsService tested end-to-end
- [ ] At least 5 integration tests added
- [ ] Tests isolated from filesystem where possible
**Blocked By**: Phase 1 (mock consolidation helps but not required)

---

### [High] Create DatFile Class Tests (Effort: M)
**Type**: Test
**Location**: `EDCToolkit.Tests/Core/DatFileTests.cs` (new file)
**Acceptance Criteria**:
- [ ] DAT file parsing tested
- [ ] Header extraction tested
- [ ] Row parsing tested
- [ ] Edge cases tested (empty file, malformed data)
- [ ] silentMode behavior tested
- [ ] At least 15 tests added
**Blocked By**: None

---

### [Medium] FileOperationsService Missing Integration Tests (Effort: M)
**Type**: Test
**Location**: `EDCToolkit.Tests/Services/FileOperationsServiceTests.cs`
**Acceptance Criteria**:
- [ ] File import with real file tested
- [ ] File type detection tested
- [ ] Error handling paths tested
- [ ] Progress reporting tested
- [ ] At least 8 integration tests added
**Blocked By**: None

---

### [Medium] Missing Tests for DataOperationsPresenter Edge Cases (Effort: M)
**Type**: Test
**Location**: `EDCToolkit.Tests/Presenters/DataOperationsPresenterTests.cs`
**Acceptance Criteria**:
- [ ] Empty DataTable handling tested
- [ ] Large dataset handling tested
- [ ] Concurrent operation handling tested
- [ ] At least 6 edge case tests added
**Blocked By**: None

---

### [Medium] No Mock Verification for Service Call Arguments (Effort: M)
**Type**: Test
**Location**: `EDCToolkit.Tests/Presenters/` (multiple files)
**Acceptance Criteria**:
- [ ] Mock classes track method call arguments
- [ ] Tests verify correct arguments passed to services
- [ ] At least 10 argument verification tests added
- [ ] Consider Moq introduction for cleaner verification
**Blocked By**: Mock consolidation (Phase 3, item 1) recommended first

---

### [Low] No Tests for Logger Injection in Presenters (Effort: M)
**Type**: Test
**Location**: `EDCToolkit.Tests/Presenters/` (multiple files)
**Acceptance Criteria**:
- [ ] Logger injection verified in constructor
- [ ] Log messages verified for key operations
- [ ] Consider mock logger for verification
**Blocked By**: None

---

### [Low] Inconsistent IDisposable Pattern in Test Classes (Effort: S)
**Type**: Test
**Location**: `EDCToolkit.Tests/` (multiple files)
**Acceptance Criteria**:
- [ ] All test classes implement IDisposable consistently
- [ ] Dispose() cleans up test fixtures
- [ ] No resource leaks in tests
**Blocked By**: None

---

## Phase 4: Medium Priority Improvements

*Performance, reliability, and code quality improvements*

### [High] Optimize Split() Method in Import.cs (Effort: M)
**Type**: Performance
**Location**: `WindowsFormsApplication19/Import.cs`
**Acceptance Criteria**:
- [ ] Hot path identified and profiled
- [ ] String allocation reduced
- [ ] Span<T> or StringSegment considered
- [ ] Performance improvement measured (target: 20%+)
- [ ] All import tests pass
- [ ] Functionality unchanged
**Blocked By**: None

---

### [High] Improve Import.cs Error Propagation (Effort: M)
**Type**: Reliability
**Location**: `WindowsFormsApplication19/Import.cs`
**Acceptance Criteria**:
- [ ] Error details captured in result object
- [ ] Exception messages not swallowed
- [ ] Caller can determine failure reason
- [ ] User-facing error messages improved
- [ ] Logging added for errors
**Blocked By**: None

---

### [High] Main.cs Legacy Methods Not Covered by Tests (Effort: L)
**Type**: Test
**Location**: `WindowsFormsApplication19/Main.cs`
**Acceptance Criteria**:
- [ ] Testable methods identified and extracted
- [ ] At least 10 legacy methods have tests
- [ ] Integration tests for menu handlers
- [ ] Coverage increased by 10%+
**Blocked By**: Presenter refactoring helps enable this

---

### [Medium] Missing Tests for DateOperationsPresenter Format Edge Cases (Effort: S)
**Type**: Test
**Location**: `EDCToolkit.Tests/Presenters/DateOperationsPresenterTests.cs`
**Acceptance Criteria**:
- [ ] Invalid date formats tested
- [ ] Boundary dates tested (year 0, year 9999)
- [ ] Locale-specific formats tested
- [ ] At least 5 edge case tests added
**Blocked By**: None

---

### [Medium] Export Class silentMode Tests Incomplete (Effort: S)
**Type**: Test
**Location**: `EDCToolkit.Tests/Phase2_Async/ExportTests.cs`
**Acceptance Criteria**:
- [ ] silentMode=true suppresses all dialogs
- [ ] silentMode=false shows expected dialogs
- [ ] Error paths tested in both modes
- [ ] At least 4 silentMode tests added
**Blocked By**: None

---

### [Low] Missing Tests for ToolsPresenter Data Validation (Effort: S)
**Type**: Test
**Location**: `EDCToolkit.Tests/Presenters/ToolsPresenterTests.cs`
**Acceptance Criteria**:
- [ ] Input validation tested
- [ ] Empty input handling tested
- [ ] Invalid data handling tested
**Blocked By**: None

---

### [Medium] DII Import Reads File Twice (Effort: M)
**Type**: Performance
**Location**: `WindowsFormsApplication19/Import.cs` (DII handling)
**Acceptance Criteria**:
- [ ] Single-pass file reading implemented
- [ ] Memory usage reduced
- [ ] Import time improved
- [ ] All DII tests pass
**Blocked By**: None

---

### [Medium] Regex Compilation on Every FindAndReplace Call (Effort: S)
**Type**: Performance
**Location**: `WindowsFormsApplication19/Services/Data/DataOperationsService.cs`
**Acceptance Criteria**:
- [ ] Regex compiled and cached where appropriate
- [ ] Performance improved for repeated searches
- [ ] Functionality unchanged
**Blocked By**: None

---

## Phase 5: Low Priority Backlog

*Nice-to-have improvements for future sessions*

### [Low] DataTable Operations Without BeginLoadData/EndLoadData (Effort: S)
**Type**: Performance
**Location**: `WindowsFormsApplication19/` (multiple files)
**Acceptance Criteria**:
- [ ] BeginLoadData() called before bulk inserts
- [ ] EndLoadData() called after bulk inserts
- [ ] Constraint checking deferred during bulk operations
- [ ] Performance improved for large imports
**Blocked By**: None

---

### [Low] Silent Exception Swallowing in DomainExtraction.NormalizeEmail (Effort: S)
**Type**: Reliability
**Location**: `WindowsFormsApplication19/DomainExtraction.cs`
**Acceptance Criteria**:
- [ ] Exceptions logged before being swallowed
- [ ] Return value indicates failure vs empty result
- [ ] Debug information available
**Blocked By**: None

---

### [Low] Console.WriteLine Used for Error Logging in DatFile.cs (Effort: M)
**Type**: Reliability
**Location**: `WindowsFormsApplication19/DatFile.cs`
**Acceptance Criteria**:
- [ ] Console.WriteLine replaced with ILogger
- [ ] Log levels appropriate (Error, Warning, etc.)
- [ ] Debug output removed from production
**Blocked By**: Logger injection in DatFile class

---

### [Low] Application.DoEvents() in Progress Dialogs (Effort: M)
**Type**: Performance
**Location**: `WindowsFormsApplication19/Main.cs` (lines 448, 514)
**Acceptance Criteria**:
- [ ] DoEvents() replaced with async/await pattern
- [ ] UI remains responsive
- [ ] No reentrancy issues
**Blocked By**: Async refactoring understanding required

---

### [Low] Encoding Test Flakiness (Effort: S)
**Type**: Test
**Location**: `EDCToolkit.Tests/` (UTF-8 encoding tests)
**Acceptance Criteria**:
- [ ] Root cause identified
- [ ] Test isolation improved
- [ ] Temp file cleanup automated
- [ ] Test passes consistently in CI
**Blocked By**: None

---

## Blocked Items Summary

| Item | Blocked By | Unblock Action |
|------|------------|----------------|
| Mock Verification Tests | Mock Consolidation | Complete Phase 3, Item 1 first |
| Main.cs Legacy Tests | Presenter Refactoring | Continue extracting methods to presenters |
| DatFile Logger Update | Logger Injection | Add constructor parameter for ILogger |

---

## Quick Reference: Items by Type

### Security (3)
- [Critical] Remove credentials from Settings.Designer.cs
- [High] Remove credentials from Importer.cs
- [High] Update System.Data.OleDb package

### Code (3)
- [Critical] Delete duplicate MVP/ folder
- [Medium] Wire empty menu handlers
- [Low] Delete legacy backup files

### Test (16)
- [High] Consolidate mock classes
- [High] Integration tests for presenter-service
- [High] DatFile class tests
- [High] Main.cs legacy method tests
- [Medium] BasePresenter tests
- [Medium] IMainView.DataGrid tests
- [Medium] FileOperationsService integration tests
- [Medium] DataOperationsPresenter edge cases
- [Medium] Mock verification tests
- [Medium] DateOperationsPresenter format edge cases
- [Medium] Export silentMode tests
- [Low] Constructor null logger tests
- [Low] Logger injection tests
- [Low] IDisposable pattern consistency
- [Low] ToolsPresenter validation tests
- [Low] Encoding test flakiness

### Docs (2)
- [High] Create README.md
- [High] Update CLAUDE.md

### CI (1)
- [Low] Update actions/cache to v4

### Performance (6)
- [High] Optimize Split() method
- [High] Reuse OleDbCommand
- [Medium] DII single-pass import
- [Medium] Regex caching
- [Low] BeginLoadData/EndLoadData
- [Low] Remove DoEvents()

### Reliability (3)
- [High] Import.cs error propagation
- [Low] Exception logging in DomainExtraction
- [Low] Replace Console.WriteLine in DatFile

---

## Recommended Session 5 Targets

**Minimum Viable Session** (2-3 hours):
1. Delete duplicate MVP/ folder (Phase 1)
2. Remove hardcoded credentials (Phase 1)
3. Create README.md (Phase 2)
4. Update CLAUDE.md (Phase 2)

**Full Session** (4-6 hours):
- All of Phase 1
- All of Phase 2
- Begin Phase 3 (mock consolidation)

**Stretch Goals**:
- Complete Phase 3 testing infrastructure
- Begin Phase 4 optimizations

---

*Backlog generated from refinement cycle analysis. Items prioritized by severity (Critical > High > Medium > Low) and effort (S > M > L for quick wins first).*
