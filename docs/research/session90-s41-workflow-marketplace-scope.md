# S41: Workflow Template Marketplace - Scope

**Session**: 90
**Date**: 2026-03-15
**Status**: Implemented

## What Was Implemented

A complete workflow template marketplace system that allows operators to:

- Browse available workflow templates by category and tags
- Search templates by name, description, and tag matching
- Publish new templates to the marketplace
- Install templates (tracked per-tenant with install counts)
- Rate templates with star ratings (1-5, one per tenant, replaceable)
- View marketplace statistics (totals, category breakdown, average ratings)
- Delete templates from the marketplace

### Service Layer (`engine/src/agent33/workflows/marketplace.py`)

Core `WorkflowMarketplace` class with:
- Thread-safe in-memory store (bounded at 10,000 templates)
- `TemplateCategory` enum: automation, data-pipeline, research, review, deployment, custom
- `TemplateSortField` enum: name, rating, install_count, created_at, updated_at
- CRUD: register, get, list (with category filter + pagination), remove
- Search: query string (name/description/tags), category filter, tag set matching, sort
- Install: returns workflow definition dict, tracks unique tenants per template
- Rate: star ratings 1-5, per-tenant deduplication (latest replaces previous), running average
- Stats: total count, by-category breakdown, total installs/ratings, average rating
- `create_template_from_workflow()`: create marketplace template from existing WorkflowDefinition
- `discover_builtin_templates()`: auto-discover from YAML files in configured directory

### API Layer (`engine/src/agent33/api/routes/workflow_marketplace.py`)

7 endpoints under `/v1/workflow-marketplace`:
- `GET  /templates` - List/search with q, category, tags, sort_by, limit, offset params
- `GET  /templates/{id}` - Get template detail
- `POST /templates` - Publish new template
- `POST /templates/{id}/install` - Install template (tenant tracked from auth)
- `POST /templates/{id}/rate` - Submit star rating
- `GET  /stats` - Marketplace statistics
- `DELETE /templates/{id}` - Remove template

All endpoints require `workflows:read` or `workflows:write` scopes.

### Configuration (`engine/src/agent33/config.py`)

Two new settings:
- `workflow_marketplace_enabled: bool = True`
- `workflow_templates_dir: str = "workflow-templates"`

### Lifespan Wiring (`engine/src/agent33/main.py`)

Marketplace initialized after template catalog, before discovery service.
Stored on `app.state.workflow_marketplace` and module-level singleton.

## Key Design Decisions

1. **Separate prefix from pack marketplace**: Used `/v1/workflow-marketplace` instead of `/v1/marketplace` since that prefix is already occupied by the existing pack marketplace routes.

2. **In-memory store with thread-safe locking**: Follows the existing SkillRegistry and TemplateCatalog patterns. No database dependency, bounded capacity.

3. **Per-tenant rating deduplication**: Each tenant can have one rating per template. Re-rating replaces the previous value. This prevents rating inflation.

4. **Install tracking by unique tenants**: Install count reflects unique tenants, not total install API calls. Same tenant installing twice counts once.

5. **String-based query params for enums**: Used `str | None` for category and sort_by query parameters to avoid ruff B008 lint errors, with safe fallback parsing in the handler body.

6. **structlog over stdlib logging**: Consistent with project convention for structured keyword logging.

## Files Created

- `engine/src/agent33/workflows/marketplace.py` - Core marketplace service (320 lines)
- `engine/src/agent33/api/routes/workflow_marketplace.py` - API routes (230 lines)
- `engine/tests/test_workflow_marketplace.py` - 46 tests covering all behavior
- `docs/research/session90-s41-workflow-marketplace-scope.md` - This document

## Files Modified

- `engine/src/agent33/config.py` - Added 2 config fields
- `engine/src/agent33/main.py` - Added import, lifespan init block, router inclusion

## Test Coverage

46 tests organized into 8 test classes:
- `TestTemplateCRUD` (9 tests): register/get/list/delete/count
- `TestTemplateSearch` (8 tests): name/description/tags/category/sort/pagination
- `TestTemplateInstall` (4 tests): install flow, count tracking, tenant dedup, error
- `TestTemplateRating` (6 tests): rating, average, tenant replace, bounds validation
- `TestTemplateStats` (2 tests): empty and populated statistics
- `TestCreateFromWorkflow` (2 tests): from workflow with explicit and default metadata
- `TestMarketplaceAPI` (14 tests): all 7 endpoints with auth mocking, happy + error paths
- `TestMarketplaceAPIUninitialised` (1 test): 503 when marketplace not set
