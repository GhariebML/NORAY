import { useLayoutStore, MainView } from '../store/layoutStore';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Network, Cpu, Database, Server, Wrench, Shield, LineChart, Target, ChevronLeft, ChevronRight } from 'lucide-react';
import clsx from 'clsx';

const NAV_ITEMS: { id: MainView; label: string; icon: any }[] = [
  { id: 'execution-graph', label: 'Execution DAG', icon: Network },
  { id: 'agent-monitor', label: 'Agent Monitor', icon: Cpu },
  { id: 'memory-explorer', label: 'Memory', icon: Database },
  { id: 'universal-retriever', label: 'Retriever', icon: Target },
  { id: 'tool-registry', label: 'Tools', icon: Wrench },
  { id: 'model-observatory', label: 'Models', icon: Server },
  { id: 'telemetry', label: 'Telemetry', icon: Activity },
  { id: 'governance', label: 'Governance', icon: Shield },
];

export default function Sidebar() {
  const { mainView, setMainView, sidebarCollapsed, setSidebarCollapsed } = useLayoutStore();

  return (
    <motion.div 
      initial={false}
      animate={{ width: sidebarCollapsed ? '60px' : '240px' }}
      className="border-r border-slate-800/50 bg-slate-900/30 backdrop-blur-md flex flex-col justify-between h-full relative"
    >
      <div className="py-4 flex flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = mainView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setMainView(item.id)}
              className={clsx(
                "flex items-center gap-3 px-4 py-2 text-sm transition-all relative overflow-hidden group",
                isActive ? "text-emerald-400" : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
              )}
            >
              {isActive && (
                <motion.div layoutId="activeNav" className="absolute left-0 top-0 bottom-0 w-1 bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.8)]" />
              )}
              <Icon size={18} className="shrink-0" />
              <AnimatePresence mode="popLayout">
                {!sidebarCollapsed && (
                  <motion.span 
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    className="truncate font-medium"
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
            </button>
          );
        })}
      </div>

      <button 
        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        className="p-4 flex justify-center border-t border-slate-800/50 text-slate-500 hover:text-slate-300"
      >
        {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>
    </motion.div>
  );
}
