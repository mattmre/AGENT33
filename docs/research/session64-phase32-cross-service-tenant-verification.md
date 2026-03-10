# Session 64: Phase 32 Cross-Service Tenant Verification Foundation

Date: 2026-03-09
Scope: Current `main` priority 4 from `docs/next-session.md`

## Problem

Tenant filtering is inconsistent across the operational surfaces added in recent phases:

- `improvements.py` accepts `tenant_id` from request bodies and query params even when an authenticated tenant is present.
- `traces.py` filters trace lists by tenant, but direct-ID routes do not verify ownership before returning or mutating a trace.
- `multimodal.py` scopes request lifecycle reads/writes by tenant, but the policy helper route allows writes to any path tenant.

These gaps create IDOR-style leakage and mutation risk whenever a caller has a valid token for one tenant but can still name another tenant in the request.

## Design

Add one shared hardening layer at the route/service boundary:

1. Treat the authenticated tenant as the source of truth for non-admin callers.
2. Allow explicit cross-tenant targeting only when the caller has `admin`.
3. Reject mismatched tenant selectors instead of silently mixing authenticated and requested tenant context.
4. Extend trace collector direct-ID operations with optional tenant checks so route handlers can enforce ownership on reads and writes.
5. Keep unauthenticated or tenant-less test/admin flows working by falling back to existing defaults when no concrete tenant is attached to the request.

## PR Scope

- `engine/src/agent33/api/routes/improvements.py`
  - Add tenant resolution helpers.
  - Harden intake and learning endpoints that accept body/query tenant selectors.
  - Restrict backup/restore endpoints to `admin`.
- `engine/src/agent33/api/routes/traces.py`
  - Pass authenticated tenant context into direct-ID read/mutate operations.
- `engine/src/agent33/observability/trace_collector.py`
  - Add optional tenant-aware access checks for trace/failure operations.
- `engine/src/agent33/api/routes/multimodal.py`
  - Bind policy writes to the authenticated tenant unless the caller is `admin`.

## Non-Goals

- No URL-scoped tenant namespacing yet.
- No database row-level security changes.
- No connector registry or MCP client hardening in this PR; those remain later Phase 32 work.
- No new improvement-specific RBAC surface beyond `admin` protection for backup/restore.

## Acceptance Criteria

- A tenant-scoped caller cannot read or mutate another tenant's trace by ID.
- A tenant-scoped caller cannot set multimodal policy for another tenant via the path parameter.
- Improvement intake and learning routes reject cross-tenant body/query overrides for non-admin callers.
- Backup/restore routes require `admin`.
- Regression tests exercise authenticated tenant mismatch cases, not just unauthenticated failures.
