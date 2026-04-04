"""CLI commands for improvement pack management (P-PACK v1).

Provides ``agent33 packs validate``, ``agent33 packs apply``, and
``agent33 packs list`` subcommands for local validation, dry-run
simulation, and pack listing.
"""

from __future__ import annotations

import json
from pathlib import Path  # noqa: TC003 -- typer needs Path at runtime
from typing import Any

import typer

packs_app = typer.Typer(name="packs", help="Improvement pack management (P-PACK v1).")


def _load_pack_yaml(path: Path) -> dict[str, Any]:
    """Read and parse a PACK.yaml file, returning the raw dict."""
    import yaml

    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise typer.BadParameter(f"PACK.yaml must be a YAML mapping, got {type(data).__name__}")
    return data


@packs_app.command("validate")
def validate_pack(
    path: Path = typer.Argument(  # noqa: B008
        ..., help="Path to pack directory or PACK.yaml file."
    ),
) -> None:
    """Validate an improvement pack without applying it (local dry run).

    Reads the PACK.yaml, checks schema, and runs prompt-injection scanning
    on any ``prompt_addenda`` sections.
    """
    pack_yaml = path / "PACK.yaml" if path.is_dir() else path
    if not pack_yaml.exists():
        # Try lowercase fallback
        if path.is_dir():
            pack_yaml = path / "pack.yaml"
        if not pack_yaml.exists():
            typer.echo(f"Error: {pack_yaml} not found", err=True)
            raise typer.Exit(1)

    try:
        data = _load_pack_yaml(pack_yaml)
    except Exception as exc:
        typer.echo(f"Error parsing PACK.yaml: {exc}", err=True)
        raise typer.Exit(1) from exc

    name = data.get("name", "?")
    version = data.get("version", "?")
    description = data.get("description", "")

    typer.echo(f"Pack: {name} v{version}")
    typer.echo(f"Description: {description}")

    prompt_addenda: list[str] = data.get("prompt_addenda", [])
    tool_config: dict[str, Any] = data.get("tool_config", {})
    skills: list[Any] = data.get("skills", [])

    typer.echo("\nWould apply:")
    typer.echo(f"  {len(prompt_addenda)} prompt addenda section(s)")
    typer.echo(f"  {len(tool_config)} tool config override(s): {list(tool_config.keys())}")
    typer.echo(f"  {len(skills)} skill(s) to register")

    # Run injection scanning on prompt_addenda
    from agent33.security.injection import scan_inputs_recursive

    scan_result = scan_inputs_recursive(prompt_addenda)
    if not scan_result.is_safe:
        typer.echo(
            f"\nWARNING: prompt_addenda failed injection scan: {', '.join(scan_result.threats)}",
            err=True,
        )
        typer.echo("Review and sanitize the addenda before applying.", err=True)
        raise typer.Exit(1)

    # Try full Pydantic validation
    try:
        from agent33.packs.manifest import PackManifest

        PackManifest.model_validate(data)
    except Exception as exc:
        typer.echo(f"\nSchema validation failed: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo("\nValidation passed. Use 'agent33 packs apply' to apply.")


@packs_app.command("apply")
def apply_pack(
    name: str = typer.Argument(..., help="Pack name to apply."),
    session: str = typer.Option(
        "", "--session", help="Session ID for session-scoped application."
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying."),
    api_url: str = typer.Option(
        "http://localhost:8000", envvar="AGENT33_API_URL", help="API base URL."
    ),
    token: str = typer.Option("", envvar="TOKEN", help="Bearer token for authentication."),
) -> None:
    """Apply or preview an improvement pack via the server API."""
    import httpx

    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if dry_run:
            params: dict[str, str] = {}
            if session:
                params["session"] = session
            resp = httpx.get(
                f"{api_url}/v1/packs/{name}/dry-run",
                headers=headers,
                params=params,
                timeout=10,
            )
        elif session:
            resp = httpx.post(
                f"{api_url}/v1/packs/{name}/enable-session",
                headers=headers,
                params={"session_id": session},
                timeout=10,
            )
        else:
            resp = httpx.post(
                f"{api_url}/v1/packs/{name}/enable",
                headers=headers,
                timeout=10,
            )
        resp.raise_for_status()
        data = resp.json()
        if dry_run:
            typer.echo(f"Dry run for pack '{name}':")
            typer.echo(json.dumps(data, indent=2))
        else:
            scope = f" for session '{session}'" if session else ""
            typer.echo(f"Pack '{name}' applied{scope} successfully.")
    except httpx.HTTPStatusError as exc:
        typer.echo(f"Error {exc.response.status_code}: {exc.response.text}", err=True)
        raise typer.Exit(1) from exc
    except httpx.ConnectError as exc:
        typer.echo(f"Cannot connect to {api_url}: {exc}", err=True)
        raise typer.Exit(1) from exc


@packs_app.command("list")
def list_packs(
    api_url: str = typer.Option(
        "http://localhost:8000", envvar="AGENT33_API_URL", help="API base URL."
    ),
    token: str = typer.Option("", envvar="TOKEN", help="Bearer token for authentication."),
) -> None:
    """List all installed improvement packs via the server API."""
    import httpx

    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = httpx.get(f"{api_url}/v1/packs", headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        packs_list: list[dict[str, Any]] = data.get("packs", [])
        if not packs_list:
            typer.echo("No packs installed.")
            return
        typer.echo(f"Installed packs ({len(packs_list)}):")
        for p in packs_list:
            name = p.get("name", "?")
            version = p.get("version", "?")
            status = p.get("status", "?")
            typer.echo(f"  {name} v{version} [{status}]")
    except httpx.HTTPStatusError as exc:
        typer.echo(f"Error {exc.response.status_code}: {exc.response.text}", err=True)
        raise typer.Exit(1) from exc
    except httpx.ConnectError as exc:
        typer.echo(f"Cannot connect to {api_url}: {exc}", err=True)
        raise typer.Exit(1) from exc
