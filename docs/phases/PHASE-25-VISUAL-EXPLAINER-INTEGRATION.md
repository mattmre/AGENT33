# Phase 25: Visual Explainer Integration

## Status: Planned

## Overview
- **Phase**: 25 of 25+
- **Category**: Observability / Operator UX
- **Primary Goal**: Deliver visual explanation capabilities for workflow DAGs, agent decision trees, and multi-agent coordination to improve debugging efficiency and operator trust in autonomous systems.

## Objectives
- Enable real-time visualization of workflow execution graphs with step status and dependencies.
- Provide interactive drill-down for step inputs, outputs, logs, and timing.
- Implement server-side graph generation with client-side interactive rendering for scalability.
- Close observability gap between text-based traces and intuitive visual representations.

## Scope

### In Scope
- Workflow DAG visualization (Stage 1 MVP):
  - Backend route: `/v1/visualizations/workflows/{workflow_id}/graph`
  - Graph serialization with nodes, edges, layout coordinates, and status metadata
  - Frontend component using React Flow or similar library for zoom/pan/click interactions
- Real-time status updates via polling or WebSocket integration
- Server-side layout computation using graphviz or igraph for large-graph scalability
- Node detail sidebar showing step inputs/outputs/logs on click
- Docker container updates to include visualization dependencies
- Documentation for operators on graph view usage

### Out of Scope (Deferred to Future Phases)
- Agent decision tree visualization (Phase 26 candidate)
- Multi-agent coordination maps (Phase 27 candidate)
- Trace timeline Gantt views (Phase 28 candidate)
- Custom layout overrides and saved positions
- Static export formats (DOT, SVG, PNG) beyond JSON
- CLI-based ASCII art visualizations (future enhancement)

## Deliverables

| # | Deliverable | Target Path | Description |
|---|-------------|-------------|-------------|
| 1 | Research analysis | `docs/research/visual-explainer-integration-analysis-2026-02-17.md` | Problem statement, architecture options, rollout stages, risks |
| 2 | Backend visualization route | `engine/src/agent33/api/routes/visualizations.py` | Graph serialization endpoint for workflows |
| 3 | Graph generation service | `engine/src/agent33/services/graph_generator.py` | Layout computation and node/edge formatting logic |
| 4 | Frontend graph component | `frontend/src/components/WorkflowGraph.tsx` | Interactive visualization with zoom/pan/drill-down |
| 5 | API domain integration | `frontend/src/data/domains/workflows.ts` | Add graph view operation to workflows domain |
| 6 | Container dependency update | `engine/Dockerfile`, `engine/pyproject.toml` | Add graphviz or igraph for server-side layout |
| 7 | Unit tests | `engine/tests/test_visualizations_api.py` | Test graph generation for various workflow structures |
| 8 | Frontend tests | `frontend/src/components/WorkflowGraph.test.tsx` | Snapshot tests and interaction validation |
| 9 | Performance validation | `docs/progress/phase-25-visual-explainer-log.md` | Load times, render performance, real-time update latency |
| 10 | Operator documentation | `docs/walkthroughs.md` update | How to use workflow graph view for debugging |

## Acceptance Criteria
- [ ] Backend `/v1/visualizations/workflows/{workflow_id}/graph` route returns valid node/edge JSON
- [ ] Graph generation handles workflows with 10-100 steps without timeout (<1s response)
- [ ] Frontend renders workflow graphs with zoom, pan, and node-click interactions
- [ ] Clicking a node displays step details (inputs, outputs, logs, status) in sidebar
- [ ] Real-time status updates reflect workflow state changes within 2s latency
- [ ] Graph layout is readable for typical workflows without manual repositioning
- [ ] Auth middleware enforces same permissions as `/v1/workflows/` routes
- [ ] Unit tests pass for graph generation logic and frontend component
- [ ] Performance validation confirms <1s load and <500ms render for 100-node graphs
- [ ] Documentation includes workflow graph usage examples with screenshots

## Dependencies
- Phase 16 (Observability & Trace Pipeline) -- trace schema and audit trail
- Phase 22 (Unified UI Platform) -- frontend architecture and API integration layer

## Blocks
- Phase 26 (Agent Decision Tree Visualization, if introduced)
- Phase 27 (Multi-Agent Coordination Maps, if introduced)

## Orchestration Guidance

### Implementation Sequence
1. **Research & Analysis** (Architect)
   - Review existing workflow/trace data structures
   - Finalize graph JSON schema (nodes, edges, metadata)
   - Select layout engine (graphviz vs igraph) and rendering library (React Flow vs D3.js)
   
2. **Backend Graph Generation** (Implementer)
   - Create `visualizations.py` route with workflow-to-graph translation
   - Implement `graph_generator.py` service with layout computation
   - Add auth middleware wiring
   - Write unit tests for various workflow structures (linear, branching, diamond, cyclic detection)

3. **Frontend Visualization Component** (Implementer)
   - Install React Flow (or chosen library) and type definitions
   - Build `WorkflowGraph.tsx` with basic node/edge rendering
   - Add zoom/pan controls and node-click event handling
   - Implement detail sidebar for step metadata display

4. **Integration & Real-Time Updates** (Implementer)
   - Wire graph view into workflows domain operations
   - Add polling or WebSocket listener for status updates
   - Test with long-running workflows to validate refresh behavior

5. **Container & Deployment** (Implementer)
   - Update Dockerfile with graphviz/igraph installation
   - Verify docker compose builds and runs without errors
   - Test graph generation in containerized environment

6. **Validation & Documentation** (QA + Documentation)
   - Run performance tests with 10/50/100-step workflows
   - Measure load times, render times, memory usage
   - Document graph view usage in walkthroughs with example workflows
   - Capture validation evidence in phase progress log

7. **Review & Handoff** (Reviewer + Orchestrator)
   - Security review of graph endpoint auth
   - Code review of graph generation and rendering logic
   - UX review of graph layout and interaction patterns
   - Update phase status and archive artifacts

### Key Decision Points
- **Layout engine**: Graphviz (mature, widely used) vs igraph (faster, Python-native)
  - Recommendation: Start with graphviz; fallback to igraph if performance issues
- **Rendering library**: React Flow (modern, React-native) vs D3.js (flexible, lower-level)
  - Recommendation: React Flow for faster integration; D3 if custom layouts needed
- **Real-time updates**: WebSocket push vs client-side polling
  - Recommendation: Polling for MVP (<2s interval); WebSockets in future if latency critical

### Progress Tracking
- Record all checkpoints in `docs/progress/phase-25-visual-explainer-log.md`
- Include:
  - Layout engine selection rationale
  - Graph schema design decisions
  - Performance test results (load times, render times, graph sizes)
  - Debug notes for layout algorithm tuning
  - Validation evidence (commands, outputs, screenshots)

## Review Checklist
- [ ] Architecture reviewed for scalability and performance (Architect)
- [ ] Security review completed for visualization endpoint auth (Security)
- [ ] Graph generation logic tested with edge cases (cyclic, disconnected, empty workflows) (QA)
- [ ] Frontend rendering tested across browsers (Chrome, Firefox, Safari) (QA)
- [ ] Performance validated against success criteria (<1s load, <500ms render) (QA)
- [ ] Documentation reviewed for operator clarity and screenshot accuracy (Documentation)
- [ ] Code review completed for backend routes and frontend components (Reviewer)
- [ ] Deployment verified in Docker compose environment (DevOps/Orchestrator)

## Security Considerations
- Reuse existing `/v1/workflows/` auth middleware for `/v1/visualizations/workflows/` routes
- No new permission model required; visualization access = workflow read access
- Sanitize step labels and metadata to prevent XSS in frontend rendering
- Rate-limit visualization generation to prevent DoS with large workflow graphs (>1000 nodes)
- Do not expose sensitive step parameters beyond existing trace log visibility

## Performance Targets
- Graph load time <1s for 100-step workflows (server-side generation + JSON serialization)
- Graph render time <500ms in browser for 100-node graphs (client-side layout and paint)
- Real-time status update latency <2s from backend event to UI refresh
- Memory usage <50MB additional heap for frontend graph component with 100-node workflow

## Future Enhancements (Post-Phase 25)
- Agent decision tree visualization (tool selection, parameter resolution, confidence scores)
- Multi-agent coordination maps (handoff flows, message routing, escalation patterns)
- Trace timeline Gantt views (concurrent operation overlap, critical path analysis)
- Custom layout overrides (manual node positioning, saved preferences)
- Static export formats (DOT for graphviz CLI, SVG/PNG for reports)
- CLI-based ASCII art visualizations (`agent33 visualize workflow <id> --ascii`)
- Graph diffing for workflow version comparison
- Performance analytics overlays (token usage, API latency heatmaps)

## References
- Research analysis: `docs/research/visual-explainer-integration-analysis-2026-02-17.md`
- Phase 16 (Observability): `docs/phases/PHASE-16-OBSERVABILITY-AND-TRACE-PIPELINE.md`
- Phase 22 (UI Platform): `docs/phases/PHASE-22-UNIFIED-UI-PLATFORM-AND-ACCESS-LAYER.md`
- React Flow docs: https://reactflow.dev/
- Graphviz Python bindings: https://github.com/xflr6/graphviz
- igraph Python library: https://python.igraph.org/
