"""Tests for Jupyter-backed execution adapters."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from agent33.execution.adapters.jupyter import (
    DockerKernelSession,
    JupyterAdapter,
    KernelSessionManager,
    _language_to_kernel,
    build_default_jupyter_definition,
)
from agent33.execution.models import (
    AdapterDefinition,
    AdapterType,
    ExecutionContract,
    ExecutionInputs,
    ExecutionResult,
    KernelContainerPolicy,
    KernelInterface,
    OutputArtifact,
)

if TYPE_CHECKING:
    from pathlib import Path


def _make_definition(*, docker_enabled: bool = False) -> AdapterDefinition:
    return AdapterDefinition(
        adapter_id="jupyter-kernel",
        name="jupyter-kernel",
        tool_id="code-interpreter",
        type=AdapterType.KERNEL,
        kernel=KernelInterface(
            kernel_name="python3",
            max_sessions=2,
            idle_timeout_seconds=60.0,
            startup_timeout_seconds=10.0,
            execution_timeout_seconds=45.0,
            container=KernelContainerPolicy(
                enabled=docker_enabled,
                image="ghcr.io/example/jupyter:latest",
                allowed_images=["ghcr.io/example/jupyter:latest"],
                network_enabled=False,
                mount_working_directory=True,
                container_workdir="/workspace",
                extra_run_args=["--cpus", "1"],
            ),
        ),
    )


class _FakeSession:
    def __init__(self, session_id: str, kernel_name: str, *, success: bool = True) -> None:
        self.session_id = session_id
        self.kernel_name = kernel_name
        self.last_used = time.time()
        self.started = False
        self.stopped = False
        self.success = success
        self.executed_code: list[tuple[str, float]] = []

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    async def execute(
        self,
        code: str,
        timeout: float = 60.0,
    ) -> tuple[bool, str, str, list[OutputArtifact]]:
        self.executed_code.append((code, timeout))
        self.last_used = time.time()
        if self.success:
            return (
                True,
                "stdout",
                "",
                [OutputArtifact(mime_type="text/plain", data="artifact")],
            )
        return (False, "", "boom", [])

    @property
    def is_alive(self) -> bool:
        return not self.stopped


class _FakeSessionManager:
    def __init__(self, session: _FakeSession) -> None:
        self.session = session
        self.get_calls: list[tuple[str, str, str | None]] = []
        self.removed: list[str] = []
        self.shutdown_called = False

    async def get_or_create(
        self,
        session_id: str,
        kernel_name: str = "python3",
        working_directory: str | None = None,
    ) -> _FakeSession:
        self.get_calls.append((session_id, kernel_name, working_directory))
        return self.session

    async def remove(self, session_id: str) -> None:
        self.removed.append(session_id)

    async def shutdown_all(self) -> None:
        self.shutdown_called = True


class TestOutputArtifacts:
    def test_execution_result_artifacts_are_typed(self) -> None:
        result = ExecutionResult(
            execution_id="exec-1",
            success=True,
            artifacts=[{"mime_type": "text/plain", "data": "hello"}],
        )

        assert len(result.artifacts) == 1
        assert result.artifacts[0].mime_type == "text/plain"
        assert result.artifacts[0].data == "hello"


class TestLanguageMapping:
    def test_python_maps(self) -> None:
        assert _language_to_kernel("python") == "python3"
        assert _language_to_kernel("Python3") == "python3"

    def test_other_languages_map(self) -> None:
        assert _language_to_kernel("r") == "ir"
        assert _language_to_kernel("julia") == "julia-1.9"
        assert _language_to_kernel("typescript") == "tslab"

    def test_unknown_defaults_to_python(self) -> None:
        assert _language_to_kernel("rust") == "python3"


class TestKernelSessionManager:
    @pytest.mark.asyncio
    async def test_get_or_create_reuses_live_session(self) -> None:
        created: list[_FakeSession] = []

        def factory(
            session_id: str,
            kernel_name: str,
            working_directory: str | None,
        ) -> _FakeSession:
            del working_directory
            session = _FakeSession(session_id, kernel_name)
            created.append(session)
            return session

        manager = KernelSessionManager(max_sessions=2, idle_timeout=60.0, session_factory=factory)

        first = await manager.get_or_create("sess-1", "python3")
        second = await manager.get_or_create("sess-1", "python3")

        assert first is second
        assert len(created) == 1

    @pytest.mark.asyncio
    async def test_reap_idle_removes_expired_sessions(self) -> None:
        old = _FakeSession("old", "python3")
        old.last_used = time.time() - 120.0
        fresh = _FakeSession("fresh", "python3")

        manager = KernelSessionManager(max_sessions=2, idle_timeout=60.0)
        manager._sessions = {"old": old, "fresh": fresh}

        await manager._reap_idle()

        assert "old" not in manager._sessions
        assert old.stopped is True
        assert "fresh" in manager._sessions


class TestDockerKernelSession:
    def test_build_docker_command_disables_network_and_mounts_runtime(
        self,
        tmp_path: Path,
    ) -> None:
        session = DockerKernelSession(
            "sess-1",
            "python3",
            policy=KernelContainerPolicy(
                enabled=True,
                image="ghcr.io/example/jupyter:latest",
                allowed_images=["ghcr.io/example/jupyter:latest"],
                network_enabled=False,
                mount_working_directory=True,
                container_workdir="/workspace",
                extra_run_args=["--cpus", "1"],
            ),
            working_directory="D:\\workspace",
        )

        command = session._build_docker_command(
            tmp_path,
            {
                "shell_port": 10001,
                "iopub_port": 10002,
                "stdin_port": 10003,
                "control_port": 10004,
                "hb_port": 10005,
            },
        )

        assert command[:6] == ["docker", "run", "-d", "--rm", "--name", "agent33-kernel-sess-1"]
        assert "--network" in command
        assert "none" in command
        assert f"{tmp_path}:/agent33-runtime" in command
        assert "D:\\workspace:/workspace" in command
        assert "ghcr.io/example/jupyter:latest" in command
        assert "ipykernel_launcher" in command


class TestJupyterAdapter:
    def test_requires_kernel_definition(self) -> None:
        definition = AdapterDefinition(
            adapter_id="bad",
            name="bad",
            tool_id="code",
            type=AdapterType.KERNEL,
        )

        with pytest.raises(ValueError, match="kernel"):
            JupyterAdapter(definition)

    @pytest.mark.asyncio
    async def test_execute_returns_failure_without_code(self) -> None:
        manager = _FakeSessionManager(_FakeSession("s", "python3"))
        adapter = JupyterAdapter(_make_definition(), session_manager=manager)

        result = await adapter.execute(
            ExecutionContract(
                execution_id="exec-1",
                tool_id="code-interpreter",
                adapter_id="jupyter-kernel",
                inputs=ExecutionInputs(command="python"),
            )
        )

        assert result.success is False
        assert "stdin" in (result.error or "")

    @pytest.mark.asyncio
    async def test_execute_with_stateful_session_preserves_metadata(self) -> None:
        fake_session = _FakeSession("sess-123", "python3")
        manager = _FakeSessionManager(fake_session)
        adapter = JupyterAdapter(_make_definition(), session_manager=manager)

        result = await adapter.execute(
            ExecutionContract(
                execution_id="exec-2",
                tool_id="code-interpreter",
                adapter_id="jupyter-kernel",
                inputs=ExecutionInputs(
                    command="python",
                    stdin="print('hi')",
                    working_directory="D:\\repo",
                ),
                metadata={"session_id": "sess-123", "language": "python"},
            )
        )

        assert result.success is True
        assert result.stdout == "stdout"
        assert result.stderr == ""
        assert result.artifacts[0].mime_type == "text/plain"
        assert result.metadata["session_id"] == "sess-123"
        assert result.metadata["backend"] == "local"
        assert manager.get_calls == [("sess-123", "python3", "D:\\repo")]
        assert manager.removed == []
        executed_code, timeout = fake_session.executed_code[0]
        assert "os.chdir" in executed_code
        assert timeout == 30.0

    @pytest.mark.asyncio
    async def test_execute_one_shot_session_is_removed(self) -> None:
        fake_session = _FakeSession("oneshot", "python3")
        manager = _FakeSessionManager(fake_session)
        adapter = JupyterAdapter(_make_definition(), session_manager=manager)

        result = await adapter.execute(
            ExecutionContract(
                execution_id="exec-3",
                tool_id="code-interpreter",
                adapter_id="jupyter-kernel",
                inputs=ExecutionInputs(command="python", stdin="x = 1"),
            )
        )

        assert result.success is True
        assert len(manager.removed) == 1
        assert manager.removed[0].startswith("oneshot-")
        assert result.metadata["session_id"] is None

    @pytest.mark.asyncio
    async def test_execute_propagates_kernel_failure(self) -> None:
        adapter = JupyterAdapter(
            _make_definition(),
            session_manager=_FakeSessionManager(_FakeSession("sess-1", "python3", success=False)),
        )

        result = await adapter.execute(
            ExecutionContract(
                execution_id="exec-4",
                tool_id="code-interpreter",
                adapter_id="jupyter-kernel",
                inputs=ExecutionInputs(command="python", stdin="raise ValueError('x')"),
                metadata={"session_id": "sess-1"},
            )
        )

        assert result.success is False
        assert result.exit_code == 1
        assert result.stderr == "boom"

    @pytest.mark.asyncio
    async def test_shutdown_delegates_to_session_manager(self) -> None:
        manager = _FakeSessionManager(_FakeSession("sess-1", "python3"))
        adapter = JupyterAdapter(_make_definition(), session_manager=manager)

        await adapter.shutdown()

        assert manager.shutdown_called is True


class TestDefaultDefinitionBuilder:
    def test_build_default_jupyter_definition_supports_docker_mode(self) -> None:
        definition = build_default_jupyter_definition(
            adapter_id="jupyter-kernel",
            tool_id="code-interpreter",
            docker_enabled=True,
            docker_image="ghcr.io/example/jupyter:latest",
            docker_allowed_images=["ghcr.io/example/jupyter:latest"],
            docker_network_enabled=False,
            docker_mount_working_directory=False,
            docker_container_workdir="/workspace",
        )

        assert definition.type == AdapterType.KERNEL
        assert definition.kernel is not None
        assert definition.kernel.container.enabled is True
        assert definition.kernel.container.image == "ghcr.io/example/jupyter:latest"
        assert definition.sandbox_override["network"]["enabled"] is False
