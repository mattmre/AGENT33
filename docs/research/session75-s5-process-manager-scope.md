# Session 75: S5 Process Manager Scope and Implementation

Date: 2026-03-12
Worktree: `D:\GITHUB\AGENT33\worktrees\session75-s5-process-manager`
Slice: `S5 - OpenClaw Track 5B process manager surface`
Status: implementation complete, validation complete, PR prep pending

## Baseline

- `main` already includes the governed `apply_patch` tool from `S4`.
- `engine/src/agent33/workflows/actions/run_command.py` still runs commands in a fire-and-wait mode only.
- There was no dedicated runtime service for long-running commands, no persisted command inventory, and no log-tail API.
- Operator inventory surfaces existed, but process management remained a skeleton.

## Scope Lock

Included:

- backend-first managed process service for long-running commands
- durable process metadata persisted through the orchestration state store when configured
- working-directory containment under the engine workspace root
- lifecycle routes for start, list, detail, log tail, stdin write, terminate, and cleanup
- governance alignment for process start by reusing shell-tool preflight checks
- operator inventory visibility for active managed processes
- focused service and API tests

Non-goals:

- frontend process manager UX
- interactive PTY emulation
- replacing existing workflow execution primitives
- backup/export flows from Track 6

## Landed Design

### Runtime service

- Added `agent33.processes.service.ProcessManagerService`.
- Manages subprocess startup, stdout/stderr capture, bounded log files, stdin writes, termination, cleanup, and shutdown handling.
- Recovers persisted records on restart and marks previously running processes as `interrupted` because live handles cannot be reattached safely.

### API surface

- Added `GET /v1/processes`
- Added `POST /v1/processes`
- Added `GET /v1/processes/{process_id}`
- Added `GET /v1/processes/{process_id}/log`
- Added `POST /v1/processes/{process_id}/write`
- Added `DELETE /v1/processes/{process_id}`
- Added `POST /v1/processes/cleanup`

### Governance and containment

- Process start is preflighted through `ToolGovernance.pre_execute_check("shell", ...)`.
- Working directories resolve relative to the configured workspace root and are rejected if they escape it.
- New permission scopes:
  - `processes:read`
  - `processes:manage`

### Operator visibility

- `OperatorService.get_status()` now reports a `processes` inventory with total and active counts when the service is present.

## Validation

- `PYTHONPATH=D:\GITHUB\AGENT33\worktrees\session75-s5-process-manager\engine\src python -m pytest engine/tests/test_process_manager.py engine/tests/test_processes_api.py -q --no-cov`
- `PYTHONPATH=D:\GITHUB\AGENT33\worktrees\session75-s5-process-manager\engine\src python -m pytest engine/tests/test_operator_api.py engine/tests/test_process_manager.py engine/tests/test_processes_api.py -q --no-cov`
- `python -m ruff check engine/src/agent33/processes engine/src/agent33/api/routes/processes.py engine/src/agent33/operator/service.py engine/src/agent33/security/permissions.py engine/src/agent33/config.py engine/src/agent33/main.py engine/tests/test_process_manager.py engine/tests/test_processes_api.py`
- `python -m ruff format --check engine/src/agent33/processes engine/src/agent33/api/routes/processes.py engine/src/agent33/operator/service.py engine/src/agent33/security/permissions.py engine/src/agent33/config.py engine/src/agent33/main.py engine/tests/test_process_manager.py engine/tests/test_processes_api.py`
- `PYTHONPATH=D:\GITHUB\AGENT33\worktrees\session75-s5-process-manager\engine\src python -m mypy engine/src/agent33/processes engine/src/agent33/api/routes/processes.py engine/src/agent33/operator/service.py engine/src/agent33/security/permissions.py engine/src/agent33/config.py engine/src/agent33/main.py --config-file engine/pyproject.toml`

## Next Step

- Prepare the S5 PR from this validated worktree.
