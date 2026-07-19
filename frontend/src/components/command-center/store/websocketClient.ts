import { useLogStore } from './logStore';
import { useDagStore } from './dagStore';

class WebsocketClient {
  private ws: WebSocket | null = null;
  private reconnectTimer: any = null;

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    
    this.ws = new WebSocket('ws://localhost:8001/api/stream');
    
    this.ws.onopen = () => {
      console.log('Connected to AI Kernel Stream');
      useLogStore.getState().addLog({
        event_id: 'sys-connect',
        timestamp: new Date().toISOString(),
        event_type: 'SystemConnected',
        severity: 'info',
        metadata: { message: 'Connected to AI Kernel Stream' }
      });
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleEvent(data);
      } catch (e) {
        console.error('Failed to parse websocket event', e);
      }
    };

    this.ws.onclose = () => {
      console.log('Disconnected from AI Kernel. Reconnecting in 3s...');
      this.reconnectTimer = setTimeout(() => this.connect(), 3000);
    };
  }

  private handleEvent(data: any) {
    // 1. Always add to logs
    useLogStore.getState().addLog(data);

    // 2. Dispatch to specific stores based on event_type
    const dagStore = useDagStore.getState();
    
    if (data.event_type === 'NodeStarted') {
      dagStore.addNode({
        id: data.task_id || data.event_id,
        position: { x: Math.random() * 400, y: Math.random() * 400 }, // temporary random layout
        data: { label: data.metadata?.description || data.event_type, status: 'running' }
      });
    }
    else if (data.event_type === 'NodeCompleted') {
      dagStore.updateNodeStatus(data.task_id, 'completed');
    }
    else if (data.event_type === 'AgentStarted') {
       // Could update agentStore here
    }
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const wsClient = new WebsocketClient();
