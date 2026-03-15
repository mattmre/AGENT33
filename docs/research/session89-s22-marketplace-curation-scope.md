# S22: Phase 33 Marketplace Curation -- Scope

Session: 89 | Slice: S22 | Date: 2026-03-14

## Objective

Add curation lifecycle, quality assessment, and category management to the
pack marketplace. This builds on the existing Phase 33 marketplace foundation
(discovery, installation, trust, rollback) by adding the editorial layer that
controls which packs appear in public listings.

## Deliverables

### New modules

| File | Purpose |
|------|---------|
| `engine/src/agent33/packs/curation.py` | State machine, quality scoring, curation record model |
| `engine/src/agent33/packs/categories.py` | Category registry with state-store persistence |
| `engine/src/agent33/packs/curation_service.py` | Orchestration service for the curation lifecycle |

### Modified modules

| File | Change |
|------|--------|
| `engine/src/agent33/packs/api_models.py` | Added curation/category request models |
| `engine/src/agent33/packs/__init__.py` | Re-export new types |
| `engine/src/agent33/api/routes/marketplace.py` | 14 new endpoints for curation and categories |
| `engine/src/agent33/config.py` | 4 new settings (`pack_curation_enabled`, etc.) |
| `engine/src/agent33/main.py` | Wire CategoryRegistry + CurationService at startup |

### Tests

| File | Coverage |
|------|----------|
| `engine/tests/test_marketplace_curation.py` | State machine, quality scoring, service lifecycle, category CRUD, API routes |

## Architecture Decisions

1. **State machine pattern** -- mirrors `review/state_machine.py` with a
   `_VALID_TRANSITIONS` dict and static `can_transition` / `transition` methods.

2. **Quality scoring** -- weighted multi-dimension approach following
   `improvement/quality.py`, scoring description, tags, category, license,
   author, skills count, and provenance.

3. **Persistence** -- follows `TrustPolicyManager` pattern using the
   orchestration `state_store` with separate namespaces (`pack_curation`,
   `pack_categories`).

4. **Lazy service resolution** -- routes resolve `curation_service` and
   `category_registry` from `request.app.state`, returning 503 if not
   initialized.

## Curation State Machine

```
DRAFT -> SUBMITTED -> UNDER_REVIEW -> APPROVED -> LISTED -> FEATURED
                                   \-> CHANGES_REQUESTED -> SUBMITTED
                                                LISTED -> DEPRECATED -> UNLISTED
                                                LISTED -> UNLISTED
                                              FEATURED -> LISTED
                                              FEATURED -> DEPRECATED
                                              FEATURED -> UNLISTED
                                              UNLISTED -> SUBMITTED
```

## Quality Dimensions

| Dimension | Weight | Threshold |
|-----------|--------|-----------|
| description_quality | 0.20 | >= 50 chars |
| tags_present | 0.15 | >= 2 tags |
| category_assigned | 0.15 | non-empty |
| license_present | 0.10 | non-empty |
| author_present | 0.10 | non-empty |
| skills_count | 0.15 | >= 1 skill |
| provenance_signed | 0.15 | has provenance |

Labels: high >= 0.70, medium >= 0.45, low < 0.45.
