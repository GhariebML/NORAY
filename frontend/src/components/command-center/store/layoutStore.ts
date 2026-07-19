import { create } from 'zustand';

export type MainView = 
  | 'execution-graph' 
  | 'agent-monitor' 
  | 'memory-explorer' 
  | 'universal-retriever'
  | 'knowledge-graph'
  | 'tool-registry'
  | 'governance'
  | 'telemetry'
  | 'model-observatory';

interface LayoutState {
  mainView: MainView;
  setMainView: (view: MainView) => void;
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  inspectorOpen: boolean;
  setInspectorOpen: (open: boolean) => void;
  selectedNodeId: string | null;
  setSelectedNodeId: (id: string | null) => void;
}

export const useLayoutStore = create<LayoutState>((set) => ({
  mainView: 'execution-graph',
  setMainView: (view) => set({ mainView: view }),
  sidebarCollapsed: false,
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  inspectorOpen: true,
  setInspectorOpen: (open) => set({ inspectorOpen: open }),
  selectedNodeId: null,
  setSelectedNodeId: (id) => set({ selectedNodeId: id, inspectorOpen: !!id }),
}));
