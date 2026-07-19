import { create } from 'zustand';

export interface LogEvent {
  event_id: string;
  timestamp: string;
  event_type: string;
  severity: string;
  metadata: any;
}

interface LogState {
  logs: LogEvent[];
  addLog: (log: LogEvent) => void;
  clearLogs: () => void;
}

export const useLogStore = create<LogState>((set) => ({
  logs: [],
  addLog: (log) => set((state) => ({ 
    logs: [log, ...state.logs].slice(0, 1000) // Keep last 1000 logs
  })),
  clearLogs: () => set({ logs: [] })
}));
