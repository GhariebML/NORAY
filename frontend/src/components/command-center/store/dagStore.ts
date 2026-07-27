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

const initialNodes: Node[] = [
  { id: 'goal', type: 'input', position: { x: 250, y: 0 }, data: { label: 'Goal Definition (User Query)', status: 'completed' }, style: { background: '#064e3b', border: '1px solid #10b981', color: '#10b981', borderRadius: '8px', padding: '8px' } },
  { id: 'planner', position: { x: 250, y: 70 }, data: { label: 'Task Planner & Scheduler', status: 'completed' }, style: { background: '#064e3b', border: '1px solid #10b981', color: '#10b981', borderRadius: '8px', padding: '8px' } },
  { id: 'retriever', position: { x: 100, y: 150 }, data: { label: 'Vector Retriever (BM25 + RRF)', status: 'completed' }, style: { background: '#064e3b', border: '1px solid #10b981', color: '#10b981', borderRadius: '8px', padding: '8px' } },
  { id: 'kg_miner', position: { x: 400, y: 150 }, data: { label: 'Knowledge Graph Triples Search', status: 'completed' }, style: { background: '#064e3b', border: '1px solid #10b981', color: '#10b981', borderRadius: '8px', padding: '8px' } },
  { id: 'reasoner', position: { x: 250, y: 230 }, data: { label: 'Reasoner (Synthesis Engine)', status: 'running' }, style: { background: '#1e1b4b', border: '1px solid #6366f1', color: '#818cf8', borderRadius: '8px', padding: '8px' } },
  { id: 'validator', position: { x: 250, y: 310 }, data: { label: 'Grounding & Hallucination Validator', status: 'waiting' }, style: { background: '#18181b', border: '1px solid #27272a', color: '#a1a1aa', borderRadius: '8px', padding: '8px' } },
  { id: 'response', type: 'output', position: { x: 250, y: 395 }, data: { label: 'Final Structured Response', status: 'waiting' }, style: { background: '#18181b', border: '1px solid #27272a', color: '#a1a1aa', borderRadius: '8px', padding: '8px' } }
];

const initialEdges: Edge[] = [
  { id: 'e-goal-planner', source: 'goal', target: 'planner', animated: true, style: { stroke: '#10b981' } },
  { id: 'e-planner-retriever', source: 'planner', target: 'retriever', animated: true, style: { stroke: '#10b981' } },
  { id: 'e-planner-kg', source: 'planner', target: 'kg_miner', animated: true, style: { stroke: '#10b981' } },
  { id: 'e-retriever-reasoner', source: 'retriever', target: 'reasoner', animated: true, style: { stroke: '#10b981' } },
  { id: 'e-kg-reasoner', source: 'kg_miner', target: 'reasoner', animated: true, style: { stroke: '#10b981' } },
  { id: 'e-reasoner-validator', source: 'reasoner', target: 'validator', animated: true, style: { stroke: '#6366f1' } },
  { id: 'e-validator-response', source: 'validator', target: 'response', animated: false, style: { stroke: '#27272a' } }
];

export const useDagStore = create<DAGState>((set) => ({
  nodes: initialNodes,
  edges: initialEdges,
  setNodes: (updater) => set((state) => ({ nodes: typeof updater === 'function' ? updater(state.nodes) : updater })),
  setEdges: (updater) => set((state) => ({ edges: typeof updater === 'function' ? updater(state.edges) : updater })),
  addNode: (node) => set((state) => ({ nodes: [...state.nodes, node] })),
  updateNodeStatus: (nodeId, status, metadata) => set((state) => {
    let background = '#18181b';
    let borderColor = '#27272a';
    let color = '#a1a1aa';
    
    if (status === 'completed') {
      background = '#064e3b';
      borderColor = '#10b981';
      color = '#10b981';
    } else if (status === 'running') {
      background = '#1e1b4b';
      borderColor = '#6366f1';
      color = '#818cf8';
    } else if (status === 'failed') {
      background = '#4c0519';
      borderColor = '#f43f5e';
      color = '#f43f5e';
    }

    return {
      nodes: state.nodes.map(n => 
        n.id === nodeId ? { 
          ...n, 
          data: { ...n.data, status, ...metadata },
          style: { ...n.style, background, border: `1px solid ${borderColor}`, color }
        } : n
      ),
      edges: state.edges.map(e => {
        if (e.source === nodeId) {
          return { ...e, animated: status === 'running' || status === 'completed', style: { stroke: borderColor } };
        }
        return e;
      })
    };
  }),
}));
