# Connector Default Policy Packs

AGENT-33 connector boundaries now support policy-pack presets via `CONNECTOR_POLICY_PACK`.

## Available packs

- `default` (default): no connector/operation blocks. Behavior matches legacy defaults.
- `strict-web`: blocks outbound web connector surfaces:
  - connectors: `tool:web_fetch`, `workflow:http_request`
- `mcp-readonly`: prevents MCP mutation calls:
  - operations: `tools/call`

## How packs combine with explicit blocklists

Policy-pack blocks are **unioned** with:

- `CONNECTOR_GOVERNANCE_BLOCKED_CONNECTORS`
- `CONNECTOR_GOVERNANCE_BLOCKED_OPERATIONS`

So explicit blocklists still work exactly as before.

## Notes

- Packs only apply when `CONNECTOR_BOUNDARY_ENABLED=true`.
- Routes/services can opt into a specific pack by passing `policy_pack` when constructing a connector boundary executor.
