# Phase 28 - Frontend Workspace Research

**Date:** 2026-02-17  
**Status:** Complete  
**Scope:** Component Security Domain Frontend Integration

## Executive Summary

This research documents the minimal frontend workspace integration for the Component Security API domain. The goal is to expose the existing backend routes through the frontend domain panel system using the established pattern of domain config files and OperationCard components.

## Backend API Analysis

### Existing Routes
File: `engine/src/agent33/api/routes/component_security.py`

**Base Path:** `/v1/component-security`

#### Endpoints
1. **POST /runs** - Create security run
   - Scope: `component-security:write`
   - Body: `CreateSecurityRunRequest` (target, profile, options, execute_now)
   - Response: Run object with ID, status, findings

2. **GET /runs** - List security runs
   - Scope: `component-security:read`
   - Query params: status, profile, limit (default 50)
   - Response: Array of run objects

3. **GET /runs/{run_id}** - Get run details
   - Scope: `component-security:read`
   - Path param: run_id
   - Response: Single run object

4. **GET /runs/{run_id}/findings** - Get run findings
   - Scope: `component-security:read`
   - Path param: run_id
   - Query param: min_severity (optional)
   - Response: `{ findings: [], total_count: N }`

5. **POST /runs/{run_id}/cancel** - Cancel run
   - Scope: `component-security:write`
   - Path param: run_id
   - Response: Updated run object

6. **DELETE /runs/{run_id}** - Delete run
   - Scope: `component-security:write`
   - Path param: run_id
   - Response: `{ deleted: run_id }`

7. **GET /runs/{run_id}/status** - Get run status (polling)
   - Scope: `component-security:read`
   - Path param: run_id
   - Response: `{ run_id, status }`

### Models
- **ScanTarget:** path, repository info
- **SecurityProfile:** QUICK | STANDARD | DEEP
- **ScanOptions:** Configuration options
- **FindingSeverity:** CRITICAL | HIGH | MEDIUM | LOW | INFO
- **RunStatus:** PENDING | RUNNING | COMPLETED | FAILED | CANCELLED

## Frontend Pattern Analysis

### Domain Config Pattern
Reviewed: `frontend/src/data/domains/*.ts`

Each domain follows this structure:
```typescript
export const domainName: DomainConfig = {
  id: "domain-id",
  title: "Display Title",
  description: "Brief description",
  operations: [
    {
      id: "operation-id",
      title: "Operation Title",
      method: "GET|POST|PUT|PATCH|DELETE",
      path: "/v1/domain/path",
      description: "What this does",
      defaultPathParams?: { param: "value" },
      defaultQueryParams?: { param: "value" },
      defaultBody?: JSON.stringify({...}, null, 2)
    }
  ]
};
```

### Registration Pattern
File: `frontend/src/data/domains.ts`

1. Import domain config
2. Add to exported `domains` array
3. No additional glue code needed

### UI Rendering
The existing `DomainPanel` + `OperationCard` components automatically:
- Render all operations as cards
- Handle method types with color coding
- Parse path params from URL pattern
- Provide input fields for params/body
- Execute API calls
- Display responses

## Minimal Implementation Plan

### Files to Create
1. **frontend/src/data/domains/component-security.ts**
   - Domain config with all 7 endpoints
   - Default values for common params
   - Example request bodies

### Files to Modify
2. **frontend/src/data/domains.ts**
   - Import componentSecurityDomain
   - Add to domains array

### Optional Enhancement
3. **frontend/src/data/domains/__tests__/component-security.test.ts**
   - Basic structure validation
   - Ensure all operations have required fields

## Success Criteria

✅ Backend routes mapped 1:1 to operations  
✅ No custom React components required  
✅ Reuses existing DomainPanel/OperationCard rendering  
✅ Default values provided for quick testing  
✅ Path params clearly marked with `{param}` syntax  
✅ POST/PATCH operations include example bodies

## Dependencies

None. Uses existing:
- TypeScript types from `frontend/src/types`
- Domain registry system
- DomainPanel/OperationCard components

## Risk Assessment

**LOW RISK** - This is a pure configuration addition:
- No new components
- No new dependencies
- No API changes
- Follows established pattern used by 16 existing domains

## References

- Backend routes: `engine/src/agent33/api/routes/component_security.py`
- Domain pattern: `frontend/src/data/domains/evaluations.ts` (similar complexity)
- Type definitions: `frontend/src/types` (DomainConfig, OperationConfig)
- Registry: `frontend/src/data/domains.ts`
