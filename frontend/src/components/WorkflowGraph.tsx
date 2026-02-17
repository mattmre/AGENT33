import { useCallback, useMemo, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  type Edge,
  type Node,
  Panel,
  ReactFlowProvider,
  useEdgesState,
  useNodesState
} from "reactflow";
import "reactflow/dist/style.css";

export interface WorkflowNode {
  id: string;
  name: string;
  action: string;
  x?: number;
  y?: number;
  position?: { x: number; y: number };
  metadata?: Record<string, unknown>;
  status?: string;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
}

export interface WorkflowGraphData {
  workflow_id: string;
  workflow_version?: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  layout?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

interface WorkflowGraphProps {
  data: WorkflowGraphData;
}

/**
 * Maps backend WorkflowNode to ReactFlow Node format
 */
export function mapWorkflowNodesToReactFlow(nodes: WorkflowNode[]): Node[] {
  return nodes.map((node) => {
    const position = node.position ?? { x: node.x ?? 0, y: node.y ?? 0 };
    return {
      id: node.id,
      type: "default",
      position,
      data: {
        label: node.name || node.id,
        action: node.action,
        status: node.status,
        metadata: node.metadata
      }
    };
  });
}

/**
 * Maps backend WorkflowEdge to ReactFlow Edge format
 */
export function mapWorkflowEdgesToReactFlow(edges: WorkflowEdge[]): Edge[] {
  return edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    type: "smoothstep",
    animated: false
  }));
}

function WorkflowGraphInner({ data }: WorkflowGraphProps): JSX.Element {
  const initialNodes = useMemo(() => mapWorkflowNodesToReactFlow(data.nodes), [data.nodes]);
  const initialEdges = useMemo(() => mapWorkflowEdgesToReactFlow(data.edges), [data.edges]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const onNodeClick = useCallback((_event: unknown, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const selectedNodeData = selectedNode
    ? (selectedNode.data as {
        label: string;
        action?: string;
        status?: string;
        metadata?: Record<string, unknown>;
      })
    : null;

  return (
    <div className="workflow-graph-container">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        fitView
        minZoom={0.1}
        maxZoom={2}
      >
        <Background />
        <Controls />
        <Panel position="top-left" className="workflow-graph-header">
          <div>
            <strong>{data.workflow_id}</strong>
            {data.workflow_version ? <span> v{data.workflow_version}</span> : null}
          </div>
          <div className="workflow-graph-stats">
            {data.nodes.length} nodes · {data.edges.length} edges
          </div>
        </Panel>
      </ReactFlow>
      {selectedNode ? (
        <aside className="workflow-graph-detail">
          <h4>Node Details</h4>
          <div className="detail-row">
            <span className="detail-label">ID:</span>
            <span className="detail-value">{selectedNode.id}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Name:</span>
            <span className="detail-value">{selectedNodeData?.label}</span>
          </div>
          {selectedNodeData?.action ? (
            <div className="detail-row">
              <span className="detail-label">Action:</span>
              <span className="detail-value">{selectedNodeData.action}</span>
            </div>
          ) : null}
          {selectedNodeData?.status ? (
            <div className="detail-row">
              <span className="detail-label">Status:</span>
              <span className="detail-value">{selectedNodeData.status}</span>
            </div>
          ) : null}
          {selectedNodeData?.metadata ? (
            <div className="detail-row">
              <span className="detail-label">Metadata:</span>
              <pre className="detail-metadata">
                {JSON.stringify(selectedNodeData.metadata, null, 2)}
              </pre>
            </div>
          ) : null}
        </aside>
      ) : null}
    </div>
  );
}

export function WorkflowGraph({ data }: WorkflowGraphProps): JSX.Element {
  return (
    <ReactFlowProvider>
      <WorkflowGraphInner data={data} />
    </ReactFlowProvider>
  );
}
