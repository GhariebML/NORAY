import { useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  addEdge,
  type Connection,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useDagStore } from '../store/dagStore';
import { useLayoutStore } from '../store/layoutStore';

export default function ExecutionDAG() {
  const { nodes, edges, setNodes, setEdges } = useDagStore();
  const { setSelectedNodeId } = useLayoutStore();

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <div className="w-full h-full bg-slate-950">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onConnect={onConnect}
        onNodeClick={(_, node) => setSelectedNodeId(node.id)}
        onPaneClick={() => setSelectedNodeId(null)}
        fitView
        colorMode="dark"
      >
        <Controls />
        <MiniMap zoomable pannable />
        <Background gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}
