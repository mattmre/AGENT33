# Session 64: Phase 31 Backup/Restore Validation Matrix

**Date:** 2026-03-09
**Scope:** Production hardening for learning-state backup and restore.

## Problem

Phase 31 already had working backup and restore endpoints, but the persisted backup
format was still a raw state dump:

- no backup format version
- no creation timestamp
- no integrity checksum
- no metadata counts to detect truncated or partially edited payloads

That was sufficient for basic operator recovery, but not for production-scale confidence
where backups may be copied across hosts, inspected manually, or restored long after they
were created.

## Design

Introduce a versioned backup envelope around `LearningPersistenceState`:

- `format_version`
- `created_at`
- `signal_count`
- `intake_count`
- `signal_intake_map_count`
- `checksum_sha256`
- `state`

Backup writes remain portable JSON, but now carry enough metadata to detect common
corruption and tampering scenarios before state is written back into the active store.

## Validation Rules

During restore, the system now accepts two formats:

1. **Versioned envelope**: validated for count consistency and SHA-256 checksum.
2. **Legacy raw state payload**: still supported for backward compatibility with already
   published runbooks and earlier backups.

Envelope restores fail before persistence if:

- `signal_count` does not match the payload
- `intake_count` does not match the payload
- `signal_intake_map_count` does not match the payload
- `checksum_sha256` does not match the canonical serialized state

## Write Semantics

Backup creation now uses a temporary file plus replace operation so the backup path is not
left half-written if the process is interrupted during serialization.

## Coverage Added

- versioned envelope backup creation
- legacy raw backup compatibility
- checksum mismatch rejection
- count mismatch rejection
- endpoint assertions updated to verify the versioned envelope shape
