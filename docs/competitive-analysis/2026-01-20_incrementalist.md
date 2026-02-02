# Competitive Analysis: Incrementalist

**Date**: 2026-01-20  
**Repository**: https://github.com/petabridge/Incrementalist  
**Analyst**: AI Agent  
**Status**: Complete (Expanded)

---

## Executive Summary

**Incrementalist** by Petabridge is a .NET tool that leverages libgit2sharp and Roslyn to compute incremental build steps for large .NET solutions. It optimizes CI/CD pipelines by building and testing only the projects affected by Git changes.

The repository demonstrates **mature engineering practices** for dependency graph analysis, parallel execution control, and agentic development guidance (via .cursor/rules). While AGENT-33 focuses on cross-repository orchestration governance, Incrementalist provides concrete implementation patterns for **incremental work detection**, **parallel execution control**, **structured agentic rules**, and **configuration-driven automation**.

**Key Insights**:

1. **Incremental Processing Model**: Incrementalist's core pattern—detecting what changed and processing only affected components—is directly applicable to AGENT-33's orchestration needs. The system could be adapted to detect which documentation artifacts, workflows, or agents need updating based on Git changes.

2. **Three-Layer Change Detection**: Incrementalist uses a sophisticated hierarchy: (1) solution-wide triggers, (2) import/dependency analysis, (3) direct file changes. This model maps to AGENT-33's potential: (1) core framework changes, (2) workflow dependencies, (3) individual artifact changes.

3. **Parallel Execution with Safety Limits**: The `--parallel` with `--parallel-limit` pattern solves exactly what AGENT-33 needs for safe multi-agent execution.

4. **Agentic Rules (MDC Format)**: The `.cursor/rules/` directory contains 9 structured rule files that demonstrate how to encode domain knowledge for AI-assisted development.

---

## Repository Overview

### Purpose
A command-line tool and library for:
- Computing affected .NET projects from Git diffs
- Understanding project dependency graphs via Roslyn/MSBuild
- Running dotnet commands against only affected projects
- Parallel execution with configurable limits
- Configuration file management with JSON schema validation

### Technology Stack
- **.NET 8.0 / .NET 10.0** (dual-targeting)
- **libgit2sharp** - Git repository analysis
- **Roslyn** - Code analysis and project system
- **MSBuild Static Graph** - Dependency detection
- **System.CommandLine** - CLI parsing
- **JSON Schema** - Config validation with IDE IntelliSense

### Structure

```
Incrementalist/
├── .cursor/rules/         # 9 agentic development rules (MDC format)
├── docs/                  # User documentation
│   ├── building.md        # Build instructions
│   ├── config.md          # Configuration guide
│   ├── examples.md        # Real-world usage
│   └── how-it-works.md    # Architecture docs
├── src/
│   ├── Incrementalist/           # Core library
│   │   ├── Git/                  # Git diff analysis
│   │   ├── ProjectSystem/        # MSBuild project parsing
│   │   ├── SolutionWideChangeDetector.cs
│   │   └── BuildAnalysisResult.cs
│   ├── Incrementalist.Cmd/       # CLI tool
│   │   ├── Commands/             # Verb implementations
│   │   ├── Config/               # JSON config handling
│   │   └── Program.cs            # Main entry point
│   └── Incrementalist.Tests/     # Test suite
├── incrementalist.sample.json    # Example config
└── RELEASE_NOTES.md              # Version history
```

### Philosophy
1. **Incremental by Default**: Only process what changed
2. **Configuration as Code**: JSON config with schema validation
3. **Parallel Where Safe**: Configurable parallelism with limits
4. **Solution-Wide Detection**: Recognize when full builds are needed
5. **CI/CD First**: Output formats designed for pipeline integration
6. **Layered Configuration**: CLI overrides config file values (precedence rules)
7. **Graceful Degradation**: Continue-on-error with aggregated failure reporting

---

## Detailed Feature Inventory

### 1. Git Change Detection (DiffHelper.cs)

Incrementalist detects changes across three categories:

| Change Type | Detection Method | Example |
|-------------|------------------|---------|
| **Staged Changes** | `repo.RetrieveStatus().Staged` | Files added to Git index |
| **Unstaged Changes** | `Modified`, `Added`, `Untracked` | Working directory changes |
| **Branch Diff** | `repo.Diff.Compare<TreeChanges>()` | Changes vs target branch |

**Key Implementation Pattern**:
```csharp
// From DiffHelper.cs - Multi-source change aggregation
var changes = new HashSet<AbsolutePath>();

// Add staged changes
foreach (var staged in status.Staged)
    changes.Add(new AbsolutePath(Path.GetFullPath(...)));

// Add unstaged changes  
foreach (var unstaged in status.Modified.Concat(status.Added).Concat(status.Untracked))
    changes.Add(new AbsolutePath(...));

// Add changes between target branch and HEAD
var branchDiff = repo.Diff.Compare<TreeChanges>(targetTree, repo.Head.Tip.Tree);
foreach (var change in branchDiff)
    changes.Add(new AbsolutePath(...));
```

**AGENT-33 Applicability**: Could detect changes across:
- `core/` - Framework changes affecting all workflows
- `collected/` - Per-repo artifact changes
- `docs/` - Local planning artifacts

### 2. Solution-Wide Change Triggers (SolutionWideChangeDetector.cs)

Files that trigger full solution rebuilds:

| Trigger File | Reason | AGENT-33 Equivalent |
|--------------|--------|---------------------|
| `Directory.Build.props` | Affects all projects | `core/packs/policy-pack-v1.md` |
| `Directory.Packages.props` | Version dependencies | `core/ORCHESTRATION_INDEX.md` |
| `global.json` | SDK version | Framework version |
| `nuget.config` | Package sources | N/A |
| `*.sln` | Solution structure | `core/arch/workflow.md` |

**Widely Imported File Detection**:
```csharp
// A file is "widely imported" if:
// 1. It's imported by Directory.Build.props
// 2. It affects multiple projects
internal static bool IsWidelyImportedFile(ImportedFile importedFile)
{
    var isImportedByDirectoryBuildProps = importedFile.DependentProjects
        .Any(p => Path.GetFileName(p.Path.Path)
            .Equals("Directory.Build.props", StringComparison.OrdinalIgnoreCase));

    var affectsMultipleProjects = importedFile.DependentProjects.Count > 1;

    return isImportedByDirectoryBuildProps || affectsMultipleProjects;
}
```

### 3. Dependency Graph Analysis (EmitDependencyGraphTask.cs)

The task performs a sophisticated multi-stage analysis:

```
1. Open Solution → Parse all projects
2. Gather All Files → Map file→project relationships
3. Filter Affected Files → Git diff intersection
4. Check Solution-Wide Triggers → Full rebuild if needed
5. Compute Dependency Graph → Transitive closure
6. Apply Glob Filters → Include/exclude patterns
7. Return Build Strategy → Full vs Incremental
```

**File Type Classification**:
| Type | Detection | Example |
|------|-----------|---------|
| `Code` | Source files | `.cs`, `.fs` |
| `Project` | Project files | `.csproj`, `.fsproj` |
| `Solution` | Solution files | `.sln`, `.slnx` |
| `Script` | Build scripts | `.ps1`, `.sh` |
| `Other` | Everything else | `.md`, `.json` |

**Logging Pattern** (structured analytics):
```csharp
Logger.LogInformation(
    "Modified files breakdown: {SourceFiles} source files, {ProjectFiles} project files, " +
    "{SolutionFiles} solution files, {ScriptFiles} script files, {OtherFiles} other files",
    modifiedSourceFiles, modifiedProjectFiles, modifiedSolutionFiles, 
    modifiedScriptFiles, modifiedOtherFiles);
```

### 4. Parallel Execution Engine (RunDotNetCommandTask.cs)

**Key Features**:

| Feature | Implementation | Default |
|---------|----------------|---------|
| **Parallel Mode** | `Task.WhenAll()` with semaphore | Off |
| **Concurrency Limit** | `SemaphoreSlim(_parallelLimit)` | 0 (unlimited) |
| **Error Handling** | `continueOnError` flag | True |
| **Failure Tracking** | `failedProjects` list | Aggregated |
| **Timeout Control** | `CancellationTokenSource.CancelAfter()` | 2 minutes |

**Implementation Pattern**:
```csharp
if (_runInParallel)
{
    var semaphore = _parallelLimit > 0 ? new SemaphoreSlim(_parallelLimit) : null;

    var tasks = projects.Select(async project =>
    {
        if (semaphore is not null)
            await semaphore.WaitAsync();

        try
        {
            if (await RunCommandAsync(project, ct) != 0)
            {
                failedProjects.Add(project);
                if (!_continueOnError)
                    return;
            }
        }
        finally
        {
            semaphore?.Release();
        }
    });

    await Task.WhenAll(tasks);
    semaphore?.Dispose();
}
```

**Exit Code Semantics**:
| Code | Meaning |
|------|---------|
| 0 | All commands succeeded |
| 1 | One or more commands failed |
| -1 | Exception during execution |
| -2 | Not inside Git repository |
| -3 | Unable to find repository |
| -4 | Target branch not found |

### 5. Configuration System (Config/)

**Layered Configuration with Precedence**:

```
CLI Arguments → Override → Config File → Default Values
```

**JSON Schema (incrementalist.schema.json)**:
- Draft 2020-12 compliant
- IDE IntelliSense support
- Validation with detailed error messages
- Examples embedded in schema

**Full Schema Properties**:

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `solutionFilePath` | string | null | Target solution |
| `outputFile` | string | null | Output file path |
| `listFolders` | boolean | false | Folder vs project mode |
| `gitBranch` | string | "dev" | Comparison branch |
| `workingDirectory` | string | null | Override CWD |
| `verbose` | boolean | false | Debug logging |
| `timeoutMinutes` | integer | 2 | Execution timeout |
| `continueOnError` | boolean | true | Error handling |
| `runInParallel` | boolean | false | Parallel execution |
| `parallelLimit` | integer | 0 | Max concurrency |
| `failOnNoProjects` | boolean | false | Strict mode |
| `noCache` | boolean | false | Bypass cache |
| `skip` | string[] | [] | Exclude globs |
| `target` | string[] | [] | Include globs |
| `nameApplicationToStart` | string | "dotnet" | Process name |

**Config Merger Logic** (ConfigMerger.cs):
- String properties: CLI takes precedence
- Boolean properties: Config file sets base, CLI overrides if non-default
- Array properties: Primary (CLI) wins if non-empty, else secondary (config)
- Bug fixes for edge cases (#380, #381)

### 6. Glob-Based Filtering (GlobFilter.cs)

**Two-Phase Filtering**:

1. **Target Globs** (`--target-glob`): Include only matching projects
2. **Skip Globs** (`--skip-glob`): Exclude matching from remaining

**Order of Operations**:
```
All Affected Projects
    → Apply target-glob (whitelist)
    → Apply skip-glob (blacklist)
    → Final Project List
```

**Use Cases**:
```bash
# Only test projects
--target-glob "**/*.Tests.csproj"

# Exclude integration tests
--skip-glob "**/*.IntegrationTests.csproj"

# Only src projects, no tests
--target-glob "src/**/*.csproj" --skip-glob "**/*.Tests.csproj"
```

### 7. Build Result Types (BuildAnalysisResult.cs)

**Discriminated Union Pattern**:
```csharp
public abstract class BuildAnalysisResult { }

public class FullSolutionBuildResult : BuildAnalysisResult
{
    public AbsolutePath SolutionPath { get; }
}

public class IncrementalBuildResult : BuildAnalysisResult
{
    public IReadOnlyList<AbsolutePath> AffectedProjects { get; }
}
```

**Decision Logic**:
```csharp
public async Task<int> Run(BuildAnalysisResult buildResult)
{
    return buildResult switch
    {
        FullSolutionBuildResult full => await RunSolutionBuild(full.SolutionPath, _ct),
        IncrementalBuildResult incremental => await RunIncrementalBuild(incremental.AffectedProjects, _ct),
        _ => throw new InvalidOperationException($"Unknown build result type: {buildResult.GetType()}")
    };
}
```

### 8. Project Import Tracking (ProjectImportsFinder.cs)

**Parallel XML Parsing**:
```csharp
Parallel.ForEach(projectFiles, projectFile =>
{
    var xmlDoc = ParseXmlDocument(projectFile.Path.Path);
    var importTags = xmlDoc.DocumentElement?.SelectNodes("//Import");
    
    foreach (XmlNode importTag in importTags)
    {
        var importedFilePath = importTag.Attributes?.GetNamedItem("Project")?.Value;
        // Track: importedFile → [dependentProjects...]
        imports.AddOrUpdate(importedFileFillPath,
            addValue: ImmutableList<SlnFileWithPath>.Empty.Add(projectFile),
            updateValueFactory: (_, dependentProjects) => dependentProjects.Add(projectFile));
    }
});
```

**Data Model**:
```csharp
public sealed class ImportedFile
{
    public AbsolutePath Path { get; }
    public IImmutableList<SlnFileWithPath> DependentProjects { get; }
}
```

### 9. Agentic Rules System (.cursor/rules/)

**MDC (Markdown with Cursor) Format**:

```markdown
---
description: Rule description for context
globs: *.cs, *.csproj, *.ps1
---

# Rule Title

Role Definition:
 - Expert Role 1
 - Expert Role 2
 - Expert Role 3

## Section 1
...
```

**Rule Files Inventory**:

| File | Lines | Focus Area | Key Patterns |
|------|-------|------------|--------------|
| `incrementalist.mdc` | 230+ | Project-specific | Command execution, testing, MSBuildCollectionFixture |
| `coding-style.mdc` | 700+ | C# patterns | Records, immutability, Result types, async/await |
| `testing.mdc` | 550+ | xUnit patterns | TestContainers, ITestOutputHelper, Theory data |
| `dependency-management.mdc` | 170+ | NuGet | Lock files, vulnerability scanning, license compliance |
| `solution-management.mdc` | 200+ | .NET builds | global.json, Directory.Build.props, deterministic builds |
| `dotnet-build.mdc` | 180+ | MSBuild | SDK-style projects, incremental builds |
| `code-signing.mdc` | 90+ | Security | Package signing, key management |
| `consuming-dotnettool.mdc` | 120+ | Tool usage | Global vs local tools |
| `publishing-dotnettool.mdc` | 80+ | NuGet publishing | Package metadata |

**Notable Coding Patterns from coding-style.mdc**:

1. **Records for Data Types**:
```csharp
// Good: Immutable data type with value semantics
public sealed record CustomerDto(string Name, Email Email);
```

2. **Result Types for Expected Failures**:
```csharp
public sealed record Result<T>
{
    public T? Value { get; }
    public Error? Error { get; }
    
    public static Result<T> Success(T value) => new(value);
    public static Result<T> Failure(Error error) => new(error);
}
```

3. **Pattern Matching over Conditionals**:
```csharp
public decimal CalculateDiscount(Customer customer) =>
    customer switch
    {
        { Tier: CustomerTier.Premium } => 0.2m,
        { OrderCount: > 10 } => 0.1m,
        _ => 0m
    };
```

4. **Try Methods over Exceptions**:
```csharp
if (dictionary.TryGetValue(key, out var value))
{
    // Use value safely here
}
```

5. **Immutable Collections in Records**:
```csharp
public sealed record Order(
    OrderId Id, 
    ImmutableList<OrderLine> Lines,
    ImmutableDictionary<string, string> Metadata);
```

### 10. Build Engine Abstraction (BuildEngine.cs)

**Pluggable Engine Pattern**:

```csharp
public enum Engine
{
    StaticGraph,  // MSBuild Static Graph (default, faster)
    Workspace     // Roslyn Workspace (compatibility)
}

public abstract class BuildEngine : IDisposable
{
    public abstract Task<Solution> CreateSolutionAsync(AbsolutePath solutionPath, CancellationToken ct);
}
```

**Engine Selection**:
- **StaticGraph** (default): Uses MSBuild Static Graph for faster analysis
- **Workspace**: Uses Roslyn MSBuildWorkspace for F# compatibility

### 11. CI/CD Integration Patterns

**Real-World Examples from Akka.NET**:

```yaml
# Azure DevOps Pipeline
- script: |
    dotnet incrementalist run \
      -b dev \
      --parallel \
      --parallel-limit 4 \
      -- test -c Release --no-build
  displayName: 'Run Affected Tests'
```

**Output File Integration**:
```bash
# Generate affected projects list
incrementalist run --dry -b dev -f ./affected-projects.txt

# Use in subsequent pipeline steps
cat affected-projects.txt | xargs -I {} dotnet publish {}
```

### 12. Cancellation and Timeout Handling

**Linked Cancellation Pattern**:
```csharp
using var linkedCts = CancellationTokenSource.CreateLinkedTokenSource(_ct);
linkedCts.CancelAfter(_settings.TimeoutDuration);

try
{
    await process.WaitForExitAsync(linkedCts.Token);
}
catch (TaskCanceledException)
{
    _logger.LogWarning("Command was canceled for {Target} after {ElapsedTime}", ...);
}
```

**Console Interrupt Handling**:
```csharp
Console.CancelKeyPress += delegate {
    logger.LogWarning("Cancellation requested. Exiting...");
    _processCts.Cancel();
};
```

---

## Comparative Analysis

### Structural Comparison

| Aspect | Incrementalist | AGENT-33 |
|--------|---------------|----------|
| **Focus** | Incremental .NET builds | Cross-repo orchestration |
| **Detection** | Git + MSBuild dependency graph | Manual scope definition |
| **Parallelism** | Built-in with limits | Manual agent coordination |
| **Configuration** | JSON with schema | Markdown documents |
| **Agentic Rules** | .cursor/rules MDC files | Orchestrator prompts |
| **Output Formats** | CSV project lists, folders | Markdown logs |
| **Evidence** | Exit codes, test results | Commands, outcomes, artifacts |

### Pattern Comparison

| Pattern | Incrementalist | AGENT-33 |
|---------|---------------|----------|
| **Change Detection** | Automatic via Git diff | Manual scope locking |
| **Dependency Analysis** | Automatic via Roslyn | Manual ROUTING_MAP |
| **Execution Strategy** | Parallel with limits | Sequential manual |
| **Error Handling** | Continue-on-error flag | Risk triggers |
| **Dry Run** | `--dry` flag | Plan review |
| **Configuration** | Layered (file + CLI) | Document-based |

### Agentic Rules Comparison

| Rule Category | Incrementalist | AGENT-33 |
|---------------|---------------|----------|
| **Role Definition** | Explicit in MDC frontmatter | AGENT_REGISTRY entries |
| **Code Style** | Detailed with examples | Policy-pack guidelines |
| **Testing** | xUnit patterns, TestContainers | Verification evidence focus |
| **Security** | Code signing, secret management | Risk triggers, audit trail |
| **Error Handling** | Result types, exceptions | Escalation protocols |
| **Async Patterns** | CancellationToken, ValueTask | N/A (documentation focus) |

---

## Gap Analysis

### Features AGENT-33 Lacks

#### 1. **Automatic Change Detection** (HIGH PRIORITY)
Incrementalist automatically detects what changed via Git. AGENT-33 relies on manual scope locking.

**Benefits if added**:
- Auto-detect which workflows, docs, or agents need updating
- "Incremental refinement" based on what actually changed
- Reduce manual scope definition overhead

#### 2. **Dependency Graph for Artifacts** (HIGH PRIORITY)
Incrementalist maps project dependencies. AGENT-33 has ROUTING_MAP but no automated dependency detection.

**Benefits if added**:
- Know which downstream artifacts need updating when source changes
- Detect cascade effects (e.g., changing a core template affects all derived workflows)
- Validate completeness of changes

#### 3. **Parallel Execution Control** (HIGH PRIORITY)
Incrementalist has `--parallel` and `--parallel-limit`. AGENT-33 has learned "don't use background agents" but no structured parallel control.

**Benefits if added**:
- Safe parallel agent execution with limits
- Prevent resource exhaustion
- Better CI/CD integration

#### 4. **JSON Schema for Configuration** (MEDIUM PRIORITY)
Incrementalist uses JSON schema for IDE IntelliSense and validation.

**Benefits if added**:
- Schema for orchestration configs
- IDE auto-completion for agent definitions
- Validation before execution

#### 5. **Dry Run Mode** (MEDIUM PRIORITY)
Incrementalist's `--dry` flag previews without executing.

**Benefits if added**:
- Preview which agents/tasks would run
- Validate before committing to execution
- Safer automation

#### 6. **Glob-Based Filtering** (MEDIUM PRIORITY)
Incrementalist's `--target-glob` and `--skip-glob` for fine-grained control.

**Benefits if added**:
- Filter artifacts by pattern
- Exclude specific docs/agents from runs
- More flexible scope control

#### 7. **Structured MDC Rule Files** (LOW-MEDIUM PRIORITY)
Incrementalist uses MDC format with YAML frontmatter for agentic rules.

**Benefits if added**:
- Standardized rule format
- Glob patterns for applicability
- Role definitions in metadata

### Features Incrementalist Lacks

#### 1. **Cross-Repository Coordination** (PRESENT IN AGENT-33)
- Single-solution focus
- No multi-repo orchestration
- No ingestion/normalization pattern

#### 2. **Session Continuity** (PRESENT IN AGENT-33)
- No STATUS.md/PLAN.md/TASKS.md
- No handoff protocols
- Command-invocation focused

#### 3. **Evidence Capture** (PRESENT IN AGENT-33)
- Exit codes but no verification logs
- No audit trail for decisions
- No review integration

#### 4. **Multi-Agent Coordination** (PRESENT IN AGENT-33)
- Single-tool execution
- No agent registry
- No routing between specialized roles

#### 5. **Model Agnosticism** (PRESENT IN AGENT-33)
- Cursor-specific (.cursor/rules)
- No abstraction layer
- Tied to specific tooling

---

## Recommendations

### HIGH PRIORITY

#### R-01: Implement Incremental Artifact Detection System
**Action**: Create a change detection system for AGENT-33 artifacts based on Incrementalist's model.

**Design**:
```
ArtifactChangeDetector
├── Git Change Detection
│   ├── Staged changes
│   ├── Unstaged changes
│   └── Branch diff (vs main/dev)
├── Solution-Wide Triggers
│   ├── core/orchestrator/ changes → affects all workflows
│   ├── core/packs/ changes → affects referencing repos
│   └── manifest.md changes → full re-validation
├── Dependency Analysis
│   ├── Workflow → workflow dependencies
│   ├── Template → derived workflows
│   └── Agent → routing map dependencies
└── Output
    ├── Full Refinement (all artifacts)
    └── Incremental Refinement (affected only)
```

**Implementation Pattern** (adapted from DiffHelper.cs):
```python
def detect_changed_artifacts(repo_path: str, target_branch: str) -> ChangeSet:
    changes = set()
    
    # Staged changes
    for file in repo.index.diff("HEAD"):
        changes.add(normalize_path(file.a_path))
    
    # Unstaged changes
    for file in repo.index.diff(None):
        changes.add(normalize_path(file.a_path))
    
    # Branch diff
    target_tree = repo.refs[target_branch].commit.tree
    for diff in repo.head.commit.diff(target_tree):
        changes.add(normalize_path(diff.a_path))
    
    return ChangeSet(changes)
```

**Effort**: Medium-High  
**Impact**: High (automated scoping replaces manual)

#### R-02: Add Parallel Execution Control for Agents
**Action**: Define parallel execution specifications based on Incrementalist's semaphore pattern.

**Configuration Schema**:
```json
{
  "$schema": "https://agent-33.github.io/schemas/parallel-execution.schema.json",
  "parallelExecution": {
    "enabled": true,
    "maxConcurrent": 4,
    "continueOnError": true,
    "timeoutMinutes": 10,
    "safeForParallel": [
      "explore",
      "research", 
      "lint",
      "validate"
    ],
    "mustBeSequential": [
      "implementer",
      "git-push",
      "merge-pr"
    ]
  }
}
```

**Semaphore Implementation** (adapted from RunDotNetCommandTask.cs):
```python
async def run_parallel_agents(
    agents: List[Agent],
    max_concurrent: int = 4,
    continue_on_error: bool = True
) -> ExecutionResult:
    
    semaphore = asyncio.Semaphore(max_concurrent) if max_concurrent > 0 else None
    failed_agents = []
    
    async def run_with_limit(agent):
        if semaphore:
            async with semaphore:
                return await agent.execute()
        return await agent.execute()
    
    tasks = [run_with_limit(agent) for agent in agents]
    results = await asyncio.gather(*tasks, return_exceptions=continue_on_error)
    
    return ExecutionResult(results, failed_agents)
```

**Effort**: Medium  
**Impact**: High (enables safe automation)

#### R-03: Create Solution-Wide Change Trigger Definitions
**Action**: Define cross-cutting change triggers following Incrementalist's pattern.

**Trigger Definitions**:

| Trigger Path Pattern | Effect | Reason |
|---------------------|--------|--------|
| `core/orchestrator/**` | Full workflow refresh | Framework changes |
| `core/packs/**` | Notify all referencing repos | Policy changes |
| `core/arch/workflow.md` | Re-validate all workflows | Workflow spec changes |
| `manifest.md` | Full ingest re-validation | Source list changes |
| `dedup-policy.md` | Re-run deduplication | Rules changes |
| `core/ORCHESTRATION_INDEX.md` | Update all agent prompts | Index changes |

**Implementation** (adapted from SolutionWideChangeDetector.cs):
```python
ALWAYS_FULL_REFRESH_FILES = {
    "manifest.md",
    "dedup-policy.md", 
    "core/ORCHESTRATION_INDEX.md"
}

ALWAYS_FULL_REFRESH_DIRS = {
    "core/orchestrator/",
    "core/packs/"
}

def requires_full_refresh(changed_files: Set[str]) -> bool:
    for file in changed_files:
        if Path(file).name in ALWAYS_FULL_REFRESH_FILES:
            return True
        for dir_pattern in ALWAYS_FULL_REFRESH_DIRS:
            if file.startswith(dir_pattern):
                return True
    return False
```

**Effort**: Low  
**Impact**: High (prevents incomplete updates)

### MEDIUM PRIORITY

#### R-04: Add JSON Schema for Orchestration Configuration
**Action**: Create JSON schemas for agent/workflow configuration with IDE IntelliSense.

**Schema Structure**:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://agent-33.github.io/schemas/agent.schema.json",
  "title": "AGENT-33 Agent Definition",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^AGT-\\d{3}$",
      "description": "Unique agent identifier (e.g., AGT-001)"
    },
    "name": {
      "type": "string",
      "description": "Human-readable agent name"
    },
    "role": {
      "type": "string",
      "description": "Primary responsibility"
    },
    "tools": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Allowed tools for this agent"
    },
    "restrictions": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Prohibited actions"
    },
    "escalationTriggers": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Conditions requiring escalation"
    }
  },
  "required": ["id", "name", "role"]
}
```

**Effort**: Medium  
**Impact**: Medium (better tooling support)

#### R-05: Implement Dry Run Mode for Orchestration
**Action**: Add preview capability following Incrementalist's `--dry` flag pattern.

**Output Format**:
```
Dry Run Analysis
================

Changed Artifacts: 12
  - core/workflows/review.md (modified)
  - core/agents/implementer.md (modified)
  - collected/project-a/CLAUDE.md (modified)
  ...

Agents to Invoke: 3
  1. AGT-005 Reviewer → core/workflows/review.md
  2. AGT-007 Documentation → core/agents/implementer.md
  3. AGT-001 Orchestrator → collected/project-a/CLAUDE.md

Execution Mode: Incremental (12 of 156 artifacts affected)
Estimated Duration: 8 minutes

[DRY RUN] No changes will be made.
```

**Effort**: Low  
**Impact**: Medium (safer automation)

#### R-06: Adopt MDC Rule Format for Agent Definitions
**Action**: Standardize on MDC (Markdown with Cursor/Claude) format for agent rules.

**Template**:
```markdown
---
description: Agent-specific rules and context
globs: "**/*.md"
role: Implementer
triggers:
  - implementation tasks
  - code changes
  - PR creation
---

# AGT-003 Implementer Agent Rules

## Role Definition
- Code Implementation Expert
- Test Engineer
- Documentation Updater

## Allowed Actions
- Edit source code files
- Create new files
- Run tests
- Update documentation

## Restrictions
- Never push directly to main/master
- Always create feature branches
- Require review before merge

## Evidence Requirements
- Log all commands executed
- Capture test output
- Document decisions

## Escalation Triggers
- Security-sensitive changes
- API signature changes
- Schema modifications
```

**Effort**: Low  
**Impact**: Medium (standardization)

#### R-07: Implement Glob-Based Artifact Filtering
**Action**: Add pattern-based filtering following Incrementalist's `--target-glob` and `--skip-glob` pattern.

**Usage**:
```bash
# Only process core documentation
agent-orchestrate --target-glob "core/**/*.md"

# Exclude session logs from processing
agent-orchestrate --skip-glob "**/session-logs/**"

# Process collected artifacts except raw ingests
agent-orchestrate --target-glob "collected/**" --skip-glob "collected/**/raw/**"
```

**Implementation**:
```python
def filter_artifacts(
    artifacts: List[str],
    target_globs: List[str],
    skip_globs: List[str]
) -> List[str]:
    # Phase 1: Include only matching targets (if specified)
    if target_globs:
        artifacts = [a for a in artifacts 
                    if any(fnmatch(a, g) for g in target_globs)]
    
    # Phase 2: Exclude matching skips
    if skip_globs:
        artifacts = [a for a in artifacts 
                    if not any(fnmatch(a, g) for g in skip_globs)]
    
    return artifacts
```

**Effort**: Low  
**Impact**: Medium (flexible scope control)

#### R-08: Add Workflow Dependency Graph
**Action**: Track dependencies between workflows, similar to project import tracking.

**Dependency Types**:
| Dependency Type | Example | Detection |
|-----------------|---------|-----------|
| Template → Derived | `core/templates/agent.md` → `core/agents/*.md` | Template references |
| Workflow → Workflow | `review.md` → `refinement.md` | Cross-references |
| Agent → Routing | `AGT-003` → `ROUTING_MAP.md` | Registry entries |
| Pack → Repo | `policy-pack-v1` → `collected/*/` | Pack references |

**Data Model** (adapted from ImportedFile):
```python
@dataclass
class DependencyNode:
    path: str
    dependents: List['DependencyNode']
    dependencies: List['DependencyNode']
    
    def affected_by_change(self) -> List[str]:
        """Return all nodes that need updating if this node changes."""
        result = []
        for dependent in self.dependents:
            result.append(dependent.path)
            result.extend(dependent.affected_by_change())
        return result
```

**Effort**: Medium  
**Impact**: Medium (intelligent cascading updates)

### LOW PRIORITY

#### R-09: Add Execution Timing and Analytics
**Action**: Track execution timing similar to Incrementalist's stopwatch pattern.

```python
@dataclass
class ExecutionMetrics:
    start_time: datetime
    end_time: datetime
    artifacts_analyzed: int
    artifacts_affected: int
    agents_invoked: int
    commands_executed: int
    failures: int
    
    @property
    def duration(self) -> timedelta:
        return self.end_time - self.start_time
    
    def to_log(self) -> str:
        return (
            f"Execution completed in {self.duration}\n"
            f"  Artifacts: {self.artifacts_affected}/{self.artifacts_analyzed} affected\n"
            f"  Agents: {self.agents_invoked} invoked\n"
            f"  Commands: {self.commands_executed} executed\n"
            f"  Failures: {self.failures}"
        )
```

**Effort**: Low  
**Impact**: Low (observability)

#### R-10: Implement Configuration File Auto-Generation
**Action**: Add `create-config` equivalent for AGENT-33.

```bash
# Generate config from current CLI options
agent-orchestrate create-config \
  --target-glob "core/**/*.md" \
  --parallel \
  --parallel-limit 4 \
  --output .agent-33/orchestrator.json
```

**Effort**: Low  
**Impact**: Low (convenience)

---

## Backlog Items Generated

| ID | Title | Priority | Source | Effort | Impact |
|----|-------|----------|--------|--------|--------|
| CA-007 | Design incremental artifact detection system | High | R-01 | Medium-High | High |
| CA-008 | Implement parallel execution control with semaphore | High | R-02 | Medium | High |
| CA-009 | Define solution-wide change triggers | High | R-03 | Low | High |
| CA-010 | Create JSON schemas for orchestration config | Medium | R-04 | Medium | Medium |
| CA-011 | Implement dry run mode for orchestration | Medium | R-05 | Low | Medium |
| CA-012 | Adopt MDC format for agent rule definitions | Medium | R-06 | Low | Medium |
| CA-013 | Add glob-based artifact filtering | Medium | R-07 | Low | Medium |
| CA-014 | Implement workflow dependency graph | Medium | R-08 | Medium | Medium |
| CA-015 | Add execution timing and analytics | Low | R-09 | Low | Low |
| CA-016 | Implement config file auto-generation | Low | R-10 | Low | Low |

---

## Integration Opportunities

### Direct Adoption Candidates

| Asset | Source | Target | Adaptation Notes |
|-------|--------|--------|------------------|
| Change detection pattern | DiffHelper.cs | core/workflows/ | Replace libgit2sharp with GitPython |
| Semaphore parallel control | RunDotNetCommandTask.cs | core/orchestrator/ | Use asyncio.Semaphore |
| Solution-wide triggers | SolutionWideChangeDetector.cs | core/workflows/ | Define AGENT-33 trigger files |
| JSON Schema pattern | incrementalist.schema.json | core/schemas/ | Create agent.schema.json |
| Config layering | ConfigMerger.cs | core/orchestrator/ | CLI > config file > defaults |
| MDC rule format | .cursor/rules/*.mdc | core/packs/ | Adapt frontmatter keys |
| Glob filtering | GlobFilter.cs | core/workflows/ | Use fnmatch or glob library |
| Build result types | BuildAnalysisResult.cs | core/workflows/ | RefinementResult union type |
| Dependency tracking | ProjectImportsFinder.cs | core/workflows/ | Parse markdown references |
| Timing metrics | RunDotNetCommandTask.cs | core/orchestrator/ | Track agent execution time |

### Adaptation Required

| Asset | Adaptation Needed |
|-------|-------------------|
| Git Analysis | Replace project graph with artifact dependency graph |
| Build Commands | Replace dotnet commands with agent invocations |
| MSBuild Integration | Replace with markdown/YAML parsing |
| Roslyn Analysis | Not applicable (documentation-focused) |
| Static Graph Engine | Not applicable (.NET-specific) |

### Not Applicable

| Asset | Reason |
|-------|--------|
| MSBuild Static Graph | .NET-specific tooling |
| Roslyn Workspace | Code analysis specific |
| .slnx Support | Solution file format |
| NuGet package management | .NET ecosystem |

---

## Technical Patterns Worth Adopting

### 1. Discriminated Union for Results

```python
from dataclasses import dataclass
from typing import Union, List

@dataclass
class FullRefinementResult:
    reason: str
    all_artifacts: List[str]

@dataclass
class IncrementalRefinementResult:
    affected_artifacts: List[str]
    trigger_files: List[str]

RefinementResult = Union[FullRefinementResult, IncrementalRefinementResult]

def process_result(result: RefinementResult) -> None:
    match result:
        case FullRefinementResult(reason=r, all_artifacts=a):
            print(f"Full refinement needed: {r}")
        case IncrementalRefinementResult(affected=a, triggers=t):
            print(f"Incremental: {len(a)} artifacts from {len(t)} triggers")
```

### 2. Linked Cancellation with Timeout

```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def timeout_context(timeout_seconds: int):
    """Create a cancellable context with timeout."""
    try:
        async with asyncio.timeout(timeout_seconds):
            yield
    except asyncio.TimeoutError:
        logging.warning(f"Operation timed out after {timeout_seconds}s")
        raise
```

### 3. Structured Logging for Analytics

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "artifact_analysis_complete",
    source_files=12,
    project_files=3,
    workflow_files=5,
    template_files=2,
    other_files=8,
    duration_ms=1234
)
```

### 4. Two-Phase Glob Filtering

```python
def filter_with_globs(
    items: List[str],
    include_patterns: List[str],
    exclude_patterns: List[str]
) -> List[str]:
    """
    Phase 1: Include only matching (whitelist)
    Phase 2: Exclude matching (blacklist)
    """
    # Phase 1: Whitelist
    if include_patterns:
        items = [i for i in items 
                if any(fnmatch(i, p) for p in include_patterns)]
    
    # Phase 2: Blacklist
    if exclude_patterns:
        items = [i for i in items 
                if not any(fnmatch(i, p) for p in exclude_patterns)]
    
    return items
```

---

## Summary Matrix

| Category | Incrementalist | AGENT-33 | Winner |
|----------|---------------|----------|--------|
| Change Detection | ★★★★★ | ★★☆☆☆ | Incrementalist |
| Dependency Analysis | ★★★★★ | ★★★☆☆ | Incrementalist |
| Parallel Execution | ★★★★★ | ★★☆☆☆ | Incrementalist |
| Configuration | ★★★★★ | ★★★☆☆ | Incrementalist |
| Agentic Rules | ★★★★☆ | ★★★☆☆ | Incrementalist |
| Cross-Repo Coordination | ★☆☆☆☆ | ★★★★★ | AGENT-33 |
| Session Continuity | ★☆☆☆☆ | ★★★★★ | AGENT-33 |
| Evidence Capture | ★★☆☆☆ | ★★★★★ | AGENT-33 |
| Multi-Agent Coordination | ★☆☆☆☆ | ★★★★★ | AGENT-33 |
| Model Agnosticism | ★★☆☆☆ | ★★★★★ | AGENT-33 |
| Documentation | ★★★★☆ | ★★★★☆ | Tie |
| CI/CD Integration | ★★★★★ | ★★★☆☆ | Incrementalist |

**Score Summary**:
- Incrementalist: 42/60 (70%)
- AGENT-33: 42/60 (70%)

The tools are **complementary**, excelling in different areas.

---

## Conclusion

Incrementalist and AGENT-33 solve different but related problems:

- **Incrementalist**: Best for detecting what changed and executing commands against only affected targets. Provides excellent patterns for dependency analysis, parallel execution, and configuration management.

- **AGENT-33**: Best for orchestrating multi-session, multi-repo workflows with evidence capture and governance. Provides audit trails and model-agnostic coordination.

**Strategic Recommendation**: Adopt Incrementalist's core patterns—incremental detection, dependency graphing, and parallel control—to enhance AGENT-33's orchestration capabilities. This would enable:

1. **Incremental Refinement Cycles**: Only process artifacts that changed
2. **Dependency-Aware Updates**: Know which downstream artifacts need updating
3. **Safe Parallel Execution**: Run multiple agents with resource limits
4. **Configuration Validation**: JSON schemas for agent/workflow definitions
5. **Structured Agentic Rules**: MDC format for domain-specific guidance

The result would be an **"Incremental Orchestration"** capability that combines AGENT-33's governance with Incrementalist's efficiency.

---

## Appendix: Key Source Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `DiffHelper.cs` | Git change detection | 50 |
| `SolutionWideChangeDetector.cs` | Full rebuild triggers | 120 |
| `ProjectImportsFinder.cs` | Dependency tracking | 90 |
| `EmitDependencyGraphTask.cs` | Analysis orchestration | 170 |
| `RunDotNetCommandTask.cs` | Parallel execution | 180 |
| `ConfigMerger.cs` | Config layering | 100 |
| `incrementalist.schema.json` | JSON validation | 110 |
| `coding-style.mdc` | C# agentic rules | 700+ |
| `testing.mdc` | xUnit agentic rules | 550+ |
| `incrementalist.mdc` | Project-specific rules | 230+ |

---

## References

- Source Repository: https://github.com/petabridge/Incrementalist
- Commit Analyzed: af973f9444415ed1f7d58bf7b1196688c5666d78
- Version: 1.2.0 (December 2025)
- Real-World Usage: Akka.NET, Akka.Management
- AGENT-33 Documentation: core/INDEX.md, core/ORCHESTRATION_INDEX.md
- Analysis Date: 2026-01-20
