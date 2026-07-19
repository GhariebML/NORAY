import { useState } from 'react';
import { Database, Search, Filter } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function MemoryExplorer() {
  const [activeType, setActiveType] = useState('semantic');

  const types = ['Working', 'Conversation', 'Semantic', 'Procedural', 'Workspace', 'Episodic', 'Organization'];

  return (
    <div className="w-full h-full bg-[#0a0a0c] p-6 flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-200 tracking-wide flex items-center gap-2">
          <Database className="text-emerald-500" />
          Memory Explorer
        </h2>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input 
              type="text" 
              placeholder="Search memories..." 
              className="bg-slate-900 border border-slate-800 text-sm rounded-md pl-9 pr-4 py-1.5 focus:outline-none focus:border-emerald-500 transition-colors text-slate-200"
            />
          </div>
          <button className="p-1.5 bg-slate-900 border border-slate-800 rounded-md text-slate-400 hover:text-slate-200"><Filter size={16} /></button>
        </div>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-2 border-b border-slate-800/50">
        {types.map(t => (
          <button
            key={t}
            onClick={() => setActiveType(t.toLowerCase())}
            className={`px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider whitespace-nowrap transition-colors ${activeType === t.toLowerCase() ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50' : 'bg-slate-900 border border-slate-800 text-slate-500 hover:text-slate-300'}`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="grid gap-3">
           <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800 backdrop-blur">
             <div className="text-xs font-mono text-slate-500 mb-2">ID: mem_9823</div>
             <div className="text-slate-300 text-sm">User prefers strict adherence to PEP8 Python guidelines.</div>
             <div className="mt-3 flex gap-2">
               <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] uppercase">Rule</span>
               <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] uppercase">Confidence: 0.98</span>
             </div>
           </div>
        </div>
      </div>
    </div>
  );
}
