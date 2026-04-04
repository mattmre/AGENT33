"""agent33 diagnose — traffic-light health check for all subsystems."""

from __future__ import annotations

import os
import shutil
import socket
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Status(Enum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class CheckResult:
    name: str
    status: Status
    message: str
    fix_hint: str = field(default="")
    auto_fixable: bool = field(default=False)


def _icon(status: Status) -> str:
    icons = {
        Status.OK: "✓",
        Status.WARN: "!",
        Status.FAIL: "✗",
        Status.SKIP: "-",
    }
    return icons[status]


def _check_python_version() -> CheckResult:
    """Check Python version is >= 3.11."""
    v = sys.version_info
    if v >= (3, 11):
        return CheckResult("Python version", Status.OK, f"Python {v.major}.{v.minor}.{v.micro}")
    return CheckResult(
        "Python version",
        Status.FAIL,
        f"Python {v.major}.{v.minor} — requires 3.11+",
        fix_hint="Upgrade to Python 3.11 or later",
    )


def _check_env_file() -> CheckResult:
    """Check that .env or AGENT33_MODE environment variable is set."""
    env_path = Path(".env")
    env_local_path = Path(".env.local")
    agent33_mode = os.environ.get("AGENT33_MODE")

    if env_path.exists():
        return CheckResult(
            name="Environment config",
            status=Status.OK,
            message=".env found",
        )
    if env_local_path.exists():
        return CheckResult(
            name="Environment config",
            status=Status.OK,
            message=".env.local found",
        )
    if agent33_mode:
        return CheckResult(
            name="Environment config",
            status=Status.OK,
            message=f"AGENT33_MODE={agent33_mode}",
        )
    return CheckResult(
        name="Environment config",
        status=Status.WARN,
        message="No .env file and AGENT33_MODE not set",
        fix_hint="Run `agent33 bootstrap` to generate a .env.local with sensible defaults",
        auto_fixable=False,
    )


def _check_disk_space() -> CheckResult:
    """Check available disk space (warn <2 GB, fail <500 MB)."""
    try:
        total, used, free = shutil.disk_usage(".")
        free_gb = free / (1024**3)
        if free_gb >= 2.0:
            return CheckResult("Disk space", Status.OK, f"{free_gb:.1f} GB free")
        if free_gb >= 0.5:
            return CheckResult(
                "Disk space",
                Status.WARN,
                f"{free_gb:.1f} GB free — low",
                fix_hint="Free up disk space before running models",
            )
        return CheckResult(
            "Disk space",
            Status.FAIL,
            f"{free_gb:.1f} GB free — critically low",
            fix_hint="Free up at least 2 GB before running agent33",
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult("Disk space", Status.SKIP, f"Could not check: {exc}")


def _check_port(port: int) -> CheckResult:
    """Check if a TCP port is available (not already in use)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(("127.0.0.1", port))
            if result == 0:
                return CheckResult(
                    f"Port {port}",
                    Status.WARN,
                    f"Port {port} is already in use",
                    fix_hint=f"Stop the process using port {port} or change AGENT33_PORT",
                )
            return CheckResult(f"Port {port}", Status.OK, f"Port {port} is available")
    except Exception as exc:  # noqa: BLE001
        return CheckResult(f"Port {port}", Status.SKIP, f"Could not check: {exc}")


def _check_ollama() -> CheckResult:
    """Check Ollama availability and running state."""
    import platform
    import urllib.request

    ollama_path = shutil.which("ollama")
    if not ollama_path:
        system = platform.system()
        if system == "Darwin":
            hint = "Install Ollama: brew install ollama  OR  https://ollama.ai/download"
        elif system == "Linux":
            hint = "Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh"
        else:
            hint = "Install Ollama: https://ollama.ai/download"
        return CheckResult(
            "Ollama",
            Status.WARN,
            "Ollama not installed — needed for local LLM inference",
            fix_hint=hint,
        )

    # Check if ollama is running via HTTP
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)  # noqa: S310
        return CheckResult("Ollama", Status.OK, "Ollama is installed and running")
    except Exception:  # noqa: BLE001
        return CheckResult(
            "Ollama",
            Status.WARN,
            "Ollama is installed but not running",
            fix_hint="Start Ollama: `ollama serve` (or open the Ollama app)",
            auto_fixable=True,
        )


def _check_llm_config() -> CheckResult:
    """Check that some LLM provider is configured."""
    import urllib.request

    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    ollama_base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.environ.get("DEFAULT_MODEL", "")

    if openai_key:
        return CheckResult("LLM provider", Status.OK, "OpenAI API key configured")
    if anthropic_key:
        return CheckResult("LLM provider", Status.OK, "Anthropic API key configured")

    # Check if Ollama is accessible
    try:
        urllib.request.urlopen(f"{ollama_base}/api/tags", timeout=2)  # noqa: S310
        model_info = f" (model: {model})" if model else ""
        return CheckResult("LLM provider", Status.OK, f"Ollama reachable{model_info}")
    except Exception:  # noqa: BLE001
        pass

    return CheckResult(
        "LLM provider",
        Status.FAIL,
        "No LLM provider configured or reachable",
        fix_hint=(
            "Either: set OPENAI_API_KEY or ANTHROPIC_API_KEY, "
            "or install+start Ollama (https://ollama.ai/download)"
        ),
    )


def _check_database(db_url: str | None) -> CheckResult:
    """Check database configuration."""
    if not db_url:
        return CheckResult(
            "Database",
            Status.SKIP,
            "DATABASE_URL not set — using lite mode (no external DB required)",
        )
    if db_url.startswith("postgresql"):
        return CheckResult(
            "Database",
            Status.WARN,
            "PostgreSQL URL configured — connectivity not tested in diagnose",
            fix_hint="Ensure PostgreSQL is running and DATABASE_URL is correct",
        )
    return CheckResult("Database", Status.OK, f"Database URL configured: {db_url[:30]}...")


def _check_redis(redis_url: str | None) -> CheckResult:
    """Check Redis connectivity."""
    if not redis_url:
        return CheckResult(
            "Redis",
            Status.SKIP,
            "REDIS_URL not set — will use in-process cache in lite mode",
        )
    try:
        host = "localhost"
        port = 6379
        if "://" in redis_url:
            parts = redis_url.split("://")[-1].split(":")
            host = parts[0] or "localhost"
            port = int(parts[1].split("/")[0]) if len(parts) > 1 else 6379
        with socket.create_connection((host, port), timeout=2):
            return CheckResult("Redis", Status.OK, f"Redis reachable at {host}:{port}")
    except Exception:  # noqa: BLE001
        return CheckResult(
            "Redis",
            Status.FAIL,
            "Redis configured but not reachable",
            fix_hint="Start Redis: `redis-server` or `docker run -p 6379:6379 redis`",
        )


def _run_all_checks() -> list[CheckResult]:
    """Run all diagnostic checks and return results."""
    db_url = os.environ.get("DATABASE_URL")
    redis_url = os.environ.get("REDIS_URL")

    return [
        _check_python_version(),
        _check_env_file(),
        _check_disk_space(),
        _check_port(8000),
        _check_ollama(),
        _check_llm_config(),
        _check_database(db_url),
        _check_redis(redis_url),
    ]


def _print_results(results: list[CheckResult]) -> int:
    """Print a traffic-light summary table.

    Returns exit code: 0 = all OK, 1 = warnings only, 2 = at least one FAIL.
    """
    print("\n=== AGENT-33 Diagnostic Report ===\n")
    has_fail = False
    has_warn = False

    for r in results:
        icon = _icon(r.status)
        print(f"  {icon}  {r.name:<25} {r.message}")
        if r.fix_hint:
            print(f"       {'':25} Hint: {r.fix_hint}")
        if r.status == Status.FAIL:
            has_fail = True
        if r.status == Status.WARN:
            has_warn = True

    print()
    if has_fail:
        print("  FAIL — fix the issues above before starting agent33")
        return 2
    if has_warn:
        print("  WARN — some optional features may not work")
        return 1
    print("  OK — all checks passed")
    return 0


def _apply_fixes(results: list[CheckResult]) -> None:
    """Apply auto-remediable fixes where safe."""
    import platform
    import subprocess

    fixable = [r for r in results if r.auto_fixable and r.status != Status.OK]
    if not fixable:
        print("No auto-fixable issues found.")
        return

    for r in fixable:
        print(f"\nFixing: {r.name}")
        if r.name == "Ollama" and "not running" in r.message:
            system = platform.system()
            if system == "Windows":
                print(
                    "  Starting Ollama... "
                    "(open the Ollama app or run 'ollama serve' in a terminal)"
                )
            else:
                try:
                    subprocess.Popen(  # noqa: S603
                        ["ollama", "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    print("  Started 'ollama serve' in background")
                except Exception as exc:  # noqa: BLE001
                    print(f"  Could not start Ollama: {exc}")


def diagnose(fix: bool = False) -> int:
    """Run diagnostic checks on all AGENT-33 subsystems.

    Checks Python version, environment config, disk space, port availability,
    Ollama, LLM provider, database, and Redis connectivity.

    Args:
        fix: Auto-remediate issues where safe to do so.

    Returns:
        Exit code: 0 = all OK, 1 = warnings, 2 = failures.
    """
    results = _run_all_checks()
    exit_code = _print_results(results)

    if fix:
        print("\n--- Applying fixes ---")
        _apply_fixes(results)
        print("\n--- Re-checking after fixes ---")
        results = _run_all_checks()
        exit_code = _print_results(results)

    return exit_code
