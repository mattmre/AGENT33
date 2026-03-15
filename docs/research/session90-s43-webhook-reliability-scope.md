# S43: Webhook Delivery Reliability

**Session**: 90
**Date**: 2026-03-15
**Status**: Implementation complete

## Problem

The existing webhook infrastructure (`automation/webhooks.py`) handles trigger registration and dispatch but lacks delivery reliability: no retries, no receipts, no dead-letter queue, and no admin visibility into delivery health.

## Solution

Add a `WebhookDeliveryManager` that wraps outbound webhook HTTP calls with:

1. **Exponential backoff retries** -- `delay = min(base * 2^attempt, max_delay) * jitter`
2. **Delivery receipts** -- each attempt records status code, response body (truncated), duration, error
3. **Dead-letter queue** -- permanently failed deliveries (after max retries) are queryable and retryable
4. **Bounded in-memory storage** -- evicts oldest delivered records first when at capacity
5. **Admin API** -- 6 endpoints for delivery listing, detail, stats, dead-letters, retry, and purge

## Files

| File | Purpose |
|------|---------|
| `engine/src/agent33/automation/webhook_delivery.py` | Core manager: models, backoff, lifecycle |
| `engine/src/agent33/api/routes/webhook_delivery.py` | 6 admin endpoints under `/v1/webhooks/deliveries` |
| `engine/src/agent33/config.py` | 4 new settings: `webhook_delivery_*` |
| `engine/src/agent33/main.py` | Lifespan init + router registration |
| `engine/tests/test_webhook_delivery.py` | Comprehensive tests |

## Config

| Setting | Default | Description |
|---------|---------|-------------|
| `webhook_delivery_max_retries` | 5 | Max delivery attempts before dead-lettering |
| `webhook_delivery_base_delay` | 1.0 | Base delay in seconds for exponential backoff |
| `webhook_delivery_max_delay` | 300.0 | Maximum backoff delay cap in seconds |
| `webhook_delivery_max_records` | 10000 | Bounded storage limit for in-memory records |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/webhooks/deliveries` | List deliveries (filter by status, webhook_id) |
| GET | `/v1/webhooks/deliveries/stats` | Aggregate delivery statistics |
| GET | `/v1/webhooks/deliveries/dead-letters` | List dead-lettered deliveries |
| GET | `/v1/webhooks/deliveries/{id}` | Single delivery detail with attempts |
| POST | `/v1/webhooks/deliveries/{id}/retry` | Re-enqueue a dead-lettered delivery |
| DELETE | `/v1/webhooks/deliveries/purge` | Purge old delivered records |

## Design Decisions

- **In-memory only**: Matches existing patterns (DeadLetterQueue, ProvenanceCollector). Production persistence is a follow-up.
- **Thread-safe**: Uses `threading.Lock` for all mutations; safe for concurrent webhook deliveries.
- **Simulated HTTP**: `attempt_delivery()` is a simulation point. Production integrations would override/wrap with real `httpx` calls.
- **Scope-gated**: All endpoints require `admin` scope, consistent with operational endpoints.
