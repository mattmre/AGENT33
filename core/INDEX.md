# AGENT-33 Documentation Index

## Project Overview

AGENT-33 is a master aggregation repo for model-agnostic orchestration workflows, agent guidance, and reusable governance assets.

---

## Quick Links

| Document | Description |
|----------|-------------|
| [Orchestration Index](ORCHESTRATION_INDEX.md) | Entry point for orchestration workflows |
| [Core README](README.md) | Canonical core structure and usage |
| [Phase Planning](../docs/phase-planning.md) | AGENT-33 development phases |
| [Phase Index](../docs/phases/README.md) | AGENT-33 phase list and sequencing |

---

## Research Documents

| Document | Description |
|----------|-------------|
| [Agentic Orchestration Trends 2025H2](research/agentic-orchestration-trends-2025H2.md) | Industry trends and guidance for agentic coding |
| [OpenClaw Security Analysis](research/06-OPENCLAW-SECURITY-ANALYSIS.md) | Security vulnerability analysis of OpenClaw platform |
| [OpenClaw Feature Parity](research/07-OPENCLAW-FEATURE-PARITY.md) | Feature comparison and security hardening mapping |

---

## Phase Templates (Generic)

| Document | Description |
|----------|-------------|
| [Phase Templates](phases/README.md) | Generic, reusable phase outlines (examples) |

---

## AGENT-33 Phase Plan

The canonical AGENT-33 phases live in `docs/phases/`.
Use the phase index for sequencing and dependency order:
`../docs/phases/README.md`

---

## Platform Integration Specifications (CA-017)

| Document | Description |
|----------|-------------|
| [Integration Specs Index](orchestrator/integrations/README.md) | Overview, design principles, and integration checklist |
| [Channel Integration](orchestrator/integrations/CHANNEL_INTEGRATION_SPEC.md) | Multi-platform messaging channel architecture |
| [Voice & Media](orchestrator/integrations/VOICE_MEDIA_SPEC.md) | Voice interaction and media processing (privacy-first) |
| [Credential Management](orchestrator/integrations/CREDENTIAL_MANAGEMENT_SPEC.md) | Vault-backed credential storage and rotation |
| [Privacy Architecture](orchestrator/integrations/PRIVACY_ARCHITECTURE.md) | Encryption at rest, consent model, data lifecycle |

---

---

## Agentic Engineering And Planning

| Document | Description |
|----------|-------------|
| [ARCH-AEP Overview](arch/README.md) | Narrative overview for ARCH-AEP |
| [ARCH-AEP Orchestrator Briefing](arch/orchestrator-briefing.md) | Session-start narrative and folder index |
| [ARCH-AEP Workflow Spec](arch/workflow.md) | End-to-end workflow specification |
| [ARCH-AEP Templates](arch/templates.md) | ID, branch, and tracker conventions |
| [ARCH-AEP Next Session](arch/next-session.md) | Session handoff checklist |
| [ARCH-AEP Phase Planning](arch/phase-planning.md) | Long-running planning record |
| [ARCH-AEP Schedule And Tracking](arch/schedule-and-tracking.md) | Cadence and gates |
| [ARCH-AEP Tier Close Checklist](arch/tier-close-checklist.md) | Tier close audit checklist |
| [ARCH-AEP Cycle Summary Template](arch/cycle-summary-template.md) | End-of-cycle summary template |
| [ARCH-AEP Cycle Summaries](arch/cycle-summaries/README.md) | Cycle summary storage location |
| [ARCH-AEP Backlog Template](arch/backlog-template.md) | Master backlog template |
| [ARCH-AEP Backlog Index](arch/backlog-index.md) | Backlog index across cycles |
| [ARCH-AEP Tracker Pointer](arch/tracker-pointer.md) | Active tracker link |
| [ARCH-AEP Tracker Index](arch/tracker-index.md) | Tracker index across cycles |
| [ARCH-AEP Verification Log](arch/verification-log.md) | Test/build evidence log |
| [ARCH-AEP Phase Summary Template](arch/phase-summary-template.md) | Per-PR or per-phase summary template |
| [ARCH-AEP Phase Summaries](arch/phase-summaries/README.md) | Phase summary storage location |
| [ARCH-AEP Risk Memo Template](arch/risk-memo-template.md) | Critical/High risk memo template |
| [ARCH-AEP Risk Memos](arch/risk-memos/README.md) | Risk memo storage location |
| [ARCH-AEP Risk Memo Archive](arch/risk-memos/closed/README.md) | Closed risk memo archive |
| [ARCH-AEP Agent Learning](arch/agent-learning.md) | Cross-session learnings |
| [ARCH-AEP Change Log](arch/change-log.md) | Scope/defer decision log |
| [ARCH-AEP Scope Lock Template](arch/scope-lock-template.md) | Scope lock record |
| [ARCH-AEP Glossary](arch/glossary.md) | Shared terminology |
| [ARCH-AEP Test Matrix](arch/test-matrix.md) | Test selection guidance |
| [ARCH-AEP Active Tracker Template](arch/active-tracker-template.md) | Tracker template with lock block |
| [ARCH-AEP Cycle Layout Template](arch/cycle-layout-template.md) | Optional parallel cycle layout |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total Phase Templates | 40 |
| AGENT-33 Phases | 10 |
| Research Documents | 3 |

---

## Getting Started

### For Developers
1. Start at `core/ORCHESTRATION_INDEX.md`
2. Follow `core/orchestrator/README.md` and `core/orchestrator/OPERATOR_MANUAL.md`
3. Use `core/arch/workflow.md` for AEP cycles

### For AI Agents
1. Read `core/agents/CLAUDE.md` for agent instructions
2. Follow `core/orchestrator/AGENT_REGISTRY.md` for role definitions
3. Use `core/orchestrator/AGENT_ROUTING_MAP.md` for task routing

### For Project Planning
1. Review `docs/phases/README.md` for phase index
2. Consult [Feature Comparison Matrix](research/05-FEATURE-COMPARISON-MATRIX.md)
3. Review `core/orchestrator/COMPETITIVE_FEATURES_INDEX.md` for feature backlog

---

## Document Maintenance

This documentation should be updated as:
- New phases are completed
- Requirements change
- New research is conducted
- Community feedback is incorporated

Last Updated: 2026-01-30
