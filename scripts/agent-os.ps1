param(
    [ValidateSet("start", "shell", "status", "logs", "stop")]
    [string]$Command = "start"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $RepoRoot "engine\docker-compose.yml"
$EnvFile = Join-Path $RepoRoot "engine\.env"
$EnvExample = Join-Path $RepoRoot "engine\.env.example"

function Ensure-AgentOsEnv {
    if (-not (Test-Path $EnvFile)) {
        Copy-Item $EnvExample $EnvFile
        Write-Host "Created engine\.env from .env.example. Rotate secrets before shared use."
    }
}

switch ($Command) {
    "start" {
        Ensure-AgentOsEnv
        docker compose -f $ComposeFile --profile agent-os up -d postgres redis nats searxng api agent-os
        Write-Host "Agent OS is starting. Open a shell with: scripts\agent-os.ps1 shell"
    }
    "shell" {
        Ensure-AgentOsEnv
        docker compose -f $ComposeFile --profile agent-os exec agent-os bash -l
    }
    "status" {
        docker compose -f $ComposeFile --profile agent-os ps
    }
    "logs" {
        docker compose -f $ComposeFile --profile agent-os logs --tail=120 agent-os
    }
    "stop" {
        docker compose -f $ComposeFile --profile agent-os down
    }
}
