# S39: Multi-Agent DAG Visualization

**Session:** 89
**Track:** S39
**Status:** Implemented
**Date:** 2026-03-15

## Objective

Add real-time workflow graph visualization showing agent DAG execution with
positioned nodes, dependency edges, status coloring, and hover tooltips.

## Deliverables

### Backend

1. **`engine/src/agent33/workflows/dag_layout.py`** -- New module containing:
   - `DAGNode`, `DAGEdge`, `DAGLayout` Pydantic models for positioned graph data
   - `compute_dag_layout(definition, run_state=None)` function that uses the
     existing `DAGBuilder` to compute topological levels, then assigns
     grid-based x/y coordinates
   - Layout constants (`NODE_WIDTH`, `NODE_HEIGHT`, `HORIZONTAL_GAP`, etc.)

2. **API Endpoints** (added to `engine/src/agent33/api/routes/workflows.py`):
   - `GET /v1/workflows/{name}/dag` -- Return DAGLayout for a workflow definition
   - `GET /v1/workflows/runs/{run_id}/dag` -- Return DAGLayout with live run
     state overlay from execution history

3. **`engine/tests/test_dag_layout.py`** -- Comprehensive tests covering:
   - Topological level computation (single, linear, parallel, diamond)
   - Position assignment (x/y spacing, bounding box)
   - Layout computation (labels, types, status overlay, edges, levels)
   - Model serialization
   - API endpoint integration (200, 404, 401 cases)

### Frontend

4. **`frontend/src/features/workflows/DAGTypes.ts`** -- TypeScript types
   matching backend models, plus `dagStatusToColor` and `dagStatusLabel` helpers

5. **`frontend/src/features/workflows/DAGVisualization.tsx`** -- SVG-based
   React component with:
   - Rounded rectangle nodes with status-colored borders
   - Cubic bezier edges with arrowheads
   - Hover tooltips showing type, agent, duration
   - Pan (mouse drag) and zoom (scroll wheel, buttons)
   - Keyboard accessible (Enter/Space to click nodes)
   - Running node border animation
   - No external graph library dependencies

6. **`frontend/src/features/workflows/__tests__/DAGVisualization.test.tsx`** --
   Vitest tests covering:
   - Status color/label utility functions
   - Node rendering and aria-labels
   - Edge rendering
   - Click and keyboard interaction callbacks
   - Tooltip show/hide behavior
   - Zoom controls
   - Empty graph edge case

## Architecture Notes

- Reuses the existing `DAGBuilder` from `workflows/dag.py` (Kahn's algorithm
  with parallel groups) rather than duplicating topological sort logic
- SVG-based rendering avoids adding new npm dependencies -- the existing
  `WorkflowGraph` component uses ReactFlow, but DAGVisualization is
  intentionally independent and lighter-weight
- The run state overlay endpoint reads from the in-memory execution history
  deque, matching the existing pattern in workflow routes
- Both endpoints are gated by `workflows:read` scope, matching existing
  workflow route permissions

## Files Modified

- `engine/src/agent33/api/routes/workflows.py` (added import + 2 endpoints)

## Files Created

- `engine/src/agent33/workflows/dag_layout.py`
- `engine/tests/test_dag_layout.py`
- `frontend/src/features/workflows/DAGTypes.ts`
- `frontend/src/features/workflows/DAGVisualization.tsx`
- `frontend/src/features/workflows/__tests__/DAGVisualization.test.tsx`
- `docs/research/session89-s39-dag-viz-scope.md`
