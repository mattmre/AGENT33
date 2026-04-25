from __future__ import annotations

from agent33 import config as config_module


def test_runtime_service_url_rewrites_loopback_inside_container(
    monkeypatch,
) -> None:
    monkeypatch.setattr(config_module.os.path, "exists", lambda path: path == "/.dockerenv")

    resolved = config_module.resolve_runtime_service_url("http://localhost:11434")

    assert resolved == "http://host.docker.internal:11434"


def test_runtime_service_url_preserves_non_loopback_hosts(monkeypatch) -> None:
    monkeypatch.setattr(config_module.os.path, "exists", lambda path: path == "/.dockerenv")

    resolved = config_module.resolve_runtime_service_url("http://ollama:11434")

    assert resolved == "http://ollama:11434"
