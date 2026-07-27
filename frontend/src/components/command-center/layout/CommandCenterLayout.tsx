import { useLayoutStore } from '../store/layoutStore';
import TopNav from './TopNav';
import Sidebar from './Sidebar';
import ExecutionDAG from '../workspace/ExecutionDAG';
import AgentMonitor from '../workspace/AgentMonitor';
import MemoryExplorer from '../workspace/MemoryExplorer';
import RetrieverInspector from '../workspace/RetrieverInspector';
import KnowledgeGraph from '../workspace/KnowledgeGraph';
import ToolRegistry from '../workspace/ToolRegistry';
import ModelObservatory from '../workspace/ModelObservatory';
import Governance from '../workspace/Governance';
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
             ) : mainView === 'universal-retriever' ? (
                <RetrieverInspector />
             ) : mainView === 'knowledge-graph' ? (
                <KnowledgeGraph />
             ) : mainView === 'tool-registry' ? (
                <ToolRegistry />
             ) : mainView === 'model-observatory' ? (
                <ModelObservatory />
             ) : mainView === 'governance' ? (
                <Governance />
             ) : mainView === 'telemetry' ? (
                <TelemetryDashboard />
             ) : (
                <div className="absolute inset-0 flex items-center justify-center text-slate-655">
                   <h1 className="text-2xl font-bold opacity-30 uppercase tracking-widest">{(mainView as string).replace('-', ' ')}</h1>
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
              className="border-l border-slate-900 bg-slate-950 flex flex-col"
            >
              <div className="p-4 border-b border-slate-900 font-semibold text-xs uppercase tracking-wider text-slate-400 font-mono">Telemetry Inspector</div>
              <div className="p-4 text-slate-500 text-xs text-center mt-10 font-mono">
                Select a node to inspect details in real time.
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
