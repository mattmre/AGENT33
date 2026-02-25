"""Signal enrichment and quality scoring for automated intake generation."""

from __future__ import annotations

from agent33.improvement.models import LearningSignal, LearningSignalSeverity


def enrich_learning_signal(signal: LearningSignal) -> LearningSignal:
    """Apply deterministic quality scoring and enrichment metadata."""
    summary_len = len(signal.summary.strip())
    details_len = len(signal.details.strip())
    source_present = bool(signal.source.strip())
    context_items = len(signal.context)

    dimensions: dict[str, float] = {
        "summary": min(1.0, summary_len / 80.0),
        "details": min(1.0, details_len / 160.0),
        "source": 1.0 if source_present else 0.0,
        "context": min(1.0, context_items / 5.0),
        "severity": _severity_quality(signal.severity),
    }
    weights = {
        "summary": 0.25,
        "details": 0.20,
        "source": 0.10,
        "context": 0.10,
        "severity": 0.35,
    }
    score = sum(dimensions[name] * weight for name, weight in weights.items())
    quality_score = round(min(1.0, max(0.0, score)), 3)

    quality_label = "low"
    if quality_score >= 0.70:
        quality_label = "high"
    elif quality_score >= 0.45:
        quality_label = "medium"

    reasons = []
    if summary_len < 20:
        reasons.append("summary_too_short")
    if details_len == 0:
        reasons.append("details_missing")
    if not source_present:
        reasons.append("source_missing")
    if context_items == 0:
        reasons.append("context_missing")
    if not reasons:
        reasons.append("well_formed_signal")

    signal.quality_score = quality_score
    signal.quality_label = quality_label
    signal.quality_reasons = reasons
    signal.enrichment = {
        "has_source": str(source_present).lower(),
        "context_items": str(context_items),
        "summary_length": str(summary_len),
        "details_length": str(details_len),
    }
    return signal


def _severity_quality(severity: LearningSignalSeverity) -> float:
    return {
        LearningSignalSeverity.LOW: 0.3,
        LearningSignalSeverity.MEDIUM: 0.55,
        LearningSignalSeverity.HIGH: 0.8,
        LearningSignalSeverity.CRITICAL: 1.0,
    }[severity]
