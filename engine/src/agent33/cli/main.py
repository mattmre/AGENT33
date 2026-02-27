"""AGENT-33 CLI application."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import typer

app = typer.Typer(
    name="agent33",
    help="AGENT-33 -- Autonomous AI agent orchestration engine.",
    add_completion=False,
)


@app.command()
def init(
    name: str = typer.Argument(..., help="Name of the agent or workflow to scaffold."),
    kind: str = typer.Option(
        "agent",
        "--kind",
        "-k",
        help="Type of definition to create: 'agent' or 'workflow'.",
    ),
    output_dir: str = typer.Option(
        ".",
        "--output",
        "-o",
        help="Directory to write the scaffolded file into.",
    ),
) -> None:
    """Scaffold a new agent or workflow definition."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    definition: dict[str, Any]
    if kind == "agent":
        definition = {
            "name": name,
            "version": "0.1.0",
            "role": "worker",
            "description": f"{name} agent",
            "capabilities": [],
            "inputs": {
                "query": {
                    "type": "string",
                    "description": "Input query",
                    "required": True,
                }
            },
            "outputs": {
                "result": {
                    "type": "string",
                    "description": "Output result",
                }
            },
            "dependencies": [],
            "prompts": {"system": "", "user": "", "examples": []},
            "constraints": {
                "max_tokens": 4096,
                "timeout_seconds": 120,
                "max_retries": 2,
                "parallel_allowed": True,
            },
            "metadata": {"author": "", "tags": []},
        }
        file_path = out / f"{name}.agent.json"
    elif kind == "workflow":
        definition = {
            "name": name,
            "version": "0.1.0",
            "description": f"{name} workflow",
            "triggers": {"manual": True},
            "inputs": {},
            "outputs": {},
            "steps": [
                {
                    "id": "step-1",
                    "name": "First step",
                    "action": "invoke-agent",
                    "agent": "my-agent",
                    "inputs": {},
                    "outputs": {},
                }
            ],
            "execution": {"mode": "sequential"},
            "metadata": {"author": "", "tags": []},
        }
        file_path = out / f"{name}.workflow.json"
    else:
        typer.echo(f"Unknown kind: {kind}. Use 'agent' or 'workflow'.", err=True)
        raise typer.Exit(code=1)

    file_path.write_text(json.dumps(definition, indent=2) + "\n", encoding="utf-8")
    typer.echo(f"Created {file_path}")


@app.command()
def run(
    workflow: str = typer.Argument(..., help="Name of the workflow to execute."),
    base_url: str = typer.Option(
        "http://localhost:8000",
        "--base-url",
        "-b",
        help="API base URL.",
    ),
    inputs: str | None = typer.Option(
        None,
        "--inputs",
        "-i",
        help="JSON string of workflow inputs.",
    ),
    token: str | None = typer.Option(
        None,
        "--token",
        "-t",
        help="Bearer token for protected workflow execution. Falls back to TOKEN env var.",
    ),
) -> None:
    """Execute a workflow by name via the API."""
    import httpx

    payload: dict[str, object] = {"inputs": {}}
    if inputs:
        try:
            payload["inputs"] = json.loads(inputs)
        except json.JSONDecodeError as exc:
            typer.echo(f"Invalid JSON inputs: {exc}", err=True)
            raise typer.Exit(code=1) from exc

    auth_token = token or os.getenv("TOKEN")
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    try:
        with httpx.Client(base_url=base_url, timeout=120.0) as client:
            resp = client.post(
                f"/v1/workflows/{workflow}/execute",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            typer.echo(json.dumps(resp.json(), indent=2))
    except httpx.HTTPStatusError as exc:
        typer.echo(f"API error {exc.response.status_code}: {exc.response.text}", err=True)
        raise typer.Exit(code=1) from exc
    except httpx.ConnectError as exc:
        typer.echo(f"Cannot connect to {base_url}: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def test(
    path: str = typer.Argument("tests", help="Path to the test directory or file."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output."),
) -> None:
    """Run the test suite using pytest."""
    import subprocess

    cmd = [sys.executable, "-m", "pytest", path]
    if verbose:
        cmd.append("-v")
    result = subprocess.run(cmd, check=False)
    raise typer.Exit(code=result.returncode)


@app.command()
def status(
    base_url: str = typer.Option(
        "http://localhost:8000",
        "--base-url",
        "-b",
        help="API base URL.",
    ),
) -> None:
    """Show system status by calling the /health endpoint."""
    import httpx

    try:
        with httpx.Client(base_url=base_url, timeout=10.0) as client:
            resp = client.get("/health")
            resp.raise_for_status()
            data = resp.json()
            typer.echo(json.dumps(data, indent=2))
    except httpx.HTTPStatusError as exc:
        msg = f"Health check failed ({exc.response.status_code}): {exc.response.text}"
        typer.echo(msg, err=True)
        raise typer.Exit(code=1) from exc
    except httpx.ConnectError as exc:
        typer.echo(f"Cannot connect to {base_url}: {exc}", err=True)
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
