"""Prompt injection detection and defence."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Scan result
# ---------------------------------------------------------------------------


@dataclass
class ScanResult:
    """Outcome of a prompt-injection scan."""

    is_safe: bool
    threats: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

_SYSTEM_OVERRIDE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|directives)", re.I),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|directives)", re.I),
    re.compile(r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|directives)", re.I),
    re.compile(r"you\s+are\s+now\s+(?:a|an|the)\s+", re.I),
    re.compile(r"new\s+system\s+prompt", re.I),
    re.compile(r"override\s+system\s+(prompt|message|instructions)", re.I),
]

_DELIMITER_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"```\s*system", re.I),
    re.compile(r"\[SYSTEM\]", re.I),
    re.compile(r"<\|?(system|im_start|endoftext)\|?>", re.I),
    re.compile(r"###\s*(system|instruction)", re.I),
    re.compile(r"<\s*/?system\s*>", re.I),
]

_INSTRUCTION_OVERRIDE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"do\s+not\s+follow\s+(your|the)\s+(original|initial)", re.I),
    re.compile(r"instead\s*,?\s+follow\s+these\s+instructions", re.I),
    re.compile(r"act\s+as\s+if\s+you\s+have\s+no\s+(restrictions|rules|guidelines)", re.I),
    re.compile(r"pretend\s+(that\s+)?you\s+(are|have)\s+no\s+(rules|restrictions)", re.I),
    re.compile(r"reveal\s+(your|the)\s+(system|initial|original)\s+(prompt|instructions)", re.I),
]


def _check_encoded_payloads(text: str) -> list[str]:
    """Attempt to detect base64-encoded injection payloads."""
    threats: list[str] = []
    b64_re = re.compile(r"[A-Za-z0-9+/=]{40,}")
    for match in b64_re.finditer(text):
        try:
            decoded = base64.b64decode(match.group(), validate=True).decode("utf-8", errors="ignore")
            # Re-scan the decoded content for known attack patterns
            for pat in _SYSTEM_OVERRIDE_PATTERNS + _INSTRUCTION_OVERRIDE_PATTERNS:
                if pat.search(decoded):
                    threats.append(f"encoded_payload: hidden injection in base64 segment")
                    return threats
        except Exception:
            continue
    return threats


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scan_input(text: str) -> ScanResult:
    """Scan *text* for prompt-injection attempts.

    Returns a :class:`ScanResult` with ``is_safe=True`` when no threats are
    detected.
    """
    threats: list[str] = []

    for pat in _SYSTEM_OVERRIDE_PATTERNS:
        if pat.search(text):
            threats.append("system_prompt_override")
            break

    for pat in _DELIMITER_INJECTION_PATTERNS:
        if pat.search(text):
            threats.append("delimiter_injection")
            break

    for pat in _INSTRUCTION_OVERRIDE_PATTERNS:
        if pat.search(text):
            threats.append("instruction_override")
            break

    threats.extend(_check_encoded_payloads(text))

    return ScanResult(is_safe=len(threats) == 0, threats=threats)
