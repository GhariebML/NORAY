import { create } from 'zustand';

export interface AgentState {
  id: string;
  name: string;
  status: 'idle' | 'thinking' | 'executing' | 'waiting' | 'failed' | 'completed';
  currentTask?: string;
  latency: number;
  tokens: number;
  cost: number;
}

interface AgentStoreState {
  agents: Record<string, AgentState>;
  updateAgent: (id: string, updates: Partial<AgentState>) => void;
}

export const useAgentStore = create<AgentStoreState>((set) => ({
  agents: {},
  updateAgent: (id, updates) => set((state) => ({
    agents: {
      ...state.agents,
      [id]: { ...state.agents[id], ...updates, id }
    }
  }))
}));
