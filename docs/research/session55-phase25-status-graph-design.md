# Session 55 — Phase 25: Status-Aware Workflow Graph Design

**Date**: 2026-03-10  
**Scope**: WorkflowGraph status node colours, edge animation, polling refresh  
**Branch**: `feat/session55-phase25-graph-polish`

---

## 1. Problem Statement

The existing `WorkflowGraph` renders every node with the default ReactFlow
styling regardless of its workflow step status (`success`, `failed`, `running`,
`pending`). Operators cannot visually distinguish in-progress steps from
completed or failed ones, reducing the dashboard's at-a-glance value.

Additionally there is no automatic refresh mechanism — users must manually
reload to see status changes while a workflow is executing.

## 2. Design Decisions

### 2.1 Custom Node Component (`WorkflowStatusNode`)

**Decision**: Create a dedicated ReactFlow custom node that owns its own colour
coding and layout instead of CSS-hacking the built-in `default` node type.

**Rationale**:
- ReactFlow's custom node API (`nodeTypes`) is the idiomatic way to control
  node rendering (see ReactFlow v11 docs).
- Encapsulating status → colour logic in a pure function (`statusToColor`)
  makes it independently unit-testable without DOM rendering.
- The `memo()` wrapper avoids unnecessary re-renders during viewport panning
  and zooming (ReactFlow calls render on every frame during interactions).

**Colour palette**:

| Status    | Colour   | Hex       | Rationale                                |
|-----------|----------|-----------|------------------------------------------|
| success   | Green    | `#22c55e` | Universal "OK / done" signal             |
| failed    | Red      | `#ef4444` | Universal error / danger signal          |
| running   | Blue     | `#3b82f6` | Active / in-progress, distinct from both |
| retrying  | Amber    | `#f59e0b` | Still active, but distinguishable from initial execution |
| pending   | Gray     | `#9ca3af` | Neutral / waiting, muted tone            |
| skipped   | Gray     | `#9ca3af` | Terminal but intentionally neutral       |
| (default) | Gray     | `#9ca3af` | Safe fallback for unknown status strings |

Colours sourced from Tailwind's colour scale for consistency with common UI
libraries, though the project itself does not use Tailwind.

### 2.2 Running Node Pulse Animation

**Decision**: Use a CSS `@keyframes` animation (`wf-pulse-border`) that
oscillates `box-shadow` intensity on running nodes.

**Rationale**:
- Pure CSS animation avoids JS timer overhead — the GPU composites the shadow
  changes without triggering layout recalculations.
- The animation class (`wf-node-running`) is applied via the component's
  `className` prop, keeping it in `styles.css` alongside all other animations
  (matches project convention: `pulse-orb`, `pulse-recording`, etc.).
- A 1.8 s cycle with ease-in-out produces a calm, noticeable pulse without
  being distracting during long-running workflows.
- Retry states remain visually distinct by color alone; they do not reuse the
  running pulse class.

### 2.3 Edge Animation for Running Nodes

**Decision**: Set `animated: true` on any edge whose source **or** target node
has status `"running"` or `"retrying"`.

**Rationale**:
- ReactFlow's built-in edge animation draws a moving dash pattern along the
  path, visually indicating data flow.
- Animating edges connected to actively executing nodes (both directions) creates a
  localised visual cluster around active work, rather than animating the entire
  graph.
- The `mapWorkflowEdgesToReactFlow` function now accepts an optional
  `Set<string>` of running node IDs, keeping the logic pure and testable.

### 2.4 Polling Refresh

**Decision**: When `hasActiveNodes()` is true (any node is `running`,
`pending`, or `retrying`), start a `setInterval` that calls the parent-supplied `onRefresh`
callback every 2 seconds (configurable via `pollIntervalMs` prop).

**Rationale**:
- Inversion of control: the graph component does not know *how* to fetch data;
  it only signals *when* to fetch via the callback.
- 2 s default balances responsiveness against backend load. The caller can
  override (e.g., `pollIntervalMs={5000}` for larger clusters).
- The interval is cleaned up in the `useEffect` destructor on unmount or when
  `shouldPoll` becomes false, preventing stale timers.
- `retrying` is treated as active because the step is still in-flight; `skipped`
  is not, because it is already terminal from the graph's perspective.
- **Why not WebSocket?** The engine already exposes an observation stream via
  SSE (`ObservationStream` component). Polling is simpler for the graph because
  the data shape (full graph snapshot) is not event-based and the polling
  frequency is low. A future iteration may switch to SSE/WS if the engine adds
  a dedicated graph-status event channel.

### 2.5 `nodeTypes` Registry Placement

**Decision**: Define `nodeTypes` as a module-level `const` outside the
component tree.

**Rationale**:
- ReactFlow v11 documentation explicitly warns that passing an inline
  `nodeTypes` object causes full remounts on every render. Module-level
  definition is referentially stable.

## 3. Testing Strategy

The graph helpers are tested as pure functions, and the status node is rendered
directly with a light ReactFlow mock to cover display-specific behavior:

| Function                        | Tests                                           |
|---------------------------------|-------------------------------------------------|
| `statusToColor`                 | Named statuses including `retrying` / `skipped` |
| `mapWorkflowNodesToReactFlow`   | Existing tests + new `type: workflowStatus` assertion |
| `mapWorkflowEdgesToReactFlow`   | Without active IDs (all false), with source active, with target active |
| `hasActiveNodes`                | running, pending, retrying, skipped-only, terminal-only, no-status, empty |
| `getRunningNodeIds`             | Filters executing nodes used for edge animation |
| `WorkflowStatusNode` render     | running pulse class, retrying label, unknown fallback to `pending` |

## 4. Files Changed

| File | Change |
|------|--------|
| `frontend/src/components/WorkflowStatusNode.tsx` | **New** — custom node component + `statusToColor` |
| `frontend/src/components/WorkflowGraph.tsx` | Register custom node type, animated edges, polling hook |
| `frontend/src/components/WorkflowGraph.test.ts` | New test suites for colour mapping, edge animation, polling detection |
| `frontend/src/styles.css` | `wf-node-running` class + `wf-pulse-border` keyframes |
| `docs/research/session55-phase25-status-graph-design.md` | This document |

## 5. Future Considerations

- **SSE-based live updates**: Replace polling with server-sent events if the
  engine adds a `workflow/{id}/status` stream endpoint.
- **Status legend**: Add a `<Panel>` with colour swatches explaining the
  status mapping for new users.
- **Node tooltips**: Show timing / retry info on hover.
- **Transition animations**: Animate colour changes when a node moves from
  `running` → `success` using CSS `transition` on `border-color`.
