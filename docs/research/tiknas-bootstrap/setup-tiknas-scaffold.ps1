<#
.SYNOPSIS
    TIKNAS v0 scaffolding bootstrap for Windows.

.DESCRIPTION
    Creates the initial directory structure for the TIKNAS repository at
    the target path (default: D:\GITHUB\TIKNAS). TIKNAS is the internal
    codename for the enterprise agent orchestration platform that will
    launch publicly as AGENTS33 on agents33.com.

    What this script does:
      1. Creates the target directory.
      2. Writes minimal scaffolding files (README, LICENSE placeholder,
         .gitignore, .gitattributes, CHANGELOG, folder READMEs).
      3. Creates the directory skeleton (core/, platform/,
         infrastructure/, docs/research/, docs/phases/).
      4. Copies the founding planning docs from D:\GITHUB\AGENT33\docs\
         research\ if that path exists (otherwise prints a TODO).
      5. Runs `git init` and creates a single initial commit.

    What this script deliberately does NOT do:
      - It does NOT push.
      - It does NOT create a GitHub remote.
      - It does NOT install dependencies or run docker.
      - It does NOT touch your existing AGENT33 worktree.

.PARAMETER Root
    Target directory. Default: D:\GITHUB\TIKNAS.

.PARAMETER Agent33Source
    Path to your local AGENT33 worktree, used only to copy planning
    docs. Default: D:\GITHUB\AGENT33. Pass -SkipDocCopy to skip.

.PARAMETER Force
    Allow scaffolding into an existing non-empty directory.

.PARAMETER SkipDocCopy
    Skip copying planning docs from AGENT33.

.EXAMPLE
    PS> .\setup-tiknas-scaffold.ps1

.EXAMPLE
    PS> .\setup-tiknas-scaffold.ps1 -Root 'D:\GITHUB\TIKNAS' -Agent33Source 'D:\GITHUB\AGENT33'

.NOTES
    Authored on AGENT33 branch: claude/plan-analysis-tool-yAI8I
    Companion docs:
      - docs/research/agent33-vs-tiknas-product-split.md
      - docs/research/opensearch-agent-observability-analysis.md
    Both are local-only (unpushed) on the AGENT33 branch above.
#>

[CmdletBinding()]
param(
    [string]$Root = 'D:\GITHUB\TIKNAS',
    [string]$Agent33Source = 'D:\GITHUB\AGENT33',
    [switch]$Force,
    [switch]$SkipDocCopy
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Write-Section($Text) {
    Write-Host ''
    Write-Host "==> $Text" -ForegroundColor Cyan
}

function Write-Created($Path) {
    Write-Host "    + $Path" -ForegroundColor Green
}

function Write-Skipped($Path, $Reason) {
    Write-Host "    . $Path  ($Reason)" -ForegroundColor DarkGray
}

# --- Preflight -----------------------------------------------------------

Write-Section "Preflight"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is not on PATH. Install git and re-run."
}

if (Test-Path $Root) {
    $existing = Get-ChildItem -Path $Root -Force -ErrorAction SilentlyContinue
    if ($existing -and -not $Force) {
        throw "'$Root' already exists and is non-empty. Re-run with -Force to merge into it."
    }
    Write-Host "    '$Root' exists; will merge into it." -ForegroundColor Yellow
} else {
    New-Item -ItemType Directory -Path $Root -Force | Out-Null
    Write-Created $Root
}

# --- Directory skeleton --------------------------------------------------

Write-Section "Directory skeleton"

$dirs = @(
    'core',
    'platform',
    'infrastructure',
    'docs',
    'docs/research',
    'docs/phases',
    'docs/operators'
)

foreach ($d in $dirs) {
    $full = Join-Path $Root $d
    if (Test-Path $full) {
        Write-Skipped $full "already exists"
    } else {
        New-Item -ItemType Directory -Path $full -Force | Out-Null
        Write-Created $full
    }
}

# --- Files: write only if missing ---------------------------------------

function Write-IfMissing {
    param([string]$RelPath, [string]$Body)
    $full = Join-Path $Root $RelPath
    if (Test-Path $full) {
        Write-Skipped $full "already exists"
        return
    }
    $dir = Split-Path $full -Parent
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    Set-Content -Path $full -Value $Body -Encoding UTF8 -NoNewline
    Write-Created $full
}

Write-Section "Scaffolding files"

# README.md (root) ----------------------------------------------------------
$readme = @"
# TIKNAS

> **Internal codename.** Public launch brand: **AGENTS33** on
> ``agents33.com``. All internal repos, packages, code identifiers,
> planning docs, and operator conversations use TIKNAS. Marketing
> surfaces flip to AGENTS33 at launch.

## What is TIKNAS

TIKNAS is the enterprise orchestration and engineering platform for AI
agent fleets. Its audience is AI engineers and AI architects responsible
for managing thousands of agents across hundreds of users — observability,
evals, fine-tuning, governance, and dashboards for AI-enriched data-driven
processes.

TIKNAS is **not** a re-implementation of an autonomous agent. The singular
autonomous-agent product is **AGENT33** (separate repo), which TIKNAS
imports as a versioned library. AGENT33 owns the contract surface (agent
definitions, capability taxonomy, trace conventions, tool schema, skill
manifest, workflow YAML). TIKNAS extends it with a fleet control plane.

## Status

**v0 scaffolding only.** No code yet. Planning docs in ``docs/research/``
are the founding charter; they originated on the AGENT33 branch
``claude/plan-analysis-tool-yAI8I`` and are imported here as the
authoritative roadmap.

## Repository layout

```
core/             # Versioned import surface from AGENT33 (contracts)
platform/         # TIKNAS-specific control plane and engine
infrastructure/   # Docker / Helm / IaC for deployment
docs/
  research/       # Strategic analysis (split, OpenSearch, landscape)
  phases/         # Phase plans (OS-0 decision spike, OS-1+ rollout)
  operators/      # Runbooks for ops owners
```

## Founding decisions (locked)

- Internal codename **TIKNAS**, public brand **AGENTS33**.
- Architecture **Option C** (library + platform): TIKNAS imports
  AGENT33 as a stable, versioned dependency.
- Platform vision: enterprise agent fleet management, observability,
  evals, governance.

## Open decisions (gating Phase OS-0)

See ``docs/research/agent33-vs-tiknas-product-split.md`` §10 — ten open
questions in three buckets (structural, productisation, scope). None of
them have been answered yet. No production code change happens until
Phase OS-0 is run.

## How TIKNAS relates to AGENT33

| | AGENT33 | TIKNAS |
|---|---|---|
| Product | One agent | Many agents |
| Audience | Solo operator | AI engineers / architects |
| Scale | Personal | Enterprise |
| Vector store | pgvector + BM25 | OpenSearch k-NN (Phase OS-0 decision) |
| Observability | In-memory + file | Langfuse + OpenSearch (Phase OS-0 decision) |
| License | Open (MIT-leaning) | Source-available + commercial enterprise (TBD Q4) |

## Local-only

This scaffold was created locally and is not pushed. The decision to
push (and create the GitHub remote) is gated on operator approval of the
split — see the AGENT33 branch ``claude/plan-analysis-tool-yAI8I`` for
the planning conversation that produced this layout.
"@
Write-IfMissing 'README.md' $readme

# LICENSE (placeholder) ---------------------------------------------------
$license = @"
TIKNAS — License posture: TBD

This is a scaffolding placeholder. The license posture for TIKNAS is an
open question (see docs/research/agent33-vs-tiknas-product-split.md §8
and §10 question Q4).

Current proposal (not yet ratified):
  - Source-available core under SSPL, BSL, or Elastic License v2.
  - Commercial enterprise features (SSO, fleet RBAC, audit, SLAs)
    distributed under a separate commercial license.
  - Same model as Langfuse, Posthog, Sentry.

Do not redistribute this codebase under any license until the operator
ratifies a posture and replaces this file. Internal use only until then.
"@
Write-IfMissing 'LICENSE' $license

# .gitignore --------------------------------------------------------------
$gitignore = @"
# TIKNAS .gitignore

# --- Python ---
__pycache__/
*.py[cod]
*`$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.mypy_cache/
.ruff_cache/
.tox/
.coverage
htmlcov/
.pyre/
.pytype/

# --- Virtual environments ---
.venv/
venv/
env/
ENV/
.python-version

# --- Node ---
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
.pnpm-store/
.next/
.nuxt/
.svelte-kit/
.vite/
.turbo/

# --- IDE ---
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# --- Local config ---
.env
.env.*
!.env.example
*.local

# --- OpenSearch / Langfuse / Dify spike artifacts ---
# Scratch from the Phase OS-0 decision spike. Do not commit.
.spike/
spike-data/
opensearch-data/
langfuse-data/
dify-data/

# --- Docker ---
docker-compose.override.yml

# --- Logs ---
*.log
logs/
"@
Write-IfMissing '.gitignore' $gitignore

# .gitattributes ----------------------------------------------------------
$gitattributes = @"
* text=auto eol=lf
*.ps1 text eol=crlf
*.bat text eol=crlf
*.cmd text eol=crlf
"@
Write-IfMissing '.gitattributes' $gitattributes

# CHANGELOG.md ------------------------------------------------------------
$changelog = @"
# Changelog

All notable changes to TIKNAS are recorded here.

This file follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- v0 scaffolding (this commit). Empty directory skeleton, README,
  LICENSE placeholder, ``.gitignore``, ``.gitattributes``, planning
  docs imported from AGENT33 branch ``claude/plan-analysis-tool-yAI8I``.

### Open
- Phase OS-0 decision spike (Path X / Y / Z) — see
  ``docs/research/opensearch-agent-observability-analysis.md`` §7.
- Ten gating questions — see
  ``docs/research/agent33-vs-tiknas-product-split.md`` §10.
"@
Write-IfMissing 'CHANGELOG.md' $changelog

# core/README.md ----------------------------------------------------------
$coreReadme = @"
# core/

The contract surface that TIKNAS imports from AGENT33.

## Purpose

This directory holds the **versioned import boundary** between AGENT33
and TIKNAS. Per the Option C architecture (see
``docs/research/agent33-vs-tiknas-product-split.md`` §4), AGENT33 owns
these primitives and TIKNAS treats them as stable contracts.

## What lives here

When the contract surface is extracted from AGENT33, this directory
will mirror or vendor:

- Agent-definition JSON schema
- Capability taxonomy (P/I/V/R/X)
- Trace conventions (``gen_ai.*`` semantic conventions, ``tenant_id``
  resource attribute, F-* failure taxonomy)
- Tool schema protocol (``SchemaAwareTool``, ``validated_execute``)
- Skill manifest format (SKILL.md frontmatter)
- Workflow definition format (DAG YAML)

## What does NOT live here

TIKNAS-specific code (control plane, dashboards, fleet evaluator)
lives in ``platform/``, not here. The rule of thumb: if it would also
be useful inside a single AGENT33 instance, it belongs in AGENT33.

## Status

Empty. Awaits the AGENT33 ``core-1.0`` extraction (see split doc §11
sequencing step 2).
"@
Write-IfMissing 'core/README.md' $coreReadme

# platform/README.md ------------------------------------------------------
$platformReadme = @"
# platform/

TIKNAS-specific control plane and engine.

## Purpose

Code that exists *only* in TIKNAS — fleet management, multi-runtime
control plane, multi-tenant routing, dashboards, evals across runs.

## What lives here

Initial expected layout (post Phase OS-0):

- ``control_plane/`` — adapter pattern over multiple agent runtimes
  (AGENT33, LangGraph, Claude Agent SDK, ML Commons V2, CrewAI).
- ``fleet/`` — multi-agent fleet operations (rollout, drain, recall).
- ``observability/`` — TIKNAS-side OTel collector wiring + OpenSearch
  ingestion config + Langfuse client (depending on Path X / Y / Z).
- ``evaluation/`` — fleet-scale evals + regression detection.
- ``governance/`` — autonomy budgets, escalation, audit at fleet level.
- ``api/`` — TIKNAS public API.
- ``ui/`` — TIKNAS web app (dashboards, fleet view, run inspector).

## Status

Empty. Awaits Phase OS-1 (Telemetry Backbone) once Phase OS-0 settles.
"@
Write-IfMissing 'platform/README.md' $platformReadme

# infrastructure/README.md ------------------------------------------------
$infraReadme = @"
# infrastructure/

Deployment surface for TIKNAS.

## Purpose

Docker compose, Helm charts, IaC modules, and operator runbooks for
running TIKNAS at various scales.

## Expected layout

- ``docker-compose/`` — local dev profiles (the Phase OS-0 spike stack
  lives here when it lands: Langfuse + OpenSearch + Dify side-by-side).
- ``helm/`` — production Helm chart for fleet-scale deployment.
- ``terraform/`` — optional cloud module bundle.
- ``observability/`` — saved OpenSearch Dashboards NDJSON, anomaly
  detector definitions, Langfuse seed data.

## Status

Empty. Phase OS-0 docker-compose drops here first.
"@
Write-IfMissing 'infrastructure/README.md' $infraReadme

# docs/README.md ----------------------------------------------------------
$docsReadme = @"
# docs/

Living documentation for TIKNAS.

## Subdirectories

- ``research/`` — strategic analysis. Founding charter docs (split,
  OpenSearch, competitive landscape) live here.
- ``phases/`` — phase plans (Phase OS-0 decision spike, OS-1
  telemetry backbone, OS-2 multi-source CLI capture, etc.). Lifted from
  the OpenSearch rev-2 plan in ``research/`` once each phase is approved.
- ``operators/`` — runbooks for ops owners (deployment, upgrade,
  incident response).

## Reading order for new contributors

1. Root ``README.md`` — what TIKNAS is.
2. ``research/agent33-vs-tiknas-product-split.md`` — strategic case.
3. ``research/opensearch-agent-observability-analysis.md`` — technical
   integration plan.
4. ``research/`` for the rest — landscape, decisions, spikes.
"@
Write-IfMissing 'docs/README.md' $docsReadme

# placeholders for empty dirs --------------------------------------------
foreach ($keep in @('docs/research/.gitkeep', 'docs/phases/.gitkeep', 'docs/operators/.gitkeep')) {
    Write-IfMissing $keep ""
}

# --- Copy planning docs from AGENT33 -------------------------------------

if ($SkipDocCopy) {
    Write-Section "Planning doc import (skipped via -SkipDocCopy)"
} elseif (-not (Test-Path $Agent33Source)) {
    Write-Section "Planning doc import"
    Write-Host "    AGENT33 worktree not found at '$Agent33Source'." -ForegroundColor Yellow
    Write-Host "    TODO: After fetching the claude/plan-analysis-tool-yAI8I" -ForegroundColor Yellow
    Write-Host "    branch in your AGENT33 worktree, copy these files manually:" -ForegroundColor Yellow
    Write-Host "      docs/research/agent33-vs-tiknas-product-split.md" -ForegroundColor Yellow
    Write-Host "      docs/research/opensearch-agent-observability-analysis.md" -ForegroundColor Yellow
    Write-Host "    into TIKNAS at docs/research/." -ForegroundColor Yellow
} else {
    Write-Section "Planning doc import from $Agent33Source"
    $sourceDir = Join-Path $Agent33Source 'docs\research'
    $targetDir = Join-Path $Root 'docs\research'
    $docs = @(
        'agent33-vs-tiknas-product-split.md',
        'opensearch-agent-observability-analysis.md'
    )
    foreach ($doc in $docs) {
        $src = Join-Path $sourceDir $doc
        $dst = Join-Path $targetDir $doc
        if (-not (Test-Path $src)) {
            Write-Host "    ! $doc not found in source. Are you on branch claude/plan-analysis-tool-yAI8I?" -ForegroundColor Yellow
            continue
        }
        if ((Test-Path $dst) -and -not $Force) {
            Write-Skipped $dst "already exists (use -Force to overwrite)"
            continue
        }
        Copy-Item -Path $src -Destination $dst -Force
        Write-Created $dst
    }
}

# --- git init + initial commit ------------------------------------------

Write-Section "Git initialization"

Push-Location $Root
try {
    if (Test-Path '.git') {
        Write-Host "    git repo already initialized; skipping git init." -ForegroundColor DarkGray
    } else {
        git init --initial-branch=main 2>&1 | Out-Host
    }

    $status = git status --porcelain 2>&1
    if (-not $status) {
        Write-Host "    Working tree already clean; nothing to commit." -ForegroundColor DarkGray
    } else {
        git add . 2>&1 | Out-Host
        $commitMsg = "chore: initial TIKNAS scaffolding (v0, local-only)`n`n" +
                     "Internal codename TIKNAS for the enterprise agent orchestration`n" +
                     "platform that will launch publicly as AGENTS33 on agents33.com.`n`n" +
                     "Scaffolded by docs/research/tiknas-bootstrap/setup-tiknas-scaffold.ps1`n" +
                     "from AGENT33 branch claude/plan-analysis-tool-yAI8I.`n`n" +
                     "Status: scaffolding only. No code, no remote, no push."
        git commit -m $commitMsg 2>&1 | Out-Host
    }
} finally {
    Pop-Location
}

# --- Summary ------------------------------------------------------------

Write-Section "Summary"
Write-Host ""
Write-Host "  TIKNAS scaffolded at: $Root" -ForegroundColor Green
Write-Host ""
Write-Host "  Next manual steps (operator decision required):" -ForegroundColor Cyan
Write-Host "    1. Review docs/research/ planning docs."
Write-Host "    2. Answer the ten gating questions in"
Write-Host "       docs/research/agent33-vs-tiknas-product-split.md §10."
Write-Host "    3. Run Phase OS-0 decision spike (stand up Langfuse +"
Write-Host "       OpenSearch + Dify locally, score the matrices)."
Write-Host "    4. Decide whether to create a GitHub remote."
Write-Host ""
Write-Host "  Nothing has been pushed. Nothing has touched AGENT33." -ForegroundColor DarkGray
Write-Host ""
