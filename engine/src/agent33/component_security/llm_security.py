"""AI/LLM security scanning for AGENT-33.

Provides prompt injection detection, tool definition poisoning checks
(OWASP MCP-01), and integration points for LLM Guard and Garak.
"""

from __future__ import annotations

import importlib
from typing import Any

import structlog

from agent33.component_security.models import (
    FindingCategory,
    FindingSeverity,
    SecurityFinding,
)
from agent33.security.injection import ScanResult, scan_input, scan_inputs_recursive

logger = structlog.get_logger()

# Optional-dependency guards — same pattern as mcp_server/jupyter adapters.
# These are set at import time so test code can patch them as module attributes.
_HAS_LLMGUARD = False
try:
    import llm_guard  # noqa: F401
    _HAS_LLMGUARD = True
except ImportError:
    pass

_HAS_GARAK = False
try:
    import garak  # noqa: F401
    _HAS_GARAK = True
except ImportError:
    pass

# OWASP MCP Top 10 category mapping
# See: https://owasp.org/www-project-top-10-for-large-language-model-applications/
OWASP_MCP_CATEGORIES: dict[str, tuple[str, FindingCategory]] = {
    "MCP-01": ("Tool Poisoning", FindingCategory.TOOL_POISONING),
    "MCP-02": ("Excessive Agency", FindingCategory.AUTHORIZATION_BYPASS),
    "MCP-03": ("Tool Shadowing", FindingCategory.TOOL_POISONING),
    "MCP-04": ("Rug Pull", FindingCategory.SUPPLY_CHAIN),
    "MCP-05": ("Server Compromise", FindingCategory.SUPPLY_CHAIN),
    "MCP-06": ("Indirect Prompt Injection", FindingCategory.PROMPT_INJECTION),
    "MCP-07": ("Resource Exhaustion", FindingCategory.CONFIGURATION_ISSUE),
    "MCP-08": ("Consent & Data Privacy", FindingCategory.MODEL_SECURITY),
    "MCP-09": ("Supply Chain Attack", FindingCategory.SUPPLY_CHAIN),
    "MCP-10": ("Authentication Bypass", FindingCategory.AUTHENTICATION_WEAKNESS),
}

# Suspicious patterns in tool descriptions that indicate poisoning (MCP-01)
_POISONING_PATTERNS: list[tuple[str, str]] = [
    ("ignore previous", "Tool description attempts to override system instructions"),
    ("disregard", "Tool description contains instruction override attempt"),
    ("you must", "Tool description contains coercive instruction"),
    ("do not tell", "Tool description attempts to hide behavior from user"),
    ("secret", "Tool description references hidden behavior"),
    ("always call this tool first", "Tool description demands priority execution"),
    ("before any other tool", "Tool description demands priority execution"),
    ("<system>", "Tool description contains system prompt delimiter"),
    ("[SYSTEM]", "Tool description contains system prompt delimiter"),
    ("```system", "Tool description contains system prompt code block"),
]

# Suspicious patterns in tool input schemas that indicate shadowing (MCP-03)
_SHADOWING_PATTERNS: list[tuple[str, str]] = [
    ("override", "Schema property name suggests override behavior"),
    ("hidden", "Schema property name suggests hidden behavior"),
    ("system_prompt", "Schema exposes system prompt manipulation"),
    ("inject", "Schema property name suggests injection vector"),
]


class LLMSecurityScanner:
    """Scans for AI/LLM-specific security threats.

    Integrates with existing prompt injection detection from
    agent33.security.injection and adds tool definition scanning
    per OWASP MCP Top 10 guidelines.
    """

    def scan_prompt_safety(
        self,
        text: str,
        *,
        run_id: str = "",
        source: str = "user_input",
    ) -> list[SecurityFinding]:
        """Scan text for prompt injection threats.

        Wraps the existing scan_input() function and converts results
        to SecurityFinding format.

        Args:
            text: Text to scan for injection attempts.
            run_id: Security run ID to associate findings with.
            source: Description of where the text came from.

        Returns:
            List of SecurityFindings for detected threats.
        """
        result = scan_input(text)
        return self._scan_result_to_findings(result, run_id=run_id, source=source, text=text)

    def scan_nested_inputs(
        self,
        data: object,
        *,
        run_id: str = "",
        source: str = "structured_input",
    ) -> list[SecurityFinding]:
        """Scan nested data structures for prompt injection.

        Wraps scan_inputs_recursive() and converts results.

        Args:
            data: Nested dict/list/string structure to scan.
            run_id: Security run ID to associate findings with.
            source: Description of where the data came from.

        Returns:
            List of SecurityFindings for detected threats.
        """
        result = scan_inputs_recursive(data)
        return self._scan_result_to_findings(
            result, run_id=run_id, source=source, text=str(data)[:200]
        )

    def scan_tool_definitions(
        self,
        tools: list[dict[str, Any]],
        *,
        run_id: str = "",
    ) -> list[SecurityFinding]:
        """Check tool definitions for poisoning/shadowing patterns.

        Implements OWASP MCP-01 (Tool Poisoning) and MCP-03 (Tool Shadowing)
        detection by scanning tool names, descriptions, and input schemas
        for suspicious patterns.

        Args:
            tools: List of tool definition dicts, each with 'name',
                   'description', and optionally 'input_schema'/'parameters'.
            run_id: Security run ID to associate findings with.

        Returns:
            List of SecurityFindings for detected threats.
        """
        findings: list[SecurityFinding] = []

        for tool in tools:
            tool_name = tool.get("name", "unknown")
            description = tool.get("description", "")
            schema = tool.get("input_schema") or tool.get("parameters", {})

            # Check description for poisoning patterns (MCP-01)
            desc_lower = description.lower()
            for pattern, reason in _POISONING_PATTERNS:
                if pattern.lower() in desc_lower:
                    findings.append(
                        SecurityFinding(
                            run_id=run_id,
                            severity=FindingSeverity.HIGH,
                            category=FindingCategory.TOOL_POISONING,
                            title=f"Tool poisoning detected in '{tool_name}'",
                            description=(
                                f"OWASP MCP-01: {reason}. "
                                f"Pattern '{pattern}' found in tool description."
                            ),
                            tool="llm-security",
                            remediation=(
                                "Review and sanitize tool description. "
                                "Remove any instruction override attempts."
                            ),
                        )
                    )
                    break  # One finding per tool for description

            # Run injection scanner on description
            desc_result = scan_input(description)
            if not desc_result.is_safe:
                findings.append(
                    SecurityFinding(
                        run_id=run_id,
                        severity=FindingSeverity.CRITICAL,
                        category=FindingCategory.TOOL_POISONING,
                        title=f"Injection in tool description: '{tool_name}'",
                        description=(
                            f"OWASP MCP-01: Tool description contains prompt "
                            f"injection patterns: {', '.join(desc_result.threats)}"
                        ),
                        tool="llm-security",
                        remediation=(
                            "Remove injection payloads from tool description. "
                            "This tool definition should not be trusted."
                        ),
                    )
                )

            # Check schema for shadowing patterns (MCP-03)
            if isinstance(schema, dict):
                properties = schema.get("properties", {})
                for prop_name in properties:
                    prop_lower = prop_name.lower()
                    for pattern, reason in _SHADOWING_PATTERNS:
                        if pattern in prop_lower:
                            findings.append(
                                SecurityFinding(
                                    run_id=run_id,
                                    severity=FindingSeverity.MEDIUM,
                                    category=FindingCategory.TOOL_POISONING,
                                    title=(f"Suspicious schema in '{tool_name}'"),
                                    description=(
                                        f"OWASP MCP-03: {reason}. "
                                        f"Property '{prop_name}' in tool "
                                        f"'{tool_name}'."
                                    ),
                                    tool="llm-security",
                                    remediation=(
                                        "Review tool schema properties. "
                                        "Rename or remove suspicious parameters."
                                    ),
                                )
                            )
                            break  # One finding per property

        logger.info(
            "llm_security_tool_scan_complete",
            tools_scanned=len(tools),
            findings_count=len(findings),
        )
        return findings

    def _scan_result_to_findings(
        self,
        result: ScanResult,
        *,
        run_id: str,
        source: str,
        text: str,
    ) -> list[SecurityFinding]:
        """Convert injection ScanResult to SecurityFindings."""
        if result.is_safe:
            return []

        findings: list[SecurityFinding] = []
        for threat in result.threats:
            severity = self._threat_severity(threat)
            findings.append(
                SecurityFinding(
                    run_id=run_id,
                    severity=severity,
                    category=FindingCategory.PROMPT_INJECTION,
                    title=f"Prompt injection detected: {threat}",
                    description=(
                        f"Detected '{threat}' in {source}. Input preview: {text[:100]}..."
                    ),
                    tool="llm-security",
                    remediation=(
                        "Sanitize or reject this input. Do not pass it "
                        "directly to LLM system prompts."
                    ),
                )
            )
        return findings

    @staticmethod
    def _threat_severity(threat: str) -> FindingSeverity:
        """Map threat type to severity."""
        if threat in {"system_prompt_override", "encoded_payload"}:
            return FindingSeverity.CRITICAL
        if threat in {"delimiter_injection", "instruction_override"}:
            return FindingSeverity.HIGH
        return FindingSeverity.MEDIUM


class LLMGuardAdapter:
    """Adapter for Protect AI's LLM Guard integration.

    LLM Guard (MIT, 4.5k+ stars) provides input/output scanners for:
    - Prompt injection detection
    - Toxicity filtering
    - PII detection and anonymization
    - Invisible text detection

    Uses lazy imports so the llm-guard package is only required when
    scanner methods are actually called.
    """

    @staticmethod
    def is_available() -> bool:
        """Check if llm-guard package is installed."""
        return _HAS_LLMGUARD

    def scan_input(
        self, text: str, *, run_id: str = ""
    ) -> list[SecurityFinding]:
        """Scan input text using LLM Guard scanners.

        Runs PromptInjection, Toxicity, and InvisibleText scanners
        against the supplied text and returns findings for any flagged
        content.
        """
        if not self.is_available():
            logger.info("llm_guard_not_available", adapter="scan_input")
            return []
        try:
            llm_guard_mod = importlib.import_module("llm_guard")
            input_scanners = importlib.import_module(
                "llm_guard.input_scanners"
            )

            scanners = [
                input_scanners.PromptInjection(threshold=0.5),
                input_scanners.Toxicity(threshold=0.5),
                input_scanners.InvisibleText(),
            ]
            sanitized, results_valid, results_score = (
                llm_guard_mod.scan_prompt(scanners, text)
            )

            findings: list[SecurityFinding] = []
            scanner_names = [
                "PromptInjection",
                "Toxicity",
                "InvisibleText",
            ]
            for name, is_valid, score in zip(
                scanner_names, results_valid, results_score, strict=False
            ):
                if not is_valid:
                    findings.append(
                        SecurityFinding(
                            run_id=run_id or "adhoc",
                            severity=self._score_to_severity(score),
                            category=self._scanner_to_category(name),
                            title=(
                                f"LLM Guard: {name} detected in input"
                            ),
                            description=(
                                f"{name} scanner flagged input text "
                                f"(score: {score:.2f})"
                            ),
                            tool="llm-guard",
                        )
                    )
            return findings
        except Exception:
            logger.warning(
                "llm_guard_scan_input_failed", exc_info=True
            )
            return []

    def scan_output(
        self, text: str, *, run_id: str = ""
    ) -> list[SecurityFinding]:
        """Scan LLM output using LLM Guard scanners.

        Runs Sensitive and NoRefusal scanners against the supplied
        output text and returns findings for any flagged content.
        """
        if not self.is_available():
            logger.info("llm_guard_not_available", adapter="scan_output")
            return []
        try:
            llm_guard_mod = importlib.import_module("llm_guard")
            output_scanners = importlib.import_module(
                "llm_guard.output_scanners"
            )

            scanners = [
                output_scanners.Sensitive(),
                output_scanners.NoRefusal(),
            ]
            sanitized, results_valid, results_score = (
                llm_guard_mod.scan_output(scanners, "", text)
            )

            findings: list[SecurityFinding] = []
            scanner_names = ["Sensitive", "NoRefusal"]
            for name, is_valid, score in zip(
                scanner_names, results_valid, results_score, strict=False
            ):
                if not is_valid:
                    findings.append(
                        SecurityFinding(
                            run_id=run_id or "adhoc",
                            severity=self._score_to_severity(score),
                            category=self._scanner_to_category(name),
                            title=(
                                f"LLM Guard: {name} detected in output"
                            ),
                            description=(
                                f"{name} scanner flagged output text "
                                f"(score: {score:.2f})"
                            ),
                            tool="llm-guard",
                        )
                    )
            return findings
        except Exception:
            logger.warning(
                "llm_guard_scan_output_failed", exc_info=True
            )
            return []

    @staticmethod
    def _score_to_severity(score: float) -> FindingSeverity:
        """Map a 0–1 scanner score to a severity level."""
        if score >= 0.9:
            return FindingSeverity.CRITICAL
        if score >= 0.7:
            return FindingSeverity.HIGH
        if score >= 0.5:
            return FindingSeverity.MEDIUM
        return FindingSeverity.LOW

    @staticmethod
    def _scanner_to_category(scanner_name: str) -> FindingCategory:
        """Map an LLM Guard scanner name to a finding category."""
        mapping: dict[str, FindingCategory] = {
            "PromptInjection": FindingCategory.PROMPT_INJECTION,
            "Toxicity": FindingCategory.MODEL_SECURITY,
            "InvisibleText": FindingCategory.PROMPT_INJECTION,
            "Sensitive": FindingCategory.SECRETS_EXPOSURE,
            "NoRefusal": FindingCategory.MODEL_SECURITY,
        }
        return mapping.get(
            scanner_name, FindingCategory.MODEL_SECURITY
        )


class GarakAdapter:
    """Adapter for NVIDIA's Garak LLM vulnerability scanner.

    Garak (Apache-2.0, 3k+ stars) provides:
    - Prompt injection probes
    - Data leakage detection
    - Hallucination testing
    - Toxicity generation testing

    Uses lazy imports so the garak package is only required when
    probe methods are actually called.
    """

    @staticmethod
    def is_available() -> bool:
        """Check if garak package is installed."""
        return _HAS_GARAK

    def run_probes(
        self,
        model_name: str,
        *,
        run_id: str = "",
        probe_types: list[str] | None = None,
    ) -> list[SecurityFinding]:
        """Run Garak probes against a model.

        Discovers probe classes within selected modules and reports
        each probe with test prompts as an informational finding.
        """
        if not self.is_available():
            logger.info("garak_not_available", adapter="run_probes")
            return []
        try:
            importlib.import_module("garak.probes")

            available_probes: dict[str, str] = {
                "promptinject": "Prompt Injection",
                "encoding": "Encoding Bypass",
                "dan": "DAN Jailbreak",
                "leakreplay": "Data Leakage",
            }

            selected = probe_types or list(available_probes.keys())
            findings: list[SecurityFinding] = []

            for probe_name in selected:
                if probe_name not in available_probes:
                    continue
                try:
                    probe_mod = importlib.import_module(
                        f"garak.probes.{probe_name}"
                    )
                    probe_classes = [
                        name
                        for name in dir(probe_mod)
                        if not name.startswith("_")
                        and isinstance(
                            getattr(probe_mod, name, None), type
                        )
                    ]
                    for cls_name in probe_classes[:3]:
                        cls = getattr(probe_mod, cls_name)
                        if hasattr(cls, "prompts"):
                            instance = cls()
                            prompt_count = len(
                                getattr(instance, "prompts", [])
                            )
                            if prompt_count > 0:
                                label = available_probes[probe_name]
                                findings.append(
                                    SecurityFinding(
                                        run_id=run_id or "adhoc",
                                        severity=FindingSeverity.INFO,
                                        category=(
                                            FindingCategory.PROMPT_INJECTION
                                            if "inject" in probe_name
                                            else FindingCategory.MODEL_SECURITY
                                        ),
                                        title=(
                                            f"Garak: {label} "
                                            f"probe available"
                                        ),
                                        description=(
                                            f"Probe {cls_name} has "
                                            f"{prompt_count} test "
                                            f"prompts for {label} "
                                            f"testing against "
                                            f"{model_name}"
                                        ),
                                        tool="garak",
                                    )
                                )
                except Exception:
                    logger.warning(
                        "garak_probe_load_failed",
                        probe=probe_name,
                        exc_info=True,
                    )

            return findings
        except Exception:
            logger.warning(
                "garak_run_probes_failed", exc_info=True
            )
            return []
