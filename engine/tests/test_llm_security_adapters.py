"""Tests for real LLMGuard and Garak adapter implementations (Phase 28 Stage 3).

All tests use ``unittest.mock.patch`` so they pass even when llm_guard and
garak are **not** installed in the test environment.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import agent33.component_security.llm_security as _module
from agent33.component_security.llm_security import GarakAdapter, LLMGuardAdapter
from agent33.component_security.models import FindingCategory, FindingSeverity

# Path to the importlib proxy used by the adapters
_IMP = "agent33.component_security.llm_security.importlib"

# Module path for patching the guard flags
_MOD = "agent33.component_security.llm_security"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _llm_guard_side_effect(
    *,
    scan_prompt_return: tuple | None = None,
    scan_output_return: tuple | None = None,
):
    """Return (side_effect_fn, mock_llm_guard) for importlib.import_module."""
    mock_llm_guard = MagicMock()
    mock_input_scanners = MagicMock()
    mock_output_scanners = MagicMock()

    if scan_prompt_return is not None:
        mock_llm_guard.scan_prompt.return_value = scan_prompt_return
    if scan_output_return is not None:
        mock_llm_guard.scan_output.return_value = scan_output_return

    modules = {
        "llm_guard": mock_llm_guard,
        "llm_guard.input_scanners": mock_input_scanners,
        "llm_guard.output_scanners": mock_output_scanners,
    }

    def _side(name: str) -> MagicMock:
        if name in modules:
            return modules[name]
        raise ImportError(name)

    return _side, mock_llm_guard


def _garak_side_effect(probe_modules: dict[str, MagicMock]):
    """Return side_effect_fn for importlib.import_module for garak."""
    garak_probes_mod = MagicMock()

    def _side(name: str) -> MagicMock:
        if name == "garak.probes":
            return garak_probes_mod
        if name.startswith("garak.probes."):
            key = name.split(".")[-1]
            if key in probe_modules:
                return probe_modules[key]
            raise ImportError(name)
        raise ImportError(name)

    return _side


def _make_probe_module(class_defs: dict[str, int]) -> MagicMock:
    """Build a fake garak probe module whose classes expose a ``prompts`` list."""
    mod = MagicMock()
    names: list[str] = []
    for cls_name, prompt_count in class_defs.items():
        cls = type(cls_name, (), {"prompts": ["p"] * prompt_count})
        setattr(mod, cls_name, cls)
        names.append(cls_name)
    mod.__dir__ = lambda self: ["_private", *names]  # type: ignore[method-assign]
    return mod


# ===========================================================================
# 1. Module-level guard flags exist and are bool
# ===========================================================================


def test_has_llmguard_flag_is_bool() -> None:
    assert isinstance(_module._HAS_LLMGUARD, bool)


def test_has_garak_flag_is_bool() -> None:
    assert isinstance(_module._HAS_GARAK, bool)


# ===========================================================================
# 2. _HAS_LLMGUARD = False → scan_input / scan_output return []
# ===========================================================================


def test_scan_input_returns_empty_when_flag_false() -> None:
    with patch(f"{_MOD}._HAS_LLMGUARD", False):
        adapter = LLMGuardAdapter()
        # is_available() reads the module flag directly
        assert adapter.scan_input("some prompt") == []


def test_scan_output_returns_empty_when_flag_false() -> None:
    with patch(f"{_MOD}._HAS_LLMGUARD", False):
        adapter = LLMGuardAdapter()
        assert adapter.scan_output("some output") == []


def test_is_available_reflects_llmguard_flag() -> None:
    with patch(f"{_MOD}._HAS_LLMGUARD", False):
        assert LLMGuardAdapter().is_available() is False
    with patch(f"{_MOD}._HAS_LLMGUARD", True):
        assert LLMGuardAdapter().is_available() is True


# ===========================================================================
# 3. _HAS_GARAK = False → run_probes returns []
# ===========================================================================


def test_run_probes_returns_empty_when_flag_false() -> None:
    with patch(f"{_MOD}._HAS_GARAK", False):
        adapter = GarakAdapter()
        assert adapter.run_probes("gpt-4") == []


def test_garak_is_available_reflects_flag() -> None:
    with patch(f"{_MOD}._HAS_GARAK", False):
        assert GarakAdapter().is_available() is False
    with patch(f"{_MOD}._HAS_GARAK", True):
        assert GarakAdapter().is_available() is True


# ===========================================================================
# 4. LLMGuardAdapter.scan_input — mock-based functional tests
# ===========================================================================


def test_scan_input_returns_list() -> None:
    side, _ = _llm_guard_side_effect(
        scan_prompt_return=("sanitized", [True, True, True], [0.1, 0.05, 0.0])
    )
    with patch(f"{_MOD}._HAS_LLMGUARD", True), patch(_IMP) as m:
        m.import_module.side_effect = side
        result = LLMGuardAdapter().scan_input("hello world")
    assert isinstance(result, list)


def test_scan_input_prompt_injection_critical() -> None:
    side, _ = _llm_guard_side_effect(
        scan_prompt_return=("s", [False, True, True], [0.95, 0.0, 0.0])
    )
    with patch(f"{_MOD}._HAS_LLMGUARD", True), patch(_IMP) as m:
        m.import_module.side_effect = side
        findings = LLMGuardAdapter().scan_input("bad", run_id="r1")
    assert len(findings) == 1
    f = findings[0]
    assert f.severity == FindingSeverity.CRITICAL
    assert f.category == FindingCategory.PROMPT_INJECTION
    assert f.tool == "llm-guard"
    assert f.run_id == "r1"
    assert "PromptInjection" in f.title


def test_scan_input_toxicity_high() -> None:
    side, _ = _llm_guard_side_effect(
        scan_prompt_return=("s", [True, False, True], [0.0, 0.75, 0.0])
    )
    with patch(f"{_MOD}._HAS_LLMGUARD", True), patch(_IMP) as m:
        m.import_module.side_effect = side
        findings = LLMGuardAdapter().scan_input("toxic text")
    assert len(findings) == 1
    assert findings[0].severity == FindingSeverity.HIGH
    assert "Toxicity" in findings[0].title


def test_scan_input_invisible_text_medium() -> None:
    side, _ = _llm_guard_side_effect(
        scan_prompt_return=("s", [True, True, False], [0.0, 0.0, 0.55])
    )
    with patch(f"{_MOD}._HAS_LLMGUARD", True), patch(_IMP) as m:
        m.import_module.side_effect = side
        findings = LLMGuardAdapter().scan_input("text\u200b")
    assert len(findings) == 1
    assert findings[0].severity == FindingSeverity.MEDIUM
    assert "InvisibleText" in findings[0].title


def test_scan_input_all_clean_empty_list() -> None:
    side, _ = _llm_guard_side_effect(
        scan_prompt_return=("clean", [True, True, True], [0.02, 0.01, 0.0])
    )
    with patch(f"{_MOD}._HAS_LLMGUARD", True), patch(_IMP) as m:
        m.import_module.side_effect = side
        findings = LLMGuardAdapter().scan_input("safe text")
    assert findings == []


def test_scan_input_exception_returns_empty() -> None:
    with (
        patch(f"{_MOD}._HAS_LLMGUARD", True),
        patch(_IMP) as m,
    ):
        m.import_module.side_effect = RuntimeError("scanner crash")
        findings = LLMGuardAdapter().scan_input("anything")
    assert findings == []


# ===========================================================================
# 5. LLMGuardAdapter.scan_output — mock-based functional tests
# ===========================================================================


def test_scan_output_returns_list() -> None:
    side, _ = _llm_guard_side_effect(
        scan_output_return=("ok", [True, True], [0.0, 0.0])
    )
    with patch(f"{_MOD}._HAS_LLMGUARD", True), patch(_IMP) as m:
        m.import_module.side_effect = side
        result = LLMGuardAdapter().scan_output("safe output")
    assert isinstance(result, list)


def test_scan_output_sensitive_detected() -> None:
    side, _ = _llm_guard_side_effect(
        scan_output_return=("redacted", [False, True], [0.82, 0.0])
    )
    with patch(f"{_MOD}._HAS_LLMGUARD", True), patch(_IMP) as m:
        m.import_module.side_effect = side
        findings = LLMGuardAdapter().scan_output("SSN: 123-45-6789", run_id="o1")
    assert len(findings) == 1
    assert "Sensitive" in findings[0].title
    assert findings[0].severity == FindingSeverity.HIGH
    assert findings[0].category == FindingCategory.SECRETS_EXPOSURE
    assert findings[0].run_id == "o1"


def test_scan_output_no_refusal_critical() -> None:
    side, _ = _llm_guard_side_effect(
        scan_output_return=("text", [True, False], [0.0, 0.91])
    )
    with patch(f"{_MOD}._HAS_LLMGUARD", True), patch(_IMP) as m:
        m.import_module.side_effect = side
        findings = LLMGuardAdapter().scan_output("I cannot help with that")
    assert len(findings) == 1
    assert findings[0].severity == FindingSeverity.CRITICAL
    assert "NoRefusal" in findings[0].title


def test_scan_output_exception_returns_empty() -> None:
    with (
        patch(f"{_MOD}._HAS_LLMGUARD", True),
        patch(_IMP) as m,
    ):
        m.import_module.side_effect = ValueError("oops")
        findings = LLMGuardAdapter().scan_output("output")
    assert findings == []


# ===========================================================================
# 6. Score → severity mapping (parametrised)
# ===========================================================================


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.90, FindingSeverity.CRITICAL),
        (0.95, FindingSeverity.CRITICAL),
        (0.70, FindingSeverity.HIGH),
        (0.89, FindingSeverity.HIGH),
        (0.50, FindingSeverity.MEDIUM),
        (0.69, FindingSeverity.MEDIUM),
        (0.00, FindingSeverity.LOW),
        (0.49, FindingSeverity.LOW),
    ],
)
def test_score_to_severity_mapping(score: float, expected: FindingSeverity) -> None:
    assert LLMGuardAdapter._score_to_severity(score) == expected


# ===========================================================================
# 7. GarakAdapter.run_probes — mock-based functional tests
# ===========================================================================


def test_run_probes_returns_list() -> None:
    mod = _make_probe_module({"InjectorX": 3})
    side = _garak_side_effect({"promptinject": mod})
    with patch(f"{_MOD}._HAS_GARAK", True), patch(_IMP) as m:
        m.import_module.side_effect = side
        result = GarakAdapter().run_probes("gpt-4", probe_types=["promptinject"])
    assert isinstance(result, list)


def test_run_probes_prompt_inject_finding() -> None:
    mod = _make_probe_module({"InjectorA": 5})
    side = _garak_side_effect({"promptinject": mod})
    with patch(f"{_MOD}._HAS_GARAK", True), patch(_IMP) as m:
        m.import_module.side_effect = side
        findings = GarakAdapter().run_probes(
            "gpt-4", run_id="g1", probe_types=["promptinject"]
        )
    assert len(findings) == 1
    f = findings[0]
    assert f.severity == FindingSeverity.INFO
    assert f.category == FindingCategory.PROMPT_INJECTION
    assert f.tool == "garak"
    assert "gpt-4" in f.description
    assert f.run_id == "g1"
    assert "Prompt Injection" in f.title


def test_run_probes_non_inject_uses_model_security() -> None:
    mod = _make_probe_module({"DanProbe": 2})
    side = _garak_side_effect({"dan": mod})
    with patch(f"{_MOD}._HAS_GARAK", True), patch(_IMP) as m:
        m.import_module.side_effect = side
        findings = GarakAdapter().run_probes("model", probe_types=["dan"])
    assert len(findings) == 1
    assert findings[0].category == FindingCategory.MODEL_SECURITY


def test_run_probes_exception_returns_empty() -> None:
    with (
        patch(f"{_MOD}._HAS_GARAK", True),
        patch(_IMP) as m,
    ):
        m.import_module.side_effect = RuntimeError("garak crash")
        findings = GarakAdapter().run_probes("model")
    assert findings == []


def test_run_probes_zero_prompt_class_skipped() -> None:
    mod = _make_probe_module({"Empty": 0, "Full": 3})
    side = _garak_side_effect({"promptinject": mod})
    with patch(f"{_MOD}._HAS_GARAK", True), patch(_IMP) as m:
        m.import_module.side_effect = side
        findings = GarakAdapter().run_probes("model", probe_types=["promptinject"])
    assert len(findings) == 1
    assert "Full" in findings[0].description


def test_run_probes_all_four_probe_types() -> None:
    mod = _make_probe_module({"P": 1})
    side = _garak_side_effect(
        {"promptinject": mod, "encoding": mod, "dan": mod, "leakreplay": mod}
    )
    with patch(f"{_MOD}._HAS_GARAK", True), patch(_IMP) as m:
        m.import_module.side_effect = side
        findings = GarakAdapter().run_probes("model")
    assert len(findings) == 4
