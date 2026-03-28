# Operator Verification Runbook

## Purpose

Run the shortest honest verification path for the current operator control
plane and the adjacent high-risk operator surfaces already shipped on `main`.

Use this runbook with:

- [`production-deployment-runbook.md`](production-deployment-runbook.md)
- [`incident-response-playbooks.md`](incident-response-playbooks.md)
- [`process-registry-runbook.md`](process-registry-runbook.md)
- [`../../engine/src/agent33/api/routes/operator.py`](../../engine/src/agent33/api/routes/operator.py)
- [`../../engine/src/agent33/api/routes/backups.py`](../../engine/src/agent33/api/routes/backups.py)

This runbook does not define new dashboards, new automation, or destructive
restore execution.

## Required Scopes

Use a read-only verification token with:

- `operator:read`
- `processes:read`

Use a separate elevated reset token with:

- `operator:write`
- `admin`

Keep the first verification pass on the read-only token. Only use the elevated
token if you have already captured `status` and `doctor` and a bounded reset is
actually justified.

## Canonical Verification Order

Use the authenticated checks in this order:

1. `GET /v1/operator/status`
2. `GET /v1/operator/doctor`
3. `GET /v1/processes?limit=50`
4. `GET /v1/backups`
5. If a backup exists, `POST /v1/backups/{backup_id}/verify`
6. If restore safety must be inspected, `POST /v1/backups/{backup_id}/restore-plan`
7. If you are planning a fresh backup, `GET /v1/backups/inventory`

This order keeps the first pass read-only and short.

## Operator Control Plane Check

1. Capture the status snapshot.

```bash
curl "http://127.0.0.1:8000/v1/operator/status" \
  -H "Authorization: Bearer $READ_TOKEN"
```

Use it to confirm:

- overall authenticated operator reachability
- subsystem inventory counts
- dependency-aware health states already surfaced by `/health`

2. Capture the diagnostic snapshot.

```bash
curl "http://127.0.0.1:8000/v1/operator/doctor" \
  -H "Authorization: Bearer $READ_TOKEN"
```

Use it to confirm:

- whether the failure is a warning or an error
- the first remediation text for the failing subsystem
- whether a bounded reset is justified

## Process Registry Check

Use the canonical process inventory command from the dedicated process runbook:

```bash
curl "http://127.0.0.1:8000/v1/processes?limit=50" \
  -H "Authorization: Bearer $READ_TOKEN"
```

If any process needs deeper inspection or recovery, continue in
[`process-registry-runbook.md`](process-registry-runbook.md).

## Backup Verification Check

1. List existing archives.

```bash
curl "http://127.0.0.1:8000/v1/backups" \
  -H "Authorization: Bearer $READ_TOKEN"
```

2. Verify one archive.

```bash
curl -X POST "http://127.0.0.1:8000/v1/backups/$BACKUP_ID/verify" \
  -H "Authorization: Bearer $READ_TOKEN"
```

3. Inspect the inventory for a potential new backup.

```bash
curl "http://127.0.0.1:8000/v1/backups/inventory" \
  -H "Authorization: Bearer $READ_TOKEN"
```

4. If you need a read-only safety check before later restore work, generate a
   restore preview.

```bash
curl -X POST "http://127.0.0.1:8000/v1/backups/$BACKUP_ID/restore-plan" \
  -H "Authorization: Bearer $READ_TOKEN"
```

Use restore preview only to inspect conflicts and planned actions. This slice
does not claim a destructive restore command.

## Bounded Reset Path

Use `/v1/operator/reset` only after `status` and `doctor` have been captured.

Registry-only reset:

```bash
curl -X POST "http://127.0.0.1:8000/v1/operator/reset" \
  -H "Authorization: Bearer $RESET_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"targets":["registries"]}'
```

Cache-only reset:

```bash
curl -X POST "http://127.0.0.1:8000/v1/operator/reset" \
  -H "Authorization: Bearer $RESET_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"targets":["caches"]}'
```

Use reset when the doctor output points to stale cache or discovery state. Do
not use it as a substitute for dependency recovery, rollout rollback, or backup
restore execution.

## Escalate When

- `/v1/operator/status` or `/v1/operator/doctor` returns `503`
- the doctor reports repeated `error` checks after one bounded reset
- process-registry inspection suggests lost ownership or unsafe tenant leakage
- backup verification or restore preview reports conflicts that do not match the
  expected on-disk state
