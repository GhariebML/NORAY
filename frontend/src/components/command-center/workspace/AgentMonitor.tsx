import { useAgentStore } from '../store/agentStore';
import { Cpu, Activity, Clock, Coins } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';

export default function AgentMonitor() {
  const { agents } = useAgentStore();
  
  // For demo if empty:
  const displayAgents = Object.keys(agents).length > 0 ? Object.values(agents) : [
    { id: 'career_v1', name: 'Career Agent', status: 'thinking', currentTask: 'Analyzing ATS resume match', latency: 450, tokens: 1204, cost: 0.003 },
    { id: 'scholar_v2', name: 'Scholarship Agent', status: 'idle', currentTask: 'Waiting for task', latency: 0, tokens: 4500, cost: 0.012 },
  ];

  return (
    <div className="w-full h-full bg-[#0a0a0c] p-6 overflow-y-auto">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-xl font-bold text-slate-200 tracking-wide flex items-center gap-2">
          <Cpu className="text-emerald-500" />
          Active Agents
        </h2>
        <div className="text-sm text-slate-500">Live Execution Monitoring</div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <AnimatePresence>
          {displayAgents.map((agent) => (
            <motion.div
              key={agent.id}
              layout
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="border border-slate-800/50 bg-slate-900/40 rounded-xl p-5 backdrop-blur-md flex flex-col gap-4 relative overflow-hidden group hover:border-slate-700 transition-colors"
            >
              {/* Status Glow */}
              <div className={clsx(
                "absolute -top-20 -right-20 w-40 h-40 rounded-full blur-3xl opacity-20 transition-all duration-1000",
                agent.status === 'thinking' ? 'bg-amber-500' :
                agent.status === 'idle' ? 'bg-slate-500' :
                agent.status === 'executing' ? 'bg-emerald-500' :
                'bg-rose-500'
              )} />

              <div className="flex justify-between items-start z-10">
                <div className="flex flex-col gap-1">
                  <span className="font-bold text-slate-200">{agent.name}</span>
                  <span className="text-xs font-mono text-slate-500">{agent.id}</span>
                </div>
                <div className={clsx(
                  "px-2 py-1 rounded text-[10px] uppercase font-bold tracking-wider",
                  agent.status === 'thinking' ? 'bg-amber-500/20 text-amber-400' :
                  agent.status === 'idle' ? 'bg-slate-500/20 text-slate-400' :
                  agent.status === 'executing' ? 'bg-emerald-500/20 text-emerald-400' :
                  'bg-rose-500/20 text-rose-400'
                )}>
                  {agent.status}
                  {agent.status === 'thinking' && (
                    <span className="inline-block ml-1 animate-pulse">...</span>
                  )}
                </div>
              </div>

              <div className="flex-1 z-10">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Current Task</div>
                <div className="text-sm text-slate-300 h-10 line-clamp-2">{agent.currentTask}</div>
              </div>

              <div className="grid grid-cols-3 gap-2 border-t border-slate-800/50 pt-4 mt-2 z-10">
                <div className="flex flex-col gap-1">
                  <div className="text-[10px] text-slate-500 uppercase flex items-center gap-1"><Clock size={10}/> Latency</div>
                  <div className="font-mono text-xs text-slate-300">{agent.latency}ms</div>
                </div>
                <div className="flex flex-col gap-1">
                  <div className="text-[10px] text-slate-500 uppercase flex items-center gap-1"><Activity size={10}/> Tokens</div>
                  <div className="font-mono text-xs text-slate-300">{agent.tokens.toLocaleString()}</div>
                </div>
                <div className="flex flex-col gap-1">
                  <div className="text-[10px] text-slate-500 uppercase flex items-center gap-1"><Coins size={10}/> Cost</div>
                  <div className="font-mono text-xs text-emerald-400">${agent.cost.toFixed(4)}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
