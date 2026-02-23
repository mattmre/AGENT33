"""AI/LLM security scanning for AGENT-33.

Provides prompt injection detection, tool definition poisoning checks
(OWASP MCP-01), and integration points for LLM Guard and Garak.
"""

from __future__ import annotations

from typing import Any

import structlog

from agent33.component_security.models import (
    FindingCategory,
    FindingSeverity,
    SecurityFinding,
)
from agent33.security.injection import ScanResult, scan_input, scan_inputs_recursive

logger = structlog.get_logger()

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
    """Stub adapter for Protect AI's LLM Guard integration.

    LLM Guard (MIT, 4.5k+ stars) provides input/output scanners for:
    - Prompt injection detection
    - Toxicity filtering
    - PII detection and anonymization
    - Invisible text detection

    This stub defines the integration interface. Full implementation
    requires the llm-guard package to be installed.
    """

    @staticmethod
    def is_available() -> bool:
        """Check if llm-guard package is installed."""
        try:
            import importlib

            importlib.import_module("llm_guard")
            return True
        except ImportError:
            return False

    def scan_input(self, text: str, *, run_id: str = "") -> list[SecurityFinding]:
        """Scan input text using LLM Guard scanners.

        Stub: returns empty list until llm-guard is installed.
        """
        if not self.is_available():
            logger.debug("llm_guard_not_available")
            return []
        return []

    def scan_output(self, text: str, *, run_id: str = "") -> list[SecurityFinding]:
        """Scan LLM output using LLM Guard scanners.

        Stub: returns empty list until llm-guard is installed.
        """
        if not self.is_available():
            return []
        return []


class GarakAdapter:
    """Stub adapter for NVIDIA's Garak LLM vulnerability scanner.

    Garak (Apache-2.0, 3k+ stars) provides:
    - Prompt injection probes
    - Data leakage detection
    - Hallucination testing
    - Toxicity generation testing

    This stub defines the integration interface. Full implementation
    requires the garak package to be installed.
    """

    @staticmethod
    def is_available() -> bool:
        """Check if garak package is installed."""
        try:
            import importlib

            importlib.import_module("garak")
            return True
        except ImportError:
            return False

    def run_probes(
        self,
        model_name: str,
        *,
        run_id: str = "",
        probe_types: list[str] | None = None,
    ) -> list[SecurityFinding]:
        """Run Garak probes against a model.

        Stub: returns empty list until garak is installed.
        """
        if not self.is_available():
            logger.debug("garak_not_available")
            return []
        return []
