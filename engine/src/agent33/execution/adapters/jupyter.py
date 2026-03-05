"""Jupyter kernel adapter for stateful code execution."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# Check if jupyter_client is available
_HAS_JUPYTER = False
try:
    import jupyter_client  # noqa: F401

    _HAS_JUPYTER = True
except ImportError:
    pass


class OutputArtifact:
    """A captured output artifact from kernel execution."""

    __slots__ = ("mime_type", "data", "metadata")

    def __init__(
        self,
        mime_type: str,
        data: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.mime_type = mime_type
        self.data = data
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "mime_type": self.mime_type,
            "data": self.data,
            "metadata": self.metadata,
        }


class KernelSession:
    """Manages a single Jupyter kernel session."""

    def __init__(self, session_id: str, kernel_name: str = "python3") -> None:
        self.session_id = session_id
        self.kernel_name = kernel_name
        self.created_at = time.time()
        self.last_used = time.time()
        self._manager: Any = None
        self._client: Any = None
        self._started = False

    async def start(self) -> None:
        """Start the kernel."""
        if not _HAS_JUPYTER:
            msg = "jupyter_client is not installed. Install with: pip install agent33[jupyter]"
            raise RuntimeError(msg)
        import jupyter_client

        self._manager = jupyter_client.AsyncKernelManager(kernel_name=self.kernel_name)
        await self._manager.start_kernel()
        self._client = self._manager.client()
        self._client.start_channels()
        # Wait for kernel to be ready
        try:
            await asyncio.wait_for(self._client.wait_for_ready(), timeout=30.0)
        except TimeoutError as exc:
            await self.stop()
            msg = "Kernel failed to start within 30 seconds"
            raise RuntimeError(msg) from exc
        self._started = True

    async def stop(self) -> None:
        """Shutdown the kernel."""
        if self._client:
            self._client.stop_channels()
        if self._manager and self._manager.is_alive():
            await self._manager.shutdown_kernel(now=True)
        self._started = False

    async def execute(
        self,
        code: str,
        timeout: float = 60.0,
    ) -> tuple[str, list[OutputArtifact]]:
        """Execute code and capture output.

        Returns:
            Tuple of (stdout_text, list of OutputArtifacts).
        """
        if not self._started or not self._client:
            msg = "Kernel not started"
            raise RuntimeError(msg)

        self.last_used = time.time()
        msg_id = self._client.execute(code)

        stdout_parts: list[str] = []
        artifacts: list[OutputArtifact] = []

        deadline = time.time() + timeout

        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise TimeoutError(f"Kernel execution timed out after {timeout}s")

            try:
                msg = await asyncio.wait_for(
                    self._client.get_iopub_msg(),
                    timeout=min(remaining, 5.0),
                )
            except TimeoutError:
                continue

            if msg["parent_header"].get("msg_id") != msg_id:
                continue

            msg_type = msg["msg_type"]
            content = msg["content"]

            if msg_type == "stream":
                stdout_parts.append(content.get("text", ""))
            elif msg_type in ("display_data", "execute_result"):
                data = content.get("data", {})
                metadata = content.get("metadata", {})
                for mime, value in data.items():
                    artifacts.append(
                        OutputArtifact(
                            mime_type=mime,
                            data=value if isinstance(value, str) else str(value),
                            metadata=metadata.get(mime, {}),
                        )
                    )
            elif msg_type == "error":
                tb_lines = content.get("traceback", [])
                error_text = "\n".join(tb_lines)
                stdout_parts.append(f"Error: {error_text}")
            elif msg_type == "status" and content.get("execution_state") == "idle":
                break

        return "".join(stdout_parts), artifacts

    @property
    def is_alive(self) -> bool:
        if self._manager is None:
            return False
        return bool(self._manager.is_alive())


class KernelSessionManager:
    """Manages a pool of kernel sessions."""

    def __init__(
        self,
        max_sessions: int = 10,
        idle_timeout: float = 300.0,
    ) -> None:
        self._sessions: dict[str, KernelSession] = {}
        self._max_sessions = max_sessions
        self._idle_timeout = idle_timeout
        self._lock = asyncio.Lock()

    async def get_or_create(
        self,
        session_id: str,
        kernel_name: str = "python3",
    ) -> KernelSession:
        """Get an existing session or create a new one."""
        async with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                if session.is_alive:
                    return session
                # Dead session, remove and recreate
                del self._sessions[session_id]

            # Reap idle sessions if at capacity
            if len(self._sessions) >= self._max_sessions:
                await self._reap_idle()

            if len(self._sessions) >= self._max_sessions:
                msg = f"Maximum kernel sessions ({self._max_sessions}) reached"
                raise RuntimeError(msg)

            session = KernelSession(session_id, kernel_name)
            await session.start()
            self._sessions[session_id] = session
            return session

    async def remove(self, session_id: str) -> None:
        """Stop and remove a session."""
        async with self._lock:
            session = self._sessions.pop(session_id, None)
            if session:
                await session.stop()

    async def _reap_idle(self) -> None:
        """Remove sessions idle beyond timeout."""
        now = time.time()
        to_remove = [
            sid for sid, s in self._sessions.items() if now - s.last_used > self._idle_timeout
        ]
        for sid in to_remove:
            session = self._sessions.pop(sid)
            await session.stop()
            logger.info("Reaped idle kernel session %s", sid)

    async def shutdown_all(self) -> None:
        """Shutdown all sessions."""
        for session in self._sessions.values():
            await session.stop()
        self._sessions.clear()

    @property
    def active_count(self) -> int:
        return len(self._sessions)


class JupyterAdapter:
    """Adapter for executing code via Jupyter kernels.

    Implements the same interface as CLIAdapter but with stateful execution.
    """

    def __init__(
        self,
        session_manager: KernelSessionManager | None = None,
    ) -> None:
        self._session_manager = session_manager or KernelSessionManager()

    async def execute(
        self,
        code: str,
        language: str = "python",
        session_id: str | None = None,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        """Execute code in a Jupyter kernel.

        Args:
            code: Code to execute.
            language: Programming language (maps to kernel name).
            session_id: Session ID for stateful execution. None = one-shot.
            timeout: Execution timeout in seconds.

        Returns:
            Dict with stdout, artifacts, session_id.
        """
        if not _HAS_JUPYTER:
            return {
                "success": False,
                "stdout": "",
                "stderr": "jupyter_client not installed",
                "artifacts": [],
                "session_id": None,
            }

        kernel_name = _language_to_kernel(language)
        effective_session_id = session_id or f"oneshot-{time.time()}"

        try:
            session = await self._session_manager.get_or_create(effective_session_id, kernel_name)
            stdout, artifacts = await session.execute(code, timeout)

            # Clean up one-shot sessions
            if session_id is None:
                await self._session_manager.remove(effective_session_id)

            return {
                "success": True,
                "stdout": stdout,
                "stderr": "",
                "artifacts": [a.to_dict() for a in artifacts],
                "session_id": session_id,
            }
        except Exception as exc:
            logger.exception("Jupyter execution failed")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(exc),
                "artifacts": [],
                "session_id": session_id,
            }

    async def shutdown(self) -> None:
        """Shutdown all kernel sessions."""
        await self._session_manager.shutdown_all()


def _language_to_kernel(language: str) -> str:
    """Map language name to Jupyter kernel name."""
    mapping = {
        "python": "python3",
        "python3": "python3",
        "r": "ir",
        "julia": "julia-1.9",
        "javascript": "javascript",
        "typescript": "tslab",
    }
    return mapping.get(language.lower(), "python3")
