# Phase 28 - Frontend Workspace Architecture

**Date:** 2026-02-17  
**Status:** Complete  
**Phase:** Component Security Frontend Integration  
**Scope:** MVP - Domain Config Only

## Architecture Overview

Integrate Component Security API into the frontend workspace by adding a domain configuration file following the established pattern. No custom UI components required.

## System Context

```
┌─────────────────────────────────────────────────────┐
│         Frontend Domain Panel System                │
├─────────────────────────────────────────────────────┤
│  DomainPanel (existing)                             │
│    ├─> Reads domains array                          │
│    └─> Renders OperationCard for each operation     │
│                                                      │
│  domains.ts (registry)                              │
│    ├─> healthDomain                                 │
│    ├─> authDomain                                   │
│    ├─> ... (14 more)                                │
│    └─> componentSecurityDomain (NEW)                │
└─────────────────────────────────────────────────────┘
                        │
                        │ HTTP Requests
                        ▼
┌─────────────────────────────────────────────────────┐
│         Backend API (existing)                       │
├─────────────────────────────────────────────────────┤
│  /v1/component-security/runs              (7 routes)│
│  /v1/component-security/runs/{run_id}               │
│  /v1/component-security/runs/{run_id}/findings      │
│  ...                                                 │
└─────────────────────────────────────────────────────┘
```

## File Structure

```
frontend/src/data/
├── domains.ts                     # Registry (modify)
├── domains/
│   ├── component-security.ts      # New domain config
│   ├── evaluations.ts             # Reference pattern
│   └── ... (15 other domains)
└── domains/__tests__/
    └── component-security.test.ts # Optional unit test
```

## Domain Configuration Specification

### File: frontend/src/data/domains/component-security.ts

```typescript
import type { DomainConfig } from "../../types";

export const componentSecurityDomain: DomainConfig = {
  id: "component-security",
  title: "Component Security",
  description: "Security scans, findings, profiles.",
  operations: [
    // 7 operations mapped to backend routes
  ]
};
```

### Operations Mapping

| Operation ID | Method | Backend Route | Purpose |
|--------------|--------|---------------|---------|
| `sec-create-run` | POST | `/v1/component-security/runs` | Create new scan run |
| `sec-list-runs` | GET | `/v1/component-security/runs` | List all runs |
| `sec-get-run` | GET | `/v1/component-security/runs/{run_id}` | Get run details |
| `sec-get-findings` | GET | `/v1/component-security/runs/{run_id}/findings` | Get findings |
| `sec-cancel-run` | POST | `/v1/component-security/runs/{run_id}/cancel` | Cancel run |
| `sec-delete-run` | DELETE | `/v1/component-security/runs/{run_id}` | Delete run |
| `sec-run-status` | GET | `/v1/component-security/runs/{run_id}/status` | Poll run status |

### Default Values Strategy

**Path Parameters:**
- `run_id`: `"replace-with-run-id"` (user must update)

**Query Parameters:**
- `limit`: 20 (reasonable default)
- `status`: null (show all)
- `profile`: null (show all)
- `min_severity`: null (show all findings)

**Request Bodies:**

1. **Create Run (POST /runs):**
```json
{
  "target": {
    "path": "/path/to/component",
    "repository": "optional-repo-url"
  },
  "profile": "QUICK",
  "options": {},
  "execute_now": true
}
```

2. **Cancel Run (POST /runs/{run_id}/cancel):**
- No body required

## Type Safety

Uses existing TypeScript types:
- `DomainConfig` from `frontend/src/types`
- `OperationConfig` for each operation
- No new types needed

## Integration Points

### 1. Domain Registry (domains.ts)

```typescript
// Add import
import { componentSecurityDomain } from "./domains/component-security";

// Add to array (alphabetical position or logical grouping)
export const domains: DomainConfig[] = [
  healthDomain,
  authDomain,
  // ... existing domains ...
  componentSecurityDomain,  // ADD HERE
  // ... remaining domains ...
];
```

### 2. Existing UI Components (No Changes)

- `DomainPanel`: Already renders all domains
- `OperationCard`: Already handles all methods
- No custom components needed

## Security & Permissions

Backend enforces scopes:
- `component-security:read` - GET operations
- `component-security:write` - POST, DELETE operations

Frontend domain config is passive - it only defines available operations. Authorization is handled by:
1. Backend route decorators (`require_scope`)
2. API client token inclusion
3. HTTP 403 responses on unauthorized access

## Testing Strategy

### Unit Test (Optional)
File: `frontend/src/data/domains/__tests__/component-security.test.ts`

```typescript
import { componentSecurityDomain } from "../component-security";

describe("componentSecurityDomain", () => {
  it("should have valid structure", () => {
    expect(componentSecurityDomain.id).toBe("component-security");
    expect(componentSecurityDomain.operations.length).toBe(7);
  });

  it("should have all required operation fields", () => {
    componentSecurityDomain.operations.forEach(op => {
      expect(op.id).toBeDefined();
      expect(op.method).toMatch(/^(GET|POST|DELETE)$/);
      expect(op.path).toMatch(/^\/v1\/component-security/);
    });
  });
});
```

## Implementation Sequence

1. **Create domain config file**
   - Define 7 operations with correct paths
   - Add default values for quick testing
   - Export `componentSecurityDomain`

2. **Register in domains.ts**
   - Import domain
   - Add to array

3. **Optional: Add unit test**
   - Validate structure
   - Ensure no typos in paths/methods

4. **Manual verification**
   - Load frontend
   - Navigate to Component Security domain
   - Verify 7 operation cards render
   - Test API call execution

## Non-Goals (Out of Scope)

❌ Custom React components for security findings  
❌ Real-time status polling UI  
❌ Findings visualization dashboard  
❌ Scan result diff viewer  
❌ Integration with other domains  

These may be added in future phases if needed.

## Success Metrics

- ✅ All 7 backend routes accessible via UI
- ✅ No console errors on domain load
- ✅ API calls execute successfully with valid tokens
- ✅ Response data displays in UI
- ✅ Zero new dependencies added

## Rollback Plan

If issues arise:
1. Remove import from `domains.ts`
2. Remove from domains array
3. Delete `component-security.ts` file
4. No other cleanup needed (zero side effects)

## Future Enhancements (Not in Phase 28)

- Custom findings table component
- Live status polling with progress indicator
- Security profile comparison tool
- Finding trend charts
- Integration with release workflow

## References

- **Backend API:** `engine/src/agent33/api/routes/component_security.py`
- **Pattern Reference:** `frontend/src/data/domains/evaluations.ts`
- **Type Definitions:** `frontend/src/types` (DomainConfig interface)
- **Research Doc:** `docs/research/phase28-frontend-workspace-research-2026-02-17.md`
