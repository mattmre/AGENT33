"""Tests for Phase 42: Jupyter kernel adapter."""

from __future__ import annotations

from unittest.mock import patch

from agent33.execution.adapters.jupyter import (
    JupyterAdapter,
    KernelSession,
    KernelSessionManager,
    OutputArtifact,
    _language_to_kernel,
)


class TestOutputArtifact:
    def test_creation(self) -> None:
        art = OutputArtifact(mime_type="text/plain", data="hello")
        assert art.mime_type == "text/plain"
        assert art.data == "hello"
        assert art.metadata == {}

    def test_to_dict(self) -> None:
        art = OutputArtifact(
            mime_type="image/png",
            data="base64data",
            metadata={"width": 100},
        )
        d = art.to_dict()
        assert d["mime_type"] == "image/png"
        assert d["data"] == "base64data"
        assert d["metadata"]["width"] == 100

    def test_to_dict_default_metadata(self) -> None:
        art = OutputArtifact(mime_type="text/html", data="<b>hi</b>")
        d = art.to_dict()
        assert d["metadata"] == {}


class TestLanguageMapping:
    def test_python_maps(self) -> None:
        assert _language_to_kernel("python") == "python3"
        assert _language_to_kernel("python3") == "python3"

    def test_r_maps(self) -> None:
        assert _language_to_kernel("r") == "ir"

    def test_julia_maps(self) -> None:
        assert _language_to_kernel("julia") == "julia-1.9"

    def test_javascript_maps(self) -> None:
        assert _language_to_kernel("javascript") == "javascript"

    def test_typescript_maps(self) -> None:
        assert _language_to_kernel("typescript") == "tslab"

    def test_unknown_defaults_python(self) -> None:
        assert _language_to_kernel("rust") == "python3"

    def test_case_insensitive(self) -> None:
        assert _language_to_kernel("Python") == "python3"
        assert _language_to_kernel("PYTHON") == "python3"
        assert _language_to_kernel("R") == "ir"


class TestKernelSession:
    def test_creation(self) -> None:
        session = KernelSession("test-1")
        assert session.session_id == "test-1"
        assert session.kernel_name == "python3"
        assert not session.is_alive

    def test_custom_kernel(self) -> None:
        session = KernelSession("test-r", kernel_name="ir")
        assert session.kernel_name == "ir"

    def test_not_alive_without_manager(self) -> None:
        session = KernelSession("test-2")
        assert not session.is_alive

    def test_timestamps_set(self) -> None:
        session = KernelSession("test-3")
        assert session.created_at > 0
        assert session.last_used > 0


class TestKernelSessionManager:
    async def test_active_count_starts_zero(self) -> None:
        mgr = KernelSessionManager()
        assert mgr.active_count == 0

    async def test_shutdown_all_empty(self) -> None:
        mgr = KernelSessionManager()
        await mgr.shutdown_all()
        assert mgr.active_count == 0

    async def test_remove_nonexistent(self) -> None:
        mgr = KernelSessionManager()
        await mgr.remove("does-not-exist")
        assert mgr.active_count == 0

    def test_custom_limits(self) -> None:
        mgr = KernelSessionManager(max_sessions=5, idle_timeout=120.0)
        assert mgr._max_sessions == 5
        assert mgr._idle_timeout == 120.0


class TestJupyterAdapter:
    async def test_execute_without_jupyter(self) -> None:
        """When jupyter_client is not available, return error."""
        adapter = JupyterAdapter()
        with patch("agent33.execution.adapters.jupyter._HAS_JUPYTER", False):
            result = await adapter.execute("print('hi')")
            assert not result["success"]
            assert "not installed" in result["stderr"]

    async def test_execute_returns_dict(self) -> None:
        """Result has expected keys."""
        adapter = JupyterAdapter()
        with patch("agent33.execution.adapters.jupyter._HAS_JUPYTER", False):
            result = await adapter.execute("x = 1")
            assert "success" in result
            assert "stdout" in result
            assert "stderr" in result
            assert "artifacts" in result
            assert "session_id" in result

    async def test_execute_no_jupyter_empty_artifacts(self) -> None:
        """Artifacts should be an empty list when jupyter is unavailable."""
        adapter = JupyterAdapter()
        with patch("agent33.execution.adapters.jupyter._HAS_JUPYTER", False):
            result = await adapter.execute("x = 1")
            assert result["artifacts"] == []

    async def test_execute_no_jupyter_session_id_none(self) -> None:
        """Session ID should be None for one-shot when jupyter unavailable."""
        adapter = JupyterAdapter()
        with patch("agent33.execution.adapters.jupyter._HAS_JUPYTER", False):
            result = await adapter.execute("x = 1")
            assert result["session_id"] is None

    async def test_shutdown(self) -> None:
        mgr = KernelSessionManager()
        adapter = JupyterAdapter(session_manager=mgr)
        await adapter.shutdown()
        assert mgr.active_count == 0

    async def test_default_session_manager(self) -> None:
        adapter = JupyterAdapter()
        assert adapter._session_manager is not None
        assert adapter._session_manager.active_count == 0


class TestAdapterTypeEnum:
    def test_kernel_adapter_type_exists(self) -> None:
        from agent33.execution.models import AdapterType

        assert hasattr(AdapterType, "KERNEL")
        assert AdapterType.KERNEL.value == "kernel"

    def test_existing_types_preserved(self) -> None:
        from agent33.execution.models import AdapterType

        assert AdapterType.CLI.value == "cli"
        assert AdapterType.API.value == "api"
        assert AdapterType.SDK.value == "sdk"
        assert AdapterType.MCP.value == "mcp"


class TestExecutionResultArtifacts:
    def test_artifacts_default_empty(self) -> None:
        from agent33.execution.models import ExecutionResult

        r = ExecutionResult(execution_id="test-1", success=True)
        assert r.artifacts == []

    def test_artifacts_with_data(self) -> None:
        from agent33.execution.models import ExecutionResult

        r = ExecutionResult(
            execution_id="test-2",
            success=True,
            artifacts=[
                {"mime_type": "text/plain", "data": "hello", "metadata": {}},
            ],
        )
        assert len(r.artifacts) == 1
        assert r.artifacts[0]["mime_type"] == "text/plain"
