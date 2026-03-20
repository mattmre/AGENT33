"""Validation for the horizontal-scaling architecture doc."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DOC_PATH = _REPO_ROOT / "docs" / "operators" / "horizontal-scaling-architecture.md"
_EXPECTED_SECTIONS = {
    "## Purpose",
    "## Current Deployment Guardrail",
    "## State Boundary Model",
    "## Shared Durable Surfaces Available Today",
    "## Single-Replica Durable But Not Shared Yet",
    "## Replica-Local Surfaces That Need Ownership or Affinity",
    "## Multi-Replica Blocking Surfaces",
    "## Storage and Ownership Constraints",
    "## Ingress and Transport Contract",
    "## Secondary Divergence Risks",
    "## P1.2 Migration Sequence",
    "## Readiness Gate Before `replicas > 1`",
}
_EXPECTED_STRINGS = {
    "production-deployment-runbook.md",
    "incident-response-playbooks.md",
    "service-level-objectives.md",
    "session102-p11-scaling-scope.md",
    "Do not increase the API deployment above `replicas: 1`",
    "engine/src/agent33/main.py",
    "engine/src/agent33/api/routes/auth.py",
    "engine/src/agent33/security/auth.py",
    "engine/src/agent33/api/routes/workflows.py",
    "engine/src/agent33/services/orchestration_state.py",
    "engine/src/agent33/api/routes/cron.py",
    "engine/src/agent33/automation/webhooks.py",
    "engine/src/agent33/automation/webhook_delivery.py",
    "engine/src/agent33/evaluation/service.py",
    "engine/src/agent33/evaluation/scheduled_gates.py",
    "engine/src/agent33/review/service.py",
    "engine/src/agent33/sessions/storage.py",
    "engine/src/agent33/workflows/ws_manager.py",
    "engine/src/agent33/tools/builtin/browser.py",
    "engine/src/agent33/multimodal/service.py",
    "engine/src/agent33/memory/observation.py",
    "engine/src/agent33/memory/bm25.py",
    "engine/src/agent33/tools/discovery_runtime.py",
    "engine/src/agent33/security/rate_limiter.py",
    "OrchestrationStateStore",
    "FileSessionStorage",
    "loaded once per process",
    "sticky routing or shared replay / pubsub state",
    "single-instance baseline",
}
_REFERENCED_PATHS = {
    _REPO_ROOT
    / "docs"
    / "operators"
    / "production-deployment-runbook.md": "production-deployment-runbook.md",
    _REPO_ROOT
    / "docs"
    / "operators"
    / "incident-response-playbooks.md": "incident-response-playbooks.md",
    _REPO_ROOT
    / "docs"
    / "operators"
    / "service-level-objectives.md": "service-level-objectives.md",
    _REPO_ROOT
    / "docs"
    / "research"
    / "session102-p11-scaling-scope.md": "session102-p11-scaling-scope.md",
}


def test_horizontal_scaling_doc_has_expected_sections_and_content() -> None:
    content = _DOC_PATH.read_text(encoding="utf-8")

    for section in _EXPECTED_SECTIONS:
        assert section in content, section

    for expected in _EXPECTED_STRINGS:
        assert expected in content, expected


def test_horizontal_scaling_doc_references_files_that_exist() -> None:
    content = _DOC_PATH.read_text(encoding="utf-8")

    for path, marker in _REFERENCED_PATHS.items():
        assert path.exists(), path
        assert marker in content
