import { create } from 'zustand';
import { Node, Edge } from '@xyflow/react';

interface DAGState {
  nodes: Node[];
  edges: Edge[];
  setNodes: (nodes: Node[] | ((prev: Node[]) => Node[])) => void;
  setEdges: (edges: Edge[] | ((prev: Edge[]) => Edge[])) => void;
  addNode: (node: Node) => void;
  updateNodeStatus: (nodeId: string, status: string, metadata?: any) => void;
}

export const useDagStore = create<DAGState>((set) => ({
  nodes: [],
  edges: [],
  setNodes: (updater) => set((state) => ({ nodes: typeof updater === 'function' ? updater(state.nodes) : updater })),
  setEdges: (updater) => set((state) => ({ edges: typeof updater === 'function' ? updater(state.edges) : updater })),
  addNode: (node) => set((state) => ({ nodes: [...state.nodes, node] })),
  updateNodeStatus: (nodeId, status, metadata) => set((state) => ({
    nodes: state.nodes.map(n => 
      n.id === nodeId ? { ...n, data: { ...n.data, status, ...metadata } } : n
    )
  })),
}));
