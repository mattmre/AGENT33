# CLAUDE Addendum (Project-Specific Contexts)

This file holds condensed context for non-RSMF projects.

## EDCToolkit
- Purpose: Windows Forms (.NET 8.0) eDiscovery data processing for DAT/CSV/DII load files.
- Status: Refinement Remediation Cycle (last updated 2026-01-16; PRs #87-94 merged).
- Build: `dotnet build WindowsFormsApplication19`
- Tests: clean temp folder then `dotnet test EDCToolkit.Tests` (expect 655 passing).
- Known: flaky encoding test if temp not cleaned; high warning count expected.
- Next: finish remaining MEDIUM/LOW remediation items; plan namespace standardization.

## EDCwayback
- Purpose: forensic web archive collection platform.
- Status: Phase 1.1 Configuration Management complete; Phase 1.2 Database Layer next.
- Core: config schema/loader/encryption, CLI subcommands, /config API.
- CLI: `edc run jobs.csv`, `edc config show/validate/init`, `edc config encrypt-value`.
- Tests: config/encryption/API tests run without playwright; full suite requires playwright.
- Known: Windows key ACLs, duplicated `_mask_sensitive`, long `cmd_run`.

## Claudius Maximus
- Purpose: crawl eDiscovery KBs, process with local LLM, produce narrative specs.
- Run: start local LLM runtime, then `python monitor_relevance.py`.
- Status: ~25% processed as of 2026-01-14; state persists in `processing_state.json`.
- Pipeline: 5-step post-processing pipeline in `pipeline/` (parse, catalog, dedup, deps, phases).
- Risks: long processing time, duplicate copy folders, truncation in source crawls.
