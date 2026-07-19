import { useLayoutStore } from '../store/layoutStore';
import TopNav from './TopNav';
import Sidebar from './Sidebar';
import ExecutionDAG from '../workspace/ExecutionDAG';
import AgentMonitor from '../workspace/AgentMonitor';
import MemoryExplorer from '../workspace/MemoryExplorer';
import TelemetryDashboard from '../workspace/TelemetryDashboard';
import BottomConsole from '../console/BottomConsole';
import { motion, AnimatePresence } from 'framer-motion';

export default function CommandCenterLayout() {
  const { inspectorOpen, mainView } = useLayoutStore();

  return (
    <div className="flex flex-col h-full w-full bg-[#0a0a0c]">
      <TopNav />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        
        {/* Main Workspace Area */}
        <div className="flex-1 flex flex-col overflow-hidden relative">
          <div className="flex-1 relative">
             {mainView === 'execution-graph' ? (
                <ExecutionDAG />
             ) : mainView === 'agent-monitor' ? (
                <AgentMonitor />
             ) : mainView === 'memory-explorer' ? (
                <MemoryExplorer />
             ) : mainView === 'telemetry' ? (
                <TelemetryDashboard />
             ) : (
                <div className="absolute inset-0 flex items-center justify-center text-slate-600">
                   <h1 className="text-2xl font-bold opacity-30 uppercase tracking-widest">{mainView.replace('-', ' ')}</h1>
                </div>
             )}
          </div>
          
          <BottomConsole />
        </div>
        
        {/* Right Inspector */}
        <AnimatePresence>
          {inspectorOpen && (
            <motion.div 
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 320, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              className="border-l border-slate-800/50 bg-slate-900/30 backdrop-blur-md flex flex-col"
            >
              <div className="p-4 border-b border-slate-800/50 font-semibold text-sm">Inspector</div>
              <div className="p-4 text-slate-400 text-xs text-center mt-10">
                Select a node to inspect details.
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
