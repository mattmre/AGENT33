---
title: "Session 17: Matrix Channel Adapter Requirements Analysis"
date: 2026-02-15
session: 17
type: research
status: complete
---

# Session 17: Matrix Channel Adapter Requirements Analysis

## Overview

This document analyzes the requirements for implementing a Matrix channel adapter for AGENT-33's messaging subsystem. Matrix is the last remaining channel adapter from the ZeroClaw feature parity analysis (item #8 on the 20-item roadmap). This analysis covers the existing adapter patterns, Matrix-specific protocol requirements, and a concrete implementation plan.

## MessagingAdapter Protocol (6 Members)

The `MessagingAdapter` protocol in `messaging/` defines the contract that all channel adapters must implement:

```python
class MessagingAdapter(Protocol):
    @property
    def platform(self) -> str:
        """Platform identifier (e.g., 'telegram', 'discord', 'matrix')."""
        ...

    async def send(self, channel_id: str, text: str) -> None:
        """Send a text message to a channel."""
        ...

    async def receive(self) -> Message:
        """Receive the next incoming message (blocks until available)."""
        ...

    async def start(self) -> None:
        """Initialize the adapter and begin listening for messages."""
        ...

    async def stop(self) -> None:
        """Gracefully shut down the adapter."""
        ...

    async def health_check(self) -> ChannelHealthResult:
        """Check adapter health status."""
        ...
```

All 4 existing adapters (Telegram, Discord, Slack, WhatsApp) implement this protocol. The Matrix adapter must do the same.

## Existing Adapter Patterns

### HTTP Client Approach

All existing adapters use `httpx.AsyncClient` directly rather than platform-specific SDKs. This is a deliberate architectural decision:

- **Consistency**: All adapters follow the same HTTP pattern
- **Dependency minimization**: No platform SDK dependencies to manage
- **Control**: Direct HTTP gives full control over retry logic, timeouts, and error handling
- **ZeroClaw alignment**: ZeroClaw also uses raw HTTP for Matrix

### Constructor Pattern

```python
class TelegramAdapter:
    def __init__(self, bot_token: str, ...):
        self._bot_token = bot_token
        self._client: httpx.AsyncClient | None = None
        self._queue: asyncio.Queue[Message] = asyncio.Queue()
        self._running = False
```

All adapters take credentials in the constructor (not a config object). Internal state consists of:
- `_client`: httpx.AsyncClient instance (created in `start()`, closed in `stop()`)
- `_queue`: asyncio.Queue for incoming messages
- `_running`: Boolean flag for lifecycle management

### Lifecycle Pattern

```python
async def start(self) -> None:
    self._client = httpx.AsyncClient(...)
    self._running = True
    # Start background polling/websocket task

async def stop(self) -> None:
    self._running = False
    if self._client:
        await self._client.aclose()
        self._client = None
```

### Health Check Pattern (3-Tier)

All adapters implement the same 3-tier health check pattern:

1. **Not started** -> `ChannelHealthResult(status="unavailable", message="Adapter not started")`
2. **API probe succeeds** -> `ChannelHealthResult(status="ok", ...)` or `ChannelHealthResult(status="degraded", ...)` (based on queue depth)
3. **API probe fails** -> `ChannelHealthResult(status="unavailable", message=str(error))`

Queue depth thresholds:
- `queue_depth < 100` -> "ok"
- `queue_depth >= 100` -> "degraded"

## Matrix-Specific Requirements

### Core Endpoints

The Matrix Client-Server API (spec v1.11) endpoints needed for a basic adapter:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/_matrix/client/v3/sync` | GET | Long-polling for new events |
| `/_matrix/client/v3/rooms/{roomId}/send/{eventType}/{txnId}` | PUT | Send message to room |
| `/_matrix/client/v3/account/whoami` | GET | Health check / auth verification |

### Authentication

Matrix uses access token authentication via the `Authorization: Bearer {token}` header. The access token is obtained out-of-band (manual login, SSO, or token generation via admin API).

### Sync Mechanism

Matrix uses a long-polling sync endpoint with `next_batch` tokens for incremental updates:

```
GET /_matrix/client/v3/sync?since={next_batch}&timeout=30000
```

- First call: No `since` parameter, returns full initial state
- Subsequent calls: Include `since={next_batch}` from previous response
- `timeout` parameter controls long-poll duration (30 seconds recommended)
- Response includes `next_batch` token for the next request

### Transaction IDs

Message sending uses transaction IDs for idempotency:

```
PUT /_matrix/client/v3/rooms/{roomId}/send/m.room.message/{txnId}
```

- `txnId` must be unique per access token per message
- If the same `txnId` is sent twice, the server returns the original event_id without creating a duplicate
- Implementation: Use a monotonically increasing counter or UUID

### Echo Suppression

When the adapter sends a message, the sync endpoint will return that message as an incoming event. The adapter must filter out its own messages:

```python
def _is_own_message(self, event: dict) -> bool:
    return event.get("sender") == self._user_id
```

### Room Filtering

Optional room filtering allows restricting the adapter to specific rooms:

```python
def __init__(self, ..., allowed_room_ids: list[str] | None = None):
    self._allowed_room_ids = set(allowed_room_ids) if allowed_room_ids else None

def _should_process_event(self, event: dict, room_id: str) -> bool:
    if self._allowed_room_ids and room_id not in self._allowed_room_ids:
        return False
    return True
```

### Rate Limit Handling

Matrix servers return HTTP 429 with a `Retry-After` header (or `retry_after_ms` in the JSON body) when rate-limited:

```python
if response.status_code == 429:
    retry_after = response.json().get("retry_after_ms", 5000) / 1000
    await asyncio.sleep(retry_after)
    # Retry the request
```

### End-to-End Encryption (E2EE)

E2EE is NOT included in the initial implementation. Rationale:
- ZeroClaw does not implement Matrix E2EE
- E2EE requires Olm/Megolm cryptographic libraries and device management
- Adds significant complexity (~500+ lines) for limited initial value
- Can be added as a follow-up if needed

## Implementation Plan

### New File: `messaging/matrix.py`

```python
class MatrixAdapter:
    """Matrix channel adapter using Client-Server API v3.

    Uses raw httpx (no SDK) consistent with other adapters.
    Implements the MessagingAdapter protocol.
    """

    def __init__(
        self,
        homeserver_url: str,
        access_token: str,
        user_id: str,
        device_id: str | None = None,
        allowed_room_ids: list[str] | None = None,
        sync_timeout_ms: int = 30000,
    ):
        self._homeserver_url = homeserver_url.rstrip("/")
        self._access_token = access_token
        self._user_id = user_id
        self._device_id = device_id
        self._allowed_room_ids = set(allowed_room_ids) if allowed_room_ids else None
        self._sync_timeout_ms = sync_timeout_ms

        self._client: httpx.AsyncClient | None = None
        self._queue: asyncio.Queue[Message] = asyncio.Queue()
        self._running = False
        self._next_batch: str | None = None
        self._txn_counter = 0
        self._sync_task: asyncio.Task | None = None

    @property
    def platform(self) -> str:
        return "matrix"

    async def start(self) -> None:
        """Create HTTP client and start sync loop."""
        self._client = httpx.AsyncClient(
            base_url=self._homeserver_url,
            headers={"Authorization": f"Bearer {self._access_token}"},
            timeout=httpx.Timeout(self._sync_timeout_ms / 1000 + 10),
        )
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())

    async def stop(self) -> None:
        """Stop sync loop and close HTTP client."""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._sync_task
            self._sync_task = None
        if self._client:
            await self._client.aclose()
            self._client = None

    async def send(self, channel_id: str, text: str) -> None:
        """Send a text message to a Matrix room."""
        if not self._client:
            raise RuntimeError("Adapter not started")

        self._txn_counter += 1
        txn_id = f"agent33_{self._txn_counter}_{int(time.time() * 1000)}"

        response = await self._client.put(
            f"/_matrix/client/v3/rooms/{channel_id}/send/m.room.message/{txn_id}",
            json={
                "msgtype": "m.text",
                "body": text,
            },
        )

        if response.status_code == 429:
            retry_ms = response.json().get("retry_after_ms", 5000)
            await asyncio.sleep(retry_ms / 1000)
            response = await self._client.put(
                f"/_matrix/client/v3/rooms/{channel_id}/send/m.room.message/{txn_id}",
                json={"msgtype": "m.text", "body": text},
            )

        response.raise_for_status()

    async def receive(self) -> Message:
        """Receive the next incoming message (blocks until available)."""
        return await self._queue.get()

    async def health_check(self) -> ChannelHealthResult:
        """3-tier health check matching existing adapter pattern."""
        if not self._client or not self._running:
            return ChannelHealthResult(
                platform="matrix",
                status="unavailable",
                message="Adapter not started",
                queue_depth=0,
            )

        try:
            response = await self._client.get("/_matrix/client/v3/account/whoami")
            response.raise_for_status()

            queue_depth = self._queue.qsize()
            status = "ok" if queue_depth < 100 else "degraded"

            return ChannelHealthResult(
                platform="matrix",
                status=status,
                message=f"Connected as {self._user_id}",
                queue_depth=queue_depth,
            )
        except Exception as e:
            return ChannelHealthResult(
                platform="matrix",
                status="unavailable",
                message=str(e),
                queue_depth=self._queue.qsize(),
            )

    async def _sync_loop(self) -> None:
        """Background task that long-polls the /sync endpoint."""
        while self._running:
            try:
                params = {"timeout": str(self._sync_timeout_ms)}
                if self._next_batch:
                    params["since"] = self._next_batch

                response = await self._client.get(
                    "/_matrix/client/v3/sync",
                    params=params,
                )

                if response.status_code == 429:
                    retry_ms = response.json().get("retry_after_ms", 5000)
                    await asyncio.sleep(retry_ms / 1000)
                    continue

                response.raise_for_status()
                data = response.json()

                self._next_batch = data.get("next_batch")
                await self._process_sync_response(data)

            except httpx.TimeoutException:
                continue  # Normal for long-polling
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5)  # Back off on errors

    async def _process_sync_response(self, data: dict) -> None:
        """Extract messages from sync response and enqueue them."""
        rooms = data.get("rooms", {}).get("join", {})
        for room_id, room_data in rooms.items():
            if self._allowed_room_ids and room_id not in self._allowed_room_ids:
                continue

            timeline = room_data.get("timeline", {}).get("events", [])
            for event in timeline:
                if event.get("type") != "m.room.message":
                    continue
                if event.get("sender") == self._user_id:
                    continue  # Echo suppression

                content = event.get("content", {})
                if content.get("msgtype") != "m.text":
                    continue

                message = Message(
                    platform="matrix",
                    channel_id=room_id,
                    sender_id=event["sender"],
                    text=content["body"],
                    timestamp=datetime.fromtimestamp(
                        event.get("origin_server_ts", 0) / 1000,
                        tz=timezone.utc,
                    ),
                    metadata={"event_id": event.get("event_id")},
                )
                await self._queue.put(message)
```

## Config Fields

New fields in `config.py`:

```python
# Matrix adapter configuration
matrix_homeserver_url: str = ""           # e.g., "https://matrix.org"
matrix_access_token: SecretStr = SecretStr("")  # Bot access token
matrix_user_id: str = ""                  # e.g., "@agent33:matrix.org"
matrix_device_id: str = ""               # Optional, for future E2EE
matrix_room_ids: str = ""                # Comma-separated room IDs
```

Note: `matrix_access_token` uses `SecretStr` consistent with the SecretStr migration pattern documented in the project memory.

## Test Specification

### Health Check Tests (6 tests, matching existing pattern)

1. `test_health_check_not_started` -- Returns unavailable when adapter not started
2. `test_health_check_ok` -- Returns ok when API probe succeeds and queue < 100
3. `test_health_check_degraded` -- Returns degraded when queue >= 100
4. `test_health_check_api_failure` -- Returns unavailable when API probe fails
5. `test_health_check_timeout` -- Returns unavailable on timeout
6. `test_health_check_platform_name` -- Verifies platform is "matrix"

### Protocol Compliance Test (1 test)

1. `test_implements_messaging_adapter` -- Verifies MatrixAdapter satisfies the MessagingAdapter protocol

### Unit Tests (8+ tests)

1. `test_send_message` -- Sends message with correct endpoint, body, and txn_id
2. `test_send_rate_limited` -- Handles 429 response with retry
3. `test_receive_blocks_until_message` -- Blocks on empty queue, returns when message available
4. `test_sync_parses_messages` -- Extracts messages from sync response correctly
5. `test_sync_echo_suppression` -- Filters out own messages
6. `test_sync_room_filtering` -- Only processes messages from allowed rooms
7. `test_start_creates_client` -- Start creates httpx client and begins sync
8. `test_stop_closes_client` -- Stop cancels sync task and closes client
9. `test_sync_next_batch_token` -- Correctly passes next_batch between sync calls
10. `test_send_not_started_raises` -- Raises RuntimeError if send called before start

### Estimated Total: 15-20 tests

## Effort and Priority

- **Estimated effort**: 1-2 days
- **Lines of code**: ~200-250 (production) + ~200-250 (tests)
- **Priority**: LOW
- **Rationale**: Matrix is the last remaining channel adapter from the ZeroClaw parity list, but messaging adapters are not on the critical path for SkillsBench evaluation or AWM adaptations. The other 4 adapters provide sufficient channel coverage for most deployments.

## Dependencies

- `httpx` (already a project dependency)
- No new dependencies required
- No Matrix SDK needed (raw HTTP approach)

## Future Enhancements

1. **E2EE support**: Would require `python-olm` or `vodozemac` for Olm/Megolm encryption. Estimated additional 500+ lines.
2. **Media message support**: Handle `m.image`, `m.file`, `m.video` message types. Estimated additional 50-80 lines.
3. **Presence tracking**: Monitor user online/offline status via `/presence` endpoint. Estimated additional 30-50 lines.
4. **Room management**: Join/leave rooms, invite users, set room topic. Estimated additional 80-120 lines.
